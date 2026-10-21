from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aq_rdagent_semantic_bridge import (
    P12QlibCorrelationRecord,
    _CURRENT_EXECUTION,
    _correlation_config_text,
    _install_qlib_execute_hook,
    build_semantic_loop_class,
    capture_trace_semantics,
    invoke_upstream_main,
    run_native_quant,
)


class FactorTask:
    def __init__(self, name: str, formulation: str = "f"):
        self.name = name
        self.version = 1
        self.description = "description"
        self.factor_name = name
        self.factor_formulation = formulation
        self.variables = {"close": "$close"}
        self.factor_resources = None
        self.factor_implementation = False
        self.base_code = None
        self.user_instructions = None


class ModelTask:
    def __init__(self, name: str):
        self.name = name
        self.version = 1
        self.description = "description"
        self.architecture = "GRU"
        self.formulation = None
        self.variables = "features"
        self.hyperparameters = {"hidden": "32"}
        self.training_hyperparameters = {"epochs": "5"}
        self.model_type = "TimesSeries"
        self.base_code = None
        self.user_instructions = None


FactorTask.__module__ = "rdagent.components.coder.factor_coder.factor"
ModelTask.__module__ = "rdagent.components.coder.model_coder.model"


class Hypothesis:
    def __init__(self, text: str, action: str):
        self.hypothesis = text
        self.reason = "reason"
        self.concise_reason = "concise"
        self.concise_observation = "observation"
        self.concise_justification = "justification"
        self.concise_knowledge = "knowledge"
        self.action = action


class Workspace:
    def __init__(self, task: object, path: Path, code: str):
        self.target_task = task
        self.workspace_path = path
        self.file_dict = {"factor.py": code}


class Experiment:
    def __init__(self, task: object, hypothesis: Hypothesis, workspace: Workspace, based=()):
        self.hypothesis = hypothesis
        self.sub_tasks = [task]
        self.sub_workspace_list = [workspace]
        self.based_experiments = list(based)
        self.plan = {"features": {"close": "$close"}}
        self.base_features = {"close": "$close"}
        self.base_feature_codes = {}


