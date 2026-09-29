"""US workspace selection through RD-Agent's public experiment seam."""

from pathlib import Path
from typing import Any

from rdagent.scenarios.qlib.experiment import factor_experiment, model_experiment
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorExperiment
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelExperiment
from rdagent.scenarios.qlib.experiment.workspace import QlibFBWorkspace
from rdagent.scenarios.qlib.proposal.factor_proposal import QlibFactorHypothesis2Experiment
from rdagent.scenarios.qlib.proposal.model_proposal import QlibModelHypothesis2Experiment


_TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "p3-official-us"
_FACTOR_BASE = Path(factor_experiment.__file__).parent / "factor_template"
_MODEL_BASE = Path(model_experiment.__file__).parent / "model_template"


def _workspace(base: Path, overlay: Path) -> QlibFBWorkspace:
    workspace = QlibFBWorkspace(template_folder_path=base)
    workspace.inject_code_from_folder(overlay)
    return workspace


class USQlibFactorHypothesis2Experiment(QlibFactorHypothesis2Experiment):
    def convert_response(self, response: str, hypothesis: Any, trace: Any) -> QlibFactorExperiment:
        experiment = super().convert_response(response, hypothesis, trace)
        overlay = _TEMPLATES / "factor_template"
        experiment.experiment_workspace = _workspace(_FACTOR_BASE, overlay)
        experiment.based_experiments[0].experiment_workspace = _workspace(_FACTOR_BASE, overlay)
        return experiment


class USQlibModelHypothesis2Experiment(QlibModelHypothesis2Experiment):
    def convert_response(self, response: str, hypothesis: Any, trace: Any) -> QlibModelExperiment:
        experiment = super().convert_response(response, hypothesis, trace)
        experiment.experiment_workspace = _workspace(_MODEL_BASE, _TEMPLATES / "model_template")
        return experiment
