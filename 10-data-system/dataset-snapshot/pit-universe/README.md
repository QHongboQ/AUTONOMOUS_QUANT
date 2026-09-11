# PIT universe DatasetSnapshot

This leaf owns the immutable downstream representation of the public P1
`ResearchReadyUniverse`. It emits deterministic UTF-8 JSONL rows with exactly
four fields: `episode_id`, `ticker`, `membership_from`, and `membership_to`.
The adjacent JSON metadata records only the logical schema/universe identity,
coverage, row count, and `RESEARCH_READY` publication state.

It does not own PIT membership/identity truth, DVC cache or pipeline behavior,
calendar semantics, source evidence, market data, Qlib conversion, or P2
certification. DVC tracks the files externally through the repository pipeline;
no DVC Python object crosses this contract.
