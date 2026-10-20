import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import verify_alpaca_qlib_refresh as refresh


def bar(day="2026-08-17", **values):
    result = {"t": f"{day}T00:00:00Z", "o": 100, "h": 101, "l": 99, "c": 100.5, "v": 1234}
    result.update(values)
    return result


class BarsValidationTests(unittest.TestCase):
    def test_symbol_is_group_key_not_numeric_feature(self):
        self.assertEqual(refresh.CSV_FIELDS, ("date", "symbol", "open", "high", "low", "close", "volume"))
        self.assertEqual(refresh.QLIB_VALUE_FIELDS, ("open", "high", "low", "close", "volume"))
        rows = refresh._bars_for_symbol("AAPL", {"bars": [bar()]}, {date(2026, 8, 17)})
        self.assertEqual(rows[0]["symbol"], "AAPL")
        self.assertNotIn("symbol", refresh.QLIB_VALUE_FIELDS)

    def test_unapproved_symbol_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "SYMBOL_NOT_ALLOWED"):
            refresh._bars_for_symbol("SNDK", {"bars": [bar()]}, {date(2026, 8, 17)})

    def test_duplicate_and_unexpected_dates_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_DATE"):
            refresh._bars_for_symbol("AAPL", {"bars": [bar(), bar()]}, {date(2026, 8, 17)})
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_DATE"):
            refresh._bars_for_symbol("AAPL", {"bars": [bar("2026-08-18")]}, {date(2026, 8, 17)})

    def test_missing_nonfinite_and_pagination_inputs_fail_closed(self):
        bad = bar()
        del bad["v"]
        with self.assertRaisesRegex(ValueError, "BAR_SCHEMA_INVALID"):
            refresh._bars_for_symbol("AAPL", {"bars": [bad]}, {date(2026, 8, 17)})
        with self.assertRaisesRegex(ValueError, "NONFINITE_OHLCV"):
            refresh._bars_for_symbol("AAPL", {"bars": [bar(c=float("nan"))]}, {date(2026, 8, 17)})
        with self.assertRaisesRegex(ValueError, "PAGINATION_INCOMPLETE"):
            refresh._bars_for_symbol("AAPL", {"bars": [bar()], "next_page_token": "more"}, {date(2026, 8, 17)})


if __name__ == "__main__":
    unittest.main()
