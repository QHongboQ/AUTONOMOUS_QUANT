# P4 Frouros ADWIN upstream leaf

This directory freezes the only new upstream selected by the P4 residual
capability substitution audit:

```text
PROJECT = IFCA-Advanced-Computing/frouros
PACKAGE = frouros
VERSION = 0.9.0
MODULE = frouros.detectors.concept_drift.streaming.window_based.ADWIN
RUNTIME = ISOLATED_PYTHON_3_10_21
ENVIRONMENT = /home/zhou/AQ_ENVS/p4-frouros-adwin
```

Frouros owns ADWIN detector math. AQ must not copy, patch, fork, or reimplement
that math. The adjacent V1 adapter is bounded glue only: it validates one
explicit Qlib RankIC artifact, emits a neutral immutable observation stream,
records the audited `+1.0` translation, calls public Frouros ADWIN, and emits
detector evidence. It contains no financial-decay policy, lifecycle policy,
workflow engine, metric engine, or state database.

## Reproduction boundary

Create a new isolated environment; never install this lock into the Qlib,
RD-Agent, AlphaGen, DVC, or MLflow authority environments:

```bash
/home/zhou/.local/bin/uv venv \
  --python 3.10.21 \
  --seed \
  /home/zhou/AQ_ENVS/p4-frouros-adwin

/home/zhou/.local/bin/uv pip install \
  --python /home/zhou/AQ_ENVS/p4-frouros-adwin/bin/python \
  -r /mnt/d/AUTONOMOUS_QUANT/40-certification-system/champion-challenger/p4-frouros-adwin/requirements.lock

/home/zhou/AQ_ENVS/p4-frouros-adwin/bin/python -m pip check
```

The accepted deployment used the official PyPI wheel
`frouros-0.9.0-py3-none-any.whl`, SHA-256
`0c88ddeccfe2ac1f105b44efcfc65ba5b879cd8a07e492139c4316677b708980`.
The audited upstream release-source commit is
`2484916fe0ba50dd2f28bbf1899f2ef3e499df31`. This records release provenance;
it does not claim byte identity between the installed wheel and Git checkout.

## Accepted runtime facts

- public `ADWIN` and `ADWINConfig` imports pass;
- a negative input from zero raises the upstream `ValueError` because total
  must remain non-negative;
- a constant additive translation produced identical full drift sequences in
  all five frozen synthetic cases;
- the exact prior Frouros POC outcomes replayed;
- fresh, reset, and preserved Python-pickle replay passed;
- no historical TEST or sealed OOS data was accessed.

Private deployment evidence is rooted at:

```text
D:/AQ_DATA/P4/selected-upstream-components-deployment-001/
```

## RankIC-only evidence adapter

The V1 boundary is intentionally closed:

```text
explicit Qlib sig_analysis/ric.pkl
  -> MetricObservationStreamV1 exact bytes + SHA-256
  -> RankIC x + 1.0
  -> Frouros 0.9.0 public ADWIN
  -> DetectorEvidenceV1 exact bytes + SHA-256
```

Run the exporter only in the authoritative Qlib environment:

```bash
/home/zhou/miniforge3/envs/rdagent4qlib/bin/python \
  adapter/export_rank_ic.py \
  --input /explicit/recorder/path/sig_analysis/ric.pkl \
  --output /explicit/evidence/path/metric-observations-v1.json
```

Then pass the exact observation-file SHA-256 to the isolated Frouros runner:

```bash
/home/zhou/AQ_ENVS/p4-frouros-adwin/bin/python \
  adapter/run_adwin.py \
  --input /explicit/evidence/path/metric-observations-v1.json \
  --input-sha256 <lowercase-sha256> \
  --output /explicit/evidence/path/detector-evidence-v1.json
```

Both outputs are write-once. V1 rejects missing/non-finite/out-of-domain
observations, unordered or duplicate timestamps, unsupported metrics,
translation changes, and runtime identity mismatches. Detector state is
recreated by replaying the immutable ordered observations; pickle is not an
authority. The JSON encoding is deterministic exact-byte serialization and
makes no RFC 8785 semantic-canonical identity claim.

The next task may project the two evidence identities to real Qlib Recorder,
MLflow, and DVC identities. It may not change detector or financial/lifecycle
policy semantics.
