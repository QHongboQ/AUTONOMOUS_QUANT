from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from edgar import Filing
from edgar.attachments import Attachment, Attachments
from edgar.company_reports import (
    CurrentReport,
    FortyF,
    SixK,
    TenK,
    TenQ,
    TwentyF,
)
from edgar.documents import ParserConfig, parse_html
from edgar.xbrl.notes import Note, Notes


TEN_K_HTML = """
<html><body>
<h1>ITEM 1. BUSINESS</h1>
<p>Example Corp sells analytical systems to institutional customers.</p>
<h1>ITEM 1A. RISK FACTORS</h1>
<p>Demand and supply-chain conditions may materially affect results.</p>
<h1>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS</h1>
<p>Revenue increased because subscription demand expanded.</p>
<h1>ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA</h1>
<p>Audited financial statements follow.</p>
</body></html>
"""

TEN_Q_HTML = """
<html><body>
<h1>PART I</h1>
<h2>ITEM 1. FINANCIAL STATEMENTS</h2>
<p>Condensed statements follow.</p>
<h2>ITEM 2. MANAGEMENT'S DISCUSSION AND ANALYSIS</h2>
<p>Quarterly revenue increased because product demand expanded.</p>
<h1>PART II</h1>
<h2>ITEM 1A. RISK FACTORS</h2>
<p>Risk factors remain substantially unchanged.</p>
</body></html>
"""

EIGHT_K_HTML = """
<html><body>
<h1>ITEM 2.02 RESULTS OF OPERATIONS AND FINANCIAL CONDITION</h1>
<p>Example Corp announced quarterly operating results.</p>
<h1>ITEM 9.01 FINANCIAL STATEMENTS AND EXHIBITS</h1>
<p>An earnings release is furnished as Exhibit 99.1.</p>
</body></html>
"""

SIX_K_HTML = """
<html><body>
<h1>REPORT OF FOREIGN PRIVATE ISSUER</h1>
<p>Example Foreign Issuer reports quarterly operating results.</p>
</body></html>
"""


def _press_release_attachment() -> Attachment:
    return Attachment(
        sequence_number="2",
        description="QUARTERLY EARNINGS RELEASE",
        document="earnings-release.htm",
        ixbrl=False,
        path="/Archives/local/earnings-release.htm",
        document_type="EX-99.1",
        size=128,
    )


@dataclass
class _FrozenFiling:
    form: str
    source_html: str
    attachments: Attachments

    company: str = "Example Corp"
    cik: int = 1
    filing_date: str = "2024-03-01"
    accession_no: str = "0000000001-24-000001"
    period_of_report: str = "2023-12-31"

    def html(self) -> str:
        return self.source_html

    def text(self) -> str:
        return parse_html(
            self.source_html,
            ParserConfig(form=self.form),
        ).text()

    def xbrl(self):
        return None

    @property
    def exhibits(self):
        return self.attachments.exhibits


def _filing(form: str, source_html: str) -> _FrozenFiling:
    release = _press_release_attachment()
    attachments = Attachments(
        document_files=[release],
        data_files=[],
        primary_documents=[],
    )
    return _FrozenFiling(form, source_html, attachments)


class _FrozenStatement:
    def __init__(self, title: str, text: str, html: str | None = None):
        self.role_or_type = title
        self._text = text
        self._html = html or f"<p>{text}</p>"

    def text(self, raw_html: bool = False) -> str:
        return self._html if raw_html else self._text

    def render(self):
        return SimpleNamespace(title=self.role_or_type)


