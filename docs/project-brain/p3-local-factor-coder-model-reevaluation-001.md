# P3 Local Factor Coder Model Reevaluation 001

Implementation date: 2026-09-16

## Scope

This task aligned the existing local `qwen2.5-coder:7b` logical chat slot with
the official LiteLLM/Ollama chat structured-output path, then executed one
bounded official Microsoft RD-Agent `FactorImplementEval` admission. It did
not download or switch models, change the embedding epoch, run the project DVC
stage, execute `fin_quant`, create `p3-fin-quant-004`, train a Qlib model,
generate predictions, backtest, access sealed OOS, or create a Candidate V2
instance.

## Official structured-output authority

The implementation was checked against:

- Ollama Structured Outputs: `https://docs.ollama.com/capabilities/structured-outputs`
- Ollama Chat API: `https://docs.ollama.com/api/chat`
- pinned LiteLLM `1.100.1` `OllamaChatConfig` source
- pinned Microsoft RD-Agent `0.8.1.dev37` backend source at
  `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd`

The pinned `ollama_chat` transform maps OpenAI `response_format` with
`json_object` to Ollama `format="json"`, and maps `json_schema` to the schema
object accepted by Ollama `/api/chat`. Direct local-only calls through pinned
LiteLLM passed both forms with valid unfenced JSON.

Both logical aliases exposed `response_format` in
`get_supported_openai_params`, but the custom aliases returned false from
`supports_response_schema` before model metadata registration. The existing
public LiteLLM `register_model` seam was therefore used to publish the
independently proven capability for `ollama_chat/aq-brain-local`. No RD-Agent,
LiteLLM, or Ollama source was patched.

```text
OLD_CHAT_ROUTE = ollama/aq-brain-local
NEW_CHAT_ROUTE = ollama_chat/aq-brain-local
OFFICIAL_OLLAMA_CHAT_PATH = SUPPORTED
OFFICIAL_OLLAMA_STRUCTURED_OUTPUT = SUPPORTED
PINNED_LITELLM_RESPONSE_FORMAT_MAPPING = SUPPORTED
OLLAMA_ROUTE_SUPPORTS_RESPONSE_SCHEMA_BEFORE = FALSE
OLLAMA_CHAT_ROUTE_SUPPORTS_RESPONSE_SCHEMA_BEFORE = FALSE
PUBLIC_CAPABILITY_METADATA_SEAM = PASS
LITELLM_OLLAMA_CHAT_JSON_OBJECT = PASS
LITELLM_OLLAMA_CHAT_JSON_SCHEMA = PASS
RDAGENT_RESPONSE_FORMAT_RETAINED = YES
RDAGENT_NATIVE_JSON_PARSE = PASS
MARKDOWN_FENCE_PRESENT = NO
CHAT_STREAM_CHANGED = NO
CUSTOM_JSON_PARSER_CREATED = NO
CUSTOM_FENCE_STRIPPER_CREATED = NO
CUSTOM_RETRY_LOGIC_CREATED = NO
```

## Identity and implementation boundary

The resolved chat model and digest remain unchanged. The embedding slot and
embedding epoch also remain unchanged. The thin backend still inherits its
completion and embedding implementations from `LiteLLMAPIBackend`; the only
runtime alignment is the official `ollama_chat` route plus truthful public
capability metadata.

