import unittest

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
    authoritative_target,
    mask_vwap,
)


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
        selection_rule="fixture",
    )


class USPitAdapterTests(unittest.TestCase):
    def test_feature_indices_map_exactly_to_five_channels(self):
        view = fixture_view()
        self.assertEqual([int(feature) for feature, _ in FEATURE_FIELDS], list(range(5)))
        for feature, _ in FEATURE_FIELDS:
            expected = view.data[
                view.max_backtrack_days : view.max_backtrack_days + view.n_days,
                int(feature),
                :,
            ]
            actual = Feature(feature).evaluate(view)
            self.assertTrue(torch.equal(actual, expected))

    def test_authoritative_target_alignment(self):
        view = fixture_view()
        actual = authoritative_target().evaluate(view)
        close = view.data[:, int(FeatureType.CLOSE), :]
        start = view.max_backtrack_days
        expected = close[start + 2 : start + 2 + view.n_days] / close[
            start + 1 : start + 1 + view.n_days
        ] - 1
        self.assertTrue(torch.allclose(actual, expected))

    def test_non_vwap_expression_fixture(self):
        view = fixture_view()
        expression = Ref(Feature(FeatureType.CLOSE), 5)
        actual = expression.evaluate(view)
        expected = view.data[: view.n_days, int(FeatureType.CLOSE), :]
        self.assertTrue(torch.equal(actual, expected))

    def test_action_mask_changes_only_vwap(self):
        view = fixture_view()
        calculator = USPitAlphaCalculator(view, authoritative_target())
        pool = MseAlphaPool(capacity=2, calculator=calculator, device=torch.device("cpu"))
        base_env = AlphaEnv(pool=pool, device=torch.device("cpu"))
        masked_env = mask_vwap(base_env)
        masked_env.reset()
        self.assertEqual(VWAP_ACTION_INDEX, SIZE_OP + int(FeatureType.VWAP))

        for action in [None, SIZE_OP + int(FeatureType.CLOSE), 0]:
            base = base_env.action_masks().copy()
            masked = masked_env.action_masks()
            self.assertEqual(len(masked), base_env.action_space.n)
            self.assertFalse(masked[VWAP_ACTION_INDEX])
            diff = np.flatnonzero(base != masked)
            self.assertLessEqual(len(diff), 1)
            self.assertTrue(all(index == VWAP_ACTION_INDEX for index in diff))
            if action is not None and base[action]:
                base_env.step(action)


if __name__ == "__main__":
    unittest.main()
