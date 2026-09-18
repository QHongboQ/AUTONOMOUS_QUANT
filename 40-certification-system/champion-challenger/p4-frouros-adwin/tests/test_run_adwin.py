from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapter"))

import run_adwin  # noqa: E402


class FrourosRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.stream = {
            "contract_version": "MetricObservationStreamV1",
            "metric_kind": "RANK_IC",
            "observations": [
                {"observation_time": f"2024-01-{day:02d}T00:00:00", "value": 0.05}
                for day in range(1, 21)
            ],
            "source_artifact_sha256": "a" * 64,
            "source_format": "QLIB_SIGANA_RIC_PICKLE",
        }
        self.input_path = self.root / "observations.json"
        self.input_path.write_bytes(run_adwin.deterministic_json_bytes(self.stream))
        self.input_sha = hashlib.sha256(self.input_path.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_public_adwin_run_and_exact_byte_replay(self) -> None:
        first = self.root / "first.json"
        second = self.root / "second.json"
        run_adwin.run_adwin(self.input_path, self.input_sha, first)
        run_adwin.run_adwin(self.input_path, self.input_sha, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        evidence = json.loads(first.read_bytes())
        self.assertEqual(evidence["detector_project"], "FROUROS")
        self.assertEqual(evidence["detector_kind"], "ADWIN")
        self.assertEqual(evidence["translation_constant"], 1.0)
        self.assertNotIn("lifecycle_state", evidence)

    def test_rank_ic_translation_is_exact_additive_offset(self) -> None:
        self.assertEqual(run_adwin.translate_rank_ic(-1.0), 0.0)
        self.assertEqual(run_adwin.translate_rank_ic(0.0), 1.0)
        self.assertEqual(run_adwin.translate_rank_ic(1.0), 2.0)

    def test_rejects_tampered_observation_stream_hash(self) -> None:
        with self.assertRaises(ValueError):
            run_adwin.load_observation_stream(self.input_path, "0" * 64)

    def test_rejects_unsupported_metric_kind(self) -> None:
        invalid = deepcopy(self.stream)
        invalid["metric_kind"] = "IC"
        with self.assertRaises(ValueError):
            run_adwin._parse_observation_stream(invalid)

    def test_rejects_unsupported_translation(self) -> None:
        with self.assertRaises(ValueError):
            run_adwin.translate_rank_ic(0.1, translation_kind="Z_SCORE")
        with self.assertRaises(ValueError):
            run_adwin.translate_rank_ic(0.1, translation_constant=2.0)

    def test_rejects_wrong_frouros_version_and_runtime_freeze(self) -> None:
        with self.assertRaises(RuntimeError):
            run_adwin._validate_runtime_identity(expected_version="0.8.0")
        with self.assertRaises(RuntimeError):
            run_adwin._validate_runtime_identity(
                expected_runtime_freeze_sha256="0" * 64
            )

    def test_rejects_wrong_module_identity(self) -> None:
        with self.assertRaises(RuntimeError):
            run_adwin._validate_runtime_identity(expected_module_sha256="0" * 64)

    def test_rejects_tampered_detector_identity(self) -> None:
        output = self.root / "evidence.json"
        run_adwin.run_adwin(self.input_path, self.input_sha, output)
        evidence = json.loads(output.read_bytes())
        for field, value in (
            ("detector_version", "0.8.0"),
            ("frouros_runtime_freeze_sha256", "0" * 64),
        ):
            invalid = deepcopy(evidence)
            invalid[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                run_adwin._validate_detector_evidence(invalid)


if __name__ == "__main__":
    unittest.main()
