# P5 filing-feature historical materialization design and ablation protocol 001

## Authority, scope, and ownership

This policy starts from authoritative main
`900cdac923692fa1f3c86c9d75d5e7f8eea0a7b7`. It freezes the future
historical materialization and evaluation boundary for the five already-merged
`FilingFeatureObservationV1` features. It does not materialize a historical
feature row, retrieve a filing, train a model, produce a prediction, run a
backtest, inspect performance, or access P2 V2 sealed OOS.

## Current authority supersession

This document remains the historical design and contract evidence for five
valid filing-derived research ideas. The final P5 V1 scope authority now
classifies their mass historical materialization and ablation as a
`DEFERRED_OPTIONAL_P5_EXTENSION`, not a P5 V1 completion requirement. The
proven EdgarTools filing/document/exhibit interfaces remain available upstream;
no interface or feature contract is invalidated.

The safely stopped all-form attempt is retained without promotion or deletion:

```text
ALL_FORM_POPULATION_CENSUS = DIAGNOSTIC_SUPERSEDED_PRE_EVALUATION
ALL_FORM_POPULATION_CENSUS_STATUS = DIAGNOSTIC_SUPERSEDED_PRE_EVALUATION
TOTAL_ADMITTED_FILING_ACCESSIONS = 826859
EVENT_FORM_ACCESSION_COUNT = 62371
PARTIAL_COMPLETED_ACCESSION_COUNT = 20000
PARTIAL_COMPLETED_OBSERVATION_COUNT = 100000
PARTIAL_OUTPUT_CLASSIFICATION = PARTIAL_ABORTED_SUPERSEDED_SCOPE
P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION = DEFERRED_OPTIONAL_P5_EXTENSION
FILING_FEATURE_HISTORICAL_MATERIALIZATION_STATUS = DEFERRED_OPTIONAL_P5_EXTENSION
P5_V1_REQUIRED_FILING_DERIVED_FEATURE_COUNT = 0
```

The remaining sections preserve the historical optional-extension design.
They do not authorize resumption, promotion into P5 V1 DVC authority, S2/H2
execution, or a P5 V1 completion blocker. Separate future authorization would
be required to activate them.

```text
CAPABILITY = historical materialization and later evaluation of five deterministic P5 filing features
EDGARTOOLS = UPSTREAM_WHOLE
QLIB = UPSTREAM_WHOLE
EXCHANGE_CALENDARS = UPSTREAM_LEAF
PANDAS = UPSTREAM_LEAF
PYARROW = UPSTREAM_LEAF
DVC = UPSTREAM_LEAF
ARCH = UPSTREAM_LEAF
AQ = THIN_DOMAIN_POLICY_ONLY
CUSTOM_ENGINE_REQUIRED = NO
NEW_PRODUCTION_LOC = 0
SEC_DATA_REQUEST_COUNT = 0
```

EdgarTools owns filing metadata, typed reports, attachments, press-release
selection, and exhibit semantics. `exchange_calendars` owns XNYS sessions.
Pandas supplies exact joins (and as-of projection only where a separately
frozen state semantic requires it), PyArrow owns Parquet persistence, DVC owns
artifact/dependency identity, Qlib owns `StaticDataLoader`, `DataHandlerLP`,
`DatasetH`, model execution, Recorder, signal analysis, and backtesting, and
arch owns any later multiple-testing statistics required by the frozen
protocol. AQ owns only the five contracts, source-population policy, PIT and
identity admission, dataset column mapping, the two-trial inventory, and the
interpretation decision.

No AQ dataset, as-of, feature-store, experiment, backtest, statistics, model,
or artifact engine is authorized.

## Frozen feature family

The historical build may emit exactly these five IDs, in this order:

1. `p5_filing_lag_days_v1`
2. `p5_accepted_after_market_close_v1`
3. `p5_is_amendment_v1`
4. `p5_press_release_exhibit_present_v1`
5. `p5_authorized_exhibit_count_v1`

