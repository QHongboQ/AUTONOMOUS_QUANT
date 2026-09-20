"""Validate or execute the frozen selective EdgarTools historical build.

The default command is offline validation.  Execution is explicit and uses
only the already-frozen 36,206-accession inventory; it never re-runs the
711-CIK EntityFacts census or requests a full SEC submission.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


REPO = Path(__file__).resolve().parents[3]
for dependency in (
    REPO / "20-intelligence-system/fundamental-factors/evidence-contract",
    REPO / "10-data-system/fundamentals/historical-dataset",
):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

from aq_edgartools_full_build import (  # noqa: E402
    BUILD_SPEC_VERSION,
    EDGARTOOLS_VERSION,
    ENTITYFACTS_DISCOVERY_ROLE,
    SELECTIVE_REQUIRED_ACCESSION_COUNT,
    SELECTIVE_POLICY_IDENTITY,
    bounded_batches,
    checkpoint_identity,
    checkpoint_reusable,
    failure_record,
    native_financial_object_info,
    native_xbrl_source_manifest,
    select_numeric_fact_value,
    sha256_file,
)
from aq_fundamental_evidence.materialize import materialize_edgartools_fact  # noqa: E402
from aq_hybrid_fundamentals import (  # noqa: E402
    admit_period_class,
    consolidated_projection_events,
    project_edgartools_standard_concept,
)


ROOT_DEFAULT = Path("/mnt/d/AQ_DATA/P5/edgartools-native-full-universe-historical-build-001")
IDENTITY_PATH = Path("/home/zhou/.config/autonomous-quant/p5-edgar.env")
UPSTREAM_IDENTITY = "PYPI_DISTRIBUTION:edgartools==5.58.0"
EXPECTED_ENTITYFACTS_REPORT_SHA256 = (
    "0ed3e4da1eb68bdc00a2e68a24188e0de1e4c3c40cf6e7942f6a83e330edb8fd"
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(path.suffix + ".staging")
    staging.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    staging.replace(path)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(path.suffix + ".staging")
    with staging.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            stream.write("\n")
    staging.replace(path)


def _load_identity() -> str:
    if not IDENTITY_PATH.is_file() or IDENTITY_PATH.stat().st_mode & 0o077:
        raise RuntimeError("private SEC identity is absent or insecure")
    for raw in IDENTITY_PATH.read_text(encoding="utf-8").splitlines():
        key, separator, value = raw.strip().removeprefix("export ").partition("=")
        if separator and key.strip() in {"EDGAR_IDENTITY", "SEC_IDENTITY"}:
            identity = value.strip().strip('"').strip("'")
            if re.fullmatch(
                r".+\s+[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", identity
            ):
                return identity
    raise RuntimeError("meaningful private SEC identity is not configured")


def validate_frozen_selective_inventory(root: Path) -> dict[str, object]:
    """Validate the prior successful selection without network or source reads."""

    report_path = root / "reports/entityfacts_first_realign_report.json"
    inventory_path = root / "selective/entityfacts_selective_accessions.json"
    if sha256_file(report_path) != EXPECTED_ENTITYFACTS_REPORT_SHA256:
        raise RuntimeError("frozen EntityFacts-first report hash mismatch")
    report = _read_json(report_path)
    inventory = _read_json(inventory_path)
    rows = inventory.get("rows")
    if (
        report.get("storage_preflight") != "PASS"
        or report.get("broad_accession_acquisition_started") is not False
        or report.get("full_historical_build_started") is not False
        or report.get("selective_required_accession_count")
        != SELECTIVE_REQUIRED_ACCESSION_COUNT
        or report.get("selective_policy_identity") != SELECTIVE_POLICY_IDENTITY
        or not isinstance(rows, list)
        or len(rows) != SELECTIVE_REQUIRED_ACCESSION_COUNT
        or any(row.get("source_role") != ENTITYFACTS_DISCOVERY_ROLE for row in rows)
    ):
        raise RuntimeError("frozen selective inventory contract mismatch")
    return {
        "schema": BUILD_SPEC_VERSION,
        "status": "PASS",
        "build_spec_identity": report["build_spec_identity"],
        "selective_policy_identity": report["selective_policy_identity"],
        "selected_accession_count": len(rows),
        "entityfacts_final_source_authority": False,
        "broad_accession_acquisition_started": False,
        "full_historical_build_started": False,
    }


def _clean_fact(raw: Mapping[str, object]) -> dict[str, object]:
    cleaned: dict[str, object] = {}
    for key, value in raw.items():
        if hasattr(value, "item"):
            value = value.item()
        cleaned[key] = None if isinstance(value, float) and math.isnan(value) else value
    return cleaned


def _acceptance(value: object) -> object:
    accepted = pd.Timestamp(value)
    if accepted.tzinfo is None:
        accepted = accepted.tz_localize("America/New_York")
    return accepted.tz_convert("UTC").to_pydatetime()


def _output_paths(root: Path, accession: str) -> dict[str, Path]:
    return {
        "evidence": root / "evidence" / f"{accession}.jsonl",
        "events": root / "standardized-events" / f"{accession}.jsonl",
        "source_manifest": root / "source-manifests" / f"{accession}.json",
    }


def _process_accession(
    row: Mapping[str, object],
    metadata: Mapping[str, object],
    *,
    root: Path,
    build_spec_identity: str,
) -> dict[str, object]:
    """Use native attachment/XBRL surfaces and seal one accession atomically."""

    from edgar import Filing
    from edgar.xbrl.core import classify_duration, duration_days
    from edgar.xbrl.standardization import get_default_mapper

    accession = str(row["accession"])
    admitted, object_type = native_financial_object_info(str(row["form"]))
    if not admitted:
        raise ValueError(f"EdgarTools object capability rejected {row['form']}")
    filing = Filing(
        cik=int(str(metadata["cik"])),
        company=str(metadata["issuer_name"]),
        form=str(metadata["form"]),
        filing_date=str(metadata["filing_date"]),
        accession_no=accession,
    )
    source_manifest = native_xbrl_source_manifest(filing)
    if not source_manifest["assets"]:
        raise RuntimeError("selected EntityFacts accession has no native XBRL assets")
    xbrl = filing.xbrl()
    if xbrl is None:
        raise RuntimeError("native assets exist but EdgarTools returned no XBRL object")

    mapper = get_default_mapper()
    evidence_rows: list[dict[str, object]] = []
    event_candidates: list[dict[str, object]] = []
    for raw in xbrl.facts.to_dataframe().to_dict("records"):
        fact = _clean_fact(raw)
        if fact.get("period_type") not in {"instant", "duration"}:
            continue
        selection, canonical = select_numeric_fact_value(fact)
        if canonical is None:
            continue
        standard = project_edgartools_standard_concept(
            mapper.map_concept(
                str(fact.get("concept") or ""),
                str(fact.get("label") or fact.get("concept") or ""),
                {},
            )
        )
        if standard is None:
            continue
        fact["value"] = canonical
        evidence = materialize_edgartools_fact(
            filing,
            fact,
            acceptance_datetime=_acceptance(metadata["acceptance_datetime"]),
            report_period_end=str(metadata["report_period"]),
            source_document_sha256=str(source_manifest["source_document_sha256"]),
            source_document_identity=str(source_manifest["source_document_identity"]),
            source_document_url=str(source_manifest["source_document_url"]),
            edgartools_version=EDGARTOOLS_VERSION,
            upstream_identity=UPSTREAM_IDENTITY,
        )
        evidence_rows.append(evidence.model_dump(mode="json"))
        duration_class = None
        if fact["period_type"] == "duration":
            start = pd.Timestamp(fact["period_start"]).date()
            end = pd.Timestamp(fact["period_end"]).date()
            duration_class = classify_duration(duration_days(start, end))
        period_class = admit_period_class(str(fact["period_type"]), duration_class)
        event_candidates.append(
            {
                "cik": evidence.entity.cik,
                "standard_concept": standard,
                "period_class": period_class,
                "canonical_value": evidence.fact.value,
                "unit": evidence.fact.unit,
                "evidence_id": evidence.evidence_id,
                "accession": accession,
                "first_available_at": evidence.availability.first_available_at.isoformat(),
                "report_period_start": (
                    evidence.fact.period_start.isoformat()
                    if evidence.fact.period_start
                    else None
                ),
                "report_period_end": (
                    evidence.fact.period_end or evidence.fact.instant
                ).isoformat(),
                "dimensions": evidence.fact.dimensions or {},
            }
        )

    event_frame = (
        consolidated_projection_events(pd.DataFrame(event_candidates))
        if event_candidates
        else pd.DataFrame()
    )
    event_rows = event_frame.to_dict("records") if not event_frame.empty else []
    output_paths = _output_paths(root, accession)
    evidence_path = output_paths["evidence"]
    event_path = output_paths["events"]
    manifest_path = output_paths["source_manifest"]
    _write_jsonl(evidence_path, evidence_rows)
    _write_jsonl(event_path, event_rows)
    _write_json(manifest_path, source_manifest)
    output_hashes = {name: sha256_file(path) for name, path in output_paths.items()}
    checkpoint = {
        "accession": accession,
        "cik": str(metadata["cik"]),
        "build_spec_identity": build_spec_identity,
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "source_storage_class": source_manifest["source_storage_class"],
        "terminal_state": (
            "COMPLETE_WITH_EVIDENCE"
            if evidence_rows
            else "COMPLETE_NO_AUTHORIZED_FACTS"
        ),
        "evidence_sealed": True,
        "output_hashes": output_hashes,
    }
    checkpoint["checkpoint_identity"] = checkpoint_identity(
        build_spec_identity=build_spec_identity,
        accession=accession,
        source_manifest_sha256=str(source_manifest["manifest_sha256"]),
        output_hashes=output_hashes,
    )
    _write_json(root / "checkpoints" / f"{accession}.json", checkpoint)
    return checkpoint


def execute_frozen_inventory(root: Path) -> dict[str, object]:
    """Execute only the frozen inventory in bounded, independently sealed batches."""

    if importlib.metadata.version("edgartools") != EDGARTOOLS_VERSION:
        raise RuntimeError("EdgarTools version drift")
    frozen = validate_frozen_selective_inventory(root)
    identity = _load_identity()
    os.environ["EDGAR_IDENTITY"] = identity
    os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = "2"
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(root / "staging/edgar-data")
    from edgar import set_identity

    set_identity(identity)
    selected = _read_json(root / "selective/entityfacts_selective_accessions.json")["rows"]
    metadata_rows = _read_json(root / "inventory/accession_inventory.json")["rows"]
    metadata = {str(row["accession"]): row for row in metadata_rows}
    if any(str(row["accession"]) not in metadata for row in selected):
        raise RuntimeError("selective accession lacks frozen native metadata")
    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for batch in bounded_batches(selected):
        for row in batch:
            accession = str(row["accession"])
            checkpoint_path = root / "checkpoints" / f"{accession}.json"
            if checkpoint_path.is_file():
                checkpoint = _read_json(checkpoint_path)
                if checkpoint_reusable(
                    checkpoint,
                    build_spec_identity=str(frozen["build_spec_identity"]),
                    output_paths=_output_paths(root, accession),
                ):
                    results.append(checkpoint)
                    continue
            error: BaseException | None = None
            attempts = 0
            for attempts in range(1, 4):
                try:
                    results.append(
                        _process_accession(
                            row,
                            metadata[accession],
                            root=root,
                            build_spec_identity=str(frozen["build_spec_identity"]),
                        )
                    )
                    error = None
                    break
                except (ConnectionError, TimeoutError) as transient:
                    error = transient
                    continue
                except Exception as deterministic:
                    error = deterministic
                    break
            if error is not None:
                failures.append(
                    failure_record(
                        accession=accession,
                        cik=str(row["cik"]),
                        stage="NATIVE_ASSET_XBRL_MATERIALIZATION",
                        error=error,
                        attempts=attempts,
                    )
                )
    report = {
        "schema": BUILD_SPEC_VERSION,
        "selected_accession_count": len(selected),
        "completed_count": len(results),
        "failed_count": len(failures),
        "terminal_state_counts": dict(
            sorted(Counter(str(row["terminal_state"]) for row in results + failures).items())
        ),
        "failures": failures,
    }
    _write_json(root / "reports/selective_execution_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate", "execute"), default="validate", nargs="?")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    args = parser.parse_args()
    result = (
        validate_frozen_selective_inventory(args.root)
        if args.command == "validate"
        else execute_frozen_inventory(args.root)
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
