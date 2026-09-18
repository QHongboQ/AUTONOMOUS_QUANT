"""Validate the fixed P4 Shadow mechanism fixture and emit one DVC seal."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


STAGE_NAME = "p4_shadow_evidence_path_fixture_seal"
SEAL_VERSION = "P4ShadowEvidencePathDVCSealV1"
FIXTURE_CLASSIFICATION = "TEST_FIXTURE_NOT_REAL_SHADOW"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.resolve(strict=True).read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve(strict=True).read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def require_sha256(value: Any, field: str, *, prefixed: bool = False) -> str:
    if prefixed:
        if not isinstance(value, str) or not value.startswith("sha256:"):
            raise ValueError(f"{field} must be a prefixed SHA256 identity")
        value = value.removeprefix("sha256:")
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be lowercase SHA256")
    return value


def deterministic_json_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def validate_and_build_seal(
    *,
    fixture_task_config_path: Path,
    qlib_identity_path: Path,
    history_path: Path,
    tag_report_path: Path,
    prediction_report_path: Path,
    sigana_report_path: Path,
    shadow_fixture_path: Path,
    zero_capital_path: Path,
    pre_epoch_path: Path,
    ric_artifact_path: Path,
    prediction_artifact_path: Path,
    policy_module_path: Path,
    policy_schema_path: Path,
    policy_config_path: Path,
) -> dict[str, Any]:
    qlib_identity = load_json(qlib_identity_path)
    history = load_json(history_path)
    tags = load_json(tag_report_path)
    prediction = load_json(prediction_report_path)
    sigana = load_json(sigana_report_path)
    shadow = load_json(shadow_fixture_path)
    zero_capital = load_json(zero_capital_path)
    pre_epoch = load_json(pre_epoch_path)

    if qlib_identity.get("fixture_classification") != FIXTURE_CLASSIFICATION:
        raise ValueError("Qlib identity is not the approved fixture classification")
    required_components = {
        "manager": "qlib.workflow.online.manager.OnlineManager",
        "strategy": "qlib.workflow.online.strategy.RollingStrategy",
        "rolling_gen": "qlib.workflow.task.gen.RollingGen",
        "trainer": "qlib.model.trainer.TrainerR",
        "online_tool": "qlib.workflow.online.utils.OnlineToolR",
    }
    if qlib_identity.get("component_classes") != required_components:
        raise ValueError("Qlib online component ownership mismatch")
    if qlib_identity.get("history_timepoint_count", 0) < 2:
        raise ValueError("at least two Qlib OnlineManager history timepoints are required")
    if qlib_identity.get("historical_test_rows_accessed") != 0:
        raise ValueError("historical TEST firewall violated")
    if qlib_identity.get("sealed_oos_rows_accessed") != 0:
        raise ValueError("sealed OOS firewall violated")

    if history.get("history_timepoint_count", 0) < 2:
        raise ValueError("online history is incomplete")
    if tags.get("online_recorder_count", 0) < 1 or tags.get("offline_recorder_count", 0) < 1:
        raise ValueError("OnlineToolR online/offline tag proof is incomplete")
    if tags.get("qlib_online_tag_is_p4_shadow_authority") is not False:
        raise ValueError("Qlib online tag must not be P4 Shadow authority")

    ric_sha256 = sha256_file(ric_artifact_path)
    prediction_sha256 = sha256_file(prediction_artifact_path)
    if sigana.get("aq_rankic_computation") is not False:
        raise ValueError("AQ RankIC computation is prohibited")
    if sigana.get("artifact_sha256") != ric_sha256:
        raise ValueError("SigAna ric.pkl content identity mismatch")
    if prediction.get("artifact_sha256") != prediction_sha256:
        raise ValueError("prediction content identity mismatch")
    if sigana.get("qlib_recorder_id") != sigana.get("mlflow_run_id"):
        raise ValueError("Qlib Recorder / MLflow run identity mismatch")

    if shadow.get("contract_version") != "ShadowEvidenceV2":
        raise ValueError("ShadowEvidenceV2 is required")
    if shadow.get("evidence_classification") != FIXTURE_CLASSIFICATION:
        raise ValueError("real Shadow evidence is prohibited in this fixture")
    if shadow.get("completion_status") != "INCOMPLETE":
        raise ValueError("fixture Shadow must remain INCOMPLETE")
    if shadow.get("outcome_return_evidence_identity") is not None:
        raise ValueError("fixture INCOMPLETE Shadow must not claim realized outcome evidence")
    if shadow.get("zero_capital_attestation") is not True:
        raise ValueError("zero-capital attestation is required")
    if shadow.get("qlib_recorder_id") != sigana.get("qlib_recorder_id"):
        raise ValueError("Shadow / Qlib Recorder identity mismatch")
    if shadow.get("mlflow_run_id") != sigana.get("mlflow_run_id"):
        raise ValueError("Shadow / MLflow run identity mismatch")
    if require_sha256(
        shadow.get("prediction_evidence_identity"),
        "prediction_evidence_identity",
        prefixed=True,
    ) != prediction_sha256:
        raise ValueError("Shadow prediction identity mismatch")
    require_sha256(
        shadow.get("dvc_reproducibility_identity"),
        "dvc_reproducibility_identity",
        prefixed=True,
    )

    if zero_capital != {
        "backtest_executed": False,
        "broker_calls": 0,
        "capital_allocated": 0,
        "contract_version": "ZeroCapitalAttestationV1",
        "fixture_classification": FIXTURE_CLASSIFICATION,
        "order_count": 0,
        "portfolio_strategy_executed": False,
        "zero_capital_attestation": True,
    }:
        raise ValueError("zero-capital attestation fields changed")
    if pre_epoch.get("production_policy_effective_epoch") != "2026-10-01":
        raise ValueError("production policy epoch mismatch")
    if pre_epoch.get("pre_epoch_production_decay_evaluation") != "REJECTED":
        raise ValueError("pre-epoch evaluation did not fail closed")

    dependencies = {
        "fixture_task_config": sha256_file(fixture_task_config_path),
        "online_history_manifest": sha256_file(history_path),
        "online_tag_report": sha256_file(tag_report_path),
        "policy_config": sha256_file(policy_config_path),
        "policy_module": sha256_file(policy_module_path),
        "policy_schema": sha256_file(policy_schema_path),
        "prediction_artifact": prediction_sha256,
        "prediction_identity_report": sha256_file(prediction_report_path),
        "qlib_online_identity_report": sha256_file(qlib_identity_path),
        "ric_artifact": ric_sha256,
        "shadow_fixture": sha256_file(shadow_fixture_path),
        "sigana_identity_report": sha256_file(sigana_report_path),
        "zero_capital_attestation": sha256_file(zero_capital_path),
        "pre_epoch_firewall_report": sha256_file(pre_epoch_path),
    }
    return {
        "contract_version": SEAL_VERSION,
        "dependencies": dependencies,
        "dvc_reproducibility_identity": shadow["dvc_reproducibility_identity"],
        "fixture_classification": FIXTURE_CLASSIFICATION,
        "mlflow_experiment_id": shadow["mlflow_experiment_id"],
        "mlflow_run_id": shadow["mlflow_run_id"],
        "qlib_experiment_id": shadow["qlib_experiment_id"],
        "qlib_recorder_id": shadow["qlib_recorder_id"],
        "stage_name": STAGE_NAME,
        "zero_capital_shadow": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
        "ric_artifact",
        "prediction_artifact",
        "policy_module",
        "policy_schema",
        "policy_config",
        "output",
    ):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    seal = validate_and_build_seal(
        **{
            f"{name}_path": getattr(args, name)
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
                "ric_artifact",
                "prediction_artifact",
                "policy_module",
                "policy_schema",
                "policy_config",
            )
        }
    )
    output_bytes = deterministic_json_bytes(seal)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    print(json.dumps({"output_sha256": hashlib.sha256(output_bytes).hexdigest(), **seal}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
