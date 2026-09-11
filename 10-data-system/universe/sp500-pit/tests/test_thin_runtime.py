from __future__ import annotations

import ast
from dataclasses import fields, replace
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aq_pit.export import ResearchUniverseRowV1
from aq_pit.facts import accepted as accepted_module
from aq_pit.facts import load_accepted_facts
from aq_pit.gates.research_ready import assess_research_ready
from aq_pit.thin_runtime import build_research_ready_universe
from fixture_loader import load_fixture


DATA_ROOT = os.environ.get("AQ_PIT_DATA_ROOT")
SUMMARY = load_fixture("active_runtime_summary_v1.json")


@unittest.skipUnless(DATA_ROOT, "set AQ_PIT_DATA_ROOT for frozen real-data compatibility")
class ThinRuntimeRealDataIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.universe = build_research_ready_universe(Path(DATA_ROOT))
        cls.compilation = cls.universe.compilation

    def _episodes(self, ticker: str) -> list[tuple[str, str]]:
        return [
            (item.membership_from, item.membership_to)
            for item in self.compilation.episodes
            if item.normalized_ticker == ticker
        ]

    def test_static_fixture_counts(self) -> None:
        metrics = dict(self.universe.gate.metrics)
        expected = SUMMARY["counts"]
        for name in (
            "canonical_facts",
            "identity_events",
            "overlay_cases",
            "overlay_rows",
            "reconciled_membership_events",
            "instrument_episodes",
        ):
            self.assertEqual(metrics[name], expected[name])
        terminal = sum(
            item.valid_to == "2025-01-01" for item in self.compilation.episodes
        )
        self.assertEqual(terminal, expected["terminal_membership"])
        self.assertEqual(self.compilation.output_hash, SUMMARY["output_hash"])

    def test_gate_passes_without_runtime_domain_errors(self) -> None:
        self.assertTrue(self.universe.gate.research_ready)
        self.assertEqual(self.universe.gate.failures, ())
        self.assertEqual(self.compilation.domain_errors, ())

    def test_deterministic_compile_hash(self) -> None:
        repeated = build_research_ready_universe(Path(DATA_ROOT))
        self.assertEqual(repeated.compilation.output_hash, self.compilation.output_hash)
        self.assertEqual(repeated.rows, self.universe.rows)

    def test_rename_boundaries_and_backfill_coexistence(self) -> None:
        self.assertIn(("2012-12-24", "2017-12-05"), self._episodes("DLPH"))
        self.assertIn(("2017-12-05", "2025-01-01"), self._episodes("APTV"))
        self.assertIn(("2013-11-13", "2019-01-02"), self._episodes("KORS"))
        self.assertIn(("2019-01-02", "2020-05-12"), self._episodes("CPRI"))

    def test_reuse_boundaries_remain_distinct(self) -> None:
        self.assertEqual(
            self._episodes("Q"),
            [("2010-01-04", "2011-04-01"), ("2017-08-29", "2017-11-15")],
        )
        self.assertIn(("2017-11-15", "2025-01-01"), self._episodes("IQV"))
        self.assertEqual(len(self._episodes("GAS")), 2)
        self.assertIn(("2020-03-03", "2025-01-01"), self._episodes("TT"))
        self.assertIn(("2020-03-03", "2025-01-01"), self._episodes("IR"))

    def test_exit_reentry_gaps_remain_real(self) -> None:
        for ticker in ("AMD", "TER", "JBL", "FSLR", "EQT", "PCG"):
            episodes = self._episodes(ticker)
            self.assertEqual(len(episodes), 2, ticker)
            self.assertLess(episodes[0][1], episodes[1][0], ticker)

    def test_public_rows_are_primitive_and_minimal(self) -> None:
        self.assertEqual(
            tuple(field.name for field in fields(ResearchUniverseRowV1)),
            ("episode_id", "ticker", "membership_from", "membership_to"),
        )
        self.assertEqual(len(self.universe.rows), 832)

    def test_nondeterministic_result_fails_gate(self) -> None:
        result = assess_research_ready(
            self.compilation,
            self.universe.facts,
            deterministic=False,
        )
        self.assertFalse(result.research_ready)
        self.assertIn("NONDETERMINISTIC_COMPILE", result.failures)

    def test_domain_error_fails_gate(self) -> None:
        compilation = replace(self.compilation, domain_errors=("ADD_PRESENT:test",))
        result = assess_research_ready(
            compilation,
            self.universe.facts,
            deterministic=True,
        )
        self.assertFalse(result.research_ready)
        self.assertIn("MEMBERSHIP_OR_IDENTITY_DOMAIN_ERROR", result.failures)


class ThinRuntimeStructureTests(unittest.TestCase):
    def test_declarative_fact_set_is_complete(self) -> None:
        facts = load_accepted_facts()
        expected = SUMMARY["counts"]
        self.assertEqual(len(facts.finding_resolutions), expected["canonical_facts"])
        self.assertEqual(len(facts.identity_events), expected["identity_events"])
        self.assertEqual(len(facts.overlay_cases), expected["overlay_cases"])
        self.assertEqual(
            accepted_module._FACTS_SHA256,
            SUMMARY["accepted_facts_sha256"],
        )

    def test_accepted_facts_content_hash_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            altered = Path(directory) / "accepted_reconciliation_facts.json"
            altered.write_bytes(
                accepted_module._FACTS_PATH.read_bytes() + b"\n"
            )
            with patch.object(accepted_module, "_FACTS_PATH", altered):
                with self.assertRaisesRegex(ValueError, "frozen P1 authority"):
                    accepted_module.load_accepted_facts()

    def test_active_python_has_no_accepted_symbol_constants(self) -> None:
        root = Path(__file__).parents[1]
        facts = load_accepted_facts()
        symbols = {
            value
            for item in facts.identity_events
            for value in (item.old_ticker, item.new_ticker)
            if len(value) > 1
        }
        paths = (
            root / "aq_pit" / "thin_runtime.py",
            root / "aq_pit" / "domain" / "thin.py",
            root / "aq_pit" / "adapters" / "fja.py",
            root / "aq_pit" / "gates" / "research_ready" / "gate.py",
            root / "aq_pit" / "export" / "rows.py",
        )
        constants = {
            node.value
            for path in paths
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        self.assertFalse(symbols & constants)


if __name__ == "__main__":
    unittest.main()
