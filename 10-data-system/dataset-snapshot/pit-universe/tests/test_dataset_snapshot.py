from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
PIT_ROOT = ROOT / "10-data-system" / "universe" / "sp500-pit"
SNAPSHOT_ROOT = ROOT / "10-data-system" / "dataset-snapshot" / "pit-universe"
sys.path.insert(0, str(PIT_ROOT))
sys.path.insert(0, str(SNAPSHOT_ROOT))

from aq_dataset_snapshot import export_dataset_snapshot
from aq_pit import build_research_ready_universe


DATA_ROOT = os.environ.get("AQ_PIT_DATA_ROOT")
DVC_BIN = os.environ.get("AQ_DVC_BIN")


@unittest.skipUnless(DATA_ROOT, "set AQ_PIT_DATA_ROOT for frozen snapshot tests")
class DatasetSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.universe = build_research_ready_universe(Path(DATA_ROOT))
        cls.first_temp = tempfile.TemporaryDirectory()
        cls.second_temp = tempfile.TemporaryDirectory()
        cls.first = Path(cls.first_temp.name)
        cls.second = Path(cls.second_temp.name)
        cls.snapshot = export_dataset_snapshot(cls.universe, cls.first)
        export_dataset_snapshot(cls.universe, cls.second)
        cls.rows = tuple(
            json.loads(line)
            for line in (cls.first / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.first_temp.cleanup()
        cls.second_temp.cleanup()

    def test_exact_episode_count(self) -> None:
        self.assertEqual(self.snapshot.row_count, 832)
        self.assertEqual(len(self.rows), 832)

    def test_required_row_fields_only(self) -> None:
        expected = {"episode_id", "ticker", "membership_from", "membership_to"}
        self.assertTrue(all(set(row) == expected for row in self.rows))

    def test_episode_ids_are_unique(self) -> None:
        self.assertEqual(len({row["episode_id"] for row in self.rows}), len(self.rows))

    def test_membership_intervals_are_nonempty(self) -> None:
        self.assertTrue(all(row["membership_from"] < row["membership_to"] for row in self.rows))

    def test_order_is_deterministic(self) -> None:
        expected = sorted(
            self.rows,
            key=lambda row: (
                row["membership_from"], row["ticker"],
                row["membership_to"], row["episode_id"],
            ),
        )
        self.assertEqual(list(self.rows), expected)

    def test_identical_input_is_byte_identical(self) -> None:
        for name in ("episodes.jsonl", "snapshot.json"):
            self.assertEqual((self.first / name).read_bytes(), (self.second / name).read_bytes())

    def test_snapshot_has_no_p2_certification_fields(self) -> None:
        forbidden = {"certification_id", "authority_graph", "promotion_state", "official_terminal"}
        metadata = json.loads((self.first / "snapshot.json").read_text(encoding="utf-8"))
        self.assertFalse(forbidden & set(metadata))
        self.assertTrue(all(not (forbidden & set(row)) for row in self.rows))

    def test_dataset_code_does_not_import_dvc(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in (
            SNAPSHOT_ROOT / "aq_dataset_snapshot" / "contract.py",
            SNAPSHOT_ROOT / "aq_dataset_snapshot" / "export.py",
            SNAPSHOT_ROOT / "export_snapshot.py",
        ))
        self.assertNotIn("from dvc", source)
        self.assertNotIn("import dvc", source)

    def test_pit_runtime_does_not_import_dvc(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (PIT_ROOT / "aq_pit").rglob("*.py")
        )
        self.assertNotIn("from dvc", source)
        self.assertNotIn("import dvc", source)

    def test_repository_stage_declares_dependencies_and_output(self) -> None:
        pipeline = (ROOT / "dvc.yaml").read_text(encoding="utf-8")
        self.assertIn("pit_universe_snapshot:", pipeline)
        self.assertIn("deps:", pipeline)
        self.assertIn("outs:", pipeline)
        self.assertIn("accepted_reconciliation_facts", pipeline)
        self.assertIn("dataset-snapshot/pit-universe/data", pipeline)


@unittest.skipUnless(DVC_BIN, "set AQ_DVC_BIN for DVC CLI behavior tests")
class DvcCliBoundaryTests(unittest.TestCase):
    def test_skip_invalidation_isolation_and_cache_restore(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.txt").write_text("alpha\n", encoding="utf-8")
            (root / "build.py").write_text(
                "from pathlib import Path\n"
                "Path('output.txt').write_text(Path('input.txt').read_text().upper())\n",
                encoding="utf-8",
            )
            (root / "dvc.yaml").write_text(
                "stages:\n  build:\n    cmd: python -B build.py\n"
                "    deps:\n      - build.py\n      - input.txt\n"
                "    outs:\n      - output.txt\n",
                encoding="utf-8",
            )
            environment = {**os.environ, "DVC_NO_ANALYTICS": "1"}

            def dvc(*arguments: str) -> subprocess.CompletedProcess[str]:
                result = subprocess.run(
                    (DVC_BIN, *arguments), cwd=root, env=environment,
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result

            dvc("init", "--no-scm", "--quiet")
            dvc("repro", "build")
            unchanged = dvc("repro", "build")
            self.assertIn("didn't change", unchanged.stdout)

            (root / "unrelated.txt").write_text("irrelevant\n", encoding="utf-8")
            irrelevant = dvc("repro", "build")
            self.assertIn("didn't change", irrelevant.stdout)

            (root / "input.txt").write_text("beta\n", encoding="utf-8")
            relevant = dvc("repro", "build")
            self.assertIn("Running stage 'build'", relevant.stdout)
            self.assertEqual((root / "output.txt").read_text(), "BETA\n")

            (root / "output.txt").unlink()
            dvc("checkout", "output.txt")
            self.assertEqual((root / "output.txt").read_text(), "BETA\n")


if __name__ == "__main__":
    unittest.main()
