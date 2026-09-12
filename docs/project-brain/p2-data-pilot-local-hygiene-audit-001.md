# P2 Data Pilot Local Hygiene Audit 001

## Status and authority

```text
TASK = AUTONOMOUS-QUANT-P2-DATA-PILOT-LOCAL-HYGIENE-AUDIT-001
AUDIT_DATE = 2026-09-12
BASE_MAIN = 142022b8400b8653662f5e996d4f03533d02cdbf
P2_DATA_PILOT_LOCAL_HYGIENE_AUDIT = COMPLETE
FINAL_CLASSIFICATION = PASS_WITH_DEFERRED_RETENTION
NO_DELETION_PERFORMED = YES
CLEANUP_REQUIRES_EXPLICIT_USER_AUTHORIZATION = YES
```

This was an inventory and classification audit only. No local artifact,
credential, environment, branch, or worktree was deleted, moved, modified,
archived, compressed, decrypted, or promoted. No provider or account was
called and no data content was printed.

## Ownership preamble

```text
CAPABILITY = P2 pilot local artifact hygiene and retention adjudication
UPSTREAM_OWNER = DVC for durable accepted dataset-version mechanics;
                 AQ for project-specific retention, credential, and evidence policy
OWNERSHIP_MODE = UPSTREAM_LEAF + AQ_OWNED_POLICY
UPSTREAM_ALREADY_DEPLOYED = YES_PARTIAL
AQ_IMPLEMENTATION_ALLOWED = YES
AQ_ALLOWED_SCOPE = audit, policy, retention classification, evidence inventory,
                   cleanup authorization boundary
CUSTOM_ENGINE_REQUIRED = NO
CUSTOM_ENGINE_JUSTIFICATION = N/A
```

Preserved authority:

```text
QUANTIACS_PROVIDER_RIGHTS_CONFIRMATION = REQUIRED_BEFORE_DURABLE_RETENTION
REVISION_SEMANTICS = OBSERVED_REPEATABLE_NOT_VENDOR_VERSIONED
PRIVATE_DVC_RETENTION = BLOCKED_PENDING_PROVIDER_CONFIRMATION
QUANTIACS_ROLE = PRIMARY_CANDIDATE
```

## Bounded scope and counting rule

Six filesystem scopes were inspected:

1. `D:\AQ_DATA\P2\quantiacs-free-data-pilot-001`
2. `D:\AQ_DATA\P2\quantiacs-free-data-pilot-correction-001`
3. `D:\AQ_ENVS\quantiacs-pilot-001`
4. `%LOCALAPPDATA%\AUTONOMOUS_QUANT\secrets`
5. `D:\API.txt` (existence check only)
6. `D:\AUTONOMOUS_QUANT` and its directly related Git refs/worktrees

`TOTAL_SCOPED_FILES` and byte totals below cover the two pilot trees, isolated
environment, and one encrypted secret file. Repository source, `.git` object
storage, unrelated existing DVC cache/data, and branch-ref bytes are excluded
so the recovery estimate measures only pilot-related local artifacts.

```text
SCOPED_PATHS_INSPECTED = 6
TOTAL_SCOPED_FILES = 10363
TOTAL_SCOPED_BYTES = 453915679
```

No other related artifact path was named in the selected authority or found in
the known locations. The correction cache is a directly related subdirectory
of scope 2 and is inventoried separately as a deletion unit.

## Pilot artifact inventory

### Original pilot

```text
PATH = D:\AQ_DATA\P2\quantiacs-free-data-pilot-001
TYPE = PRIVATE_PILOT_EVIDENCE_TREE
FILE_COUNT = 31
DIRECTORY_COUNT = 2
TOTAL_BYTES = 920657
EARLIEST_FILE_CREATION_UTC = 2026-09-12T04:33:26.9514917Z
LATEST_FILE_MODIFICATION_UTC = 2026-09-12T04:58:45.0385005Z
```

