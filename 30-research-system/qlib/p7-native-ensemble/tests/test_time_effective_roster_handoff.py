from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from qlib.workflow.online.utils import OnlineToolR

MODULE_PATH = Path(__file__).parents[1] / "time_effective_roster_handoff.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("time_effective_roster_handoff", MODULE_PATH)
assert SPEC and SPEC.loader
handoff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = handoff
SPEC.loader.exec_module(handoff)

FIXTURE = "TEST_FIXTURE_NOT_REAL_EVIDENCE"
MODEL_CLASS = "qlib.contrib.model.linear.LinearModel"


def identity(number: int) -> str:
    return f"sha256:{number:064x}"


def member(number: int) -> object:
    return handoff.RosterMember(
        candidate_id=identity(number),
        model_class=MODEL_CLASS,
        model_identity=identity(100 + number),
        recorder_identity=f"fixture-recorder-{number}",
        online_status=OnlineToolR.ONLINE_TAG,
        eligibility_evidence_identity=identity(200 + number),
        evidence_classification=FIXTURE,
    )


def utc(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=timezone.utc)


def fixtures() -> tuple[tuple[object, ...], dict[str, pd.DataFrame], pd.MultiIndex]:
    members = {number: member(number) for number in range(1, 6)}
    first = handoff.build_roster(
        roster_version="fixture-v1",
        use_scope="TEST_FIXTURE_RESEARCH_ONLY",
        authorization_evidence_identity=identity(301),
        evidence_cutoff=utc(1),
        effective_at=utc(2),
        supersedes_roster_id=None,
        members=[members[1], members[2], members[3]],
    )
    second = handoff.build_roster(
        roster_version="fixture-v2",
        use_scope="TEST_FIXTURE_RESEARCH_ONLY",
        authorization_evidence_identity=identity(302),
        evidence_cutoff=utc(3),
        effective_at=utc(4),
        supersedes_roster_id=first.roster_id,
        members=[members[1], members[2], members[3], members[4], members[5]],
    )
    third = handoff.build_roster(
        roster_version="fixture-v3",
        use_scope="TEST_FIXTURE_RESEARCH_ONLY",
        authorization_evidence_identity=identity(303),
        evidence_cutoff=utc(5),
        effective_at=utc(6),
        supersedes_roster_id=second.roster_id,
        members=[members[4], members[5]],
    )
    sessions = pd.to_datetime(
        ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07"]
    )
    eligible = pd.MultiIndex.from_product(
        [sessions, ["A", "B", "C"]], names=["datetime", "instrument"]
    )
    patterns = {
        1: [1.0, 2.0, 3.0],
        2: [3.0, 1.0, 2.0],
        3: [2.0, 3.0, 1.0],
        4: [1.0, 3.0, 2.0],
        5: [2.0, 1.0, 3.0],
    }
    active_sessions = {
        1: sessions[:4],
        2: sessions[:4],
        3: sessions[:4],
        4: sessions[2:],
        5: sessions[2:],
    }
    predictions = {}
    for number, dates in active_sessions.items():
        index = pd.MultiIndex.from_product(
            [dates, ["A", "B", "C"]], names=["datetime", "instrument"]
        )
        predictions[identity(number)] = pd.DataFrame(
            {"score": patterns[number] * len(dates)}, index=index
        )
    return (first, second, third), predictions, eligible


