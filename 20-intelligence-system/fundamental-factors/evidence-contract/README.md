# FundamentalEvidenceV1

`FundamentalEvidenceV1` is the smallest AQ-owned point-in-time admission
contract for structured SEC fundamentals. One record means one numeric XBRL
fact, from one SEC accession, for one entity, with one provable market
availability time. It is a domain contract, not a fetcher, parser, statement
normalizer, warehouse, or generic financial-data engine.

## Ownership

- SEC EDGAR is the authoritative US filing and acceptance-time source.
- EdgarTools owns filing discovery/retrieval, accession-bound documents, XBRL,
  statements, sections, and tables.
- AQ owns only evidence admission and later factor semantics.
- OpenBB SEC is supplementary and non-authoritative. A standardized OpenBB
  value without SEC accession, acceptance datetime, and accession-bound source
  hash is rejected.

## Immutable identity

The contract has exactly eight top-level fields:

`schema_version`, `evidence_id`, `entity`, `filing`, `availability`, `source`,
`fact`, and `upstream`.

`evidence_id` is `sha256:` followed by SHA-256 over Python `rfc8785` 0.1.4 JCS
bytes for all seven authoritative non-ID fields. Optional fields are serialized
as explicit JSON `null`, so omitted and explicit-null inputs produce the same
validated semantics. Dimensions participate in the identity and cannot be
collapsed.

`fact.value` is an exact canonical decimal string: base-10 fixed notation, no
exponent, no leading or trailing redundant zeros, no `-0`, no NaN/Infinity,
and no rounding. V1 intentionally admits numeric facts only.

## Fail-closed rules

- `first_available_at` must equal the timezone-aware UTC SEC
  `acceptance_datetime`.
- Accession and accession-bound source SHA-256 are required.
- Filing date, report-period end, CIK, ticker text, or current aggregate Company
  Facts cannot substitute for accession plus acceptance time.
- Original and amended accessions are distinct vintages. Later amendments or
  comparative restatements are never projected backward.
- A fact has exactly one instant context or one duration context. Upstream
  context and dimensions are preserved when available.
- Missing optional metadata remains `null`; it is never fabricated.

## Storage boundary

The contract retains compact identity, provenance, selected fact, and selected
context metadata. It does not require a permanent SEC mirror or retention of
every attachment. Source bytes may be replaced by deterministic re-download
only while the exact accession-bound document remains available and its bytes
recompute to `source_document_sha256`; otherwise the evidence fails closed.

## Thin materialization boundary

`aq_fundamental_evidence.materialize.materialize_edgartools_fact` is a pure
projection from an already-parsed EdgarTools `Filing` plus fact mapping into
this contract. It performs no network access, filing/XBRL parsing, taxonomy
normalization, statement reconstruction, storage, or scheduling. Deterministic
sample and concept selection belong to bounded private evidence work, not this
module.
