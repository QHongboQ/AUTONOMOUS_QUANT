# P0 Upstream Batch Deployment 001

> Status: **CORE SET RECORDED WITH BLOCKERS AND DEFERRED CANDIDATES**
>
> Task: `AUTONOMOUS-QUANT-P0-UPSTREAM-BATCH-DEPLOYMENT-001`
>
> Date: 2026-09-09

## 1. Authority and baseline

- Authoritative repository: `D:\AUTONOMOUS_QUANT`
- Baseline verified after `git fetch origin --prune`: `origin/main` = `42405b20f11feaf15a02e055baffe7ea4190e46c`
- Local `main` matched that SHA and was clean before branch creation.
- Task branch: `agent/p0-upstream-batch-deployment-001`
- `AGENTS.md`: not present.
- Read-first documents: `docs/project-brain/README.md` and `docs/project-brain/p0-upstream-fit-audit.md`.

### Historical deployment record

Earlier staging evidence was collected under a prior deployment policy that no longer governs P0. The authoritative sequence is now deployment staging, then Interface Audit, then functional POCs. The current state is recorded in the later addenda; the initial observations remain as historical evidence only.

## 2. Machine preflight

| Item | Observed value |
|---|---|
| OS | Microsoft Windows 11 Pro 10.0.26200 (build 26200) |
| PowerShell | 7.6.5 |
| CPU | Intel Core i7-10870H @ 2.20 GHz |
| RAM | 15.77 GiB |
| GPU | NVIDIA GeForce RTX 3060 Laptop GPU; Intel UHD Graphics; StarDesk Virtual Display Adapter |
| D: free before | 275.45 GiB (295,762,194,432 bytes) |
| D: free after | 274.58 GiB (294,824,898,560 bytes) |
| Git | 2.55.0.windows.4 |
| Git LFS | 3.7.1 |
| Python launchers | CPython 3.13.15; uv-managed CPython 3.12.14 |
| uv | 0.12.9 |
| .NET SDK | none detected |
| .NET runtimes | Microsoft.NETCore.App 9.0.7; Microsoft.WindowsDesktop.App 9.0.7 |
| WSL | unavailable; no distributions installed |
| Docker | unavailable (`docker` not found) |

## 3. Initial local layout and storage snapshot

All third-party content is outside the authoritative repository.

| Path | Post-deployment size |
|---|---:|
| `D:\AUTONOMOUS_QUANT` | 93,821 bytes before documentation update |
| `D:\AQ_UPSTREAM\qlib` | 19,497,995 bytes |
| `D:\AQ_ENVS\qlib` | 761,540,605 bytes |
| `D:\AQ_DATA` | empty |
| `D:\AQ_CACHE\uv` | 784,858,180 bytes |
| `D:\AQ_CACHE\pip` | empty |
| `D:\AQ_CACHE\huggingface` | empty |
| `D:\AQ_CACHE\torch` | empty |

`D:\AQ_UPSTREAM`, `D:\AQ_ENVS`, `D:\AQ_DATA`, and `D:\AQ_CACHE` were created as contract roots. The cache was absent at baseline, so the listed uv cache is attributable to this Qlib deployment. No data or model-artifact root contains downloaded data or weights.

## 4. Official-source check

