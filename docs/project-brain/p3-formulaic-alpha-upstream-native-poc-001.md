# P3 Formulaic Alpha Upstream Native POC 001

## Scope

This task evaluated the three frozen upstream projects through their native
interfaces only:

- AlphaGen at `259687e8f316994426416c530a94842a2fe6405e`;
- AlphaForge at `d0cfc27df23c60f271bc885fd43027b86b787746`;
- AlphaGPT at `e0eddaf4218a04dee1edc98255415c6090f2a849`.

No upstream source was modified. No AQ adapter, AQ PIT data, RD-Agent, Ollama,
training workaround, or source-path patch was used.

Private evidence is frozen under:

`D:\AQ_DATA\P3\formulaic-alpha-upstream-native-poc-001`

The canonical summary SHA-256 is:

`4d7d0603682fa3915615a5b9f7af12011dd2550f5c46924b9ecb704bd5b84773`

## AlphaGen

The fresh `aq-alphagen-upstream-guidance` environment follows the upstream
maintainer guidance in Issue #15 and merged PR #16:

- current source uses Gymnasium;
- legacy Gym was uninstalled;
- a higher available Qlib version is permitted;
- the stale NumPy 1.20.1 pin was not forced.

Resolved key versions are Python 3.10.21, pyqlib 0.9.7, NumPy 1.26.4,
Gymnasium 0.28.1, stable-baselines3 2.0.0, sb3-contrib 2.0.0, and Torch
2.0.1+cu117. Required imports and `python -m scripts.rl -h` pass. CUDA sees
the NVIDIA GeForce RTX 3060 Laptop GPU.

The environment does not pass `pip check` because pyqlib 0.9.7 still declares
legacy `gym` in its package metadata while the AlphaGen maintainer explicitly
instructs users to uninstall Gym. Installing Gym merely to silence metadata
would contradict the selected upstream authority.

The native data path is also not bounded. It requires Qlib CN metadata, then
enumerates the full A-share universe plus four indices and retrieves each
security from its IPO date through the provider's latest date. The script has
no official instrument/date subset parameters. This represents thousands of
securities, roughly 1990 through 2026 depending on IPO date, and an estimated
multi-GB footprint across pickle, CSV, and Qlib binary copies. No download was
started.

Classification:

`ALPHAGEN_NATIVE_POC = BLOCKED_UNBOUNDED_OFFICIAL_DATA_PREPARATION`

## AlphaForge

The fresh `aq-alphaforge-readme-poc` environment tested the README path rather
than fabricating the nonexistent `baostock==00.8.90` release. Public Baostock
resolved to distribution 0.9.3 (module version `00.9.30`), and current pyqlib
resolved to 0.9.7. Imports and the `train_AFF.py` and `combine_AFF.py` help
paths pass after installing the source's direct TensorBoard dependency.

The native training stack remains unreconciled:

- stable-baselines3 1.8.0 requires Gym 0.21.0, whose published source fails
  modern package construction because of invalid `extras_require` metadata;
- the current index does not provide the upstream-stated pyqlib 0.9.0;
- the fixed upstream NumPy 1.24.3 conflicts with current Qlib's installed
  `skops` requirement of NumPy 1.25 or newer;
- Torch 1.13.0+cu117 does not expose CUDA in this environment;
- `gan/utils/data.py` retains the literal `path/for/qlib`, and the README
  instructs the user to modify source to configure it.

The task contract prohibits that source edit and any AQ data adaptation.

Classification:

`ALPHAFORGE_NATIVE_POC = BLOCKED_DEPENDENCY_AND_DOCUMENTED_SOURCE_CONFIGURATION`

## AlphaGPT

The existing `aq-alphagpt-native` environment remains healthy:

- Python 3.11.16;
- `pip check` passes;
- `run_daily.py --help` passes;
- Torch 2.14.0+cu130 sees the NVIDIA GPU.

No real `TUSHARE_TOKEN` is present in the process environment, Windows process
environment, repository `.env`, or Conda environment variables. The token was
not fabricated or printed. Therefore no data request was made.

The native trainer also fixes `TRAIN_STEPS = 100000` in source with no CLI
override; source was not changed to create a bounded run.

Classification:

`ALPHAGPT_NATIVE_POC = READY_FOR_NATIVE_POC_PENDING_CREDENTIAL`

## Decision

No project produced a native formulaic-alpha artifact in this task. This is an
honest upstream-native boundary result, not permission to create an AQ adapter
or patch upstream source.

```text
UPSTREAM_SOURCE_MODIFIED = NO
AQ_ADAPTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NATIVE_ALPHA_GENERATION_EXECUTED = NO
NATIVE_ALPHA_ARTIFACTS_PRODUCED = 0
PERMANENT_UPSTREAM_AUTHORITY_SELECTED = NO
RD_AGENT_LOCAL_BRAIN_SEARCH = PAUSED_NOT_P3_BLOCKER
AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
CURRENT_NEXT = P3_FORMULAIC_ALPHA_UPSTREAM_BLOCKER_CLOSEOUT_001
```