```text
RESOLVED_CHAT_MODEL = qwen2.5-coder:7b
RESOLVED_CHAT_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
OLD_LLM_CONFIGURATION_SHA256 = e087c4edb0d4516c0ea5bf0ade8f6129cf070be276566ab8162c5b65ac2db825
NEW_LLM_CONFIGURATION_SHA256 = 625aa6834f8466535e12e49c643e69d7edf40bbc066e1ba5a56869ac82ba46c1
EMBEDDING_EPOCH_CHANGED = NO
CANDIDATE_V2_SCHEMA_CHANGE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Official factor-coder re-admission

Admission-002 reused the immutable admission-001 fixture, case ordering,
ground-truth validation, two-round requirement, P3 debug source, model digest,
and CoSTEER maximum of ten loops. The only intentional difference was the
corrected official structured-output path.

Structured parsing remained healthy throughout the official run. The model
nevertheless failed all three factor tasks after ten native CoSTEER feedback
loops. `alpha053` and `alpha053_5` ended with index-construction failures;
`alpha053_15` executed but retained multiple source columns and an invalid
non-MultiIndex output. The official `FactorImplementEval.develop()` path then
raised `CoderError: All tasks are failed` during the first configured round,
before any of the six required evaluator slots could satisfy the hard gate.

The six required admission slots therefore fail closed as
`COSTEER_RECOVERY`. The terminal causal evidence is retained separately as
`INDEX` and `SOURCE_SCHEMA`; it is not represented as completed evaluator
scoring.

Private evidence is retained under
`D:\AQ_DATA\P3\factor-coder-admission-002`.

```text
PRIOR_ADMISSION_REPORT_SHA256 = 3623fbb52b1d7b25f7c3889784302787176e6cc976a322233778caafbbf774be
ADMISSION_FIXTURE_SHA256 = cf4c71c3e1758664082bbd45e06cfb78ca71e625fbf5f45d7a5acbf2587b2b49
GROUND_TRUTH_VALIDATION_SHA256 = 674a9a05dfbe0648ffb8db47b8a7623fff9c968a1e3bbe1f4bc2af1909b5d5f5
ADMISSION_002_REPORT_SHA256 = b963e550197ae12850991ed1e673b68d2f34850d7e511aca93bc7cc5bfca98cb
FACTOR_CODER_ADMISSION_CASES = alpha053; alpha053_15; alpha053_5
FACTOR_CODER_ADMISSION_ROUNDS = 2
FACTOR_CODER_ADMISSION_TOTAL_REQUIRED = 6
FACTOR_CODER_ADMISSION_COMPLETED = 0
FACTOR_CODER_ADMISSION_PASSES = 0
FACTOR_CODER_ADMISSION_FAILURES = 6
FAILURE_TAXONOMY = COSTEER_RECOVERY:6
TERMINAL_CAUSAL_EVIDENCE = INDEX; SOURCE_SCHEMA
ADMISSION_LOCAL_LLM_CALLS = 90
PROTOCOL_PROBE_LOCAL_LLM_CALLS = 4
CLOUD_INFERENCE_REQUESTS = 0
PAID_LLM_REQUESTS = 0
QWEN2_5_CODER_7B_FACTOR_ADMISSION = FAIL
MODEL_REPLACEMENT_REQUIRED = YES
ALTERNATE_MODEL_DOWNLOADED = NO
```

## Validation and decision

The route mismatch fully explains the prior Markdown-fence parsing failure,
but it was not sufficient to admit the current model. With protocol behavior
corrected, the remaining blocker is factor-coding capability under the fixed
official benchmark. Another prompt/parser fix, extra retry, or autonomous
attempt is not authorized.

```text
LLM_BACKEND_TESTS = 8/8_PASS
BINDING_TESTS = 15/15_PASS
MATERIALIZER_TESTS = 5/5_PASS
TOTAL_RELEVANT_TESTS = 28/28_PASS
RESOURCE_RECOVERY = PASS
P3_RUN_NAMESPACE = p3-fin-quant-004
P3_RUN_004_ROOT_CREATED = NO
DVC_REPRO_EXECUTED = NO
RD_AGENT_RESEARCH_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
SEALED_OOS_ACCESSED = NO
NEXT_AUTONOMOUS_ATTEMPT_AUTHORIZED = NO
CURRENT_NEXT = P3_LOCAL_FACTOR_CODER_CANDIDATE_MODEL_BENCHMARK_001
FINAL_CLASSIFICATION = BLOCKED_CURRENT_MODEL_FACTOR_CAPABILITY_INSUFFICIENT
```