Their merged formulae, missingness, evidence identity, and
acceptance-to-first-XNYS-session rules remain unchanged. There is no sixth
feature, tuned transform, clipping, winsorization, normalization, or textual
inference.

## Historical accession populations

The structured-fundamental inventory of 36,204 accessions is not a complete
filing-feature population. It was selected through EntityFacts and authorized
numeric-concept eligibility; it intentionally does not represent all native
filings and therefore cannot establish the complete 8-K/6-K surface or the
complete metadata surface.

```text
STRUCTURED_FUNDAMENTAL_ACCESSION_INVENTORY_REUSABLE_FOR_ALL_FILING_FEATURES = NO
```

It remains reusable as a provenance-bearing subset only. It must not be
treated as the filing-feature denominator.

The future population authority is the exact accession inventory returned by
EdgarTools 5.58.0 for authoritative bound CIKs, with `amendments=True`, within
the authorized historical range. Discovery uses the native
`Company(cik).get_filings(filing_date=..., amendments=True,
trigger_full_load=True)` surface (or its native `Filings.filter` equivalent),
never an AQ SEC client. Query boundaries are widened to the previous XNYS
session date where needed, then admitted only when the existing computed
`first_available_xnys_session` is contained in both the P1 episode and the
date-valid `EpisodeSecCikBindingV1`. Accession number is the deduplication key.
No current-ticker query participates.

The form/family policy is deliberately feature-specific and follows the
already-merged applicability rules:

| Feature | Future discovery population | Scalar eligibility |
|---|---|---|
| `p5_filing_lag_days_v1` | All exact accession-bound SEC forms for authoritative CIKs | Verified acceptance datetime and exact report-period end; no form restriction is invented. |
| `p5_accepted_after_market_close_v1` | All exact accession-bound SEC forms for authoritative CIKs | Verified acceptance on an XNYS session date with an exact official close; non-session dates retain `NOT_APPLICABLE_SESSION_DATE`. |
| `p5_is_amendment_v1` | All exact accession-bound SEC forms for authoritative CIKs | Verified exact filed form; value follows only the exact `/A` suffix. |
| `p5_press_release_exhibit_present_v1` | Exactly `8-K`, `8-K/A`, `6-K`, and `6-K/A` | Applicable native `CurrentReport`/`SixK` object with a loaded attachment inventory. |
| `p5_authorized_exhibit_count_v1` | Exactly `8-K`, `8-K/A`, `6-K`, and `6-K/A` | Applicable native `CurrentReport`/`SixK` content-exhibit collection. |

Restricting the first three features to periodic forms would silently change
their merged applicability and is prohibited. Conversely, running native
exhibit materialization on other forms merely for implementation convenience
is prohibited.

The future build first seals a population manifest containing at least the
accession, CIK, form, filing date, acceptance datetime, report period when
present, authoritative episode/binding identities, discovery runtime identity,
and canonical population hash. No census is executed by this design task.

## Sparse immutable primary store

```text
PRIMARY_STORAGE_SHAPE = SPARSE_ACCESSION_BOUND_OBSERVATIONS
```

The primary Parquet dataset is the exact serialized
`FilingFeatureObservationV1` relation: one row per feature from one accession,
with one acceptance/effective-session identity. `immutable_evidence_identity`
is the primary key. A duplicate ID with different content is a hard failure;
an exact duplicate is deduplicated without changing the canonical row.

The sparse store retains rows with no scalar so that missingness remains
auditable. The only permitted missingness values are:

```text
NOT_APPLICABLE_FORM
NOT_APPLICABLE_SESSION_DATE
NATIVE_OBJECT_UNAVAILABLE
SOURCE_UNAVAILABLE
REQUIRED_METADATA_MISSING
VALIDATED_ABSENCE
INVALID_VALUE
```

