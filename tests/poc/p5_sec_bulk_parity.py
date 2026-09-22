"""Audit-only exact join of frozen SEC bulk archives for the P5 bound CIKs.

This script does not fetch network data or provide a production API.
"""

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path


FIELDS = ("start", "end", "val", "accn", "form", "filed", "fy", "fp", "frame")
ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def submission_rows(blob):
    recent = blob.get("filings", {}).get("recent", {})
    accessions = recent.get("accessionNumber", [])
    for index, accession in enumerate(accessions):
        yield {key: values[index] if index < len(values) else None
               for key, values in recent.items() if isinstance(values, list)} | {"accessionNumber": accession}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("join", "parity", "verify", "seal"), default="join")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    root = args.root
    if args.mode == "parity":
        run_parity(root)
        return
    if args.mode == "verify":
        run_verify(root)
        return
    if args.mode == "seal":
        run_seal(root)
        return
    if args.ledger is None:
        parser.error("--ledger is required for join mode")
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    ciks = sorted({str(row["cik"]).zfill(10) for row in ledger["records"]})
    if len(ciks) != 711 or ledger["bound_episode_count"] != 721:
        raise ValueError("Frozen episode/CIK population mismatch")
    cf_path = root / "companyfacts.zip"
    sub_path = root / "submissions.zip"
    if not cf_path.is_file() or not sub_path.is_file():
        raise FileNotFoundError("Both official bulk archives must already exist")
    source = {}
    for name, path in (("companyfacts", cf_path), ("submissions", sub_path)):
        source[name] = {"url": "https://www.sec.gov/Archives/edgar/daily-index/" + ("xbrl/companyfacts.zip" if name == "companyfacts" else "bulkdata/submissions.zip"),
                        "bytes": path.stat().st_size, "sha256": sha256(path),
                        "local_mtime_utc": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat()}
    write_json(root / "bulk-source-identities.json", source)
    candidate = {}
    facts_by_form = collections.Counter()
    facts_by_year = collections.Counter()
    missing_cik_files = []
    fact_count = 0
    with zipfile.ZipFile(cf_path) as facts_zip, gzip.open(root / "companyfacts-fact-inventory.jsonl.gz", "wt", encoding="utf-8") as inventory:
        names = set(facts_zip.namelist())
        for cik in ciks:
            name = f"CIK{cik}.json"
            if name not in names:
                missing_cik_files.append(cik)
                continue
            body = json.loads(facts_zip.read(name))
            for taxonomy, concepts in body.get("facts", {}).items():
                for concept, entry in concepts.items():
                    for unit, rows in entry.get("units", {}).items():
                        for row in rows:
                            fact = {"cik": cik, "taxonomy": taxonomy, "concept": concept, "unit": unit}
                            fact.update({key: row.get(key) for key in FIELDS})
                            inventory.write(json.dumps(fact, separators=(",", ":"), sort_keys=True) + "\n")
                            fact_count += 1
                            accession = row.get("accn")
                            if ACCESSION.fullmatch(accession or ""):
                                key = (cik, accession)
                                state = candidate.setdefault(key, {"companyfacts_forms": set(), "companyfacts_filed": set(), "fact_count": 0})
                                state["companyfacts_forms"].add(row.get("form"))
                                state["companyfacts_filed"].add(row.get("filed"))
                                state["fact_count"] += 1
                                facts_by_form[str(row.get("form"))] += 1
                                facts_by_year[str(row.get("filed"))[:4]] += 1
    results = {}
    older_references = []
    absent_submissions_ciks = []
    with zipfile.ZipFile(sub_path) as submissions_zip:
        names = set(submissions_zip.namelist())
        for cik in ciks:
            name = f"CIK{cik}.json"
            if name not in names:
                absent_submissions_ciks.append(cik)
                continue
            body = json.loads(submissions_zip.read(name))
            for item in body.get("filings", {}).get("files", []):
                older_references.append({"cik": cik, **item, "present_in_bulk": item.get("name") in names})
            for row in submission_rows(body):
                key = (cik, row.get("accessionNumber"))
                if key in candidate:
                    results.setdefault(key, []).append({"source": name, "form": row.get("form"),
                                                          "acceptanceDateTime": row.get("acceptanceDateTime"),
                                                          "filingDate": row.get("filingDate"),
                                                          "reportDate": row.get("reportDate")})
        # An official bulk ZIP may include older referenced JSON files. If so, read them here.
        for ref in older_references:
            name = ref.get("name")
            if not name or name not in names:
                continue
            body = json.loads(submissions_zip.read(name))
            for row in submission_rows({"filings": {"recent": body}}):
                key = (ref["cik"], row.get("accessionNumber"))
                if key in candidate:
                    results.setdefault(key, []).append({"source": name, "form": row.get("form"),
                                                          "acceptanceDateTime": row.get("acceptanceDateTime"),
                                                          "filingDate": row.get("filingDate"),
                                                          "reportDate": row.get("reportDate")})
    by_year_form = collections.Counter()
    classifications = collections.Counter()
    missing_ledger = []
    identical_bulk_overlap_count = 0
    for (cik, accession), state in sorted(candidate.items()):
        original_rows = results.get((cik, accession), [])
        rows = list({(row["form"], row["acceptanceDateTime"], row["filingDate"], row["reportDate"]): row
                     for row in original_rows}.values())
        identical_bulk_overlap_count += len(original_rows) - len(rows)
        forms = sorted(str(value) for value in state["companyfacts_forms"])
        years = sorted(str(value)[:4] for value in state["companyfacts_filed"])
        if (len(rows) == 1 and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z",
                                             str(rows[0].get("acceptanceDateTime") or ""))
                and rows[0].get("form") in state["companyfacts_forms"]):
            classification = "EXACT_ACCEPTANCE_FROM_SEC_SUBMISSIONS"
        elif len(rows) > 1:
            classification = "DUPLICATE_SUBMISSION_ACCESSION"
        elif len(rows) == 1 and rows[0].get("form") not in state["companyfacts_forms"]:
            classification = "CONFLICTING_FORM"
        elif len(rows) == 1:
            classification = "NO_EXACT_ACCEPTANCE_AUTHORITY"
        else:
            classification = "MISSING_SUBMISSION_ACCESSION"
        classifications[classification] += 1
        for year in set(years):
            for form in forms:
                by_year_form[(year, form, classification)] += 1
        if classification != "EXACT_ACCEPTANCE_FROM_SEC_SUBMISSIONS":
            missing_ledger.append({"cik": cik, "accession": accession, "companyfacts_forms": forms,
                                   "companyfacts_filed": years, "submission_records": rows,
                                   "classification": classification})
    report = {"bound_cik_count": len(ciks), "bound_episode_count": ledger["bound_episode_count"],
              "identity_exclusion_count": 111, "companyfacts_missing_cik_files": missing_cik_files,
              "submissions_missing_cik_files": absent_submissions_ciks,
              "companyfacts_fact_count": fact_count, "companyfacts_unique_accessions": len(candidate),
              "joined_unique_accessions": sum(bool(results.get(key)) for key in candidate),
              "classifications": dict(classifications), "companyfacts_facts_by_form": dict(facts_by_form),
              "companyfacts_facts_by_filed_year": dict(facts_by_year),
              "by_year_form_classification": [{"year": y, "form": f, "classification": c, "count": n}
                                               for (y, f, c), n in sorted(by_year_form.items())],
              "older_references_total": len(older_references),
              "older_references_present_in_bulk": sum(x["present_in_bulk"] for x in older_references),
              "identical_bulk_recent_older_overlap_count": identical_bulk_overlap_count,
              "older_references": older_references}
    write_json(root / "acceptance-join-report.json", report)
    write_json(root / "acceptance-missing-ledger.json", missing_ledger)
    print(json.dumps({"facts": fact_count, "candidate_accessions": len(candidate),
                      "joined": report["joined_unique_accessions"], "classifications": dict(classifications),
                      "older_refs": len(older_references), "older_refs_in_zip": report["older_references_present_in_bulk"]}))


