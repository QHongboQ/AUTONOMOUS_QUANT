# ARCH isolated deployment 001

**Task:** `AUTONOMOUS-QUANT-ARCH-ISOLATED-DEPLOYMENT-001`
**Result:** `PASS` — isolated Windows statistical-evidence runtime prepared; no P1 research or Certification orchestration started.

## Upstream pin and environment

| Item | Recorded value |
|---|---|
| Upstream | [`bashtage/arch`](https://github.com/bashtage/arch) |
| Upstream tag | `v8.0.0` |
| Upstream tag commit | `038d78b709e75f2590890757af32705817a6fad8` |
| Pinned release | `v8.0.0`, published 2025-10-21 |
| Installed package | `arch==8.0.0` |
| Environment | `D:\AQ_ENVS\arch` |
| Python | `3.12.14` (existing uv-managed CPython) |
| Python requirement | `>=3.10`; upstream metadata lists Python 3.10 through 3.13 |
| Windows support | upstream `pyproject.toml` explicitly classifies `Microsoft :: Windows` |
| Installation method | `uv venv --python 3.12 D:\AQ_ENVS\arch`; `uv pip install --python D:\AQ_ENVS\arch\Scripts\python.exe arch==8.0.0` |

No system Python, existing environment, optional documentation/test/development extra, or production source was changed.

## Dependency and license evidence

The pinned upstream declares runtime dependencies `numpy>=1.22.3,<3`, `pandas>=1.4.0`, `scipy>=1.8`, `statsmodels>=0.13.0`, and `packaging`. The resolved isolated package freeze is:

```text
arch==8.0.0
formulaic==1.2.2
interface-meta==2.0.1
narwhals==2.26.0
numpy==2.5.3
packaging==26.3
pandas==3.0.5
patsy==1.0.3
python-dateutil==2.9.0.post0
scipy==1.18.1
six==1.17.0
statsmodels==0.15.0
typing-extensions==4.16.0
tzdata==2026.3
wrapt==2.4.0
```

`uv pip check` passed for all 15 resolved packages. The exact `LICENSE.md` bytes at verified tag `v8.0.0` (`038d78b709e75f2590890757af32705817a6fad8`) have SHA-256 `c6e622bd89db4e13315f4e91605ff96fcbb9012d78ee74e429855870b203eed6`.

```text
UPSTREAM_TAG = v8.0.0
UPSTREAM_TAG_COMMIT = 038d78b709e75f2590890757af32705817a6fad8
LICENSE_IDENTIFIER = NCSA
LICENSE_CLASSIFICATION = PERMISSIVE
LICENSE_METADATA_NON_SPDX = YES
LICENSE_TEXT_PERMISSIVE = YES
LICENSE_PIN_REQUIREMENT = exact LICENSE.md text with selected version/commit
ARCH_LEGAL_BLOCKER = NO
```

## API validation

The isolated runtime imported `arch` and reported version `8.0.0`. These imports passed:

```python
from arch.bootstrap import (
    SPA,
    RealityCheck,
    StepM,
    MCS,
    IIDBootstrap,
    MovingBlockBootstrap,
    StationaryBootstrap,
)
```

All four multiple-comparison constructors expose an explicit keyword-only `seed` parameter. `SPA`, `RealityCheck`, and `StepM` accept benchmark/model loss inputs and bootstrap configuration; `MCS` accepts a loss matrix, test size, bootstrap configuration, and seed.

## Bounded synthetic smoke evidence

One local-only smoke program generated a fixed 48-observation benchmark loss vector and a 48×3 model-loss matrix with `numpy.random.default_rng(20260910)`. It used stationary bootstrap, block size `4`, `59` repetitions, and independent explicit seeds `811` through `814` for SPA, RealityCheck, StepM, and MCS respectively.

| Procedure | Result from deterministic synthetic test |
|---|---|
| SPA | completed; three returned p-values `[0.0, 0.0, 0.0]` |
| RealityCheck | completed; three returned p-values `[0.0, 0.0, 0.0]` |
| StepM | completed; `superior_models=['0']` |
| MCS | completed; `included=['1']`, `excluded=['0', '2', '3']` |
| Reproducibility | repeating the exact data and seeds produced identical result tuples for all four procedures |

These values demonstrate API execution and reproducibility only. The inputs are synthetic loss arrays, not market data or strategy research; the values have no profitability, model-selection, CertificationDecision, promotion, or trading interpretation. arch emitted statistical evidence in process-local objects only and did not mutate any project state.

## Isolation and non-actions

Before/after normalized freeze hashes confirmed no change to the existing Windows environments:

| Environment | Before SHA-256 | After SHA-256 | Result |
|---|---|---|---|
| `D:\AQ_ENVS\skfolio` | `7ac5cafe011551728c0433e5ae6dbd76c751a8a1c2a3900501f7bccde2cbe19b` | same | unchanged |
| `D:\AQ_ENVS\qlib` | `4a4beaca6ac3c1dae58fbedc2f1fe8c2ae4870f0ec2311f536efdb78a021f0ee` | same | unchanged |
| `D:\AQ_ENVS\openbb` | `bc7e569e27c384f12b56db2720f57972feaf1ade6f3cb16656223f5973fa13bf` | same | unchanged |
| `D:\AQ_ENVS\rdagent` | no Windows environment in this deployment target | not invoked or touched | unchanged by scope |

```text
CODE_CHANGED = NO
QLIB_EXECUTED = NO
RDAGENT_EXECUTED = NO
OPENBB_CALLED = NO
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_MINIMAL_QUANT
```
