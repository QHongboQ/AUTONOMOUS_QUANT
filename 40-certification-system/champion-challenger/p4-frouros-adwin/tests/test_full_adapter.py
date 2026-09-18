from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "adapter/export_rank_ic.py"
RUNNER = ROOT / "adapter/run_adwin.py"
FROUROS_PYTHON = Path(
    os.environ.get(
        "AQ_FROUROS_PYTHON", "/home/zhou/AQ_ENVS/p4-frouros-adwin/bin/python"
    )
)
EXPECTED = {
    "near_zero": 1247,
    "sign_reversal": 1119,
    "stable_noise": None,
    "gradual_deterioration": 1823,
    "temporary_shock_recovery": None,
}


def frozen_streams() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(20260918)
    stable_a = rng.normal(0.05, 0.01, 1000)
    return {
        "near_zero": np.concatenate([stable_a, rng.normal(0.0, 0.01, 1000)]),
        "sign_reversal": np.concatenate(
            [rng.normal(0.05, 0.01, 1000), rng.normal(-0.05, 0.01, 1000)]
        ),
        "stable_noise": rng.normal(0.05, 0.01, 2000),
        "gradual_deterioration": np.concatenate(
            [
                rng.normal(0.05, 0.01, 1000),
                np.linspace(0.05, 0.0, 1000) + rng.normal(0.0, 0.01, 1000),
            ]
        ),
        "temporary_shock_recovery": np.concatenate(
            [
                rng.normal(0.05, 0.01, 1000),
                rng.normal(-0.05, 0.01, 100),
                rng.normal(0.05, 0.01, 900),
            ]
        ),
    }


class FullAdapterParityTests(unittest.TestCase):
    def test_five_frozen_cases_and_fresh_replay(self) -> None:
        observation_schema = json.loads(
            (ROOT / "adapter/schemas/metric_observation_stream_v1.schema.json").read_text()
        )
        evidence_schema = json.loads(
            (ROOT / "adapter/schemas/detector_evidence_v1.schema.json").read_text()
        )
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            for case, values in frozen_streams().items():
                with self.subTest(case=case):
                    case_root = temporary_root / case
                    source = case_root / "sig_analysis/ric.pkl"
                    source.parent.mkdir(parents=True)
                    pd.Series(
                        values,
                        index=pd.date_range("2000-01-03", periods=len(values), freq="B"),
                        name="ric",
                    ).to_pickle(source)
                    observations = case_root / "observations.json"
                    evidence_a = case_root / "evidence-a.json"
                    evidence_b = case_root / "evidence-b.json"
                    subprocess.run(
                        [
                            sys.executable,
                            str(EXPORTER),
                            "--input",
                            str(source),
                            "--output",
                            str(observations),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    stream_sha = hashlib.sha256(observations.read_bytes()).hexdigest()
                    for output in (evidence_a, evidence_b):
                        subprocess.run(
                            [
                                str(FROUROS_PYTHON),
                                str(RUNNER),
                                "--input",
                                str(observations),
                                "--input-sha256",
                                stream_sha,
                                "--output",
                                str(output),
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                    self.assertEqual(evidence_a.read_bytes(), evidence_b.read_bytes())
                    stream = json.loads(observations.read_bytes())
                    evidence = json.loads(evidence_a.read_bytes())
                    jsonschema.validate(stream, observation_schema)
                    jsonschema.validate(evidence, evidence_schema)
                    first_change = (
                        evidence["change_indices"][0]
                        if evidence["change_indices"]
                        else None
                    )
                    self.assertEqual(first_change, EXPECTED[case])
                    self.assertEqual(evidence["observation_count"], 2000)
                    self.assertEqual(
                        evidence["source_observation_stream_sha256"], stream_sha
                    )


if __name__ == "__main__":
    unittest.main()
