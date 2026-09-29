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


REPLACEMENTS = (
    ('provider_uri: "~/.qlib/qlib_data/cn_data"', 'provider_uri: "{{ provider_uri }}"'),
    ("region: cn", "region: {{ region }}"),
    ("market: &market csi300", "market: &market {{ market }}"),
    ("benchmark: &benchmark SH000300", "benchmark: &benchmark {{ benchmark }}"),
    ("limit_threshold: 0.095", "limit_threshold: {{ limit_threshold }}"),
    (
        "    region: {{ region }}\n",
        """    region: {{ region }}
    {% if calendar_provider_uri %}
    calendar_provider:
        class: LocalCalendarProvider
        module_path: qlib.data.data
        kwargs:
            backend:
                class: FileCalendarStorage
                module_path: qlib.data.storage.file_storage
                kwargs:
                    provider_uri: "{{ calendar_provider_uri }}"
    {% endif %}
""",
    ),
)

CALENDAR_PROVIDER_URI = "/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime"
RENDER_CONTEXT = {
    "provider_uri": "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data",
    "region": "us",
    "market": "p2_pit",
    "benchmark": {"market": "p2_pit", "filter_pipe": []},
    "limit_threshold": 0.095,
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
        self.assertEqual(
            FactorBasePropSetting().scen,
            "rdagent.scenarios.qlib.experiment.factor_experiment.QlibFactorScenario",
        )
        self.assertEqual(
            ModelBasePropSetting().scen,
            "rdagent.scenarios.qlib.experiment.model_experiment.QlibModelScenario",
        )
        with patch.dict(
            os.environ,
            {
                "QLIB_FACTOR_HYPOTHESIS2EXPERIMENT": (
                    "aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment"
                ),
                "QLIB_MODEL_HYPOTHESIS2EXPERIMENT": (
                    "aq_rdagent_official_us_binding.USQlibModelHypothesis2Experiment"
                ),
            },
        ):
            self.assertEqual(
                FactorBasePropSetting().hypothesis2experiment,
                "aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment",
            )
            self.assertEqual(
                ModelBasePropSetting().hypothesis2experiment,
                "aq_rdagent_official_us_binding.USQlibModelHypothesis2Experiment",
            )

    def test_factor_adapter_delegates_first_and_changes_only_new_workspaces(self) -> None:
        experiment = QlibFactorExperiment([])
        baseline = QlibFactorExperiment([])
        prior = QlibFactorExperiment([])
        prior_workspace = prior.experiment_workspace
        experiment.based_experiments = [baseline, prior]
        with patch.object(
            QlibFactorHypothesis2Experiment, "convert_response", return_value=experiment
        ) as upstream:
            result = binding.USQlibFactorHypothesis2Experiment().convert_response("r", object(), object())
        upstream.assert_called_once()
        self.assertIs(result, experiment)
        self.assertIs(prior.experiment_workspace, prior_workspace)
        self.assertEqual(
            experiment.experiment_workspace.file_dict["conf_baseline.yaml"],
            (binding._TEMPLATES / "factor_template" / "conf_baseline.yaml").read_text(),
        )
        self.assertEqual(
            baseline.experiment_workspace.file_dict["conf_baseline.yaml"],
            (binding._TEMPLATES / "factor_template" / "conf_baseline.yaml").read_text(),
        )

    def test_model_adapter_delegates_first_and_changes_only_new_workspace(self) -> None:
        experiment = QlibModelExperiment([])
        original = experiment.experiment_workspace
        with patch.object(
            QlibModelHypothesis2Experiment, "convert_response", return_value=experiment
        ) as upstream:
            result = binding.USQlibModelHypothesis2Experiment().convert_response("r", object(), object())
        upstream.assert_called_once()
        self.assertIs(result, experiment)
        self.assertIsNot(experiment.experiment_workspace, original)
        self.assertEqual(
            experiment.experiment_workspace.file_dict["conf_baseline_factors_model.yaml"],
            (binding._TEMPLATES / "model_template" / "conf_baseline_factors_model.yaml").read_text(),
        )

    def test_overlays_are_exact_official_templates_with_six_authorized_deltas(self) -> None:
        pairs = (
            (binding._FACTOR_BASE, binding._TEMPLATES / "factor_template"),
            (binding._MODEL_BASE, binding._TEMPLATES / "model_template"),
        )
        for base, overlay in pairs:
            for target in sorted(overlay.glob("*.yaml")):
                expected = (base / target.name).read_text()
                for original, replacement in REPLACEMENTS:
                    self.assertEqual(expected.count(original), 1)
                    expected = expected.replace(original, replacement)
                self.assertEqual(target.read_text(), expected)

    def test_calendar_provider_is_optional_and_uses_qlib_native_configuration(self) -> None:
        environment = Environment(keep_trailing_newline=True)
        for target in sorted(binding._TEMPLATES.rglob("*.yaml")):
            template = environment.from_string(target.read_text())

            without_calendar = yaml.safe_load(template.render(**RENDER_CONTEXT))
            self.assertNotIn("calendar_provider", without_calendar["qlib_init"])

            with_calendar = yaml.safe_load(
                template.render(**RENDER_CONTEXT, calendar_provider_uri=CALENDAR_PROVIDER_URI)
            )
            self.assertEqual(
                with_calendar["qlib_init"]["calendar_provider"],
                {
                    "class": "LocalCalendarProvider",
                    "module_path": "qlib.data.data",
                    "kwargs": {
                        "backend": {
                            "class": "FileCalendarStorage",
                            "module_path": "qlib.data.storage.file_storage",
                            "kwargs": {"provider_uri": CALENDAR_PROVIDER_URI},
                        }
                    },
                },
            )

    def test_official_non_yaml_template_files_remain_the_workspace_base(self) -> None:
        workspace = binding._workspace(binding._FACTOR_BASE, binding._TEMPLATES / "factor_template")
        for name in ("README.md", "read_exp_res.py"):
            self.assertEqual(workspace.file_dict[name], (binding._FACTOR_BASE / name).read_text())

    def test_binding_has_no_scenario_runner_recorder_llm_prompt_or_p2_code(self) -> None:
        source_path = Path(binding.__file__)
        source = source_path.read_text()
        tree = ast.parse(source)
        bases = {
            ast.unparse(base)
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            for base in node.bases
        }
        self.assertEqual(
            bases,
            {"QlibFactorHypothesis2Experiment", "QlibModelHypothesis2Experiment"},
        )
        combined = source + "\n" + "\n".join(
            path.read_text() for path in sorted(binding._TEMPLATES.rglob("*.yaml"))
        )
        for forbidden in ("Scenario", "prompt", "Runner", "Recorder", "LLM", "p2_pit"):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
