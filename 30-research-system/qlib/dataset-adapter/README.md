# Qlib DatasetSnapshot adapter

This replaceable research leaf converts the public AQ PIT DatasetSnapshot into
Qlib's documented local instrument-membership representation: tab-separated
`instrument`, inclusive start date, and inclusive end date. AQ's source episode
ID remains in a parallel deterministic map; repeated ticker episodes remain
separate Qlib spans and are never stitched across a membership gap.

The accepted runtime is the existing WSL `rdagent4qlib` environment: Qlib
`0.9.8.dev26` from pinned source commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`. Windows Qlib `0.9.7` remains
historical deployment evidence and is not this consumer authority.

The leaf relies on public Qlib surfaces: `qlib.init`, `qlib.data.D.instruments`,
`D.list_instruments`, `DatasetH`, `Alpha158`, `qlib.workflow.R`,
`TopkDropoutStrategy`, `qlib.backtest.backtest`, and `PortAnaRecord`. The small
synthetic probe verifies discovery and dynamic ranges only. No real data,
Alpha158 execution, training, prediction, strategy run, backtest, or performance
claim occurs.

Qlib owns future Dataset/handler, feature, model workflow, recorder, prediction,
Top-K, backtest, transaction-cost, and portfolio-analysis machinery. AQ owns
only this conversion boundary. The adapter reads no PIT source/compiler/facts,
imports no DVC runtime, and does not mutate DatasetSnapshot input.
