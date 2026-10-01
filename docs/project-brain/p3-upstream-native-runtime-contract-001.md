# P3 Upstream-Native Runtime Contract 001

## Authority and ownership

Smoke-006 is the functional authority for P3 autonomous research:
`PASS_UPSTREAM_NATIVE_US_PIT_FINQUANT_SMOKE`. Microsoft RD-Agent owns the
research loop, CoSTEER, coding, execution, and feedback; Qlib owns dataset
execution, evaluation, portfolio analysis, Recorder, and MLflow integration.
LiteLLM is the upstream backend and DeepSeek is its external chat provider.

AQ owns only the thin US/PIT workspace/template binding, frozen provider and
factor-data bindings, process configuration, governance, and later Candidate
handoff. AQ owns no LLM backend, research loop, Qlib runner, Recorder, or
benchmark engine.

## Exact runtime identities

| Component | Authority |
| --- | --- |
| RD-Agent | `1.0.0`, `/home/zhou/miniforge3/envs/rdagent-official-v1/bin/rdagent` |
| Qlib | `0.9.8.dev26`, source `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`, environment `rdagent4qlib` |
| Chat | `rdagent.oai.backend.LiteLLMAPIBackend` -> `deepseek/deepseek-chat` |
| Embedding | LiteLLM -> `ollama/qwen3-embedding:0.6b` |
| Model CoSTEER environment | `conda` |
| US factor data | `/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source` |
| Qlib provider / market | `/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data` / `p2_pit` |

The native research benchmark is the Qlib dynamic market configuration
`{market: p2_pit, filter_pipe: []}`. It is a research-only equal-weight
matched-universe benchmark over frozen PIT membership, not a P2 certification
market benchmark. Qlib's native `MLflowExpManager` uses a unique run-scoped
SQLite URI.

## Required process contract

The private RD-Agent working-directory `.env` is the provider authority for
`BACKEND`, `CHAT_MODEL`, `EMBEDDING_MODEL`, `DEEPSEEK_API_KEY`, and
`MODEL_COSTEER_ENV_TYPE`; it is never committed. The direct process requires:

```text
PATH=/home/zhou/miniforge3/bin:/home/zhou/miniforge3/condabin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
CONDA_DEFAULT_ENV=rdagent4qlib
FACTOR_COSTEER_PYTHON_BIN=/home/zhou/miniforge3/envs/rdagent4qlib/bin/python
PYTHONPATH=<checkout>/30-research-system/rd-agent/binding
FACTOR_COSTEER_DATA_FOLDER=/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/full
FACTOR_COSTEER_DATA_FOLDER_DEBUG=/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/debug
QLIB_QUANT_FACTOR_HYPOTHESIS2EXPERIMENT=aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment
QLIB_QUANT_MODEL_HYPOTHESIS2EXPERIMENT=aq_rdagent_official_us_binding.USQlibModelHypothesis2Experiment
```

All `QLIB_QUANT_*`, `QLIB_FACTOR_*`, and `QLIB_MODEL_*` date families must
remain aligned: train `2015-01-02`--`2019-12-31`, valid
`2020-01-02`--`2021-12-31`, and research test `2022-01-03`--`2024-12-31`.
`WORKSPACE_PATH`, `PICKLE_CACHE_FOLDER_PATH_STR`, `LOG_TRACE_PATH`, and
`QLIB_MLFLOW_URI` must resolve to one unique run namespace.

The authoritative entry point is direct upstream RD-Agent:

```bash
cd /home/zhou/UPSTREAM_RUNTIME/rdagent-v1.0.0
/home/zhou/miniforge3/envs/rdagent-official-v1/bin/rdagent fin_quant --loop-n 1
```

## Retired layers and operations boundary

The former DVC P3 `fin_quant` launcher, its DVC run namespace, the old
`/home/zhou/AQ_ENVS/rdagent-v1.0.0` route, and the deepseek-flash runtime JSON
are retired as active P3 authority. No wrapper, DVC stage, systemd unit,
Docker container, custom launcher, or DPAPI bridge is part of this proven
research runtime. DVC remains available for post-run reproducibility and
sealing only.

Legacy factor-coder admission fixtures used during superseded local-model experiments are retired and must not be reused as future capability or admission benchmarks. Future capability evaluation requires a new unseen benchmark design.

Smoke-006 completed proposal, CoSTEER coding, Qlib dataset/training/prediction,
native dynamic-market backtest and portfolio analysis, SQLite Recorder, and
RD-Agent feedback. Docker, Compose, and systemd may be evaluated later for
deployment supervision after functional construction is complete; they are not
part of the proven current P3 research runtime.
