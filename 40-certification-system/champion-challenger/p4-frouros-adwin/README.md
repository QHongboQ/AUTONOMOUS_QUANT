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
that math. This deployment contains no Qlib adapter, financial-decay policy,
lifecycle policy, workflow engine, metric engine, or state database.

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

The next authorized task is the bounded evidence adapter. It may validate and
translate approved metric observations, call the public upstream ADWIN API,
and emit immutable detector evidence. It may not implement detector math or
financial/lifecycle policy.