def _notes() -> Notes:
    debt_table = _FrozenStatement(
        "Debt Maturities (Tables)",
        "Debt maturities by year.",
    )
    debt_policy = _FrozenStatement(
        "Debt Accounting Policy (Policies)",
        "Debt is measured at amortized cost.",
    )
    return Notes(
        [
            Note(
                1,
                "Debt",
                "Debt",
                "local:debt",
                statement=_FrozenStatement(
                    "Debt",
                    "Long-term debt maturities extend through 2030.",
                ),
                tables=[debt_table],
                policies=[debt_policy],
            ),
            Note(
                2,
                "Leases",
                "Leases",
                "local:leases",
                statement=_FrozenStatement(
                    "Leases",
                    "Operating lease obligations include office facilities.",
                ),
            ),
            Note(
                3,
                "Revenue Recognition",
                "Revenue Recognition",
                "local:revenue",
                statement=_FrozenStatement(
                    "Revenue Recognition",
                    "Revenue is recognized when control transfers.",
                ),
            ),
            Note(
                4,
                "Commitments and Contingencies",
                "Commitments and Contingencies",
                "local:contingencies",
                statement=_FrozenStatement(
                    "Commitments and Contingencies",
                    "Legal contingencies are evaluated each reporting period.",
                ),
            ),
        ],
        entity_name="Example Corp",
        form="10-K",
        period="2023-12-31",
    )


def test_native_tenk_sections_markdown_and_search() -> None:
    report = TenK(_filing("10-K", TEN_K_HTML))

    assert "analytical systems" in report.business
    assert "supply-chain" in report.risk_factors
    assert "subscription demand" in report.management_discussion
    assert "ITEM 1. BUSINESS" in report.document.to_markdown()
    assert report.document.search("subscription demand")
    # This synthetic fixture has no SEC anchor navigation, so the dedicated
    # anchor-based API is exercised but honestly remains fixture-inconclusive.
    assert report.document.get_sec_section("Item 1") is None


def test_native_tenq_and_current_report_item_access() -> None:
    tenq = TenQ(_filing("10-Q", TEN_Q_HTML))
    current = CurrentReport(_filing("8-K", EIGHT_K_HTML))

    assert "Quarterly revenue" in tenq.get("Item 2")
    assert current.items == ["Item 2.02", "Item 9.01"]
    assert "quarterly operating results" in current.get("Item 2.02")
    assert current.get_exhibits("EX-99")


def test_native_sixk_attachments_exhibits_and_press_release_selection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        Attachment,
        "download",
        lambda _self: "<html><body>Quarterly operating results.</body></html>",
    )
    report = SixK(_filing("6-K", SIX_K_HTML))

    assert "Quarterly operating results" in report.text()
    assert [item.document_type for item in report.exhibits] == ["EX-99.1"]
    assert report.press_releases is not None
    assert len(report.press_releases) == 1


def test_native_notes_text_tables_policies_and_topic_search() -> None:
    notes = _notes()
    debt = notes.search("debt")[0]

    assert debt.text.startswith("Long-term debt")
    assert debt.has_tables
    assert debt.tables[0].text() == "Debt maturities by year."
    assert debt.policies[0].text() == "Debt is measured at amortized cost."
    assert "maturities" in debt.to_context(detail="full")
    assert len(notes.grep("maturities")) == 1
    assert notes.search("leases")[0].short_name == "Leases"
    assert notes.search("revenue")[0].short_name == "Revenue Recognition"
    assert notes.search("contingencies")[0].number == 4
    assert notes.with_tables == [debt]


def test_remaining_typed_report_and_xbrl_interfaces_are_present() -> None:
    # No local 20-F, 40-F, or parsed XBRL filing fixture is available. These
    # assertions intentionally prove only native interface presence; the audit
    # report classifies their content proof as fixture-not-available.
    assert hasattr(TwentyF, "business")
    assert hasattr(TwentyF, "risk_factors")
    assert hasattr(TwentyF, "management_discussion")
    assert hasattr(FortyF, "business")
    assert hasattr(FortyF, "risk_factors")
    for name in (
        "document",
        "text",
        "markdown",
        "parse",
        "search",
        "grep",
        "attachments",
        "exhibits",
    ):
        assert hasattr(Filing, name)
    assert hasattr(CurrentReport, "press_releases")

    from edgar.xbrl import XBRL

    assert hasattr(XBRL, "notes")
    assert hasattr(XBRL, "disclosures")