class TimeEffectiveRosterHandoffTests(unittest.TestCase):
    def test_three_five_two_sequence_and_boundaries(self) -> None:
        rosters, predictions, eligible = fixtures()
        result, report = handoff.combine_effective_roster_predictions(
            rosters=rosters, predictions=predictions, eligible_index=eligible
        )
        self.assertTrue(result.index.equals(eligible))
        self.assertEqual(report["effective_member_count"].tolist(), [3, 3, 5, 5, 2, 2])
        self.assertEqual(report["valid_prediction_member_count"].tolist(), [3, 3, 5, 5, 2, 2])
        self.assertEqual(
            report["roster_id"].tolist(),
            [rosters[0].roster_id] * 2 + [rosters[1].roster_id] * 2 + [rosters[2].roster_id] * 2,
        )

    def test_future_roster_does_not_rewrite_earlier_outputs(self) -> None:
        rosters, predictions, eligible = fixtures()
        full, _ = handoff.combine_effective_roster_predictions(
            rosters=rosters, predictions=predictions, eligible_index=eligible
        )
        prefix = eligible[eligible.get_level_values("datetime") < pd.Timestamp("2024-01-06")]
        earlier, _ = handoff.combine_effective_roster_predictions(
            rosters=rosters[:2], predictions=predictions, eligible_index=prefix
        )
        assert_frame_equal(full.loc[prefix], earlier)

    def test_same_model_class_retains_distinct_candidate_and_recorder_identities(self) -> None:
        rosters, _, _ = fixtures()
        members = rosters[1].members
        self.assertEqual(rosters[1].use_scope, "TEST_FIXTURE_RESEARCH_ONLY")
        self.assertEqual({item.model_class for item in members}, {MODEL_CLASS})
        self.assertEqual(len({item.candidate_id for item in members}), 5)
        self.assertEqual(len({item.model_identity for item in members}), 5)
        self.assertEqual(len({item.recorder_identity for item in members}), 5)
        self.assertEqual(
            {item.evidence_classification for item in members}, {FIXTURE}
        )

    def test_new_members_need_no_pre_entry_predictions(self) -> None:
        rosters, predictions, eligible = fixtures()
        for number in (4, 5):
            dates = predictions[identity(number)].index.get_level_values("datetime")
            self.assertGreaterEqual(dates.min(), pd.Timestamp("2024-01-04"))
        handoff.combine_effective_roster_predictions(
            rosters=rosters, predictions=predictions, eligible_index=eligible
        )

    def test_missing_and_nonfinite_inputs_fail_closed(self) -> None:
        rosters, predictions, eligible = fixtures()
        missing = dict(predictions)
        missing.pop(identity(2))
        with self.assertRaisesRegex(ValueError, "prediction input is missing"):
            handoff.combine_effective_roster_predictions(
                rosters=rosters, predictions=missing, eligible_index=eligible
            )

        nonfinite = {name: frame.copy() for name, frame in predictions.items()}
        nonfinite[identity(2)].iloc[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "missing or non-finite"):
            handoff.combine_effective_roster_predictions(
                rosters=rosters, predictions=nonfinite, eligible_index=eligible
            )

    def test_session_prediction_row_mismatch_fails_closed(self) -> None:
        rosters, predictions, eligible = fixtures()
        misaligned = {name: frame.copy() for name, frame in predictions.items()}
        misaligned[identity(2)] = misaligned[identity(2)].drop(
            index=(pd.Timestamp("2024-01-02"), "C")
        )
        with self.assertRaisesRegex(ValueError, "do not match eligibility"):
            handoff.combine_effective_roster_predictions(
                rosters=rosters, predictions=misaligned, eligible_index=eligible
            )

    def test_constant_policy_and_minimum_active_gate(self) -> None:
        rosters, predictions, eligible = fixtures()
        one_constant = {name: frame.copy() for name, frame in predictions.items()}
        first_session = pd.Timestamp("2024-01-02")
        mask = one_constant[identity(3)].index.get_level_values("datetime") == first_session
        one_constant[identity(3)].loc[mask, "score"] = 7.5
        _, report = handoff.combine_effective_roster_predictions(
            rosters=rosters, predictions=one_constant, eligible_index=eligible
        )
        self.assertEqual(report.iloc[0]["active_component_count"], 2)
        self.assertEqual(report.iloc[0]["inactive_components"], (identity(3),))

        insufficient = {name: frame.copy() for name, frame in predictions.items()}
        last_session = pd.Timestamp("2024-01-07")
        for number in (4, 5):
            mask = insufficient[identity(number)].index.get_level_values("datetime") == last_session
            insufficient[identity(number)].loc[mask, "score"] = float(number)
        with self.assertRaisesRegex(ValueError, "fewer than two active components"):
            handoff.combine_effective_roster_predictions(
                rosters=rosters, predictions=insufficient, eligible_index=eligible
            )

    def test_replay_is_deterministic(self) -> None:
        rosters, predictions, eligible = fixtures()
        first, first_report = handoff.combine_effective_roster_predictions(
            rosters=rosters, predictions=predictions, eligible_index=eligible
        )
        second, second_report = handoff.combine_effective_roster_predictions(
            rosters=rosters, predictions=predictions, eligible_index=eligible
        )
        assert_frame_equal(first, second)
        assert_frame_equal(first_report, second_report)

    def test_ambiguous_or_broken_roster_sequence_fails_closed(self) -> None:
        rosters, _, _ = fixtures()
        ambiguous = handoff.build_roster(
            roster_version="fixture-ambiguous",
            use_scope="TEST_FIXTURE_RESEARCH_ONLY",
            authorization_evidence_identity=identity(304),
            evidence_cutoff=utc(3),
            effective_at=utc(4),
            supersedes_roster_id=rosters[0].roster_id,
            members=rosters[0].members,
        )
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            handoff.validate_roster_sequence((rosters[0], rosters[1], ambiguous))


if __name__ == "__main__":
    unittest.main()
