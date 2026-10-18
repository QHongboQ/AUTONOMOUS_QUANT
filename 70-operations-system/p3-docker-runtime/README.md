# Pinned RD-Agent / Qlib Docker runtime

This image packages the previously accepted RD-Agent 1.0.0 control runtime
and `rdagent4qlib` Python 3.10 environment. RD-Agent and Qlib source are
installed from their exact frozen Git commits. Conda explicit specs and pip
version locks were exported from the existing WSL environments; Conda packages
carry their upstream MD5s. The Qlib lock adds the upstream `QlibCondaEnv`
dependencies missing from the base host Qlib env: official PyTorch CPU 2.14.0
(also present in the accepted model-capable Qlib environment), CatBoost 1.2.10,
and XGBoost 3.2.0. No host environment was changed. XGBoost 3.4.1 was
unavailable for Python 3.10 on the configured package index, so the pinned
Python 3.10 compatible release is 3.2.0. PyTorch uses the [official CPU wheel
index](https://download.pytorch.org/whl/cpu) so acceptance does not require
CUDA libraries or a GPU. Qlib's pinned source compiles its official rolling
extension during installation, so the image build installs the base Ubuntu
C++ compiler; no compiler is required by or invoked during runtime acceptance.

The entry point runs RD-Agent in its official control environment while restoring `CONDA_DEFAULT_ENV=rdagent4qlib` for the upstream factor/model CoSTEER configuration. The official RD-Agent source prepares `rdagent4qlib` only when that environment
is missing. This image creates it at build time with Qlib `0.9.8.dev26` and
the pinned dependencies; the acceptance run uses `--network none`, so the
image cannot fetch packages or data while running. The checks construct the
official `QlibCondaEnv` and factor/model CoSTEER environments but do not run
training.

See [BUILD-VERIFICATION.md](BUILD-VERIFICATION.md) for the actual local image
digest, pinned build inputs, package versions and runtime test evidence.

## Build once

From the repository root:

```powershell
docker build --platform linux/amd64 `
  --build-arg P3_RUNTIME_IMAGE_VERSION=rdagent-1.0.0-qlib-0.9.8.dev26-v1 `
  -f 70-operations-system/p3-docker-runtime/Dockerfile `
  -t aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1 .
```

The Dockerfile pins the official `condaforge/miniforge3:26.7.2-0` amd64
manifest digest and both upstream Git SHAs. The image tag is stable and reused;
do not rebuild it for each request.

## Runtime acceptance

The acceptance container should have only these two data mounts, both
read-only:

```text
D:/AQ_DATA/P3/rdagent-us-ragged/factor-source -> /data/factor-source
D:/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data -> /data/qlib
```

Use the image with no network, a non-root UID, a read-only root filesystem,
and a dedicated writable temporary workspace. Example WSL/Docker invocation:

```bash
docker run --detach --name aq-p3-runtime-acceptance \
  --network none --read-only --user 10001:10001 \
  --cap-drop ALL --security-opt no-new-privileges --pids-limit 256 --memory 4g \
  --tmpfs /workspace:rw,nosuid,nodev,size=1g,uid=10001,gid=10001 --tmpfs /tmp:rw,nosuid,nodev,size=256m,uid=10001,gid=10001 \
  --tmpfs /home/rdagent:rw,nosuid,nodev,size=256m,uid=10001,gid=10001 \
  --mount type=bind,source=/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source,target=/data/factor-source,readonly \
  --mount type=bind,source=/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data,target=/data/qlib,readonly \
  --entrypoint sleep aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1 infinity

docker exec aq-p3-runtime-acceptance \
  conda run --name rdagent-official-v1 --no-capture-output \
  python /opt/aq/runtime_acceptance.py

docker inspect aq-p3-runtime-acceptance
docker rm --force aq-p3-runtime-acceptance
```

Confirm inspect reports `NetworkMode=none`, user `10001:10001`, exactly two
bind mounts with `RW=false`, and no Docker socket. The acceptance script also
checks RD-Agent/Qlib source commits and imports, Conda, LightGBM, Torch, Tables,
CatBoost and XGBoost, resolves factor/model CoSTEER to `rdagent4qlib`, and
initializes native Qlib as US against `market=p2_pit` for the existing
2015--2024 historical research calendar. It does not open any sealed-OOS
protocol or files, train a model, invoke an LLM, or create a Candidate.

The image contains no provider credentials or owner keys. It includes the
existing AQ US binding and frozen templates only. It does not include P12 or
launch `fin_quant`; a future handoff must select an isolated run-specific
workspace and remain subject to P12 authorization.
