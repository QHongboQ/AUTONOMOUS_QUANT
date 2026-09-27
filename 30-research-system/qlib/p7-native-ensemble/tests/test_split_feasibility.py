from __future__ import annotations

import unittest

import numpy as np
from skfolio.model_selection import CombinatorialPurgedCV, WalkForward


class SyntheticSplitFeasibilityTests(unittest.TestCase):
    def test_walkforward_yields_only_complete_nonempty_test_folds(self) -> None:
        values = np.arange(700, dtype=float).reshape(-1, 1)
        splitter = WalkForward(
            test_size=63,
            train_size=504,
            purged_size=2,
            expand_train=False,
            reduce_test=False,
        )
        splits = list(splitter.split(values))
        self.assertEqual(len(splits), 3)
        self.assertTrue(all(len(train) == 504 and len(test) == 63 for train, test in splits))
        self.assertTrue(all(test[0] - train[-1] == 3 for train, test in splits))

    def test_minimum_guard_does_not_guarantee_a_complete_test_fold(self) -> None:
        values = np.arange(568, dtype=float).reshape(-1, 1)
        splitter = WalkForward(
            test_size=63,
            train_size=504,
            purged_size=2,
            expand_train=False,
            reduce_test=False,
        )
        self.assertEqual(list(splitter.split(values)), [])

    def test_historical_385_observations_are_rejected_without_reopening_finsen(self) -> None:
        values = np.arange(385, dtype=float).reshape(-1, 1)
        splitter = WalkForward(test_size=63, train_size=504, purged_size=2, reduce_test=False)
        with self.assertRaises(ValueError):
            list(splitter.split(values))

    def test_cpcv_accounts_for_purge_embargo_and_nonempty_test_folds(self) -> None:
        values = np.arange(100, dtype=float).reshape(-1, 1)
        splitter = CombinatorialPurgedCV(
            n_folds=10,
            n_test_folds=2,
            purged_size=2,
            embargo_size=2,
        )
        splits = list(splitter.split(values))
        self.assertEqual(len(splits), 45)
        self.assertTrue(all(len(test_folds) == 2 for _, test_folds in splits))
        self.assertTrue(all(len(test) == 10 for _, test_folds in splits for test in test_folds))
        self.assertGreaterEqual(min(len(train) for train, _ in splits), 68)


if __name__ == "__main__":
    unittest.main()
