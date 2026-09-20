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

The module does not implement SEC transport, parse XBRL, standardize statements,
resolve securities, index FSDS, or implement a generic ETL/as-of framework.

`run_full_universe_preflight.py` is the bounded orchestration entry point for
the frozen EdgarTools-native full-universe build. Its selected production shape
starts from EdgarTools CompanyFacts/EntityFacts, applies only the frozen
StandardConcept surface, and derives the exact accession inventory before any
filing-source acquisition. EntityFacts is discovery evidence; acceptance time,
source identity/hash, and final fact admission still require accession-bound
EdgarTools filing/XBRL validation. Accession is the deduplication and recovery
unit.

The older 36,582-accession native filing inventory remains a diagnostic
superset, not an instruction to persist every numeric XBRL fact. The frozen
32-accession sample and completed metadata-only 711-CIK EntityFacts pass define
the selective 36,206-accession population. They are audit evidence and are not
reimplemented by the production entry point.

The corrected execution authority preserves all 36,206 discovered accessions
as 36,204 source-verifiable required accessions plus two immutable
`SOURCE_UNAVAILABLE_FOR_FINAL_PROVENANCE` accounting records. The latter cannot
become `FundamentalEvidenceV1`, receive a source hash, or name a replacement
accession. Four SEC transition forms (`10-KT`, `10-KT/A`, `10-QT`, and
`10-QT/A`) have one narrow admission leaf into the unchanged EdgarTools native
XBRL path. Their filed form is preserved, while fact period classes continue to
come only from native XBRL instant/duration semantics.

Source storage is remote-first. EdgarTools' native `XBRLAttachments` selection
defines the required instance/schema/linkbase asset set; the complete SGML
submission is not acquired merely to support numeric XBRL facts. AQ seals a
deterministic manifest of each native asset's SEC-relative identity, URL,
byte count, role, and SHA-256. Re-extraction must reacquire through
SEC/EdgarTools and match every asset and the manifest hash exactly. The
ordinary cache becomes evictable only after all derived output hashes seal.
DVC owns the structured evidence and build authority, not a SEC source mirror.

The companion `aq_edgartools_full_build` module contains only finite selection,
bounded batches, native-source manifest projection, minimal checkpoint/hash
validation, and failure accounting. Decimal admission and the concept
vocabulary remain in the existing evidence and hybrid-dataset authorities.
It does not contain a SEC client, form router, XBRL/statement parser, identity
engine, generic checkpoint framework, ETL framework, warehouse, or as-of
implementation.
