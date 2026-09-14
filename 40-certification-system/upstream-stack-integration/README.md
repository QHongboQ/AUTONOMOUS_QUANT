# P2 upstream certification stack integration

This leaf contains bounded integration probes only. Each probe invokes a
selected upstream through its public interface and writes private evidence
outside Git. It is not a certification engine and contains no CV, statistics,
backtest, experiment-database, data, optimizer, bootstrap, or promotion engine.

The fixed flow is:

```text
P2 Qlib local provider
  -> Qlib DatasetH / Alpha158 / LGBModel / prediction
  -> Qlib Recorder backed by MLflowExpManager
  -> skfolio WalkForward / CombinatorialPurgedCV
  -> arch SPA / RealityCheck / StepM / MCS
  -> DVC dependency and evidence hashes
```

Pandera and exchange_calendars are validation authorities around the handoff.
Their probes are retained here, but this task does not provision a missing
runtime. AQ policy remains outside these upstream-owned algorithms.

Private task evidence belongs under
`D:\AQ_DATA\P2\upstream-certification-stack-integration-001`. The DVC stage
tracks hashes for the accepted provider report and private integration reports;
the small generated seal remains a DVC output and is ignored by Git.
