import json
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import torch

from alphagen.data.expression import Feature, Ref
from alphagen.models.linear_alpha_pool import MseAlphaPool
from alphagen.rl.env.wrapper import AlphaEnv, SIZE_OP
from alphagen.utils.correlation import batch_pearsonr, batch_spearmanr
from alphagen.utils.pytorch_utils import normalize_by_day
from alphagen_qlib.stock_data import FeatureType

from aq_alphagen_us_pit import (
    FAST_CONFIG_ID,
    FEATURE_FIELDS,
    USPitAlphaCalculator,
    USPitDataView,
    VWAP_ACTION_INDEX,
    apply_feature_availability_mask,
    assert_research_window,
    load_authoritative_target,
    make_lstsq_fast_config,
    resolve_effective_partition,
)
from aq_alphagen_us_pit.calculator import EXPECTED_TARGET_EXPRESSION
from aq_alphagen_us_pit.calculator import _normalize_preserving_missing
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
        membership_mask=torch.ones((rows, n_stocks), dtype=torch.bool),
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

    def test_off_membership_and_provider_gap_nan_survive_normalization(self):
        raw = torch.tensor(
            [[1.0, 2.0, float("nan")], [3.0, float("nan"), 5.0]],
            dtype=torch.float32,
        )
        normalized = _normalize_preserving_missing(raw)
        self.assertTrue(torch.isnan(normalized[0, 2]))
        self.assertTrue(torch.isnan(normalized[1, 1]))

    def test_valid_normalized_values_match_upstream(self):
        raw = torch.tensor(
            [[1.0, 2.0, float("nan"), 4.0], [2.0, 4.0, 6.0, 8.0]],
            dtype=torch.float32,
        )
        expected = normalize_by_day(raw)
        actual = _normalize_preserving_missing(raw)
        valid = ~torch.isnan(raw)
        self.assertTrue(torch.allclose(actual[valid], expected[valid]))

    def test_upstream_correlations_ignore_restored_nan(self):
        factor = torch.tensor([[1.0, 2.0, float("nan"), 4.0]], dtype=torch.float32)
        target = torch.tensor([[2.0, 4.0, float("nan"), 8.0]], dtype=torch.float32)
        normalized_factor = _normalize_preserving_missing(factor)
        normalized_target = _normalize_preserving_missing(target)
        self.assertAlmostEqual(
            float(batch_pearsonr(normalized_factor, normalized_target)[0]), 1.0, places=6
        )
        self.assertAlmostEqual(
            float(batch_spearmanr(normalized_factor, normalized_target)[0]), 1.0, places=6
        )

    def test_all_nan_identity_does_not_change_valid_identity_ic(self):
        factor = torch.tensor([[1.0, 2.0, 4.0], [4.0, 2.0, 1.0]], dtype=torch.float32)
        target = factor * 2
        baseline = batch_pearsonr(
            _normalize_preserving_missing(factor),
            _normalize_preserving_missing(target),
        )
        missing_column = torch.full((factor.shape[0], 1), torch.nan)
        expanded = batch_pearsonr(
            _normalize_preserving_missing(torch.cat([factor, missing_column], dim=1)),
            _normalize_preserving_missing(torch.cat([target, missing_column], dim=1)),
        )
        self.assertTrue(torch.allclose(baseline, expanded))

    def test_dynamic_membership_missingness_never_becomes_zero(self):
        raw = torch.tensor(
            [[1.0, float("nan"), 3.0], [float("nan"), 2.0, 4.0]],
            dtype=torch.float32,
        )
        normalized = _normalize_preserving_missing(raw)
        self.assertTrue(torch.isnan(normalized[0, 1]))
        self.assertTrue(torch.isnan(normalized[1, 0]))
        self.assertFalse(bool((normalized[torch.isnan(raw)] == 0).any()))

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

    def test_partition_purge_keeps_two_session_label_in_partition(self):
        calendar = pd.DatetimeIndex(
            pd.to_datetime(
                [
                    "2019-12-26",
                    "2019-12-27",
                    "2019-12-30",
                    "2019-12-31",
                    "2020-01-02",
                ]
            )
        )
        start, end = resolve_effective_partition(
            calendar,
            pd.Timestamp("2019-12-26"),
            pd.Timestamp("2019-12-31"),
            2,
        )
        self.assertEqual(start, pd.Timestamp("2019-12-26"))
        self.assertEqual(end, pd.Timestamp("2019-12-27"))

    def test_historical_test_access_guard(self):
        with self.assertRaises(ValueError):
            assert_research_window(
                pd.Timestamp("2021-12-31"), pd.Timestamp("2022-01-03")
            )

    def test_official_lstsq_fast_config_preserves_fixed_research_parameters(self):
        config = make_lstsq_fast_config(seed=999, total_timesteps=8192)
        self.assertEqual(FAST_CONFIG_ID, "ALPHAGEN_MSE_LSTSQ_FAST_V1")
        self.assertEqual(config.pool_capacity, 20)
        self.assertEqual(config.l1_alpha, 0.0)
        self.assertEqual(config.n_steps, 2048)
        self.assertEqual(config.batch_size, 128)
        self.assertEqual(config.gamma, 1.0)
        self.assertEqual(config.entropy_coefficient, 0.01)
        self.assertEqual(config.lstm_layers, 2)
        self.assertEqual(config.lstm_model_dim, 128)
        self.assertEqual(config.lstm_dropout, 0.1)

    def test_upstream_lstsq_fast_path_matches_numpy(self):
        class ObservedMseAlphaPool(MseAlphaPool):
            lstsq_calls = 0

            def _optimize_lstsq(self):
                self.lstsq_calls += 1
                return super()._optimize_lstsq()

        pool = ObservedMseAlphaPool(
            capacity=2,
            calculator=mock.Mock(),
            l1_alpha=0.0,
            device=torch.device("cpu"),
        )
        pool.size = 2
        pool.single_ics[:2] = np.array([0.04, 0.02])
        pool._mutual_ics[:2, :2] = np.array([[1.0, 0.25], [0.25, 1.0]])
        pool._weights[:2] = np.array([0.5, 0.5])
        expected = np.linalg.lstsq(
            pool._mutual_ics[:2, :2], pool.single_ics[:2], rcond=-1
        )[0]
        actual = pool.optimize()
        self.assertEqual(pool.lstsq_calls, 1)
        self.assertTrue(np.allclose(actual, expected))
        source = inspect.getsource(MseAlphaPool.optimize)
        self.assertIn("math.isclose(alpha, 0.)", source)
        self.assertIn("return self._optimize_lstsq()", source)


if __name__ == "__main__":
    unittest.main()
