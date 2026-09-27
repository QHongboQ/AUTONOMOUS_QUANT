from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

MODULE_PATH = Path(__file__).parents[1] / "time_effective_roster_handoff.py"
sys.path.insert(0, str(MODULE_PATH.parent))
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


def fixture_inputs() -> tuple[
    dict[pd.Timestamp, tuple[object, ...]],
    dict[str, pd.DataFrame],
    frozenset[str],
    pd.MultiIndex,
]:
    members = {number: member(number) for number in range(1, 6)}
    sessions = pd.to_datetime(
        ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09"]
    )
    selected = {
        sessions[0]: (members[1], members[2], members[3]),
        sessions[1]: (members[1], members[2], members[3]),
        sessions[2]: tuple(members.values()),
        sessions[3]: tuple(members.values()),
        sessions[4]: (members[4], members[5]),
        sessions[5]: (members[4], members[5]),
    }
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
    ready = frozenset(f"fixture-recorder-{number}" for number in range(1, 6))
    return selected, predictions, ready, eligible


class TimeEffectiveRosterHandoffTests(unittest.TestCase):
    def test_three_five_two_sequence(self) -> None:
        selected, predictions, ready, eligible = fixture_inputs()
        result, report = handoff.combine_selected_roster_predictions(
            selected=selected,
            predictions=predictions,
            runtime_ready_recorders=ready,
            eligible_index=eligible,
        )
        self.assertTrue(result.index.equals(eligible))
        self.assertEqual(report["authorized_member_count"].tolist(), [3, 3, 5, 5, 2, 2])

    def test_authorized_but_runtime_not_ready_is_distinct(self) -> None:
        selected, predictions, ready, eligible = fixture_inputs()
        baseline, _ = handoff.combine_selected_roster_predictions(
            selected=selected,
            predictions=predictions,
            runtime_ready_recorders=ready,
            eligible_index=eligible,
        )
        extra = dict(predictions)
        extra[identity(6)] = pd.DataFrame({"score": [9.0] * len(eligible)}, index=eligible)
        with_ready_nonmember, _ = handoff.combine_selected_roster_predictions(
            selected=selected,
            predictions=extra,
            runtime_ready_recorders=ready | {"fixture-recorder-6"},
            eligible_index=eligible,
        )
        assert_frame_equal(baseline, with_ready_nonmember)
        with self.assertRaisesRegex(RuntimeError, "authorized member Recorder is not runtime-ready"):
            handoff.combine_selected_roster_predictions(
                selected=selected,
                predictions=predictions,
                runtime_ready_recorders=ready - {"fixture-recorder-2"},
                eligible_index=eligible,
            )

    def test_missing_nonfinite_and_row_mismatch_fail_closed(self) -> None:
        selected, predictions, ready, eligible = fixture_inputs()
        missing = dict(predictions)
        missing.pop(identity(2))
        with self.assertRaisesRegex(ValueError, "prediction input is missing"):
            handoff.combine_selected_roster_predictions(
                selected=selected,
                predictions=missing,
                runtime_ready_recorders=ready,
                eligible_index=eligible,
            )

        nonfinite = {name: frame.copy() for name, frame in predictions.items()}
        nonfinite[identity(2)].iloc[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "missing or non-finite"):
            handoff.combine_selected_roster_predictions(
                selected=selected,
                predictions=nonfinite,
                runtime_ready_recorders=ready,
                eligible_index=eligible,
            )

        misaligned = {name: frame.copy() for name, frame in predictions.items()}
        misaligned[identity(2)] = misaligned[identity(2)].drop(
            index=(pd.Timestamp("2024-01-02"), "C")
        )
        with self.assertRaisesRegex(ValueError, "do not match eligibility"):
            handoff.combine_selected_roster_predictions(
                selected=selected,
                predictions=misaligned,
                runtime_ready_recorders=ready,
                eligible_index=eligible,
            )

    def test_constant_policy_and_minimum_active_gate(self) -> None:
        selected, predictions, ready, eligible = fixture_inputs()
        one_constant = {name: frame.copy() for name, frame in predictions.items()}
        first = pd.Timestamp("2024-01-02")
        mask = one_constant[identity(3)].index.get_level_values("datetime") == first
        one_constant[identity(3)].loc[mask, "score"] = 7.5
        _, report = handoff.combine_selected_roster_predictions(
            selected=selected,
            predictions=one_constant,
            runtime_ready_recorders=ready,
            eligible_index=eligible,
        )
        self.assertEqual(report.iloc[0]["active_component_count"], 2)

        insufficient = {name: frame.copy() for name, frame in predictions.items()}
        last = pd.Timestamp("2024-01-09")
        for number in (4, 5):
            mask = insufficient[identity(number)].index.get_level_values("datetime") == last
            insufficient[identity(number)].loc[mask, "score"] = float(number)
        with self.assertRaisesRegex(ValueError, "fewer than two active components"):
            handoff.combine_selected_roster_predictions(
                selected=selected,
                predictions=insufficient,
                runtime_ready_recorders=ready,
                eligible_index=eligible,
            )

    def test_replay_and_prior_prefix_are_deterministic(self) -> None:
        selected, predictions, ready, eligible = fixture_inputs()
        first, first_report = handoff.combine_selected_roster_predictions(
            selected=selected,
            predictions=predictions,
            runtime_ready_recorders=ready,
            eligible_index=eligible,
        )
        second, second_report = handoff.combine_selected_roster_predictions(
            selected=selected,
            predictions=predictions,
            runtime_ready_recorders=ready,
            eligible_index=eligible,
        )
        assert_frame_equal(first, second)
        assert_frame_equal(first_report, second_report)
        prefix = eligible[eligible.get_level_values("datetime") < pd.Timestamp("2024-01-08")]
        earlier, _ = handoff.combine_selected_roster_predictions(
            selected={key: value for key, value in selected.items() if key < pd.Timestamp("2024-01-08")},
            predictions=predictions,
            runtime_ready_recorders=ready,
            eligible_index=prefix,
        )
        assert_frame_equal(first.loc[prefix], earlier)


if __name__ == "__main__":
    unittest.main()
