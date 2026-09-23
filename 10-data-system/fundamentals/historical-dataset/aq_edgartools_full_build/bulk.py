"""P5 V1 frozen SEC bulk facts: exact admission and native EdgarTools projection.

This module reads caller-supplied ZIPs only. It owns neither SEC acquisition nor
workflow scheduling; DVC invokes it as one bounded transformation stage.
"""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pandera as pa
from edgar.entity.parser import EntityFactsParser
from edgar.standardization import get_synonym_groups
from edgar.xbrl.core import classify_duration

from aq_fundamental_evidence.materialize import materialize_bulk_entityfact
from aq_hybrid_fundamentals import FROZEN_STANDARD_CONCEPTS, admit_period_class, effective_session


SPEC_PATH = Path(__file__).resolve().parents[1] / "p5-minimal-upstream-v1.json"
GROUP_NAMES = {
    "Revenue": "revenue",
    "NetIncome": "net_income",
    "Assets": "total_assets",
    "Liabilities": "total_liabilities",
    "CommonEquity": "stockholders_equity",
    "NetCashFromOperatingActivities": "operating_cash_flow",
    "CashAndCashEquivalents": "cash_and_equivalents",
    "CurrentAssetsTotal": "total_current_assets",
    "CurrentLiabilitiesTotal": "total_current_liabilities",
    "LongTermDebt": "long_term_debt",
}
FINANCIAL_FORMS = frozenset({
    "10-K", "10-K/A", "10-Q", "10-Q/A", "10-KT", "10-KT/A", "10-QT", "10-QT/A",
    "20-F", "20-F/A", "40-F", "40-F/A", "6-K", "6-K/A",
})
SCHEMA = pa.DataFrameSchema({
    "cik": pa.Column(str, nullable=False),
    "accession": pa.Column(str, nullable=False),
    "standard_concept": pa.Column(str, nullable=False),
    "period_class": pa.Column(str, nullable=False),
    "evidence_id": pa.Column(str, nullable=False),
    "canonical_value": pa.Column(str, nullable=False),
}, strict=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def declared_path(value: str) -> Path:
    """Resolve the one frozen Windows data volume in Windows or its WSL mount."""

    if os.name != "nt" and value.startswith("D:/"):
        return Path("/mnt/d") / value[3:]
    return Path(value)


def _frozen_inputs(spec: dict[str, object], binding_path: Path, exclusion_path: Path) -> tuple[Path, Path]:
    if tuple(spec["structured_fundamentals"]) != FROZEN_STANDARD_CONCEPTS:
        raise ValueError("tracked ten-feature authority differs from runtime")
    if len(spec["structured_fundamentals"]) != 10 or "ShortTermDebt" in spec["structured_fundamentals"]:
        raise ValueError("P5 V1 feature scope changed")
    if sha256_file(binding_path) != spec["bound_episode_ledger_sha256"]:
        raise ValueError("bound episode ledger hash mismatch")
    if sha256_file(exclusion_path) != spec["exclusion_evidence_sha256"]:
        raise ValueError("PR78 exclusion evidence hash mismatch")
    source_paths = []
    for name in ("companyfacts", "submissions"):
        source = spec[name]
        path = declared_path(source["path"])
        if path.stat().st_size != source["bytes"] or sha256_file(path) != source["sha256"]:
            raise ValueError(f"frozen SEC bulk source identity mismatch: {name}")
        source_paths.append(path)
    return tuple(source_paths)


def _native_tags() -> dict[str, tuple[str, int]]:
    groups = get_synonym_groups()
    tags: dict[str, tuple[str, int]] = {}
    for concept, group_name in GROUP_NAMES.items():
        group = groups.get_group(group_name)
        if group is None:
            raise ValueError(f"EdgarTools native group unavailable: {group_name}")
        for priority, tag in enumerate(group.synonyms):
            if tag in tags and tags[tag][0] != concept:
                raise ValueError(f"overlapping native concept groups: {tag}")
            tags[tag] = (concept, priority)
    return tags


def _submission_index(archive: zipfile.ZipFile, members: set[str], cik: str) -> dict[str, dict[str, object] | None]:
    primary = f"CIK{cik}.json"
    if primary not in members:
        return {}
    source = archive.read(primary)
    body = json.loads(source)
    selected: dict[str, dict[str, object] | None] = {}
    sources = [(primary, body["filings"]["recent"], hashlib.sha256(source).hexdigest())]
    for older in body["filings"].get("files", []):
        member = str(older["name"])
        if member not in members:
            raise ValueError(f"SEC Submissions older-history member absent: {member}")
        payload = archive.read(member)
        sources.append((member, json.loads(payload), hashlib.sha256(payload).hexdigest()))
    for member, columns, source_hash in sources:
        accessions = columns.get("accessionNumber", [])
        for i, accession in enumerate(accessions):
            metadata = {
                "form": columns["form"][i],
                "acceptance_datetime": columns["acceptanceDateTime"][i],
                "filing_date": columns["filingDate"][i],
                "report_date": columns["reportDate"][i],
                "submissions_member": member,
                "submissions_member_sha256": source_hash,
            }
            previous = selected.get(accession)
            if previous is None and accession in selected:
                continue
            if previous is not None and any(previous[k] != metadata[k] for k in
                                            ("form", "acceptance_datetime", "filing_date", "report_date")):
                selected[accession] = None
            else:
                selected[accession] = metadata
    return selected


def _acceptance(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _period(fact: object) -> str:
    if fact.period_type == "instant":
        return admit_period_class("instant")
    if fact.period_type != "duration" or not fact.period_start or not fact.period_end:
        raise ValueError("native EntityFacts period is incomplete")
    days = (fact.period_end - fact.period_start).days + 1
    return admit_period_class("duration", classify_duration(days))


def build_bulk(
    output: Path,
    *,
    binding_path: Path,
    exclusion_path: Path,
    cik_limit: int | None = None,
) -> dict[str, object]:
    """Build issuer partitions from frozen bulk sources; no SEC request path."""

    import exchange_calendars as xcals

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    facts_path, filings_path = _frozen_inputs(spec, binding_path, exclusion_path)
    bindings = json.loads(binding_path.read_text(encoding="utf-8"))
    ciks = sorted({str(row["cik"]).zfill(10) for row in bindings["records"]})
    if len(ciks) != spec["bound_cik_count"] or bindings["bound_episode_count"] != 721:
        raise ValueError("bound episode/CIK population changed")
    closeout = json.loads(exclusion_path.read_text(encoding="utf-8"))
    exclusions = {(row["cik"], row["accession"]) for row in closeout["unresolved_relevant_accessions"]}
    if exclusions != {tuple(row) for row in spec["known_exact_authority_exclusions"]}:
        raise ValueError("the five frozen accession exclusions changed")
    if cik_limit is not None:
        if cik_limit <= 0:
            raise ValueError("cik_limit must be positive")
        ciks = ciks[:cik_limit]
    tags = _native_tags()
    calendar = xcals.get_calendar("XNYS")
    output.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    seen_exclusions: set[tuple[str, str]] = set()
    observed_concepts: set[str] = set()
    with zipfile.ZipFile(facts_path) as facts_zip, zipfile.ZipFile(filings_path) as filings_zip:
        fact_members = set(facts_zip.namelist())
        filing_members = set(filings_zip.namelist())
        for cik in ciks:
            member = f"CIK{cik}.json"
            if member not in fact_members:
                counts["companyfacts_cik_absent"] += 1
                continue
            metadata = _submission_index(filings_zip, filing_members, cik)
            payload = facts_zip.read(member)
            member_hash = hashlib.sha256(payload).hexdigest()
            native = EntityFactsParser.parse_company_facts(json.loads(payload, parse_float=Decimal))
            if native is None:
                raise ValueError(f"EdgarTools cannot parse frozen CompanyFacts member {member}")
            rows: list[dict[str, object]] = []
            duplicate_ids: set[str] = set()
            availability_cache: dict[str, str] = {}
            for fact in native.query().execute():
                pair = (cik, str(fact.accession))
                if pair in exclusions:
                    seen_exclusions.add(pair)
                    continue
                tag = str(fact.concept).rsplit(":", 1)[-1]
                concept_priority = tags.get(tag)
                if concept_priority is None or fact.value is None:
                    continue
                filing = metadata.get(fact.accession)
                if filing is None:
                    counts["missing_or_conflicting_exact_accession"] += 1
                    continue
                if filing["form"] not in FINANCIAL_FORMS or filing["filing_date"] > spec["historical_end"]:
                    continue
                accepted = _acceptance(filing["acceptance_datetime"])
                if accepted is None:
                    counts["missing_exact_acceptance"] += 1
                    continue
                if fact.accession not in availability_cache:
                    availability_cache[fact.accession] = effective_session(accepted, calendar).date().isoformat()
                evidence = materialize_bulk_entityfact(
                    fact,
                    cik=cik,
                    issuer_name=native.name,
                    canonical_form=str(filing["form"]),
                    canonical_filing_date=str(filing["filing_date"]),
                    canonical_report_date=str(filing["report_date"] or "") or None,
                    acceptance_datetime=accepted,
                    source_member=member,
                    source_member_sha256=member_hash,
                    source_zip_sha256=spec["companyfacts"]["sha256"],
                )
                if evidence.evidence_id in duplicate_ids:
                    counts["identical_evidence_repeated"] += 1
                    continue
                duplicate_ids.add(evidence.evidence_id)
                concept, priority = concept_priority
                observed_concepts.add(concept)
                period_class = _period(fact)
                rows.append({
                    "cik": cik, "accession": str(fact.accession),
                    "canonical_form": str(filing["form"]), "raw_fact_form": str(fact.form_type),
                    "acceptance_datetime": accepted.isoformat(),
                    "effective_session": availability_cache[fact.accession],
                    "standard_concept": concept, "native_group_priority": priority,
                    "raw_taxonomy_tag": str(fact.concept), "period_class": period_class,
                    "period_start": str(fact.period_start) if fact.period_start else None,
                    "period_end": str(fact.period_end), "unit": str(fact.unit),
                    "dimensions": json.dumps(fact.dimensions or {}, sort_keys=True),
                    "canonical_value": evidence.fact.value, "evidence_id": evidence.evidence_id,
                    "companyfacts_member_sha256": member_hash,
                    "submissions_member_sha256": filing["submissions_member_sha256"],
                    "evidence_json": evidence.model_dump_json(),
                })
            if rows:
                frame = SCHEMA.validate(pd.DataFrame.from_records(rows), lazy=True)
                frame = frame.sort_values(["accession", "standard_concept", "period_end",
                                           "native_group_priority", "evidence_id"], kind="mergesort")
                frame.to_parquet(output / f"CIK{cik}.parquet", index=False, compression="zstd")
                counts["evidence_rows"] += len(frame)
            counts["ciks_processed"] += 1
    if cik_limit is None and seen_exclusions != exclusions:
        raise ValueError("not all five frozen excluded accessions were observed")
    result = {
        "schema": "AQ_P5_MINIMAL_BULK_BUILD_V1",
        "scope_spec_sha256": sha256_file(SPEC_PATH),
        "companyfacts_sha256": spec["companyfacts"]["sha256"],
        "submissions_sha256": spec["submissions"]["sha256"],
        "bound_cik_count": len(ciks),
        "selected_fundamental_feature_count": len(spec["structured_fundamentals"]),
        "observed_selected_concepts": sorted(observed_concepts),
        "short_term_debt_output_column_present": False,
        "long_term_debt_output_column_present": "LongTermDebt" in observed_concepts,
        "unresolved_exact_acceptance_exclusion_count": len(seen_exclusions),
        "unresolved_exact_acceptance_admitted_count": 0,
        "historical_build_sec_network_request_count": 0,
        "counts": dict(counts),
    }
    (output / "manifest.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result
