# P5 Fundamental Intelligence Selected Upstream Deployment 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-FUNDAMENTAL-INTELLIGENCE-SELECTED-UPSTREAM-DEPLOYMENT-001
SELECTED_RUNTIME_CREATED = YES
P5_SELECTED_UPSTREAM_DEPLOYMENT = PASS
P5_RUNTIME = ISOLATED
CURRENT_DEVELOPMENT_NEXT = P5_SEC_LIVE_IDENTITY_AND_PIT_BINDING_POC_001_PENDING_LOCAL_IDENTITY
FINAL_CLASSIFICATION = PASS
```

This task deployed and qualified only the upstream stack selected by the prior
fit audit. It did not add an AQ crawler, parser, RAG system, vector database,
fundamental engine, factor, model, backtest, or investment conclusion.

The operational authority remains unchanged:

```text
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Isolated runtime

```text
P5_RUNTIME_PATH = /home/zhou/AQ_ENVS/p5-fundamental-intelligence
PYTHON_VERSION = 3.14.7
OPENBB_CORE_VERSION = 1.6.13
OPENBB_SEC_VERSION = 1.6.7
EDGARTOOLS_VERSION = 5.58.0
PIP_CHECK = PASS
RUNTIME_DISK_FOOTPRINT_BYTES = 424487352
AUTHORITATIVE_ENV_MUTATION = NO
```

CPython 3.14.7 was the newest stable interpreter available through `uv` and is
jointly supported by the exact selected package metadata. CPython 3.15 was
release-candidate only and was not selected.

The complete transitive freeze, distribution metadata hashes, RECORD hashes,
and public entry-module hashes are sealed privately. The audited EdgarTools
source commit remains source-review authority; no byte-identity claim is made
between that Git checkout and the installed PyPI distribution.

The permanent runtime excludes all audit-only challengers:

```text
SEC_PARSER_PRESENT = NO
ARELLE_PRESENT = NO
SEC_EDGAR_DOWNLOADER_PRESENT = NO
```

## Runtime health

OpenBB Core and OpenBB SEC import successfully. The `sec` Provider registers
its public filing, statement, growth, mapping, and related fetchers. The audited
income statement, balance sheet, cash-flow, and income-growth query surfaces
retain `pit_mode`.

```text
OPENBB_SEC_IMPORT = PASS
OPENBB_SEC_PROVIDER_REGISTRATION = PASS
OPENBB_PIT_MODE = PARTIAL
OPENBB_STANDALONE_PIT_AUTHORITY = NO
```

EdgarTools exposes the selected Company, Filings, filing-object, amendment,
attachment, HTML/text, XBRL, report-object, financial-statement, and
`to_context` surfaces. Its upstream XBRL schema and Skill export tests were run
against the installed distribution and passed `45/45` using only local copied
upstream fixtures. Temporary test dependencies were then retired and the
permanent runtime again passed `pip check`.

A bounded offline replay also reproduced:

- Apple 2010 10-K accession `0001193125-10-238044`: 1,377 XBRL facts and 74
  revenue-matching facts;
- 2021 8-K accession `0000887919-21-000012`: 6,524 text characters, 119
  blocks, 31 chunks, and raw HTML SHA-256
  `506cca6f069ce64b3d8f7199f82be60cfdbb118b5ba8d38f44d20c40cd69ce44`.

## Upstream Skill

EdgarTools exported its official Skill through `edgar.ai.install_skill` with a
private copy and through `edgar.ai.package_skill`. Nothing was installed in a
global Skill directory or copied into repository source.

```text
SKILL_STAGING_PATH = D:/AQ_DATA/P5/selected-upstream-deployment-001/skills/edgartools
SKILL_FILE_COUNT = 22
SKILL_MD_SHA256 = 65ff350a67cbb8ff9ca0dc6038aa9b6856fe3855e9e4b008bfe81124617d4791
SKILL_PACKAGE_SHA256 = 63e29e5794ec577817199cf6551c9acd83f988146da7bf20d07d9b74891eaf6c
SKILL_CONTENT_MANIFEST_SHA256 = 08b0a196d4e31ce6317753493a3699205bad67029b50cfdfcb9968a07bb40549
UPSTREAM_SKILL_MODIFIED = NO
AGENT_SKILL_CONSUMPTION = PASS
```

All three identities and the complete 22-file content manifest match the prior
audit. The agent consulted upstream `SKILL.md` and its relative reports,
financials, and XBRL guidance, then answered a bounded filing question using
the local 8-K fixture while preserving its accession and hash. No AQ rewrite
was used.

## SEC and PIT boundaries

`EDGAR_IDENTITY` was absent in both Windows and WSL process environments. Its
value was neither fabricated nor logged, so no live SEC request occurred.

```text
P5_SEC_LIVE_IDENTITY = NOT_CONFIGURED
SEC_LIVE_NETWORK_TEST = BLOCKED_IDENTITY_NOT_CONFIGURED
SEC_NETWORK_REQUEST_COUNT = 0
FIRST_AVAILABLE_AT_POLICY = SEC_ACCEPTANCE_DATETIME_FAIL_CLOSED
RESTATEMENT_HANDLING = FAIL_CLOSED_AND_EXPLICIT
```

Filing date and report-period end never substitute for availability time.
Original filings, amendments, and later comparative restatements remain
separate accession-bound vintages. OpenBB standardized values require an
external SEC accession and acceptance-time join before admission.

## No implementation creep

```text
AQ_SEC_FETCHER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_PARSER = NO
AQ_FILING_PARSER = NO
AQ_RAG_ENGINE = NO
AQ_VECTOR_DB = NO
AQ_FUNDAMENTAL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_BACKTEST = NO
```

Private deployment evidence is stored under
`D:/AQ_DATA/P5/selected-upstream-deployment-001/`.

```text
RUNTIME_IDENTITY_SHA256 = 9af9c7aee64f7f74ac3fe1529dce6082e2eb497e3d945510c67605fbb94f7804
PRIVATE_REPORT = D:/AQ_DATA/P5/selected-upstream-deployment-001/deployment_summary.json
PRIVATE_REPORT_SHA256 = 04bdf3b384f04a6cae991f53c988b0c774207397c0d5c48b23c8d507099cc8b8
```
