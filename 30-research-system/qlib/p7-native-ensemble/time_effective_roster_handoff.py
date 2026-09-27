"""Thin daily-session roster handoff to the existing P7/Qlib boundary."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from itertools import pairwise
from typing import Annotated, Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

Sha256Identity = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
NonEmptyIdentity = Annotated[str, StringConstraints(min_length=1)]


class RosterMember(BaseModel):
    """References existing Candidate, authorization, and Recorder authorities."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: Sha256Identity
    authorization_evidence_id: Sha256Identity
    recorder_id: NonEmptyIdentity


class EffectiveRoster(BaseModel):
    """Immutable externally authorized roster for daily XNYS research."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    roster_id: Sha256Identity
    use_scope: NonEmptyIdentity
    authorization_evidence_id: Sha256Identity
    evidence_cutoff: datetime
    effective_session: date
    supersedes_roster_id: Sha256Identity | None
    members: tuple[RosterMember, ...]

    @field_validator("evidence_cutoff")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("evidence_cutoff must be timezone-aware UTC")
        return value.astimezone(timezone.utc)

    @field_validator("members")
    @classmethod
    def sort_unique_members(
        cls, value: tuple[RosterMember, ...]
    ) -> tuple[RosterMember, ...]:
        members = tuple(sorted(value, key=lambda member: member.candidate_id))
        identities = [member.candidate_id for member in members]
        if not members or len(identities) != len(set(identities)):
            raise ValueError("roster members must be nonempty and unique")
        return members


def _identity_projection(fields: Mapping[str, Any]) -> dict[str, Any]:
    members = sorted(fields["members"], key=lambda member: member["candidate_id"])
    return {
        "use_scope": fields["use_scope"],
        "authorization_evidence_id": fields["authorization_evidence_id"],
        "evidence_cutoff": fields["evidence_cutoff"].isoformat(),
        "effective_session": fields["effective_session"].isoformat(),
        "supersedes_roster_id": fields["supersedes_roster_id"],
        "members": members,
    }


def roster_content_identity(fields: Mapping[str, Any]) -> str:
    """Use the authorized RFC 8785 leaf for semantic identity."""

    import rfc8785

    if rfc8785.__version__ != "0.1.4":
        raise RuntimeError("rfc8785 runtime identity mismatch")
    return "sha256:" + hashlib.sha256(
        rfc8785.dumps(_identity_projection(fields))
    ).hexdigest()


def build_roster(**fields: Any) -> EffectiveRoster:
    """Create an RFC 8785 identity in the existing contract-authority runtime."""

    members = [
        member.model_dump(mode="json") if isinstance(member, RosterMember) else member
        for member in fields["members"]
    ]
    roster_id = roster_content_identity({**fields, "members": members})
    return EffectiveRoster(roster_id=roster_id, **fields)


def select_effective_rosters(
    *,
    rosters: Sequence[EffectiveRoster],
    sessions: pd.DatetimeIndex,
    decision_cutoffs: Mapping[pd.Timestamp, datetime],
    xnys_sessions: pd.DatetimeIndex,
) -> dict[pd.Timestamp, tuple[RosterMember, ...]]:
    """Select one authorized roster per validated XNYS daily session."""

    if not rosters:
        raise ValueError("at least one roster is required")
    for roster in rosters:
        fields = roster.model_dump(mode="python", exclude={"roster_id"})
        fields["members"] = [member.model_dump(mode="json") for member in roster.members]
        if roster.roster_id != roster_content_identity(fields):
            raise ValueError("roster content identity mismatch")
    if tuple(rosters) != tuple(sorted(rosters, key=lambda item: item.effective_session)):
        raise ValueError("rosters must be ordered by effective_session")
    for previous, current in pairwise(rosters):
        if current.effective_session <= previous.effective_session:
            raise ValueError("roster effective sessions must be strictly increasing")
        if current.supersedes_roster_id != previous.roster_id:
            raise ValueError("roster supersession chain is broken")

    calendar = pd.DatetimeIndex(xnys_sessions)
    requested = pd.DatetimeIndex(sessions)
    if calendar.tz is not None or requested.tz is not None:
        raise ValueError("XNYS and requested sessions must be naive labels")
    effective = pd.DatetimeIndex([roster.effective_session for roster in rosters])
    if not requested.isin(calendar).all() or not effective.isin(calendar).all():
        raise ValueError("session is not an XNYS session")

    selected: dict[pd.Timestamp, tuple[RosterMember, ...]] = {}
    for session in requested:
        cutoff = decision_cutoffs.get(session)
        if (
            cutoff is None
            or cutoff.tzinfo is None
            or cutoff.utcoffset() != timezone.utc.utcoffset(cutoff)
        ):
            raise ValueError("every session requires a timezone-aware UTC cutoff")
        eligible = [
            roster
            for roster in rosters
            if pd.Timestamp(roster.effective_session) <= session
            and roster.evidence_cutoff <= cutoff
        ]
        if not eligible:
            raise ValueError("no authorized roster is effective at the session cutoff")
        selected[session] = eligible[-1].members
    return selected


def combine_selected_roster_predictions(
    *,
    selected: Mapping[pd.Timestamp, tuple[RosterMember, ...]],
    predictions: Mapping[str, pd.DataFrame],
    runtime_ready_recorders: frozenset[str],
    eligible_index: pd.MultiIndex,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply a validated handoff through the existing Qlib-owned combiner."""

    from session_local_router import combine_session_local_nonconstant

    if list(eligible_index.names) != ["datetime", "instrument"]:
        raise ValueError("eligible index names must be datetime/instrument")
    if eligible_index.has_duplicates or not eligible_index.is_monotonic_increasing:
        raise ValueError("eligible index must be unique and sorted")

    outputs: list[pd.DataFrame] = []
    reports: list[dict[str, object]] = []
    for session in eligible_index.get_level_values("datetime").unique():
        members = selected.get(session)
        if members is None:
            raise ValueError("validated roster handoff is missing for session")
        inputs: dict[str, pd.DataFrame] = {}
        expected = eligible_index[eligible_index.get_level_values("datetime") == session]
        for member in members:
            if member.recorder_id not in runtime_ready_recorders:
                raise RuntimeError(
                    f"{member.candidate_id}: authorized member Recorder is not runtime-ready"
                )
            frame = predictions.get(member.candidate_id)
            if frame is None:
                raise ValueError(f"{member.candidate_id}: prediction input is missing")
            actual = frame.loc[frame.index.get_level_values("datetime") == session]
            if not actual.index.equals(expected):
                raise ValueError(
                    f"{member.candidate_id}: session prediction rows do not match eligibility"
                )
            inputs[member.candidate_id] = actual

        combined, qualification = combine_session_local_nonconstant(inputs)
        outputs.append(combined)
        reports.append(
            {
                "datetime": session,
                "authorized_member_count": len(members),
                "runtime_ready_member_count": len(inputs),
                "active_component_count": int(
                    qualification.iloc[0]["active_component_count"]
                ),
                "inactive_components": qualification.iloc[0]["inactive_components"],
            }
        )

    result = pd.concat(outputs)
    if not result.index.equals(eligible_index):
        raise RuntimeError("roster handoff changed eligible row identity or order")
    return result, pd.DataFrame.from_records(reports).set_index("datetime")
