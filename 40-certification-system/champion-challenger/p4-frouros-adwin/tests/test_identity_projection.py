from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import identity_projection  # noqa: E402


RUNTIME_FREEZE = Path(
    "/mnt/d/AQ_DATA/P4/selected-upstream-components-deployment-001/runtime_freeze_manifest.json"
)


def write_json(path: Path, payload: dict) -> None:
    path.write_bytes(identity_projection.deterministic_json_bytes(payload))


class IdentityProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ric = self.root / "ric.pkl"
        self.ric.write_bytes(b"synthetic-qib-ric-pickle")
        self.ric_sha = identity_projection.sha256_file(self.ric)

        self.observation = self.root / "observation.json"
        self.observation_payload = {
            "contract_version": "MetricObservationStreamV1",
            "metric_kind": "RANK_IC",
            "observations": [
                {"observation_time": "2024-01-02T00:00:00", "value": 0.05}
            ],
            "source_artifact_sha256": self.ric_sha,
            "source_format": "QLIB_SIGANA_RIC_PICKLE",
        }
        write_json(self.observation, self.observation_payload)

        self.detector = self.root / "detector.json"
        self.detector_payload = {
            "change_detected": False,
            "change_indices": [],
            "contract_version": "DetectorEvidenceV1",
            "detector_config": {
                "clock": 32,
                "delta": 0.002,
                "m": 5,
                "min_num_instances": 10,
                "min_window_size": 5,
            },
            "detector_kind": "ADWIN",
            "detector_project": "FROUROS",
            "detector_version": "0.9.0",
            "first_observation_time": "2024-01-02T00:00:00",
            "frouros_runtime_freeze_sha256": identity_projection.FROUROS_RUNTIME_FREEZE_SHA256,
            "installed_adwin_module_sha256": identity_projection.FROUROS_ADWIN_MODULE_SHA256,
            "last_observation_time": "2024-01-02T00:00:00",
            "metric_kind": "RANK_IC",
            "observation_count": 1,
            "original_domain": [-1.0, 1.0],
            "source_artifact_sha256": self.ric_sha,
            "source_observation_stream_sha256": identity_projection.sha256_file(
                self.observation
            ),
            "state_authority": "REPLAY_FROM_IMMUTABLE_OBSERVATIONS",
            "translated_domain": [0.0, 2.0],
            "translation_constant": 1.0,
            "translation_kind": "CONSTANT_ADDITIVE_OFFSET",
        }
        write_json(self.detector, self.detector_payload)

        self.interpretation_paths = {}
        for name in identity_projection.INTERPRETATION_KEYS:
            path = self.root / f"{name}.txt"
            path.write_text(f"{name}\n", encoding="utf-8")
            self.interpretation_paths[name] = path

        self.projection = self.root / "projection.json"
        self.projection_payload = {
            "contract_version": "UpstreamIdentityProjectionV1",
            "detector_evidence_sha256": identity_projection.sha256_file(self.detector),
            "fixture_classification": "TEST_FIXTURE_NOT_REAL_RESEARCH",
            "frouros_identity": {
                "installed_adwin_module_sha256": identity_projection.FROUROS_ADWIN_MODULE_SHA256,
                "runtime_freeze_sha256": identity_projection.FROUROS_RUNTIME_FREEZE_SHA256,
                "version": "0.9.0",
            },
            "interpretation_identity": {
                name: identity_projection.sha256_file(path)
                for name, path in self.interpretation_paths.items()
            },
            "metric_kind": "RANK_IC",
            "metric_observation_stream_sha256": identity_projection.sha256_file(
                self.observation
            ),
            "mlflow_identity": {
                "artifact_logical_path": "sig_analysis/ric.pkl",
                "artifact_sha256": self.ric_sha,
                "experiment_id": "1",
                "run_id": "run-1",
                "status": "FINISHED",
                "version": "3.16.0",
            },
            "qlib_identity": {
                "artifact_logical_path": "sig_analysis/ric.pkl",
                "artifact_sha256": self.ric_sha,
                "experiment_id": "1",
                "recorder_id": "run-1",
                "status": "FINISHED",
                "version": "0.9.8.dev26",
            },
        }
        write_json(self.projection, self.projection_payload)

        self.identity_report = self.root / "identity-report.json"
        self.report_payload = {
            "artifact": {
                "logical_path": "sig_analysis/ric.pkl",
                "sha256": self.ric_sha,
            },
            "fixture_classification": "TEST_FIXTURE_NOT_REAL_RESEARCH",
            "mlflow": {
                "experiment_id": "1",
                "run_id": "run-1",
                "status": "FINISHED",
            },
            "qlib": {
                "experiment_id": "1",
                "recorder_id": "run-1",
                "status": "FINISHED",
            },
        }
        write_json(self.identity_report, self.report_payload)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def call(self) -> dict:
        return identity_projection.validate_and_build_seal(
            projection_path=self.projection,
            expected_projection_sha256=identity_projection.sha256_file(self.projection),
            observation_path=self.observation,
            detector_path=self.detector,
            ric_path=self.ric,
            identity_report_path=self.identity_report,
            runtime_freeze_path=RUNTIME_FREEZE,
            interpretation_paths=self.interpretation_paths,
        )

    def rewrite_projection(self) -> None:
        write_json(self.projection, self.projection_payload)

    def test_valid_projection_schema_and_deterministic_seal(self) -> None:
        schema = json.loads(
            (ROOT / "adapter/schemas/upstream_identity_projection_v1.schema.json").read_text()
        )
        jsonschema.validate(self.projection_payload, schema)
        first = self.call()
        second = self.call()
        self.assertEqual(
            identity_projection.deterministic_json_bytes(first),
            identity_projection.deterministic_json_bytes(second),
        )
        self.assertEqual(first["stage_name"], "p4_frouros_identity_projection")

    def test_rejects_qlib_run_not_finished(self) -> None:
        self.projection_payload["qlib_identity"]["status"] = "FAILED"
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_mlflow_run_not_finished(self) -> None:
        self.projection_payload["mlflow_identity"]["status"] = "FAILED"
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_run_id_mismatch(self) -> None:
        self.projection_payload["qlib_identity"]["recorder_id"] = "other"
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_experiment_id_mismatch(self) -> None:
        self.projection_payload["qlib_identity"]["experiment_id"] = "2"
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_ric_content_mismatch(self) -> None:
        self.ric.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_wrong_logical_artifact_path(self) -> None:
        self.projection_payload["qlib_identity"]["artifact_logical_path"] = "ric.pkl"
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_metric_observation_source_hash_mismatch(self) -> None:
        self.observation_payload["source_artifact_sha256"] = "f" * 64
        write_json(self.observation, self.observation_payload)
        self.detector_payload["source_observation_stream_sha256"] = (
            identity_projection.sha256_file(self.observation)
        )
        write_json(self.detector, self.detector_payload)
        self.projection_payload["metric_observation_stream_sha256"] = (
            identity_projection.sha256_file(self.observation)
        )
        self.projection_payload["detector_evidence_sha256"] = (
            identity_projection.sha256_file(self.detector)
        )
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_detector_observation_hash_mismatch(self) -> None:
        self.detector_payload["source_observation_stream_sha256"] = "f" * 64
        write_json(self.detector, self.detector_payload)
        self.projection_payload["detector_evidence_sha256"] = (
            identity_projection.sha256_file(self.detector)
        )
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_wrong_frouros_runtime_freeze(self) -> None:
        self.projection_payload["frouros_identity"]["runtime_freeze_sha256"] = "f" * 64
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_wrong_frouros_module_hash(self) -> None:
        self.projection_payload["frouros_identity"]["installed_adwin_module_sha256"] = "f" * 64
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_tampered_projection_bytes(self) -> None:
        expected = identity_projection.sha256_file(self.projection)
        self.projection.write_bytes(self.projection.read_bytes() + b" ")
        with self.assertRaises(ValueError):
            identity_projection.validate_and_build_seal(
                projection_path=self.projection,
                expected_projection_sha256=expected,
                observation_path=self.observation,
                detector_path=self.detector,
                ric_path=self.ric,
                identity_report_path=self.identity_report,
                runtime_freeze_path=RUNTIME_FREEZE,
                interpretation_paths=self.interpretation_paths,
            )

    def test_rejects_tampered_dvc_dependency(self) -> None:
        path = self.interpretation_paths["qlib_exporter"]
        path.write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.call()

    def test_rejects_unsupported_metric(self) -> None:
        self.projection_payload["metric_kind"] = "IC"
        self.rewrite_projection()
        with self.assertRaises(ValueError):
            self.call()


if __name__ == "__main__":
    unittest.main()
