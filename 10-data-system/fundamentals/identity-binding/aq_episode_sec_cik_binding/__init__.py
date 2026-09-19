"""Fail-closed, date-bounded binding from a P1 episode to an SEC filer CIK."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from datetime import date
from itertools import pairwise
from typing import Annotated, Literal

import rfc8785
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

EpisodeId = Annotated[str, StringConstraints(pattern=r"^P1EP-[0-9a-f]{64}$")]
Cik = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}$")]
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
BindingId = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
BindingClassification = Literal["PASS_EXACT", "PASS_CORROBORATED"]
CoverageClassification = Literal["FULL", "PARTIAL", "UNBOUND"]
ExclusionClassification = Literal[
    "INSUFFICIENT_EVIDENCE",
    "NO_FREE_UPSTREAM_COVERAGE",
    "CONFLICT_REMAINS_FAIL_CLOSED",
]
DecisionId = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]

SCHEMA_VERSION = "EpisodeSecCikBindingV1"
RFC8785_IMPLEMENTATION = "rfc8785==0.1.4"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class _BindingProjection(_FrozenModel):
    episode_id: EpisodeId
    cik: Cik
    valid_from: date
    valid_to: date
    binding_classification: BindingClassification
    evidence_source_identities: Annotated[
        tuple[NonEmptyString, ...],
        Field(min_length=1, json_schema_extra={"uniqueItems": True}),
    ]

    @field_validator("evidence_source_identities")
    @classmethod
    def require_distinct_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("evidence_source_identities must be unique")
        return value

    @model_validator(mode="after")
    def require_half_open_interval(self) -> _BindingProjection:
        if self.valid_from >= self.valid_to:
            raise ValueError("binding interval must be non-empty and half-open")
        return self


class _ExclusionProjection(_FrozenModel):
    episode_id: EpisodeId
    classification: ExclusionClassification
    reason: NonEmptyString
    evidence_source_identities: Annotated[
        tuple[NonEmptyString, ...],
        Field(min_length=1, json_schema_extra={"uniqueItems": True}),
    ]

    @field_validator("evidence_source_identities")
    @classmethod
    def require_distinct_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("evidence_source_identities must be unique")
        return value


def binding_id_for(fields: Mapping[str, object] | _BindingProjection) -> str:
    """Return the RFC 8785 + SHA-256 identity of the six authoritative fields."""

    projection = (
        fields
        if isinstance(fields, _BindingProjection)
        else _BindingProjection.model_validate(fields)
    )
    canonical = rfc8785.dumps(projection.model_dump(mode="json"))
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def exclusion_decision_id_for(
    fields: Mapping[str, object] | _ExclusionProjection,
) -> str:
    """Return the RFC 8785 + SHA-256 identity of an exclusion decision."""

    projection = (
        fields
        if isinstance(fields, _ExclusionProjection)
        else _ExclusionProjection.model_validate(fields)
    )
    canonical = rfc8785.dumps(projection.model_dump(mode="json"))
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _authority_field(item: object, name: str) -> object:
    if isinstance(item, Mapping):
        if name not in item:
            raise ValueError(f"episode authority lacks {name}")
        return item[name]
    if not hasattr(item, name):
        raise ValueError(f"episode authority lacks {name}")
    return getattr(item, name)


def _as_date(value: object, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"episode authority {field_name} is not an ISO date") from exc
    raise ValueError(f"episode authority {field_name} is not a date")


def _episode_authority_map(
    authoritative_episodes: Iterable[object],
) -> dict[str, tuple[date, date]]:
    authority: dict[str, tuple[date, date]] = {}
    for item in authoritative_episodes:
        episode_id = _authority_field(item, "episode_id")
        if not isinstance(episode_id, str) or not episode_id.startswith("P1EP-"):
            raise ValueError("episode authority contains an invalid P1 episode_id")
        valid_from = _as_date(_authority_field(item, "valid_from"), "valid_from")
        valid_to = _as_date(_authority_field(item, "valid_to"), "valid_to")
        if valid_from >= valid_to:
            raise ValueError("episode authority interval must be non-empty")
        if episode_id in authority:
            raise ValueError(f"duplicate episode authority: {episode_id}")
        authority[episode_id] = (valid_from, valid_to)
    return authority


class EpisodeSecCikBindingV1(_BindingProjection):
    """One immutable SEC filer binding admitted against full P1 episode authority."""

    binding_id: BindingId

    @model_validator(mode="after")
    def validate_identity_and_episode_authority(
        self, info: ValidationInfo
    ) -> EpisodeSecCikBindingV1:
        expected = binding_id_for(
            _BindingProjection.model_validate(
                self.model_dump(mode="python", exclude={"binding_id"})
            )
        )
        if self.binding_id != expected:
            raise ValueError("binding_id does not match RFC 8785 identity")

        context = info.context if isinstance(info.context, Mapping) else None
        authority = context.get("episode_authority") if context is not None else None
        if not isinstance(authority, Mapping):
            raise ValueError(  # noqa: TRY004 - Pydantic must wrap this as ValidationError.
                "full P1 InstrumentEpisodeV1 authority is required"
            )
        interval = authority.get(self.episode_id)
        if interval is None:
            raise ValueError("binding episode_id is unknown to full P1 authority")
        episode_from, episode_to = interval
        if self.valid_from < episode_from or self.valid_to > episode_to:
            raise ValueError("binding interval exceeds the authoritative P1 episode")
        return self

    @classmethod
    def admit(
        cls,
        *,
        authoritative_episodes: Iterable[object],
        **authoritative_fields: object,
    ) -> EpisodeSecCikBindingV1:
        """Create an immutable record only after exact P1 authority validation."""

        projection = _BindingProjection.model_validate(authoritative_fields)
        payload = {
            **projection.model_dump(mode="python"),
            "binding_id": binding_id_for(projection),
        }
        return cls.model_validate(
            payload,
            context={"episode_authority": _episode_authority_map(authoritative_episodes)},
        )


class EpisodeSecCikExclusionV1(_ExclusionProjection):
    """One immutable, fail-closed absence-of-authority decision for a P1 episode."""

    decision_id: DecisionId

    @model_validator(mode="after")
    def validate_identity_and_episode_authority(
        self, info: ValidationInfo
    ) -> EpisodeSecCikExclusionV1:
        expected = exclusion_decision_id_for(
            _ExclusionProjection.model_validate(
                self.model_dump(mode="python", exclude={"decision_id"})
            )
        )
        if self.decision_id != expected:
            raise ValueError("decision_id does not match RFC 8785 identity")
        context = info.context if isinstance(info.context, Mapping) else None
        authority = context.get("episode_authority") if context is not None else None
        if not isinstance(authority, Mapping):
            raise ValueError(  # noqa: TRY004 - Pydantic must wrap this as ValidationError.
                "full P1 InstrumentEpisodeV1 authority is required"
            )
        if self.episode_id not in authority:
            raise ValueError("exclusion episode_id is unknown to full P1 authority")
        return self

    @classmethod
    def admit(
        cls,
        *,
        authoritative_episodes: Iterable[object],
        **authoritative_fields: object,
    ) -> EpisodeSecCikExclusionV1:
        projection = _ExclusionProjection.model_validate(authoritative_fields)
        payload = {
            **projection.model_dump(mode="python"),
            "decision_id": exclusion_decision_id_for(projection),
        }
        return cls.model_validate(
            payload,
            context={"episode_authority": _episode_authority_map(authoritative_episodes)},
        )


def validate_binding_record(
    record: Mapping[str, object] | EpisodeSecCikBindingV1,
    *,
    authoritative_episodes: Iterable[object],
) -> EpisodeSecCikBindingV1:
    payload = record.model_dump(mode="python") if isinstance(record, BaseModel) else record
    return EpisodeSecCikBindingV1.model_validate(
        payload,
        context={"episode_authority": _episode_authority_map(authoritative_episodes)},
    )


def validate_exclusion_record(
    record: Mapping[str, object] | EpisodeSecCikExclusionV1,
    *,
    authoritative_episodes: Iterable[object],
) -> EpisodeSecCikExclusionV1:
    payload = record.model_dump(mode="python") if isinstance(record, BaseModel) else record
    return EpisodeSecCikExclusionV1.model_validate(
        payload,
        context={"episode_authority": _episode_authority_map(authoritative_episodes)},
    )


def validate_exclusion_set(
    records: Iterable[Mapping[str, object] | EpisodeSecCikExclusionV1],
    *,
    authoritative_episodes: Iterable[object],
) -> tuple[EpisodeSecCikExclusionV1, ...]:
    """Validate identities and reject duplicate episode exclusion decisions."""

    authority = _episode_authority_map(authoritative_episodes)
    validated: list[EpisodeSecCikExclusionV1] = []
    decision_ids: set[str] = set()
    episode_ids: set[str] = set()
    for record in records:
        payload = record.model_dump(mode="python") if isinstance(record, BaseModel) else record
        exclusion = EpisodeSecCikExclusionV1.model_validate(
            payload, context={"episode_authority": authority}
        )
        if exclusion.decision_id in decision_ids:
            raise ValueError(f"duplicate decision_id: {exclusion.decision_id}")
        if exclusion.episode_id in episode_ids:
            raise ValueError(f"duplicate exclusion episode_id: {exclusion.episode_id}")
        decision_ids.add(exclusion.decision_id)
        episode_ids.add(exclusion.episode_id)
        validated.append(exclusion)
    return tuple(validated)


def validate_binding_set(
    records: Iterable[Mapping[str, object] | EpisodeSecCikBindingV1],
    *,
    authoritative_episodes: Iterable[object],
) -> tuple[EpisodeSecCikBindingV1, ...]:
    """Validate IDs and reject duplicate or overlapping episode intervals."""

    authority = _episode_authority_map(authoritative_episodes)
    validated: list[EpisodeSecCikBindingV1] = []
    binding_ids: set[str] = set()
    for record in records:
        payload = record.model_dump(mode="python") if isinstance(record, BaseModel) else record
        binding = EpisodeSecCikBindingV1.model_validate(
            payload, context={"episode_authority": authority}
        )
        if binding.binding_id in binding_ids:
            raise ValueError(f"duplicate binding_id: {binding.binding_id}")
        binding_ids.add(binding.binding_id)
        validated.append(binding)

    by_episode: dict[str, list[EpisodeSecCikBindingV1]] = {}
    for binding in validated:
        by_episode.setdefault(binding.episode_id, []).append(binding)
    for episode_id, episode_bindings in by_episode.items():
        ordered = sorted(episode_bindings, key=lambda item: (item.valid_from, item.valid_to))
        for previous, current in pairwise(ordered):
            if current.valid_from < previous.valid_to:
                conflict = (
                    "CONFLICTING_CIK_OVERLAP"
                    if current.cik != previous.cik
                    else "REDUNDANT_BINDING_OVERLAP"
                )
                raise ValueError(f"{conflict}: {episode_id}")
    return tuple(validated)


def classify_episode_coverage(
    authoritative_episode: object,
    records: Iterable[Mapping[str, object] | EpisodeSecCikBindingV1],
) -> CoverageClassification:
    """Report binding interval coverage without inferring or creating authority."""

    authority = _episode_authority_map([authoritative_episode])
    episode_id, (episode_from, episode_to) = next(iter(authority.items()))
    validated = validate_binding_set(records, authoritative_episodes=[authoritative_episode])
    relevant = sorted(
        (item for item in validated if item.episode_id == episode_id),
        key=lambda item: item.valid_from,
    )
    if not relevant:
        return "UNBOUND"
    cursor = episode_from
    for binding in relevant:
        if binding.valid_from != cursor:
            return "PARTIAL"
        cursor = binding.valid_to
    return "FULL" if cursor == episode_to else "PARTIAL"


__all__ = [
    "RFC8785_IMPLEMENTATION",
    "SCHEMA_VERSION",
    "EpisodeSecCikBindingV1",
    "EpisodeSecCikExclusionV1",
    "binding_id_for",
    "classify_episode_coverage",
    "exclusion_decision_id_for",
    "validate_binding_record",
    "validate_binding_set",
    "validate_exclusion_record",
    "validate_exclusion_set",
]
