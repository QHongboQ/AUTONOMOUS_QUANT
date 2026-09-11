from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import shlex
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


def windows_path_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    if len(drive) != 1 or not drive.isalpha():
        raise ValueError("WSL probe requires a dynamically resolved Windows drive path")
    return f"/mnt/{drive}/" + "/".join(resolved.parts[1:])


def write_snapshot(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    path.mkdir(parents=True)
    metadata = {
        "schema_version": "DatasetSnapshotV1",
        "universe_id": "SYNTHETIC_TEST_ONLY",
        "coverage_start": min(row["membership_from"] for row in rows),
        "coverage_end": max(row["membership_to"] for row in rows),
        "row_count": len(rows),
        "publication_state": "RESEARCH_READY",
    }
    (path / "snapshot.json").write_text(json.dumps(metadata), encoding="utf-8")
    (path / "episodes.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8", newline="",
    )


SYNTHETIC_ROWS = (
    {"episode_id": "aaa-1", "ticker": "AAA", "membership_from": "2020-01-02", "membership_to": "2020-01-06"},
    {"episode_id": "aaa-2", "ticker": "AAA", "membership_from": "2020-01-08", "membership_to": "2020-01-10"},
    {"episode_id": "old-1", "ticker": "OLD", "membership_from": "2020-01-02", "membership_to": "2020-02-03"},
    {"episode_id": "new-1", "ticker": "NEW", "membership_from": "2020-02-03", "membership_to": "2020-03-02"},
)


class QlibHandoffUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.snapshot = self.root / "snapshot"
        write_snapshot(self.snapshot, SYNTHETIC_ROWS)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_snapshot_contract_parsing(self) -> None:
        result = prepare_qlib_universe(self.snapshot, self.root / "output")
        self.assertEqual((result.episode_count, result.instrument_range_count), (4, 4))

    def test_duplicate_episode_rejected(self) -> None:
        write_snapshot(self.root / "duplicate", (*SYNTHETIC_ROWS, SYNTHETIC_ROWS[0]))
        with self.assertRaisesRegex(ValueError, "duplicate episode_id"):
            prepare_qlib_universe(self.root / "duplicate", self.root / "output")

    def test_deterministic_conversion(self) -> None:
        first, second = self.root / "first", self.root / "second"
        prepare_qlib_universe(self.snapshot, first)
        prepare_qlib_universe(self.snapshot, second)
        for relative in ("instruments/aq_pit.txt", "episode-map.jsonl", "handoff.json"):
            self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())

    def test_disjoint_ranges_preserve_reuse_gap(self) -> None:
        output = self.root / "output"
        prepare_qlib_universe(self.snapshot, output)
        lines = (output / "instruments" / "aq_pit.txt").read_text().splitlines()
        aaa = [line.split("\t") for line in lines if line.startswith("AAA\t")]
        self.assertEqual(len(aaa), 2)
        self.assertLess(aaa[0][2], aaa[1][1])

    def test_no_private_or_dvc_imports(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in (
            LEAF / "aq_qlib_handoff" / "contract.py",
            LEAF / "aq_qlib_handoff" / "adapter.py",
            LEAF / "prepare_qlib_universe.py",
        ))
        self.assertNotIn("aq_pit.", source)
        self.assertNotIn("sp500-pit", source)
        self.assertNotIn("from dvc", source)
        self.assertNotIn("import dvc", source)

    def test_no_custom_aq_research_framework(self) -> None:
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


@unittest.skipUnless(SNAPSHOT.exists(), "DVC DatasetSnapshot output is not checked out")
class QlibHandoffIntegrationTests(unittest.TestCase):
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

    def run_qlib_public_api_compatibility_probe(self) -> None:
        probe = windows_path_to_wsl(LEAF / "tests" / "qlib_public_api_probe.py")
        quoted_probe = shlex.quote(probe)
        try:
            available = subprocess.run(
                ("wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc",
                 'test -f "$HOME/miniforge3/etc/profile.d/conda.sh" && '
                 f"test -f {quoted_probe}"),
                text=True, capture_output=True, check=False,
            )
        except FileNotFoundError:
            self.skipTest("WSL is unavailable")
        if available.returncode != 0:
            self.skipTest("accepted Qlib environment launcher is unavailable")
        result = subprocess.run(
            (
                "wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc",
                'source "$HOME/miniforge3/etc/profile.d/conda.sh" && '
                f"conda run -n rdagent4qlib python {quoted_probe}",
            ),
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"qlib_version": "0.9.8.dev26"', result.stdout)
        self.assertIn('"range_count": 3', result.stdout)

class QlibPublicApiIntegrationTests(unittest.TestCase):
    def test_qlib_public_api_compatibility_probe(self) -> None:
        QlibHandoffIntegrationTests.run_qlib_public_api_compatibility_probe(self)


if __name__ == "__main__":
    unittest.main()
