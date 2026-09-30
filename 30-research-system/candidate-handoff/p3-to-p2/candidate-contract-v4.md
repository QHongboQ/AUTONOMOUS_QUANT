# P3 Candidate-to-P2 Contract V4

V4 is the versioned P3-to-P2 handoff interface for the official RD-Agent
1.0.0 native runtime.  It retains V3's eight top-level fields and RFC8785
JCS/SHA-256 Candidate identifier over the seven non-ID fields.  V1, V2, V3,
their hashes, the 17 Formulaic Alpha V3 candidates, and P2 protocols remain
immutable historical authorities.

## Producer branches

`RD_AGENT` uses the V1 research identity because hypothesis, task, generated
code, parent-lineage, and feedback semantics did not change.  It binds the
official RD-Agent `1.0.0` release SHA `484776c211e4fbbeef03e0ec00d6bbee7362a4f4`,
Qlib `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`, and the native
`LiteLLMAPIBackend` route.  The chat provider is explicitly `deepseek`; an
OpenAI-compatible wire protocol is not a provider identity.

`FORMULAIC_ALPHA` references the V3 Formulaic definitions without semantic
change.  Existing V3 instances remain V3 and are not reissued under V4.

## Runtime and embedding evidence

The RD-Agent route is `deepseek/deepseek-chat` with `CLOUD_ONLY` chat and
LiteLLM `1.103.1`.  The configured embedding route is separately bound as
`ollama/qwen3-embedding:0.6b`.  `embedding_execution.executed: false` is a
truthful valid state: it records configuration without inventing an embedding
call, digest, or dimensionality.  Executed embeddings require their own call,
dimension, and provider-model evidence.

## Recorder and reproducibility boundary

Qlib/MLflow owns the Recorder.  A RD-Agent Candidate requires a `FINISHED`
Recorder with exact experiment and run IDs plus `task`, `params.pkl`,
`dataset`, and `pred.pkl`.  The materializer only hashes the native artifact
bytes; it does not serialize a model or operate Qlib.

DVC is optional post-run sealing evidence.  It is not a `fin_quant` launcher
and V4 does not require the retired `p3_rdagent_us_quant_research` stage.

## P2 boundary

V4 records provenance only.  A new RD-Agent V4 Candidate is
`INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION`; P3 cannot certify, edit a P2
protocol, promote to production, or access sealed OOS.
