from __future__ import annotations

from contextlib import AbstractContextManager

import pyarrow as pa

import run_full_universe_preflight as runner
from aq_edgartools_full_build import (
    LIVE_ADMIT_EXISTING_PROCESSOR,
    LIVE_REJECT_NON_BOUND_CIK,
    LIVE_SKIP_DUPLICATE_ACCESSION,
    LIVE_SKIP_NON_PERIODIC_FILING,
    LIVE_SOURCE_UNAVAILABLE,
    plan_native_current_filings_page,
)
from edgar.current_filings import CurrentFilings


def _current_filings() -> CurrentFilings:
    rows = [
        {"form": "10-Q", "company": "Bound", "cik": 1, "filing_date": "2024-05-01", "accession_number": "0001-24-000001", "accepted": "2024-05-01T16:01:00", "report_period": "2024-03-31"},
        {"form": "10-Q", "company": "Bound", "cik": 1, "filing_date": "2024-05-01", "accession_number": "0001-24-000001", "accepted": "2024-05-01T16:01:00", "report_period": "2024-03-31"},
        {"form": "10-K", "company": "Bound", "cik": 1, "filing_date": "2024-02-01", "accession_number": "0001-24-000002", "accepted": "2024-02-01T16:01:00", "report_period": "2023-12-31"},
        {"form": "10-K/A", "company": "Bound", "cik": 1, "filing_date": "2024-03-01", "accession_number": "0001-24-000003", "accepted": "2024-03-01T16:01:00", "report_period": "2023-12-31"},
        {"form": "10-KT", "company": "Bound", "cik": 1, "filing_date": "2024-04-01", "accession_number": "0001-24-000004", "accepted": "2024-04-01T16:01:00", "report_period": "2024-01-31"},
        {"form": "10-Q", "company": "Other", "cik": 9, "filing_date": "2024-05-02", "accession_number": "0009-24-000001", "accepted": "2024-05-02T16:01:00", "report_period": "2024-03-31"},
        {"form": "10-Q", "company": "Bound", "cik": 1, "filing_date": "2024-05-03", "accession_number": "0001-24-000005", "accepted": "2024-05-03T16:01:00", "report_period": "2024-03-31"},
        {"form": "8-K", "company": "Bound", "cik": 1, "filing_date": "2024-05-04", "accession_number": "0001-24-000006", "accepted": "2024-05-04T16:01:00", "report_period": "2024-05-04"},
    ]
    return CurrentFilings(pa.Table.from_pylist(rows), page_size=40)


def test_native_current_page_applies_only_thin_policy() -> None:
    plan = plan_native_current_filings_page(
        _current_filings(),
        accepted_ciks={"0000000001"},
        processed_accessions=set(),
        source_unavailable_accessions={"0001-24-000005"},
    )
    decisions = {row["accession"]: row["decision"] for row in plan["decisions"]}
    selected = [row["accession"] for row in plan["selected"]]

    assert plan["observed_count"] == 8
    assert selected == [
        "0001-24-000001",
        "0001-24-000002",
        "0001-24-000003",
        "0001-24-000004",
    ]
    assert [row["decision"] for row in plan["decisions"]].count(
        LIVE_SKIP_DUPLICATE_ACCESSION
    ) == 1
    assert decisions["0001-24-000003"] == LIVE_ADMIT_EXISTING_PROCESSOR
    assert decisions["0001-24-000004"] == LIVE_ADMIT_EXISTING_PROCESSOR
    assert decisions["0009-24-000001"] == LIVE_REJECT_NON_BOUND_CIK
    assert decisions["0001-24-000005"] == LIVE_SOURCE_UNAVAILABLE
    assert decisions["0001-24-000006"] == LIVE_SKIP_NON_PERIODIC_FILING


class _NetworkMeter(AbstractContextManager):
    request_count = 0
    byte_count = 0

    def __exit__(self, *args: object) -> None:
        return None


def test_selected_rows_reuse_existing_exact_accession_processor(
    monkeypatch, tmp_path
) -> None:
    plan = plan_native_current_filings_page(
        _current_filings(),
        accepted_ciks={1},
        processed_accessions=set(),
        source_unavailable_accessions={"0001-24-000005"},
    )
    processed: list[str] = []

    def fake_process(row, metadata, *, root, build_spec_identity, cache_stats):
        accession = str(row["accession"])
        processed.append(accession)
        (root / "source-manifests").mkdir(parents=True, exist_ok=True)
        runner._write_json(
            root / "source-manifests" / f"{accession}.json",
            {"source_byte_count": 0},
        )
        return {"accession": accession, "terminal_state": "COMPLETE_WITH_EVIDENCE"}

    monkeypatch.setattr(runner, "process_exact_accession", fake_process)
    monkeypatch.setattr(runner, "_NetworkMeter", _NetworkMeter)
    monkeypatch.setattr(runner, "_configure_edgartools", lambda _path: None)
    report = runner.execute_accession_set(
        build_root=tmp_path,
        output_root=tmp_path / "live-cycle",
        selected=plan["selected"],
        build_spec_identity="sha256:offline-live-poc",
        invocation_name="offline-native-current-page",
    )

    assert processed == [row["accession"] for row in plan["selected"]]
    assert report["processed_count"] == 4
    assert report["network_request_count"] == 0