| Extension | Files | Bytes | Content class |
|---|---:|---:|---|
| `.bin` | 17 | 361111 | provider-returned decompressed response bytes |
| `.csv` | 1 | 18197 | derived identity translation table |
| `.json` | 9 | 145756 | request/provider/evidence metadata |
| `.jsonl` | 1 | 326572 | normalized provider rows |
| `.parquet` | 2 | 68535 | mapped table and Qlib handoff |
| `.txt` | 1 | 486 | package snapshot |

The manifest declares 30 artifacts (the manifest itself is the 31st file).
Every declared path exists and every declared SHA-256 matches. All 17 response
filenames contain their content hash and all 17 filename/hash pairs match.

Important current hashes:

```text
ARTIFACT_MANIFEST_SHA256 = 4744f1965f1ca51df5f3091b51b2d914f200fad730759e39c8dc1450c7a07199
MAPPED_PARQUET_SHA256 = 23f33d8c80d13e2a92aaba59fcae8c9e8efaa77efcccc1ee3ac79525c640b0b4
QLIB_INPUT_SHA256 = 08ea31c510830b64f96c27c675340fd377e05dd146ba06e9abe51e326bac6cdf
MANIFEST_HASH_MISMATCH = 0
RESPONSE_FILENAME_HASH_MISMATCH = 0
```

### Correction pilot

```text
PATH = D:\AQ_DATA\P2\quantiacs-free-data-pilot-correction-001
TYPE = PRIVATE_CORRECTION_EVIDENCE_TREE
FILE_COUNT = 37
DIRECTORY_COUNT = 2
TOTAL_BYTES = 424695
EARLIEST_FILE_CREATION_UTC = 2026-09-12T05:16:32.2315431Z
LATEST_FILE_MODIFICATION_UTC = 2026-09-12T05:27:29.7814037Z
```

| Extension | Files | Bytes | Content class |
|---|---:|---:|---|
| `.bin` | 6 | 218058 | provider-returned decompressed response bytes |
| `.gz` | 18 | 73824 | Toolbox transport cache args/value pairs |
| `.json` | 10 | 40246 | request/validation/hash evidence metadata |
| `.jsonl` | 1 | 27785 | correction provider rows |
| `.parquet` | 2 | 64782 | corrected mapped table and Qlib handoff |

The correction manifest declares the 18 non-cache evidence artifacts other
than the manifest itself. Every declared path exists and every declared hash
matches. All six response filename/hash pairs match.

```text
CORRECTED_PARQUET_SHA256 = 0622f86ee6e69ab2baa60b9333d87beb2acab7c0df88325eb1c0f56afaf94892
CORRECTED_PARQUET_HASH_MATCH = YES
CORRECTED_QLIB_INPUT_SHA256 = 667eb678a50ccf384a75a1be2936b4fc6070aeb485512b49826e8705145566f8
CORRECTED_QLIB_INPUT_HASH_MATCH = YES
MANIFEST_HASH_MISMATCH = 0
RESPONSE_FILENAME_HASH_MISMATCH = 0
```

The recorded original-pilot document hash is calculated over canonical LF Git
content. The Windows worktree uses CRLF because `core.autocrlf=true`:

```text
RECORDED_ORIGINAL_PILOT_DOCUMENT_SHA256 = dd8c5cbd827d5b0cf1b47d13ba96d3788d5a969cfe181a5aeda61527464ccb91
LF_NORMALIZED_WORKTREE_SHA256 = dd8c5cbd827d5b0cf1b47d13ba96d3788d5a969cfe181a5aeda61527464ccb91
RAW_CRLF_WORKTREE_SHA256 = f79bf691c4c74d38b5aa3a9a8b1c9b384a18243ccf19dccddaf390e47a68281a
CANONICAL_HASH_MATCH = YES
MAIN_AND_ORIGINAL_BRANCH_GIT_BLOB_MATCH = YES
```

This is a line-ending representation difference, not an evidence-integrity
failure. No historical pilot or correction document was rewritten.

## Secret and credential hygiene

Only metadata and ACLs were inspected. The DPAPI file was not decrypted or
printed.