A legitimate zero remains numeric zero. Every missingness state remains a null
scalar and is never coerced to zero. The immutable long-form observation store
and a Qlib numeric projection are separate surfaces; the numeric projection
does not erase the long-form missingness/provenance authority.

Suggested physical partitioning is `feature_id` plus acceptance year, with a
single build manifest and schema identity above the partitions. PyArrow writes
staging partitions, validates them, and atomically promotes a new immutable
root. DVC seals that root and its population/build-spec dependencies. It does
not track transient EdgarTools caches.

## Frozen temporal representation and PIT routing

All five values describe one filing event, not an issuer state. Their future
session representation is therefore frozen before performance inspection:

```text
FILING_LAG_TEMPORAL_SEMANTIC = POINT_EVENT
AFTER_CLOSE_TEMPORAL_SEMANTIC = POINT_EVENT
IS_AMENDMENT_TEMPORAL_SEMANTIC = POINT_EVENT
PRESS_RELEASE_TEMPORAL_SEMANTIC = POINT_EVENT
EXHIBIT_COUNT_TEMPORAL_SEMANTIC = POINT_EVENT
```

A valid scalar appears only on its carried
`first_available_xnys_session`. It is not visible earlier and is not carried
to a later session. No forward-fill, backward-fill, persistence horizon,
decay, or latest-known-state interpretation is allowed for V1.

The future numeric projection is an exact keyed projection, not a universal
as-of fill. If more than one eligible accession maps to the same
`(episode_id, session, feature_id)`, choose the observation with greatest
`(sec_acceptance_datetime, source_accession)` within that feature's own
eligible population. The chosen cell retains its accession and immutable
evidence ID in a companion long-form projection ledger. A later inapplicable
form never competes with the four-form exhibit population. A selected missing
observation remains null; it is not replaced by an earlier scalar. Equal
ordering keys with conflicting evidence fail closed. No sum, maximum, mean,
or other new feature formula is introduced.

## Identity and universe admission

The left authority is the existing P1 episode/session universe. A filing may
contribute only when all of these are true:

1. its CIK has exactly one date-valid `EpisodeSecCikBindingV1`;
2. its `first_available_xnys_session` is within that binding;
3. the same session is within the P1 `InstrumentEpisodeV1` membership interval;
4. no CIK, episode, or accession conflict exists.

The Qlib `instrument` is the immutable `episode_id`, not current ticker text.
Ticker may remain descriptive provenance only. The 111 existing identity
exclusions, or any successor frozen exclusion inventory, remain in the
eligible session denominator with five null values and explicit exclusion
status. There is no current-ticker inference, predecessor/successor
substitution, cross-CIK carry, or excluded-episode repair.

## Exact future Qlib handoff

The output boundary is:

```text
sparse FilingFeatureObservationV1 Parquet
  -> exact episode/session numeric projection DataFrame
  -> Qlib StaticDataLoader
  -> DataHandlerLP
  -> DatasetH
```

The loader input has a unique MultiIndex named `(datetime, instrument)`, where
`datetime` is the XNYS session and `instrument` is `episode_id`. The feature
group contains exactly the five feature IDs as columns. All other eligible
episode/session cells are IEEE/Arrow nulls, while valid binary/count zero is
retained as zero. The companion provenance/missingness relation remains keyed
by `(datetime, instrument, feature_id)` and is not silently converted into
model inputs.

The exact P1 session grid is the left relation. Therefore filing rows cannot
create sessions, extend membership, or manufacture instruments. Qlib owns the
loader, handlers, segments, model, Recorder, signal analysis, and later
backtest. AQ owns only this column/index mapping and the hard admission checks.

```text
QLIB_HANDOFF_OWNER = MICROSOFT_QLIB
```

## Historical preregistered two-trial ablation (deferred)

The historical optional-extension hypothesis asks whether the five frozen
features add value as one preregistered family. It is not a current P5 V1
required hypothesis. Its retained trial inventory is:

| Trial | Dataset inputs | Model/workflow |
|---|---|---|
| `CONTROL` | Existing approved baseline; none of the five P5 filing columns | One future separately frozen existing Qlib vehicle |
| `ALL_FIVE_FILING_FEATURES` | The same baseline plus all five columns in frozen order | Byte-identical model/workflow, hyperparameters, seeds, labels, strategy, costs, splits, and missing-data processing |

```text
PRIMARY_ABLATION_CONTROL = CONTROL_EXISTING_APPROVED_QLIB_BASELINE_WITHOUT_P5_FILING_V1
PRIMARY_ABLATION_CHALLENGER = SAME_FROZEN_QLIB_BASELINE_PLUS_ALL_FIVE_P5_FILING_V1
PREREGISTERED_TRIAL_COUNT = 2
```

There are no leave-one-out runs, grouped ablations, feature variants, model
comparisons, normalization variants, or threshold searches. A failed family
is rejected as a family. Any later single-feature analysis requires a new
preregistration and new multiple-testing family.

## Historical optional-extension model authority

At design time, the Brain contained a P1 exploratory LightGBM reference and
P2-specific frozen candidates but did not authorize one fixed filing-feature
evaluation vehicle. The current required P5 V1 H1 separately uses the frozen
`qlib.contrib.model.gbdt.LGBModel`; this optional extension remains deferred
and receives no execution authority from that decision.

```text
HISTORICAL_FILING_ABLATION_EVALUATION_MODEL_AUTHORITY = DEFERRED_WITH_OPTIONAL_EXTENSION
```

Before either trial runs, a separate authority action must select one already
existing Qlib model/workflow and freeze its config hash, label, handler,
processors, hyperparameters, seeds, strategy, costs, and runtime. That choice
must be made without observing these five features' performance. Both trials
then reuse it unchanged.

## Frozen historical research split policy

The future P5 ablation uses historical research partitions only:

```text
TRAIN = 2015-04-01 through 2019-12-31
VALIDATION = 2020-01-01 through 2021-12-31
P5_HISTORICAL_RESEARCH_TEST = 2022-01-03 through 2024-12-31
```

The endpoints are calendar bounds resolved to available XNYS/P1 sessions.
The historical test is consumed research evidence, not pristine certification
OOS and never becomes P2 V2 sealed OOS. It may not be used to change feature
formulas, family membership, missingness, normalization, trial inventory,
model choice, or thresholds.

Temporal robustness reuses mature policy primitives already frozen by the
project, when the later model authority activates evaluation:

```text
WALKFORWARD = WalkForward(test_size=63, train_size=504, purged_size=2, expand_train=False, reduce_test=False)
CPCV = CombinatorialPurgedCV(n_folds=10, n_test_folds=2, purged_size=2, embargo_size=2)
```

No new split or CV implementation is permitted. A later certification claim
requires its own P5 certification protocol and genuinely sealed evidence; it
cannot use or reveal the P2 V2 sealed window.

## Metrics and multiple testing

The preregistered primary prediction metric is Qlib Rank IC, evaluated as the
paired challenger-minus-control difference on identical rows. Qlib IC is a
secondary prediction diagnostic. Strategy evidence is limited to native net
return, active return versus control, information ratio where emitted,
maximum drawdown, turnover, and transaction cost. Metrics not listed here may
not replace the primary metric after results are seen.

For confirmatory return evidence, arch 8.0.0 remains the statistical owner and
uses the existing project policy: stationary bootstrap, block size 10, 5,000
replications, seed 20260913, alpha 0.05, and loss equal to negative net daily
return. SPA and RealityCheck are the required two-trial evidence. StepM/MCS
are required only if the governing frozen certification authority requires
them; the trial inventory may not be enlarged to make those procedures more
interesting.

```text
MULTIPLE_TESTING_OWNER = ARCH_8.0.0
AQ_MULTIPLE_TESTING_ENGINE = NO
```

## Frozen result classification

No result is classified in this task. A future complete evidence bundle maps
to exactly one state:

