"""Thin, content-only semantic evidence bridge for pinned RD-Agent QuantRDLoop.

This module does not implement or reorder research steps. The worker entrypoint
patches only the pinned loop's existing ``record`` method and delegates to the
upstream ``quant.main`` function with the same arguments as ``fin_quant``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Callable


UPSTREAM_RELEASE_SHA = "484776c211e4fbbeef03e0ec00d6bbee7362a4f4"
EVIDENCE_FILENAME = "p12-rdagent-semantic-evidence.json"
_HYPOTHESIS_FIELDS = (
    "hypothesis", "reason", "concise_reason", "concise_observation",
    "concise_justification", "concise_knowledge", "action",
)
_FACTOR_TASK_FIELDS = (
    "name", "version", "description", "base_code", "user_instructions",
    "factor_name", "factor_formulation", "variables", "factor_resources",
    "factor_implementation",
)
_MODEL_TASK_FIELDS = (
    "name", "version", "description", "base_code", "user_instructions",
    "architecture", "formulation", "variables", "hyperparameters",
    "training_hyperparameters", "model_type",
)
_DEFAULT_WORKSPACE_SUFFIXES = frozenset({".py"})


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _stable_value(value: Any) -> Any:
    """Accept only simple deterministic object data; never stringify objects."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("NON_FINITE_SEMANTIC_VALUE")
        return value
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("NON_STRING_SEMANTIC_KEY")
        return {key: _stable_value(value[key]) for key in sorted(value)}
    raise ValueError("UNSUPPORTED_SEMANTIC_VALUE")


def _type_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _field_identity(obj: Any, names: tuple[str, ...]) -> dict[str, Any]:
    attributes = vars(obj)
    selected = {name: _stable_value(attributes[name]) for name in names if name in attributes}
    if not selected:
        raise ValueError("NO_STABLE_FIELDS")
    field_hashes = {name: _sha256(_canonical_bytes(value)) for name, value in selected.items()}
    body = {"type": _type_name(obj), "field_sha256s": field_hashes}
    return {
        "type": body["type"],
        "field_names": sorted(field_hashes),
        "field_sha256s": field_hashes,
        "content_sha256": _sha256(_canonical_bytes(body)),
    }


def _task_identity(task: Any) -> dict[str, Any]:
    class_name = type(task).__name__
    class_module = type(task).__module__
    if class_name == "FactorTask" and class_module == "rdagent.components.coder.factor_coder.factor":
        branch, fields = "factor", _FACTOR_TASK_FIELDS
    elif class_name == "ModelTask" and class_module == "rdagent.components.coder.model_coder.model":
        branch, fields = "model", _MODEL_TASK_FIELDS
    else:
        raise ValueError("UNSUPPORTED_TASK_TYPE")
    identity = _field_identity(task, fields)
    identity["branch"] = branch
    identity["identity_sha256"] = _sha256(_canonical_bytes(identity))
    return identity


def _safe_workspace_files(
    workspace: Any, workspace_root: Path, *,
    suffixes: set[str] | frozenset[str] | None = _DEFAULT_WORKSPACE_SUFFIXES,
    exclude_test_files: bool = True,
) -> list[dict[str, Any]]:
    """Hash workspace files and require their on-disk bytes to match file_dict."""
    file_dict = vars(workspace).get("file_dict")
    workspace_path = vars(workspace).get("workspace_path")
    if type(file_dict) is not dict or not isinstance(workspace_path, (Path, str)):
        raise ValueError("WORKSPACE_IDENTITY_UNAVAILABLE")
    root = Path(workspace_path)
    root_real = root.resolve(strict=True)
    output_real = workspace_root.resolve(strict=True)
    if not root_real.is_relative_to(output_real) or root_real != root:
        raise ValueError("WORKSPACE_PATH_ESCAPE_OR_SYMLINK")
    files: list[dict[str, Any]] = []
    for logical_name in sorted(file_dict):
        if type(logical_name) is not str:
            raise ValueError("WORKSPACE_FILE_PATH_INVALID")
        if suffixes is not None and Path(logical_name).suffix.lower() not in suffixes:
            continue
        if exclude_test_files and "test" in logical_name.lower():
            continue
        relative = PurePosixPath(logical_name)
        if relative.is_absolute() or "\\" in logical_name or any(part in ("", ".", "..") for part in relative.parts):
            raise ValueError("WORKSPACE_FILE_PATH_INVALID")
        expected = file_dict[logical_name]
        if type(expected) is not str:
            raise ValueError("WORKSPACE_CODE_NOT_TEXT")
        expected_bytes = expected.encode("utf-8")
        path = root.joinpath(*relative.parts)
        resolved_parent = path.parent.resolve(strict=True)
        if not resolved_parent.is_relative_to(root_real) or resolved_parent != path.parent:
            raise ValueError("WORKSPACE_FILE_PATH_ESCAPE_OR_SYMLINK")
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ValueError("WORKSPACE_CODE_NOT_REGULAR")
        actual = path.read_bytes()
        if actual != expected_bytes:
            raise ValueError("WORKSPACE_CODE_BYTES_MISMATCH")
        files.append({
            "relative_path": relative.as_posix(),
            "workspace_relative_path": path.relative_to(output_real).as_posix(),
            "size_bytes": len(actual),
            "sha256": _sha256(actual),
        })
    if not files:
        raise ValueError("NO_GENERATED_PYTHON_FILES")
    return files


