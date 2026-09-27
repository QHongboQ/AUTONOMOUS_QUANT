from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import exchange_calendars
import pandas as pd

MODULE_PATH = Path(__file__).parents[1] / "time_effective_roster_handoff.py"
SPEC = importlib.util.spec_from_file_location("time_effective_roster_handoff", MODULE_PATH)
assert SPEC and SPEC.loader
handoff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = handoff
SPEC.loader.exec_module(handoff)


def identity(number: int) -> str:
    return f"sha256:{number:064x}"


def member(number: int) -> object:
    return handoff.RosterMember(
        candidate_id=identity(number),
        authorization_evidence_id=identity(100 + number),
        recorder_id=f"fixture-recorder-{number}",
    )


def utc(day: int, hour: int = 0) -> datetime:
    return datetime(2024, 1, day, hour, tzinfo=timezone.utc)


def roster_sequence() -> tuple[object, ...]:
    members = {number: member(number) for number in range(1, 6)}
    first = handoff.build_roster(
        use_scope="TEST_FIXTURE_NOT_REAL_EVIDENCE",
        authorization_evidence_id=identity(301),
        evidence_cutoff=utc(1),
        effective_session=date(2024, 1, 2),
        supersedes_roster_id=None,
        members=[members[3], members[1], members[2]],
    )
    second = handoff.build_roster(
        use_scope="TEST_FIXTURE_NOT_REAL_EVIDENCE",
        authorization_evidence_id=identity(302),
        evidence_cutoff=utc(3),
        effective_session=date(2024, 1, 4),
        supersedes_roster_id=first.roster_id,
        members=[members[5], members[1], members[4], members[2], members[3]],
    )
    third = handoff.build_roster(
        use_scope="TEST_FIXTURE_NOT_REAL_EVIDENCE",
        authorization_evidence_id=identity(303),
        evidence_cutoff=utc(7, 23),
        effective_session=date(2024, 1, 8),
        supersedes_roster_id=second.roster_id,
        members=[members[5], members[4]],
    )
    return first, second, third


class TimeEffectiveRosterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sessions = exchange_calendars.get_calendar("XNYS").sessions_in_range(
            "2024-01-01", "2024-01-12"
        ).tz_localize(None)

    def test_member_contract_references_authorities_without_model_duplication(self) -> None:
        members = [member(number) for number in range(1, 6)]
        self.assertEqual(
            set(handoff.RosterMember.model_fields),
            {"candidate_id", "authorization_evidence_id", "recorder_id"},
        )
        self.assertEqual(len({item.candidate_id for item in members}), 5)

    def test_rfc8785_identity_is_deterministic_and_member_order_independent(self) -> None:
        first, _, _ = roster_sequence()
        reordered = handoff.build_roster(
            use_scope=first.use_scope,
            authorization_evidence_id=first.authorization_evidence_id,
            evidence_cutoff=first.evidence_cutoff,
            effective_session=first.effective_session,
            supersedes_roster_id=None,
            members=list(reversed(first.members)),
        )
        self.assertEqual(first.roster_id, reordered.roster_id)

    def test_member_or_effective_session_changes_identity(self) -> None:
        first, _, _ = roster_sequence()
        member_changed = handoff.build_roster(
            use_scope=first.use_scope,
            authorization_evidence_id=first.authorization_evidence_id,
            evidence_cutoff=first.evidence_cutoff,
            effective_session=first.effective_session,
            supersedes_roster_id=None,
            members=[member(1), member(2), member(4)],
        )
        session_changed = handoff.build_roster(
            use_scope=first.use_scope,
            authorization_evidence_id=first.authorization_evidence_id,
            evidence_cutoff=first.evidence_cutoff,
            effective_session=date(2024, 1, 3),
            supersedes_roster_id=None,
            members=first.members,
        )
        self.assertNotEqual(first.roster_id, member_changed.roster_id)
        self.assertNotEqual(first.roster_id, session_changed.roster_id)

        tampered = first.model_copy(update={"roster_id": identity(999)})
        with self.assertRaisesRegex(ValueError, "content identity mismatch"):
            handoff.select_effective_rosters(
                rosters=(tampered,),
                sessions=pd.DatetimeIndex(["2024-01-02"]),
                decision_cutoffs={pd.Timestamp("2024-01-02"): utc(2, 23)},
                xnys_sessions=self.sessions,
            )

    def test_exact_xnys_activation_and_no_backward_rewrite(self) -> None:
        rosters = roster_sequence()
        requested = pd.to_datetime(
            ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09"]
        )
        cutoffs = {session: utc(session.day, 23) for session in requested}
        selected = handoff.select_effective_rosters(
            rosters=rosters,
            sessions=requested,
            decision_cutoffs=cutoffs,
            xnys_sessions=self.sessions,
        )
        self.assertEqual([len(selected[item]) for item in requested], [3, 3, 5, 5, 2, 2])
        prefix = requested[:4]
        earlier = handoff.select_effective_rosters(
            rosters=rosters[:2],
            sessions=prefix,
            decision_cutoffs={item: cutoffs[item] for item in prefix},
            xnys_sessions=self.sessions,
        )
        self.assertEqual({key: selected[key] for key in prefix}, earlier)

    def test_authorized_after_cutoff_cannot_affect_that_session(self) -> None:
        first, second, _ = roster_sequence()
        late = handoff.build_roster(
            use_scope=second.use_scope,
            authorization_evidence_id=second.authorization_evidence_id,
            evidence_cutoff=utc(4, 23),
            effective_session=second.effective_session,
            supersedes_roster_id=first.roster_id,
            members=second.members,
        )
        requested = pd.to_datetime(["2024-01-04", "2024-01-05"])
        selected = handoff.select_effective_rosters(
            rosters=(first, late),
            sessions=requested,
            decision_cutoffs={requested[0]: utc(4, 20), requested[1]: utc(5, 20)},
            xnys_sessions=self.sessions,
        )
        self.assertEqual(len(selected[requested[0]]), 3)
        self.assertEqual(len(selected[requested[1]]), 5)

    def test_non_xnys_session_fails_closed(self) -> None:
        first, _, _ = roster_sequence()
        saturday = pd.Timestamp("2024-01-06")
        with self.assertRaisesRegex(ValueError, "not an XNYS session"):
            handoff.select_effective_rosters(
                rosters=(first,),
                sessions=pd.DatetimeIndex([saturday]),
                decision_cutoffs={saturday: utc(6, 23)},
                xnys_sessions=self.sessions,
            )

    def test_extra_fields_and_non_utc_cutoff_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "Extra inputs are not permitted"):
            handoff.RosterMember(
                candidate_id=identity(1),
                authorization_evidence_id=identity(101),
                recorder_id="fixture-recorder-1",
                online_status="online",
            )
        with self.assertRaisesRegex(ValueError, "timezone-aware UTC"):
            handoff.EffectiveRoster(
                roster_id=identity(401),
                use_scope="TEST_FIXTURE_NOT_REAL_EVIDENCE",
                authorization_evidence_id=identity(301),
                evidence_cutoff=datetime(2024, 1, 1),  # noqa: DTZ001 - rejection fixture
                effective_session=date(2024, 1, 2),
                supersedes_roster_id=None,
                members=(member(1), member(2)),
            )


if __name__ == "__main__":
    unittest.main()