def run_parity(root):
    """Probe two installed upstreams against the pre-frozen SEC accession set."""
    from edgar.entity.entity_facts import EntityFacts
    from edgar.entity.parser import EntityFactsParser
    from edgar.standardization import get_synonym_groups

    config_path = root / "secfsdstools-readonly.cfg"
    if "AutoUpdate = False" not in config_path.read_text(encoding="utf-8"):
        raise ValueError("secfsdstools AutoUpdate must be disabled before import")
    os.environ["SECFSDSTOOLS_CFG"] = str(config_path)
    from secfsdstools.e_collector.reportcollecting import SingleReportCollector
    from secfsdstools.e_filter.rawfiltering import (MainCoregRawFilter, OfficialTagsOnlyRawFilter,
                                                      ReportPeriodRawFilter, USDOnlyRawFilter)
    from secfsdstools.f_standardize.bs_standardize import BalanceSheetStandardizer
    from secfsdstools.f_standardize.is_standardize import IncomeStatementStandardizer
    from secfsdstools.f_standardize.cf_standardize import CashFlowStandardizer

    fixture_path = root / "fixture-manifest.json"
    fixture_sha = sha256(fixture_path)
    manifest = json.loads(fixture_path.read_text(encoding="utf-8"))
    names = {
        "Revenue": "revenue", "NetIncome": "net_income", "Assets": "total_assets",
        "Liabilities": "total_liabilities", "CommonEquity": "stockholders_equity",
        "NetCashFromOperatingActivities": "operating_cash_flow",
        "CashAndCashEquivalents": "cash_and_equivalents",
        "CurrentAssetsTotal": "total_current_assets",
        "CurrentLiabilitiesTotal": "total_current_liabilities",
        "ShortTermDebt": "short_term_debt", "LongTermDebt": "long_term_debt",
    }
    fsds_columns = {
        "Revenue": ("IS", "Revenues"), "NetIncome": ("IS", "NetIncomeLoss"),
        "Assets": ("BS", "Assets"), "Liabilities": ("BS", "Liabilities"),
        "CommonEquity": ("BS", "HolderEquity"),
        "NetCashFromOperatingActivities": ("CF", "NetCashProvidedByUsedInOperatingActivities"),
        "CashAndCashEquivalents": ("BS", "Cash"),
        "CurrentAssetsTotal": ("BS", "AssetsCurrent"),
        "CurrentLiabilitiesTotal": ("BS", "LiabilitiesCurrent"),
        "ShortTermDebt": ("BS", "ShortTermDebt"),
        "LongTermDebt": ("BS", "LongTermDebt"),
    }
    synonyms = get_synonym_groups()
    tagsets = {name: set(synonyms.get_group(group).synonyms) for name, group in names.items()}
    earlier = Path("/mnt/d/AQ_DATA/P5/sec-fsds-secfsdstools-deployment-and-bounded-poc-001")
    db_path = earlier / "secfsdstools-db/secfsdstools.db"
    db_sha_before = sha256(db_path)
    edgar_rows = []
    fsds_rows = []
    with zipfile.ZipFile(root / "companyfacts.zip") as companyfacts_zip:
        for fixture in manifest["fixtures"]:
            cik = fixture["cik"]
            accession = fixture["accession"]
            source_name = f"CIK{cik}.json"
            entry = {"fixture": fixture, "fixture_manifest_sha256": fixture_sha,
                     "companyfacts_member": source_name}
            if source_name not in companyfacts_zip.namelist():
                entry["classification"] = "COMPANYFACTS_CIK_ABSENT"
                edgar_rows.append(entry)
            else:
                source_bytes = companyfacts_zip.read(source_name)
                entry["companyfacts_member_sha256"] = hashlib.sha256(source_bytes).hexdigest()
                parsed = EntityFactsParser.parse_company_facts(json.loads(source_bytes))
                if parsed is None:
                    entry["classification"] = "EDGARTOOLS_NATIVE_PARSE_FAIL"
                else:
                    facts = [fact for fact in parsed.query().execute() if fact.accession == accession]
                    entry["accession_fact_count"] = len(facts)
                    entry["concepts"] = {}
                    for name, tags in tagsets.items():
                        selected = [fact for fact in facts if fact.concept.rsplit(":", 1)[-1] in tags]
                        entry["concepts"][name] = [
                            {"tag": fact.concept, "value": fact.value, "unit": fact.unit,
                             "period_start": fact.period_start, "period_end": fact.period_end,
                             "period_type": fact.period_type, "fiscal_year": fact.fiscal_year,
                             "fiscal_period": fact.fiscal_period, "form": fact.form_type,
                             "filing_date": fact.filing_date, "accession": fact.accession,
                             "dimensions": fact.dimensions, "is_restated": fact.is_restated,
                             "source_path": "EntityFactsParser.parse_company_facts -> EntityFacts.query().execute()",
                             "direct_or_derived": "DIRECT_SEC_COMPANYFACTS"} for fact in selected]
                    # The same installed upstream statement methods are probed with only
                    # this exact accession's facts, not an implicit latest-filing view.
                    isolated = EntityFacts(cik=int(cik), name=parsed.name, facts=facts) if facts else None
                    statements = {}
                    if isolated:
                        for key, method in (("IS", isolated.income_statement),
                                            ("BS", isolated.balance_sheet),
                                            ("CF", isolated.cash_flow_statement)):
                            try:
                                selected_period = "quarterly" if fixture["form"] in ("10-Q", "10-Q/A", "10-QT") else "annual"
                                statement = method(periods=4, as_dataframe=True, period=selected_period)
                                statements[key] = {"shape": list(statement.shape),
                                                   "requested_period": selected_period,
                                                   "columns": [str(x) for x in statement.columns],
                                                   "index": [str(x) for x in statement.index],
                                                   "rows": statement.reset_index().to_dict("records")}
                            except Exception as exc:
                                statements[key] = {"error": type(exc).__name__ + ": " + str(exc)[:500]}
                    entry["native_statement_probe"] = statements
                    entry["classification"] = "RAW_ACCESSION_FACTS_PRESENT" if facts else "NO_COMPANYFACTS_FOR_ACCESSION"
                edgar_rows.append(entry)

            fsds = {"fixture": fixture, "fixture_manifest_sha256": fixture_sha,
                    "historical_upstream_index_sha256_before": db_sha_before}
            try:
                bag = SingleReportCollector.get_report_by_adsh(accession).collect()
                fsds["raw_submissions"] = bag.sub_df.to_dict("records")
                fsds["raw_num_count"] = len(bag.num_df)
                fsds["raw_pre_count"] = len(bag.pre_df)
                main = bag[MainCoregRawFilter()]
                official = main[OfficialTagsOnlyRawFilter()]
                period = official[ReportPeriodRawFilter()]
                fsds["filter_counts"] = {"main_coreg": len(main.num_df),
                                          "official_tags": len(official.num_df),
                                          "report_period": len(period.num_df)}
                # USD filter is diagnostic only for non-foreign filings.
                if fixture["form"] not in ("20-F", "6-K"):
                    period = period[USDOnlyRawFilter()]
                    fsds["filter_counts"]["usd"] = len(period.num_df)
                fsds["raw_period_rows"] = period.num_df[["tag", "version", "ddate", "qtrs", "uom", "coreg", "segments", "value"]].to_dict("records")
                joined = period.join()
                standardized = {}
                for key, cls in (("BS", BalanceSheetStandardizer),
                                 ("IS", IncomeStatementStandardizer),
                                 ("CF", CashFlowStandardizer)):
                    try:
                        standardizer = cls()
                        frame = joined.present(standardizer)
                        standardized[key] = {"columns": list(frame.columns),
                                             "rows": frame.to_dict("records"),
                                             "rule_log_rows": len(standardizer.get_standardize_bag().applied_rules_log_df)}
                    except Exception as exc:
                        standardized[key] = {"error": type(exc).__name__ + ": " + str(exc)[:500]}
                fsds["native_standardized_statements"] = standardized
                fsds["concepts"] = {}
                for name, (statement, column) in fsds_columns.items():
                    source = standardized[statement]
                    fsds["concepts"][name] = {
                        "standardizer_column": column,
                        "native_rows": [{"adsh": row.get("adsh"), "form": row.get("form"),
                                         "fy": row.get("fy"), "fp": row.get("fp"),
                                         "ddate": row.get("ddate"), "qtrs": row.get("qtrs"),
                                         "value": row.get(column)}
                                        for row in source.get("rows", []) if column in row],
                        "raw_synonym_rows": [row for row in fsds["raw_period_rows"] if row["tag"] in tagsets[name]],
                    }
                fsds["classification"] = "COLLECTED_AND_STANDARDIZED"
            except Exception as exc:
                fsds["classification"] = "UPSTREAM_COLLECTION_OR_STANDARDIZATION_FAILURE"
                fsds["error"] = type(exc).__name__ + ": " + str(exc)[:500]
            fsds_rows.append(fsds)
            print(fixture["id"], entry["classification"], fsds["classification"], flush=True)
    db_sha_after = sha256(db_path)
    write_json(root / "edgartools-parity-report.json", {"version": "5.58.0", "fixture_manifest_sha256": fixture_sha,
                                                       "fixtures": edgar_rows})
    write_json(root / "secfsdstools-parity-report.json", {"version": "2.4.3", "fixture_manifest_sha256": fixture_sha,
                                                        "upstream_index_sha256_before": db_sha_before,
                                                        "upstream_index_sha256_after": db_sha_after,
                                                        "upstream_index_mutated": db_sha_before != db_sha_after,
                                                        "fixtures": fsds_rows})
    if db_sha_before != db_sha_after:
        raise RuntimeError("Read-only upstream evidence index mutated")


