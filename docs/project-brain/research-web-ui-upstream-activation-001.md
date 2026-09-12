# Research Web UI Upstream Activation 001

## Result and ownership

```text
TASK = AUTONOMOUS-QUANT-RESEARCH-WEB-UI-UPSTREAM-ACTIVATION-001
STATUS = COMPLETE
CAPABILITY = Research experiment Web visualization
UPSTREAM_OWNER = MLflow
OWNERSHIP_MODE = UPSTREAM_WHOLE
RESEARCH_WEB_UI_IMPLEMENTATION = UPSTREAM_MLFLOW_UI
AQ_CUSTOM_WEB_UI = NONE
AQ_CUSTOM_WEB_BACKEND = NONE
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

The existing upstream MLflow Web UI was activated for the three independent
P1 research tracking stores. No AQ frontend, dashboard engine, Web backend,
REST wrapper, chart engine, experiment database, launcher, or persistence
orchestration was created.

Qlib's pinned Recorder documentation states that `MLflowExpManager` is based
on MLflow and identifies `mlflow ui` for visualizing and checking experiment
results. The pinned implementation constructs MLflow's public
`MlflowClient` with the configured tracking URI. The installed MLflow runtime
provides `mlflow server`, described by its own CLI as the tracking server with
UI and REST API.

## Runtime authority

```text
PYTHON_VERSION = 3.10.21
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_SOURCE_WORKTREE_CLEAN = YES
QLIB_RUNTIME_AUTHORITY_MATCH = YES
MLFLOW_VERSION = 3.16.0
MLFLOW_CLI_AVAILABLE = YES
MLFLOW_UI_OR_SERVER_COMMAND_AVAILABLE = YES (mlflow server)
PACKAGES_CHANGED = NO
```

No package was installed or upgraded. The accepted `rdagent4qlib`
environment and Qlib source were not modified.

## Tracking-store inventory

The authoritative databases were hashed before Web launch. Only byte copies
under
`/home/zhou/AQ_DATA/WEB_UI_VERIFY/research-web-ui-upstream-activation-001`
were served. Stores were not merged, migrated, imported, vacuumed, or
rewritten.

| Store | Authoritative database | Size (bytes) | SHA-256 | Experiments | Runs | Served copy | UI |
|---|---|---:|---|---:|---:|---|---|
| Baseline | `/home/zhou/AQ_DATA/P1/qlib-native-baseline-001/native-run/mlflow.db` | 901120 | `5a15a80743720979cb2a6ee73c7289282a4d8ac0be1400fd4e5046c60c19ab91` | 2 | 1 | `baseline.db` | `http://127.0.0.1:5000` |
| Model comparison | `/home/zhou/AQ_DATA/P1/qlib-native-model-comparison-001/linear-run/mlflow.db` | 876544 | `9d48dd1793ff8890f61a46319682722b6e75b71f0e7a77e39e51cc74def2af0f` | 2 | 1 | `model-comparison.db` | `http://127.0.0.1:5001` |
| Strategy comparison | `/home/zhou/AQ_DATA/P1/qlib-native-strategy-comparison-001/mlflow.db` | 876544 | `3fb9fe0f6723a16ff5b1ca14d86c9338e02470e738b629017202d3f9e8924e18` | 3 | 2 | `strategy-comparison.db` | `http://127.0.0.1:5002` |

The experiment totals include MLflow's default experiment where present.
Run totals were obtained with MLflow public APIs across all experiments,
including active and deleted lifecycle views.

## UI and API verification

Three instances of the same upstream MLflow UI were launched, one per copied
store, with one worker each and artifact proxying disabled. These are not
three AQ Web systems.

| Store | Listener PID | Bind | HTTP root | REST experiments/runs | Expected Recorder | Status | Metrics / params |
|---|---:|---|---|---|---|---|---|
| Baseline | 403 | `127.0.0.1:5000` | 200 | 2 / 1 | `16bd043b00914e54bca7458efc5af9e9` | FINISHED | 19 / 25 |
| Model comparison | 868 | `127.0.0.1:5001` | 200 | 2 / 1 | `ef143027d1a0486cb876ba8e615496b5` | FINISHED | 21 / 19 |
| Strategy comparison | 906 | `127.0.0.1:5002` | 200 | 3 / 2 | `52a61a96342c4f349ed234d988b08be8` | FINISHED | 13 / 8 |
| Strategy comparison | 906 | `127.0.0.1:5002` | 200 | 3 / 2 | `64b2d358929f47d28861e760939b41a5` | FINISHED | 13 / 8 |

```text
PROCESS_STARTED = YES
HTTP_ROOT_RESPONDS = YES
MLFLOW_API_RESPONDS = YES
EXPERIMENTS_VISIBLE = YES
RUNS_VISIBLE = YES
EXPECTED_RECORDERS_VISIBLE = YES
METRICS_AND_PARAMS_READABLE = YES
AUTHORITATIVE_DB_HASH_UNCHANGED = YES
```

After verification, each authoritative database retained exactly its
pre-launch SHA-256. The served copies also retained the same byte hashes.

## Security and process lifetime

```text
WEB_BIND_SCOPE = LOCALHOST_ONLY
LISTEN_ADDRESS = 127.0.0.1
RESEARCH_WEB_UI_VERIFIED = YES
RESEARCH_WEB_UI_PERSISTENT = YES
SYSTEMD_SERVICE_CREATED = NO
WINDOWS_SERVICE_CREATED = NO
DOCKER_USED = NO
REVERSE_PROXY_CREATED = NO
AUTH_PROXY_CREATED = NO
```

The three transient background processes were left running after
verification. `PERSISTENT = YES` means they remained live for local use at
task completion; it does not mean reboot persistence or a managed service.
No listener binds to `0.0.0.0`, and no LAN or Internet exposure was created.

## Project state

```text
P1 = COMPLETE
P1_MINIMAL_QUANT = COMPLETE
PIT_UNIVERSE_CERTIFIED = NO
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
P2_CERTIFICATION = NOT STARTED
CURRENT_NEXT = P2_CERTIFICATION_ENTRY
```

Activation changes no research result, certification state, production
permission, or live-capital boundary.
