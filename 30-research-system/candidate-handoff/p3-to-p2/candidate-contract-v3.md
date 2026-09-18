# P3 Candidate-to-P2 Identity Contract V3

## Status and scope

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V3
CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
PRODUCER_NEUTRAL = YES
SUPPORTED_PRODUCER_KINDS = RD_AGENT; FORMULAIC_ALPHA
CANDIDATE_ID_INPUT_FIELD_COUNT = 7
AQ_CUSTOM_CANONICALIZER = NO
AQ_CANDIDATE_REGISTRY = NO
```

V3 is the producer-neutral identity boundary between completed P3 research and
P2 Certification. It does not certify, rank, promote, or rerun a Candidate.
V1 and V2 remain immutable. The normative machine-readable definition is
`candidate-contract-v3.schema.json`.

## Exact top-level contract

Every instance has exactly these eight required fields and no others:

1. `candidate_contract_version`
2. `candidate_id`
3. `research_producer_identity`
4. `qlib_recorder_identity`
5. `artifact_identity_bundle`
6. `dataset_identity_bundle`
7. `runtime_identity_bundle`
8. `p2_target_and_eligibility_boundary`

`research_producer_identity` is a closed discriminated union keyed by
`producer_kind`. The artifact and runtime bundles carry the same discriminator.
The schema fails closed if those three producer branches do not match.

## Producer branches

### RD-Agent

The `RD_AGENT` branch references the immutable V1 RD-Agent research and
artifact definitions and the immutable V2 runtime definition. It therefore
preserves exact RD-Agent source/wheel/environment identity, generated research
identity, native DVC artifact identity, LiteLLM execution identity, native
trace identity, resolved chat identity, embedding identity, and embedding
epoch. V3 does not weaken or synthesize any V2 requirement.

No RD-Agent V3 instance is materialized by this task.

### Formulaic Alpha

The `FORMULAIC_ALPHA` branch records only systems that actually executed:

```text
producer_kind = FORMULAIC_ALPHA
engine_name = ALPHAGEN
engine_git_sha = 259687e8f316994426416c530a94842a2fe6405e
discovery_configuration_identity = ALPHAGEN_MSE_LSTSQ_FAST_V1
discovery_summary_sha256 = 5212564ed15b3fa15bde40f14b9fe9a067b725bc5dd472a6046af0013893523a
frozen_candidate_manifest_sha256 = de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145
```

Each instance binds one exact AlphaGen expression, its SHA-256, source
candidate ID, cluster identity, numerically sorted origin seeds, and origin
seed/pool locations. It does not contain TRAIN/VALID/TEST metrics, pool
weights, runtime durations, or hardware measurements.

Formulaic runtime identity binds AlphaGen and Qlib source SHAs, the research
configuration identity, the post-run runtime-freeze identity and its truthful
`NO_PROVEN_DRIFT` classification, both executed Python environments, and the
actual Stable-Baselines3, SB3-Contrib, and Gymnasium versions. RD-Agent,
LiteLLM, Ollama, embedding, and LLM trace fields are structurally forbidden in
this branch.

## Candidate ID

`candidate_id` is derived from exactly the seven non-ID top-level fields:

```text
candidate_id =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8(
        RFC_8785_JCS(seven_field_projection)
      )
    )
  )
```

The authorized implementation is the upstream Python package `rfc8785`
version `0.1.4`. AQ does not implement JCS.

Before JCS, collection-valued identity fields must be deterministically sorted:

- origin seeds: numeric ascending;
- origin locations: `origin_seed`, then `pool_index`;
- content/evaluation identities: `logical_role`, then `sha256`;
- DVC dependencies: `logical_role`, then `algorithm`, then `value`;
- all inherited V1/V2 collections: the immutable V1 ordering rules.

Filesystem traversal order is never identity authority.

## Qlib and artifact identity

One Candidate represents one AlphaGen expression and one real Qlib recorder.
The recorder requires exact `experiment_id`, exact `run_id`, and
`status = FINISHED`.

The Formulaic artifact bundle binds:

```text
DVC_STAGE = p3_formulaic_alpha_reproducibility_seal
DVC_STAGE_LOCK_ENTRY_IDENTITY = sha256:659b1ae448be57c915d5f096fa3b112afef0232f69739fb4eaa7ab267c301df1
SEAL_OUTPUT_SHA256 = 60e5d0b271fa6e5a074f329a752ea5d80abfe2a1cb49dd89d1ed33609052fecb
SEAL_OUTPUT_DVC_IDENTITY = md5:2247c8d12da0bda075b172940284a94f
QLIB_EXECUTION_CONFIG_AUTHORITY = DETERMINISTIC_RUN_CONFIG_JSON
```

Each Candidate additionally binds its deterministic `run_config.json`, native
prediction bytes, recorder-evidence file, prediction-evidence file, and the
applicable frozen evaluation manifests. A rendered Qlib YAML is not invented.

Serialized model state is a closed union:

- `PERSISTED` requires a real content identity;
- `NOT_PERSISTED_BY_UPSTREAM` forbids an identity.

All 17 current Formulaic Candidates use `NOT_PERSISTED_BY_UPSTREAM` because
the completed upstream execution did not persist model bytes.

## Dataset and P2 boundary

The dataset bundle references the existing provider build, calendar,
instrument, PIT membership, date-bound and row-count authorities. It does not
copy market data. Relevant provider dependencies use the DVC-calculated
identities from the Formulaic seal stage.

Every currently materialized Formulaic Candidate states:

```text
candidate_eligibility_status = INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION
historical_research_test_accessed = true
historical_research_test_status = CONSUMED_AS_RESEARCH_EVIDENCE
sealed_oos_accessed_by_p3 = false
p3_can_issue_certified = false
p3_can_edit_protocol = false
p3_can_promote_to_production = false
```

Historical TEST is not pristine OOS. Candidate identity does not change P2
Protocol V1, certify a Candidate, or authorize production promotion.

## Identity exclusions

Candidate V3 identity excludes IC, RankIC, Sharpe, returns, PnL, TEST
performance, runtime seconds, GPU/CPU measurements, timestamps, hostnames,
absolute operational paths, display names, and certification outcomes.
Performance evidence remains with its upstream owner and outside Candidate ID.

## Ownership

```text
CONTRACT_SCHEMA_POLICY = AQ_OWNED_DOMAIN_CONTRACT
ALPHAGEN = UPSTREAM_WHOLE
QLIB = UPSTREAM_WHOLE
DVC = UPSTREAM_LEAF
RFC8785 = UPSTREAM_LEAF
AQ_CUSTOM_CANONICALIZER = NO
AQ_CANDIDATE_REGISTRY = NO
AQ_CUSTOM_RECORDER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```
