# P5 filing features

This leaf materializes only the five deterministic filing features frozen by
`p5-filing-intelligence-deterministic-feature-policy-001`. EdgarTools owns the
native filing/report/attachment interfaces, `exchange_calendars` owns XNYS
schedule semantics, and the existing `effective_session` policy owns PIT
availability. AQ owns only the exact scalar definitions and the immutable
`FilingFeatureObservationV1` projection.

The module performs no SEC retrieval, parsing, attachment classification,
storage, registration, factor execution, or generic transformation. Missing
values remain explicit and original/amended accessions remain separate.
