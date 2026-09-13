# Qlib research-data handoff

This replaceable research leaf provides two thin handoffs into Qlib. The
original DatasetSnapshot adapter converts public PIT membership into Qlib's
documented instrument-range representation. The P2 ragged-panel adapter stages
the frozen private Quantiacs/SimFin observations as CSV and delegates final
binary serialization to Qlib's pinned upstream `scripts/dump_bin.py`.

P2 instrument IDs derive only from `security_identity`; historical ticker is
metadata. The handoff preserves all 745 accepted membership ranges across 730
security identities. Each of the 1,267,963 required member sessions contains
either accepted OHLCV or NaN. Missing observations never remove membership or
an entire year, and their reason remains in a private availability sidecar.

The accepted runtime is the existing WSL `rdagent4qlib` environment: Qlib
`0.9.8.dev26` from pinned source commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`. Windows Qlib `0.9.7` remains
historical deployment evidence and is not this consumer authority.

The leaf relies on public Qlib surfaces: `qlib.init`, `qlib.data.D.instruments`,
`D.list_instruments`, `DatasetH`, `Alpha158DL`, `DropnaLabel`, `LGBModel`,
`Exchange`, `qlib.workflow.R`, `TopkDropoutStrategy`, `qlib.backtest.backtest`,
and `PortAnaRecord`. `RaggedAlpha158` is configuration only: upstream
Alpha158DL owns all feature/operator formulas, with VWAP excluded because the
frozen source contract supplies only open/high/low/close/volume.

Pure conversion tests construct small temporary inputs and run without private
data. The real P2 probe runs against the private generated provider in the
existing WSL `rdagent4qlib` environment. It verifies DatasetH, 157 upstream
Alpha158-compatible features, ExpressionDFilter exclusion of current-session
NaN-close samples from inference/training, native DropnaLabel exclusion of
unavailable future labels from learning, a bounded LightGBM fit/prediction, and
Qlib Exchange suspension for a NaN close. The 20,671 trainable-label count is
only for this deterministic smoke cohort, not the full P2 panel. This is an
integration proof, not a certification or performance claim.

Qlib owns Dataset/handler, feature, model workflow, recorder, prediction,
Top-K, exchange, backtest, transaction-cost, and portfolio-analysis machinery.
AQ owns PIT membership, stable security identity, declarative provider-binding
facts, and this thin staging/configuration boundary. No provider API, provider
router, generic data engine, or identity lookup runs during research.

Private build outputs belong under
`D:\AQ_DATA\P2\qlib-native-ragged-panel-001`; no provider rows, Qlib binaries,
models, predictions, or MLflow artifacts belong in Git.
