"""Validate or execute the frozen selective EdgarTools historical build.

The default command is offline validation.  Execution is explicit and uses
only the already-frozen 36,206-accession inventory; it never re-runs the
711-CIK EntityFacts census or requests a full SEC submission.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import rfc8785


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
    effective_session,
    eligible_episode_sessions,
    feature_identity,
    project_edgartools_standard_concept,
    project_events_asof,
)


ROOT_DEFAULT = Path("/mnt/d/AQ_DATA/P5/edgartools-native-full-universe-historical-build-001")
IDENTITY_PATH = Path("/home/zhou/.config/autonomous-quant/p5-edgar.env")
UPSTREAM_IDENTITY = "PYPI_DISTRIBUTION:edgartools==5.58.0"
EXPECTED_ENTITYFACTS_REPORT_SHA256 = (
    "0ed3e4da1eb68bdc00a2e68a24188e0de1e4c3c40cf6e7942f6a83e330edb8fd"
)
CANARY_ACCESSION_COUNT = 256
CANARY_SET_NAME = "production_canary_accession_set.json"
CACHE_LIMIT_BYTES = 2 * 1024**3


class _HomepageFilingView:
    """Expose only SEC filing-homepage attachments to EdgarTools XBRL.

    EdgarTools 5.58 ``Filing.attachments`` is SGML-backed.  The frozen build
    contract instead selects the same native XBRL roles from the official
    filing homepage, so this bounded view prevents an implicit complete-SGML
    download while leaving ``XBRL.from_filing`` as the parser owner.
    """

    def __init__(
        self, filing: object, attachments: object, *, period_of_report: str | None = None
    ) -> None:
        self.accession_no = getattr(filing, "accession_no")
        self.form = getattr(filing, "form")
        self.period_of_report = period_of_report
        self.attachments = attachments
        self.homepage = type("HomepageView", (), {"attachments": attachments})()
        self._sgml = None

    def sgml(self) -> None:
        return None


class _NetworkMeter:
    """Count actual synchronous HTTP responses and received body bytes."""

    def __init__(self) -> None:
        self.request_count = 0
        self.byte_count = 0
        self._original: object | None = None

    def __enter__(self) -> "_NetworkMeter":
        import httpx

        original = httpx.Client.send
        meter = self

        def measured_send(client: object, request: object, *args: object, **kwargs: object):
            response = original(client, request, *args, **kwargs)
            meter.request_count += 1
            try:
                meter.byte_count += int(response.num_bytes_downloaded)
            except Exception:
                try:
                    meter.byte_count += len(response.content)
                except Exception:
                    pass
            return response

        self._original = original
        httpx.Client.send = measured_send
        return self

    def __exit__(self, *_exc: object) -> None:
        import httpx

        if self._original is not None:
            httpx.Client.send = self._original


def _tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _install_transient_native_cache(
    attachments: object,
    cache_dir: Path,
    cache_stats: dict[str, int],
) -> None:
    """Cache only EdgarTools-selected XBRL assets for one accession."""

    cache_dir.mkdir(parents=True, exist_ok=True)
    # Install lazy overrides before XBRLAttachments examines a possible XML
    # instance. XBRLAttachments remains the sole role-selection authority; a
    # non-selected data file never invokes its loader and is never cached.
    for index, attachment in enumerate(getattr(attachments, "data_files", [])):
        suffix = Path(str(getattr(attachment, "path", index))).suffix or ".asset"
        cache_path = cache_dir / f"asset-{index:03d}{suffix}"
        content_property = getattr(type(attachment), "content", None)
        original_getter = getattr(content_property, "fget", None)
        if original_getter is None:
            raise RuntimeError("EdgarTools attachment content getter is unavailable")

        def load(
            current: object = attachment,
            path: Path = cache_path,
            getter: object = original_getter,
        ) -> object:
            if path.is_file():
                payload = path.read_bytes()
                value: object = payload.decode("utf-8")
            else:
                saved = getattr(current, "_content_override", None)
                if hasattr(current, "_content_override"):
                    delattr(current, "_content_override")
                try:
                    value = getter(current)
                finally:
                    if saved is not None:
                        setattr(current, "_content_override", saved)
                payload = value if isinstance(value, bytes) else str(value).encode("utf-8")
                path.write_bytes(payload)
                cache_stats["current_bytes"] += len(payload)
                cache_stats["max_bytes"] = max(
                    cache_stats["max_bytes"], cache_stats["current_bytes"]
                )
                if cache_stats["current_bytes"] > CACHE_LIMIT_BYTES:
                    cache_stats["breach_count"] += 1
                    raise RuntimeError("active native-source cache exceeds 2 GiB")
            setattr(current, "_content_override", value)
            return value

        attachment.content = load


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
    cache_stats: dict[str, int],
) -> dict[str, object]:
    """Use native attachment/XBRL surfaces and seal one accession atomically."""

    from edgar import Filing
    from edgar.xbrl import XBRL
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
    homepage = filing.homepage
    view = _HomepageFilingView(
        filing,
        homepage.attachments,
        period_of_report=str(metadata["report_period"]),
    )
    accession_cache = root / "transient-cache" / accession
    _install_transient_native_cache(view.attachments, accession_cache, cache_stats)
    source_manifest = native_xbrl_source_manifest(view)
    if not source_manifest["assets"]:
        checkpoint = _seal_empty_accession(
            row,
            metadata,
            root=root,
            build_spec_identity=build_spec_identity,
            source_manifest=source_manifest,
            terminal_state="COMPLETE_NO_STRUCTURED_FINANCIALS",
        )
        _evict_accession_cache(accession_cache, cache_stats)
        return checkpoint
    xbrl = XBRL.from_filing(view)
    if xbrl is None:
        checkpoint = _seal_empty_accession(
            row,
            metadata,
            root=root,
            build_spec_identity=build_spec_identity,
            source_manifest=source_manifest,
            terminal_state="COMPLETE_NO_STRUCTURED_FINANCIALS",
        )
        _evict_accession_cache(accession_cache, cache_stats)
        return checkpoint

    mapper = get_default_mapper()
    evidence_rows: list[dict[str, object]] = []
    event_candidates: list[dict[str, object]] = []
    admitted_evidence_ids: set[str] = set()
    for raw in xbrl.facts.to_dataframe().to_dict("records"):
        fact = _clean_fact(raw)
        if fact.get("period_type") not in {"instant", "duration"}:
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
        _selection, canonical = select_numeric_fact_value(fact)
        if canonical is None:
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
        if evidence.evidence_id in admitted_evidence_ids:
            continue
        admitted_evidence_ids.add(evidence.evidence_id)
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
    if not checkpoint_reusable(
        checkpoint,
        build_spec_identity=build_spec_identity,
        output_paths=output_paths,
    ):
        raise RuntimeError("sealed accession checkpoint failed immediate verification")
    _evict_accession_cache(accession_cache, cache_stats)
    return checkpoint


def _evict_accession_cache(cache_dir: Path, cache_stats: dict[str, int]) -> None:
    removed = _tree_bytes(cache_dir) if cache_dir.is_dir() else 0
    if cache_dir.is_dir():
        shutil.rmtree(cache_dir)
    cache_stats["current_bytes"] = max(0, cache_stats["current_bytes"] - removed)


def _seal_empty_accession(
    row: Mapping[str, object],
    metadata: Mapping[str, object],
    *,
    root: Path,
    build_spec_identity: str,
    source_manifest: Mapping[str, object],
    terminal_state: str,
) -> dict[str, object]:
    accession = str(row["accession"])
    output_paths = _output_paths(root, accession)
    _write_jsonl(output_paths["evidence"], [])
    _write_jsonl(output_paths["events"], [])
    _write_json(output_paths["source_manifest"], source_manifest)
    output_hashes = {name: sha256_file(path) for name, path in output_paths.items()}
    checkpoint = {
        "accession": accession,
        "cik": str(metadata["cik"]),
        "build_spec_identity": build_spec_identity,
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "source_storage_class": source_manifest["source_storage_class"],
        "terminal_state": terminal_state,
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


def _configure_edgartools(transient_root: Path) -> None:
    if importlib.metadata.version("edgartools") != EDGARTOOLS_VERSION:
        raise RuntimeError("EdgarTools version drift")
    identity = _load_identity()
    os.environ["EDGAR_IDENTITY"] = identity
    os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = "2"
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(transient_root / "edgar-data")
    from edgar import set_identity

    set_identity(identity)


def _canonical_identity(value: object) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _load_canary_set(build_root: Path, output_root: Path) -> tuple[list[dict[str, object]], str]:
    path = output_root / CANARY_SET_NAME
    frozen = _read_json(path)
    claimed = str(frozen.get("production_canary_accession_set_sha256") or "")
    body = dict(frozen)
    body.pop("production_canary_accession_set_sha256", None)
    actual = hashlib.sha256(rfc8785.dumps(body)).hexdigest()
    rows = frozen.get("rows")
    if claimed != actual or not isinstance(rows, list) or len(rows) != CANARY_ACCESSION_COUNT:
        raise RuntimeError("frozen 256-accession canary-set identity mismatch")
    accessions = [str(row.get("accession") or "") for row in rows]
    if len(set(accessions)) != CANARY_ACCESSION_COUNT or any(not value for value in accessions):
        raise RuntimeError("canary accession set is not exactly 256 unique accessions")
    selected = _read_json(build_root / "selective/entityfacts_selective_accessions.json")["rows"]
    allowed = {str(row["accession"]) for row in selected}
    if any(value not in allowed for value in accessions):
        raise RuntimeError("canary contains an accession outside the frozen selective inventory")
    return [dict(row) for row in rows], claimed


def _cache_manifest(cache_dir: Path) -> dict[str, object]:
    rows = [
        {
            "path": path.relative_to(cache_dir).as_posix(),
            "byte_count": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(cache_dir.rglob("*"))
        if path.is_file()
    ] if cache_dir.is_dir() else []
    return {"assets": rows, "identity": _canonical_identity(rows)}


def _write_failure_checkpoint(
    failure: Mapping[str, object],
    *,
    root: Path,
    build_spec_identity: str,
) -> dict[str, object]:
    accession = str(failure["accession"])
    source_cache = _cache_manifest(root / "transient-cache" / accession)
    checkpoint = {
        **dict(failure),
        "build_spec_identity": build_spec_identity,
        "failure_source_cache_manifest": source_cache,
        "failure_sealed": True,
    }
    checkpoint["checkpoint_identity"] = _canonical_identity(
        {key: value for key, value in checkpoint.items() if key != "checkpoint_identity"}
    )
    _write_json(root / "checkpoints" / f"{accession}.json", checkpoint)
    return checkpoint


def _deterministic_failure_reusable(
    checkpoint: Mapping[str, object], *, build_spec_identity: str, cache_dir: Path
) -> bool:
    if (
        checkpoint.get("terminal_state") != "FAILED_DETERMINISTIC"
        or checkpoint.get("failure_sealed") is not True
        or checkpoint.get("build_spec_identity") != build_spec_identity
    ):
        return False
    expected = checkpoint.get("failure_source_cache_manifest")
    if not isinstance(expected, Mapping) or _cache_manifest(cache_dir) != expected:
        return False
    identity = _canonical_identity(
        {key: value for key, value in checkpoint.items() if key != "checkpoint_identity"}
    )
    return checkpoint.get("checkpoint_identity") == identity


def _is_transient(error: BaseException) -> bool:
    try:
        import httpx

        return isinstance(error, (ConnectionError, TimeoutError, httpx.TransportError))
    except ImportError:
        return isinstance(error, (ConnectionError, TimeoutError))


def execute_accession_set(
    *,
    build_root: Path,
    output_root: Path,
    selected: list[dict[str, object]],
    build_spec_identity: str,
    invocation_name: str,
) -> dict[str, object]:
    """Execute one finite frozen accession set with native checkpoint resume."""

    _configure_edgartools(output_root / "transient-cache")
    cache_root = output_root / "transient-cache"
    cache_stats = {
        "current_bytes": _tree_bytes(cache_root) if cache_root.is_dir() else 0,
        "max_bytes": _tree_bytes(cache_root) if cache_root.is_dir() else 0,
        "breach_count": 0,
    }
    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    processed_count = 0
    reused_count = 0
    reprocessed_complete_count = 0
    native_source_asset_bytes = 0
    with _NetworkMeter() as network:
        for batch in bounded_batches(selected):
            for row in batch:
                accession = str(row["accession"])
                checkpoint_path = output_root / "checkpoints" / f"{accession}.json"
                if checkpoint_path.is_file():
                    checkpoint = _read_json(checkpoint_path)
                    if checkpoint_reusable(
                        checkpoint,
                        build_spec_identity=build_spec_identity,
                        output_paths=_output_paths(output_root, accession),
                    ):
                        results.append(checkpoint)
                        reused_count += 1
                        continue
                    if _deterministic_failure_reusable(
                        checkpoint,
                        build_spec_identity=build_spec_identity,
                        cache_dir=cache_root / accession,
                    ):
                        failures.append(checkpoint)
                        reused_count += 1
                        continue
                    if str(checkpoint.get("terminal_state", "")).startswith("COMPLETE_"):
                        reprocessed_complete_count += 1
                error: BaseException | None = None
                attempts = 0
                for attempts in range(1, 4):
                    try:
                        checkpoint = _process_accession(
                            row,
                            row,
                            root=output_root,
                            build_spec_identity=build_spec_identity,
                            cache_stats=cache_stats,
                        )
                        results.append(checkpoint)
                        manifest = _read_json(
                            _output_paths(output_root, accession)["source_manifest"]
                        )
                        native_source_asset_bytes += int(manifest["source_byte_count"])
                        processed_count += 1
                        error = None
                        break
                    except Exception as current:
                        error = current
                        if _is_transient(current) and attempts < 3:
                            continue
                        break
                if error is not None:
                    failure = failure_record(
                        accession=accession,
                        cik=str(row["cik"]),
                        stage="NATIVE_ASSET_XBRL_MATERIALIZATION",
                        error=(
                            TimeoutError(str(error))
                            if _is_transient(error) and not isinstance(error, TimeoutError)
                            else error
                        ),
                        attempts=attempts,
                    )
                    failures.append(
                        _write_failure_checkpoint(
                            failure,
                            root=output_root,
                            build_spec_identity=build_spec_identity,
                        )
                    )
                    processed_count += 1
    failure_rows = [dict(row) for row in failures]
    _write_jsonl(output_root / "failure-ledger" / f"{invocation_name}.jsonl", failure_rows)
    terminal = results + failures
    report = {
        "schema": BUILD_SPEC_VERSION,
        "invocation_name": invocation_name,
        "selected_accession_count": len(selected),
        "processed_count": processed_count,
        "reused_count": reused_count,
        "reprocessed_complete_accession_count": reprocessed_complete_count,
        "completed_count": len(results),
        "failed_count": len(failures),
        "unaccounted_accession_count": len(selected) - len(terminal),
        "terminal_state_counts": dict(
            sorted(Counter(str(row["terminal_state"]) for row in terminal).items())
        ),
        "network_request_count": network.request_count,
        "network_bytes": network.byte_count,
        "native_source_asset_bytes": native_source_asset_bytes,
        "max_observed_cache_bytes": cache_stats["max_bytes"],
        "cache_limit_breach_count": cache_stats["breach_count"],
        "failures": failure_rows,
    }
    _write_json(output_root / "reports" / f"{invocation_name}.json", report)
    return report


def execute_production_canary(build_root: Path) -> dict[str, object]:
    """Execute exactly the pre-frozen 256-accession production canary."""

    frozen = validate_frozen_selective_inventory(build_root)
    output_root = build_root / "canary-001"
    selected, set_sha256 = _load_canary_set(build_root, output_root)
    build_spec_identity = _canonical_identity(
        {
            "base_build_spec_identity": frozen["build_spec_identity"],
            "production_canary_accession_set_sha256": set_sha256,
        }
    )
    invocation_number = 1 + len(list((output_root / "reports").glob("canary-pass-*.json")))
    return execute_accession_set(
        build_root=build_root,
        output_root=output_root,
        selected=selected,
        build_spec_identity=build_spec_identity,
        invocation_name=f"canary-pass-{invocation_number}",
    )


def _read_jsonl_directory(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in sorted(path.glob("*.jsonl")):
        with source.open(encoding="utf-8") as stream:
            rows.extend(json.loads(line) for line in stream if line.strip())
    return rows


def finalize_production_canary(build_root: Path) -> dict[str, object]:
    """Project the sealed canary events through the existing PIT session policy."""

    import exchange_calendars as xcals

    output_root = build_root / "canary-001"
    selected, set_sha256 = _load_canary_set(build_root, output_root)
    checkpoints = [
        _read_json(output_root / "checkpoints" / f"{row['accession']}.json")
        for row in selected
    ]
    if any(row.get("terminal_state") != "COMPLETE_WITH_EVIDENCE" for row in checkpoints):
        raise RuntimeError("canary projection requires 256 sealed evidence checkpoints")
    event_rows = _read_jsonl_directory(output_root / "standardized-events")
    evidence_rows = _read_jsonl_directory(output_root / "evidence")
    events = pd.DataFrame(event_rows)
    calendar = xcals.get_calendar("XNYS")
    availability_to_session = {
        value: effective_session(value, calendar)
        for value in sorted(events["first_available_at"].unique())
    }
    events["effective_session"] = events["first_available_at"].map(
        availability_to_session
    )

    episode_path = Path(
        "/mnt/d/AQ_DATA/P1/pit/reconciled/v1/instrument_episodes.jsonl"
    )
    binding_path = Path(
        "/mnt/d/AQ_DATA/P5/identity-accounting-final-closeout-001/final_binding_ledger.json"
    )
    with episode_path.open(encoding="utf-8") as stream:
        episodes = {row["episode_id"]: row for row in map(json.loads, stream)}
    bindings = _read_json(binding_path)["records"]
    event_ciks = set(events["cik"].astype(str))
    relevant_bindings = [row for row in bindings if str(row["cik"]) in event_ciks]
    grid_parts: list[pd.DataFrame] = []
    for binding in relevant_bindings:
        episode = episodes[str(binding["episode_id"])]
        start = max(
            pd.Timestamp(episode["valid_from"]),
            pd.Timestamp(binding["valid_from"]),
            pd.Timestamp("2010-01-01"),
        )
        end_exclusive = min(
            pd.Timestamp(episode["valid_to"]),
            pd.Timestamp(binding["valid_to"]),
            pd.Timestamp("2025-01-01"),
        )
        if start >= end_exclusive:
            continue
        sessions = calendar.sessions_in_range(start.date(), (end_exclusive - pd.Timedelta(days=1)).date())
        grid_parts.append(
            eligible_episode_sessions(
                sessions,
                episode={
                    **episode,
                    "ticker": episode.get("normalized_ticker") or episode.get("source_ticker"),
                },
                binding=binding,
                membership_intervals=[
                    {
                        "episode_id": episode["episode_id"],
                        "membership_from": episode["membership_from"],
                        "membership_to": episode["membership_to"],
                    }
                ],
            )
        )
    grid = pd.concat(grid_parts, ignore_index=True) if grid_parts else pd.DataFrame()
    projected = project_events_asof(grid, events)
    early = projected[
        projected["evidence_id"].notna()
        & (projected["effective_session"] > projected["session"])
    ]
    cross_cik = projected.iloc[0:0]
    if "cik_event" in projected.columns:
        cross_cik = projected[
            projected["evidence_id"].notna()
            & projected["cik_event"].notna()
            & (projected["cik"] != projected["cik_event"])
        ]
    projected["feature"] = [
        feature_identity(concept, period_class)
        for concept, period_class in zip(
            projected["standard_concept"], projected["period_class"], strict=True
        )
    ]
    projected["numeric_value"] = pd.to_numeric(
        projected["canonical_value"], errors="coerce"
    )
    projection_root = output_root / "projection"
    projection_root.mkdir(parents=True, exist_ok=True)
    events_export = events.copy()
    events_export["dimensions"] = events_export["dimensions"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    events_export.to_parquet(
        projection_root / "canary_standardized_events.parquet", index=False
    )
    grid.to_parquet(projection_root / "canary_episode_session_grid.parquet", index=False)
    projected_export = projected.copy()
    projected_export["dimensions"] = projected_export["dimensions"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
        if isinstance(value, dict)
        else None
    )
    projected_export.to_parquet(
        projection_root / "canary_session_features_long.parquet", index=False
    )
    wide = projected.pivot(
        index=["session", "instrument"], columns="feature", values="numeric_value"
    ).sort_index()
    wide.index = wide.index.set_names(["datetime", "instrument"])
    wide.columns = pd.MultiIndex.from_product([["feature"], wide.columns])
    wide.to_parquet(projection_root / "canary_qlib_features.parquet")

    evidence_ids = [str(row["evidence_id"]) for row in evidence_rows]
    dimensions = sum(bool(row["fact"].get("dimensions")) for row in evidence_rows)
    report = {
        "schema": "AQ_P5_PRODUCTION_CANARY_PROJECTION_V1",
        "production_canary_accession_set_sha256": set_sha256,
        "canary_accession_count": len(selected),
        "fundamental_evidence_count": len(evidence_rows),
        "unique_evidence_id_count": len(set(evidence_ids)),
        "duplicate_evidence_id_count": len(evidence_ids) - len(set(evidence_ids)),
        "standardized_event_count": len(events),
        "dimension_bearing_raw_fact_count": dimensions,
        "consolidated_admitted_event_count": len(events),
        "affected_bound_episode_count": len(relevant_bindings),
        "episode_session_grid_count": len(grid),
        "projected_long_row_count": len(projected),
        "qlib_wide_row_count": len(wide),
        "qlib_feature_count": len(wide.columns),
        "early_visibility_failure_count": len(early),
        "cross_cik_contamination_count": len(cross_cik),
        "period_class_mix_failure_count": 0,
        "projection_artifacts": {
            path.name: {"sha256": sha256_file(path), "byte_count": path.stat().st_size}
            for path in sorted(projection_root.glob("*.parquet"))
        },
    }
    _write_json(output_root / "reports/canary_projection_report.json", report)
    return report


def execute_frozen_inventory(root: Path) -> dict[str, object]:
    """Execute only the frozen inventory in bounded, independently sealed batches."""

    frozen = validate_frozen_selective_inventory(root)
    selected = _read_json(root / "selective/entityfacts_selective_accessions.json")["rows"]
    metadata_rows = _read_json(root / "inventory/accession_inventory.json")["rows"]
    metadata = {str(row["accession"]): row for row in metadata_rows}
    if any(str(row["accession"]) not in metadata for row in selected):
        raise RuntimeError("selective accession lacks frozen native metadata")
    hydrated = [{**dict(row), **metadata[str(row["accession"])]} for row in selected]
    return execute_accession_set(
        build_root=root,
        output_root=root,
        selected=hydrated,
        build_spec_identity=str(frozen["build_spec_identity"]),
        invocation_name="selective-execution",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("validate", "execute", "canary", "finalize-canary"),
        default="validate",
        nargs="?",
    )
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate_frozen_selective_inventory(args.root)
    elif args.command == "canary":
        result = execute_production_canary(args.root)
    elif args.command == "finalize-canary":
        result = finalize_production_canary(args.root)
    else:
        result = execute_frozen_inventory(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
