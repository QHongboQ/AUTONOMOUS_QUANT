"""Create a deterministic DVC evidence seal for a completed or blocked rehearsal."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_lf_sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8"),
    ).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--activation", required=True, type=Path)
    parser.add_argument("--provider-report", required=True, type=Path)
    parser.add_argument("--primary-pred", required=True, type=Path)
    parser.add_argument("--control-pred", required=True, type=Path)
    parser.add_argument("--mlflow-db", required=True, type=Path)
    parser.add_argument("--blocker", required=True, type=Path)
    parser.add_argument("--historical-summary", required=True, type=Path)
    parser.add_argument("--runtime-day", required=True, type=Path)
    parser.add_argument("--runtime-future", required=True, type=Path)
    parser.add_argument("--qlib-report", required=True, type=Path)
    parser.add_argument("--daily-returns", required=True, type=Path)
    parser.add_argument("--skfolio-report", required=True, type=Path)
    parser.add_argument("--arch-report", required=True, type=Path)
    parser.add_argument("--validation-report", required=True, type=Path)
    parser.add_argument("--final-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    seal = {
        "schema_version": "P2HistoricalRehearsalEvidenceSealV1",
        "protocol_sha256_canonical_lf": canonical_lf_sha256(args.protocol),
        "activation_sha256_canonical_lf": canonical_lf_sha256(args.activation),
        "provider_report_sha256": sha256(args.provider_report),
        "primary_prediction_sha256": sha256(args.primary_pred),
        "control_prediction_sha256": sha256(args.control_pred),
        "mlflow_db_sha256": sha256(args.mlflow_db),
        "blocker_sha256": sha256(args.blocker),
        "historical_summary_sha256": sha256(args.historical_summary),
        "runtime_day_calendar_sha256": sha256(args.runtime_day),
        "runtime_future_calendar_sha256": sha256(args.runtime_future),
        "qlib_report_sha256": sha256(args.qlib_report),
        "daily_returns_sha256": sha256(args.daily_returns),
        "skfolio_report_sha256": sha256(args.skfolio_report),
        "arch_report_sha256": sha256(args.arch_report),
        "validation_report_sha256": sha256(args.validation_report),
        "final_summary_sha256": sha256(args.final_summary),
    }
    args.output.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(seal, sort_keys=True))


if __name__ == "__main__":
    main()