```text
DPAPI_SECRET = %LOCALAPPDATA%\AUTONOMOUS_QUANT\secrets\quantiacs-api-key.dpapi
DPAPI_SECRET_EXISTS = YES
DPAPI_FILE_BYTES = 588
WRAPPER_CLASSIFICATION = ESTABLISHED_DPAPI_WRAPPER_NOT_PLAINTEXT
ACL = CURRENT_USER_AND_SYSTEM_FULL_CONTROL_ONLY
PLAINTEXT_SOURCE_D_API_TXT_EXISTS = NO
SCOPED_ENV_FILE_COUNT = 0
TEXT_FILES_SCANNED_FOR_STRONG_CREDENTIAL_PATTERNS = 120
CREDENTIAL_PATTERN_MATCHED_FILE_COUNT = 0
PRIOR_EXACT_SECRET_LEAK_CHECK = PASS
CREDENTIAL_HYGIENE = PASS
```

The prior exact-value leak evidence reports zero matches without recording the
credential value or hash. Current filename and strong-pattern checks found no
plaintext credential in either pilot tree or tracked repository text. No
secret content was used to perform this audit.

## Isolated environment

```text
PATH = D:\AQ_ENVS\quantiacs-pilot-001
EXISTS = YES
FILE_COUNT = 10294
DIRECTORY_COUNT = 1186
TOTAL_BYTES = 452569739
PYTHON = 3.12.14
UV = 0.12.9
PACKAGE_COUNT = 27
PACKAGE_CHECK = PASS
QNT = 0.0.507
NUMPY = 2.2.6
PANDAS = 2.2.3
XARRAY = 2025.12.0
SCIPY = 1.18.1
```

No market-data, provider-response, Parquet, JSONL, debug, or trace artifact was
found outside ordinary environment packages. `CACHEDIR.TAG` is ordinary
environment metadata. Quantiacs remains a primary candidate, so retaining the
environment until the gap-fill authority and provider-rights decisions are
complete avoids needless recreation.

## Repository hygiene

Safe Git metadata inspection found:

```text
TRACKED_FILE_COUNT = 152
TRACKED_MARKET_DATA = NO
TRACKED_CREDENTIAL = NO
UNTRACKED_FILE_COUNT = 0
UNTRACKED_SENSITIVE_ARTIFACT = NO
```

Nineteen ignored entries exist: ordinary DVC and Ruff cache/control files plus
the pre-existing PIT-universe DVC dataset (`episodes.jsonl` and
`snapshot.json`). They are unrelated to the Quantiacs pilot, were not opened or
modified, and are excluded from this retention plan. No pilot response,
Parquet, cache, environment, `.env`, or DPAPI file is present in the repository
working tree.

## Branch and worktree hygiene

Squash-merge safety was checked by comparing the relevant document Git blobs
to `origin/main`, not by relying on branch ancestry. All four required blobs
match authoritative main exactly:

| Resource | Location | Evidence in main | Classification |
|---|---|---|---|
| Free-route audit branch | local `agent/p2-certified-data-free-route-quantiacs-audit-001` at `3dd9aab3eec68601b5b75f8155e20446500587de` | exact document blob match | `DELETE_CANDIDATE` |
| Original pilot branch | local and remote `agent/p2-quantiacs-free-data-pilot-001` at `2834a484ad0c4fb3bab5a3cccd7d201a612ae8d1` | exact document blob match | `DELETE_CANDIDATE` |
| Correction branch | local `agent/p2-quantiacs-free-data-pilot-correction-001` at `83ed7615dacc0431e68a7d7d02f95fd8e5b47802` | exact document blob match | `DELETE_CANDIDATE` |
| Upstream-substitution branch | local `agent/p2-data-upstream-substitution-audit-001` at `45628166d519dedda45962e94fbb4d83c4aa5505` | exact document blob match | `DELETE_CANDIDATE` |
| Current audit worktree | `D:\AUTONOMOUS_QUANT` | active task worktree | `KEEP` |

