# P4 Residual Capability Upstream Substitution Audit 001

## Decision

```text
P4_RESIDUAL_UPSTREAM_SUBSTITUTION_AUDIT = PASS
ALL_P4_RESIDUAL_CAPABILITIES_AUDITED = YES
ALL_SERIOUS_UPSTREAM_CANDIDATES_EVALUATED = YES
MODULE_LEVEL_REUSE_AUDITED = YES
REAL_POC_FOR_FINALISTS = YES
CURRENT_AUTHORITATIVE_ENVS_MUTATED = NO
UPSTREAM_SOURCE_COPIED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P4_SELECTED_UPSTREAM_COMPONENTS_DEPLOYMENT_001
```

This audit supersedes immediate implementation of
`P4_LIFECYCLE_CONTRACT_AND_STATE_POLICY_001`. It refines, but does not erase,
the prior P4 Champion-System upstream-fit audit. It does not implement the
Champion lifecycle, change an authoritative dependency environment, issue a
Certified artifact, consume historical TEST, or access sealed OOS.

## Frozen existing owners

The following remain `KEEP_EXISTING_UPSTREAM`:

- Qlib `0.9.8.dev26` at source
  `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`: training, prediction,
  IC/RankIC, signal/portfolio analysis, rolling tasks, rolling/online model
  mechanics, history, refresh, and Recorder;
- MLflow `3.16.0`: experiment/run/artifact identity and model versions,
  aliases, and tags where model artifacts exist;
- DVC `3.67.1`: dependency/output identity, invalidation, reproducibility, and
  lock state;
- RFC 8785: canonical content identity;
- P2: sole certification authority;
- P12: recurring scheduling and operational timing;
- Pydantic and JSON Schema for object contracts, with Pandera only where
  dataframe semantics apply.

No replacement churn is authorized for these owners.

## Residual capability result

| Capability | Generic mechanism owner | AQ domain responsibility |
| --- | --- | --- |
| Lifecycle transitions | frozen literal edge relation plus pure validation | six state meanings, five authorized edges, and P2-only certification |
| Policy expression | Pydantic/JSON Schema validation | transparent fixed financial/lifecycle predicates |
| Change-detection math | selected Frouros ADWIN leaf | admissible streams and financial interpretation |
| Financial decay | upstream detector evidence | thresholds, corroboration, cooldown, and lifecycle consequence |
| Challenger/Champion roles | Qlib history plus MLflow tags/aliases | eligibility, promotion, demotion, and role authority |
| Retirement | existing identity/evidence projections | terminal eligibility and irreversibility |
| Shadow admission | Qlib/MLflow/DVC evidence | zero-capital completeness and admission contract |
| Research Request | Pydantic/JSON Schema plus RFC 8785 | producer-neutral `ResearchRequestV1` payload |
| Event envelope | CloudEvents is technically fit, deferred to P12 | domain payload only |
| Config versioning | DVC plus RFC 8785 and schema validation | policy field meanings |
| Policy execution | ordinary pure function call | small fixed project predicates |
| Persistence | Qlib/MLflow/DVC projections and immutable evidence | replayable decision evidence; no database |

## FSM decision

Isolated Python 3.10.21 POCs exercised `transitions 0.9.3` and
`python-statemachine 3.2.1` over six states and five edges. Both were
deterministic and failed closed on an unauthorized direct promotion.
`transitions` could disable auto-transitions. Both nevertheless require a
mutable machine/model or class/callback surface.

`Automat 25.4.16` was also inspected as the strongest active alternate. None
of the three removes P4 domain policy; each replaces a frozen edge table and a
small pure validator with more machinery.

```text
FSM_UPSTREAM_DECISION = REJECT_OVERABSTRACTION
AQ_GENERIC_FSM_ENGINE_REQUIRED = NO
```

## Policy-engine decision

`rule-engine 5.0.2` correctly evaluated a typed local predicate, returned the
expected healthy/degraded results, rejected an unknown symbol, and did not
execute arbitrary Python. OPA `1.20.2` also returned the expected results from
Rego using the official Linux static binary. The binary was 63,571,086 bytes
with SHA-256
`69da5179ee403d10fa11bab6cfb4ffb0d23dba5f9b682fa977db772a1da5670f`.

Both POCs prove these projects can evaluate conditions. They do not define
what financial degradation means. A new expression DSL, Rego runtime, or CEP
engine would add more code and operational surface than the fixed predicates
it replaces. `durable_rules 2.0.28` is also stale at the package boundary.
`python-jsonlogic 0.2.0` is a credible lightweight alternate but remains
unnecessary. The official `cel-expr-python 0.1.3` requires Python >=3.11.

```text
POLICY_ENGINE_DECISION = REJECT_OVERABSTRACTION
AQ_GENERIC_POLICY_ENGINE_REQUIRED = NO
```

