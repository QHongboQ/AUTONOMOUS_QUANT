# P3 Official Upstream Thin Runtime Consolidation 001

## Current authority

P3 composes immutable official upstreams without an AQ research-loop or LLM
implementation:

```text
DeepSeek -> LiteLLM -> Microsoft RD-Agent -> Microsoft Qlib -> AQ Candidate handoff -> P2
AQ US/PIT configuration boundary -> AlphaGen -> Microsoft Qlib -> AQ Candidate handoff -> P2
```

```text
RD_AGENT = UPSTREAM_WHOLE
QLIB = UPSTREAM_WHOLE
ALPHAGEN = UPSTREAM_WHOLE
LITELLM = UPSTREAM_LEAF
DEEPSEEK = EXTERNAL_LLM_PROVIDER
AQ = THIN_INTERFACE_ONLY
RD2BENCH = DIAGNOSTIC_EVIDENCE_ONLY
```

The only active RD-Agent US binding is
`aq_rdagent_official_us_binding.py`. It delegates experiment conversion to the
official RD-Agent implementation and selects only the US/PIT Qlib template
overlays. RD-Agent continues to own scenarios, prompts, runners, CoSTEER,
recorders, coding, research-loop behavior, and feedback.

`aq_rdagent_official_us_factor_source.py` is not an active RD-Agent binding
or research-loop component. It preserves the separate AQ-owned one-time
US/PIT evidence-to-`daily_pv.h5` projection needed to reproduce the frozen
FactorCoSTEER input. It performs no factor search, model evaluation, benchmark
admission, or runtime selection.

The authoritative P3 DVC stage is a declarative reproducibility definition;
it does not launch the P3 runtime. The only authorized research path starts
the official `rdagent fin_quant --loop-n N` directly in the WSL-native clean
AQ checkout, with `rdagent.oai.backend.LiteLLMAPIBackend`,
`deepseek/deepseek-flash`, `reasoning_effort=high`, no model fallback, and a
separately owned native LiteLLM/Ollama embedding route. After a completed
immutable run, DVC records reproducibility through `dvc commit --force` and
`dvc exp save`; it does not start RD-Agent. Secrets remain process-bound and
outside Git. The historical local-Ollama chat backend and the superseded
RD2Bench admission framing are not active runtime authority. The normative
post-run procedure is frozen in
[P3 Direct Runtime and Post-Run DVC Experiment Authority Freeze 001](p3-direct-runtime-postrun-dvc-experiment-authority-freeze-001.md).

P2 sealed OOS remains prohibited for P3 runtime integration smokes.