def _workspace_identity(
    workspace: Any, workspace_root: Path, *,
    suffixes: set[str] | frozenset[str] | None = _DEFAULT_WORKSPACE_SUFFIXES,
    exclude_test_files: bool = True,
) -> dict[str, Any]:
    task = vars(workspace).get("target_task")
    task_identity = _task_identity(task) if task is not None else None
    files = _safe_workspace_files(
        workspace, workspace_root, suffixes=suffixes, exclude_test_files=exclude_test_files
    )
    stable_files = [
        {key: item[key] for key in ("relative_path", "size_bytes", "sha256")}
        for item in files
    ]
    stable = {"task_identity_sha256": task_identity and task_identity["identity_sha256"], "files": stable_files}
    return {
        "type": _type_name(workspace),
        "identity_sha256": _sha256(_canonical_bytes(stable)),
        "task_identity_sha256": task_identity and task_identity["identity_sha256"],
        "files": files,
    }


def _experiment_identity(experiment: Any, workspace_root: Path) -> dict[str, Any]:
    attributes = vars(experiment)
    hypothesis = attributes.get("hypothesis")
    if hypothesis is None:
        raise ValueError("EXPERIMENT_HYPOTHESIS_MISSING")
    hypothesis_identity = _field_identity(hypothesis, _HYPOTHESIS_FIELDS)
    tasks_value = attributes.get("sub_tasks")
    if not isinstance(tasks_value, (list, tuple)) or not tasks_value:
        raise ValueError("EXPERIMENT_TASKS_MISSING")
    task_identities = [_task_identity(task) for task in tasks_value]
    template_workspace = attributes.get("experiment_workspace")
    if template_workspace is None:
        template_identity = {"status": "UNAVAILABLE", "identity_sha256": None, "files": []}
    else:
        template_content = _workspace_identity(
            template_workspace, workspace_root, suffixes=None, exclude_test_files=False
        )
        template_identity = {"status": "OBSERVED", **template_content}
    based_value = attributes.get("based_experiments", ())
    if not isinstance(based_value, (list, tuple)):
        raise ValueError("BASED_EXPERIMENTS_INVALID")
    based_identities = [_workspace_identity(item, workspace_root) for item in based_value]
    workspaces = attributes.get("sub_workspace_list")
    if not isinstance(workspaces, (list, tuple)):
        raise ValueError("EXPERIMENT_WORKSPACES_MISSING")
    code_files: list[dict[str, Any]] = []
    for index, workspace in enumerate(workspaces):
        if workspace is None:
            continue
        workspace_task = vars(workspace).get("target_task")
        task_id = _task_identity(workspace_task)["identity_sha256"] if workspace_task is not None else None
        for item in _safe_workspace_files(workspace, workspace_root):
            code_files.append({
                "task_identity_sha256": task_id,
                "relative_path": item["relative_path"],
                "workspace_relative_path": item["workspace_relative_path"],
                "size_bytes": item["size_bytes"],
                "sha256": item["sha256"],
            })
    stable_code = [
        {key: item[key] for key in ("task_identity_sha256", "relative_path", "size_bytes", "sha256")}
        for item in sorted(code_files, key=lambda entry: (entry["task_identity_sha256"] or "", entry["relative_path"], entry["sha256"]))
    ]
    code_manifest_sha = _sha256(_canonical_bytes(stable_code)) if stable_code else None
    plan = attributes.get("plan")
    base_features = attributes.get("base_features")
    base_feature_codes = attributes.get("base_feature_codes")
    feature_inputs = {
        "plan": _stable_value(plan) if plan is not None else None,
        "base_features": _stable_value(base_features) if base_features is not None else None,
        "base_feature_codes": _stable_value(base_feature_codes) if base_feature_codes is not None else None,
    }
    stable = {
        "type": _type_name(experiment),
        "hypothesis_sha256": hypothesis_identity["content_sha256"],
        "task_identity_sha256s": [item["identity_sha256"] for item in task_identities],
        "experiment_template_identity_sha256": template_identity.get("identity_sha256"),
        "based_experiment_identity_sha256s": [item["identity_sha256"] for item in based_identities],
        "generated_code_manifest_sha256": code_manifest_sha,
        "feature_inputs_sha256": _sha256(_canonical_bytes(feature_inputs)),
    }
    return {
        "identity_sha256": _sha256(_canonical_bytes(stable)),
        "type": stable["type"],
        "hypothesis": hypothesis_identity,
        "tasks": task_identities,
        "experiment_template": template_identity,
        "based_experiments": based_identities,
        "generated_code": {"status": "OBSERVED" if code_files else "UNAVAILABLE", "files": code_files,
                            "manifest_sha256": code_manifest_sha},
        "feature_inputs_sha256": stable["feature_inputs_sha256"],
    }


