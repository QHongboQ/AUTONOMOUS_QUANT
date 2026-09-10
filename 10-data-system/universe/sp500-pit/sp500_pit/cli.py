"""Write deterministic universe evidence from a frozen source revision."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from .canonical import canonical_bytes, sha256
from .parser import parse_sp500_html
from .reconstruct import build_symbol_mapping, interval_hash, mapping_hash, reconstruct_membership, universe_hash
from .validate import compare_qlib_overlap, parse_qlib_sp500, terminal_state_difference, unresolved_mappings, validate_intervals


QLIB_SAMPLE_DATES = ("2012-06-29", "2014-06-30", "2016-06-30", "2018-06-29", "2020-06-30")
ACTIVE_COUNT_DATES = ("2012-06-29", "2016-06-30", "2020-06-30", "2022-06-30", "2024-06-28", "2024-12-31")


def write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_bytes(value) + b"\n")


def run_reconstruct(args: argparse.Namespace) -> int:
    source_path = Path(args.html)
    html = source_path.read_text(encoding="utf-8")
    parsed = parse_sp500_html(html)
    intervals = reconstruct_membership(parsed.current_constituents, parsed.changes, args.start, args.cutoff)
    validate_intervals(intervals)
    terminal = terminal_state_difference(parsed.current_constituents, intervals, args.cutoff)
    mappings = build_symbol_mapping(intervals, args.start, f"{int(args.cutoff[:4]) + 1:04d}-01-01")
    unresolved = unresolved_mappings(intervals, mappings)
    if unresolved:
        raise SystemExit(f"unresolved active price identities: {unresolved}")

    membership_value = [asdict(item) for item in intervals]
    mapping_value = [asdict(item) for item in mappings]
    source_manifest = {
        "schema_version": "SP500_PIT_SOURCE_EVIDENCE_V1",
        "parser_version": "SP500_PIT_PARSER_V1",
        "source_url": args.source_url,
        "retrieved_at": args.retrieved_at,
        "revision_id": args.revision_id,
        "http_metadata": json.loads(args.http_metadata),
        "content_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "current_table_schema": parsed.current_schema,
        "change_table_schema": parsed.change_schema,
        "logical_identity_excludes_absolute_paths": True,
    }
    report: dict[str, object] = {
        "schema_version": "SP500_PIT_VALIDATION_V2",
        "interval_semantics": "half_open_start_inclusive_end_exclusive",
        "period_start": args.start,
        "period_end_inclusive": args.cutoff,
        "current_constituent_count": len(parsed.current_constituents),
        "change_history_start": min(value.effective_date for value in parsed.changes),
        "change_history_end": max(value.effective_date for value in parsed.changes),
        "membership_interval_count": len(intervals),
        "logical_security_count": len({value.logical_security_identity for value in intervals}),
        "active_count_samples": [{"date": day, "active_count": sum(item.membership_start <= day < item.membership_end for item in intervals)} for day in ACTIVE_COUNT_DATES],
        "unresolved_active_symbols": unresolved,
        "membership_intervals_hash": interval_hash(intervals),
        "symbol_mapping_hash": mapping_hash(mappings),
        "universe_source_hash": sha256(source_manifest),
        "universe_hash": universe_hash(intervals, mappings),
        "terminal_state": terminal,
        "acceptance_policy": "The reconstructed terminal state must exactly match the frozen current constituent table; otherwise PIT_UNIVERSE is BLOCKED.",
    }
    if args.baseline_sp500:
        report["qlib_overlap"] = compare_qlib_overlap(intervals, parse_qlib_sp500(Path(args.baseline_sp500)), QLIB_SAMPLE_DATES)
        report["qlib_overlap_unexplained_unique_identities"] = sorted({identity for row in report["qlib_overlap"] for key in ("new_only", "old_only") for identity in row[key]})
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if not terminal["matches"]:
        report["pit_universe"] = "BLOCKED"
        report["blocker"] = "FROZEN_WIKIPEDIA_CHANGE_HISTORY_INCOMPLETE_TERMINAL_STATE_MISMATCH"
        write_json(out / "source_evidence_manifest.json", source_manifest)
        write_json(out / "validation_report.json", report)
        print(json.dumps({"pit_universe": "BLOCKED", "terminal_state": terminal}, sort_keys=True))
        return 2
    if report.get("qlib_overlap_unexplained_unique_identities"):
        report["pit_universe"] = "BLOCKED"
        report["blocker"] = "QLIB_OVERLAP_IDENTITY_DIFFERENCES_REQUIRE_FIRST_PARTY_RESOLUTION"
    else:
        report["pit_universe"] = "PASS"
    write_json(out / "membership_intervals.json", membership_value)
    write_json(out / "symbol_mapping.json", mapping_value)
    write_json(out / "source_evidence_manifest.json", source_manifest)
    write_json(out / "validation_report.json", report)
    print(json.dumps({key: report[key] for key in ("membership_interval_count", "membership_intervals_hash", "symbol_mapping_hash", "universe_hash")}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    reconstruct = commands.add_parser("reconstruct")
    reconstruct.add_argument("--html", required=True)
    reconstruct.add_argument("--out", required=True)
    reconstruct.add_argument("--source-url", required=True)
    reconstruct.add_argument("--retrieved-at", required=True)
    reconstruct.add_argument("--revision-id", required=True)
    reconstruct.add_argument("--http-metadata", required=True)
    reconstruct.add_argument("--start", default="2010-01-01")
    reconstruct.add_argument("--cutoff", default="2024-12-31")
    reconstruct.add_argument("--baseline-sp500")
    reconstruct.set_defaults(func=run_reconstruct)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
