"""Thin, fail-closed projection from native Valuein identity rows."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping
from datetime import date, datetime
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


def _episode_identity(episode: object) -> tuple[str, str, date, date, str]:
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
    provenance_hash = str(_episode_field(episode, "provenance_hash"))
    return episode_id, ticker, episode_from, episode_to, provenance_hash


def _validated_relation(
    security: Mapping[str, Any],
    *,
    entity_rows: tuple[Mapping[str, Any], ...],
    reference_rows: tuple[Mapping[str, Any], ...],
) -> tuple[str, str, Mapping[str, Any]]:
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
    return security_id, cik, reference


def _membership_evidence(
    membership: Mapping[str, Any], *, successor_cik: str | None = None
) -> str:
    effective_date = _start(membership, "effective_date")
    removal_date = _end(membership, "removal_date")
    identity = (
        "VALUEIN_SP500_MEMBERSHIP:"
        f"{_identity_part(membership.get('id'))}:"
        f"{_identity_part(membership.get('source'))}:"
        f"{_cik(_required(membership, 'cik'))}:{effective_date.isoformat()}:"
        f"{None if removal_date == date.max else removal_date.isoformat()}"
    )
    if successor_cik is not None:
        identity += f":SUCCESSOR_CIK:{successor_cik}"
    return identity


def _security_evidence(
    security: Mapping[str, Any],
    *,
    cik: str,
    reference: Mapping[str, Any],
) -> tuple[str, str]:
    security_id = _security_id(security)
    security_from = _start(security, "valid_from")
    security_to = _end(security, "valid_to")
    return (
        (
            "VALUEIN_SECURITY:"
            f"{security_id}:{cik}:{security_from.isoformat()}:"
            f"{None if security_to == date.max else security_to.isoformat()}:"
            f"{_identity_part(security.get('exchange'))}"
        ),
        (
            "VALUEIN_REFERENCE:"
            f"{security_id}:{cik}:{_identity_part(reference.get('figi'))}:"
            f"{_identity_part(reference.get('composite_figi'))}:"
            f"{_identity_part(reference.get('share_class_figi'))}"
        ),
    )


def _validated_xnys_sessions(
    sessions: Iterable[object] | None,
    *,
    episode_from: date,
    episode_to: date,
) -> tuple[date, ...] | None:
    if sessions is None:
        return None
    parsed = tuple(_iso_date(value, "XNYS session") for value in sessions)
    if tuple(sorted(set(parsed))) != parsed:
        raise ValueError("XNYS sessions must be sorted and unique")
    if any(value < episode_from or value >= episode_to for value in parsed):
        raise ValueError("XNYS sessions must be contained by the P1 episode")
    return parsed


def _session_set_identity(sessions: tuple[date, ...]) -> str:
    digest = hashlib.sha256(
        "\n".join(value.isoformat() for value in sessions).encode("ascii")
    ).hexdigest()
    return f"XNYS_EPISODE_SESSIONS_SHA256:{digest}"


def _project_single_security(
    episode: object,
    *,
    authoritative_episodes: Iterable[object],
    security: Mapping[str, Any],
    entity_rows: tuple[Mapping[str, Any], ...],
    membership_rows: tuple[Mapping[str, Any], ...],
    reference_rows: tuple[Mapping[str, Any], ...],
    snapshot_identity: str,
    xnys_sessions: tuple[date, ...] | None,
) -> EpisodeSecCikBindingV1:
    episode_id, _, episode_from, episode_to, provenance_hash = _episode_identity(
        episode
    )
    security_from = _start(security, "valid_from")
    security_to = _end(security, "valid_to")
    security_id, cik, reference = _validated_relation(
        security, entity_rows=entity_rows, reference_rows=reference_rows
    )
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

    boundary_evidence: list[str] = []
    if not _contains(security_from, security_to, episode_from, episode_to):
        if xnys_sessions is None:
            raise ValueError("Valuein security interval does not contain the P1 episode")
        uncovered = [
            session
            for session in xnys_sessions
            if not (security_from <= session < security_to)
        ]
        if uncovered:
            raise ValueError("Valuein security interval leaves an eligible XNYS session gap")
        boundary_evidence.extend(
            (
                _session_set_identity(xnys_sessions),
                (
                    "VALUEIN_ZERO_XNYS_SESSION_GAP:"
                    f"{security_id}:{security_from.isoformat()}:"
                    f"{security_to.isoformat()}:{episode_from.isoformat()}:"
                    f"{episode_to.isoformat()}"
                ),
            )
        )

    security_identity, reference_identity = _security_evidence(
        security, cik=cik, reference=reference
    )
    evidence = [
        f"P1_PROVENANCE:{provenance_hash}",
        f"VALUEIN_SNAPSHOT_SHA256:{snapshot_identity}",
        security_identity,
        f"VALUEIN_ENTITY:{cik}",
        reference_identity,
        *(_membership_evidence(row) for row in containing_memberships),
        *boundary_evidence,
    ]
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


def _project_explicit_successor_pair(
    episode: object,
    *,
    authoritative_episodes: Iterable[object],
    securities: tuple[Mapping[str, Any], Mapping[str, Any]],
    entity_rows: tuple[Mapping[str, Any], ...],
    membership_rows: tuple[Mapping[str, Any], ...],
    reference_rows: tuple[Mapping[str, Any], ...],
    snapshot_identity: str,
) -> tuple[EpisodeSecCikBindingV1, EpisodeSecCikBindingV1]:
    episode_id, _, episode_from, episode_to, provenance_hash = _episode_identity(
        episode
    )
    ordered = tuple(sorted(securities, key=lambda row: _start(row, "valid_from")))
    first, second = ordered
    first_from, first_to = _start(first, "valid_from"), _end(first, "valid_to")
    second_from, second_to = _start(second, "valid_from"), _end(second, "valid_to")
    if not (
        first_from <= episode_from
        and first_to == second_from
        and episode_from < first_to < episode_to
        and second_to >= episode_to
    ):
        raise ValueError("P1 ticker interval lacks one unambiguous Valuein security")
    first_id, first_cik, first_reference = _validated_relation(
        first, entity_rows=entity_rows, reference_rows=reference_rows
    )
    second_id, second_cik, second_reference = _validated_relation(
        second, entity_rows=entity_rows, reference_rows=reference_rows
    )
    if first_cik == second_cik:
        raise ValueError("Valuein successor relation must change exact CIK")

    successor_memberships = []
    for row in membership_rows:
        if str(row.get("index_name") or "") != "SP500":
            continue
        if str(row.get("source") or "").strip().lower() == "fund_holdings":
            continue
        if _cik(_required(row, "cik")) != first_cik:
            continue
        successor = row.get("successor_cik")
        if _missing(successor) or _cik(successor) != second_cik:
            continue
        if (
            _start(row, "effective_date") <= episode_from
            and _end(row, "removal_date") == first_to
        ):
            successor_memberships.append(row)
    if len(successor_memberships) != 1:
        raise ValueError("Valuein identity lacks one explicit SP500 successor_cik relation")
    membership = successor_memberships[0]
    membership_identity = _membership_evidence(
        membership, successor_cik=second_cik
    )
    shared = [
        f"P1_PROVENANCE:{provenance_hash}",
        f"VALUEIN_SNAPSHOT_SHA256:{snapshot_identity}",
        membership_identity,
        f"VALUEIN_EXPLICIT_SUCCESSOR_PAIR:{first_id}:{first_cik}:{second_id}:{second_cik}:{first_to.isoformat()}",
    ]
    bindings = []
    for security, security_id, cik, reference, valid_from, valid_to in (
        (first, first_id, first_cik, first_reference, episode_from, first_to),
        (second, second_id, second_cik, second_reference, second_from, episode_to),
    ):
        security_identity, reference_identity = _security_evidence(
            security, cik=cik, reference=reference
        )
        evidence = tuple(
            dict.fromkeys(
                sorted(
                    [
                        *shared,
                        security_identity,
                        f"VALUEIN_ENTITY:{cik}",
                        reference_identity,
                    ]
                )
            )
        )
        bindings.append(
            EpisodeSecCikBindingV1.admit(
                authoritative_episodes=authoritative_episodes,
                episode_id=episode_id,
                cik=cik,
                valid_from=valid_from,
                valid_to=valid_to,
                binding_classification="PASS_CORROBORATED",
                evidence_source_identities=evidence,
            )
        )
    return bindings[0], bindings[1]


def project_valuein_native_bindings(
    episode: object,
    *,
    authoritative_episodes: Iterable[object],
    security_rows: Iterable[Mapping[str, Any]],
    entity_rows: Iterable[Mapping[str, Any]],
    membership_rows: Iterable[Mapping[str, Any]],
    reference_rows: Iterable[Mapping[str, Any]],
    snapshot_identity: str,
    xnys_sessions: Iterable[object] | None = None,
) -> tuple[EpisodeSecCikBindingV1, ...]:
    """Project a native Valuein binding set or fail closed.

    The ordinary path preserves one containing security identity. A terminal
    boundary difference is admissible only when an authoritative XNYS session
    set proves zero uncovered sessions. Exactly two subintervals are admissible
    only when Valuein supplies one explicit ``successor_cik`` relation.
    """

    if len(snapshot_identity) != 64 or any(
        character not in "0123456789abcdef" for character in snapshot_identity
    ):
        raise ValueError("Valuein snapshot_identity must be an exact SHA-256")
    _, ticker, episode_from, episode_to, _ = _episode_identity(episode)
    entities = tuple(entity_rows)
    memberships = tuple(membership_rows)
    references = tuple(reference_rows)
    sessions = _validated_xnys_sessions(
        xnys_sessions, episode_from=episode_from, episode_to=episode_to
    )

    overlapping: list[Mapping[str, Any]] = []
    for row in security_rows:
        if str(row.get("symbol") or "").strip().upper() != ticker:
            continue
        valid_from = _start(row, "valid_from")
        valid_to = _end(row, "valid_to")
        if _overlaps(valid_from, valid_to, episode_from, episode_to):
            overlapping.append(row)
    if len(overlapping) == 1:
        return (
            _project_single_security(
                episode,
                authoritative_episodes=authoritative_episodes,
                security=overlapping[0],
                entity_rows=entities,
                membership_rows=memberships,
                reference_rows=references,
                snapshot_identity=snapshot_identity,
                xnys_sessions=sessions,
            ),
        )
    if len(overlapping) == 2:
        return _project_explicit_successor_pair(
            episode,
            authoritative_episodes=authoritative_episodes,
            securities=(overlapping[0], overlapping[1]),
            entity_rows=entities,
            membership_rows=memberships,
            reference_rows=references,
            snapshot_identity=snapshot_identity,
        )
    raise ValueError("P1 ticker interval lacks one unambiguous Valuein security")


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
    """Preserve the original singular projection contract."""

    bindings = project_valuein_native_bindings(
        episode,
        authoritative_episodes=authoritative_episodes,
        security_rows=security_rows,
        entity_rows=entity_rows,
        membership_rows=membership_rows,
        reference_rows=reference_rows,
        snapshot_identity=snapshot_identity,
    )
    if len(bindings) != 1:
        raise ValueError("P1 ticker interval lacks one unambiguous Valuein security")
    return bindings[0]


__all__ = ["project_valuein_native_binding", "project_valuein_native_bindings"]