def capture_trace_semantics(trace: Any, *, request_id: str, attempt_id: str, workspace_root: Path) -> dict[str, Any]:
    """Project structured identities from trusted in-memory RD-Agent objects only."""
    history = vars(trace).get("hist")
    parents = vars(trace).get("dag_parent")
    if not isinstance(history, list) or not isinstance(parents, list) or len(history) != len(parents) or not history:
        raise ValueError("TRACE_HISTORY_OR_LINEAGE_UNAVAILABLE")
    experiments: list[dict[str, Any]] = []
    history_identity_by_index: list[str | None] = []
    status = "OBSERVED"
    for index, pair in enumerate(history):
        if not isinstance(pair, tuple) or len(pair) != 2:
            status = "PARTIAL"
            history_identity_by_index.append(None)
            continue
        experiment = pair[0]
        try:
            identity = _experiment_identity(experiment, workspace_root)
        except (OSError, ValueError, TypeError):
            status = "PARTIAL"
            history_identity_by_index.append(None)
            continue
        if (
            identity["experiment_template"].get("status") != "OBSERVED"
            or identity["generated_code"].get("status") != "OBSERVED"
        ):
            status = "PARTIAL"
        parent_indexes = parents[index]
        if not isinstance(parent_indexes, tuple) or any(type(parent) is not int for parent in parent_indexes):
            identity["lineage"] = {"status": "UNAVAILABLE", "parent_experiment_ids": []}
            status = "PARTIAL"
        else:
            resolved_ids = []
            for parent in parent_indexes:
                if parent == -1:
                    parent = index - 1
                if parent < 0 or parent >= index:
                    if parent_indexes:
                        identity["lineage"] = {"status": "UNAVAILABLE", "parent_experiment_ids": []}
                        status = "PARTIAL"
                    continue
                parent_id = history_identity_by_index[parent] if parent < len(history_identity_by_index) else None
                if not parent_id:
                    identity["lineage"] = {"status": "UNAVAILABLE", "parent_experiment_ids": []}
                    status = "PARTIAL"
                    break
                resolved_ids.append(parent_id)
            if "lineage" not in identity:
                lineage = {"parent_experiment_identity_sha256s": resolved_ids,
                           "based_experiment_identity_sha256s": [item["identity_sha256"] for item in identity["based_experiments"]]}
                identity["lineage"] = {
                    "status": "OBSERVED",
                    "parent_experiment_ids": resolved_ids,
                    "identity_sha256": _sha256(_canonical_bytes(lineage)),
                }
        # Loop/history indexes are locators only and are excluded from stable hashes.
        identity["trace_locator"] = {"history_index": index}
        experiments.append(identity)
        history_identity_by_index.append(identity["identity_sha256"])
    if not experiments:
        status = "PARTIAL"
    # Select only the actual final Trace history entry.  If that entry could not
    # be safely projected, never fall back to an older experiment from this run.
    final_identity = history_identity_by_index[-1] if history_identity_by_index else None
    selected = next(
        (item for item in reversed(experiments) if item["identity_sha256"] == final_identity),
        None,
    )
    return {
        "format_version": "P12_RDAGENT_SEMANTIC_EVIDENCE_V1",
        "request_id": request_id,
        "attempt_id": attempt_id,
        "upstream_release_sha": UPSTREAM_RELEASE_SHA,
        "trace_history_length": len(history),
        "status": status,
        "experiments": experiments,
        "selected_experiment_identity_sha256": selected.get("identity_sha256") if selected else None,
        "qlib_recorder_binding": {
            "status": "SEMANTIC_BINDING_PARTIAL",
            "reason": "PINNED_QLIB_WORKSPACE_DOES_NOT_EXPOSE_RECORDER_ID_TO_RDAGENT_TRACE",
        },
    }