No old related worktree exists. Branch deletion is not authorized by this
audit. The original `FAIL_FREE_ROUTE_COVERAGE` result and correction
`PASS_TECHNICAL_PILOT_FREE_GAP_FILL_REQUIRED` supersession remain represented
in main.

## A. KEEP

| Path / resource | Type | Approx bytes | Reason | Dependency | Risk if deleted | Risk if retained | Recommended action |
|---|---|---:|---|---|---|---|---|
| `D:\AQ_ENVS\quantiacs-pilot-001` | isolated Python environment | 452569739 | likely reused for bounded Quantiacs authority work | future gap-fill/rights audits | recreation and dependency drift | 432 MiB disk use | keep until those audits complete |
| `%LOCALAPPDATA%\AUTONOMOUS_QUANT\secrets\quantiacs-api-key.dpapi` | encrypted credential | 588 | Quantiacs remains a primary candidate | future authorized provider work | credential must be re-established | small local secret attack surface, mitigated by DPAPI/ACL | keep; do not decrypt |
| Original pilot evidence metadata: `acquisition_summary.json`, `artifact-manifest.json`, `credential-leak-check.json`, `metadata_probe_manifest.json`, `package-freeze.txt`, `provider_request_manifest.json`, `provider-confirmation-questions.json`, `qlib_handoff_summary.json`, `validation_summary.json` | metadata/evidence set | 28995 | supports verification without reopening data payloads | pending rights/evidence adjudication | weakens audit trail | negligible storage | keep |
| Correction evidence metadata: `artifact-manifest.json`, `corrected_qlib_handoff_summary.json`, `correction_query_summary.json`, `correction_validation_summary.json`, `credential-leak-check.json`, both `original_pilot_artifact_hashes_*.json`, `provider_request_manifest.json`, `raw_response_inspection.json` | metadata/evidence set | 39031 | proves correction and preservation state | pending rights/evidence adjudication | weakens audit trail | negligible storage | keep |
| `D:\AUTONOMOUS_QUANT` current worktree | active repository worktree | excluded | required for current work | current task | disrupts repository | none material | keep |

## B. DELETE_CANDIDATE

| Path / resource | Type | Approx bytes | Reason | Dependency | Risk if deleted | Risk if retained | Recommended action |
|---|---|---:|---|---|---|---|---|
| `D:\AQ_DATA\P2\quantiacs-free-data-pilot-correction-001\cache` | redundant Toolbox transport cache | 73824 | authoritative response files, request metadata, and hashes exist separately; future execution does not depend on this cache | none after explicit approval | loses cached args/value copies but not retained evidence | redundant provider bytes remain locally | delete exact directory only after authorization |
| local `agent/p2-certified-data-free-route-quantiacs-audit-001` | Git branch ref | not material | exact audit document exists in main | none | loses convenient historical ref | branch clutter | delete exact ref only after authorization |
| local and remote `agent/p2-quantiacs-free-data-pilot-001` | Git branch refs | not material | exact pilot document exists in main | none | loses convenient historical refs | branch clutter | delete exact refs only after authorization |
| local `agent/p2-quantiacs-free-data-pilot-correction-001` | Git branch ref | not material | exact correction document exists in main | none | loses convenient historical ref | branch clutter | delete exact ref only after authorization |
| local `agent/p2-data-upstream-substitution-audit-001` | Git branch ref | not material | exact audit document exists in main | none | loses convenient historical ref | branch clutter | delete exact ref only after authorization |

The only filesystem deletion unit authorized for consideration is the exact
cache directory shown above. No wildcard or parent-directory deletion is safe.
Branch refs are separate future Git actions and are not filesystem cleanup
commands.

## C. DEFER

