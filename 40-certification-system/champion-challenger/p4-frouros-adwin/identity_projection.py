"""Validate one fixed upstream identity chain and emit one DVC seal."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PROJECTION_VERSION = "UpstreamIdentityProjectionV1"
SEAL_VERSION = "P4IdentityProjectionDVCSealV1"
FIXTURE_CLASSIFICATION = "TEST_FIXTURE_NOT_REAL_RESEARCH"
METRIC_KIND = "RANK_IC"
ARTIFACT_LOGICAL_PATH = "sig_analysis/ric.pkl"
FROUROS_VERSION = "0.9.0"
FROUROS_RUNTIME_FREEZE_SHA256 = (
    "8c66ad3fde0f116d89aa31c0454a093eba00b16fe6d5946ac973bd5850dfb5d5"
)
FROUROS_ADWIN_MODULE_SHA256 = (
    "f3b2c06acf88b6938eac907909ca16b8daa382133eb1247e297a12f299ebd8fd"
)
STAGE_NAME = "p4_frouros_identity_projection"
INTERPRETATION_KEYS = {
    "detector_evidence_schema",
    "frouros_runner",
    "metric_observation_schema",
    "projection_schema",
    "qlib_exporter",
    "seal_script",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.resolve(strict=True).read_bytes())


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


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    payload_bytes = path.resolve(strict=True).read_bytes()
    payload = json.loads(payload_bytes)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload, payload_bytes


def require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be lowercase SHA256")
    return value


def validate_projection_contract(projection: dict[str, Any]) -> None:
    if set(projection) != {
        "contract_version",
        "detector_evidence_sha256",
        "fixture_classification",
        "frouros_identity",
        "interpretation_identity",
        "metric_kind",
        "metric_observation_stream_sha256",
        "mlflow_identity",
        "qlib_identity",
    }:
        raise ValueError("invalid UpstreamIdentityProjectionV1 fields")
    if projection["contract_version"] != PROJECTION_VERSION:
        raise ValueError("unsupported projection contract version")
    if projection["fixture_classification"] != FIXTURE_CLASSIFICATION:
        raise ValueError("invalid fixture classification")
    if projection["metric_kind"] != METRIC_KIND:
        raise ValueError("unsupported metric kind")
    require_sha256(
        projection["metric_observation_stream_sha256"],
        "metric_observation_stream_sha256",
    )
    require_sha256(projection["detector_evidence_sha256"], "detector_evidence_sha256")

    qlib_identity = projection["qlib_identity"]
    if not isinstance(qlib_identity, dict) or set(qlib_identity) != {
        "artifact_logical_path",
        "artifact_sha256",
        "experiment_id",
        "recorder_id",
        "status",
        "version",
    }:
        raise ValueError("invalid qlib_identity fields")
    if qlib_identity["status"] != "FINISHED":
        raise ValueError("Qlib recorder must be FINISHED")
    if qlib_identity["artifact_logical_path"] != ARTIFACT_LOGICAL_PATH:
        raise ValueError("wrong Qlib artifact logical path")
    require_sha256(qlib_identity["artifact_sha256"], "qlib artifact SHA256")

    mlflow_identity = projection["mlflow_identity"]
    if not isinstance(mlflow_identity, dict) or set(mlflow_identity) != {
        "artifact_logical_path",
        "artifact_sha256",
        "experiment_id",
        "run_id",
        "status",
        "version",
    }:
        raise ValueError("invalid mlflow_identity fields")
    if mlflow_identity["status"] != "FINISHED":
        raise ValueError("MLflow run must be FINISHED")
    if mlflow_identity["artifact_logical_path"] != ARTIFACT_LOGICAL_PATH:
        raise ValueError("wrong MLflow artifact logical path")
    if mlflow_identity["version"] != "3.16.0":
        raise ValueError("wrong MLflow version")
    require_sha256(mlflow_identity["artifact_sha256"], "MLflow artifact SHA256")
    if qlib_identity["experiment_id"] != mlflow_identity["experiment_id"]:
        raise ValueError("Qlib/MLflow experiment ID mismatch")
    if qlib_identity["recorder_id"] != mlflow_identity["run_id"]:
        raise ValueError("Qlib recorder ID / MLflow run ID mismatch")
    if qlib_identity["artifact_sha256"] != mlflow_identity["artifact_sha256"]:
        raise ValueError("Qlib/MLflow artifact SHA256 mismatch")

    frouros_identity = projection["frouros_identity"]
    if not isinstance(frouros_identity, dict) or set(frouros_identity) != {
        "installed_adwin_module_sha256",
        "runtime_freeze_sha256",
        "version",
    }:
        raise ValueError("invalid frouros_identity fields")
    if frouros_identity["version"] != FROUROS_VERSION:
        raise ValueError("wrong Frouros version")
    if frouros_identity["runtime_freeze_sha256"] != FROUROS_RUNTIME_FREEZE_SHA256:
        raise ValueError("wrong Frouros runtime freeze")
    if (
        frouros_identity["installed_adwin_module_sha256"]
        != FROUROS_ADWIN_MODULE_SHA256
    ):
        raise ValueError("wrong Frouros ADWIN module SHA256")

    interpretation = projection["interpretation_identity"]
    if not isinstance(interpretation, dict) or set(interpretation) != INTERPRETATION_KEYS:
        raise ValueError("invalid interpretation identity")
    for name, value in interpretation.items():
        require_sha256(value, f"interpretation_identity.{name}")


def validate_and_build_seal(
    *,
    projection_path: Path,
    expected_projection_sha256: str,
    observation_path: Path,
    detector_path: Path,
    ric_path: Path,
    identity_report_path: Path,
    runtime_freeze_path: Path,
    interpretation_paths: dict[str, Path],
) -> dict[str, Any]:
    require_sha256(expected_projection_sha256, "expected projection SHA256")
    projection, projection_bytes = load_json(projection_path)
    projection_sha256 = sha256_bytes(projection_bytes)
    if projection_sha256 != expected_projection_sha256:
        raise ValueError("projection exact-byte SHA256 mismatch")
    validate_projection_contract(projection)

    if set(interpretation_paths) != INTERPRETATION_KEYS:
        raise ValueError("incomplete interpretation dependency set")
    for name, path in interpretation_paths.items():
        if sha256_file(path) != projection["interpretation_identity"][name]:
            raise ValueError(f"tampered interpretation dependency: {name}")

    observation, observation_bytes = load_json(observation_path)
    observation_sha256 = sha256_bytes(observation_bytes)
    if observation_sha256 != projection["metric_observation_stream_sha256"]:
        raise ValueError("MetricObservationStreamV1 byte identity mismatch")
    if observation.get("contract_version") != "MetricObservationStreamV1":
        raise ValueError("unsupported observation contract")
    if observation.get("metric_kind") != METRIC_KIND:
        raise ValueError("unsupported observation metric")

    detector, detector_bytes = load_json(detector_path)
    detector_sha256 = sha256_bytes(detector_bytes)
    if detector_sha256 != projection["detector_evidence_sha256"]:
        raise ValueError("DetectorEvidenceV1 byte identity mismatch")
    if detector.get("contract_version") != "DetectorEvidenceV1":
        raise ValueError("unsupported detector contract")
    if detector.get("metric_kind") != METRIC_KIND:
        raise ValueError("unsupported detector metric")
    if detector.get("source_observation_stream_sha256") != observation_sha256:
        raise ValueError("DetectorEvidenceV1 observation binding mismatch")

    ric_sha256 = sha256_file(ric_path)
    if observation.get("source_artifact_sha256") != ric_sha256:
        raise ValueError("MetricObservationStreamV1 source artifact mismatch")
    qlib_identity = projection["qlib_identity"]
    mlflow_identity = projection["mlflow_identity"]
    if qlib_identity["artifact_sha256"] != ric_sha256:
        raise ValueError("Qlib projection artifact content mismatch")
    if mlflow_identity["artifact_sha256"] != ric_sha256:
        raise ValueError("MLflow projection artifact content mismatch")

    if detector.get("detector_version") != FROUROS_VERSION:
        raise ValueError("detector Frouros version mismatch")
    if detector.get("frouros_runtime_freeze_sha256") != FROUROS_RUNTIME_FREEZE_SHA256:
        raise ValueError("detector Frouros runtime freeze mismatch")
    if detector.get("installed_adwin_module_sha256") != FROUROS_ADWIN_MODULE_SHA256:
        raise ValueError("detector Frouros module identity mismatch")
    if sha256_file(runtime_freeze_path) != FROUROS_RUNTIME_FREEZE_SHA256:
        raise ValueError("runtime-freeze evidence bytes mismatch")

    identity_report, _ = load_json(identity_report_path)
    if identity_report.get("fixture_classification") != FIXTURE_CLASSIFICATION:
        raise ValueError("identity report fixture classification mismatch")
    report_qlib = identity_report.get("qlib", {})
    report_mlflow = identity_report.get("mlflow", {})
    report_artifact = identity_report.get("artifact", {})
    if report_qlib.get("status") != "FINISHED":
        raise ValueError("identity report Qlib run not FINISHED")
    if report_mlflow.get("status") != "FINISHED":
        raise ValueError("identity report MLflow run not FINISHED")
    if report_qlib.get("experiment_id") != qlib_identity["experiment_id"]:
        raise ValueError("identity report Qlib experiment mismatch")
    if report_mlflow.get("experiment_id") != mlflow_identity["experiment_id"]:
        raise ValueError("identity report MLflow experiment mismatch")
    if report_qlib.get("recorder_id") != qlib_identity["recorder_id"]:
        raise ValueError("identity report Qlib recorder mismatch")
    if report_mlflow.get("run_id") != mlflow_identity["run_id"]:
        raise ValueError("identity report MLflow run mismatch")
    if report_artifact.get("logical_path") != ARTIFACT_LOGICAL_PATH:
        raise ValueError("identity report logical artifact path mismatch")
    if report_artifact.get("sha256") != ric_sha256:
        raise ValueError("identity report artifact SHA256 mismatch")

    return {
        "contract_version": SEAL_VERSION,
        "detector_evidence_sha256": detector_sha256,
        "fixture_classification": FIXTURE_CLASSIFICATION,
        "frouros_identity": dict(projection["frouros_identity"]),
        "metric_observation_stream_sha256": observation_sha256,
        "mlflow_run_id": mlflow_identity["run_id"],
        "projection_sha256": projection_sha256,
        "qlib_recorder_id": qlib_identity["recorder_id"],
        "ric_artifact_sha256": ric_sha256,
        "stage_name": STAGE_NAME,
    }


def parse_interpretation(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path or name in parsed:
            raise ValueError("interpretation dependencies must be unique name=path pairs")
        parsed[name] = Path(path)
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection", required=True, type=Path)
    parser.add_argument("--projection-sha256", required=True)
    parser.add_argument("--observation-stream", required=True, type=Path)
    parser.add_argument("--detector-evidence", required=True, type=Path)
    parser.add_argument("--ric-artifact", required=True, type=Path)
    parser.add_argument("--identity-report", required=True, type=Path)
    parser.add_argument("--runtime-freeze", required=True, type=Path)
    parser.add_argument("--interpretation", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    seal = validate_and_build_seal(
        projection_path=args.projection,
        expected_projection_sha256=args.projection_sha256,
        observation_path=args.observation_stream,
        detector_path=args.detector_evidence,
        ric_path=args.ric_artifact,
        identity_report_path=args.identity_report,
        runtime_freeze_path=args.runtime_freeze,
        interpretation_paths=parse_interpretation(args.interpretation),
    )
    output_bytes = deterministic_json_bytes(seal)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    print(json.dumps({"output_sha256": sha256_bytes(output_bytes), **seal}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
