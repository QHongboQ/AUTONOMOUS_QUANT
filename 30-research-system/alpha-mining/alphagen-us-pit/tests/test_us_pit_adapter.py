import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from alphagen.data.expression import Feature, Ref
from alphagen.models.linear_alpha_pool import MseAlphaPool
from alphagen.rl.env.wrapper import AlphaEnv, SIZE_OP
from alphagen_qlib.stock_data import FeatureType

from aq_alphagen_us_pit import (
    FEATURE_FIELDS,
    USPitAlphaCalculator,
    USPitDataView,
    VWAP_ACTION_INDEX,
    apply_feature_availability_mask,
    load_authoritative_target,
)
from aq_alphagen_us_pit.calculator import EXPECTED_TARGET_EXPRESSION
from aq_alphagen_us_pit.data_view import _covers_interval, _validate_time_bounds
from run_bounded_poc import select_bounded_instruments


def fixture_view() -> USPitDataView:
    backtrack, future, n_days, n_stocks = 5, 2, 8, 4
    rows = backtrack + n_days + future
    data = torch.empty((rows, 5, n_stocks), dtype=torch.float32)
    base = torch.arange(rows * n_stocks, dtype=torch.float32).reshape(rows, n_stocks) + 10
    for channel in range(5):
        data[:, channel, :] = base + channel * 1000
    return USPitDataView(
        data=data,
        dates=pd.date_range("2024-01-02", periods=rows, freq="B"),
        stock_ids=pd.Index([f"S{i}" for i in range(n_stocks)]),
        max_backtrack_days=backtrack,
        max_future_days=future,
        evaluation_start=pd.Timestamp("2024-01-09"),
        evaluation_end=pd.Timestamp("2024-01-18"),
    )


class USPitAdapterTests(unittest.TestCase):
    def test_feature_indices_map_exactly_to_ohlcv_channels(self):
        view = fixture_view()
        self.assertEqual([int(feature) for feature, _ in FEATURE_FIELDS], list(range(5)))
        self.assertNotIn(FeatureType.VWAP, [feature for feature, _ in FEATURE_FIELDS])
        for feature, _ in FEATURE_FIELDS:
            expected = view.data[
                view.max_backtrack_days : view.max_backtrack_days + view.n_days,
                int(feature),
                :,
            ]
            self.assertTrue(torch.equal(Feature(feature).evaluate(view), expected))

    def test_target_comes_from_frozen_protocol_and_aligns(self):
        view = fixture_view()
        authority = load_authoritative_target()
        self.assertEqual(authority.source_expression, EXPECTED_TARGET_EXPRESSION)
        self.assertEqual(authority.lookahead_sessions, 2)
        actual = authority.expression.evaluate(view)
        close = view.data[:, int(FeatureType.CLOSE), :]
        start = view.max_backtrack_days
        expected = close[start + 2 : start + 2 + view.n_days] / close[
            start + 1 : start + 1 + view.n_days
        ] - 1
        self.assertTrue(torch.allclose(actual, expected))

    def test_protocol_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "protocol.json"
            path.write_text(
                json.dumps(
                    {
                        "protocol_version": "P2_CERTIFICATION_PROTOCOL_V1",
                        "label_temporal_policy": {
                            "expression": "Ref($close, -1)/$close - 1",
                            "effective_lookahead_sessions": 1,
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_authoritative_target(path)

    def test_membership_requires_one_date_valid_interval(self):
        intervals = [(pd.Timestamp("2024-01-02"), pd.Timestamp("2024-03-28"))]
        self.assertTrue(
            _covers_interval(intervals, pd.Timestamp("2024-01-02"), pd.Timestamp("2024-03-28"))
        )
        self.assertFalse(
            _covers_interval(intervals, pd.Timestamp("2023-12-29"), pd.Timestamp("2024-03-28"))
        )

    def test_sealed_oos_is_rejected_before_provider_access(self):
        with self.assertRaises(ValueError):
            _validate_time_bounds(pd.Timestamp("2026-09-11"), pd.Timestamp("2026-09-14"))

    def test_non_vwap_expression_fixture(self):
        view = fixture_view()
        expression = Ref(Feature(FeatureType.CLOSE), 5)
        actual = expression.evaluate(view)
        expected = view.data[: view.n_days, int(FeatureType.CLOSE), :]
        self.assertTrue(torch.equal(actual, expected))

    def test_action_mask_changes_only_vwap(self):
        view = fixture_view()
        calculator = USPitAlphaCalculator(view, load_authoritative_target().expression)
        pool = MseAlphaPool(capacity=2, calculator=calculator, device=torch.device("cpu"))
        base_env = AlphaEnv(pool=pool, device=torch.device("cpu"))
        masked_env = apply_feature_availability_mask(base_env)
        masked_env.reset()
        self.assertEqual(VWAP_ACTION_INDEX, SIZE_OP + int(FeatureType.VWAP))
        for action in [None, SIZE_OP + int(FeatureType.CLOSE), 0]:
            upstream = base_env.action_masks().copy()
            effective = masked_env.action_masks()
            self.assertEqual(len(effective), base_env.action_space.n)
            self.assertFalse(effective[VWAP_ACTION_INDEX])
            diff = np.flatnonzero(upstream != effective)
            self.assertLessEqual(len(diff), 1)
            self.assertTrue(all(index == VWAP_ACTION_INDEX for index in diff))
            if action is not None and upstream[action]:
                base_env.step(action)

    def test_poc_subset_selection_is_sorted_and_deterministic(self):
        candidates = ["NYS:Z", "NAS:A", "NYS:B"]
        self.assertEqual(select_bounded_instruments(candidates, 2), ["NAS:A", "NYS:B"])
        self.assertEqual(
            select_bounded_instruments(list(reversed(candidates)), 2),
            ["NAS:A", "NYS:B"],
        )

    def test_module_boundaries_import_without_cycle(self):
        from aq_alphagen_us_pit import calculator, data_view, feature_mask, runner

        self.assertIsNotNone(calculator.USPitAlphaCalculator)
        self.assertIsNotNone(data_view.USPitDataView)
        self.assertIsNotNone(feature_mask.unavailable_feature_action_mask)
        self.assertIsNotNone(runner.run_alphagen)


if __name__ == "__main__":
    unittest.main()
