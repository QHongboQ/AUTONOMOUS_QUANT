import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import date
from unittest import mock

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


class ForwardRawIsolationTests(unittest.TestCase):
    def test_xnys_last_completed_session_handles_close_dst_weekends_holidays_and_early_close(self):
        # October is EDT (20:00 UTC close); January is EST (21:00 UTC close).
        self.assertEqual(refresh.last_completed_xnys_session("2026-10-20T19:59:00Z")["status"], "SKIPPED_SESSION_NOT_COMPLETE")
        self.assertEqual(refresh.last_completed_xnys_session("2026-10-20T20:01:00Z")["session"], "2026-10-20")
        self.assertEqual(refresh.last_completed_xnys_session("2026-01-05T20:30:00Z")["status"], "SKIPPED_SESSION_NOT_COMPLETE")
        # Weekend and Thanksgiving do not fall back to a prior session.
        self.assertEqual(refresh.last_completed_xnys_session("2026-10-24T16:00:00Z")["status"], "SKIPPED_NON_TRADING_DAY")
        self.assertEqual(refresh.last_completed_xnys_session("2026-11-26T17:00:00Z")["status"], "SKIPPED_NON_TRADING_DAY")
        # Black Friday is an early close at 18:00 UTC, not 21:00 UTC.
        self.assertEqual(refresh.last_completed_xnys_session("2026-11-27T17:59:00Z")["status"], "SKIPPED_SESSION_NOT_COMPLETE")
        self.assertEqual(refresh.last_completed_xnys_session("2026-11-27T18:01:00Z")["session"], "2026-11-27")

    def test_xnys_last_completed_rejects_naive_or_invalid_time(self):
        with self.assertRaisesRegex(ValueError, "XNYS_NOW_UTC_MUST_BE_TIMEZONE_AWARE"):
            refresh.last_completed_xnys_session("2026-10-20T20:01:00")
        with self.assertRaisesRegex(ValueError, "XNYS_NOW_UTC_INVALID"):
            refresh.last_completed_xnys_session("not-a-time")

    def write_payload(self, directory: pathlib.Path, symbol: str, bars: list[dict]) -> bytes:
        raw = json.dumps({"bars": bars}, separators=(",", ":")).encode()
        (directory / f"{symbol}.json").write_bytes(raw)
        return raw

    def test_forward_fixture_is_stored_raw_outside_qlib_format(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp) / "FORWARD_RAW_ONLY"
            raw_dir = pathlib.Path(temp) / "input"
            raw_dir.mkdir()
            original = self.write_payload(raw_dir, "XYZ", [bar("2026-09-14")])
            result = refresh.store_forward_raw_only(
                raw_dir,
                "synthetic-sealed-session",
                "2026-09-14",
                "2026-09-14",
                ["XYZ"],
                root=root,
            )

            destination = root / "synthetic-sealed-session"
            self.assertEqual(result["status"], "FORWARD_RAW_ONLY_COMPLETE")
            self.assertEqual(result["source_attestation"], "UNVERIFIED_INPUT_PAYLOAD")
            self.assertEqual((destination / "XYZ.json").read_bytes(), original)
            self.assertTrue((destination / "manifest.json").is_file())
            self.assertFalse(any(destination.rglob("*.day.bin")))
            self.assertFalse((pathlib.Path(temp) / "P3" / "qlib-provider").exists())
            self.assertFalse((pathlib.Path(temp) / "P2").exists())

    def test_forward_cli_uses_separate_root_and_does_not_allow_replay_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp) / "forward"
            raw_dir = pathlib.Path(temp) / "input"
            raw_dir.mkdir()
            self.write_payload(raw_dir, "XYZ", [bar("2026-09-14")])
            argv = [
                "forward-raw-only",
                "--raw", str(raw_dir),
                "--output-id", "fixture-001",
                "--start", "2026-09-14",
                "--end", "2026-09-14",
                "--symbols", "XYZ",
            ]
            output = io.StringIO()
            with mock.patch.object(refresh, "FORWARD_RAW_ONLY_ROOT", root), contextlib.redirect_stdout(output):
                self.assertEqual(refresh.main(argv), 0)
            self.assertIn("FORWARD_RAW_ONLY_COMPLETE", output.getvalue())
            before = (root / "fixture-001" / "XYZ.json").read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(refresh.main(argv), 2)
            self.assertEqual((root / "fixture-001" / "XYZ.json").read_bytes(), before)

    def test_forward_storage_rejects_preseal_dates_and_bad_payloads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp) / "forward"
            raw_dir = pathlib.Path(temp) / "input"
            raw_dir.mkdir()
            self.write_payload(raw_dir, "XYZ", [bar("2026-09-14")])
            with self.assertRaisesRegex(ValueError, "FORWARD_RAW_RANGE_MUST_START"):
                refresh.store_forward_raw_only(raw_dir, "too-early", "2026-09-11", "2026-09-14", ["XYZ"], root=root)
            self.assertFalse(root.exists())

            self.write_payload(raw_dir, "XYZ", [bar("2026-09-14"), bar("2026-09-14")])
            with self.assertRaisesRegex(ValueError, "FORWARD_RAW_DUPLICATE_DATE"):
                refresh.store_forward_raw_only(raw_dir, "duplicate", "2026-09-14", "2026-09-14", ["XYZ"], root=root)
            self.assertFalse(root.exists())

    def test_forward_storage_requires_wsl_path_and_iso_dates(self):
        with tempfile.TemporaryDirectory() as temp:
            raw_dir = pathlib.Path(temp) / "input"
            raw_dir.mkdir()
            self.write_payload(raw_dir, "XYZ", [bar("2026-09-14")])
            with mock.patch.object(refresh.os, "name", "nt"):
                with self.assertRaisesRegex(ValueError, "FORWARD_RAW_ONLY_REQUIRES_WSL_PATH"):
                    refresh.store_forward_raw_only(raw_dir, "windows-path", "2026-09-14", "2026-09-14", ["XYZ"])
            with self.assertRaisesRegex(ValueError, "FORWARD_RAW_DATE_FORMAT"):
                refresh.store_forward_raw_only(raw_dir, "bad-date", "20260914", "2026-09-14", ["XYZ"])

    def test_research_calendar_still_rejects_post_cutoff(self):
        with self.assertRaisesRegex(ValueError, "DATE_RANGE_OUTSIDE_APPROVED_PRESEAL_SCOPE"):
            refresh.make_calendar("2026-09-14", "2026-09-14")

    def test_research_prepare_and_verify_reject_post_cutoff_before_io(self):
        missing = pathlib.Path("/does-not-exist")
        with self.assertRaisesRegex(ValueError, "DATE_RANGE_OUTSIDE_APPROVED_PRESEAL_SCOPE"):
            refresh.prepare(missing, missing, missing, "2026-09-14", "2026-09-14")
        with self.assertRaisesRegex(ValueError, "DATE_RANGE_OUTSIDE_APPROVED_PRESEAL_SCOPE"):
            refresh.verify(missing, missing, missing, missing, "2025-01-02", "2026-08-18", "2026-09-14")

    def test_research_worker_compose_does_not_mount_forward_raw_root(self):
        repository = pathlib.Path(__file__).resolve().parents[3]
        compose_dir = repository / "70-operations-system" / "research-handoff" / "docker-rdagent-smoke"
        for name in ("compose.yaml", "compose.deepseek-staging.yaml", "compose.persistent-test.yaml"):
            content = (compose_dir / name).read_text(encoding="utf-8")
            self.assertNotIn("FORWARD_RAW_ONLY", content)
            self.assertNotRegex(content, r"source:\s*/mnt/d/AQ_DATA\s*(?:\n|$)")
        standard = (compose_dir / "compose.yaml").read_text(encoding="utf-8")
        worker = standard.split("  rdagent-finquant-worker:", 1)[1].split("\nnetworks:", 1)[0]
        self.assertIn("/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source", worker)
        self.assertIn("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data", worker)
        self.assertIn("read_only: true", worker)
        staging = (compose_dir / "compose.deepseek-staging.yaml").read_text(encoding="utf-8")
        owner_worker = staging.split("  rdagent-owner-oneshot-worker:", 1)[1].split("\nnetworks:", 1)[0]
        self.assertIn("/mnt/d/AQ/OPERATIONS/P12/finquant-output/*/*", owner_worker)
        self.assertIn("create_host_path: false", owner_worker)


if __name__ == "__main__":
    unittest.main()
