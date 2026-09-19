"""Thin, fail-closed projection from native Valuein identity rows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
import math
from typing import Any

from aq_episode_sec_cik_binding import EpisodeSecCikBindingV1


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


def _security_id(row: Mapping[str, Any]) -> str:
    value = row.get("security_id")
    if _missing(value):
        value = row.get("id")
    if _missing(value) or str(value).strip() == "":
        raise ValueError("Valuein row is missing security_id")
    return str(value)


def _start(row: Mapping[str, Any], name: str) -> date:
    return _iso_date(_required(row, name), name)


def _end(row: Mapping[str, Any], name: str) -> date:
    value = row.get(name)
    return date.max if _missing(value) else _iso_date(value, name)


def _overlaps(
    left_from: date,
    left_to: date,
    right_from: date,
    right_to: date,
) -> bool:
    return left_from < right_to and right_from < left_to


def _contains(
    outer_from: date,
    outer_to: date,
    inner_from: date,
    inner_to: date,
) -> bool:
    return outer_from <= inner_from and outer_to >= inner_to


def _identity_part(value: object) -> str:
    return "NONE" if _missing(value) else str(value).strip() or "NONE"


def project_valuein_native_binding(
    episode: object,
    *,
    authoritative_episodes: Iterable[object],
    security_rows: Iterable[Mapping[str, Any]],
    entity_rows: Iterable[Mapping[str, Any]],
    membership_rows: Iterable[Mapping[str, Any]],
    reference_rows: Iterable[Mapping[str, Any]],
    snapshot_identity: str,
) -> EpisodeSecCikBindingV1:
    """Project one native Valuein identity or fail closed.

    P1 owns the episode boundary. Valuein must provide one containing security
    identity, its exact entity/reference relations, and containing membership
    evidence from ``index_membership`` where ``index_name == "SP500"``.
    """

    if len(snapshot_identity) != 64 or any(
        character not in "0123456789abcdef" for character in snapshot_identity
    ):
        raise ValueError("Valuein snapshot_identity must be an exact SHA-256")
    if str(_episode_field(episode, "resolution_state")) != "RESOLVED":
        raise ValueError("P1 episode must be RESOLVED")
    if str(_episode_field(episode, "index_id")) != "SP500":
        raise ValueError("P1 episode must belong to SP500")

    episode_id = str(_episode_field(episode, "episode_id"))
    ticker = str(_episode_field(episode, "normalized_ticker")).strip().upper()
    episode_from = _iso_date(_episode_field(episode, "valid_from"), "valid_from")
    episode_to = _iso_date(_episode_field(episode, "valid_to"), "valid_to")
    if episode_from >= episode_to:
        raise ValueError("P1 episode interval is empty")

    overlapping: list[Mapping[str, Any]] = []
    for row in security_rows:
        if str(row.get("symbol") or "").strip().upper() != ticker:
            continue
        valid_from = _start(row, "valid_from")
        valid_to = _end(row, "valid_to")
        if _overlaps(valid_from, valid_to, episode_from, episode_to):
            overlapping.append(row)
    if len(overlapping) != 1:
        raise ValueError("P1 ticker interval lacks one unambiguous Valuein security")

    security = overlapping[0]
    security_from = _start(security, "valid_from")
    security_to = _end(security, "valid_to")
    if not _contains(security_from, security_to, episode_from, episode_to):
        raise ValueError("Valuein security interval does not contain the P1 episode")
    security_id = _security_id(security)
    cik = _cik(_required(security, "entity_id"))
    if not _missing(security.get("cik")) and _cik(security["cik"]) != cik:
        raise ValueError("Valuein security CIK conflicts with entity_id")

    entities = [row for row in entity_rows if _cik(_required(row, "cik")) == cik]
    if len(entities) != 1:
        raise ValueError("Valuein security lacks one exact entity relation")

    references = [row for row in reference_rows if _security_id(row) == security_id]
    if len(references) != 1:
        raise ValueError("Valuein security lacks one exact references relation")
    reference = references[0]
    if _cik(_required(reference, "cik")) != cik:
        raise ValueError("Valuein references CIK conflicts with entity relation")

    containing_memberships: list[Mapping[str, Any]] = []
    for row in membership_rows:
        if str(row.get("index_name") or "") != "SP500":
            continue
        if str(row.get("source") or "").strip().lower() == "fund_holdings":
            continue
        if _cik(_required(row, "cik")) != cik:
            continue
        effective_date = _start(row, "effective_date")
        removal_date = _end(row, "removal_date")
        if _contains(effective_date, removal_date, episode_from, episode_to):
            containing_memberships.append(row)
    if not containing_memberships:
        raise ValueError("Valuein identity lacks containing SP500 membership evidence")

    provenance_hash = str(_episode_field(episode, "provenance_hash"))
    evidence = [
        f"P1_PROVENANCE:{provenance_hash}",
        f"VALUEIN_SNAPSHOT_SHA256:{snapshot_identity}",
        "VALUEIN_SECURITY:"
        f"{security_id}:{cik}:{security_from.isoformat()}:"
        f"{None if security_to == date.max else security_to.isoformat()}:"
        f"{_identity_part(security.get('exchange'))}",
        f"VALUEIN_ENTITY:{cik}",
        "VALUEIN_REFERENCE:"
        f"{security_id}:{cik}:{_identity_part(reference.get('figi'))}:"
        f"{_identity_part(reference.get('composite_figi'))}:"
        f"{_identity_part(reference.get('share_class_figi'))}",
    ]
    for membership in containing_memberships:
        effective_date = _start(membership, "effective_date")
        removal_date = _end(membership, "removal_date")
        membership_id = _identity_part(membership.get("id"))
        source = _identity_part(membership.get("source"))
        evidence.append(
            "VALUEIN_SP500_MEMBERSHIP:"
            f"{membership_id}:{source}:{cik}:{effective_date.isoformat()}:"
            f"{None if removal_date == date.max else removal_date.isoformat()}"
        )
    evidence_identities = tuple(dict.fromkeys(sorted(evidence)))

    exact_membership = any(
        _start(row, "effective_date") == episode_from
        and _end(row, "removal_date") == episode_to
        for row in containing_memberships
    )
    classification = (
        "PASS_EXACT"
        if security_from == episode_from
        and security_to == episode_to
        and exact_membership
        else "PASS_CORROBORATED"
    )
    return EpisodeSecCikBindingV1.admit(
        authoritative_episodes=authoritative_episodes,
        episode_id=episode_id,
        cik=cik,
        valid_from=episode_from,
        valid_to=episode_to,
        binding_classification=classification,
        evidence_source_identities=evidence_identities,
    )


__all__ = ["project_valuein_native_binding"]
