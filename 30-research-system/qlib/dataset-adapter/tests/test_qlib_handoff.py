from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
LEAF = ROOT / "30-research-system" / "qlib" / "dataset-adapter"
SNAPSHOT = ROOT / "10-data-system" / "dataset-snapshot" / "pit-universe" / "data"
sys.path.insert(0, str(LEAF))

from aq_qlib_handoff import prepare_qlib_universe


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode())
            digest.update(item.read_bytes())
    return digest.hexdigest()


@unittest.skipUnless(SNAPSHOT.exists(), "DVC DatasetSnapshot output is not checked out")
class QlibHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before_hash = tree_hash(SNAPSHOT)
        cls.first_temp = tempfile.TemporaryDirectory()
        cls.second_temp = tempfile.TemporaryDirectory()
        cls.first = Path(cls.first_temp.name)
        cls.second = Path(cls.second_temp.name)
        cls.result = prepare_qlib_universe(SNAPSHOT, cls.first)
        prepare_qlib_universe(SNAPSHOT, cls.second)
        cls.rows = tuple(
            json.loads(line)
            for line in (cls.first / "episode-map.jsonl").read_text(encoding="utf-8").splitlines()
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.first_temp.cleanup()
        cls.second_temp.cleanup()

    def _ticker(self, ticker: str) -> list[dict[str, str]]:
        return [row for row in self.rows if row["ticker"] == ticker]

    def test_accepts_all_832_dataset_snapshot_episodes(self) -> None:
        self.assertEqual(self.result.episode_count, 832)

    def test_dynamic_membership_range_count_is_preserved(self) -> None:
        lines = (self.first / "instruments" / "aq_pit.txt").read_text().splitlines()
        self.assertEqual(self.result.instrument_range_count, 832)
        self.assertEqual(len(lines), 832)

    def test_output_is_byte_deterministic(self) -> None:
        for relative in ("instruments/aq_pit.txt", "episode-map.jsonl", "handoff.json"):
            self.assertEqual((self.first / relative).read_bytes(), (self.second / relative).read_bytes())

    def test_duplicate_episode_is_not_silently_collapsed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken = Path(directory) / "snapshot"
            shutil.copytree(SNAPSHOT, broken)
            rows_path = broken / "episodes.jsonl"
            first = rows_path.read_text(encoding="utf-8").splitlines()[0]
            with rows_path.open("a", encoding="utf-8", newline="") as stream:
                stream.write(first + "\n")
            metadata_path = broken / "snapshot.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["row_count"] += 1
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate episode_id"):
                prepare_qlib_universe(broken, Path(directory) / "output")

    def test_exit_reentry_gaps_remain_absent_from_active_ranges(self) -> None:
        for ticker in ("AMD", "TER", "JBL", "FSLR", "EQT", "PCG"):
            ranges = self._ticker(ticker)
            self.assertEqual(len(ranges), 2, ticker)
            self.assertLess(ranges[0]["qlib_end_inclusive"], ranges[1]["membership_from"], ticker)

    def test_ticker_reuse_and_rename_firewall(self) -> None:
        self.assertEqual(len(self._ticker("Q")), 2)
        self.assertEqual(len(self._ticker("GAS")), 2)
        self.assertEqual(len(self._ticker("IR")), 2)
        self.assertEqual(len(self._ticker("TT")), 1)
        self.assertEqual(len(self._ticker("DLPH")), 1)
        self.assertEqual(len(self._ticker("APTV")), 1)
        self.assertEqual(len(self._ticker("IQV")), 1)

    def test_dataset_snapshot_is_read_only(self) -> None:
        self.assertEqual(tree_hash(SNAPSHOT), self.before_hash)

    def test_adapter_has_no_pit_private_import(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in (
            LEAF / "aq_qlib_handoff" / "contract.py",
            LEAF / "aq_qlib_handoff" / "adapter.py",
            LEAF / "prepare_qlib_universe.py",
        ))
        self.assertNotIn("aq_pit.", source)
        self.assertNotIn("sp500-pit", source)

    def test_adapter_has_no_dvc_runtime_import(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in (LEAF / "aq_qlib_handoff").glob("*.py"))
        self.assertNotIn("from dvc", source)
        self.assertNotIn("import dvc", source)

    def test_qlib_public_api_compatibility_probe(self) -> None:
        probe = "/mnt/d/AUTONOMOUS_QUANT/30-research-system/qlib/dataset-adapter/tests/qlib_public_api_probe.py"
        result = subprocess.run(
            (
                "wsl", "-d", "Ubuntu-24.04", "--",
                "/home/zhou/miniforge3/bin/conda", "run", "-n", "rdagent4qlib",
                "python", probe,
            ),
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"qlib_version": "0.9.8.dev26"', result.stdout)
        self.assertIn('"range_count": 3', result.stdout)

    def test_qlib_owns_dataset_and_alpha158(self) -> None:
        config = (LEAF / "qlib-research-skeleton.yaml").read_text(encoding="utf-8")
        self.assertIn("class: DatasetH", config)
        self.assertIn("class: Alpha158", config)

    def test_qlib_owns_topk(self) -> None:
        self.assertIn(
            "class: TopkDropoutStrategy",
            (LEAF / "qlib-research-skeleton.yaml").read_text(encoding="utf-8"),
        )

    def test_qlib_owns_backtest_and_portfolio_analysis(self) -> None:
        config = (LEAF / "qlib-research-skeleton.yaml").read_text(encoding="utf-8")
        self.assertIn("owner: qlib.backtest", config)
        self.assertIn("class: PortAnaRecord", config)

    def test_no_custom_research_framework_added(self) -> None:
        forbidden = (
            "AQDatasetEngine", "AQFactorEngine", "AQAlpha158", "AQModelTournamentEngine",
            "AQPredictionEngine", "AQRankingEngine", "AQTopKEngine", "AQBacktestEngine",
            "AQPortfolioAnalyticsEngine", "AQExperimentTracker",
        )
        source = "\n".join(path.read_text(encoding="utf-8") for path in (
            LEAF / "aq_qlib_handoff" / "__init__.py",
            LEAF / "aq_qlib_handoff" / "contract.py",
            LEAF / "aq_qlib_handoff" / "adapter.py",
            LEAF / "prepare_qlib_universe.py",
        ))
        self.assertTrue(all(name not in source for name in forbidden))


if __name__ == "__main__":
    unittest.main()
