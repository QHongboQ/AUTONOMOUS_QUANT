"""Small data-quality adapter around Alpaca bars and pinned Qlib APIs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import pathlib
import sys
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

SYMBOLS = ("AAPL", "MSFT")
SOURCE_FIELDS = ("o", "h", "l", "c", "v")
CSV_FIELDS = ("date", "symbol", "open", "high", "low", "close", "volume")
QLIB_FIELDS = ("$open", "$high", "$low", "$close", "$volume")
QLIB_VALUE_FIELDS = ("open", "high", "low", "close", "volume")
FIELD_PAIRS = tuple(zip(SOURCE_FIELDS, QLIB_VALUE_FIELDS, strict=True))


def _day(value: str) -> date:
    return date.fromisoformat(value[:10])


def _bars_for_symbol(symbol: str, payload: dict, expected_days: set[date]) -> list[dict]:
    if symbol not in SYMBOLS:
        raise ValueError(f"SYMBOL_NOT_ALLOWED:{symbol}")
    if not isinstance(payload, dict) or not isinstance(payload.get("bars"), list):
        raise ValueError(f"BARS_ARRAY_INVALID:{symbol}")
    if payload.get("next_page_token"):
        raise ValueError(f"PAGINATION_INCOMPLETE:{symbol}")

    rows = []
    seen = set()
    for bar in payload["bars"]:
        try:
            timestamp = datetime.fromisoformat(bar["t"].replace("Z", "+00:00"))
            day = timestamp.astimezone(timezone.utc).date()
            values = {field: float(bar[key]) for key, field in FIELD_PAIRS}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"BAR_SCHEMA_INVALID:{symbol}") from exc
        if day in seen:
            raise ValueError(f"DUPLICATE_DATE:{symbol}:{day}")
        if day not in expected_days:
            raise ValueError(f"UNEXPECTED_DATE:{symbol}:{day}")
        if any(not math.isfinite(value) for value in values.values()):
            raise ValueError(f"NONFINITE_OHLCV:{symbol}:{day}")
        seen.add(day)
        rows.append({"date": day.isoformat(), "symbol": symbol, **values})

    if seen != expected_days:
        missing = sorted(day.isoformat() for day in expected_days - seen)
        raise ValueError(f"MISSING_XNYS_SESSIONS:{symbol}:{','.join(missing)}")
    return sorted(rows, key=lambda row: row["date"])


def make_calendar(start: str, end: str) -> dict:
    import exchange_calendars as xcals

    first, last = _day(start), _day(end)
    if last < first or last.isoformat() > "2026-09-11":
        raise ValueError("DATE_RANGE_OUTSIDE_APPROVED_PRESEAL_SCOPE")
    sessions = xcals.get_calendar("XNYS", start=first.isoformat(), end=last.isoformat())
    days = [item.date().isoformat() for item in sessions.sessions_in_range(first.isoformat(), last.isoformat())]
    if not days:
        raise ValueError("NO_EXPECTED_XNYS_SESSIONS")
    return {"calendar": "XNYS", "package": "exchange_calendars", "version": importlib.metadata.version("exchange-calendars"), "start": first.isoformat(), "end": last.isoformat(), "sessions": days}


def _read_calendar(path: pathlib.Path, start: str, end: str) -> list[str]:
    calendar = json.loads(path.read_text(encoding="utf-8"))
    if calendar.get("calendar") != "XNYS" or calendar.get("package") != "exchange_calendars":
        raise ValueError("CALENDAR_SOURCE_MISMATCH")
    if calendar.get("start") != start or calendar.get("end") != end:
        raise ValueError("CALENDAR_RANGE_MISMATCH")
    sessions = calendar.get("sessions")
    if not isinstance(sessions, list) or not sessions or len(sessions) != len(set(sessions)):
        raise ValueError("CALENDAR_SESSIONS_INVALID")
    if sessions != sorted(sessions):
        raise ValueError("CALENDAR_SESSIONS_NOT_SORTED")
    return sessions


def prepare(raw_dir: pathlib.Path, csv_dir: pathlib.Path, calendar_path: pathlib.Path, start: str, end: str) -> dict:
    expected_days = _read_calendar(calendar_path, start, end)
    expected = {_day(item) for item in expected_days}
    if not expected:
        raise ValueError("NO_EXPECTED_XNYS_SESSIONS")

    csv_dir.mkdir(parents=True, exist_ok=True)
    quality = []
    for symbol in SYMBOLS:
        raw_path = raw_dir / f"{symbol}.json"
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        rows = _bars_for_symbol(symbol, payload, expected)
        csv_path = csv_dir / f"{symbol}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
        raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        quality.append(
            {
                "symbol": symbol,
                "bars": len(rows),
                "first_date": rows[0]["date"],
                "last_date": rows[-1]["date"],
                "expected_xnys_sessions": len(expected),
                "available_xnys_sessions": len({row["date"] for row in rows}),
                "duplicate_dates": 0,
                "nonfinite_ohlcv_values": 0,
                "raw_sha256": raw_hash,
                "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            }
        )

    result = {
        "status": "INPUT_VALIDATED",
        "start": _day(start).isoformat(),
        "end": _day(end).isoformat(),
        "calendar": "XNYS",
        "calendar_source": json.loads(calendar_path.read_text(encoding="utf-8")),
        "symbols": quality,
        "numeric_fields": list(QLIB_VALUE_FIELDS),
    }
    (csv_dir / "input-validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def _tree_hash(root: pathlib.Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def verify(
    parent: pathlib.Path,
    provider: pathlib.Path,
    raw_dir: pathlib.Path,
    calendar_path: pathlib.Path,
    start: str,
    parent_end: str,
    end: str,
) -> dict:
    import qlib
    from qlib.data import D

    parent_before = _tree_hash(parent)
    qlib.init(provider_uri=str(parent), region="us")
    old = D.features(list(SYMBOLS), list(QLIB_FIELDS), start_time=start, end_time=parent_end)
    qlib.init(provider_uri=str(provider), region="us")
    new = D.features(list(SYMBOLS), list(QLIB_FIELDS), start_time=start, end_time=end)
    parent_after = _tree_hash(parent)
    if parent_before != parent_after:
        raise ValueError("PARENT_PROVIDER_CHANGED_DURING_VALIDATION")

    first, old_last, last = _day(start), _day(parent_end), _day(end)
    expected_dates = _read_calendar(calendar_path, first.isoformat(), last.isoformat())
    parent_dates = [line.strip() for line in (parent / "calendars/day.txt").read_text().splitlines() if line.strip()]
    candidate_dates = [line.strip() for line in (provider / "calendars/day.txt").read_text().splitlines() if line.strip()]
    if candidate_dates != expected_dates or parent_dates != expected_dates[: len(parent_dates)]:
        raise ValueError("QLIB_CALENDAR_MISMATCH")
    if len(parent_dates) != len([d for d in expected_dates if _day(d) <= old_last]):
        raise ValueError("PARENT_CALENDAR_LENGTH_MISMATCH")
    if len(set(candidate_dates)) != len(candidate_dates):
        raise ValueError("DUPLICATE_QLIB_CALENDAR_DATE")

    instrument_lines = (provider / "instruments/all.txt").read_text().splitlines()
    expected_instruments = {f"{symbol}\t{first.isoformat()}\t{last.isoformat()}" for symbol in SYMBOLS}
    if set(instrument_lines) != expected_instruments or len(instrument_lines) != len(SYMBOLS):
        raise ValueError("QLIB_INSTRUMENTS_MISMATCH")

    old_rows = new.loc[new.index.get_level_values("datetime") <= pd.Timestamp(old_last.isoformat())]
    if not old.equals(old_rows):
        raise ValueError("ORIGINAL_QLIB_ROWS_CHANGED")

    all_feature_files = sorted(p.name for p in (provider / "features").glob("*/" + "*.day.bin"))
    for symbol in ("aapl", "msft"):
        files = sorted(p.name for p in (provider / "features" / symbol).glob("*.day.bin"))
        if files != sorted(f"{field}.day.bin" for field in QLIB_VALUE_FIELDS):
            raise ValueError(f"UNEXPECTED_FEATURE_FILES:{symbol}:{files}")

    by_symbol = {}
    for symbol in SYMBOLS:
        part = new.xs(symbol, level="instrument")
        if len(part) != len(expected_dates) or part.isna().any().any() or not np.isfinite(part.to_numpy()).all():
            raise ValueError(f"QLIB_FEATURE_COVERAGE_INVALID:{symbol}")
        input_payload = json.loads((raw_dir / f"{symbol}.json").read_text(encoding="utf-8"))
        bars = input_payload["bars"]
        by_day = {
            datetime.fromisoformat(bar["t"].replace("Z", "+00:00")).astimezone(timezone.utc).date().isoformat(): bar
            for bar in bars
        }
        added = part.loc[part.index > pd.Timestamp(old_last.isoformat())]
        if len(added) != len([d for d in expected_dates if _day(d) > old_last]):
            raise ValueError(f"NEW_SESSION_COUNT_MISMATCH:{symbol}")
        for input_day, raw_bar in by_day.items():
            day = pd.Timestamp(input_day)
            row = part.loc[day]
            if raw_bar is None:
                raise ValueError(f"RAW_BAR_MISSING:{symbol}:{input_day}")
            for source_field, qlib_field in FIELD_PAIRS:
                expected_value = float(np.float32(float(raw_bar[source_field])))
                if not np.isclose(float(row[f"${qlib_field}"]), expected_value, rtol=0, atol=1e-6):
                    raise ValueError(f"RAW_VALUE_MISMATCH:{symbol}:{qlib_field}:{input_day}")
        by_symbol[symbol] = {
            "rows": len(part),
            "first_date": str(part.index.min().date()),
            "last_date": str(part.index.max().date()),
            "new_rows": len(added),
            "missing_values": int(part.isna().sum().sum()),
        }

    prefix_unchanged = True
    for symbol in ("aapl", "msft"):
        for field in QLIB_VALUE_FIELDS:
            rel = pathlib.Path("features") / symbol / f"{field}.day.bin"
            before, after = (parent / rel).read_bytes(), (provider / rel).read_bytes()
            if after[: len(before)] != before or len(after) - len(before) != (len(candidate_dates) - len(parent_dates)) * 4:
                prefix_unchanged = False
    if not prefix_unchanged:
        raise ValueError("QLIB_BINARY_PREFIX_CHANGED")

    return {
        "status": "PASS",
        "qlib_version": "0.9.8.dev26",
        "parent_provider_sha256": parent_before,
        "parent_provider_unchanged": parent_before == parent_after,
        "parent_sessions": len(parent_dates),
        "candidate_sessions": len(candidate_dates),
        "candidate_calendar_matches_xnys": True,
        "instruments_match": True,
        "d_features": "PASS",
        "original_rows_unchanged": True,
        "original_binary_prefix_unchanged": True,
        "added_values_match_raw_float32": True,
        "symbols": by_symbol,
        "unexpected_feature_files": False,
        "feature_file_count": len(all_feature_files),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--raw", type=pathlib.Path, required=True)
    prepare_parser.add_argument("--csv", type=pathlib.Path, required=True)
    prepare_parser.add_argument("--calendar", type=pathlib.Path, required=True)
    prepare_parser.add_argument("--start", required=True)
    prepare_parser.add_argument("--end", required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--parent", type=pathlib.Path, required=True)
    verify_parser.add_argument("--provider", type=pathlib.Path, required=True)
    verify_parser.add_argument("--raw", type=pathlib.Path, required=True)
    verify_parser.add_argument("--calendar", type=pathlib.Path, required=True)
    verify_parser.add_argument("--start", required=True)
    verify_parser.add_argument("--parent-end", required=True)
    verify_parser.add_argument("--end", required=True)
    calendar_parser = sub.add_parser("calendar")
    calendar_parser.add_argument("--start", required=True)
    calendar_parser.add_argument("--end", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "calendar":
            result = make_calendar(args.start, args.end)
        elif args.command == "prepare":
            result = prepare(args.raw, args.csv, args.calendar, args.start, args.end)
        else:
            result = verify(args.parent, args.provider, args.raw, args.calendar, args.start, args.parent_end, args.end)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:  # CLI reports stable failure category; traceback is retained by caller stderr.
        print(f"VALIDATION_FAILED:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
