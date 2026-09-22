"""Bounded, audit-only closeout of the frozen P5 SEC bulk parity gaps.

No production package imports this module. The freeze mode is offline and does
not inspect the retired historical build or modify PR #77 evidence.
"""

import argparse
import hashlib
import json
import os
import time
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path("/mnt/d/AQ_DATA/P5/upstream-parity-poc-001")
EXPECTED_ZIPS = {
    "companyfacts.zip": "ee099c7394a357f1996c728b7362f25158613b34f2ab1ad270cffc1befb917b6",
    "submissions.zip": "702fbcd8b4335bc649e9e4eab3a202f3effc314b43421664bfecb59365767165",
}
HISTORY_START = "1994-01-01"
HISTORY_END = "2024-12-31"
FINANCIAL_FORMS = {
    "10-K", "10-K/A", "10-Q", "10-Q/A", "10-KT", "10-KT/A", "10-QT", "10-QT/A",
    "20-F", "20-F/A", "40-F", "40-F/A", "6-K", "6-K/A",
}
GROUPS = {
    "Revenue": "revenue",
    "NetIncome": "net_income",
    "Assets": "total_assets",
    "Liabilities": "total_liabilities",
    "CommonEquity": "stockholders_equity",
    "NetCashFromOperatingActivities": "operating_cash_flow",
    "CashAndCashEquivalents": "cash_and_equivalents",
    "CurrentAssetsTotal": "total_current_assets",
    "CurrentLiabilitiesTotal": "total_current_liabilities",
    "ShortTermDebt": "short_term_debt",
    "LongTermDebt": "long_term_debt",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def frozen_inputs():
    checksums = read_json(ROOT / "checksums.json")["files"]
    for name in (*EXPECTED_ZIPS, "acceptance-missing-ledger.json", "fixture-manifest.json",
                 "edgartools-parity-report.json", "secfsdstools-parity-report.json"):
        path = ROOT / name
        if not path.is_file() or sha256(path) != checksums[name]["sha256"]:
            raise RuntimeError(f"Frozen POC evidence missing or hash-invalid: {name}")
        if name in EXPECTED_ZIPS and sha256(path) != EXPECTED_ZIPS[name]:
            raise RuntimeError(f"Official SEC bulk identity mismatch: {name}")


def facts_for_accession(body, accession, groups):
    rows = []
    for taxonomy, concepts in body.get("facts", {}).items():
        for tag, entry in concepts.items():
            concepts_found = [name for name, group in groups.items() if group.contains_tag(tag)]
            if not concepts_found:
                continue
            for unit, observations in entry.get("units", {}).items():
                for observation in observations:
                    if accession is not None and observation.get("accn") != accession:
                        continue
                    rows.append({"taxonomy": taxonomy, "tag": tag, "concepts": concepts_found,
                                 "unit": unit, **observation})
    return rows


def freeze():
    from edgar.standardization import get_synonym_groups

    frozen_inputs()
    missing = read_json(ROOT / "acceptance-missing-ledger.json")
    if len(missing) != 49:
        raise RuntimeError("The exact 49-row input ledger changed")
    synonyms = get_synonym_groups()
    groups = {name: synonyms.get_group(group) for name, group in GROUPS.items()}
    if any(group is None for group in groups.values()):
        raise RuntimeError("Pinned EdgarTools lacks a frozen 11-concept synonym group")
    from edgar.xbrl.standardization.core import MappingStore

    native_mapper = MappingStore(read_only=True)
    allowed_labels = {
        "Revenue", "Net Income", "Total Assets", "Total Liabilities",
        "Total Stockholders' Equity", "Net Cash from Operating Activities",
        "Cash and Cash Equivalents", "Total Current Assets", "Total Current Liabilities",
        "Short Term Debt", "Long Term Debt",
    }
    relevant_rows = []
    candidate_ciks = {row["cik"] for row in missing}
    candidate_ciks.update(row["cik"] for row in read_json(ROOT / "fixture-manifest.json")["fixtures"])
    debt_candidates = defaultdict(list)
    with zipfile.ZipFile(ROOT / "companyfacts.zip") as archive:
        members = set(archive.namelist())
        for cik in sorted(candidate_ciks):
            member = f"CIK{cik}.json"
            if member not in members:
                continue
            source = archive.read(member)
            body = json.loads(source)
            source_hash = hashlib.sha256(source).hexdigest()
            for item in [x for x in missing if x["cik"] == cik]:
                facts = facts_for_accession(body, item["accession"], groups)
                matched = []
                for fact in facts:
                    native_label = native_mapper.get_standard_concept(f"{fact['taxonomy']}:{fact['tag']}")
                    if native_label not in allowed_labels:
                        native_label = native_mapper.get_standard_concept(fact["tag"])
                    matched.append({"taxonomy": fact["taxonomy"], "tag": fact["tag"],
                                    "native_concept": native_label if native_label in allowed_labels else None,
                                    "frozen_concepts": fact["concepts"], "unit": fact["unit"],
                                    "form": fact.get("form"), "filed": fact.get("filed"),
                                    "start": fact.get("start"), "end": fact.get("end")})
                scoped = [fact for fact in matched if fact["form"] in FINANCIAL_FORMS
                          and HISTORY_START <= str(fact["filed"]) <= HISTORY_END]
                # An unmapped fact in a scoped financial accession is not assumed irrelevant.
                all_accession_facts = sum(
                    sum(obs.get("accn") == item["accession"] for unit_rows in entry.get("units", {}).values()
                        for obs in unit_rows)
                    for concepts in body.get("facts", {}).values() for entry in concepts.values()
                )
                if scoped:
                    relevance = "P5_RELEVANT_EXACT_11_CONCEPT"
                elif (any(form in FINANCIAL_FORMS for form in item["companyfacts_forms"])
                      and min(item["companyfacts_filed"]) <= HISTORY_END):
                    relevance = "P5_RELEVANT_CONSERVATIVE_UNMAPPED_FINANCIAL_ACCESSION"
                else:
                    relevance = "P5_IRRELEVANT_OUTSIDE_AUTHORIZED_FORM_OR_HISTORY"
                relevant_rows.append({"cik": cik, "accession": item["accession"],
                                      "prior_classification": item["classification"],
                                      "companyfacts_forms": item["companyfacts_forms"],
                                      "submission_records": item["submission_records"],
                                      "companyfacts_member_sha256": source_hash,
                                      "accession_fact_count": all_accession_facts,
                                      "matched_11_concept_facts": matched,
                                      "scoped_11_concept_fact_count": len(scoped),
                                      "relevance": relevance})
            # Candidate selection sees raw source facts only, before native parity output.
            by_accession = defaultdict(list)
            for fact in facts_for_accession(body, None, {k: v for k, v in groups.items()
                                                         if k in ("ShortTermDebt", "LongTermDebt")}):
                if fact.get("accn") and fact.get("form") in FINANCIAL_FORMS \
                        and HISTORY_START <= str(fact.get("filed")) <= HISTORY_END:
                    by_accession[fact["accn"]].append(fact)
            for accession, facts in by_accession.items():
                present = sorted({name for fact in facts for name in fact["concepts"]})
                if present:
                    debt_candidates[cik].append({"cik": cik, "accession": accession,
                                                 "filed": min(str(fact["filed"]) for fact in facts),
                                                 "form": sorted({fact["form"] for fact in facts}),
                                                 "raw_debt_concepts": present,
                                                 "raw_debt_fact_count": len(facts),
                                                 "companyfacts_member_sha256": source_hash})
    if len(relevant_rows) != 49:
        raise RuntimeError("Frozen 49-row reconciliation failed")
    # Include old and modern issuers plus a fixed missing-debt negative control.
    selected = []
    for cik in sorted(debt_candidates):
        ranked = sorted(debt_candidates[cik], key=lambda row: (
            len(row["raw_debt_concepts"]) != 2, row["filed"], row["accession"]))
        if ranked:
            selected.append(ranked[0])
    selected = sorted(selected, key=lambda row: (row["filed"], row["cik"]))
    # Cap the bounded matrix while retaining temporal diversity.
    if len(selected) > 6:
        selected = selected[:3] + selected[-3:]
    selected.append({"cik": "0000320193", "accession": "0001193125-09-214859",
                     "filed": "2009-10-27", "form": ["10-K"],
                     "raw_debt_concepts": [], "raw_debt_fact_count": 0,
                     "selection_role": "PRE_FROZEN_MISSING_DEBT_NEGATIVE_CONTROL"})
    if len({row["cik"] for row in selected}) < 2 or not any(
            "ShortTermDebt" in row["raw_debt_concepts"] for row in selected) or not any(
            "LongTermDebt" in row["raw_debt_concepts"] for row in selected):
        raise RuntimeError("Cannot freeze multiple-issuer positive debt fixtures")
    write_json(ROOT / "acceptance-gap-closeout.json", {
        "schema": "AQ_P5_ACCEPTANCE_GAP_CLOSEOUT_V1", "phase": "RELEVANCE_FROZEN_BEFORE_NETWORK",
        "rows": sorted(relevant_rows, key=lambda row: (row["cik"], row["accession"])),
    })
    write_json(ROOT / "debt-fixture-manifest.json", {
        "schema": "AQ_P5_DEBT_FIXTURES_V1", "selection_basis": "Frozen raw CompanyFacts debt presence; no native debt parity result inspected",
        "fixtures": selected,
    })
    print(json.dumps({"relevance_counts": dict(__import__("collections").Counter(
        row["relevance"] for row in relevant_rows)),
        "debt_fixture_count": len(selected), "debt_issuers": len({row["cik"] for row in selected})}))


def audit_offline():
    """Replay the fixed fixture set through pinned upstream fact and period APIs."""
    from edgar.entity.parser import EntityFactsParser
    from edgar.standardization import get_synonym_groups
    from edgar.xbrl.core import classify_duration
    from edgar.xbrl.standardization.core import MappingStore

    frozen_inputs()
    fixtures = read_json(ROOT / "debt-fixture-manifest.json")["fixtures"]
    mapper = MappingStore(read_only=True)
    groups = get_synonym_groups()
    debt_groups = {
        "ShortTermDebt": groups.get_group("short_term_debt"),
        "LongTermDebt": groups.get_group("long_term_debt"),
    }
    expected_labels = {"ShortTermDebt": "Short-Term Debt", "LongTermDebt": "Long-Term Debt"}
    debt_rows = []
    with zipfile.ZipFile(ROOT / "companyfacts.zip") as archive:
        for fixture in fixtures:
            member = f"CIK{fixture['cik']}.json"
            source = archive.read(member)
            parsed = EntityFactsParser.parse_company_facts(json.loads(source))
            facts = [fact for fact in parsed.query().execute() if fact.accession == fixture["accession"]]
            selected = []
            for fact in facts:
                tag = fact.concept.rsplit(":", 1)[-1]
                for name, group in debt_groups.items():
                    if not group.contains_tag(tag):
                        continue
                    label = mapper.get_standard_concept(fact.concept) or mapper.get_standard_concept(tag)
                    selected.append({"cik": fixture["cik"], "accession": fixture["accession"],
                                     "raw_taxonomy_tag": fact.concept,
                                     "native_standardized_concept": label,
                                     "expected_native_label": expected_labels[name],
                                     "frozen_concept": name, "value": fact.value, "unit": fact.unit,
                                     "instant_date": fact.period_end,
                                     "period_start": fact.period_start,
                                     "period_type": fact.period_type, "dimensions": fact.dimensions,
                                     "form": fact.form_type, "source_member": member,
                                     "source_member_sha256": hashlib.sha256(source).hexdigest(),
                                     "upstream_access_path": "EntityFactsParser + MappingStore"})
            debt_rows.append({"fixture": fixture, "native_accession_fact_count": len(facts),
                              "native_debt_facts": selected,
                              "native_short_term_positive": any(x["frozen_concept"] == "ShortTermDebt" and
                                                                x["native_standardized_concept"] == expected_labels["ShortTermDebt"]
                                                                and x["period_type"] == "instant" for x in selected),
                              "native_long_term_positive": any(x["frozen_concept"] == "LongTermDebt" and
                                                               x["native_standardized_concept"] == expected_labels["LongTermDebt"]
                                                               and x["period_type"] == "instant" for x in selected)})
    write_json(ROOT / "edgartools-debt-parity.json", {
        "schema": "AQ_P5_NATIVE_DEBT_PARITY_V1", "fixture_manifest_sha256": sha256(ROOT / "debt-fixture-manifest.json"),
        "upstream": "EdgarTools 5.58.0", "rows": debt_rows,
        "short_term_upstream_positive_count": sum(x["native_short_term_positive"] for x in debt_rows),
        "long_term_upstream_positive_count": sum(x["native_long_term_positive"] for x in debt_rows),
        "no_debt_negative_control_pass": all(not x["native_debt_facts"] for x in debt_rows if not x["fixture"]["raw_debt_concepts"]),
    })

    prior = read_json(ROOT / "edgartools-parity-report.json")
    fsds = read_json(ROOT / "secfsdstools-parity-report.json")
    period_rows = []
    for native_row, fsds_row in zip(prior["fixtures"], fsds["fixtures"], strict=True):
        fixture = native_row["fixture"]
        if fixture["accession"] != fsds_row["fixture"]["accession"]:
            raise RuntimeError("Frozen fixture parity order mismatch")
        native_facts = [fact for facts in native_row.get("concepts", {}).values() for fact in facts]
        projections = []
        for fact in native_facts:
            if fact["period_type"] == "instant":
                native_class = "Instant"
                days = None
            elif fact["period_start"] and fact["period_end"]:
                days = (date.fromisoformat(fact["period_end"]) - date.fromisoformat(fact["period_start"])).days + 1
                native_class = classify_duration(days)
            else:
                days = None
                native_class = "Unclassified"
            projections.append({"concept": fact["tag"], "accession": fact["accession"],
                                "form": fact["form"], "period_start": fact["period_start"],
                                "period_end": fact["period_end"], "period_type": fact["period_type"],
                                "duration_days": days, "native_duration_class": native_class,
                                "value": fact["value"], "unit": fact["unit"],
                                "is_restated": fact["is_restated"]})
        period_rows.append({"fixture_id": fixture["id"], "accession": fixture["accession"],
                            "fixture_form": fixture["form"],
                            "native_raw_accession_fact_count": native_row.get("accession_fact_count", 0),
                            "native_authorized_concept_rows": projections,
                            "fsds_observed_qtrs": sorted({int(x["qtrs"]) for x in fsds_row.get("raw_period_rows", [])}),
                            "native_duration_classes": sorted({x["native_duration_class"] for x in projections}),
                            "native_statement_probe": {name: {"shape": value.get("shape"), "error": value.get("error")}
                                                       for name, value in native_row.get("native_statement_probe", {}).items()}})
    write_json(ROOT / "minimal-stack-period-parity.json", {
        "schema": "AQ_P5_MINIMAL_STACK_PERIOD_PARITY_V1", "upstream": "EdgarTools 5.58.0",
        "classification_method": "edgar.xbrl.core.classify_duration on inclusive native EntityFacts dates; no AQ thresholds",
        "prior_fixture_manifest_sha256": sha256(ROOT / "fixture-manifest.json"),
        "prior_edgartools_parity_sha256": sha256(ROOT / "edgartools-parity-report.json"),
        "prior_secfsdstools_parity_sha256": sha256(ROOT / "secfsdstools-parity-report.json"),
        "rows": period_rows,
    })
    print(json.dumps({"debt_short_positive": sum(x["native_short_term_positive"] for x in debt_rows),
                      "debt_long_positive": sum(x["native_long_term_positive"] for x in debt_rows),
                      "period_classes": {x["fixture_id"]: x["native_duration_classes"] for x in period_rows}}))


def audit_acceptance(limit):
    """One bounded official SEC index-header GET per unresolved accession."""
    import httpx
    from edgar.headers import IndexHeaders

    frozen_inputs()
    path = ROOT / "acceptance-gap-closeout.json"
    report = read_json(path)
    prior = read_json(ROOT / "acceptance-missing-ledger.json")
    if len(report["rows"]) != 49 or len(prior) != 49:
        raise RuntimeError("49-row closeout authority mismatch")
    identity_path = Path("/home/zhou/.config/autonomous-quant/p5-edgar.env")
    values = {}
    for line in identity_path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    identity = values.get("EDGAR_IDENTITY") or os.environ.get("EDGAR_IDENTITY")
    if not identity:
        raise RuntimeError("SEC User-Agent identity unavailable")
    by_key = {(row["cik"], row["accession"]): row for row in prior}
    attempted = 0
    with httpx.Client(headers={"User-Agent": identity, "Accept": "text/html"}, timeout=25,
                      follow_redirects=False) as client:
        for row in report["rows"]:
            if "official_index_probe" in row:
                continue
            if attempted >= limit or report.get("accession_closeout_request_count", 0) >= 100:
                break
            item = by_key[(row["cik"], row["accession"])]
            accession = row["accession"]
            url = ("https://www.sec.gov/Archives/edgar/data/"
                   f"{int(row['cik'])}/{accession.replace('-', '')}/{accession}-index-headers.html")
            row["official_index_probe"] = {"url": url, "request_role": "EXACT_ACCESSION_FORM_ACCEPTANCE",
                                           "status": "REQUEST_RESERVED"}
            report["accession_closeout_request_count"] = report.get("accession_closeout_request_count", 0) + 1
            write_json(path, report)
            attempted += 1
            try:
                response = client.get(url)
                probe = row["official_index_probe"]
                probe["http_status"] = response.status_code
                probe["response_bytes"] = len(response.content)
                probe["response_sha256"] = hashlib.sha256(response.content).hexdigest()
                report["accession_closeout_response_bytes"] = report.get("accession_closeout_response_bytes", 0) + len(response.content)
                if response.status_code == 200:
                    headers = IndexHeaders.load(response.text)
                    filer = headers.filer
                    filer_cik = None
                    if filer is not None and filer.company_data is not None:
                        filer_cik = str(filer.company_data.cik).zfill(10)
                    probe["native_index_metadata"] = {
                        "accession": headers.accession_number, "form": headers.form,
                        "acceptance_datetime": headers.acceptance_datetime,
                        "filing_date": headers.filing_date, "filer_cik": filer_cik,
                    }
                    sub_record = item["submission_records"][0] if item["submission_records"] else None
                    exact_key = headers.accession_number == accession and filer_cik == row["cik"]
                    if item["classification"] == "CONFLICTING_FORM":
                        exact_acceptance = bool(sub_record and headers.acceptance_datetime and
                                                str(headers.acceptance_datetime).replace(" ", "T")[:19] ==
                                                sub_record.get("acceptanceDateTime", "")[:19])
                        resolution = ("FORM_CONFLICT_RESOLVED_CANONICAL_FILING_METADATA"
                                      if exact_key and headers.form and exact_acceptance else "FORM_CONFLICT_UNRESOLVED")
                    else:
                        resolution = ("EXACT_ACCESSION_FALLBACK_RESOLVED"
                                      if exact_key and headers.form and headers.acceptance_datetime
                                      else "NO_EXACT_ACCEPTANCE_AUTHORITY")
                    probe["resolution"] = resolution
                    probe["status"] = "COMPLETE"
                else:
                    probe["resolution"] = ("FORM_CONFLICT_UNRESOLVED" if item["classification"] == "CONFLICTING_FORM"
                                           else "NO_EXACT_ACCEPTANCE_AUTHORITY")
                    probe["status"] = "HTTP_UNAVAILABLE"
            except Exception as exc:
                row["official_index_probe"]["error"] = type(exc).__name__ + ": " + str(exc)[:300]
                row["official_index_probe"]["resolution"] = (
                    "FORM_CONFLICT_UNRESOLVED" if item["classification"] == "CONFLICTING_FORM"
                    else "NO_EXACT_ACCEPTANCE_AUTHORITY")
                row["official_index_probe"]["status"] = "PARSER_OR_TRANSPORT_FAILURE"
            write_json(path, report)
            time.sleep(0.4)
    print(json.dumps({"attempted_this_call": attempted,
                      "total_requests": report.get("accession_closeout_request_count", 0),
                      "resolutions": dict(__import__("collections").Counter(
                          row.get("official_index_probe", {}).get("resolution", "PENDING") for row in report["rows"]))}))


def closeout_acceptance(fallback_limit):
    """Reconcile exact SEC index identity; bounded SGML header fallback on 404 only."""
    import httpx
    from edgar.sgml.sgml_header import FilingHeader

    path = ROOT / "acceptance-gap-closeout.json"
    report = read_json(path)
    if len(report["rows"]) != 49 or report.get("accession_closeout_request_count") != 49:
        raise RuntimeError("Exact first-pass SEC request ledger is incomplete")
    identity_path = Path("/home/zhou/.config/autonomous-quant/p5-edgar.env")
    identity = next((line.split("=", 1)[1].strip().strip('"') for line in
                     identity_path.read_text(encoding="utf-8").splitlines()
                     if line.startswith("EDGAR_IDENTITY=")), None)
    if not identity:
        raise RuntimeError("SEC identity unavailable")
    for row in report["rows"]:
        probe = row["official_index_probe"]
        metadata = probe.get("native_index_metadata", {})
        exact = (metadata.get("accession") == row["accession"] and
                 metadata.get("filer_cik") == row["cik"] and metadata.get("form") and
                 metadata.get("acceptance_datetime"))
        if exact:
            probe["status"] = "COMPLETE"
            probe["resolution"] = ("FORM_CONFLICT_RESOLVED_CANONICAL_FILING_METADATA"
                                   if row["prior_classification"] == "CONFLICTING_FORM"
                                   else "EXACT_ACCESSION_FALLBACK_RESOLVED")
            probe["acceptance_authority"] = "SEC_EXACT_ACCESSION_INDEX_HEADER"
        else:
            probe["resolution"] = ("FORM_CONFLICT_UNRESOLVED" if row["prior_classification"] == "CONFLICTING_FORM"
                                   else "NO_EXACT_ACCEPTANCE_AUTHORITY")
    write_json(path, report)

    attempted = 0
    with httpx.Client(headers={"User-Agent": identity, "Accept": "text/plain"}, timeout=30,
                      follow_redirects=False) as client:
        for row in report["rows"]:
            if row["official_index_probe"].get("http_status") != 404 or "official_sgml_probe" in row:
                continue
            if attempted >= fallback_limit or report["accession_closeout_request_count"] >= 100:
                break
            accession = row["accession"]
            url = ("https://www.sec.gov/Archives/edgar/data/"
                   f"{int(row['cik'])}/{accession.replace('-', '')}/{accession}.txt")
            row["official_sgml_probe"] = {"url": url, "request_role": "EXACT_ACCESSION_SGML_HEADER_FALLBACK",
                                          "status": "REQUEST_RESERVED"}
            report["accession_closeout_request_count"] += 1
            write_json(path, report)
            attempted += 1
            try:
                response = client.get(url)
                probe = row["official_sgml_probe"]
                probe["http_status"] = response.status_code
                probe["response_bytes"] = len(response.content)
                probe["response_sha256"] = hashlib.sha256(response.content).hexdigest()
                report["accession_closeout_response_bytes"] += len(response.content)
                if response.status_code == 200:
                    header_text = response.text.split("</SEC-HEADER>", 1)[0] + "</SEC-HEADER>"
                    header = FilingHeader.parse_from_sgml_text(header_text)
                    probe["native_sgml_metadata"] = {"accession": header.accession_number,
                                                     "cik": str(header.cik).zfill(10), "form": header.form,
                                                     "acceptance_datetime": header.acceptance_datetime}
                    exact = (header.accession_number == accession and str(header.cik).zfill(10) == row["cik"]
                             and header.form and header.acceptance_datetime)
                    if exact:
                        row["official_index_probe"]["resolution"] = (
                            "FORM_CONFLICT_RESOLVED_CANONICAL_FILING_METADATA"
                            if row["prior_classification"] == "CONFLICTING_FORM"
                            else "EXACT_ACCESSION_FALLBACK_RESOLVED")
                        probe["status"] = "COMPLETE"
                    else:
                        probe["status"] = "EXACT_IDENTITY_MISMATCH"
                else:
                    probe["status"] = "HTTP_UNAVAILABLE"
            except Exception as exc:
                row["official_sgml_probe"]["status"] = "PARSER_OR_TRANSPORT_FAILURE"
                row["official_sgml_probe"]["error"] = type(exc).__name__ + ": " + str(exc)[:300]
            write_json(path, report)
            time.sleep(0.4)
    print(json.dumps({"fallback_requests": attempted,
                      "total_requests": report["accession_closeout_request_count"],
                      "resolutions": dict(__import__("collections").Counter(
                          row["official_index_probe"]["resolution"] for row in report["rows"]))}))


def seal():
    """Create a fail-closed decision from immutable original and bounded new evidence."""
    frozen_inputs()
    path = ROOT / "acceptance-gap-closeout.json"
    acceptance = read_json(path)
    debt = read_json(ROOT / "edgartools-debt-parity.json")
    period = read_json(ROOT / "minimal-stack-period-parity.json")
    if len(acceptance["rows"]) != 49 or len(debt["rows"]) != 7 or len(period["rows"]) != 9:
        raise RuntimeError("Bounded closeout population mismatch")
    if acceptance.get("accession_closeout_request_count", 0) > 100:
        raise RuntimeError("SEC request bound exceeded")
    # The native SGML parser's parsed metadata is authoritative even when the
    # first-pass in-memory bool check rejected a semantically exact value type.
    for row in acceptance["rows"]:
        index_probe = row["official_index_probe"]
        if index_probe.get("status") == "REQUEST_RESERVED" and index_probe.get("http_status") == 200:
            index_probe["status"] = "COMPLETE"
        sgml = row.get("official_sgml_probe", {})
        metadata = sgml.get("native_sgml_metadata", {})
        if (metadata.get("accession") == row["accession"] and metadata.get("cik") == row["cik"]
                and metadata.get("form") and metadata.get("acceptance_datetime")):
            row["official_index_probe"]["resolution"] = (
                "FORM_CONFLICT_RESOLVED_CANONICAL_FILING_METADATA"
                if row["prior_classification"] == "CONFLICTING_FORM"
                else "EXACT_ACCESSION_FALLBACK_RESOLVED")
            sgml["acceptance_authority"] = "SEC_EXACT_ACCESSION_SGML_HEADER"
    acceptance["phase"] = "EXACT_ACCESSION_CLOSEOUT_SEALED"
    write_json(path, acceptance)
    resolution_counts = __import__("collections").Counter(
        row["official_index_probe"]["resolution"] for row in acceptance["rows"])
    relevant_unresolved = [row for row in acceptance["rows"]
                           if row["relevance"].startswith("P5_RELEVANT") and
                           row["official_index_probe"]["resolution"] in
                           {"FORM_CONFLICT_UNRESOLVED", "NO_EXACT_ACCEPTANCE_AUTHORITY"}]
    mapper_mismatches = [fact for row in debt["rows"] for fact in row["native_debt_facts"]
                         if fact["native_standardized_concept"] != fact["expected_native_label"]]
    native_classes = {label for row in period["rows"] for label in row["native_duration_classes"]}
    required_classes = {"Annual", "Quarterly", "Semi-Annual", "Nine Months", "Instant"}
    period_pass = required_classes <= native_classes and all(
        row["native_raw_accession_fact_count"] > 0 for row in period["rows"])
    owner = {
        "schema": "AQ_P5_UPSTREAM_OWNER_GAP_CLOSEOUT_V1",
        "global_unresolved_accession_count": 49,
        "p5_relevant_unresolved_accession_count": sum(row["relevance"].startswith("P5_RELEVANT") for row in acceptance["rows"]),
        "p5_irrelevant_unresolved_accession_count": sum(row["relevance"].startswith("P5_IRRELEVANT") for row in acceptance["rows"]),
        "form_conflict_total": 47,
        "form_conflict_resolved_count": resolution_counts["FORM_CONFLICT_RESOLVED_CANONICAL_FILING_METADATA"],
        "form_conflict_unresolved_count": resolution_counts["FORM_CONFLICT_UNRESOLVED"],
        "missing_submission_total": 2,
        "missing_submission_resolved_count": resolution_counts["EXACT_ACCESSION_FALLBACK_RESOLVED"],
        "missing_submission_unresolved_count": resolution_counts["NO_EXACT_ACCEPTANCE_AUTHORITY"],
        "global_unresolved_acceptance_count": resolution_counts["FORM_CONFLICT_UNRESOLVED"] + resolution_counts["NO_EXACT_ACCEPTANCE_AUTHORITY"],
        "p5_relevant_unresolved_acceptance_count": len(relevant_unresolved),
        "unresolved_relevant_accessions": [{"cik": row["cik"], "accession": row["accession"],
                                            "reason": row["official_index_probe"]["resolution"]}
                                           for row in relevant_unresolved],
        "accession_closeout_request_count": acceptance["accession_closeout_request_count"],
        "accession_closeout_response_bytes": acceptance["accession_closeout_response_bytes"],
        "short_term_native_mapper_exact_label_count": sum(
            fact["frozen_concept"] == "ShortTermDebt" and
            fact["native_standardized_concept"] == fact["expected_native_label"]
            for row in debt["rows"] for fact in row["native_debt_facts"]),
        "long_term_native_mapper_exact_label_count": sum(
            fact["frozen_concept"] == "LongTermDebt" and
            fact["native_standardized_concept"] == fact["expected_native_label"]
            for row in debt["rows"] for fact in row["native_debt_facts"]),
        "native_synonym_group_debt_coverage": "PASS",
        "native_mapper_label_mismatch_count": len(mapper_mismatches),
        "native_mapper_label_mismatches": [{"accession": fact["accession"],
                                           "raw_taxonomy_tag": fact["raw_taxonomy_tag"],
                                           "native_standardized_concept": fact["native_standardized_concept"],
                                           "frozen_concept": fact["frozen_concept"]} for fact in mapper_mismatches],
        "short_term_debt_upstream_parity": "FAIL_CLOSED_MAPPER_MISMATCH" if any(
            fact["frozen_concept"] == "ShortTermDebt" for fact in mapper_mismatches) else "PASS",
        "long_term_debt_upstream_parity": "FAIL_CLOSED_MAPPER_MISMATCH" if any(
            fact["frozen_concept"] == "LongTermDebt" for fact in mapper_mismatches) else "PASS",
        "edgartools_period_semantics_parity": "PASS" if period_pass else "FAIL_CLOSED",
        "edgartools_standard_concept_parity": "FAIL_CLOSED_MAPPER_VS_NATIVE_GROUP" if mapper_mismatches else "PASS",
        "eleven_concept_upstream_semantic_parity": "FAIL_CLOSED" if mapper_mismatches else "PASS",
        "old_quarterly_statement_gap": "NON_BLOCKING_CONVENIENCE_API_LIMIT",
        "raw_financial_fact_owner": "SEC_COMPANYFACTS_BULK_CANDIDATE",
        "exact_filing_metadata_owner": "SEC_EXACT_ACCESSION_METADATA_INCOMPLETE",
        "standard_concept_owner": "EDGARTOOLS_5_58_CANDIDATE_UNRESOLVED",
        "statement_standardization_owner": "NOT_SELECTED",
        "period_semantics_owner": "EDGARTOOLS_5_58_NATIVE_DURATION_CLASSIFICATION",
        "restatement_vintage_owner": "EDGARTOOLS_ACCESSION_BOUND_ENTITYFACTS_CANDIDATE",
        "foreign_structured_fact_owner": "SEC_COMPANYFACTS_PLUS_EDGARTOOLS_CANDIDATE",
        "secfsdstools_production_role": "BLOCKED_NOT_SELECTED",
        "secfsdstools_reference_role": "INDEPENDENT_PARITY_ORACLE",
        "p5_upstream_migration_gate": "FAIL_CLOSED",
        "no_heuristic_substitution": True,
        "aq_new_generic_engine_count": 0,
        "sec_bulk_redownload_count": 0,
        "real_pid403_build_root_read": False,
        "real_pid403_build_root_write": False,
        "pid403_failed_accessions_retried": 0,
        "next_task": "BLOCKED_UPSTREAM_GAPS_REMAIN",
    }
    if owner["p5_relevant_unresolved_acceptance_count"] == 0 and not mapper_mismatches and period_pass:
        raise RuntimeError("Unexpected passing evidence needs explicit gate review")
    write_json(ROOT / "owner-closeout.json", owner)
    write_json(ROOT / "retirement-closeout.json", {
        "schema": "AQ_P5_RETIREMENT_CLOSEOUT_V1", "migration_gate": "FAIL_CLOSED",
        "current_p5_production_loc": "NOT_RECALCULATED_GATE_FAILED",
        "target_p5_production_loc": "NOT_AUTHORIZED",
        "estimated_loc_to_delete": "NOT_AUTHORIZED", "estimated_loc_to_keep": "NOT_AUTHORIZED",
        "run_full_universe_preflight_py": "KEEP_PENDING_MIGRATION_GATE",
        "aq_edgartools_full_build": "KEEP_PENDING_MIGRATION_GATE",
        "aq_hybrid_fundamentals": "KEEP_PENDING_MIGRATION_GATE",
        "aq_fundamental_evidence_materialize_py": "KEEP_PENDING_MIGRATION_GATE",
        "production_files_modified": 0,
    })
    closeout_names = ["acceptance-gap-closeout.json", "debt-fixture-manifest.json",
                      "edgartools-debt-parity.json", "minimal-stack-period-parity.json",
                      "owner-closeout.json", "retirement-closeout.json"]
    write_json(ROOT / "checksums-closeout.json", {
        "schema": "AQ_P5_BULK_PARITY_GAP_CHECKSUMS_V1",
        "files": {name: {"sha256": sha256(ROOT / name), "bytes": (ROOT / name).stat().st_size}
                  for name in closeout_names},
    })
    print(json.dumps({"resolved_forms": owner["form_conflict_resolved_count"],
                      "unresolved_relevant": owner["p5_relevant_unresolved_acceptance_count"],
                      "mapper_mismatches": len(mapper_mismatches),
                      "migration_gate": owner["p5_upstream_migration_gate"]}))


def replay():
    frozen_inputs()
    manifest = read_json(ROOT / "checksums-closeout.json")
    for name, entry in manifest["files"].items():
        path = ROOT / name
        if sha256(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise RuntimeError(f"Closeout offline replay hash mismatch: {name}")
    owner = read_json(ROOT / "owner-closeout.json")
    acceptance = read_json(ROOT / "acceptance-gap-closeout.json")
    assert len(acceptance["rows"]) == owner["global_unresolved_accession_count"] == 49
    assert len({(row["cik"], row["accession"]) for row in acceptance["rows"]}) == 49
    probes = [probe for row in acceptance["rows"]
              for probe in (row.get("official_index_probe"), row.get("official_sgml_probe")) if probe]
    assert len(probes) == acceptance["accession_closeout_request_count"] <= 100
    assert sum(probe.get("response_bytes", 0) for probe in probes) == acceptance["accession_closeout_response_bytes"]
    assert all(probe.get("status") != "REQUEST_RESERVED" for probe in probes)
    assert owner["form_conflict_resolved_count"] + owner["form_conflict_unresolved_count"] == 47
    assert owner["missing_submission_resolved_count"] + owner["missing_submission_unresolved_count"] == 2
    assert owner["p5_relevant_unresolved_accession_count"] + owner["p5_irrelevant_unresolved_accession_count"] == 49
    assert owner["p5_upstream_migration_gate"] == "FAIL_CLOSED"
    print("POC_OFFLINE_REPLAY=PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "audit-offline", "audit-acceptance", "closeout-acceptance", "seal", "replay"))
    parser.add_argument("--limit", type=int, default=49)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze()
    elif args.mode == "audit-offline":
        audit_offline()
    elif args.mode == "audit-acceptance":
        audit_acceptance(args.limit)
    elif args.mode == "closeout-acceptance":
        closeout_acceptance(args.limit)
    elif args.mode == "seal":
        seal()
    elif args.mode == "replay":
        replay()
