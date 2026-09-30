from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml
from jinja2 import Environment


TEST_FILE = Path(__file__).resolve()
RDAGENT_ROOT = TEST_FILE.parents[2]
BINDING_ROOT = RDAGENT_ROOT / "binding"
sys.path.insert(0, str(BINDING_ROOT))

import aq_rdagent_official_us_binding as binding
from rdagent.app.qlib_rd_loop.conf import FactorBasePropSetting, ModelBasePropSetting
from rdagent.core.experiment import RD_AGENT_SETTINGS
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorExperiment
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelExperiment
from rdagent.scenarios.qlib.proposal.factor_proposal import QlibFactorHypothesis2Experiment
from rdagent.scenarios.qlib.proposal.model_proposal import QlibModelHypothesis2Experiment


QLIB_PROVIDER_URI = "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data"
CALENDAR_PROVIDER_URI = "/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime"
RENDER_CONTEXT = {
    "train_start": "2015-01-02",
    "train_end": "2019-12-31",
    "valid_start": "2020-01-02",
    "valid_end": "2021-12-31",
    "test_start": "2022-01-03",
    "test_end": "2024-12-31",
    "feature_expressions": ["$close"],
    "feature_names": ["CLOSE0"],
    "n_epochs": 1,
    "lr": 0.001,
    "early_stop": 1,
    "batch_size": 8,
    "weight_decay": 0.0,
    "num_features": 1,
    "num_timesteps": 1,
    "dataset_cls": "DatasetH",
}


def expected_overlay(base: Path) -> str:
    text = base.read_text()
    text = text.replace('provider_uri: "~/.qlib/qlib_data/cn_data"', f"provider_uri: {QLIB_PROVIDER_URI}")
    text = text.replace(
        "    region: cn\n",
        "    region: us\n"
        "    calendar_provider:\n"
        "        class: LocalCalendarProvider\n"
        "        module_path: qlib.data.data\n"
        "        kwargs:\n"
        "            backend:\n"
        "                class: FileCalendarStorage\n"
        "                module_path: qlib.data.storage.file_storage\n"
        "                kwargs:\n"
        f"                    provider_uri: {CALENDAR_PROVIDER_URI}\n",
    )
    text = text.replace("market: &market csi300", "market: &market p2_pit")
    text = text.replace("benchmark: &benchmark SH000300", "benchmark: &benchmark SPY")
    return text.replace("limit_threshold: 0.095", "limit_threshold: null")


class OfficialUSBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        RD_AGENT_SETTINGS.workspace_path = Path(self.temporary.name) / "workspaces"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_upstream_sources_are_exact_and_clean(self) -> None:
        authorities = (
            (Path("/home/zhou/AQ_UPSTREAM/rd-agent-v1.0.0"), "484776c211e4fbbeef03e0ec00d6bbee7362a4f4"),
            (Path("/home/zhou/AQ_UPSTREAM/qlib-rdagent-v1-pin"), "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"),
        )
        for root, expected in authorities:
            head = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()
            status = subprocess.check_output(["git", "-C", root, "status", "--porcelain"], text=True)
            self.assertEqual(head, expected)
            self.assertEqual(status, "")

    def test_official_scenarios_and_configurable_converter_seams_remain_selected(self) -> None:
        self.assertEqual(FactorBasePropSetting().scen, "rdagent.scenarios.qlib.experiment.factor_experiment.QlibFactorScenario")
        self.assertEqual(ModelBasePropSetting().scen, "rdagent.scenarios.qlib.experiment.model_experiment.QlibModelScenario")
        with patch.dict(
            os.environ,
            {
                "QLIB_FACTOR_HYPOTHESIS2EXPERIMENT": "aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment",
                "QLIB_MODEL_HYPOTHESIS2EXPERIMENT": "aq_rdagent_official_us_binding.USQlibModelHypothesis2Experiment",
            },
        ):
            self.assertEqual(FactorBasePropSetting().hypothesis2experiment, "aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment")
            self.assertEqual(ModelBasePropSetting().hypothesis2experiment, "aq_rdagent_official_us_binding.USQlibModelHypothesis2Experiment")

    def test_factor_adapter_delegates_first_and_changes_only_new_workspaces(self) -> None:
        experiment = QlibFactorExperiment([])
        baseline = QlibFactorExperiment([])
        prior = QlibFactorExperiment([])
        prior_workspace = prior.experiment_workspace
        experiment.based_experiments = [baseline, prior]
        with patch.object(QlibFactorHypothesis2Experiment, "convert_response", return_value=experiment) as upstream:
            result = binding.USQlibFactorHypothesis2Experiment().convert_response("r", object(), object())
        upstream.assert_called_once()
        self.assertIs(result, experiment)
        self.assertIs(prior.experiment_workspace, prior_workspace)
        self.assertEqual(experiment.experiment_workspace.file_dict["conf_baseline.yaml"], (binding._TEMPLATES / "factor_template" / "conf_baseline.yaml").read_text())

    def test_model_adapter_delegates_first_and_changes_only_new_workspace(self) -> None:
        experiment = QlibModelExperiment([])
        original = experiment.experiment_workspace
        with patch.object(QlibModelHypothesis2Experiment, "convert_response", return_value=experiment) as upstream:
            result = binding.USQlibModelHypothesis2Experiment().convert_response("r", object(), object())
        upstream.assert_called_once()
        self.assertIs(result, experiment)
        self.assertIsNot(experiment.experiment_workspace, original)

    def test_templates_are_exact_official_templates_with_us_pit_configuration_only(self) -> None:
        pairs = ((binding._FACTOR_BASE, binding._TEMPLATES / "factor_template"), (binding._MODEL_BASE, binding._TEMPLATES / "model_template"))
        for base, overlay in pairs:
            for target in sorted(overlay.glob("*.yaml")):
                self.assertEqual(target.read_text(), expected_overlay(base / target.name))

    def test_templates_render_with_only_upstream_runner_context(self) -> None:
        environment = Environment(keep_trailing_newline=True)
        for target in sorted(binding._TEMPLATES.rglob("*.yaml")):
            rendered = environment.from_string(target.read_text()).render(**RENDER_CONTEXT)
            config = yaml.safe_load(rendered)
            self.assertEqual(config["qlib_init"]["provider_uri"], QLIB_PROVIDER_URI)
            self.assertEqual(config["qlib_init"]["region"], "us")
            self.assertEqual(config["qlib_init"]["calendar_provider"]["kwargs"]["backend"]["kwargs"]["provider_uri"], CALENDAR_PROVIDER_URI)
            self.assertEqual(config["market"], "p2_pit")
            self.assertEqual(config["benchmark"], "SPY")
            self.assertNotIn("cn_data", rendered)

    def test_official_non_yaml_template_files_remain_the_workspace_base(self) -> None:
        workspace = binding._workspace(binding._FACTOR_BASE, binding._TEMPLATES / "factor_template")
        for name in ("README.md", "read_exp_res.py"):
            self.assertEqual(workspace.file_dict[name], (binding._FACTOR_BASE / name).read_text())

    def test_binding_has_no_scenario_runner_recorder_llm_prompt_or_p2_code(self) -> None:
        source = Path(binding.__file__).read_text()
        tree = ast.parse(source)
        bases = {ast.unparse(base) for node in tree.body if isinstance(node, ast.ClassDef) for base in node.bases}
        self.assertEqual(bases, {"QlibFactorHypothesis2Experiment", "QlibModelHypothesis2Experiment"})
        for forbidden in ("Scenario", "prompt", "Runner", "Recorder", "LLM", "p2_pit"):
            self.assertNotIn(forbidden, source)

    def test_active_dvc_contract_uses_native_litellm_and_the_single_binding(self) -> None:
        stage = yaml.safe_load((TEST_FILE.parents[4] / "dvc.yaml").read_text())["stages"]["p3_rdagent_us_quant_research"]
        command = stage["cmd"]
        self.assertIn("BACKEND=rdagent.oai.backend.LiteLLMAPIBackend", command)
        self.assertIn("LITELLM_CHAT_MODEL=deepseek/deepseek-flash", command)
        self.assertIn("LITELLM_REASONING_EFFORT=high", command)
        self.assertIn("LITELLM_EMBEDDING_MODEL=ollama/qwen3-embedding:0.6b", command)
        self.assertIn("/home/zhou/AQ_ENVS/rdagent-v1.0.0/bin/rdagent fin_quant --loop-n 1", command)
        self.assertIn('AQ_REPO_ROOT="$(git rev-parse --show-toplevel)"', command)
        self.assertIn('PYTHONPATH="$AQ_REPO_ROOT/30-research-system/rd-agent/binding"', command)
        self.assertNotIn("/mnt/d/AUTONOMOUS_QUANT", command)
        self.assertIn("aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment", command)
        self.assertNotIn("aq_rdagent_us_binding", command)
        self.assertNotIn("ollama_chat", command)
        self.assertNotIn("QLIB_FACTOR_SCEN", command)
        self.assertNotIn("QLIB_QUANT_SCEN", command)
        self.assertIn("30-research-system/rd-agent/binding/aq_rdagent_official_us_binding.py", stage["deps"])


if __name__ == "__main__":
    unittest.main()
