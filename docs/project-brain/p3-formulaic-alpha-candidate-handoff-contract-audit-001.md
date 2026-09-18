# P3 Formulaic Alpha Candidate Handoff Contract Audit 001

## Result

```text
P3_FORMULAIC_ALPHA_CANDIDATE_HANDOFF_CONTRACT_AUDIT = PASS
CANDIDATE_V1 = IMMUTABLE
CANDIDATE_V2 = IMMUTABLE_RDAGENT_LLM_SPECIFIC
RECOMMENDED_CONTRACT = P3_CANDIDATE_TO_P2_CONTRACT_V3
RECOMMENDED_TOP_LEVEL_FIELD_COUNT = 8
FORMULAIC_DVC_IDENTITY = ABSENT_REQUIRES_REPRODUCIBILITY_SEAL
CURRENT_P2_PROTOCOL_ELIGIBILITY = INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION
CURRENT_NEXT = P3_FORMULAIC_ALPHA_DVC_REPRODUCIBILITY_SEAL_001
```

This was a contract and evidence audit only. Candidate V1, Candidate V2, their
schemas, all existing Candidate IDs, P2 protocol authority, AlphaGen/Qlib
evidence, and runtime implementation remain unchanged. No Candidate V3 object
was materialized.

## V1/V2 specificity audit

The exact concrete-instance field matrix expands reused schema definitions at
each semantic path and counts object/array containers once. It contains 109
paths:

| Classification | Fields |
| --- | ---: |
| Generic candidate identity | 24 |
| RD-Agent-specific | 22 |
| LLM-specific | 26 |
| Qlib-generic | 8 |
| Dataset-generic | 16 |
| P2-policy-generic | 13 |
| Generic reusable total | 61 |

V1 requires `rdagent_research_identity`, three RD-Agent runtime identities,
the fixed `p3_rdagent_us_quant_research` DVC stage, the closed RD-Agent static
template family, and generated research code. V2 preserves every one of those
requirements and adds 26 concrete LLM identity paths. Those fields cannot be
truthfully populated by an AlphaGen run with no RD-Agent or LLM execution.
`NONE`, zero-call, `N/A`, and dummy-hash substitutions are prohibited.

The complete matrix is private evidence at
`D:/AQ_DATA/P3/formulaic-alpha-candidate-handoff-contract-audit-001/v1_v2_specificity_matrix.json`.

## Real AlphaGen evidence

All 17 expressions have exact expression identities, source/config/seed
provenance, frozen-manifest linkage, a `FINISHED` Qlib experiment/run identity,
a deterministic `run_config.json` identity, and a native prediction artifact.

```text
ALPHAGEN_SHA = 259687e8f316994426416c530a94842a2fe6405e
DISCOVERY_CONFIG = ALPHAGEN_MSE_LSTSQ_FAST_V1
DISCOVERY_SUMMARY_SHA256 = 5212564ed15b3fa15bde40f14b9fe9a067b725bc5dd472a6046af0013893523a
FROZEN_CANDIDATE_MANIFEST_SHA256 = de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145
QLIB_EVALUATION_SUMMARY_SHA256 = c077196473711ebcbd33e572cb4e3de5a07103dba9e7aa8f88f255a7acf9b6a0
QLIB_ARTIFACT_MANIFEST_V2_SHA256 = 4da1e39480f84c284a7bd7d01bdc921226b4752e1759aff82dbf2d576214e01f
QLIB_RECORDERS_FINISHED = 17
PREDICTION_ARTIFACTS = 17
```

The completed path did not persist serialized model artifacts or native
rendered Qlib YAML files; its 17 deterministic JSON run configurations are
present instead. It also lacks a complete formulaic runtime environment freeze
and any DVC stage/lock/output identity. These absences are recorded rather than
replaced with fabricated evidence.

## Research TEST and P2 boundary

```text
HISTORICAL_RESEARCH_TEST_ACCESSED = YES
ALPHAGEN_HISTORICAL_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
HISTORICAL_RESEARCH_TEST_ROWS_ACCESSED = 377938
SEALED_OOS_ACCESSED = NO
```

Historical TEST evidence cannot be relabelled as pristine OOS, but its use as
research evidence is not itself a certification failure. The current frozen P2
inventory contains only
`QLIB_LGBMODEL_RAGGEDALPHA158_TOPK30_NDROP3_V1`; it explicitly requires a new
protocol version for candidate-set expansion. The 17 AlphaGen expressions and
their LinearModel evaluations are therefore
`INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION`. This audit did not edit that policy.

## Recommended V3 boundary

The producer-neutral option is smaller than a parallel Formulaic-only contract
because it reuses the existing Qlib, dataset, artifact, and P2-policy surfaces.
It keeps exactly eight top-level fields, replacing only
`rdagent_research_identity` with a discriminated
`research_producer_identity` (`RD_AGENT` or `FORMULAIC_ALPHA`). For AlphaGen,
that branch binds the engine name, upstream SHA, exact expression, discovery
config and report, frozen candidate manifest, and origin/seed provenance.

The Formulaic runtime branch requires real AlphaGen/Qlib/config/environment
identity only. RD-Agent wheel/source, LiteLLM, Ollama, embedding, and LLM trace
fields are forbidden when those systems did not execute. A future RD-Agent V3
branch must retain V2's strict LLM/runtime requirements.

The artifact branch binds DVC identity, the actual Qlib execution-config
identity, and prediction identity. A serialized model identity is conditional
on the upstream Qlib execution actually persisting one. Formulaic expression
plus AlphaGen source/config provenance replaces RD-Agent generated-code and
static-template identity.

Each expression has its own Qlib recorder and prediction, so the cardinality is
`ONE_CANDIDATE_PER_EXPRESSION`. Candidate identity remains SHA-256 over RFC 8785
JCS of the seven non-ID top-level fields. Performance metrics remain outside
identity. No AQ canonicalizer or registry is authorized.

## Reproducibility gap and next task

No AlphaGen discovery/evaluation stage exists in `dvc.yaml` or `dvc.lock`.
The minimum next seal must bind the pinned AlphaGen/Qlib sources, AQ adapter,
frozen dataset inputs, discovery config/seeds, evaluation code/config, and the
existing discovery/factor/recorder/prediction output tree through native DVC
stage, lock-entry, and output identities. It must not copy artifacts or create
an experiment database.

```text
REAL_V3_CANDIDATE_CREATED = NO
FAKE_V3_CANDIDATE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
PRIVATE_REPORT = D:/AQ_DATA/P3/formulaic-alpha-candidate-handoff-contract-audit-001/audit_summary.json
PRIVATE_REPORT_SHA256 = 280b214026f3490e58cf8bca04a532300eaa54a7337c34b2f40e551188280c74
CURRENT_NEXT = P3_FORMULAIC_ALPHA_DVC_REPRODUCIBILITY_SEAL_001
```
