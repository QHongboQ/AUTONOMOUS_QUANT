from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapter"))

import export_rank_ic  # noqa: E402


class RankICExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "sig_analysis" / "ric.pkl"
        self.source.parent.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, value: object) -> None:
        pd.to_pickle(value, self.source)

    def assert_rejected(self, value: object, error: type[BaseException]) -> None:
        self.write(value)
        with self.assertRaises(error):
            export_rank_ic.load_rank_ic_artifact(self.source)

    def test_valid_series_schema_and_exact_byte_determinism(self) -> None:
        series = pd.Series(
            [0.1, -0.2, 0.0],
            index=pd.date_range("2024-01-02", periods=3, freq="B"),
            name="ric",
        )
        self.write(series)
        first = self.root / "first.json"
        second = self.root / "second.json"
        report = export_rank_ic.export_rank_ic(self.source, first)
        export_rank_ic.export_rank_ic(self.source, second)

        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(
            report["output_sha256"], hashlib.sha256(first.read_bytes()).hexdigest()
        )
        payload = json.loads(first.read_bytes())
        schema = json.loads(
            (ROOT / "adapter/schemas/metric_observation_stream_v1.schema.json").read_text()
        )
        jsonschema.validate(payload, schema)
        self.assertEqual(payload["metric_kind"], "RANK_IC")
        self.assertEqual(len(payload["observations"]), 3)

    def test_rejects_wrong_object_type(self) -> None:
        self.assert_rejected(pd.DataFrame({"ric": [0.1]}), TypeError)

    def test_rejects_empty_series(self) -> None:
        self.assert_rejected(
            pd.Series([], index=pd.DatetimeIndex([]), dtype=float), ValueError
        )

    def test_rejects_non_datetime_index(self) -> None:
        self.assert_rejected(pd.Series([0.1], index=["2024-01-02"]), TypeError)

    def test_rejects_missing_and_infinite_values(self) -> None:
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(value=value):
                self.assert_rejected(
                    pd.Series([value], index=pd.date_range("2024-01-02", periods=1)),
                    ValueError,
                )

    def test_rejects_values_outside_rank_ic_domain(self) -> None:
        for value in (1.000001, -1.000001):
            with self.subTest(value=value):
                self.assert_rejected(
                    pd.Series([value], index=pd.date_range("2024-01-02", periods=1)),
                    ValueError,
                )

    def test_rejects_duplicate_timestamps(self) -> None:
        index = pd.DatetimeIndex(["2024-01-02", "2024-01-02"])
        self.assert_rejected(pd.Series([0.1, 0.2], index=index), ValueError)

    def test_rejects_non_monotonic_timestamps(self) -> None:
        index = pd.DatetimeIndex(["2024-01-03", "2024-01-02"])
        self.assert_rejected(pd.Series([0.1, 0.2], index=index), ValueError)

    def test_rejects_non_numeric_and_boolean_values(self) -> None:
        for values in (["0.1"], [True]):
            with self.subTest(values=values):
                self.assert_rejected(
                    pd.Series(values, index=pd.date_range("2024-01-02", periods=1)),
                    TypeError,
                )

    def test_rejects_unsupported_metric(self) -> None:
        self.write(
            pd.Series([0.1], index=pd.date_range("2024-01-02", periods=1))
        )
        with self.assertRaises(ValueError):
            export_rank_ic.load_rank_ic_artifact(self.source, metric_kind="IC")

    def test_rejects_non_ric_filename(self) -> None:
        wrong = self.source.with_name("ic.pkl")
        pd.to_pickle(
            pd.Series([0.1], index=pd.date_range("2024-01-02", periods=1)), wrong
        )
        with self.assertRaises(ValueError):
            export_rank_ic.load_rank_ic_artifact(wrong)


if __name__ == "__main__":
    unittest.main()
