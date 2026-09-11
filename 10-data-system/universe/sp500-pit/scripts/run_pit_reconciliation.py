"""Materialize the accepted PIT reconciliation into a distinct output tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from aq_pit.canonical import canonical_bytes, sha256_hex
from aq_pit.reconciliation import (
    all_gates_pass,
    build_reconciliation,
    parse_terminal_roster,
)
from aq_pit.sources.fja_sp500 import build_fja_manifest, parse_fja_snapshots


FJA_COMMIT = "a2430f2af0c79ddf0748e91de11bdeb1616ab5a7"
FJA_SOURCE_FILE = "S&P 500 Historical Components & Changes (Updated).csv"
EXPECTED_FJA_SHA256 = "646b2e47284abfb675abebacd4a4035ba22a79ea1ccdeccce7fbe5f0e27bab3a"
RETRIEVED_AT = "2026-09-11T01:08:50Z"


def _write_canonical(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    temporary.replace(path)


def _write_jsonl(path: Path, values: tuple[object, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        for value in values:
            handle.write(canonical_bytes(value) + b"\n")
    temporary.replace(path)


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(data_root: Path, output_root: Path) -> dict[str, object]:
    fja_path = data_root / "raw" / "fja_sp500" / "repo" / FJA_SOURCE_FILE
    raw = fja_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FJA_SHA256:
        raise ValueError("immutable FJA source hash differs from the accepted ingestion evidence")
    seed_manifest = build_fja_manifest(
        raw, commit=FJA_COMMIT, source_file=FJA_SOURCE_FILE, retrieved_at=RETRIEVED_AT,
    )
    observations = parse_fja_snapshots(
        raw, seed_manifest, start_date="2010-01-01", end_date="2024-12-31",
        start_session="2010-01-04",
    )
    historical_ledger = tuple(json.loads(
        (data_root / "audit" / "unresolved_findings" / "unresolved_findings.json").read_text(encoding="utf-8")
    ))
    terminal_roster = parse_terminal_roster(
        (data_root / "raw" / "terminal_reference" / "wikipedia-sp500-oldid-1265285344.wikitext").read_bytes()
    )
    first = build_reconciliation(
        seed_manifest=seed_manifest, observations=observations,
        historical_ledger=historical_ledger, terminal_roster=terminal_roster,
    )
    second = build_reconciliation(
        seed_manifest=seed_manifest, observations=observations,
        historical_ledger=historical_ledger, terminal_roster=terminal_roster,
    )
    determinism = {
        "identity_events": first.identity_events == second.identity_events,
        "overlays": first.overlays == second.overlays,
        "membership_events": first.membership_events == second.membership_events,
        "episodes": first.compilation.episodes == second.compilation.episodes,
        "findings": first.compilation.findings == second.compilation.findings,
        "compilation_hash": first.compilation.output_hash == second.compilation.output_hash,
    }
    if not all(determinism.values()) or not all_gates_pass(first.gate_results):
        raise RuntimeError(json.dumps({"determinism": determinism, "gates": first.gate_results}, indent=2))

    files: dict[str, object] = {
        "accepted_ticker_identity_events.jsonl": first.identity_events,
        "accepted_ticker_overlays.jsonl": first.overlays,
        "reconciled_membership_events.jsonl": first.membership_events,
        "instrument_episodes.jsonl": first.compilation.episodes,
    }
    for name, values in files.items():
        _write_jsonl(output_root / name, values)  # type: ignore[arg-type]
    _write_canonical(output_root / "reconciled_membership_event_manifest.json", first.reconciled_manifest)
    _write_canonical(output_root / "provenance_source_manifests.json", (seed_manifest, *first.evidence_manifests, first.reconciled_manifest))
    _write_canonical(output_root / "resolved_reconciliation_ledger.json", first.resolved_ledger)
    summary = {
        "schema_version": "P1PitReconciliationSummaryV1",
        "raw_fja_sha256": EXPECTED_FJA_SHA256,
        "counts": {
            "canonical_findings": len(first.resolved_ledger),
            "resolved_findings": sum(item["resolution_state"] == "RESOLVED" for item in first.resolved_ledger),
            "identity_events": len(first.identity_events),
            "overlay_cases": len({item.reason.rsplit(" ", 1)[-1] for item in first.overlays}),
            "overlay_rows": len(first.overlays),
            "reconciled_membership_events": len(first.membership_events),
            "instrument_episodes": len(first.compilation.episodes),
            "terminal_roster": len(terminal_roster),
        },
        "compilation_hash": first.compilation.output_hash,
        "determinism": determinism,
        "gates": first.gate_results,
        "safety": {
            "raw_fja_mutated": False,
            "symbol_specific_runtime_conditions": 0,
            "permanent_security_master_added": False,
            "corporate_lineage_graph_added": False,
        },
    }
    _write_canonical(output_root / "compilation_summary.json", summary)
    artifact_names = tuple(sorted(
        path.name for path in output_root.iterdir()
        if path.is_file() and path.name != "artifact_manifest.json"
    ))
    artifact_manifest = {
        "schema_version": "P1PitReconciliationArtifactManifestV1",
        "logical_root": "P1/pit/reconciled/v1",
        "artifacts": tuple(
            {"relative_path": name, "sha256": _file_hash(output_root / name), "byte_length": (output_root / name).stat().st_size}
            for name in artifact_names
        ),
        "logical_hash": sha256_hex({"summary": summary, "artifacts": artifact_names}),
    }
    _write_canonical(output_root / "artifact_manifest.json", artifact_manifest)
    final = {
        **summary,
        "artifact_manifest_sha256": _file_hash(output_root / "artifact_manifest.json"),
        "output_files": {
            path.name: _file_hash(path)
            for path in sorted(output_root.iterdir()) if path.is_file()
        },
    }
    print(json.dumps(final, indent=2))
    return final


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    run(args.data_root, args.output_root)


if __name__ == "__main__":
    main()
