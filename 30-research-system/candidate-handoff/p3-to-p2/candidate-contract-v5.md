# P3 Candidate-to-P2 Contract V5

V5 is the forward-only RD-Agent Candidate contract for the current native
DeepSeek route. It preserves V4 as a historical record and changes only the
versioned provider identity to `deepseek/deepseek-flash`. The P3 worker's
LiteLLM client remains `1.103.1`; the separate Proxy is pinned at `1.105.1`.
The embedding identity remains `ollama/qwen3-embedding:0.6b`.

V5 reuses the immutable V3 research, Qlib Recorder, dataset and P2 boundary
definitions. The schema does not issue Candidates or change the P2 protocol.
The existing V4 materializer continues to emit V4 and must not relabel a V4
artifact as V5. A V5 materializer is future work that must bind the actual
runtime and provider response evidence before it can produce a V5 record.

V5 Candidates remain subject to P2's independent eligibility decision. A V5
Candidate outside the frozen P2 cohort remains ineligible; this schema grants
no certification, spending, production or trading authority.