class SemanticBridgeTests(unittest.TestCase):
    def _experiment(self, root: Path, name: str, *, action: str = "factor", parent=None):
        task = FactorTask(name) if action == "factor" else ModelTask(name)
        code = f"value = {name!r}\n"
        path = root / f"workspace-{name}"
        path.mkdir()
        (path / "factor.py").write_bytes(code.encode("utf-8"))
        workspace = Workspace(task, path, code)
        exp = Experiment(task, Hypothesis(f"test {name}", action), workspace)
        template_path = root / f"template-{name}"
        template_path.mkdir()
        template = "provider: pinned-qlib-template\n"
        (template_path / "conf_baseline.yaml").write_bytes(template.encode("utf-8"))
        exp.experiment_workspace = Workspace(None, template_path, "")
        exp.experiment_workspace.file_dict = {"conf_baseline.yaml": template}
        if parent is not None:
            exp.based_experiments = [parent.sub_workspace_list[0]]
        return exp

    def test_hypothesis_task_and_experiment_content_identities(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            exp = self._experiment(root, "alpha")
            trace = SimpleNamespace(hist=[(exp, object())], dag_parent=[()])
            first = capture_trace_semantics(trace, request_id="req", attempt_id="att", workspace_root=root)
            second = capture_trace_semantics(trace, request_id="req", attempt_id="att", workspace_root=root)
        selected = first["experiments"][0]
        self.assertEqual(selected["hypothesis"]["content_sha256"], second["experiments"][0]["hypothesis"]["content_sha256"])
        self.assertEqual(selected["tasks"][0]["branch"], "factor")
        self.assertEqual(selected["identity_sha256"], first["selected_experiment_identity_sha256"])
        self.assertEqual(selected["lineage"]["status"], "OBSERVED")
        self.assertNotIn("test alpha", json.dumps(first))

    def test_factor_and_model_tasks_have_distinct_type_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            factor = self._experiment(root, "same", action="factor")
            model = self._experiment(root, "same-model", action="model")
            a = capture_trace_semantics(SimpleNamespace(hist=[(factor, None)], dag_parent=[()]),
                                        request_id="r", attempt_id="a", workspace_root=root)
            b = capture_trace_semantics(SimpleNamespace(hist=[(model, None)], dag_parent=[()]),
                                        request_id="r", attempt_id="a", workspace_root=root)
        self.assertNotEqual(a["experiments"][0]["tasks"][0]["identity_sha256"],
                            b["experiments"][0]["tasks"][0]["identity_sha256"])
        self.assertEqual(b["experiments"][0]["tasks"][0]["branch"], "model")

    def test_experiment_structure_code_hash_and_parent_lineage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self._experiment(root, "first")
            second = self._experiment(root, "second", parent=first)
            trace = SimpleNamespace(hist=[(first, None), (second, None)], dag_parent=[(), (0,)])
            result = capture_trace_semantics(trace, request_id="r", attempt_id="a", workspace_root=root)
        selected = result["experiments"][1]
        self.assertEqual(selected["lineage"]["parent_experiment_ids"], [result["experiments"][0]["identity_sha256"]])
        self.assertEqual(len(selected["based_experiments"]), 1)
        self.assertEqual(len(selected["based_experiments"][0]["identity_sha256"]), 64)
        code = b"value = 'second'\n"
        self.assertEqual(selected["generated_code"]["files"][0]["sha256"], hashlib.sha256(code).hexdigest())
        self.assertEqual(result["selected_experiment_identity_sha256"], selected["identity_sha256"])

    def test_multiple_experiments_select_only_latest_recorded_experiment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            factor = self._experiment(root, "factor")
            model = self._experiment(root, "model", action="model")
            result = capture_trace_semantics(
                SimpleNamespace(hist=[(factor, None), (model, None)], dag_parent=[(), ()]),
                request_id="r", attempt_id="a", workspace_root=root,
            )
        self.assertEqual(result["experiments"][-1]["tasks"][0]["branch"], "model")
        self.assertEqual(result["selected_experiment_identity_sha256"], result["experiments"][-1]["identity_sha256"])
        self.assertNotEqual(result["selected_experiment_identity_sha256"], result["experiments"][0]["identity_sha256"])

    def test_unreadable_final_experiment_does_not_fall_back_to_an_older_experiment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self._experiment(root, "first-valid")
            final = self._experiment(root, "final-corrupt")
            final.sub_workspace_list[0].workspace_path.joinpath("factor.py").write_text(
                "bytes differ from the trusted in-memory workspace\n", encoding="utf-8"
            )
            result = capture_trace_semantics(
                SimpleNamespace(hist=[(first, None), (final, None)], dag_parent=[(), (0,)]),
                request_id="r", attempt_id="a", workspace_root=root,
            )
        self.assertEqual(result["status"], "PARTIAL")
        self.assertIsNone(result["selected_experiment_identity_sha256"])
        self.assertEqual(len(result["experiments"]), 1)

    def test_missing_semantics_stays_partial_and_recorder_binding_is_not_inferred(self):
        with self.assertRaisesRegex(ValueError, "TRACE_HISTORY_OR_LINEAGE_UNAVAILABLE"):
            capture_trace_semantics(SimpleNamespace(hist=[], dag_parent=[]),
                                    request_id="r", attempt_id="a", workspace_root=Path("/tmp"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            exp = self._experiment(root, "partial")
            result = capture_trace_semantics(SimpleNamespace(hist=[(exp, None)], dag_parent=[()]),
                                             request_id="r", attempt_id="a", workspace_root=root)
        self.assertEqual(result["qlib_recorder_binding"]["status"], "PARTIAL")

    def test_experiment_and_recorder_pairing_is_explicitly_unproven_and_pickle_is_never_loaded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            exp = self._experiment(root, "unpaired")
            result = capture_trace_semantics(SimpleNamespace(hist=[(exp, None)], dag_parent=[()]),
                                             request_id="r", attempt_id="a", workspace_root=root)
        self.assertEqual(result["qlib_recorder_binding"]["status"], "PARTIAL")
        self.assertIn("NO_NATIVE_QLIB_RECORDER_BINDING", result["qlib_recorder_binding"]["reason"])
        self.assertNotIn("pickle.load", inspect.getsource(capture_trace_semantics))

    def test_qrun_native_record_hook_binds_the_active_recorder(self):
        import os
        import re
        import json
        import types
        from pathlib import Path
        from unittest.mock import patch

        request_id = "sha256:" + hashlib.sha256(b"request").hexdigest()
        attempt_id = "attempt-1"
        experiment_identity = {
            "identity_sha256": hashlib.sha256(b"experiment").hexdigest(),
            "tasks": [{"identity_sha256": hashlib.sha256(b"task").hexdigest()}],
            "generated_code": {"manifest_sha256": hashlib.sha256(b"code").hexdigest()},
            "experiment_template": {"identity_sha256": hashlib.sha256(b"template").hexdigest()},
        }
        trace = SimpleNamespace(_p12_qlib_recorder_bindings=[])
        context = {
            "request_id": request_id, "attempt_id": attempt_id,
            "experiment_identity": experiment_identity,
            "execution_count": 0, "trace": trace,
        }
        config = "task:\n    record:\n        - class: Existing\n          module_path: existing.module\n"

        class Client:
            def __init__(self, tracking_uri):
                self.uri = tracking_uri
            def get_experiment_by_name(self, name):
                return None
            def create_experiment(self, name, artifact_location, tags):
                self.name, self.location, self.tags = name, artifact_location, tags
                return "exp-native-1"
            def get_experiment(self, experiment_id):
                return SimpleNamespace(
                    name=self.name, artifact_location=self.location, tags=self.tags,
                )

        class Recorder:
            info = {"experiment_id": "exp-native-1", "id": "run-native-1", "status": "RUNNING"}
            tags = None
            def set_tags(self, **tags):
                self.tags = tags

        recorder = Recorder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "conf.yaml").write_bytes(config.encode("utf-8"))
            workspace = SimpleNamespace(file_dict={"conf.yaml": config}, workspace_path=root)
            client_module = types.ModuleType("mlflow.tracking")
            client_module.MlflowClient = Client
            mlflow_module = types.ModuleType("mlflow")
            mlflow_module.tracking = client_module

            def execute(_workspace, config_name, run_env, *args, **kwargs):
                self.assertEqual(run_env, {"fixed": "env"})
                augmented = (root / config_name).read_text(encoding="utf-8")
                self.assertIn("class: Existing", augmented)
                self.assertIn("class: P12QlibCorrelationRecord", augmented)
                encoded = re.search(r"marker_json: (\".*\")", augmented).group(1)
                marker_json = json.loads(encoded)
                hook = P12QlibCorrelationRecord(recorder, marker_json, re.search(
                    r"receipt_name: (\".*\")", augmented
                ).group(1).strip('"'))
                hook.generate()
                return "native-qrun-result"

            with patch.dict(os.environ, {
                "QLIB_MLFLOW_URI": "sqlite:///test.db",
                "P12_MLFLOW_ARTIFACT_VOLUME": "artifact-volume-1",
            }), patch.dict(sys.modules, {"mlflow": mlflow_module, "mlflow.tracking": client_module}), \
                 patch("pathlib.Path.cwd", return_value=root):
                wrapped_execute = _install_qlib_execute_hook(execute)
                token = _CURRENT_EXECUTION.set(context)
                try:
                    result = wrapped_execute(workspace, "conf.yaml", {"fixed": "env"})
                    with self.assertRaisesRegex(ValueError, "QLIB_CONFIG_NAME_NOT_A_SAFE_BASENAME"):
                        wrapped_execute(workspace, "../conf.yaml", {"fixed": "env"})
                finally:
                    _CURRENT_EXECUTION.reset(token)

        self.assertEqual(result, "native-qrun-result")
        self.assertEqual(len(trace._p12_qlib_recorder_bindings), 1)
        binding = trace._p12_qlib_recorder_bindings[0]
        self.assertEqual(binding["qlib_experiment_id"], "exp-native-1")
        self.assertEqual(binding["qlib_recorder_run_id"], "run-native-1")
        self.assertEqual(binding["request_id"], request_id)
        self.assertEqual(binding["attempt_id"], attempt_id)
        self.assertEqual(recorder.tags["aq.p12.correlation_sha256"], binding["marker_sha256"])
        self.assertRegex(binding["receipt_sha256"], r"^[0-9a-f]{64}$")

    def test_correlation_config_rejects_unbounded_or_ambiguous_yaml_shape(self):
        marker = {"request_id": "r", "attempt_id": "a", "correlation_sha256": "0" * 64}
        source = "task:\n    record:\n        - class: Existing\n"
        augmented = _correlation_config_text(
            source, experiment_name="aq-p12-test", marker=marker,
            receipt_name=".p12-qlib-correlation-test.json",
        )
        self.assertIn('experiment_name: "aq-p12-test"', augmented)
        self.assertIn("class: Existing", augmented)
        self.assertIn("class: P12QlibCorrelationRecord", augmented)
        with self.assertRaisesRegex(ValueError, "QLIB_CONFIG_ALREADY_HAS_RUNTIME_OVERRIDE"):
            _correlation_config_text(
                "experiment_name: existing\n" + source,
                experiment_name="aq-p12-test", marker=marker,
                receipt_name=".p12-qlib-correlation-test.json",
            )
        with self.assertRaisesRegex(ValueError, "QLIB_TASK_RECORD_LIST_UNAVAILABLE"):
            _correlation_config_text(
                "task:\n    model: {}\n", experiment_name="aq-p12-test",
                marker=marker, receipt_name=".p12-qlib-correlation-test.json",
            )

    def test_record_hook_keeps_super_order_and_failure_semantics(self):
        events = []

        class Base:
            steps = ["direct_exp_gen", "coding", "running", "feedback", "record"]
            def record(self, value):
                events.append(("base", value))
                return "base-result"

        loop_type = build_semantic_loop_class(Base, lambda trace: events.append(("evidence", trace)))
        instance = loop_type()
        instance.trace = "native-trace"
        self.assertEqual(instance.record("out"), "base-result")
        self.assertEqual(events, [("base", "out"), ("evidence", "native-trace")])
        self.assertEqual(loop_type.steps, Base.steps)

        class FailingBase:
            steps = ["record"]
            def record(self, value):
                raise RuntimeError("upstream error")

        called = []
        failing = build_semantic_loop_class(FailingBase, lambda trace: called.append(trace))()
        failing.trace = object()
        with self.assertRaisesRegex(RuntimeError, "upstream error"):
            failing.record({})
        self.assertEqual(called, [])

    def test_upstream_main_invocation_matches_fin_quant_cli_arguments(self):
        seen = {}
        def main(**kwargs):
            seen.update(kwargs)
            return "delegated"
        module = SimpleNamespace(main=main)
        self.assertEqual(invoke_upstream_main(module, loop_n=1), "delegated")
        self.assertEqual(seen, {
            "path": None, "step_n": None, "loop_n": 1,
            "all_duration": None, "checkout": True,
        })
        with self.assertRaises(ValueError):
            invoke_upstream_main(module, loop_n=2)

    def test_native_wrapper_patches_only_loop_class_and_delegates_cli_arguments(self):
        seen = {}

        class NativeLoop:
            steps = ["direct_exp_gen", "coding", "running", "feedback", "record"]

        def main(**kwargs):
            seen.update(kwargs)
            return "upstream-result"

        module = SimpleNamespace(QuantRDLoop=NativeLoop, main=main)
        fake_dotenv = SimpleNamespace(load_dotenv=lambda path: None)
        with patch.dict(sys.modules, {"dotenv": fake_dotenv}):
            result = run_native_quant(quant_module=module)

        self.assertEqual(result, "upstream-result")
        self.assertEqual(seen, {
            "path": None, "step_n": None, "loop_n": 1,
            "all_duration": None, "checkout": True,
        })
        self.assertTrue(issubclass(module.QuantRDLoop, NativeLoop))
        self.assertEqual(module.QuantRDLoop.steps, NativeLoop.steps)
        with self.assertRaises(ValueError):
            run_native_quant(2, quant_module=module)

    def test_pinned_quant_rd_loop_steps_are_unchanged_when_runtime_is_available(self):
        try:
            from rdagent.app.qlib_rd_loop.quant import QuantRDLoop
        except ImportError:
            self.skipTest("pinned RD-Agent runtime is not installed in this test interpreter")
        extended = build_semantic_loop_class(QuantRDLoop, lambda trace: None)
        self.assertEqual(extended.steps, QuantRDLoop.steps)
        self.assertEqual(extended.steps[-1], "record")
        self.assertEqual(extended.steps.count("record"), 1)

    def test_pinned_qlib_config_loader_resolves_native_correlation_record(self):
        try:
            import yaml
            from qlib.utils import init_instance_by_config
        except ImportError:
            self.skipTest("pinned Qlib runtime is not installed in this test interpreter")
        import hashlib
        from pathlib import Path
        from unittest.mock import patch

        marker_body = {
            "request_id": "request-fixture", "attempt_id": "attempt-fixture",
            "rdagent_experiment_identity_sha256": hashlib.sha256(b"experiment").hexdigest(),
            "rdagent_task_identity_sha256s": [hashlib.sha256(b"task").hexdigest()],
            "generated_code_manifest_sha256": hashlib.sha256(b"code").hexdigest(),
            "experiment_template_identity_sha256": hashlib.sha256(b"template").hexdigest(),
            "qlib_config_template_sha256": hashlib.sha256(b"config").hexdigest(),
            "execution_index": 0,
        }
        marker = {
            **marker_body,
            "correlation_sha256": hashlib.sha256(json.dumps(
                marker_body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            ).encode()).hexdigest(),
        }
        source = "task:\n    record:\n        - class: Existing\n          module_path: existing.module\n"
        rendered = _correlation_config_text(
            source, experiment_name="aq-p12-runtime-test", marker=marker,
            receipt_name=".p12-qlib-correlation-test.json",
        )
        parsed = yaml.safe_load(rendered)
        self.assertEqual(parsed["experiment_name"], "aq-p12-runtime-test")
        self.assertEqual(len(parsed["task"]["record"]), 2)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class Recorder:
                info = {"experiment_id": "exp", "id": "run", "status": "RUNNING"}
                def set_tags(self, **tags):
                    self.tags = tags
            recorder = Recorder()
            with patch("pathlib.Path.cwd", return_value=root):
                record = init_instance_by_config(
                    parsed["task"]["record"][-1], recorder=recorder,
                    default_module="qlib.workflow.record_temp",
                )
                self.assertIsInstance(record, P12QlibCorrelationRecord)
                record.generate()
            receipt = json.loads((root / ".p12-qlib-correlation-test.json").read_text())
            self.assertEqual(receipt["qlib_experiment_id"], "exp")
            self.assertEqual(receipt["qlib_recorder_run_id"], "run")
            self.assertEqual(recorder.tags["aq.p12.request_id"], "request-fixture")


if __name__ == "__main__":
    unittest.main()