- `INCREMENTAL_VALUE_SUPPORTED`: all eight leakage gates are zero, both trials
  are comparable and complete, challenger-minus-control test Rank IC is
  positive, and the preregistered arch SPA and RealityCheck gates both have
  p-values at or below 0.05 on net daily return loss. Any required StepM/MCS,
  cost, and robustness gates from the governing authority also pass.
- `NO_MEASURABLE_INCREMENTAL_VALUE`: evidence is complete and leakage-free,
  but the challenger does not satisfy every support condition, while the
  reversed comparison also does not establish degradation.
- `DEGRADED`: complete leakage-free evidence supports the control over the
  challenger under the same reversed preregistered statistical comparison, or
  the challenger fails a hard cost/robustness gate that the control passes.
- `INCONCLUSIVE`: evidence is incomplete, incomparable, provenance-invalid,
  underpowered for a required procedure, or blocked by data/runtime/model
  authority. It is not converted into success or failure.

Exploratory per-feature diagnostics cannot retain an individual feature or
alter these states.

## Leakage gates

Every accepted performance bundle must report zero for all eight gates:

1. `ACCEPTANCE_TIME_LEAKAGE_COUNT`
2. `REPORT_PERIOD_LEAKAGE_COUNT`
3. `AMENDMENT_BACKWARD_LEAKAGE_COUNT`
4. `CROSS_CIK_CONTAMINATION_COUNT`
5. `EPISODE_MEMBERSHIP_LEAKAGE_COUNT`
6. `CURRENT_TICKER_LEAKAGE_COUNT`
7. `SOURCE_UNAVAILABLE_SUBSTITUTION_COUNT`
8. `FUTURE_FILING_VISIBILITY_COUNT`

```text
LEAKAGE_GATE_COUNT = 8
```

Any nonzero value makes performance evidence inadmissible and the result
`INCONCLUSIVE`; it does not authorize a repair based on observed performance.

## Historical execution gate (not active for P5 V1)

If the optional extension is separately reauthorized, its historical
materialization may begin only after:

1. this design is merged and frozen;
2. the independent historical fundamentals build reaches terminal closeout,
   or an explicitly authorized resource-safe independent lane exists;
3. the all-form metadata population and exact four-form event population are
   frozen with identities;
4. there is no unresolved source/provenance blocker;
5. the P5 evaluation model authority is frozen before evaluation (not required
   merely to construct the sparse dataset).

The design itself remains complete historical evidence. Execution is deferred,
not waiting as a current P5 V1 gate, and the stopped all-form crawl must not be
resumed under this document.

```text
P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_DESIGN = HISTORICAL_OPTIONAL_EXTENSION_DESIGN
P5_FILING_FEATURE_ABLATION_PROTOCOL = DEFERRED_OPTIONAL_EXTENSION
HISTORICAL_BUILD_STATUS = MINIMAL_UPSTREAM_V1_BUILD_COMPLETE
HISTORICAL_BUILD_INTERFERENCE = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
CURRENT_DEVELOPMENT_NEXT = P5_H1_INCREMENTAL_FUNDAMENTAL_EVALUATION_AND_CLOSEOUT_001
```

The historical design referred to the independent fundamentals build as PID
403. It is now `HISTORICAL_REFERENCE_ONLY`; its 392 failures require no repair
and are not inspected or retried by this scope freeze.

## Validation and closeout

The existing 21-case filing-feature suite passed from local fixtures, and Ruff
passed on the existing filing-feature package. No historical observation was
created: the materialized count below describes the five-feature contract
surface already proven by the merged POC, not a historical build count.

```text
MATERIALIZED_FEATURE_COUNT = 5
TEST_RESULT = 21/21 PASS
RUFF = PASS
DIFF_CHECK = PASS
NEW_PRODUCTION_LOC = 0
FINAL_CLASSIFICATION = PASS_DESIGN_READY_WAITING_FOR_HISTORICAL_BUILD
```