| Path / resource | Type | Approx bytes | Reason | Dependency | Risk if deleted | Risk if retained | Recommended action |
|---|---|---:|---|---|---|---|---|
| `D:\AQ_DATA\P2\quantiacs-free-data-pilot-001\responses` | provider response bytes | 361111 | retention rights and evidence disposition unresolved | provider confirmation | destroys primary pilot payload evidence | unresolved rights exposure | defer without copying/promoting |
| original `id-translation.csv`, `provider_asset_metadata.json`, `normalized_provider_rows.jsonl` | provider/derived tables | 462016 | derived from provider payload and still evidentiary | provider confirmation | loses mapping evidence | unresolved rights exposure | defer |
| original `normalized_mapped_pilot.parquet`, `qlib_pilot_input.parquet` | derived Parquet / Qlib handoff | 68535 | historical pilot and handoff evidence | provider confirmation | loses reproducible pilot table | unresolved rights exposure | defer; no DVC promotion |
| `D:\AQ_DATA\P2\quantiacs-free-data-pilot-correction-001\responses` | provider response bytes | 218058 | correction payload evidence; rights unresolved | provider confirmation | loses correction evidence | unresolved rights exposure | defer without copying/promoting |
| correction `generic_identity_candidates.json`, `correction_provider_rows.jsonl` | provider/derived tables | 29000 | evidence for correction outcome | provider confirmation | loses row-level correction evidence | unresolved rights exposure | defer |
| correction `corrected_mapped_pilot.parquet`, `corrected_qlib_input.parquet` | derived Parquet / Qlib handoff | 64782 | verified corrected artifacts | provider confirmation | loses corrected handoff reproducibility | unresolved rights exposure | defer; no DVC promotion |

## Disposition boundaries

```text
QUANTIACS_RAW_RESPONSE_DISPOSITION = DEFER
QUANTIACS_DERIVED_PARQUET_DISPOSITION = DEFER
QUANTIACS_QLIB_HANDOFF_DISPOSITION = DEFER
QUANTIACS_DPAPI_SECRET_DISPOSITION = KEEP
QUANTIACS_ENV_DISPOSITION = KEEP
ONE_OFF_SCRIPTS_DISPOSITION = KEEP
ONE_OFF_SCRIPTS_FOUND = 0
OLD_PILOT_BRANCHES_DISPOSITION = DELETE_CANDIDATE
OLD_WORKTREES_DISPOSITION = KEEP
OLD_WORKTREES_FOUND = 0
```

`KEEP` for one-off scripts and old worktrees means there is no such resource to
delete; it does not invent a retained artifact.

## Space-recovery estimate

```text
TOTAL_KEEP_BYTES = 452638353
TOTAL_DELETE_CANDIDATE_BYTES = 73824
TOTAL_DEFER_BYTES = 1203502
POTENTIAL_IMMEDIATE_RECOVERY_BYTES = 73824
POTENTIAL_LATER_RECOVERY_BYTES = 1203502
CLASSIFICATION_TOTAL_BYTES = 453915679
```

The immediate recovery is only about 72 KiB and is not operationally urgent.
The later figure is a maximum contingent on provider-rights and evidence
decisions; this audit does not recommend deleting all deferred evidence.

## Cleanup authorization boundary and next state

Because an exact deletion candidate exists, local hygiene is audited but not
closed by deletion. A later user authorization may delete only explicitly
approved units; it must not delete either pilot parent directory, the
environment, the DPAPI secret, or any DEFER artifact by implication.

```text
EVIDENCE_INTEGRITY = PASS
P2_DATA_PILOT_LOCAL_HYGIENE_AUDIT = COMPLETE
LOCAL_HYGIENE_CLEANUP_REQUIRED = YES
CURRENT_NEXT = P2_DATA_PILOT_LOCAL_HYGIENE_CLEANUP_AUTHORIZATION
AFTER_LOCAL_HYGIENE = P2_FREE_DATA_GAP_FILL_AUTHORITY_AUDIT
NO_DELETION_PERFORMED = YES
CLEANUP_REQUIRES_EXPLICIT_USER_AUTHORIZATION = YES
```

## Non-actions

```text
PROVIDER_CALLS = NONE
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
MODEL_TRAINING = NO
QLIB_INGESTION = NO
DVC_PROMOTION = NO
SECRET_DECRYPTED = NO
LOCAL_ARTIFACT_MODIFIED = NO
PUSHED = NO
PR_CREATED = NO
MERGED = NO
```
