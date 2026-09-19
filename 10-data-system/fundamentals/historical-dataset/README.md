# P5 Hybrid Historical Fundamental Dataset

This leaf owns only the thin AQ policy needed to project already-admitted,
accession-bound fundamental evidence onto date-valid PIT sessions.

Upstream ownership remains fixed:

- SEC FSDS and secfsdstools own the bulk candidate catalog;
- EdgarTools owns exact filing/XBRL admission and standardization semantics;
- exchange_calendars owns XNYS sessions;
- pandas owns the as-of join primitive;
- PyArrow owns Parquet storage;
- DVC owns artifact reproducibility;
- Qlib owns research dataset consumption.

The module does not download SEC data, parse XBRL, standardize statements,
resolve securities, index FSDS, or implement a generic ETL/as-of framework.
