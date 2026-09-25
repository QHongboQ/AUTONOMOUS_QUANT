from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
REPO = ROOT.parents[2]
PROTOCOL = json.loads((ROOT / "macro-v1-ablation-protocol.json").read_text(encoding="utf-8"))
EVALUATOR = REPO / "30-research-system" / "qlib" / "p5-h1-evaluation" / "evaluate_h1.py"
MACRO_FEATURES = ["macro_v1_cpiaucsl_d2_log", "macro_v1_unrate_d1"]


def canonical_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


class ProtocolTests(unittest.TestCase):
    def test_exact_scientific_inventory_and_surfaces(self):
        inventory = PROTOCOL["scientific_inventory"]
        self.assertEqual(inventory["hypothesis_count"], 1)
        self.assertEqual(inventory["primary_surface_comparison_count"], 1)
        self.assertEqual(inventory["planned_model_fit_count"], 2)
        self.assertEqual([item["id"] for item in PROTOCOL["surfaces"]], ["M0", "M1"])
        self.assertEqual(PROTOCOL["surfaces"][0]["identity"], "BASE_157")
        self.assertEqual(PROTOCOL["surfaces"][0]["increment_features"], [])
        self.assertEqual(PROTOCOL["surfaces"][1]["increment_features"], MACRO_FEATURES)
        self.assertEqual(PROTOCOL["macro_input_authority"]["feature_ids"], MACRO_FEATURES)
        self.assertEqual(PROTOCOL["control"]["feature_column_count"], 157)
        self.assertEqual(PROTOCOL["control"]["feature_manifest_sha256"],
                         "7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463")
        self.assertEqual(PROTOCOL["control"]["dataset_identity"],
                         "P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135")
        self.assertFalse(PROTOCOL["control"]["p5_fundamentals_included"])
        self.assertTrue(all(PROTOCOL["excluded_feature_families"].values()))
        row_policy = PROTOCOL["row_identity_policy"]
        self.assertTrue(all(row_policy[key] for key in (
            "m0_m1_datetime_rows_equal", "m0_m1_instruments_equal",
            "m0_m1_membership_episode_identity_equal", "m0_m1_labels_equal",
            "m0_m1_splits_equal",
        )))
        self.assertEqual(row_policy["instrument_dependent_macro_value_count_required"], 0)
        self.assertEqual(row_policy["manufactured_instrument_session_row_count_required"], 0)

    def test_exact_splits_label_and_processors(self):
        self.assertEqual(PROTOCOL["splits"], {
            "train": ["2015-04-01", "2019-12-31"],
            "validation": ["2020-01-01", "2021-12-31"],
            "historical_research_test": ["2022-01-03", "2024-12-31"],
        })
        policy = PROTOCOL["label_and_processors"]
        self.assertEqual(policy["label"], "Ref($close, -2)/Ref($close, -1) - 1")
        self.assertEqual([item["class"] for item in policy["learn_processors"]],
                         ["DropnaLabel", "CSZScoreNorm"])
        self.assertEqual(policy["shared_processors"], [])
        self.assertEqual(policy["infer_processors"], [])
        self.assertFalse(policy["feature_fillna_used"])
        self.assertFalse(policy["macro_extra_normalization"])

    def test_model_config_matches_authoritative_p5_vehicle(self):
        spec = importlib.util.spec_from_file_location("p5_h1_authority", EVALUATOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(PROTOCOL["model"]["config"], module.MODEL_CONFIG)
        self.assertEqual(PROTOCOL["model"]["config_sha256"], canonical_sha(module.MODEL_CONFIG))
        self.assertEqual(PROTOCOL["model"]["config_sha256"],
                         "f75355629e7ad6b85f100627dbc055712d7f72d1e1e31783736f1ce4cc10a61a")
        self.assertEqual(PROTOCOL["upstream_identities"], {
            "qlib_version": "0.9.8.dev26",
            "qlib_source_sha": "2fb9380b342556ddb50a4b24e4fe8655d548b2b8",
            "lightgbm_version": "4.7.0", "skfolio_version": "1.0.6",
            "arch_version": "8.0.0",
        })
        self.assertFalse(PROTOCOL["model"]["config_changed"])
        self.assertFalse(PROTOCOL["model"]["hyperparameter_search"])

    def test_strategy_temporal_and_arch_policies(self):
        self.assertEqual(PROTOCOL["portfolio"], {
            "strategy": "TopkDropoutStrategy", "topk": 30, "n_drop": 3,
            "open_cost": 0.0005, "close_cost": 0.0015, "deal_price": "close",
            "m0_m1_assumptions_equal": True,
        })
        wf = PROTOCOL["walkforward"]
        self.assertEqual((wf["test_size"], wf["train_size"], wf["purged_size"]), (63, 504, 2))
        self.assertFalse(wf["expand_train"] or wf["reduce_test"])
        cpcv = PROTOCOL["cpcv"]
        self.assertEqual((cpcv["n_folds"], cpcv["n_test_folds"], cpcv["purged_size"],
                          cpcv["embargo_size"]), (10, 2, 2, 2))
        arch = PROTOCOL["arch_tests"]
        self.assertEqual((arch["bootstrap"], arch["block_size"], arch["reps"],
                          arch["seed"], arch["alpha"]), ("stationary", 10, 5000, 20260913, 0.05))

    def test_classification_and_safety_are_complete(self):
        self.assertEqual(set(PROTOCOL["classifications"]), {
            "INCREMENTAL_VALUE_SUPPORTED", "DEGRADED",
            "NO_MEASURABLE_INCREMENTAL_VALUE", "INCONCLUSIVE",
        })
        for name, rule in PROTOCOL["classifications"].items():
            self.assertTrue(rule.get("all_required") or rule.get("any_required"), name)
            self.assertIn("retention", rule)
        closed = PROTOCOL["post_result_policy"]["NO_MEASURABLE_INCREMENTAL_VALUE"]
        self.assertTrue(closed["macro_v1_question_closed"])
        self.assertFalse(closed["add_more_macro_series"])
        self.assertFalse(closed["try_alternate_transformations"])
        self.assertFalse(closed["add_GDP_or_GDPC1"])
        self.assertFalse(closed["tune_lags"])
        self.assertEqual(PROTOCOL["prediction_metric"]["primary"], "QLIB_RANK_IC")
        self.assertEqual(PROTOCOL["prediction_metric"]["delta"],
                         "M1_TEST_RANK_IC - M0_TEST_RANK_IC")
        safety = PROTOCOL["safety"]
        self.assertEqual(sum(safety[key] for key in (
            "model_training_count", "prediction_count", "backtest_count", "ablation_count",
            "new_production_loc", "aq_new_generic_engine_count",
        )), 0)
        self.assertFalse(safety["p2_v2_sealed_oos_accessed"])
        self.assertFalse(safety["p2_v2_sealed_oos_result_used"])


if __name__ == "__main__":
    unittest.main()