def run_verify(root):
    join = json.loads((root / "acceptance-join-report.json").read_text(encoding="utf-8"))
    fixture = json.loads((root / "fixture-manifest.json").read_text(encoding="utf-8"))
    edgar = json.loads((root / "edgartools-parity-report.json").read_text(encoding="utf-8"))
    fsds = json.loads((root / "secfsdstools-parity-report.json").read_text(encoding="utf-8"))
    classes = join["classifications"]
    assert join["bound_cik_count"] == 711 and join["bound_episode_count"] == 721
    assert join["identity_exclusion_count"] == 111
    assert join["companyfacts_unique_accessions"] == sum(classes.values())
    assert join["joined_unique_accessions"] == (
        classes.get("EXACT_ACCEPTANCE_FROM_SEC_SUBMISSIONS", 0)
        + classes.get("CONFLICTING_FORM", 0)
        + classes.get("DUPLICATE_SUBMISSION_ACCESSION", 0)
        + classes.get("NO_EXACT_ACCEPTANCE_AUTHORITY", 0)
    )
    assert join["older_references_total"] == join["older_references_present_in_bulk"]
    assert len(fixture["fixtures"]) == len(edgar["fixtures"]) == len(fsds["fixtures"]) == 9
    assert len(fixture["concepts"]) == 11
    assert fsds["upstream_index_mutated"] is False
    assert [x["fixture"]["accession"] for x in edgar["fixtures"]] == [
        x["accession"] for x in fixture["fixtures"]]
    assert [x["fixture"]["accession"] for x in fsds["fixtures"]] == [
        x["accession"] for x in fixture["fixtures"]]
    assert all(len(x.get("concepts", {})) == 11 for x in edgar["fixtures"])
    assert all(len(x.get("concepts", {})) == 11 for x in fsds["fixtures"])
    periods = {x["fixture"]["id"]: {int(row["qtrs"]) for row in x["raw_period_rows"]}
               for x in fsds["fixtures"]}
    assert {0, 4} <= periods["apple_2009_10k_original"]
    assert {0, 1} <= periods["apple_2010_10q_direct"]
    assert {0, 1, 2} <= periods["microsoft_2010_10q_six_month"]
    assert {0, 1, 3} <= periods["walmart_2009_10q_nine_month"]
    assert {0, 1, 2} <= periods["myriad_2021_10kt_transition"]
    print("POC_REPLAY_VERIFY=PASS")


def run_seal(root):
    files = sorted(path for path in root.iterdir()
                   if path.is_file() and path.name != "checksums.json" and not path.name.endswith(".part"))
    write_json(root / "checksums.json",
               {"schema": "AQ_P5_UPSTREAM_PARITY_POC_CHECKSUMS_V1",
                "files": {path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in files}})
    print(f"SEALED_FILE_COUNT={len(files)}")


if __name__ == "__main__":
    main()