def _write_semantic_evidence(trace: Any) -> None:
    output = Path(os.environ["P12_FINQUANT_OUTPUT_DIR"])
    attempt_path = output / "p12-attempt.json"
    fd = os.open(attempt_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
            raise ValueError("P12_ATTEMPT_IDENTITY_FILE_INVALID")
        attempt_value = json.loads(os.read(fd, 65537).decode("utf-8"))
    finally:
        os.close(fd)
    request_id = attempt_value.get("request_id")
    attempt_id = attempt_value.get("attempt_id")
    namespace = os.environ.get("P12_RUN_NAMESPACE")
    if not isinstance(request_id, str) or not isinstance(attempt_id, str) or not namespace:
        raise ValueError("P12_ATTEMPT_IDENTITY_MISSING")
    workspace_root = Path(os.environ.get("WORKSPACE_PATH", ""))
    if not workspace_root.is_absolute():
        raise ValueError("RDAGENT_WORKSPACE_ROOT_NOT_ABSOLUTE")
    payload = capture_trace_semantics(
        trace, request_id=request_id, attempt_id=attempt_id, workspace_root=workspace_root
    )
    data = _canonical_bytes(payload) + b"\n"
    destination = output / EVIDENCE_FILENAME
    temp = output / (EVIDENCE_FILENAME + ".tmp")
    if temp.exists() or temp.is_symlink():
        raise ValueError("SEMANTIC_EVIDENCE_TEMP_ALREADY_EXISTS")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, destination)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def build_semantic_loop_class(base_loop_class: type, emitter: Callable[[Any], None] = _write_semantic_evidence) -> type:
    """Override the existing final record step without adding/reordering steps."""
    class SemanticQuantRDLoop(base_loop_class):
        def record(self, prev_out: dict[str, Any]) -> Any:
            result = super().record(prev_out)
            try:
                emitter(self.trace)
            except Exception as exc:  # evidence is optional; preserve upstream run semantics
                print(f"P12 semantic evidence capture unavailable ({type(exc).__name__})", file=sys.stderr)
            return result

    SemanticQuantRDLoop.__name__ = "P12SemanticQuantRDLoop"
    SemanticQuantRDLoop.__qualname__ = "P12SemanticQuantRDLoop"
    return SemanticQuantRDLoop


def run_native_quant(loop_n: int = 1, *, quant_module: Any | None = None) -> Any:
    """Delegate to pinned upstream quant.main exactly as the fin_quant CLI does."""
    if loop_n != 1:
        raise ValueError("P12_OWNER_LOOP_LIMIT_MUST_EQUAL_ONE")
    from dotenv import load_dotenv

    load_dotenv(".env")
    if quant_module is None:
        import rdagent.app.qlib_rd_loop.quant as quant_module
    original = quant_module.QuantRDLoop
    quant_module.QuantRDLoop = build_semantic_loop_class(original)
    return invoke_upstream_main(quant_module, loop_n=loop_n)


def invoke_upstream_main(quant_module: Any, *, loop_n: int = 1) -> Any:
    if loop_n != 1:
        raise ValueError("P12_OWNER_LOOP_LIMIT_MUST_EQUAL_ONE")
    # fin_quant_cli passes these exact values for the bounded production command.
    return quant_module.main(path=None, step_n=None, loop_n=loop_n, all_duration=None, checkout=True)


def main(argv: list[str] | None = None) -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop-n", type=int, required=True)
    args = parser.parse_args(argv)
    return run_native_quant(args.loop_n)


if __name__ == "__main__":
    main()
