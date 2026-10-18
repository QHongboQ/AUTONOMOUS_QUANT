FROM condaforge/miniforge3:26.7.2-0@sha256:be01a3e63d4af20d8a9937d1e12fa299d1c572edf601b961180a59c78bd7250d

ARG RDAGENT_SOURCE_SHA=484776c211e4fbbeef03e0ec00d6bbee7362a4f4
ARG QLIB_SOURCE_SHA=2fb9380b342556ddb50a4b24e4fe8655d548b2b8
ARG P3_RUNTIME_IMAGE_VERSION=rdagent-1.0.0-qlib-0.9.8.dev26-v1

LABEL org.opencontainers.image.title="AQ P3 pinned RD-Agent/Qlib runtime"
LABEL org.opencontainers.image.version="${P3_RUNTIME_IMAGE_VERSION}"
LABEL org.opencontainers.image.source="https://github.com/QHongboQ/AUTONOMOUS_QUANT"
LABEL aq.p3.rdagent.source-sha="${RDAGENT_SOURCE_SHA}"
LABEL aq.p3.qlib.source-sha="${QLIB_SOURCE_SHA}"

ENV CONDA_DIR=/opt/conda \
    PATH=/opt/conda/envs/rdagent-official-v1/bin:/opt/conda/condabin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    CONDA_DEFAULT_ENV=rdagent4qlib \
    MODEL_COSTEER_ENV_TYPE=conda \
    FACTOR_COSTEER_PYTHON_BIN=/opt/conda/envs/rdagent4qlib/bin/python \
    FACTOR_COSTEER_DATA_FOLDER=/data/factor-source/full \
    FACTOR_COSTEER_DATA_FOLDER_DEBUG=/data/factor-source/debug \
    QLIB_QUANT_FACTOR_HYPOTHESIS2EXPERIMENT=aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment \
    QLIB_QUANT_MODEL_HYPOTHESIS2EXPERIMENT=aq_rdagent_official_us_binding.USQlibModelHypothesis2Experiment \
    PYTHONPATH=/opt/aq/p3/binding \
    HOME=/home/rdagent \
    TMPDIR=/tmp \
    WORKSPACE_PATH=/workspace/runs/default/workspaces \
    PICKLE_CACHE_FOLDER_PATH_STR=/workspace/runs/default/pickle-cache \
    LOG_TRACE_PATH=/workspace/runs/default/trace \
    QLIB_MLFLOW_URI=sqlite:////workspace/runs/default/mlflow.db

COPY 70-operations-system/p3-docker-runtime/locks/rdagent-official-v1-conda-explicit.txt /tmp/locks/rdagent-conda.txt
COPY 70-operations-system/p3-docker-runtime/locks/rdagent-official-v1-pip-requirements.txt /tmp/locks/rdagent-pip.txt
COPY 70-operations-system/p3-docker-runtime/locks/rdagent4qlib-conda-explicit.txt /tmp/locks/qlib-conda.txt
COPY 70-operations-system/p3-docker-runtime/locks/rdagent4qlib-pip-requirements.txt /tmp/locks/qlib-pip.txt

RUN conda create --yes --name rdagent-official-v1 --file /tmp/locks/rdagent-conda.txt \
 && conda create --yes --name rdagent4qlib --file /tmp/locks/qlib-conda.txt \
 && conda run --name rdagent-official-v1 --no-capture-output python -m pip install --no-deps --no-input -r /tmp/locks/rdagent-pip.txt \
 && conda run --name rdagent4qlib --no-capture-output python -m pip install --no-deps --no-input --extra-index-url https://download.pytorch.org/whl/cpu -r /tmp/locks/qlib-pip.txt

RUN apt-get update \
 && apt-get install --yes --no-install-recommends g++ \
 && rm -rf /var/lib/apt/lists/*

RUN conda run --name rdagent-official-v1 --no-capture-output python -m pip install --no-deps --no-build-isolation --no-input \
      "git+https://github.com/microsoft/RD-Agent.git@${RDAGENT_SOURCE_SHA}" \
 && conda run --name rdagent4qlib --no-capture-output python -m pip install --no-deps --no-build-isolation --no-input \
      "git+https://github.com/microsoft/qlib.git@${QLIB_SOURCE_SHA}" \
 && rm -rf /tmp/locks \
 && conda clean --all --yes

COPY 30-research-system/rd-agent/binding/aq_rdagent_official_us_binding.py /opt/aq/p3/binding/aq_rdagent_official_us_binding.py
COPY 30-research-system/rd-agent/templates/p3-official-us /opt/aq/p3/templates/p3-official-us
COPY 70-operations-system/p3-docker-runtime/runtime_acceptance.py /opt/aq/runtime_acceptance.py

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin rdagent \
 && mkdir -p /workspace \
 && chown 10001:10001 /workspace /home/rdagent \
 && chmod -R a+rX /opt/aq

USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["conda", "run", "--name", "rdagent-official-v1", "--no-capture-output", "env", "CONDA_DEFAULT_ENV=rdagent4qlib"]
CMD ["python", "/opt/aq/runtime_acceptance.py"]
