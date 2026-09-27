"""Thin time-effective roster handoff to the existing P7/Qlib boundary."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import pairwise

import pandas as pd
from qlib.workflow.online.utils import OnlineToolR
from session_local_router import combine_session_local_nonconstant

TEST_EVIDENCE_CLASSIFICATION = "TEST_FIXTURE_NOT_REAL_EVIDENCE"
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def _require_identity(value: str, field: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be a sha256 identity")


@dataclass(frozen=True)
class RosterMember:
    """References identity and eligibility owned outside P7."""

    candidate_id: str
    model_class: str
    model_identity: str
    recorder_identity: str
    online_status: str
    eligibility_evidence_identity: str
    evidence_classification: str

    def __post_init__(self) -> None:
        _require_identity(self.candidate_id, "candidate_id")
        _require_identity(self.model_identity, "model_identity")
        _require_identity(
            self.eligibility_evidence_identity, "eligibility_evidence_identity"
        )
        if not self.model_class or not self.recorder_identity:
            raise ValueError("model class and Recorder identity are required")
        if self.online_status != OnlineToolR.ONLINE_TAG:
            raise ValueError("roster members must reference an upstream online Recorder")
        if not self.evidence_classification:
            raise ValueError("eligibility evidence classification is required")


@dataclass(frozen=True)
class EffectiveRoster:
    """One immutable, externally authorized roster version."""

    roster_id: str
    roster_version: str
    use_scope: str
    authorization_evidence_identity: str
    evidence_cutoff: datetime
    effective_at: datetime
    supersedes_roster_id: str | None
    members: tuple[RosterMember, ...]

    def __post_init__(self) -> None:
        _require_identity(self.roster_id, "roster_id")
        _require_identity(
            self.authorization_evidence_identity, "authorization_evidence_identity"
        )
        if self.supersedes_roster_id is not None:
            _require_identity(self.supersedes_roster_id, "supersedes_roster_id")
        if not self.roster_version or not self.use_scope:
            raise ValueError("roster version and use scope are required")
        if not self.members:
            raise ValueError("roster must contain at least one member")
        if (
            self.evidence_cutoff.tzinfo != timezone.utc
            or self.effective_at.tzinfo != timezone.utc
        ):
            raise ValueError("roster times must be UTC")
        if self.evidence_cutoff > self.effective_at:
            raise ValueError("roster evidence cutoff is after its effective time")
        candidate_ids = tuple(member.candidate_id for member in self.members)
        if candidate_ids != tuple(sorted(candidate_ids)):
            raise ValueError("roster members must be sorted by Candidate identity")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("roster contains duplicate Candidate identities")
        if self.roster_id != roster_content_identity(self):
            raise ValueError("roster content identity mismatch")


def _identity_projection(roster: EffectiveRoster) -> dict[str, object]:
    return {
        "roster_version": roster.roster_version,
        "use_scope": roster.use_scope,
        "authorization_evidence_identity": roster.authorization_evidence_identity,
        "evidence_cutoff": roster.evidence_cutoff.isoformat(),
        "effective_at": roster.effective_at.isoformat(),
        "supersedes_roster_id": roster.supersedes_roster_id,
        "members": [asdict(member) for member in roster.members],
    }


def roster_content_identity(roster: EffectiveRoster) -> str:
    """Hash the narrow immutable handoff projection; this is not a registry."""

    canonical = json.dumps(
        _identity_projection(roster), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def build_roster(
    *,
    roster_version: str,
    use_scope: str,
    authorization_evidence_identity: str,
    evidence_cutoff: datetime,
    effective_at: datetime,
    supersedes_roster_id: str | None,
    members: Iterable[RosterMember],
) -> EffectiveRoster:
    """Build one roster after sorting its externally identified members."""

    member_tuple = tuple(sorted(members, key=lambda member: member.candidate_id))
    projection = {
        "roster_version": roster_version,
        "use_scope": use_scope,
        "authorization_evidence_identity": authorization_evidence_identity,
        "evidence_cutoff": evidence_cutoff.isoformat(),
        "effective_at": effective_at.isoformat(),
        "supersedes_roster_id": supersedes_roster_id,
        "members": [asdict(member) for member in member_tuple],
    }
    canonical = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    identity = "sha256:" + hashlib.sha256(canonical).hexdigest()
    return EffectiveRoster(
        roster_id=identity,
        roster_version=roster_version,
        use_scope=use_scope,
        authorization_evidence_identity=authorization_evidence_identity,
        evidence_cutoff=evidence_cutoff,
        effective_at=effective_at,
        supersedes_roster_id=supersedes_roster_id,
        members=member_tuple,
    )


def validate_roster_sequence(
    rosters: Iterable[EffectiveRoster],
) -> tuple[EffectiveRoster, ...]:
    """Require an unambiguous, strictly ordered immutable supersession chain."""

    sequence = tuple(rosters)
    if not sequence:
        raise ValueError("at least one roster is required")
    if sequence != tuple(sorted(sequence, key=lambda roster: roster.effective_at)):
        raise ValueError("rosters must be ordered by effective time")
    for previous, current in pairwise(sequence):
        if current.effective_at <= previous.effective_at:
            raise ValueError("roster effective times must be strictly increasing")
        if current.supersedes_roster_id != previous.roster_id:
            raise ValueError("roster supersession chain is broken")
    return sequence


def roster_at(
    rosters: Iterable[EffectiveRoster], decision_time: datetime
) -> EffectiveRoster:
    """Select the one already-known and effective roster at a decision time."""

    if decision_time.tzinfo != timezone.utc:
        raise ValueError("decision time must be UTC")
    sequence = validate_roster_sequence(rosters)
    eligible = [
        roster
        for roster in sequence
        if roster.evidence_cutoff <= decision_time and roster.effective_at <= decision_time
    ]
    if not eligible:
        raise ValueError("no roster is known and effective at the decision time")
    return eligible[-1]


def combine_effective_roster_predictions(
    *,
    rosters: Iterable[EffectiveRoster],
    predictions: Mapping[str, pd.DataFrame],
    eligible_index: pd.MultiIndex,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Route each eligible session through its authorized roster and Qlib."""

    sequence = validate_roster_sequence(rosters)
    if list(eligible_index.names) != ["datetime", "instrument"]:
        raise ValueError("eligible index names must be datetime/instrument")
    if eligible_index.has_duplicates or not eligible_index.is_monotonic_increasing:
        raise ValueError("eligible index must be unique and sorted")

    outputs: list[pd.DataFrame] = []
    reports: list[dict[str, object]] = []
    sessions = eligible_index.get_level_values("datetime").unique()
    for session in sessions:
        decision_time = pd.Timestamp(session).to_pydatetime().replace(tzinfo=timezone.utc)
        roster = roster_at(sequence, decision_time)
        expected = eligible_index[eligible_index.get_level_values("datetime") == session]
        selected: dict[str, pd.DataFrame] = {}
        for member in roster.members:
            frame = predictions.get(member.candidate_id)
            if frame is None:
                raise ValueError(f"{member.candidate_id}: prediction input is missing")
            actual = frame.loc[frame.index.get_level_values("datetime") == session]
            if not actual.index.equals(expected):
                raise ValueError(
                    f"{member.candidate_id}: session prediction rows do not match eligibility"
                )
            selected[member.candidate_id] = actual

        combined, qualification = combine_session_local_nonconstant(selected)
        outputs.append(combined)
        reports.append(
            {
                "datetime": session,
                "roster_id": roster.roster_id,
                "roster_version": roster.roster_version,
                "effective_member_count": len(roster.members),
                "valid_prediction_member_count": len(selected),
                "active_component_count": int(
                    qualification.iloc[0]["active_component_count"]
                ),
                "inactive_components": qualification.iloc[0]["inactive_components"],
                "combined_has_ranking_information": bool(
                    qualification.iloc[0]["combined_has_ranking_information"]
                ),
            }
        )

    result = pd.concat(outputs)
    if not result.index.equals(eligible_index):
        raise RuntimeError("roster handoff changed eligible row identity or order")
    return result, pd.DataFrame.from_records(reports).set_index("datetime")
