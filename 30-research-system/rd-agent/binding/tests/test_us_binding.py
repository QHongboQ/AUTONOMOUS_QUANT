from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch


TEST_FILE = Path(__file__).resolve()
BINDING_ROOT = TEST_FILE.parents[1]
sys.path.insert(0, str(BINDING_ROOT))

FULL_SOURCE = "/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/full"
DEBUG_SOURCE = "/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/debug"
os.environ.update(
    {
        "FACTOR_COSTEER_DATA_FOLDER": FULL_SOURCE,
        "FACTOR_COSTEER_DATA_FOLDER_DEBUG": DEBUG_SOURCE,
        "QLIB_FACTOR_HYPOTHESIS2EXPERIMENT": "aq_rdagent_us_binding.USQlibFactorHypothesis2Experiment",
        "QLIB_MODEL_HYPOTHESIS2EXPERIMENT": "aq_rdagent_us_binding.USQlibModelHypothesis2Experiment",
        "QLIB_QUANT_FACTOR_HYPOTHESIS2EXPERIMENT": "aq_rdagent_us_binding.USQlibFactorHypothesis2Experiment",
        "QLIB_QUANT_MODEL_HYPOTHESIS2EXPERIMENT": "aq_rdagent_us_binding.USQlibModelHypothesis2Experiment",
        "QLIB_FACTOR_SCEN": "aq_rdagent_us_binding.USQlibFactorScenario",
        "QLIB_QUANT_SCEN": "aq_rdagent_us_binding.USQlibQuantScenario",
        "QLIB_FACTOR_TRAIN_START": "2015-01-02",
        "QLIB_FACTOR_TRAIN_END": "2019-12-31",
        "QLIB_FACTOR_VALID_START": "2020-01-02",
        "QLIB_FACTOR_VALID_END": "2021-12-31",
        "QLIB_FACTOR_TEST_START": "2022-01-03",
        "QLIB_FACTOR_TEST_END": "2024-12-31",
        "QLIB_MODEL_TRAIN_START": "2015-01-02",
        "QLIB_MODEL_TRAIN_END": "2019-12-31",
        "QLIB_MODEL_VALID_START": "2020-01-02",
        "QLIB_MODEL_VALID_END": "2021-12-31",
        "QLIB_MODEL_TEST_START": "2022-01-03",
        "QLIB_MODEL_TEST_END": "2024-12-31",
        "QLIB_QUANT_TRAIN_START": "2015-01-02",
        "QLIB_QUANT_TRAIN_END": "2019-12-31",
        "QLIB_QUANT_VALID_START": "2020-01-02",
        "QLIB_QUANT_VALID_END": "2021-12-31",
        "QLIB_QUANT_TEST_START": "2022-01-03",
        "QLIB_QUANT_TEST_END": "2024-12-31",
    }
)

import yaml
from jinja2 import Environment, StrictUndefined

import aq_rdagent_us_binding as binding
from rdagent.app.qlib_rd_loop.conf import (
    FactorBasePropSetting,
    ModelBasePropSetting,
    QuantBasePropSetting,
)
from rdagent.core.conf import RD_AGENT_SETTINGS
from rdagent.core.proposal import ExperimentFeedback, Hypothesis, Trace
from rdagent.core.utils import import_class
from rdagent.scenarios.qlib.developer.factor_coder import QlibFactorCoSTEER
from rdagent.scenarios.qlib.developer.factor_runner import QlibFactorRunner
from rdagent.scenarios.qlib.developer.model_coder import QlibModelCoSTEER
from rdagent.scenarios.qlib.developer.model_runner import QlibModelRunner
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorExperiment
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelExperiment


# Test discovery may import the sibling materializer first, which imports this
# package before the process-local test settings above are present. Bind the
# already-created upstream settings singleton explicitly so suite order cannot
# weaken or bypass the production path guard.
binding.FACTOR_COSTEER_SETTINGS.data_folder = FULL_SOURCE
binding.FACTOR_COSTEER_SETTINGS.data_folder_debug = DEBUG_SOURCE


def hypothesis() -> Hypothesis:
    return Hypothesis("h", "r", "cr", "co", "cj", "ck")


def accepted() -> ExperimentFeedback:
    return ExperimentFeedback("accepted", decision=True)


class USBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        RD_AGENT_SETTINGS.workspace_path = Path(self.temporary.name) / "workspaces"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_exact_settings_resolve_six_project_bindings(self) -> None:
        factor = FactorBasePropSetting()
        model = ModelBasePropSetting()
        quant = QuantBasePropSetting()
        paths = [
            (factor.hypothesis2experiment, binding.USQlibFactorHypothesis2Experiment),
            (model.hypothesis2experiment, binding.USQlibModelHypothesis2Experiment),
            (quant.factor_hypothesis2experiment, binding.USQlibFactorHypothesis2Experiment),
            (quant.model_hypothesis2experiment, binding.USQlibModelHypothesis2Experiment),
            (factor.scen, binding.USQlibFactorScenario),
            (quant.scen, binding.USQlibQuantScenario),
        ]
        self.assertEqual(len(paths), 6)
        for path, expected in paths:
            self.assertIs(import_class(path), expected)
        self.assertEqual(factor.runner, "rdagent.scenarios.qlib.developer.factor_runner.QlibFactorRunner")
        self.assertEqual(model.runner, "rdagent.scenarios.qlib.developer.model_runner.QlibModelRunner")
        self.assertEqual(quant.factor_runner, factor.runner)
        self.assertEqual(quant.model_runner, model.runner)
        self.assertEqual(factor.coder, "rdagent.scenarios.qlib.developer.factor_coder.QlibFactorCoSTEER")
        self.assertEqual(model.coder, "rdagent.scenarios.qlib.developer.model_coder.QlibModelCoSTEER")
        self.assertEqual(quant.factor_coder, factor.coder)
        self.assertEqual(quant.model_coder, model.coder)
        for setting in (factor, model, quant):
            self.assertEqual(
                (
                    setting.train_start, setting.train_end, setting.valid_start,
                    setting.valid_end, setting.test_start, setting.test_end,
                ),
                ("2015-01-02", "2019-12-31", "2020-01-02", "2021-12-31", "2022-01-03", "2024-12-31"),
            )

    def test_factor_converter_rebinds_only_new_workspaces(self) -> None:
        trace = Trace(object())
        prior = QlibFactorExperiment([])
        prior.result = {"IC": 0.01}
        prior_workspace = prior.experiment_workspace
        trace.hist.append((prior, accepted()))
        response = json.dumps(
            {"f": {"description": "d", "formulation": "$close", "variables": ["$close"]}}
        )
        experiment = binding.USQlibFactorHypothesis2Experiment().convert_response(
            response, hypothesis(), trace
        )
        self.assertIs(type(experiment), QlibFactorExperiment)
        self.assertEqual([task.factor_name for task in experiment.tasks], ["f"])
        self.assertTrue(binding._workspace_uses_template(experiment.experiment_workspace, binding.FACTOR_TEMPLATE_ROOT))
        self.assertTrue(binding._workspace_uses_template(experiment.based_experiments[0].experiment_workspace, binding.FACTOR_TEMPLATE_ROOT))
        self.assertIs(experiment.based_experiments[1], prior)
        self.assertIs(prior.experiment_workspace, prior_workspace)

    def test_factor_incomplete_unsafe_trace_fails_closed(self) -> None:
        trace = Trace(object())
        trace.hist.append((QlibFactorExperiment([]), accepted()))
        response = json.dumps(
            {"f": {"description": "d", "formulation": "$close", "variables": ["$close"]}}
        )
        with self.assertRaisesRegex(RuntimeError, "incomplete prior"):
            binding.USQlibFactorHypothesis2Experiment().convert_response(response, hypothesis(), trace)

    def test_model_converter_rebinds_primary_and_preserves_history(self) -> None:
        trace = Trace(object())
        prior = QlibModelExperiment([])
        prior.result = {"IC": 0.01}
        prior_workspace = prior.experiment_workspace
        trace.hist.append((prior, accepted()))
        response = json.dumps(
            {
                "m": {
                    "description": "d",
                    "formulation": "f",
                    "architecture": "a",
                    "variables": ["$close"],
                    "hyperparameters": {},
                    "training_hyperparameters": {},
                    "model_type": "Tabular",
                }
            }
        )
        experiment = binding.USQlibModelHypothesis2Experiment().convert_response(
            response, hypothesis(), trace
        )
        self.assertIs(type(experiment), QlibModelExperiment)
        self.assertTrue(binding._workspace_uses_template(experiment.experiment_workspace, binding.MODEL_TEMPLATE_ROOT))
        self.assertEqual(experiment.based_experiments, [prior])
        self.assertIs(prior.experiment_workspace, prior_workspace)

    def test_model_incomplete_unsafe_trace_fails_closed(self) -> None:
        trace = Trace(object())
        trace.hist.append((QlibModelExperiment([]), accepted()))
        response = json.dumps(
            {
                "m": {
                    "description": "d", "formulation": "f", "architecture": "a",
                    "variables": [], "hyperparameters": {}, "training_hyperparameters": {},
                    "model_type": "Tabular",
                }
            }
        )
        with self.assertRaisesRegex(RuntimeError, "incomplete prior"):
            binding.USQlibModelHypothesis2Experiment().convert_response(response, hypothesis(), trace)

    def test_template_inventory_hashes_and_rendering(self) -> None:
        binding.validate_template_family()
        context = {
            "train_start": "2015-01-02", "train_end": "2019-12-31",
            "valid_start": "2020-01-02", "valid_end": "2021-12-31",
            "test_start": "2022-01-03", "test_end": "2024-12-31",
            "feature_expressions": ["$close"], "feature_names": ["F0"],
            "n_epochs": 1, "lr": 0.001, "early_stop": 1, "batch_size": 8,
            "weight_decay": 0.0, "num_features": 1, "num_timesteps": None,
            "step_len": None, "dataset_cls": "DatasetH",
        }
        for relative in binding.TEMPLATE_HASHES:
            text = (binding.TEMPLATE_ROOT / relative).read_text(encoding="utf-8")
            rendered = Environment(undefined=StrictUndefined).from_string(text).render(**context)
            config = yaml.safe_load(rendered)
            self.assertEqual(config["qlib_init"]["region"], "us")
            self.assertEqual(config["market"], "p2_pit")
            self.assertNotIn("Fillna", rendered)

    def test_template_hash_tamper_fails_closed(self) -> None:
        with patch.dict(binding.TEMPLATE_HASHES, {next(iter(binding.TEMPLATE_HASHES)): "0" * 64}):
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                binding.validate_template_family()

    def test_template_hash_is_checkout_newline_stable(self) -> None:
        lf = Path(self.temporary.name) / "lf.yaml"
        crlf = Path(self.temporary.name) / "crlf.yaml"
        lf.write_bytes(b"key: value\n")
        crlf.write_bytes(b"key: value\r\n")
        self.assertEqual(binding._text_sha256(lf), binding._text_sha256(crlf))

    def test_factor_and_quant_scenarios_use_source_without_generator(self) -> None:
        with patch(
            "rdagent.scenarios.qlib.experiment.utils.generate_data_folder_from_qlib",
            side_effect=AssertionError("China generator selected"),
        ) as generator, patch.object(
            binding.USQlibFactorScenario, "get_runtime_environment", return_value="pinned runtime"
        ):
            factor = binding.USQlibFactorScenario()
            quant = binding.USQlibQuantScenario()
        self.assertIn("daily_pv.h5", factor.get_source_data_desc())
        self.assertIn("daily_pv.h5", quant.get_source_data_desc())
        generator.assert_not_called()

    def test_wrong_factor_source_path_fails_before_upstream_constructor(self) -> None:
        with patch.object(binding.FACTOR_COSTEER_SETTINGS, "data_folder", "/tmp/not-approved"), patch.object(
            binding.QlibFactorScenario, "__init__"
        ) as upstream:
            with self.assertRaisesRegex(RuntimeError, "not the approved"):
                binding.USQlibFactorScenario()
        upstream.assert_not_called()

    def test_upstream_runner_selection_matches_five_file_inventory(self) -> None:
        requested = set(
            re.findall(
                r'qlib_config_name=["\']([^"\']+\.yaml)["\']',
                inspect.getsource(QlibFactorRunner) + inspect.getsource(QlibModelRunner),
            )
        )
        self.assertEqual(requested, {Path(path).name for path in binding.TEMPLATE_HASHES})
        self.assertIs(QlibFactorRunner.__module__.startswith("rdagent."), True)
        self.assertIs(QlibModelRunner.__module__.startswith("rdagent."), True)
        self.assertIs(QlibFactorCoSTEER.__module__.startswith("rdagent."), True)
        self.assertIs(QlibModelCoSTEER.__module__.startswith("rdagent."), True)

    def test_no_active_china_defaults_or_runtime_network_path(self) -> None:
        forbidden = (
            "~/.qlib/qlib_data/cn_data", "region: cn", "market: csi300", "benchmark: SH000300"
        )
        combined = "\n".join(
            (binding.TEMPLATE_ROOT / relative).read_text(encoding="utf-8")
            for relative in binding.TEMPLATE_HASHES
        )
        self.assertTrue(all(value not in combined for value in forbidden))
        source = inspect.getsource(binding)
        self.assertNotIn("requests", source)
        self.assertNotIn("httpx", source)
        self.assertNotIn("generate_data_folder_from_qlib", source)


if __name__ == "__main__":
    unittest.main()
