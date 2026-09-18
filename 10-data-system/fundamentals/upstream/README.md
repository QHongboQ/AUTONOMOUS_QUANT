# P5 selected SEC upstream runtime

This directory records the minimal tracked authority for the isolated P5
fundamental-intelligence runtime. It does not vendor any upstream package,
Skill, SEC filing, credential, or private evidence.

## Ownership

| Surface | Owner |
|---|---|
| Raw filing/accession/document/XBRL authority | SEC EDGAR upstream |
| Standardized SEC statement gateway | OpenBB SEC upstream leaf |
| Filing, document, XBRL, financial and context APIs | EdgarTools upstream |
| PIT admission and evidence identity | AQ policy only |

AQ does not own an SEC fetcher, HTTP client, XBRL parser, filing parser, RAG
engine, vector database, or fundamental engine.

## Runtime

```text
RUNTIME = /home/zhou/AQ_ENVS/p5-fundamental-intelligence
PYTHON = 3.14.7
OPENBB_CORE = 1.6.13
OPENBB_SEC = 1.6.7
EDGARTOOLS = 5.58.0
PIP_CHECK = PASS
```

`requirements.lock` contains only the selected top-level package pins. The
complete transitive freeze and installed-distribution hashes remain private at
`D:/AQ_DATA/P5/selected-upstream-deployment-001/`.

## PIT boundary

OpenBB `pit_mode` is useful but only partial. It is not standalone historical
availability authority. A structured value is inadmissible unless it can be
joined to an SEC accession and a verified SEC acceptance timestamp (or the raw
submission acceptance timestamp). Missing acceptance time fails closed.

Original filings, amendments, and later comparative restatements remain
separate vintages. No later value is backfilled into an earlier date.

## Skill

The untouched EdgarTools Skill is exported only to the private evidence root.
No global Skill installation and no repository copy exists. Its identity and
deployment path are frozen in `skill-deployment-authority.json`.

Live SEC access is intentionally blocked until the owner configures a
meaningful local `EDGAR_IDENTITY`. The value must never enter Git or evidence.
