from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal
from qlib.model.ens.ensemble import AverageEnsemble


MODULE_PATH = Path(__file__).parents[1] / "average_ensemble_boundary.py"
SPEC = importlib.util.spec_from_file_location("average_ensemble_boundary", MODULE_PATH)
assert SPEC and SPEC.loader
boundary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(boundary)


def complete_components() -> dict[str, pd.DataFrame]:
    index = pd.MultiIndex.from_product(
        [pd.to_datetime(["2024-01-02", "2024-01-03"]), ["A", "B", "C"]],
        names=["datetime", "instrument"],
    )
    return {
        "alpha": pd.DataFrame({"score": [1.0, 2.0, 3.0, 3.0, 1.0, 2.0]}, index=index),
        "beta": pd.DataFrame({"score": [1.0, 3.0, 2.0, 2.0, 1.0, 3.0]}, index=index),
    }


class AverageEnsembleBoundaryTests(unittest.TestCase):
    def test_complete_inputs_match_hand_calculation(self) -> None:
        components = complete_components()
        actual = boundary.combine_complete_predictions(components)
        expected = pd.DataFrame(
            {"score": [-1.0, 0.5, 0.5, 0.5, -1.0, 0.5]},
            index=components["alpha"].index,
        )
        assert_frame_equal(actual, expected)

    def test_repeatability_order_and_input_immutability(self) -> None:
        components = complete_components()
        before = copy.deepcopy(components)
        first = boundary.combine_complete_predictions(components)
        second = boundary.combine_complete_predictions(components)
        reversed_result = boundary.combine_complete_predictions(dict(reversed(components.items())))
        assert_frame_equal(first, second)
        assert_frame_equal(first, reversed_result)
        for name in components:
            assert_frame_equal(components[name], before[name])

    def test_mismatched_row_identities_fail_closed(self) -> None:
        components = complete_components()
        components["beta"] = components["beta"].iloc[:-1]
        with self.assertRaisesRegex(ValueError, "row identities"):
            boundary.combine_complete_predictions(components)

    def test_duplicate_keys_fail_closed(self) -> None:
        components = complete_components()
        duplicate = pd.concat([components["beta"], components["beta"].iloc[[0]]]).sort_index()
        components["beta"] = duplicate
        with self.assertRaisesRegex(ValueError, "duplicate"):
            boundary.combine_complete_predictions(components)

    def test_missing_and_nonfinite_scores_fail_closed(self) -> None:
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(value=value):
                components = complete_components()
                components["beta"].iloc[0, 0] = value
                with self.assertRaisesRegex(ValueError, "missing or non-finite"):
                    boundary.combine_complete_predictions(components)

    def test_constant_component_fails_closed(self) -> None:
        components = complete_components()
        components["beta"].loc[:, "score"] = 1.0
        with self.assertRaisesRegex(ValueError, "constant cross-sectional"):
            boundary.combine_complete_predictions(components)

    def test_insufficient_instruments_fail_closed(self) -> None:
        components = complete_components()
        for name in components:
            components[name] = components[name].loc[(slice(None), ["A"]), :]
        with self.assertRaisesRegex(ValueError, "at least two instruments"):
            boundary.combine_complete_predictions(components)

    def test_unsupported_columns_and_index_fail_closed(self) -> None:
        components = complete_components()
        components["beta"] = components["beta"].assign(extra=1.0)
        with self.assertRaisesRegex(ValueError, "exactly one column"):
            boundary.combine_complete_predictions(components)

        components = complete_components()
        components["beta"] = components["beta"].reset_index(drop=True)
        with self.assertRaisesRegex(ValueError, "MultiIndex"):
            boundary.combine_complete_predictions(components)

    def test_native_return_type_and_name_are_characterized(self) -> None:
        result = AverageEnsemble()(complete_components())
        self.assertIsInstance(result, pd.Series)
        self.assertIsNone(result.name)

    def test_native_incomplete_inputs_use_union_and_skip_missing_component(self) -> None:
        components = complete_components()
        incomplete = dict(components)
        incomplete["beta"] = incomplete["beta"].iloc[1:]
        result = AverageEnsemble()(incomplete)
        self.assertTrue(result.index.equals(components["alpha"].index))
        self.assertTrue(np.isfinite(result.iloc[0]))

    def test_native_nested_dictionary_is_flattened(self) -> None:
        components = complete_components()
        flat = AverageEnsemble()(components)
        nested = AverageEnsemble()({"group": components})
        assert_series_equal(flat, nested)


if __name__ == "__main__":
    unittest.main()
