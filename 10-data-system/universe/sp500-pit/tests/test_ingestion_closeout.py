import json
import os
from pathlib import Path
import tempfile
import unittest

from aq_pit.compiler import compile_universe
from aq_pit.contracts import CompilePolicyV1, SnapshotObservationV1, SourceManifestV1, SourceRole
from scripts.run_fja_ingestion import (
    DiagnosticRenameCandidate,
    PITINDEX_COMMIT,
    PITINDEX_REPOSITORY,
    _diagnostic_rename_report,
    _load_pitindex_rename_candidates,
    _parse_terminal_symbols,
    _pitindex_manifest,
    _terminal_roster,
)


H = "a" * 64


def seed_manifest() -> SourceManifestV1:
    return SourceManifestV1(
        "seed", SourceRole.HISTORICAL_SEED, "fixture", "https://example.invalid",
        "v1", "2026-09-10T00:00:00Z", "text/csv", 1, H, "fixture",
        "2010-01-04", "2024-12-31", (), "fixture-v1",
    )


class IngestionCloseoutTests(unittest.TestCase):
    def test_bzx_terminal_constituent_is_parsed(self):
        raw = b'id="constituents"\n|-\n|{{BZX link|CBOE}}\n|Cboe\n|}'
        self.assertEqual(_parse_terminal_symbols(raw), ("CBOE",))

    def test_pinned_terminal_reference_has_503_constituents(self):
        root = os.environ.get("AQ_PIT_DATA_ROOT")
        if not root:
            self.skipTest("AQ_PIT_DATA_ROOT is not configured")
        path = Path(root) / "raw" / "terminal_reference" / "wikipedia-sp500-oldid-1265285344.wikitext"
        if not path.is_file():
            self.skipTest("pinned terminal reference is unavailable")
        self.assertEqual(len(_terminal_roster(path.read_bytes())), 503)

    def test_pitindex_manifest_uses_pinned_repository_identity_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / "pitindex" / "data").mkdir(parents=True)
            (repo / "data").mkdir()
            metadata = {
                "indices": {"sp500": {"start_date": "2004-12-30", "end_date": "2026-09-07"}},
            }
            (repo / "pitindex" / "data" / "build_metadata.json").write_text(json.dumps(metadata))
            (repo / "pitindex" / "data" / "sp500_seed.csv").write_text("effective_date,ticker\n")
            (repo / "pitindex" / "data" / "sp500_changes.csv").write_text("date,action,ticker\n")
            (repo / "data" / "ticker_renames.csv").write_text("date,old_ticker,new_ticker,reason\n")
            manifest = _pitindex_manifest(repo, "2026-09-10T00:00:00Z", "fja-source")
        self.assertEqual(PITINDEX_REPOSITORY, "arielNacamulli/pitindex")
        self.assertEqual(manifest.source_url_or_repo, "https://github.com/arielNacamulli/pitindex")
        self.assertEqual(manifest.source_commit_or_revision, PITINDEX_COMMIT)
        self.assertEqual(manifest.coverage_end, "2026-09-07")

    def test_non_frozen_pitindex_candidate_enters_diagnostic_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ticker_renames.csv"
            path.write_text(
                "date,old_ticker,new_ticker,reason\n2018-10-31,PX,LIN,diagnostic\n",
                encoding="utf-8",
            )
            candidates = _load_pitindex_rename_candidates(path, "pitindex-diagnostic")
        observation = SnapshotObservationV1(
            "obs", "SP500", "2018-01-02", ("LIN",), "seed", H,
        )
        findings, _, ledger = _diagnostic_rename_report(
            (observation,), candidates, "seed",
        )
        self.assertEqual(len(candidates), 1)
        self.assertFalse(candidates[0].frozen_probe)
        self.assertEqual(len(findings), 1)
        self.assertEqual(ledger[0]["finding_type"], "FUTURE_TICKER_BACKFILL")

    def test_diagnostic_rename_rows_cannot_mutate_compile_state(self):
        observation = SnapshotObservationV1(
            "seed-row", "SP500", "2020-01-02", ("NEW",), "seed", H,
        )
        arguments = {
            "policy": CompilePolicyV1(
                "SP500", "2020-01-02", "2021-01-04", "fixture-calendar", "fixture-policy",
            ),
            "manifests": (seed_manifest(),),
            "observations": (observation,),
        }
        before = compile_universe(**arguments)
        raw_before = observation.tickers
        _diagnostic_rename_report(
            (observation,),
            (DiagnosticRenameCandidate("OLD", "NEW", "2020-06-01", ("diagnostic",)),),
            "seed",
        )
        after = compile_universe(**arguments)
        self.assertEqual(before, after)
        self.assertEqual(observation.tickers, raw_before)


if __name__ == "__main__":
    unittest.main()