## Drift/change-detection decision

This audit used only deterministic synthetic financial-style RankIC streams:

- stable positive to persistent near zero;
- stable positive to sign reversal;
- noisy stable stream with no structural change;
- gradual deterioration;
- temporary shock followed by recovery.

It did not tune against the 17 AlphaGen historical TEST outcomes or sealed
OOS. Both finalists used upstream ADWIN defaults and passed deterministic
replay and serialized-state restoration.

| Case | Frouros 0.9.0 | River 0.26.1 |
| --- | ---: | ---: |
| positive → near zero | index 1247 / delay 247 | index 1183 / delay 183 |
| positive → sign reversal | index 1119 / delay 119 | index 1087 / delay 87 |
| stable noise | no detection / no false positive | no detection / no false positive |
| gradual deterioration | index 1823 / delay 823 | index 1695 / delay 695 |
| temporary shock/recovery | no detection | index 1087 / delay 87 |

Frouros required a documented constant `+1` translation because its ADWIN
implementation rejects a negative running total. The translation preserves
changes but must remain explicit evidence-adapter provenance. River accepts the
signed stream directly and was faster, but its current release requires Python
>=3.11. Selection is based on runtime and ownership fit, not on the smaller
synthetic detection delay.

The selected new upstream is exactly:

```text
FROUROS_PACKAGE = 0.9.0
FROUROS_RELEASE_SOURCE_SHA = 2484916fe0ba50dd2f28bbf1899f2ef3e499df31
FROUROS_AUDITED_REPOSITORY_HEAD = 9fc1f1cd2174f0aaa7eefb7133f2a17b7ba7b970
FROUROS_MODULE = frouros.detectors.concept_drift.streaming.window_based.ADWIN
FROUROS_DEPLOYMENT = ISOLATED_PYTHON_3_10_21_P4_MONITORING_RUNTIME
DRIFT_DETECTION_DECISION = POC_PASS_ADOPT
```

Frouros `0.9.0` must not be installed into the authoritative Qlib environment:
its NumPy, SciPy, Matplotlib, and Requests constraints conflict with the
currently established versions. Deployment is therefore gated to a dedicated
P4 environment with exact dependency hashes. AQ may adapt validated metric
observations and interpret detector evidence; it may not copy or reimplement
ADWIN math.

River remains a technically successful, maintained alternate but is deferred
because it requires Python >=3.11 and a second detector is not justified.
Alibi Detect, Evidently, NannyML, Menelaus, and Deepchecks were rejected or
deferred for license, dependency-weight, maintenance, or semantic-fit reasons.
Notably, current Alibi Detect uses Business Source License 1.1, and Deepchecks
uses AGPL-3.0.

## Shadow and role tooling

P4 Shadow means research-market observation with zero capital, not inference
traffic. Qlib retains rolling prediction/simulation/Recorder evidence; MLflow
retains run/model identity and aliases/tags; DVC retains reproducibility.
Champion and Challenger remain AQ policy roles projected through those public
surfaces, never a second registry.

KServe, Seldon Core, Argo Rollouts, and BentoML solve serving, Kubernetes
traffic, or deployment rollout problems. They are rejected as semantic and
operational mismatches. Kubernetes is not required.

## Research event boundary

The CloudEvents Python SDK `2.2.0` round-tripped a transport-neutral envelope
through its public `CloudEvent` and `JSONFormat` APIs. That demonstrates a
valid future owner for id/source/type/subject/time/serialization. Transport and
scheduling belong to P12, however, so adoption is deferred:

```text
RESEARCH_EVENT_DECISION = DEFER_TO_P12
CLOUDEVENTS_DECISION = DEFER_TO_P12
MESSAGE_QUEUE_ADDED = NO
```

P4 owns only the producer-neutral ResearchRequest domain payload.

## Persistence

No new AQ state database is justified. Required history and identities can be
projected to Qlib Recorder/OnlineManager, MLflow runs/tags/artifacts/aliases,
and DVC immutable evidence. AQ decisions must be replayable documents that
reference these upstream identities.

```text
AQ_STATE_DATABASE_REQUIRED = NO
```

## Minimal residual AQ scope

AQ still owns only:

- domain facts/config: state names, allowed edges, financial meanings,
  zero-capital Shadow requirements, thresholds, corroboration, cooldown, and
  human authority boundaries;
- contract schemas: lifecycle evidence/decision objects, ResearchRequestV1,
  Shadow completeness, detector evidence, and policy versions;
- bounded glue: validate/order Qlib-derived observations, record the Frouros
  translation, call ADWIN, and link output to Qlib/MLflow/DVC identities;
- executable policy: small pure transition, admission, financial degradation,
  promotion/demotion/retirement, and request-construction predicates.

No generic upstream can own these last predicates because they are the
project-specific meanings being configured, not reusable mechanics.

