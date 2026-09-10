"""Semantic, fail-closed parser for frozen S&P 500 Wikipedia source evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
import re
import unicodedata

from .canonical import sha256


class SchemaError(ValueError):
    pass


_SPACE = re.compile(r"\s+")
_FOOTNOTE = re.compile(r"\[[^\]]+\]")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def clean(value: str) -> str:
    return _SPACE.sub(" ", _FOOTNOTE.sub("", value).replace("\xa0", " ")).strip()


def semantic(value: str) -> str:
    return _NON_ALNUM.sub(" ", unicodedata.normalize("NFKC", clean(value)).casefold()).strip()


def parse_date(value: str) -> date:
    value = clean(value)
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise SchemaError(f"unparseable source effective date: {value!r}")


@dataclass(frozen=True)
class Cell:
    text: str
    header: bool
    rowspan: int
    colspan: int
    hrefs: tuple[str, ...]


@dataclass(frozen=True)
class CurrentConstituent:
    symbol: str
    security: str
    date_added: str


@dataclass(frozen=True)
class ChangeEvent:
    effective_date: str
    added_symbol: str | None
    added_security: str | None
    removed_symbol: str | None
    removed_security: str | None
    source_row: int
    source_links: tuple[str, ...]


@dataclass(frozen=True)
class ParsedSource:
    current_constituents: tuple[CurrentConstituent, ...]
    changes: tuple[ChangeEvent, ...]
    current_schema: dict[str, object]
    change_schema: dict[str, object]


def _positive(value: str | None) -> int:
    try:
        return max(1, int(value or "1"))
    except ValueError:
        return 1


class TableCapture(HTMLParser):
    """Small stdlib HTML table capture retaining merged-heading information."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[Cell]]] = []
        self._tables: list[list[list[Cell]]] = []
        self._row: list[Cell] | None = None
        self._cell: dict[str, object] | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            table: list[list[Cell]] = []
            self.tables.append(table)
            self._tables.append(table)
        elif tag == "tr" and self._tables:
            self._row = []
        elif tag in {"th", "td"} and self._tables and self._row is not None:
            self._cell = {"text": [], "hrefs": [], "header": tag == "th", "rowspan": _positive(attrs.get("rowspan")), "colspan": _positive(attrs.get("colspan"))}
        elif tag == "a" and self._cell is not None and attrs.get("href"):
            self._cell["hrefs"].append(attrs["href"])

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"].append(data)

    def handle_endtag(self, tag):
        if tag in {"th", "td"} and self._cell is not None and self._row is not None:
            self._row.append(Cell(clean("".join(self._cell["text"])), bool(self._cell["header"]), int(self._cell["rowspan"]), int(self._cell["colspan"]), tuple(self._cell["hrefs"])))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._tables:
            self._tables[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._tables:
            self._tables.pop()


def _expand(rows: list[list[Cell]]) -> list[list[Cell]]:
    pending: dict[int, tuple[int, Cell]] = {}
    output: list[list[Cell]] = []
    for raw in rows:
        row: list[Cell] = []
        col = 0

        def occupy() -> None:
            nonlocal col
            while col in pending:
                remaining, cell = pending[col]
                row.append(cell)
                if remaining == 1:
                    del pending[col]
                else:
                    pending[col] = (remaining - 1, cell)
                col += 1

        occupy()
        for cell in raw:
            occupy()
            for offset in range(cell.colspan):
                row.append(cell)
                if cell.rowspan > 1:
                    pending[col + offset] = (cell.rowspan - 1, cell)
            col += cell.colspan
        occupy()
        output.append(row)
    return output


def _headers_and_rows(table: list[list[Cell]]) -> tuple[list[str], list[list[Cell]]]:
    rows = _expand(table)
    header_count = 0
    for row in rows:
        if any(cell.header for cell in row):
            header_count += 1
        else:
            break
    if not header_count:
        raise SchemaError("table has no heading row")
    headings = rows[:header_count]
    width = max(map(len, headings))
    output: list[str] = []
    for col in range(width):
        parts: list[str] = []
        for row in headings:
            if col < len(row):
                part = semantic(row[col].text)
                if part and (not parts or parts[-1] != part):
                    parts.append(part)
        output.append(" ".join(parts))
    return output, rows[header_count:]


def _one(headers: list[str], predicate, field: str) -> int:
    matches = [index for index, header in enumerate(headers) if predicate(header)]
    if len(matches) != 1:
        raise SchemaError(f"semantic field {field!r} is {'missing' if not matches else 'ambiguous'}: {headers!r}")
    return matches[0]


def _current_fields(headers: list[str]) -> dict[str, int]:
    return {"symbol": _one(headers, lambda h: h == "symbol", "Symbol"), "security": _one(headers, lambda h: h == "security", "Security"), "date_added": _one(headers, lambda h: h == "date added", "Date added")}


def _change_fields(headers: list[str]) -> dict[str, int]:
    def tick(prefix: str):
        return lambda h: prefix in h.split() and bool({"ticker", "symbol"} & set(h.split()))

    def company(prefix: str):
        return lambda h: prefix in h.split() and "security" in h.split()

    return {
        "date": _one(headers, lambda h: h == "date", "Date"),
        "added_symbol": _one(headers, tick("added"), "Added ticker"),
        "added_security": _one(headers, company("added"), "Added security"),
        "removed_symbol": _one(headers, tick("removed"), "Removed ticker"),
        "removed_security": _one(headers, company("removed"), "Removed security"),
    }


def _none_if_blank(value: str) -> str | None:
    value = clean(value).upper()
    return None if value in {"", "-", "—", "N/A", "NA"} else value


def _candidates(tables: list[list[list[Cell]]]):
    current = []
    changes = []
    for table in tables:
        try:
            headers, rows = _headers_and_rows(table)
        except SchemaError:
            continue
        try:
            current.append((headers, rows, _current_fields(headers)))
        except SchemaError:
            pass
        try:
            changes.append((headers, rows, _change_fields(headers)))
        except SchemaError:
            pass
    if len(current) != 1 or len(changes) != 1:
        raise SchemaError(f"expected exactly one current and one history table; current={len(current)} history={len(changes)}")
    return current[0], changes[0]


def parse_sp500_html(html: str) -> ParsedSource:
    capture = TableCapture()
    capture.feed(html)
    (ch, cr, cf), (hh, hr, hf) = _candidates(capture.tables)
    current: list[CurrentConstituent] = []
    for row in cr:
        if len(row) <= max(cf.values()):
            continue
        symbol = _none_if_blank(row[cf["symbol"]].text)
        security = clean(row[cf["security"]].text)
        if symbol and security:
            current.append(CurrentConstituent(symbol, security, clean(row[cf["date_added"]].text)))
    if not current or len({item.symbol for item in current}) != len(current):
        raise SchemaError("current table is empty or contains duplicate symbols")
    changes: list[ChangeEvent] = []
    for number, row in enumerate(hr, 1):
        if len(row) <= max(hf.values()):
            continue
        # Strictly parse the Date field. No positional fallback is permitted.
        effective = parse_date(row[hf["date"]].text).isoformat()
        source_cells = [row[i] for i in hf.values()]
        changes.append(ChangeEvent(effective, _none_if_blank(row[hf["added_symbol"]].text), clean(row[hf["added_security"]].text) or None, _none_if_blank(row[hf["removed_symbol"]].text), clean(row[hf["removed_security"]].text) or None, number, tuple(sorted({href for cell in source_cells for href in cell.hrefs}))))
    if not changes:
        raise SchemaError("change-history table is empty")
    current_schema = {"headers": ch, "fields": cf, "schema_fingerprint": sha256({"headers": ch, "fields": cf})}
    change_schema = {"headers": hh, "fields": hf, "schema_fingerprint": sha256({"headers": hh, "fields": hf})}
    return ParsedSource(tuple(current), tuple(changes), current_schema, change_schema)
