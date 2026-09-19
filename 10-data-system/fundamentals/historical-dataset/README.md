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
superset, not an instruction to persist every numeric XBRL fact. The bounded
32-accession sample and a metadata-only 711-CIK EntityFacts pass measure the
selective fact/accession population and enforce the 176 GiB persistent / 192
GiB peak storage gate before any broad acquisition.

Source storage is remote-first. Ordinary SEC filing bytes are an EdgarTools-
managed or bounded build cache, not a permanent dataset surface. AQ seals the
source identity, URL, byte count and SHA-256 with its structured PIT evidence;
the ordinary cache becomes evictable only after all derived output hashes have
sealed. Re-extraction must reacquire through SEC/EdgarTools and match that hash
exactly. DVC owns the structured evidence and build authority, not a complete
SEC source mirror.

The companion `aq_edgartools_full_build` module contains only deterministic
build accounting, sampling, checkpoint/hash validation and storage admission.
It does not contain a SEC client, form router, XBRL/statement parser, identity
engine, generic ETL framework, warehouse, or as-of implementation.
