"""Bounded Pandera and XNYS validation of the Qlib-derived handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import exchange_calendars
import numpy as np
import pandas as pd
import pandera
import pandera.pandas as pa


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--provider-calendar", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)

    frame = pd.read_csv(args.input)
    schema = pa.DataFrameSchema(
        {
            "date": pa.Column(str, checks=pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$"), unique=True),
            "score": pa.Column(float, checks=pa.Check(lambda value: np.isfinite(value).all())),
            "label": pa.Column(float, checks=pa.Check(lambda value: np.isfinite(value).all())),
            "observations": pa.Column(int, checks=pa.Check.ge(1)),
            "benchmark_loss": pa.Column(float, checks=pa.Check(lambda value: np.isfinite(value).all())),
            "model_loss": pa.Column(float, checks=pa.Check(lambda value: np.isfinite(value).all())),
        },
        strict=True,
        coerce=True,
    )
    validated = schema.validate(frame)

    calendar = exchange_calendars.get_calendar(
        "XNYS", start="2015-01-02", end="2024-12-31",
    )
    expected = tuple(
        value.strftime("%Y-%m-%d")
        for value in calendar.sessions_in_range("2015-01-02", "2024-12-31")
    )
    actual = tuple(
        line.strip() for line in args.provider_calendar.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise RuntimeError(f"XNYS mismatch: missing={missing}, extra={extra}")
    if not set(validated["date"]).issubset(set(expected)):
        raise RuntimeError("Qlib-derived evidence contains a non-XNYS date")

    report = {
        "duplicate_dates": int(validated["date"].duplicated().sum()),
        "exchange_calendars_version": exchange_calendars.__version__,
        "finite_numeric_values": "PASS",
        "input_rows": len(validated),
        "input_sha256": sha256(args.input),
        "pandera": "PASS",
        "pandera_version": pandera.__version__,
        "provider_calendar_rows": len(actual),
        "xnys_calendar_match": "PASS",
    }
    path = args.output / "validation-report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
