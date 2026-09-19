"""Direct, fail-closed Valuein projections into existing P5 contracts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
import math
from typing import Any, Literal

from aq_episode_sec_cik_binding import EpisodeSecCikBindingV1

IdentityClassification = Literal[
    "EXACT",
    "COMPATIBLE_CANDIDATE",
    "PARTIAL",
    "AMBIGUOUS",
    "NO_MATCH",
    "CONFLICT",
]

def _missing(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _required(row: Mapping[str, Any], name: str) -> object:
    value = row.get(name)
    if _missing(value) or str(value).strip() == "":
        raise ValueError(f"Valuein row is missing {name}")
    return value


def _iso_date(value: object, name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValueError(f"Valuein {name} is not an ISO date") from exc


def _cik(value: object) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())
    if not digits or len(digits) > 10:
        raise ValueError("Valuein CIK is invalid")
    return digits.zfill(10)


def _episode_field(episode: object, name: str) -> object:
    if isinstance(episode, Mapping):
        return _required(episode, name)
    value = getattr(episode, name, None)
    if value is None:
        raise ValueError(f"P1 episode is missing {name}")
    return value


@dataclass(frozen=True, slots=True)
class ValueinIdentityDecision:
    episode_id: str
    ticker: str
    episode_valid_from: date
    episode_valid_to: date
    classification: IdentityClassification
    candidates: tuple[Mapping[str, Any], ...]
    membership_intervals: tuple[Mapping[str, Any], ...]
    candidate_ciks: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "ticker": self.ticker,
            "episode_valid_from": self.episode_valid_from.isoformat(),
            "episode_valid_to": self.episode_valid_to.isoformat(),
            "classification": self.classification,
            "candidate_count": len(self.candidates),
            "candidate_ciks": list(self.candidate_ciks),
            "candidates": [dict(row) for row in self.candidates],
            "membership_intervals": [dict(row) for row in self.membership_intervals],
            "reason": self.reason,
        }


def classify_valuein_identity(
    episode: object,
    security_rows: Iterable[Mapping[str, Any]],
    membership_rows: Iterable[Mapping[str, Any]],
    *,
    accepted_cik: str | None = None,
) -> ValueinIdentityDecision:
    """Classify exact-symbol historical rows without creating binding authority."""

    episode_id = str(_episode_field(episode, "episode_id"))
    ticker = str(_episode_field(episode, "normalized_ticker")).strip().upper()
    episode_from = _iso_date(_episode_field(episode, "valid_from"), "valid_from")
    episode_to = _iso_date(_episode_field(episode, "valid_to"), "valid_to")
    if episode_from >= episode_to:
        raise ValueError("P1 episode interval is empty")

    candidates: list[Mapping[str, Any]] = []
    for row in security_rows:
        if str(row.get("symbol") or "").strip().upper() != ticker:
            continue
        start = date.min if _missing(row.get("valid_from")) else _iso_date(row["valid_from"], "valid_from")
        end = date.max if _missing(row.get("valid_to")) else _iso_date(row["valid_to"], "valid_to")
        if start <= episode_to and episode_from <= end:
            candidates.append(row)

    if not candidates:
        return ValueinIdentityDecision(
            episode_id, ticker, episode_from, episode_to, "NO_MATCH", (), (), (),
            "no exact-symbol historical Valuein security interval overlaps the P1 episode",
        )

    identities: set[tuple[str, str, str]] = set()
    invalid_identity = False
    for row in candidates:
        try:
            identities.add(
                (
                    str(_required(row, "security_id")),
                    str(_required(row, "entity_id")),
                    _cik(_required(row, "cik")),
                )
            )
        except ValueError:
            invalid_identity = True
    candidate_ciks = tuple(sorted({identity[2] for identity in identities}))
    relevant_membership = tuple(
        row
        for row in membership_rows
        if not _missing(row.get("cik")) and _cik(row["cik"]) in candidate_ciks
    )

    normalized_accepted = _cik(accepted_cik) if accepted_cik is not None else None
    if invalid_identity or (normalized_accepted and candidate_ciks != (normalized_accepted,)):
        classification: IdentityClassification = "CONFLICT"
        reason = "candidate identity is incomplete or conflicts with accepted episode authority"
    elif len(identities) != 1 or len(candidates) != 1:
        classification = "AMBIGUOUS"
        reason = "more than one security-level Valuein identity overlaps the episode"
    else:
        candidate = candidates[0]
        start = date.min if _missing(candidate.get("valid_from")) else _iso_date(candidate["valid_from"], "valid_from")
        end = date.max if _missing(candidate.get("valid_to")) else _iso_date(candidate["valid_to"], "valid_to")
        if start == episode_from and end == episode_to:
            classification = "EXACT"
            reason = "one security-level identity exactly matches the P1 episode interval"
        elif start <= episode_from and end >= episode_to:
            classification = "COMPATIBLE_CANDIDATE"
            reason = "one identity contains the episode but is not automatic binding authority"
        else:
            classification = "PARTIAL"
            reason = "one identity overlaps but does not contain the full P1 episode"

    return ValueinIdentityDecision(
        episode_id,
        ticker,
        episode_from,
        episode_to,
        classification,
        tuple(candidates),
        relevant_membership,
        candidate_ciks,
        reason,
    )


def admit_exact_valuein_binding(
    decision: ValueinIdentityDecision,
    *,
    authoritative_episodes: Iterable[object],
    episode: object,
    snapshot_identity: str,
) -> EpisodeSecCikBindingV1:
    """Admit only an exact, membership-consistent Valuein relation."""

    if len(snapshot_identity) != 64 or any(
        character not in "0123456789abcdef" for character in snapshot_identity
    ):
        raise ValueError("Valuein snapshot_identity must be an exact SHA-256")
    if decision.classification != "EXACT" or len(decision.candidates) != 1:
        raise ValueError("only an EXACT Valuein relation may be admitted")
    candidate = decision.candidates[0]
    cik = _cik(_required(candidate, "cik"))
    if decision.candidate_ciks != (cik,):
        raise ValueError("exact Valuein relation lacks one unambiguous CIK")
    supporting = []
    for row in decision.membership_intervals:
        start = date.min if _missing(row.get("effective_date")) else _iso_date(row["effective_date"], "effective_date")
        end = date.max if _missing(row.get("removal_date")) else _iso_date(row["removal_date"], "removal_date")
        if _cik(_required(row, "cik")) == cik and start <= decision.episode_valid_from and end >= decision.episode_valid_to:
            supporting.append(row)
    if not supporting:
        raise ValueError("exact Valuein relation lacks containing historical membership evidence")
    membership = sorted(
        supporting,
        key=lambda row: (
            str(row.get("effective_date") or ""),
            str(row.get("removal_date") or ""),
            str(row.get("source") or ""),
        ),
    )[0]
    provenance_hash = str(_episode_field(episode, "provenance_hash"))
    evidence = (
        f"P1_PROVENANCE:{provenance_hash}",
        f"VALUEIN_SNAPSHOT_SHA256:{snapshot_identity}",
        "VALUEIN_SECURITY:"
        f"{_required(candidate, 'security_id')}:{_required(candidate, 'entity_id')}:"
        f"{cik}:{decision.episode_valid_from.isoformat()}:{decision.episode_valid_to.isoformat()}",
        "VALUEIN_MEMBERSHIP:"
        f"{membership.get('source') or 'UNKNOWN'}:{cik}:"
        f"{membership.get('effective_date')}:{membership.get('removal_date')}",
    )
    return EpisodeSecCikBindingV1.admit(
        authoritative_episodes=authoritative_episodes,
        episode_id=decision.episode_id,
        cik=cik,
        valid_from=decision.episode_valid_from,
        valid_to=decision.episode_valid_to,
        binding_classification="PASS_EXACT",
        evidence_source_identities=evidence,
    )


__all__ = [
    "IdentityClassification",
    "ValueinIdentityDecision",
    "admit_exact_valuein_binding",
    "classify_valuein_identity",
]
