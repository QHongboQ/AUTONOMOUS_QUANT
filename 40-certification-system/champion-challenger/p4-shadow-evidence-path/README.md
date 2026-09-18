# P4 Shadow evidence path

This directory contains one bounded DVC seal for the pre-2022,
zero-capital Qlib OnlineManager mechanism fixture. Microsoft Qlib owns model
training, rolling tasks, online model tags/history, predictions, Recorder,
MLflow integration, and SigAna RankIC. DVC owns dependency/output identity.

AQ owns only the closed `ShadowEvidenceV2` completeness and identity binding.
The seal neither computes RankIC nor implements an online model, scheduler,
state database, broker, backtest, lifecycle transition, or promotion engine.
