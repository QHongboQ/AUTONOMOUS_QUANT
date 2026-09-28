# P3 Candidate-to-P2 Identity Contract V4

## Status and scope

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V4
CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
PRODUCER_NEUTRAL = YES
SUPPORTED_PRODUCER_KINDS = RD_AGENT; FORMULAIC_ALPHA
AQ_CUSTOM_CANONICALIZER = NO
AQ_CANDIDATE_REGISTRY = NO
```

V4 is a forward-only extension for future RD-Agent Candidates produced through
the DeepSeek cloud route. Candidate V1, V2, and V3 identities are immutable.
No Candidate is materialized, certified, ranked, or promoted by this contract
freeze.

The exact eight-field architecture and seven-field Candidate ID projection are
unchanged from V3. Candidate IDs remain SHA-256 over RFC 8785 JCS bytes using
the pinned upstream `rfc8785==0.1.4` implementation.

## Producer neutrality

The Formulaic Alpha branch reuses the complete immutable V3 research,
artifact, runtime, dataset, Recorder, and P2-boundary definitions. The
RD-Agent branch reuses the existing research, artifact, dataset, Recorder, and
P2-boundary definitions while replacing only the V2 local/chat runtime shape
with `rdAgentRuntimeIdentityV4`.

## RD-Agent DeepSeek runtime identity

Future RD-Agent V4 Candidates bind:

- pinned RD-Agent source, installed wheel, and environment identities;
- pinned Qlib source identity;
- LiteLLM `1.100.1`;
- the DVC-bound LLM configuration identity;
- the native RD-Agent trace identity and exact call count;
- `provider = deepseek`;
- `requested_model = deepseek/deepseek-flash`;
- the response/resolved model string returned by the provider;
- `reasoning_mode = THINKING_ENABLED`;
- `reasoning_effort = high`;
- `max_output_tokens = 65536`;
- the unchanged Qlib Recorder, serialized model, prediction, dataset/PIT, and
  P2 eligibility identities already owned by the existing contract;
- the separately owned local embedding identity and epoch until an independent
  embedding migration is completed.

The route is `DEEPSEEK_ONLY`; fallback and fallback reason entries are
structurally forbidden. API keys, secret paths, balances, performance metrics,
scores, rankings, runtime durations, and host identities remain outside the
Candidate ID.

## Ownership

```text
DEEPSEEK = UPSTREAM_WHOLE
LITELLM = UPSTREAM_LEAF
RD_AGENT = UPSTREAM_WHOLE
QLIB = UPSTREAM_WHOLE
RFC8785 = UPSTREAM_LEAF
AQ_CUSTOM_LLM_BACKEND_COUNT = 0
AQ_CUSTOM_CANONICALIZER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```
