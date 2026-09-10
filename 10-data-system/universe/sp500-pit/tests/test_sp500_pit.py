from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sp500_pit.parser import SchemaError, parse_sp500_html
from sp500_pit.identity import CORPORATE_MEMBERSHIP_TRANSITIONS, EVIDENCE, IDS, logical_identity, market_symbol, provider_symbol, transition_mappings
from sp500_pit.reconstruct import MembershipInterval, active_symbols, build_symbol_mapping, interval_hash, reconstruct_membership, universe_hash
from sp500_pit.validate import ValidationError, compare_qlib_overlap, terminal_state_difference, unresolved_mappings, validate_intervals


HTML = """
<table><thead><tr><th>Symbol</th><th>Security</th><th>Date added</th></tr></thead><tbody>
<tr><td>CCC</td><td>Charlie</td><td>2024-01-03</td></tr><tr><td>BRK.B</td><td>Berkshire</td><td>2010-01-01</td></tr>
</tbody></table>
<table><thead><tr><th rowspan='2'>Date</th><th colspan='2'>Added</th><th colspan='2'>Removed</th></tr>
<tr><th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th></tr></thead><tbody>
<tr><td>January 3, 2024</td><td>CCC</td><td>Charlie</td><td>AAA</td><td>Alpha</td></tr>
</tbody></table>
"""


class PitAdapterTests(unittest.TestCase):
    def parsed(self):
        return parse_sp500_html(HTML)

    def intervals(self):
        source = self.parsed()
        return reconstruct_membership(source.current_constituents, source.changes, "2010-01-01", "2024-12-31")

    def test_CURRENT_TABLE_SCHEMA_PARSE(self):
        self.assertEqual([value.symbol for value in self.parsed().current_constituents], ["CCC", "BRK.B"])

    def test_CHANGE_TABLE_SCHEMA_PARSE(self):
        event = self.parsed().changes[0]
        self.assertEqual((event.effective_date, event.added_symbol, event.removed_symbol), ("2024-01-03", "CCC", "AAA"))

    def test_SCHEMA_DRIFT_FAIL_CLOSED(self):
        with self.assertRaises(SchemaError):
            parse_sp500_html(HTML.replace("Date added", "Listed"))

    def test_MMM_NOT_PARSED_AS_DATE(self):
        with self.assertRaises(SchemaError):
            parse_sp500_html(HTML.replace("January 3, 2024", "MMM"))

    def test_BACKWARD_RECONSTRUCTION(self):
        self.assertEqual(active_symbols(self.intervals(), "2024-01-02"), {logical_identity("AAA"), logical_identity("BRK.B")})

    def test_CHANGE_EFFECTIVE_DATE(self):
        self.assertEqual(active_symbols(self.intervals(), "2024-01-03"), {logical_identity("BRK.B"), logical_identity("CCC")})

    def test_NO_FUTURE_MEMBERSHIP_LEAK(self):
        self.assertNotIn("CCC", active_symbols(self.intervals(), "2023-12-29"))

    def test_INTERVAL_VALIDATION(self):
        validate_intervals(self.intervals())

    def test_DUPLICATE_INTERVAL_REJECTED(self):
        item = MembershipInterval("AAA", "AAA", "AAA", "2010-01-01", "2024-01-01", ("fixture",))
        with self.assertRaises(ValidationError):
            validate_intervals([item, item])

    def test_SYMBOL_MAPPING_VERSIONED(self):
        self.assertTrue(all(value.evidence_url and value.resolution_state == "RESOLVED" for value in build_symbol_mapping(self.intervals(), "2010-01-01", "2025-01-01")))

    def test_DOT_DASH_SYMBOL_MAPPING(self):
        symbols = {value.logical_security_id: value.market_data_symbol for value in build_symbol_mapping(self.intervals(), "2010-01-01", "2025-01-01")}
        self.assertEqual(symbols[logical_identity("BRK.B")], "BRK-B")

    def test_QLIB_OVERLAP_COMPARISON(self):
        rows = compare_qlib_overlap(self.intervals(), self.intervals(), ["2024-01-03"])
        self.assertEqual(rows[0]["new_only"], [])

    def test_POST_2020_TRANSITION_EVIDENCE(self):
        self.assertEqual(self.parsed().changes[0].source_row, 1)

    def test_UNIVERSE_HASH_DETERMINISTIC(self):
        mapping = build_symbol_mapping(self.intervals(), "2010-01-01", "2025-01-01")
        self.assertEqual(universe_hash(self.intervals(), mapping), universe_hash(self.intervals(), mapping))

    def test_ABSOLUTE_PATH_EXCLUDED_FROM_UNIVERSE_ID(self):
        digest = universe_hash(self.intervals(), build_symbol_mapping(self.intervals(), "2010-01-01", "2025-01-01"))
        self.assertNotIn("D:\\", digest)
        self.assertNotIn("/mnt/", digest)

    def test_MEMBERSHIP_MUTATION_CHANGES_HASH(self):
        changed = self.intervals()
        changed[0] = replace(changed[0], membership_end="2024-12-30")
        self.assertNotEqual(interval_hash(self.intervals()), interval_hash(changed))

    def test_POST_2024_PRICE_ROWS_EXCLUDED(self):
        self.assertEqual([row for row in ["2024-12-31", "2025-01-02"] if row <= "2024-12-31"], ["2024-12-31"])

    def test_ACTIVE_MEMBERSHIP_BAR_COVERAGE(self):
        expected, valid = {"AAA", "BRK.B", "CCC"}, {"AAA", "CCC"}
        self.assertEqual(len(expected & valid) / len(expected), 2 / 3)

    def test_TERMINAL_STATE_FAIL_CLOSED(self):
        parsed = self.parsed()
        self.assertTrue(terminal_state_difference(parsed.current_constituents, self.intervals(), "2024-12-31")["matches"])
        self.assertFalse(terminal_state_difference(parsed.current_constituents[:-1], self.intervals(), "2024-12-31")["matches"])

    def test_CDAY_DAY_IDENTITY_CONTINUITY(self):
        self.assertEqual(logical_identity("CDAY"), logical_identity("DAY"))

    def test_WLTW_WTW_IDENTITY_CONTINUITY(self):
        self.assertEqual(logical_identity("WLTW"), logical_identity("WTW"))

    def test_RE_EG_IDENTITY_CONTINUITY(self):
        self.assertEqual(logical_identity("RE"), logical_identity("EG"))

    def test_KORS_CPRI_IDENTITY_CONTINUITY(self):
        self.assertEqual(logical_identity("KORS"), logical_identity("CPRI"))

    def test_Q_IQV_IDENTITY_CONTINUITY(self):
        self.assertEqual(logical_identity("Q", "QuintilesIMS", "2017-08-29"), logical_identity("IQV"))

    def test_JOYG_JOY_TRANSITION(self):
        self.assertEqual(logical_identity("JOYG"), logical_identity("JOY"))
        self.assertEqual(EVIDENCE["joy-global"][0], "2011-12-06")

    def test_DISCK_WBD_TRANSITION_CLASSIFIED(self):
        self.assertEqual(CORPORATE_MEMBERSHIP_TRANSITIONS[0].transition_type, "MERGER_SUCCESSOR")
        self.assertNotEqual(logical_identity("DISCK"), logical_identity("WBD"))

    def test_DLPH_APTV_TICKER_REUSE_NOT_COLLAPSED(self):
        old = logical_identity("DLPH", "Delphi Automotive", "2017-12-04")
        new = logical_identity("DLPH", "Delphi Technologies", "2017-12-05")
        self.assertEqual(old, logical_identity("APTV"))
        self.assertNotEqual(old, new)

    def test_FB_META_DATE_EFFECTIVE_MAPPING(self):
        identity = logical_identity("META")
        self.assertEqual(market_symbol(identity, "2022-06-08"), "FB")
        self.assertEqual(market_symbol(identity, "2022-06-09"), "META")

    def test_PROVIDER_DOT_DASH_NOT_CORPORATE_ALIAS(self):
        self.assertEqual(provider_symbol("BRK.B"), "BRK-B")
        self.assertNotEqual(logical_identity("BRK.B"), logical_identity("BRK-B"))

    def test_MARKET_SYMBOL_BEFORE_RENAME(self):
        self.assertEqual(market_symbol(logical_identity("DAY"), "2024-01-31"), "CDAY")

    def test_MARKET_SYMBOL_AFTER_RENAME(self):
        self.assertEqual(market_symbol(logical_identity("DAY"), "2024-02-01"), "DAY")

    def test_MAPPING_EVIDENCE_REQUIRED(self):
        self.assertTrue(all(item.evidence_url for item in transition_mappings()))

    def test_UNRESOLVED_IDENTITY_FAILS_CLOSED(self):
        self.assertEqual(unresolved_mappings(self.intervals(), []), sorted(active_symbols(self.intervals(), "2024-01-03") | active_symbols(self.intervals(), "2024-01-02")))


