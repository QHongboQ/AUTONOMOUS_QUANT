# Pinned P3 Docker runtime verification

## Build identity

- Base repository commit: `1346f6d770ed27081d60ff1cebf9d3b5a8ed975c`
- Base image: `condaforge/miniforge3:26.7.2-0`, linux/amd64 manifest digest `sha256:be01a3e63d4af20d8a9937d1e12fa299d1c572edf601b961180a59c78bd7250d`
- Stable local tag: `aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1`
- Docker Engine image ID after the PR #161 final build: `sha256:f0caceba9e06a618dda72bd999de78c13e34e0773831c8796936c80793e4eea2`
- Image size: 9,554,321,896 bytes; image was kept local and not pushed.
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

The final PR #161 image was built from the repository root with the current
Dockerfile and updated `runtime_acceptance.py`:

```text
docker build --platform linux/amd64 --build-arg P3_RUNTIME_IMAGE_VERSION=rdagent-1.0.0-qlib-0.9.8.dev26-v1 -f 70-operations-system/p3-docker-runtime/Dockerfile -t aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1 .
BUILD_EXIT_CODE = 0
IMAGE_ID = sha256:f0caceba9e06a618dda72bd999de78c13e34e0773831c8796936c80793e4eea2
```

The built image was run without overriding its default entrypoint or command;
the baked-in `/opt/aq/runtime_acceptance.py` executed and the container exited
with code 0. `docker inspect` reported the same image ID, user `10001:10001`,
`NetworkMode=none`, read-only root, 256 process limit, 4 GiB memory limit, and
the default command `python /opt/aq/runtime_acceptance.py`. All five
`unittest` checks passed (`Ran 5 tests in 23.535s`, `OK`).

The container was non-root (`10001:10001`), networkless (`none`), read-only at
root, capped at 4 GiB and 256 processes, and had exactly three host bind mounts.
All were `RW=false`: the existing approved P3 factor-source path; the exact P2
Qlib provider path frozen in the templates; and the separate exact
`calendar_provider` path frozen in the templates. Workspace, temporary files,
and `/home/rdagent` were isolated UID-owned tmpfs mounts. No Docker socket,
credentials, signing keys, or sealed OOS directory was mounted. The existing
`aq-p12-health` container remained `running` and `healthy` after the test.

The acceptance loaded the template's native `calendar_provider` configuration
into Qlib and checked both frozen paths and source-file hashes. The provider's
frozen `instruments/p2_pit.txt` SHA-256 was
`e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875`. Qlib
`D.list_instruments()` observed and matched the full authority: 730 security
identities and 745 membership ranges. `D.calendar()` returned 2,516 historical
sessions from 2015-01-02 through 2024-12-31 with required boundaries present.
The baked-in probe emitted `US_PIT_QLIB_DATA_ACCEPTANCE_PASS`,
`instrument_count=730`, `membership_range_count=745`, and
`membership_matches_frozen_authority=true`.
The separately mounted calendar source is documented in P2's historical
rehearsal as a calendar-only runtime generated from XNYS 4.13.2; `day.txt` and
Qlib-required `day_future.txt` matched the frozen SHA-256s. It contains no
market observations and adds only the native boundary session 2025-01-02.
A native Qlib `D.features()` read returned an observed `$close` for the
previously documented sample identity on 2015-12-29 with disk cache disabled.
No training, Candidate production, paid LLM request, or sealed OOS access
occurred.

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
