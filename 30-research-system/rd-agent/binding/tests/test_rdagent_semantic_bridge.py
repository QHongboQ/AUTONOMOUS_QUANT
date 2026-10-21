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
        self.assertEqual(result["qlib_recorder_binding"]["status"], "SEMANTIC_BINDING_PARTIAL")

    def test_experiment_and_recorder_pairing_is_explicitly_unproven_and_pickle_is_never_loaded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            exp = self._experiment(root, "unpaired")
            result = capture_trace_semantics(SimpleNamespace(hist=[(exp, None)], dag_parent=[()]),
                                             request_id="r", attempt_id="a", workspace_root=root)
        self.assertEqual(result["qlib_recorder_binding"]["status"], "SEMANTIC_BINDING_PARTIAL")
        self.assertIn("DOES_NOT_EXPOSE_RECORDER_ID", result["qlib_recorder_binding"]["reason"])
        self.assertNotIn("pickle.load", inspect.getsource(capture_trace_semantics))

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


if __name__ == "__main__":
    unittest.main()
