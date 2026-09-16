"""Thin US template and source-data binding for the pinned Microsoft RD-Agent."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from rdagent.components.coder.factor_coder.config import FACTOR_COSTEER_SETTINGS
from rdagent.scenarios.qlib.experiment.factor_experiment import (
    QlibFactorExperiment,
    QlibFactorScenario,
)
from rdagent.scenarios.qlib.experiment.model_experiment import (
    QlibModelExperiment,
)
from rdagent.scenarios.qlib.experiment.quant_experiment import QlibQuantScenario
from rdagent.scenarios.qlib.experiment.workspace import QlibFBWorkspace
from rdagent.scenarios.qlib.proposal.factor_proposal import (
    QlibFactorHypothesis2Experiment,
)
from rdagent.scenarios.qlib.proposal.model_proposal import (
    QlibModelHypothesis2Experiment,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = (_PROJECT_ROOT / "templates" / "p3-us-ragged").resolve()
FACTOR_TEMPLATE_ROOT = (TEMPLATE_ROOT / "factor_template").resolve()
MODEL_TEMPLATE_ROOT = (TEMPLATE_ROOT / "model_template").resolve()

FACTOR_SOURCE_ROOT = Path("/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source")
FACTOR_SOURCE_FULL = FACTOR_SOURCE_ROOT / "full"
FACTOR_SOURCE_DEBUG = FACTOR_SOURCE_ROOT / "debug"
_MAX_SOURCE_DATE = pd.Timestamp("2024-12-31")
_SOURCE_COLUMNS = ["$open", "$close", "$high", "$low", "$volume", "$factor"]

TEMPLATE_HASHES = {
    "factor_template/conf_baseline.yaml": "ddc6713ca9b07b44f210c0dc61d15fa3359fdd9a3e0e2dfd832331b58674bb40",
    "factor_template/conf_combined_factors.yaml": "9641b4eaca343ce3d690c4389a47e147e9de130b893af8db900f24365578f03c",
    "factor_template/conf_combined_factors_sota_model.yaml": "4ab822372277af50d3a6ccc7fb1558b6c90a3148536fe9e0b920ef092a481029",
    "model_template/conf_baseline_factors_model.yaml": "9ccbda614474cec2834543baa39e9cb0500091911718bf9df9f49dd5cc195cb7",
    "model_template/conf_sota_factors_model.yaml": "5470f63512477a0f232db3eca00db23c9cfe04227f991769513349dcff61813b",
}

_SOURCE_HASHES = {
    "full/daily_pv.h5": "deacd04bad8f5321bd49cc63cf9be37d38e4ae7b33b5c223021c80dedad98b21",
    "full/README.md": "6e545e77c1c807a23ef9fdfbadc3a51ef73d2ce7246df04b06e2f9d3d6ed9211",
    "debug/daily_pv.h5": "5fe7263630a9b7c3a796f35e0d943e62aed44ec4d22b20cbf42a4ec846016ebc",
    "debug/README.md": "6e545e77c1c807a23ef9fdfbadc3a51ef73d2ce7246df04b06e2f9d3d6ed9211",
    "materialization-report.json": "7d067e6f93409228125e7e5b6d2590242d60a5bc664f5f8aa9848e5d4a0e3033",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _text_sha256(path: Path) -> str:
    """Hash canonical text so Git checkout newline policy cannot change authority."""
    return hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()


def validate_template_family() -> None:
    actual = {
        path.relative_to(TEMPLATE_ROOT).as_posix()
        for path in TEMPLATE_ROOT.rglob("*")
        if path.is_file()
    }
    if actual != set(TEMPLATE_HASHES):
        raise RuntimeError("approved RD-Agent US template inventory mismatch")
    for relative, expected_hash in TEMPLATE_HASHES.items():
        path = (TEMPLATE_ROOT / relative).resolve()
        if not path.is_relative_to(TEMPLATE_ROOT) or _text_sha256(path) != expected_hash:
            raise RuntimeError(f"approved RD-Agent US template hash mismatch: {relative}")


def _workspace_uses_template(workspace: Any, template_root: Path) -> bool:
    expected_names = {
        path.name
        for path in template_root.iterdir()
        if path.is_file()
    }
    file_dict = getattr(workspace, "file_dict", None)
    if not isinstance(file_dict, dict):
        return False
    actual_yaml_names = {Path(name).name for name in file_dict if Path(name).suffix == ".yaml"}
    if actual_yaml_names != expected_names:
        return False
    return all(
        name in file_dict
        and hashlib.sha256(str(file_dict[name]).encode()).hexdigest() == _text_sha256(template_root / name)
        for name in expected_names
    )


def _guard_incomplete_history(experiments: Any, template_root: Path) -> None:
    for experiment in experiments:
        if getattr(experiment, "result", None) is None and not _workspace_uses_template(
            getattr(experiment, "experiment_workspace", None), template_root
        ):
            raise RuntimeError("incomplete prior experiment is not bound to the approved US template family")


def _new_workspace(template_root: Path) -> QlibFBWorkspace:
    workspace = QlibFBWorkspace(template_folder_path=template_root)
    if not _workspace_uses_template(workspace, template_root):
        raise RuntimeError("new workspace failed approved US template validation")
    return workspace


def _validate_source_frame(path: Path) -> None:
    with pd.HDFStore(path, mode="r") as store:
        if store.keys() != ["/data"]:
            raise RuntimeError(f"RD-Agent source HDF key mismatch: {path}")
    frame = pd.read_hdf(path, key="data")
    if (
        list(frame.columns) != _SOURCE_COLUMNS
        or list(frame.index.names) != ["datetime", "instrument"]
        or frame.index.has_duplicates
        or frame.empty
    ):
        raise RuntimeError(f"RD-Agent source HDF schema mismatch: {path}")
    if pd.Timestamp(frame.index.get_level_values("datetime").max()) > _MAX_SOURCE_DATE:
        raise RuntimeError(f"RD-Agent source exceeds approved historical boundary: {path}")


def validate_factor_source() -> None:
    configured = (
        Path(FACTOR_COSTEER_SETTINGS.data_folder).resolve(),
        Path(FACTOR_COSTEER_SETTINGS.data_folder_debug).resolve(),
    )
    expected = (FACTOR_SOURCE_FULL.resolve(), FACTOR_SOURCE_DEBUG.resolve())
    if configured != expected:
        raise RuntimeError("Factor CoSTEER paths are not the approved P3 US source folders")
    for relative, expected_hash in _SOURCE_HASHES.items():
        path = FACTOR_SOURCE_ROOT / relative
        if not path.is_file() or _sha256(path) != expected_hash:
            raise RuntimeError(f"approved P3 factor source hash mismatch: {relative}")
    report = json.loads((FACTOR_SOURCE_ROOT / "materialization-report.json").read_text(encoding="utf-8"))
    if (
        report.get("provider_mutated") is not False
        or report.get("max_session") != "2024-12-31"
        or report.get("ticker_only_identity_join") is not False
        or report.get("sealed_oos_isolation") != "PASS"
    ):
        raise RuntimeError("P3 factor source provenance report mismatch")
    _validate_source_frame(FACTOR_SOURCE_FULL / "daily_pv.h5")
    _validate_source_frame(FACTOR_SOURCE_DEBUG / "daily_pv.h5")


class USQlibFactorHypothesis2Experiment(QlibFactorHypothesis2Experiment):
    """Delegate conversion upstream, then bind only its new factor workspaces."""

    def convert_response(self, response: str, hypothesis: Any, trace: Any) -> QlibFactorExperiment:
        validate_template_family()
        experiment = super().convert_response(response, hypothesis, trace)
        if not isinstance(experiment, QlibFactorExperiment) or not experiment.based_experiments:
            raise RuntimeError("unexpected upstream factor experiment shape")
        baseline = experiment.based_experiments[0]
        if not isinstance(baseline, QlibFactorExperiment) or baseline.sub_tasks:
            raise RuntimeError("unexpected upstream factor baseline shape")
        _guard_incomplete_history(experiment.based_experiments[1:], FACTOR_TEMPLATE_ROOT)
        experiment.experiment_workspace = _new_workspace(FACTOR_TEMPLATE_ROOT)
        baseline.experiment_workspace = _new_workspace(FACTOR_TEMPLATE_ROOT)
        return experiment


class USQlibModelHypothesis2Experiment(QlibModelHypothesis2Experiment):
    """Delegate conversion upstream, then bind only its new model workspace."""

    def convert_response(self, response: str, hypothesis: Any, trace: Any) -> QlibModelExperiment:
        validate_template_family()
        experiment = super().convert_response(response, hypothesis, trace)
        if not isinstance(experiment, QlibModelExperiment):
            raise RuntimeError("unexpected upstream model experiment shape")
        _guard_incomplete_history(experiment.based_experiments, MODEL_TEMPLATE_ROOT)
        experiment.experiment_workspace = _new_workspace(MODEL_TEMPLATE_ROOT)
        return experiment


class USQlibFactorScenario(QlibFactorScenario):
    """Require the immutable P3 US factor source before upstream construction."""

    def __init__(self) -> None:
        validate_factor_source()
        super().__init__()


class USQlibQuantScenario(QlibQuantScenario):
    """Require the immutable P3 US factor source before upstream construction."""

    def __init__(self) -> None:
        validate_factor_source()
        super().__init__()
