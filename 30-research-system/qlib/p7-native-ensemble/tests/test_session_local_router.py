from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

MODULE_PATH = Path(__file__).parents[1] / "session_local_router.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("session_local_router", MODULE_PATH)
assert SPEC and SPEC.loader
router = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(router)


def frame(first: list[float], second: list[float]) -> pd.DataFrame:
    index = pd.MultiIndex.from_product(
        [pd.to_datetime(["2024-01-02", "2024-01-03"]), ["A", "B", "C"]],
        names=["datetime", "instrument"],
    )
    return pd.DataFrame({"score": first + second}, index=index)


class SessionLocalRouterTests(unittest.TestCase):
    def test_constant_component_is_inactive_only_on_that_session(self) -> None:
        predictions = {
            "constant_then_active": frame([7.5, 7.5, 7.5], [1.0, 2.0, 3.0]),
            "alpha": frame([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]),
            "beta": frame([3.0, 1.0, 2.0], [3.0, 2.0, 1.0]),
        }
        result, report = router.combine_session_local_nonconstant(predictions)
        self.assertTrue(result.index.equals(predictions["alpha"].index))
        self.assertEqual(report["active_component_count"].tolist(), [2, 3])
        self.assertEqual(report.iloc[0]["inactive_components"], ("constant_then_active",))
        self.assertEqual(report.iloc[1]["inactive_components"], ())

    def test_exact_nonzero_constant_is_inactive_without_threshold(self) -> None:
        predictions = {
            "constant": frame([1e-300, 1e-300, 1e-300], [4.0, 4.0, 4.0]),
            "alpha": frame([1.0, 2.0, 3.0], [2.0, 3.0, 1.0]),
            "beta": frame([3.0, 1.0, 2.0], [3.0, 1.0, 2.0]),
        }
        _, report = router.combine_session_local_nonconstant(predictions)
        self.assertEqual(report["active_component_count"].tolist(), [2, 2])

    def test_missing_and_nonfinite_values_remain_errors(self) -> None:
        for invalid in (np.nan, np.inf, -np.inf):
            with self.subTest(invalid=invalid):
                predictions = {
                    "invalid": frame([invalid, invalid, invalid], [1.0, 2.0, 3.0]),
                    "alpha": frame([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]),
                    "beta": frame([3.0, 1.0, 2.0], [3.0, 2.0, 1.0]),
                }
                with self.assertRaisesRegex(ValueError, "missing or non-finite"):
                    router.combine_session_local_nonconstant(predictions)

    def test_numeric_failure_is_not_reclassified_as_inactive(self) -> None:
        predictions = {
            "large": frame([8e307, 9e307, 1e308], [8e307, 9e307, 1e308]),
            "alpha": frame([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]),
            "beta": frame([3.0, 1.0, 2.0], [3.0, 2.0, 1.0]),
        }
        with self.assertRaisesRegex(ValueError, "non-finite standardization mean"):
            router.combine_session_local_nonconstant(predictions)

    def test_fewer_than_two_active_components_fails_closed(self) -> None:
        predictions = {
            "constant_a": frame([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]),
            "constant_b": frame([2.0, 2.0, 2.0], [3.0, 2.0, 1.0]),
            "active": frame([1.0, 2.0, 3.0], [2.0, 3.0, 1.0]),
        }
        with self.assertRaisesRegex(ValueError, "fewer than two active components"):
            router.combine_session_local_nonconstant(predictions)

    def test_row_order_and_determinism_are_exact(self) -> None:
        predictions = {
            "alpha": frame([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]),
            "beta": frame([3.0, 1.0, 2.0], [3.0, 2.0, 1.0]),
        }
        first, first_report = router.combine_session_local_nonconstant(predictions)
        second, second_report = router.combine_session_local_nonconstant(predictions)
        assert_frame_equal(first, second)
        assert_frame_equal(first_report, second_report)
        self.assertTrue(first.index.equals(predictions["alpha"].index))

    def test_flat_active_mapping_matches_existing_strict_boundary(self) -> None:
        predictions = {
            "constant": frame([8.0, 8.0, 8.0], [7.0, 7.0, 7.0]),
            "alpha": frame([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]),
            "beta": frame([3.0, 1.0, 2.0], [3.0, 2.0, 1.0]),
        }
        actual, _ = router.combine_session_local_nonconstant(predictions)
        expected, _ = router.combine_session_local_nonconstant(
            {"alpha": predictions["alpha"], "beta": predictions["beta"]}
        )
        assert_frame_equal(actual, expected)

    def test_cancelling_components_report_constant_combined_output(self) -> None:
        predictions = {
            "alpha": frame([1.0, 2.0, 3.0], [3.0, 1.0, 2.0]),
            "negative_alpha": frame([-1.0, -2.0, -3.0], [-3.0, -1.0, -2.0]),
        }
        result, report = router.combine_session_local_nonconstant(predictions)
        self.assertTrue((result["score"] == 0.0).all())
        self.assertEqual(report["combined_has_ranking_information"].tolist(), [False, False])


if __name__ == "__main__":
    unittest.main()
