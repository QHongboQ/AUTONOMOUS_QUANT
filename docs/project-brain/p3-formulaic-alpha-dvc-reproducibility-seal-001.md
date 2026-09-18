# P3 Formulaic Alpha DVC Reproducibility Seal 001

## Authority result

```text
P3_FORMULAIC_ALPHA_DVC_REPRODUCIBILITY_SEAL = PASS
FORMULAIC_DVC_IDENTITY = PRESENT
FORMULAIC_RUNTIME_FREEZE = PASS
RUNTIME_ENV_DRIFT_SINCE_RESEARCH = NO_PROVEN_DRIFT
HISTORICAL_RESEARCH_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
CURRENT_P2_PROTOCOL_ELIGIBILITY = INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION
CANDIDATE_V1 = IMMUTABLE
CANDIDATE_V2 = IMMUTABLE_RDAGENT_LLM_SPECIFIC
CURRENT_NEXT = P3_CANDIDATE_TO_P2_CONTRACT_V3_MATERIALIZATION_001
```

This task sealed the already-completed AlphaGen discovery and Qlib evaluation.
It did not rerun discovery, training, prediction, evaluation, or selection and
did not create Candidate V3. Historical TEST remains consumed research evidence,
not pristine or sealed OOS evidence.

## Runtime and source provenance

The post-run runtime reconstruction found no package or environment mutation
after either completed research execution. Conda histories predate the runs and
the two environment trees contain no files newer than their respective evidence
completion boundaries. The resulting classification is deliberately limited to
`NO_PROVEN_DRIFT`; it does not claim an independently contemporaneous freeze.

```text
DISCOVERY_ENV = /home/zhou/miniforge3/envs/aq-alphagen-upstream-guidance
DISCOVERY_PYTHON = 3.10.21
EVALUATION_ENV = /home/zhou/miniforge3/envs/rdagent4qlib
EVALUATION_PYTHON = 3.10.21
ALPHAGEN_SHA = 259687e8f316994426416c530a94842a2fe6405e
QLIB_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
AQ_SEAL_HEAD = 04a9ae29069fb34164f5637c3a59df459f0ff67d
RUNTIME_FREEZE_SHA256 = 1c86d57b148510ccdde19c36edf4c35a8d3915f624bd8d5d2fb65f0ef040fab5
```

Complete `pip freeze` and Conda explicit inventories for both environments are
stored under the private evidence root. Their hashes are embedded in the seal.

## Immutable research identities

```text
DISCOVERY_SUMMARY_SHA256 = 5212564ed15b3fa15bde40f14b9fe9a067b725bc5dd472a6046af0013893523a
FROZEN_CANDIDATE_MANIFEST_SHA256 = de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145
QLIB_EVALUATION_SUMMARY_SHA256 = c077196473711ebcbd33e572cb4e3de5a07103dba9e7aa8f88f255a7acf9b6a0
QLIB_ARTIFACT_MANIFEST_SHA256 = 4da1e39480f84c284a7bd7d01bdc921226b4752e1759aff82dbf2d576214e01f
PROVIDER_BUILD_REPORT_SHA256 = eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142
CANDIDATE_COUNT = 17
QLIB_RECORDERS_FINISHED = 17
PREDICTION_ARTIFACT_COUNT = 17
QLIB_EXECUTION_CONFIG_AUTHORITY = DETERMINISTIC_RUN_CONFIG_JSON
QLIB_RUN_CONFIG_COUNT = 17
QLIB_NATIVE_RENDERED_CONFIG = ABSENT_NOT_FABRICATED
SERIALIZED_MODEL_ARTIFACT = ABSENT_UPSTREAM_EXECUTION_DID_NOT_PERSIST
```

## DVC ownership

DVC 3.67.1 ran under WSL Linux from `/home/zhou/AQ_ENVS/dvc-p3`.
Windows DVC was not used. The new independent stage validates immutable hashes
and produces one small identity-only output; it contains no research execution.
The command initially exposed a missing bare `python` PATH entry before the seal
script started. The stage was corrected to the same DVC environment's explicit
Python executable, then the first actual seal execution passed and the immediate
second reproduction was a native no-change skip.

```text
DVC_STAGE_NAME = p3_formulaic_alpha_reproducibility_seal
DEPENDENCY_COUNT = 17
DVC_OUTPUT_COUNT = 1
FIRST_SUCCESSFUL_DVC_REPRO = PASS
SECOND_DVC_REPRO = UNCHANGED_DATA_AND_PIPELINES_UP_TO_DATE
DVC_YAML_SHA256 = 1065a2cc9fdfc2edb8c0322f9f089c6edf5842a51ee986e4e99480fbfd0ebdac
DVC_LOCK_SHA256 = 9d6019b8215ab626b1301cdb1d5e920df7641b5b1ae2baaebed44311f5342462
DVC_STAGE_LOCK_ENTRY_IDENTITY = sha256:659b1ae448be57c915d5f096fa3b112afef0232f69739fb4eaa7ab267c301df1
SEAL_OUTPUT_SHA256 = 60e5d0b271fa6e5a074f329a752ea5d80abfe2a1cb49dd89d1ed33609052fecb
SEAL_OUTPUT_DVC_HASH = md5:2247c8d12da0bda075b172940284a94f
PRIVATE_REPORT_SHA256 = a9f5dce9dee55f87e72a6b31d71b7f77fbf15db42cf0c68ce07f7c7b8dab7e10
```

The upstream ownership boundary remains intact: DVC owns dependency/output
identity and invalidation; AlphaGen and Qlib remain upstream wholes; AQ owns
only the domain-specific validation and identity seal. No generic DVC engine,
experiment registry, recorder, or new generic engine was introduced.

## Safety accounting

```text
ALPHAGEN_DISCOVERY_RERUN = NO
QLIB_MODEL_TRAINING_RERUN = NO
QLIB_PREDICTION_RERUN = NO
HISTORICAL_TEST_REEVALUATED = NO
MARKET_NETWORK_CALLS = 0
LLM_CALLS = 0
RD_AGENT_EXECUTED = NO
OLLAMA_EXECUTED = NO
BROKER_CALLS = 0
SEALED_OOS_ROWS_ACCESSED = 0
CANDIDATE_V1_MODIFIED = NO
CANDIDATE_V2_MODIFIED = NO
REAL_V3_CANDIDATE_CREATED = NO
AQ_CUSTOM_DVC_ENGINE = NO
AQ_CUSTOM_EXPERIMENT_REGISTRY = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```
