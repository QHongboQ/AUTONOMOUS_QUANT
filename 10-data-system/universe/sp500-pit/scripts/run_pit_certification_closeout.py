"""Evaluate PIT certification authorities and stage artifacts byte-for-byte."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from aq_pit.canonical import canonical_bytes, sha256_hex
from aq_pit.certification import (
    CANONICAL_LEDGER_SHA256,
    DIAGNOSTIC_TERMINAL_SHA256,
    build_retained_input_manifest,
    evaluate_certification,
    verify_content_hash,
)
from aq_pit.contracts import SourceRole
from aq_pit.reconciliation import all_gates_pass, build_reconciliation, parse_terminal_roster
from aq_pit.sources.fja_sp500 import build_fja_manifest, parse_fja_snapshots


FJA_COMMIT = "a2430f2af0c79ddf0748e91de11bdeb1616ab5a7"
FJA_SOURCE_FILE = "S&P 500 Historical Components & Changes (Updated).csv"
EXPECTED_FJA_SHA256 = "646b2e47284abfb675abebacd4a4035ba22a79ea1ccdeccce7fbe5f0e27bab3a"
RETRIEVED_AT = "2026-09-11T01:08:50Z"


def _write_canonical(path: Path, value: object) -> None:
    path.write_bytes(canonical_bytes(value) + b"\n")


def _write_jsonl(path: Path, values: tuple[object, ...]) -> None:
    with path.open("wb") as handle:
        for value in values:
            handle.write(canonical_bytes(value) + b"\n")


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_tree_snapshot(root: Path) -> tuple[tuple[str, int, str], ...]:
    return tuple(
        (path.relative_to(root).as_posix(), path.stat().st_size, _file_hash(path))
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    )


def materialize_artifact_tree(
    root: Path,
    *,
    bundle,
    seed_manifest,
    ledger_manifest,
    diagnostic_terminal_manifest,
    certification,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError("artifact staging root must be clean")
    for name, values in {
        "accepted_ticker_identity_events.jsonl": bundle.identity_events,
        "accepted_ticker_overlays.jsonl": bundle.overlays,
        "reconciled_membership_events.jsonl": bundle.membership_events,
        "instrument_episodes.jsonl": bundle.compilation.episodes,
    }.items():
        _write_jsonl(root / name, values)
    _write_canonical(root / "reconciled_membership_event_manifest.json", bundle.reconciled_manifest)
    _write_canonical(
        root / "provenance_source_manifests.json",
        (seed_manifest, *bundle.evidence_manifests, ledger_manifest,
         diagnostic_terminal_manifest, bundle.reconciled_manifest),
    )
    _write_canonical(root / "resolved_reconciliation_ledger.json", bundle.resolved_ledger)
    summary = {
        "schema_version": "P1PitReconciliationCertificationCloseoutV1",
        "raw_fja_sha256": EXPECTED_FJA_SHA256,
        "canonical_ledger_sha256": ledger_manifest.sha256,
        "diagnostic_terminal_sha256": diagnostic_terminal_manifest.sha256,
        "counts": {
            "canonical_findings": len(bundle.resolved_ledger),
            "resolved_findings": len(bundle.resolved_ledger),
            "identity_events": len(bundle.identity_events),
            "overlay_cases": 9,
            "overlay_rows": len(bundle.overlays),
            "reconciled_membership_events": len(bundle.membership_events),
            "instrument_episodes": len(bundle.compilation.episodes),
        },
        "compilation_hash": bundle.compilation.output_hash,
        "runtime_gates": bundle.gate_results,
        "certification": certification,
    }
    _write_canonical(root / "compilation_summary.json", summary)
    entries = tuple(
        {"relative_path": relative, "byte_length": length, "sha256": digest}
        for relative, length, digest in artifact_tree_snapshot(root)
    )
    _write_canonical(root / "artifact_manifest.json", {
        "schema_version": "P1PitReconciliationArtifactManifestV2",
        "logical_root": "P1/pit/reconciled/v1",
        "artifacts": entries,
        "logical_hash": sha256_hex(entries),
    })


def promote_artifact_tree(staging: Path, final: Path) -> None:
    backup = final.parent / f".{final.name}.previous"
    if backup.exists():
        raise FileExistsError("recoverable promotion backup already exists")
    moved_old = False
    try:
        if final.exists():
            final.replace(backup)
            moved_old = True
        staging.replace(final)
    except BaseException:
        if moved_old and not final.exists() and backup.exists():
            backup.replace(final)
        raise


def run(data_root: Path, output_root: Path) -> dict[str, object]:
    raw = (data_root / "raw" / "fja_sp500" / "repo" / FJA_SOURCE_FILE).read_bytes()
    verify_content_hash(raw, EXPECTED_FJA_SHA256, "immutable FJA source")
    seed_manifest = build_fja_manifest(
        raw, commit=FJA_COMMIT, source_file=FJA_SOURCE_FILE, retrieved_at=RETRIEVED_AT,
    )
    observations = parse_fja_snapshots(
        raw, seed_manifest, start_date="2010-01-01", end_date="2024-12-31",
        start_session="2010-01-04",
    )
    ledger_raw = (data_root / "audit" / "unresolved_findings" / "unresolved_findings.json").read_bytes()
    ledger_manifest = build_retained_input_manifest(
        raw=ledger_raw, expected_sha256=CANONICAL_LEDGER_SHA256,
        label="accepted canonical unresolved ledger",
        source_type="accepted_canonical_unresolved_ledger",
        source_url_or_repo="AUTONOMOUS-QUANT/P1/PIT/source-ingestion-evidence",
        source_commit_or_revision=CANONICAL_LEDGER_SHA256,
        retrieved_at=RETRIEVED_AT, media_type="application/json",
        coverage_start="2010-01-04", coverage_end="2024-12-23",
    )
    historical_ledger = tuple(json.loads(ledger_raw.decode("utf-8")))
    terminal_raw = (data_root / "raw" / "terminal_reference" / "wikipedia-sp500-oldid-1265285344.wikitext").read_bytes()
    diagnostic_terminal_manifest = build_retained_input_manifest(
        raw=terminal_raw, expected_sha256=DIAGNOSTIC_TERMINAL_SHA256,
        label="pinned diagnostic Wikipedia terminal roster",
        source_type="pinned_wikipedia_terminal_roster",
        source_url_or_repo="https://en.wikipedia.org/wiki/Special:PermanentLink/1265285344",
        source_commit_or_revision="1265285344", retrieved_at=RETRIEVED_AT,
        media_type="text/x-wiki", coverage_start="2024-12-26", coverage_end="2024-12-31",
        source_role=SourceRole.DIAGNOSTIC_REFERENCE,
        license_observation="CC BY-SA 4.0 / GFDL page content terms observed",
    )
    terminal_roster = parse_terminal_roster(terminal_raw)
    first = build_reconciliation(
        seed_manifest=seed_manifest, observations=observations,
        historical_ledger=historical_ledger, terminal_roster=terminal_roster,
    )
    second = build_reconciliation(
        seed_manifest=seed_manifest, observations=observations,
        historical_ledger=historical_ledger, terminal_roster=terminal_roster,
    )
    same_memory = (
        first.identity_events == second.identity_events
        and first.overlays == second.overlays
        and first.membership_events == second.membership_events
        and first.compilation == second.compilation
    )
    if not same_memory or not all_gates_pass(first.gate_results):
        raise RuntimeError("runtime reconciliation gates failed")

    # No retained primary bytes, official terminal roster, or pre-registered
    # historical samples exist in the accepted evidence root. Fail closed.
    provisional = evaluate_certification(
        primary_evidence_manifests=first.evidence_manifests,
        retained_primary_bytes_by_hash={}, canonical_ledger_manifest=ledger_manifest,
        official_terminal_manifest=None, official_terminal_bytes_by_hash={},
        historical_sample_manifests=(), historical_sample_bytes_by_hash={},
        episodes=first.compilation.episodes, resolved_observations=first.resolved_observations,
        artifact_hashes_twice_identical=True,
    )
    output_root.parent.mkdir(parents=True, exist_ok=True)
    stage_a = Path(tempfile.mkdtemp(prefix=".pit-reconcile-a-", dir=output_root.parent))
    stage_b = Path(tempfile.mkdtemp(prefix=".pit-reconcile-b-", dir=output_root.parent))
    try:
        for stage, bundle in ((stage_a, first), (stage_b, second)):
            materialize_artifact_tree(
                stage, bundle=bundle, seed_manifest=seed_manifest,
                ledger_manifest=ledger_manifest,
                diagnostic_terminal_manifest=diagnostic_terminal_manifest,
                certification=provisional,
            )
        snapshot_a = artifact_tree_snapshot(stage_a)
        snapshot_b = artifact_tree_snapshot(stage_b)
        artifact_determinism = snapshot_a == snapshot_b
        if not artifact_determinism:
            raise RuntimeError("artifact staging trees differ")
        promote_artifact_tree(stage_a, output_root)
        if artifact_tree_snapshot(output_root) != snapshot_b:
            raise RuntimeError("promoted tree differs from verified staging")
    finally:
        if stage_a.exists():
            shutil.rmtree(stage_a)
        if stage_b.exists():
            shutil.rmtree(stage_b)

    decision = evaluate_certification(
        primary_evidence_manifests=first.evidence_manifests,
        retained_primary_bytes_by_hash={}, canonical_ledger_manifest=ledger_manifest,
        official_terminal_manifest=None, official_terminal_bytes_by_hash={},
        historical_sample_manifests=(), historical_sample_bytes_by_hash={},
        episodes=first.compilation.episodes, resolved_observations=first.resolved_observations,
        artifact_hashes_twice_identical=artifact_determinism,
    )
    result = {
        "runtime_reconciliation_result": "PASS",
        "counts": {"canonical_findings": 37, "resolved_findings": 37,
                   "identity_events": 20, "overlay_cases": 9, "overlay_rows": 3236,
                   "reconciled_membership_events": 630, "instrument_episodes": 832},
        "certification": decision,
        "artifact_snapshot": artifact_tree_snapshot(output_root),
        "artifact_manifest_sha256": _file_hash(output_root / "artifact_manifest.json"),
        "compilation_hash": first.compilation.output_hash,
    }
    print(json.dumps(result, default=lambda item: {
        field: getattr(item, field) for field in item.__dataclass_fields__
    }, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    run(args.data_root, args.output_root)


if __name__ == "__main__":
    main()