```text
AQ_WORKFLOW_ENGINE_REQUIRED = NO
AQ_MODEL_REGISTRY_REQUIRED = NO
AQ_METRIC_ENGINE_REQUIRED = NO
AQ_DRIFT_ENGINE_REQUIRED = NO
AQ_SCHEDULER_REQUIRED = NO
AQ_STATE_DATABASE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Deployment waves

1. Pin and deploy only the Frouros `0.9.0` ADWIN leaf in a dedicated Python
   3.10.21 P4 monitoring environment; preserve all authoritative environments.
2. Add the bounded evidence adapter and synthetic/reset/replay/fail-closed
   tests without copying detector math.
3. Link detector evidence to existing Qlib/MLflow/DVC identities and project
   roles without a registry or database.
4. Run `P4_UPSTREAM_COMPONENTS_INTEGRATION_AND_OWNERSHIP_REAUDIT_001`; only
   then may `P4_RESIDUAL_THIN_POLICY_IMPLEMENTATION_001` resume.

This task performs none of those deployment actions.

## Upstream references

The audit used official project/package surfaces, including:

- Frouros ADWIN API: <https://frouros.readthedocs.io/en/v0.9.0/api_reference/detectors/concept_drift/auto_generated/frouros.detectors.concept_drift.streaming.window_based.ADWIN.html>
- River ADWIN API and runtime support: <https://riverml.xyz/dev/api/drift/ADWIN/> and <https://github.com/online-ml/river>
- transitions, python-statemachine, and Automat repositories:
  <https://github.com/pytransitions/transitions>,
  <https://github.com/fgmacedo/python-statemachine>, and
  <https://github.com/glyph/Automat>
- rule-engine and OPA policy language:
  <https://github.com/zeroSteiner/rule-engine> and
  <https://www.openpolicyagent.org/docs/policy-language>
- CloudEvents Python SDK: <https://github.com/cloudevents/sdk-python>
- deployment-serving candidates:
  <https://github.com/kserve/kserve>,
  <https://github.com/SeldonIO/seldon-core>,
  <https://github.com/argoproj/argo-rollouts>, and
  <https://github.com/bentoml/BentoML>

Current release metadata, source heads, licenses, runtime requirements,
dependency footprints, maintenance observations, and classifications are
frozen in `candidate_project_inventory.json` under the private evidence root.

## Private evidence

The private evidence root contains the 14 required JSON artifacts, isolated
POC environments, POC sources, and raw results:

```text
PRIVATE_REPORT = D:/AQ_DATA/P4/residual-upstream-substitution-audit-001/audit_summary.json
PRIVATE_REPORT_SHA256 = ce72d65b8b42c66fe4ece4891d814ce785d8f8fbce4a6a7500340b80c32fe117
```

## Final state

```text
P4_SELECTED_NEW_UPSTREAMS = FROUROS_0_9_0_ADWIN_ISOLATED_RUNTIME
P4_KEEP_EXISTING_UPSTREAMS = QLIB; MLFLOW; DVC; RFC8785; P2; P12; PYDANTIC_JSON_SCHEMA; PANDERA_DATAFRAMES_ONLY
P4_REJECTED_OR_DEFERRED_UPSTREAMS = TRANSITIONS_REJECT_OVERABSTRACTION; PYTHON_STATEMACHINE_REJECT_OVERABSTRACTION; AUTOMAT_REJECT_OVERABSTRACTION; RULE_ENGINE_REJECT_OVERABSTRACTION; OPA_REJECT_OVERWEIGHT; DURABLE_RULES_REJECT_OVERWEIGHT; PYTHON_JSONLOGIC_DEFER; CEL_PYTHON_REJECT_RUNTIME_INCOMPATIBLE; RIVER_DEFER_RUNTIME_INCOMPATIBLE_ALTERNATE; ALIBI_DETECT_REJECT_OVERWEIGHT_LICENSE; EVIDENTLY_REJECT_OVERWEIGHT; NANNYML_REJECT_SEMANTIC_MISMATCH; MENELAUS_REJECT_MAINTENANCE; DEEPCHECKS_REJECT_OVERWEIGHT_LICENSE; CLOUDEVENTS_DEFER_TO_P12; KSERVE_SELDON_ARGO_BENTOML_REJECT_SEMANTIC_MISMATCH
P4_RESIDUAL_AQ_SCOPE = DOMAIN_FACTS_AND_CONFIG; CONTRACT_SCHEMAS; BOUNDED_EVIDENCE_ADAPTER_AND_IDENTITY_PROJECTION; SMALL_PURE_FINANCIAL_AND_LIFECYCLE_PREDICATES
CURRENT_NEXT = P4_SELECTED_UPSTREAM_COMPONENTS_DEPLOYMENT_001
```