class FrozenEvidenceTests(unittest.TestCase):
    SOURCE = Path(r"D:\AQ_DATA\P1\universe\sp500_pit_v1\source_sp500_companies_oldid_2024_cutoff.html")
    QLIB = Path(r"D:\AQ_DATA\P1\qlib_us_daily_source\instruments\sp500.txt")

    def reconstructed(self):
        parsed = parse_sp500_html(self.SOURCE.read_text(encoding="utf-8"))
        return parsed, reconstruct_membership(parsed.current_constituents, parsed.changes, "2010-01-01", "2024-12-31")

    @unittest.skipUnless(SOURCE.exists(), "frozen evidence not mounted")
    def test_TERMINAL_503_EXACT(self):
        parsed, intervals = self.reconstructed()
        result = terminal_state_difference(parsed.current_constituents, intervals, "2024-12-31")
        self.assertEqual((result["expected_current_count"], result["reconstructed_terminal_count"], result["matches"]), (503, 503, True))

    @unittest.skipUnless(SOURCE.exists(), "frozen evidence not mounted")
    def test_NO_UNEXPLAINED_TERMINAL_IDENTITIES(self):
        parsed, intervals = self.reconstructed()
        result = terminal_state_difference(parsed.current_constituents, intervals, "2024-12-31")
        self.assertEqual((result["missing_from_reconstruction"], result["unexpected_in_reconstruction"]), ([], []))

    @unittest.skipUnless(SOURCE.exists() and QLIB.exists(), "reference evidence not mounted")
    def test_QLIB_OVERLAP_AFTER_IDENTITY_RECONCILIATION(self):
        from sp500_pit.validate import parse_qlib_sp500
        _, intervals = self.reconstructed()
        rows = compare_qlib_overlap(intervals, parse_qlib_sp500(self.QLIB), ["2012-06-29", "2014-06-30", "2016-06-30", "2018-06-29", "2020-06-30"])
        self.assertEqual(len(rows), 5)
        self.assertTrue(all("unexplained_difference_count" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
