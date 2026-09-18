from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import seal_fixture  # noqa: E402


def dump(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class ShadowFixtureSealTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ric = self.root / "ric.pkl"
        self.pred = self.root / "pred.pkl"
        self.ric.write_bytes(b"upstream qlib ric")
        self.pred.write_bytes(b"upstream qlib prediction")
        self.paths = {
            name: self.root / f"{name}.json"
            for name in (
                "fixture_task_config",
                "qlib_identity",
                "history",
                "tag_report",
                "prediction_report",
                "sigana_report",
                "shadow_fixture",
                "zero_capital",
                "pre_epoch",
            )
        }
        self.policy_module = self.root / "policy.py"
        self.policy_schema = self.root / "schema.json"
        self.policy_config = self.root / "policy.json"
        self.policy_module.write_text("policy\n")
        self.policy_schema.write_text("{}\n")
        self.policy_config.write_text("{}\n")
        run_id = "run-1"
        dump(self.paths["fixture_task_config"], {"model": "LinearModel"})
        dump(
            self.paths["qlib_identity"],
            {
                "fixture_classification": seal_fixture.FIXTURE_CLASSIFICATION,
                "component_classes": {
                    "manager": "qlib.workflow.online.manager.OnlineManager",
                    "strategy": "qlib.workflow.online.strategy.RollingStrategy",
                    "rolling_gen": "qlib.workflow.task.gen.RollingGen",
                    "trainer": "qlib.model.trainer.TrainerR",
                    "online_tool": "qlib.workflow.online.utils.OnlineToolR",
                },
                "history_timepoint_count": 2,
                "historical_test_rows_accessed": 0,
                "sealed_oos_rows_accessed": 0,
            },
        )
        dump(self.paths["history"], {"history_timepoint_count": 2})
        dump(
            self.paths["tag_report"],
            {
                "online_recorder_count": 1,
                "offline_recorder_count": 1,
                "qlib_online_tag_is_p4_shadow_authority": False,
            },
        )
        dump(
            self.paths["prediction_report"],
            {"artifact_sha256": digest(self.pred.read_bytes())},
        )
        dump(
            self.paths["sigana_report"],
            {
                "aq_rankic_computation": False,
                "artifact_sha256": digest(self.ric.read_bytes()),
                "qlib_recorder_id": run_id,
                "mlflow_run_id": run_id,
            },
        )
        dump(
            self.paths["shadow_fixture"],
            {
                "contract_version": "ShadowEvidenceV2",
                "evidence_classification": seal_fixture.FIXTURE_CLASSIFICATION,
                "completion_status": "INCOMPLETE",
                "outcome_return_evidence_identity": None,
                "zero_capital_attestation": True,
                "qlib_experiment_id": "1",
                "qlib_recorder_id": run_id,
                "mlflow_experiment_id": "1",
                "mlflow_run_id": run_id,
                "prediction_evidence_identity": "sha256:" + digest(self.pred.read_bytes()),
                "dvc_reproducibility_identity": "sha256:" + "a" * 64,
            },
        )
        dump(
            self.paths["zero_capital"],
            {
                "contract_version": "ZeroCapitalAttestationV1",
                "fixture_classification": seal_fixture.FIXTURE_CLASSIFICATION,
                "backtest_executed": False,
                "broker_calls": 0,
                "capital_allocated": 0,
                "order_count": 0,
                "portfolio_strategy_executed": False,
                "zero_capital_attestation": True,
            },
        )
        dump(
            self.paths["pre_epoch"],
            {
                "production_policy_effective_epoch": "2026-10-01",
                "pre_epoch_production_decay_evaluation": "REJECTED",
            },
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self) -> dict[str, object]:
        return seal_fixture.validate_and_build_seal(
            **{f"{name}_path": path for name, path in self.paths.items()},
            ric_artifact_path=self.ric,
            prediction_artifact_path=self.pred,
            policy_module_path=self.policy_module,
            policy_schema_path=self.policy_schema,
            policy_config_path=self.policy_config,
        )

    def test_valid_fixture_builds_deterministic_seal(self) -> None:
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(first["stage_name"], seal_fixture.STAGE_NAME)
        self.assertTrue(first["zero_capital_shadow"])

    def test_tampered_rank_ic_fails_closed(self) -> None:
        self.ric.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SigAna"):
            self.build()

    def test_real_or_complete_shadow_fails_closed(self) -> None:
        value = json.loads(self.paths["shadow_fixture"].read_text())
        value["evidence_classification"] = "PROSPECTIVE_ZERO_CAPITAL_SHADOW"
        dump(self.paths["shadow_fixture"], value)
        with self.assertRaisesRegex(ValueError, "real Shadow"):
            self.build()

    def test_historical_test_access_fails_closed(self) -> None:
        value = json.loads(self.paths["qlib_identity"].read_text())
        value["historical_test_rows_accessed"] = 1
        dump(self.paths["qlib_identity"], value)
        with self.assertRaisesRegex(ValueError, "historical TEST"):
            self.build()


if __name__ == "__main__":
    unittest.main()