Qlib was validated against the [Microsoft Qlib repository](https://github.com/microsoft/qlib) and its current [installation guidance](https://github.com/microsoft/qlib/blob/main/README.md). The current project metadata declares Python `>=3.8`; the README documents Python 3.8 through 3.12 and both package and source installation paths. Python 3.12.14 was selected from an existing local uv interpreter.

## 5. Initial deployment result matrix (superseded by section 9)

| Upstream | Source | Environment | Install | Health | SHA/version | Disk | Classification |
|---|---|---|---|---|---|---|---|
| Qlib | `D:\AQ_UPSTREAM\qlib` | `D:\AQ_ENVS\qlib` | Official package fallback installed after source-build attempt | `import qlib`; `python -m qlib.cli.run --help` passed | source `79633dd9506ea689e5400dea0197717b5b3d74b7` / package `pyqlib 0.9.7` | source 19,497,995 B; env 761,540,605 B | PASS_WITH_WARNING |
| RD-Agent | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| skfolio | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| OpenBB | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| FinRL-X | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| LEAN | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| Robinhood MCP | no local artifact assessed | no environment | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| TradingAgents | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| FinGPT | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| FinBERT | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |
| AlphaGen | not deployed | not deployed | pending under prior staging policy | not run | not recorded | 0 B | HISTORICAL_SNAPSHOT |

## 6. Qlib detail

- Remote: `https://github.com/microsoft/qlib.git`
- Default branch: `origin/main`; checked-out branch: `main`
- Source HEAD: `79633dd9506ea689e5400dea0197717b5b3d74b7`
- Tracked upstream worktree dirty: **NO**
- Environment interpreter: Python 3.12.14
- Installed package: `pyqlib 0.9.7`
- Source-install command attempted: `uv pip install --python D:\AQ_ENVS\qlib\Scripts\python.exe .`
- Source-install result: blocked while building `qlib.data._libs.rolling`; the build backend reported that Microsoft Visual C++ 14.0 or later is required. No compiler was installed and no upstream source was modified.
- Official package fallback command: `uv pip install --python D:\AQ_ENVS\qlib\Scripts\python.exe pyqlib`
- Health command: `D:\AQ_ENVS\qlib\Scripts\python.exe -c "import qlib; print(qlib.__version__)"` and `D:\AQ_ENVS\qlib\Scripts\python.exe -m qlib.cli.run --help`
- Health result: passed; Qlib reports version `0.9.7` and the CLI displayed usage.

## 7. Explicit non-actions

- No Qlib dataset, market history, tick data, order-book data, news archive, or model weights were downloaded.
- No training, backtest, Alpha158 workflow, model tournament, portfolio experiment, Interface Audit, P1 work, paper trading, live trading, broker authentication, or Robinhood order was performed.
- No Windows Service, Scheduled Task, startup entry, daemon, Nomad, QuestDB, database server, WSL, Docker, CUDA toolkit, global Python dependency, machine PATH edit, or persistent environment variable was created.
- No API keys, tokens, credentials, or secrets were requested or written.
- No upstream tracked source was modified.

## 8. Initial readiness and next-gate statement (superseded)

Qlib's lightweight deployment health is recorded, with the source-build C++ compiler prerequisite documented. It is **not** a completed functional POC and does not authorize P1.

The owner subsequently updated the P0 sequence to deployment staging, Interface Audit, then functional POCs, and then stopped further installation and repair work. At this historical stop, P0 Interface Audit was **NOT STARTED**.

## 9. Strategy-update addendum — exact state at stop

### Current upstream tiers

| Tier | Candidates |
|---|---|
| Core | Qlib, RD-Agent, skfolio, OpenBB, Robinhood MCP |
| Challenger / fallback | FinRL-X, LEAN |
| Deferred | TradingAgents, FinGPT, FinBERT, AlphaGen |

### Exact local disk state

| Path | Size |
|---|---:|
| `D:\AQ_UPSTREAM` | 760,882,712 B |
| `D:\AQ_ENVS` | 2,384,160,172 B |
| `D:\AQ_DATA` | empty |
| `D:\AQ_CACHE` | 2,006,596,623 B |
| `D:\AQ_CACHE\uv` | 2,006,596,519 B |
| `D:\AQ_CACHE\huggingface` | empty |
| `D:\AQ_CACHE\openbb-home` | 104 B |
| D: free space | 272.57 GiB (292,667,248,640 B) |

`D:\AQ_CACHE\openbb-home` contains only OpenBB's non-secret local settings. No model weights or datasets were downloaded.

### Exact source and environment state

| Upstream | Tier | Source state | Environment state | Health / blocker | Classification |
|---|---|---|---|---|---|
| Qlib | Core | `main` `79633dd9506ea689e5400dea0197717b5b3d74b7`; 19,497,995 B | `D:\AQ_ENVS\qlib`, Python 3.12.14, 761,540,605 B | `pyqlib 0.9.7`; import and CLI help pass. Source build requires C++ Build Tools. | PASS_WITH_WARNING |
| RD-Agent | Core | `main` `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd`; 24,266,102 B | none | Official Linux/Docker requirement recorded. No WSL, Docker, install, or repair attempted. | BLOCKED_PLATFORM_PREREQUISITE |
| skfolio | Core | package-only | `D:\AQ_ENVS\skfolio`, Python 3.12.14, 268,156,796 B | `skfolio 1.0.6`; WalkForward, CombinatorialPurgedCV, and MeanRisk imports pass. | PASS |
| OpenBB | Core | package-only | `D:\AQ_ENVS\openbb`, Python 3.12.14, 196,714,954 B | `openbb 4.7.2`; `from openbb import obb` passes with isolated settings; no provider credentials. | PASS_WITH_WARNING |
| Robinhood MCP | Core | existing Codex connector configuration | none | Configured connector recorded; authentication and account access were not assessed, and no trading action occurred. | CONNECTOR_CONFIGURED |
| FinRL-X | Challenger | `master` `e65d6f0483ead7d2ef4a5fc940cdf960392a25c1`; 138,977,891 B | `D:\AQ_ENVS\finrlx`, Python 3.12.14, 551,702 B | Source install resolver found declared `finnhub>=2.4.19` unsatisfiable. No repair attempted. | UPSTREAM_BROKEN |
| LEAN | Challenger | `master` `01215376568960c912c1296de26b5a8005d6a525`; 531,493,516 B | none | No .NET SDK and no Docker. No installation or repair attempted. | BLOCKED_PLATFORM_PREREQUISITE |
| TradingAgents | Deferred | `main` `be952b8eccb49720509af544c6675233bc1f10d0`; 9,013,510 B | `D:\AQ_ENVS\tradingagents`, Python 3.13.15, 226,503,862 B | Installed before deferral; import and CLI help pass. No LLM/data API call. | DEFERRED_BY_STRATEGY |
| FinGPT | Deferred | `master` `781a7c020da977092f2f2c4916024a412c5e3801`; 36,202,502 B | `D:\AQ_ENVS\fingpt`, Python 3.11.16, 929,477,285 B | Installed before deferral; package, Transformers, and CPU PyTorch imports pass. No model or inference run. | DEFERRED_LARGE_ARTIFACT |
| FinBERT | Deferred | `master` `44995e0c5870c4ab37a189d756550654ae87cdf0`; 197,891 B | none | Official environment locks Python 3.7; no supported local runtime. No installation or repair attempted. | DEFERRED_BY_STRATEGY |
| AlphaGen | Deferred | `master` `259687e8f316994426416c530a94842a2fe6405e`; 1,233,305 B | `D:\AQ_ENVS\alphagen`, Python 3.8.20, 1,214,968 B | Environment and non-writing syntax scan completed before deferral. Locked requirements are unsatisfiable: stable-baselines3 2.0.0 requires NumPy >=1.21 while source pins 1.20.1. No repair attempted. | DEFERRED_BY_STRATEGY |

### Created directories and safety state

- Source clones present: `qlib`, `rd-agent`, `finrl-x`, `lean`, `tradingagents`, `fingpt`, `finbert`, `alphagen` under `D:\AQ_UPSTREAM`.
- Environments present: `qlib`, `skfolio`, `openbb`, `finrlx`, `tradingagents`, `fingpt`, `alphagen` under `D:\AQ_ENVS`.
- No source checkout exists for package-distributed skfolio or OpenBB; Robinhood MCP has no local-source requirement.
- All existing upstream tracked worktrees are clean. No created source clone or environment was deleted.
- No further installation or repair work occurred after the stop instruction.
- At this historical stop, Interface Audit and P1 were **NOT STARTED**. No services, scheduled tasks, startup entries, datasets, model weights, credentials, broker authentication, paper trading, or live trading were created or performed.

## 10. Lab prune 001 — final local state

On 2026-09-09, `AUTONOMOUS-QUANT-P0-LAB-PRUNE-001` performed deterministic cleanup only. Before deletion, the four removed upstream worktrees were verified clean, and all removed-source SHA and blocker evidence was confirmed present in this document.

### Removed environments

- `D:\AQ_ENVS\finrlx`
- `D:\AQ_ENVS\tradingagents`
- `D:\AQ_ENVS\fingpt`
- `D:\AQ_ENVS\alphagen`

### Removed deferred source clones

- `D:\AQ_UPSTREAM\tradingagents` — recorded SHA `be952b8eccb49720509af544c6675233bc1f10d0`
- `D:\AQ_UPSTREAM\fingpt` — recorded SHA `781a7c020da977092f2f2c4916024a412c5e3801`
- `D:\AQ_UPSTREAM\finbert` — recorded SHA `44995e0c5870c4ab37a189d756550654ae87cdf0`
- `D:\AQ_UPSTREAM\alphagen` — recorded SHA `259687e8f316994426416c530a94842a2fe6405e`

`D:\AQ_CACHE` and `D:\AQ_DATA` were not deleted. The existing Robinhood MCP configuration was not read or modified.

### Robinhood connector record

```text
CONNECTOR_CONFIGURED = YES
AUTH_STATE = NOT_ASSESSED_IN_THIS_TASK
ACCOUNT_ACCESS = NOT_PERFORMED
TRADING_ACTION = NONE
```

### Final directory whitelist

| Root | Final directories |
|---|---|
| `D:\AQ_UPSTREAM` | `finrl-x`, `lean`, `qlib`, `rd-agent` |
| `D:\AQ_ENVS` | `openbb`, `qlib`, `skfolio` |

### Retained health checks

| Component | Command / result |
|---|---|
| Qlib | `import qlib` reported `0.9.7`; `python -m qlib.cli.run --help` passed. |
| skfolio | `import skfolio` reported `1.0.6`; `WalkForward`, `CombinatorialPurgedCV`, and `MeanRisk` imports passed. |
| OpenBB | `from openbb import obb` passed with its isolated cache home; package version `4.7.2`, root object `App`. |

### Final resource and persistence audit

- `D:\AQ_CACHE`: 2,006,596,623 B
- D: free space: 292,768,395,264 B (272.66 GiB)
- Active uv/pip installer processes: **NONE**
- AQ Windows services: **NONE**
- AQ scheduled tasks: **NONE**
- AQ startup entries: **NONE**
- Machine/user PATH entries beginning `D:\AQ`: **NONE**

No installation, Interface Audit, P1 work, PR merge, scheduled work, service, startup entry, broker authentication, paper trading, or live trading was performed during this cleanup.

## 11. RD-Agent WSL deployment 001 — runtime staging

On 2026-09-09, `AUTONOMOUS-QUANT-P0-RDAGENT-WSL-DEPLOYMENT-001` staged a separate Linux runtime in the WSL distribution filesystem. This supersedes only the historical RD-Agent Windows-runtime status in section 9; the historical Windows clone is retained and unmodified.

### WSL runtime and source evidence

| Item | Recorded state |
|---|---|
| Distribution | `Ubuntu-24.04`, Ubuntu 24.04.4 LTS, WSL 2 |
| Linux user / home | `zhou` / `/home/zhou` |
| Linux layout | `/home/zhou/AQ_UPSTREAM`, `/home/zhou/AQ_ENVS`, `/home/zhou/AQ_CACHE` |
| RD-Agent source | `/home/zhou/AQ_UPSTREAM/rd-agent` |
| Remote / default branch | `https://github.com/microsoft/RD-Agent.git` / `main` |
| Linux source HEAD / worktree | `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` / clean |
| Windows retained source HEAD | `D:\AQ_UPSTREAM\rd-agent` — `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd`, clean |
| Source SHA comparison | MATCH |
| Runtime environment | `/home/zhou/AQ_ENVS/rdagent`, uv-managed CPython 3.11.16 |

The active runtime is entirely in the Linux filesystem, not under `/mnt/c` or `/mnt/d`. The existing Windows clone was not deleted or modified.

### Package and execution-runtime evidence

- Official user-package path used: `pip install rdagent` in the isolated CPython 3.11.16 environment.
- Installed package: `rdagent 0.8.0`; `pip check` reported no broken requirements and `import rdagent` passed.
- `AUTONOMOUS-QUANT-P0-RDAGENT-DEPENDENCY-ALIGNMENT-001` read the checked-out source requirement `pydantic-ai-slim[mcp,openai,prefect]==1.66.0` and aligned only the isolated environment from `pydantic-ai-slim 2.31.1` to `1.66.0`. `rdagent --help` then passed (with a non-failing `fitz` deprecation warning). No source edit, API key, LLM call, or execution scenario was attempted.
- The checked-out official documentation identifies Docker as the primary code-execution environment and documents Docker/Conda selection through `MODEL_COSTEER_ENV_TYPE` and `DS_CODER_COSTEER_ENV_TYPE`. Docker and Conda are not installed; no `.env` file, credentials, model call, Quant loop, factor generation, model training, dataset, or image pull was created or run.

```text
RD_AGENT_WSL_RUNTIME = STAGED
PACKAGE_INSTALL = PASS
PACKAGE_HEALTH = PASS
PYDANTIC_AI_SLIM = 1.66.0 (ALIGNED_TO_CHECKED_OUT_UPSTREAM_REQUIREMENT)
RDAGENT_CLI_HELP = PASS
QUANT_EXECUTION_RUNTIME = DEFERRED_DOCKER_OR_CONDA
DOCKER_INSTALLED = NO
CONDA_INSTALLED = NO
LLM_CALL_PERFORMED = NO
```

### Interop and persistence evidence

- From WSL, `/mnt/d/AUTONOMOUS_QUANT` and `/mnt/d/AQ_DATA` were visible.
- The Windows-side `\\wsl.localhost\Ubuntu-24.04\home\zhou\AQ_UPSTREAM\rd-agent` resolver check was denied by the Codex filesystem sandbox. This does not indicate an absent Linux source or a WSL failure; no Windows-side access control was changed for this task.
- No Windows service, Scheduled Task, startup entry, system/user PATH entry, AQ environment variable, Linux systemd service, cron job, background daemon, Docker installation, or CUDA installation was created.
- Final WSL process inspection found no RD-Agent process running.

```text
P0 = IN_PROGRESS
P0_FUNCTIONAL_POC_DESIGN = COMPLETE
P0_INTERFACE_AUDIT = COMPLETE
P0_POC_B_LINUX_QLIB_RDAGENT_RUNTIME = FAIL
CURRENT_NEXT = P0_POC_B_BLOCKER_RESOLUTION
P1 = NOT_STARTED
```
