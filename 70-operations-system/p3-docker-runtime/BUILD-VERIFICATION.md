# Pinned P3 Docker runtime verification

## Build identity

- Base repository commit: `1346f6d770ed27081d60ff1cebf9d3b5a8ed975c`
- Base image: `condaforge/miniforge3:26.7.2-0`, linux/amd64 manifest digest `sha256:be01a3e63d4af20d8a9937d1e12fa299d1c572edf601b961180a59c78bd7250d`
- Stable local tag: `aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1`
- Docker Engine local image digest: `sha256:80d832b0899c8d9e380b4ace42afeea931ed789e491b21b0ed6be09add64bc84`
- Image size: 9,554,316,541 bytes; image was kept local and not pushed.
- RD-Agent source: `microsoft/RD-Agent@484776c211e4fbbeef03e0ec00d6bbee7362a4f4`
- Qlib source: `microsoft/qlib@2fb9380b342556ddb50a4b24e4fe8655d548b2b8`
- Python: 3.10.21 in both `rdagent-official-v1` and `rdagent4qlib`.
- Qlib runtime imports: Qlib 0.9.8.dev26; LightGBM 4.7.0; PyTables 3.10.1; official PyTorch CPU 2.14.0; CatBoost 1.2.10; XGBoost 3.2.0.
- Conda explicit package manifests and exact pip version locks are under `locks/`.
- SHA-256 `rdagent-official-v1-conda-explicit.txt`: `754095d7ab7993e8606d201f6222805a51bfb360ca7c1f0d113351883bbc1f42`
- SHA-256 `rdagent-official-v1-pip-requirements.txt`: `b7c42ed8c12ab01bc49f61b166962a7931a35f709c3bd175c4c83d0f2c754d3a`
- SHA-256 `rdagent4qlib-conda-explicit.txt`: `2ae99ccc5301ba162fb005a28df4885194fbdd4f786fe4419b43246d17675bcf`
- SHA-256 `rdagent4qlib-pip-requirements.txt`: `81a851dd96937966a579572f0c966ed589e775269d2305f7ec4a25ea1967e909`

## Actual runtime acceptance

The image default entry point and command were run in a disposable container.
The container exited with code 0 after all five `unittest` checks passed.
Acceptance verified RD-Agent and Qlib source commit metadata, Conda availability,
the `rdagent4qlib` environment, native imports, official `QlibCondaEnv`, and
factor/model CoSTEER environment resolution.

Qlib initialized on the approved US `p2_pit` data. It resolved 2 instruments
and 2,516 historical calendar entries from 2015-01-02 through 2024-12-31;
the required train/validation/history boundary dates were present. No training
or Candidate production occurred.

The runtime container was non-root (`10001:10001`), networkless (`none`),
read-only at root, capped at 4 GiB and 256 processes, and had exactly two host
bind mounts. Both mounts were `RW=false`: the approved P3 factor-source path
and P2 Qlib `p2_pit` data path. Workspace, temporary files, and `/home/rdagent`
were isolated UID-owned tmpfs mounts. No Docker socket, credentials, signing
keys, or sealed OOS directory was mounted.

RD-Agent's imported LiteLLM utility attempted its optional public model-cost
metadata refresh; the networkless container blocked name resolution and it
used its packaged local backup. No LLM request was made. This confirms that
runtime has no public egress while noting the upstream metadata lookup attempt.

The first package resolution showed XGBoost 3.4.1 unavailable for Python 3.10,
so the compatible 3.2.0 release was pinned. Qlib source installation required
the Ubuntu C++ compiler to build its upstream rolling extension. Acceptance
found that the official control environment resets `CONDA_DEFAULT_ENV`; the
image entry point restores the intended `rdagent4qlib` selection for native
factor/model configuration while retaining the official control environment.
