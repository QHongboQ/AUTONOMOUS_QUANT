"""Read native MLflow/Qlib evidence without loading serialized artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


_REQUIRED_FILES = {
    "task": "task",
    "dataset": "dataset",
    "model_parameters": "params.pkl",
    "predictions": "pred.pkl",
    "signal_ic": "sig_analysis/ic.pkl",
    "signal_rank_ic": "sig_analysis/ric.pkl",
    "portfolio_report": "portfolio_analysis/report_normal_1day.pkl",
    "portfolio_analysis": "portfolio_analysis/port_analysis_1day.pkl",
}


class ArtifactListingDepthExceeded(ValueError):
    """Raised when MLflow artifact traversal cannot produce a complete listing."""


def _artifact_files(client: Any, run_id: str, path: str = "", depth: int = 0) -> dict[str, int | None]:
    if depth > 8:
        raise ArtifactListingDepthExceeded("MLflow artifact listing exceeded maximum depth 8")
    found: dict[str, int | None] = {}
    for item in client.list_artifacts(run_id, path or None):
        artifact_path = item.path.strip("/")
        if item.is_dir:
            found.update(_artifact_files(client, run_id, artifact_path, depth + 1))
        else:
            size = getattr(item, "file_size", None)
            found[artifact_path] = size if isinstance(size, int) and size >= 0 else None
    return found


def _hash_regular_file(path: Path, root: Path) -> tuple[str, int]:
    """Hash an artifact without following a symlink or trusting MLflow's size."""
    resolved_root = root.resolve(strict=True)
    parent = path.parent.resolve(strict=True)
    if not parent.is_relative_to(resolved_root) or parent != path.parent:
        raise ValueError("artifact path escaped or traversed a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    digest = hashlib.sha256()
    total = 0
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("artifact is not a regular file")
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            digest.update(block)
            total += len(block)
    finally:
        os.close(descriptor)
    return digest.hexdigest(), total


def _artifact_content_identity(
    *, run_id: str, artifact_uri: str, artifact_path: str,
    listed_files: dict[str, int | None],
) -> dict[str, Any]:
    """Hash exact artifact bytes; directories get a canonical child manifest."""
    expected_root = Path("/qlib-artifacts") / run_id / "artifacts"
    root = Path(PurePosixPath(artifact_uri.removeprefix("file://")))
    if not root.is_absolute() or root != expected_root:
        raise ValueError("unexpected MLflow artifact root")
    return _artifact_content_identity_at_root(
        root=root, artifact_path=artifact_path, listed_files=listed_files
    )


def _artifact_content_identity_at_root(
    *, root: Path, artifact_path: str, listed_files: dict[str, int | None],
) -> dict[str, Any]:
    """Testable path-safe content hasher; production callers fix the volume root above."""
    cursor = Path(root.anchor)
    for component in root.parts[1:]:
        cursor = cursor / component
        component_info = cursor.lstat()
        if stat.S_ISLNK(component_info.st_mode):
            raise ValueError("MLflow artifact root traverses a symlink")
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError("MLflow artifact root is not a plain directory")
    for name in listed_files:
        candidate = PurePosixPath(name)
        if (
            candidate.is_absolute()
            or not candidate.parts
            or any(part in {"", ".", ".."} for part in candidate.parts)
            or "\\" in name
        ):
            raise ValueError("MLflow artifact listing contains an unsafe path")
    artifact_parts = PurePosixPath(artifact_path)
    if (
        artifact_parts.is_absolute()
        or not artifact_parts.parts
        or any(part in {"", ".", ".."} for part in artifact_parts.parts)
        or "\\" in artifact_path
    ):
        raise ValueError("required MLflow artifact path is unsafe")
    exact = artifact_path in listed_files
    children = sorted(name for name in listed_files if name.startswith(artifact_path.rstrip("/") + "/"))
    if exact and children:
        raise ValueError("artifact path is both a file and a directory")
    if exact:
        target = root.joinpath(*PurePosixPath(artifact_path).parts)
        digest, size = _hash_regular_file(target, root)
        return {"relative_path": artifact_path, "entry_type": "file", "size_bytes": size, "sha256": digest}
    if not children:
        raise FileNotFoundError(artifact_path)
    files = []
    for child in children:
        relative_child = PurePosixPath(child).relative_to(PurePosixPath(artifact_path)).as_posix()
        if not relative_child or relative_child.startswith("../"):
            raise ValueError("artifact child path escaped its directory")
        target = root.joinpath(*PurePosixPath(child).parts)
        digest, size = _hash_regular_file(target, root)
        files.append({"relative_path": relative_child, "size_bytes": size, "sha256": digest})
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "relative_path": artifact_path,
        "entry_type": "directory",
        "file_count": len(files),
        "files": files,
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "digest_semantics": "SHA256_OF_CANONICAL_CHILD_MANIFEST",
    }


def _attempt_tags(request_id: str, attempt_id: str, artifact_volume: str) -> dict[str, str]:
    return {
        "aq.p12.request_id": request_id,
        "aq.p12.attempt_id": attempt_id,
        "aq.p12.artifact_volume": artifact_volume,
    }


def _expected_attempt_bindings(request_id: str, attempt_id: str) -> tuple[str, str]:
    run_namespace = "aq-p12-owner-" + hashlib.sha256(
        f"{request_id}:{attempt_id}".encode()
    ).hexdigest()[:12]
    volume_suffix = hashlib.sha256(f"{request_id}:{attempt_id}".encode()).hexdigest()[:16]
    return (
        f"sqlite:////workspace/runs/{run_namespace}/mlflow.db",
        "aq-p12-owner-artifacts-" + volume_suffix,
    )


def _artifact_uri_is_in_volume(artifact_uri: str, run_id: str) -> bool:
    parsed = urlparse(artifact_uri)
    if parsed.scheme != "file" or parsed.netloc:
        return False
    path = PurePosixPath(parsed.path)
    return path == PurePosixPath(f"/qlib-artifacts/{run_id}/artifacts")


def _metrics_are_complete(metrics: dict[str, Any]) -> bool:
    if not metrics:
        return False
    if not all(
        isinstance(value, (int, float)) and math.isfinite(value)
        for value in metrics.values()
    ):
        return False
    names = set(metrics)
    signal_metrics = {"IC", "ICIR", "Rank IC", "Rank ICIR"}.issubset(names)
    portfolio_metrics = {
        f"1day.{kind}.{metric}"
        for kind in ("excess_return_without_cost", "excess_return_with_cost")
        for metric in ("annualized_return", "information_ratio", "max_drawdown")
    }.issubset(names)
    return signal_metrics and portfolio_metrics


def inspect_research_evidence(
    client: Any, experiment_name: str = "workflow", *, request_id: str,
    attempt_id: str, artifact_volume: str,
) -> dict[str, Any]:
    """Require one FINISHED Recorder and hash its native artifact bytes."""
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "MLFLOW_EXPERIMENT_MISSING"}
    expected_tags = _attempt_tags(request_id, attempt_id, artifact_volume)
    if (
        experiment.artifact_location != "file:///qlib-artifacts"
        or any(experiment.tags.get(key) != value for key, value in expected_tags.items())
    ):
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "ATTEMPT_OR_ARTIFACT_VOLUME_MISMATCH"}
    runs = client.search_runs([experiment.experiment_id], max_results=1000)
    finished = [run for run in runs if run.info.status == "FINISHED"]
    if not finished:
        return {
            "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
            "reason": "NO_FINISHED_RECORDER",
            "experiment_id": experiment.experiment_id,
            "observed_run_statuses": sorted({run.info.status for run in runs}),
            "artifact_volume": artifact_volume,
            "attempt_id": attempt_id,
        }

    candidates = []
    depth_limited_runs: list[str] = []
    for run in finished:
        if (
            str(run.info.experiment_id) != str(experiment.experiment_id)
            or not _artifact_uri_is_in_volume(run.info.artifact_uri, run.info.run_id)
        ):
            continue
        try:
            names = _artifact_files(client, run.info.run_id)
        except ArtifactListingDepthExceeded:
            depth_limited_runs.append(str(run.info.run_id))
            continue
        except Exception:
            continue
        metrics = getattr(run.data, "metrics", {}) or {}
        missing = [name for name, path in _REQUIRED_FILES.items() if path not in names]
        if not _metrics_are_complete(metrics):
            missing.append("native_signal_and_portfolio_metrics")
        candidates.append((run, names, metrics, missing))
    if depth_limited_runs:
        return {
            "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
            "reason": "ARTIFACT_LISTING_INCOMPLETE_DEPTH_LIMIT",
            "experiment_id": experiment.experiment_id,
            "recorder_ids": sorted(depth_limited_runs),
            "artifact_volume": artifact_volume,
            "attempt_id": attempt_id,
        }
    complete = [candidate for candidate in candidates if not candidate[3]]
    if len(complete) == 1:
        run, names, metrics, _ = complete[0]
        try:
            artifact_manifest = {
                logical_name: _artifact_content_identity(
                    run_id=run.info.run_id, artifact_uri=run.info.artifact_uri,
                    artifact_path=path, listed_files=names,
                )
                for logical_name, path in _REQUIRED_FILES.items()
            }
        except (OSError, ValueError, FileNotFoundError):
            return {
                "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
                "reason": "REQUIRED_ARTIFACT_CONTENT_UNREADABLE_OR_UNSAFE",
                "experiment_id": experiment.experiment_id,
                "recorder_id": run.info.run_id,
                "recorder_status": run.info.status,
                "artifact_volume": artifact_volume,
                "attempt_id": attempt_id,
            }
        return {
            "classification": "RESEARCH_EVIDENCE_COMPLETE",
            "experiment_id": experiment.experiment_id,
            "recorder_id": run.info.run_id,
            "recorder_status": run.info.status,
            "artifact_uri": run.info.artifact_uri,
            "artifact_volume": artifact_volume,
            "attempt_id": attempt_id,
            "artifacts": sorted(names),
            "artifact_manifest": artifact_manifest,
            "metric_names": sorted(metrics),
            "missing": [],
        }
    if len(complete) > 1:
        return {
            "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
            "reason": "MULTIPLE_COMPLETE_RECORDERS",
            "experiment_id": experiment.experiment_id,
            "attempt_id": attempt_id,
            "artifact_volume": artifact_volume,
        }
    if not candidates:
        return {
            "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
            "reason": "NO_ATTEMPT_BOUND_RECORDER",
            "experiment_id": experiment.experiment_id,
            "attempt_id": attempt_id,
            "artifact_volume": artifact_volume,
        }
    run, names, metrics, missing = candidates[0]
    return {
        "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
        "reason": "FINISHED_RECORDER_MISSING_REQUIRED_OUTPUTS",
        "experiment_id": experiment.experiment_id,
        "recorder_id": run.info.run_id,
        "recorder_status": run.info.status,
        "artifact_uri": run.info.artifact_uri,
        "artifact_volume": artifact_volume,
        "attempt_id": attempt_id,
        "artifacts": sorted(names),
        "metric_names": sorted(metrics),
        "missing": missing,
    }


def _read_semantic_correlation(path: Path, *, request_id: str, attempt_id: str) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 8 * 1024 * 1024:
            raise ValueError("SEMANTIC_CORRELATION_FILE_INVALID")
        chunks = []
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            chunks.append(block)
    finally:
        os.close(fd)
    raw = b"".join(chunks)
    value = json.loads(raw.decode("utf-8"))
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
    if raw != canonical or value.get("request_id") != request_id or value.get("attempt_id") != attempt_id:
        raise ValueError("SEMANTIC_CORRELATION_CANONICAL_OR_ATTEMPT_MISMATCH")
    binding = value.get("qlib_recorder_binding")
    selected = value.get("selected_experiment_identity_sha256")
    matches = binding.get("matches") if isinstance(binding, dict) else None
    if (
        binding.get("status") != "PARTIAL" or not isinstance(matches, list) or len(matches) != 1
        or not isinstance(selected, str)
    ):
        raise ValueError("SEMANTIC_CORRELATION_NOT_UNIQUE")
    match = matches[0]
    marker = match.get("marker") if isinstance(match, dict) else None
    if (
        match.get("status") != "RECORDER_CREATED_BY_NATIVE_QRUN"
        or match.get("request_id") != request_id or match.get("attempt_id") != attempt_id
        or match.get("rdagent_experiment_identity_sha256") != selected
        or match.get("recorder_status_at_hook") != "RUNNING"
        or not isinstance(marker, dict)
        or marker.get("request_id") != request_id or marker.get("attempt_id") != attempt_id
        or marker.get("rdagent_experiment_identity_sha256") != selected
        or marker.get("correlation_sha256") != match.get("marker_sha256")
        or not re.fullmatch(r"[0-9a-f]{64}", str(match.get("receipt_sha256", "")))
    ):
        raise ValueError("SEMANTIC_CORRELATION_BINDING_MISMATCH")
    marker_body = dict(marker)
    marker_digest = marker_body.pop("correlation_sha256", None)
    if hashlib.sha256(json.dumps(marker_body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest() != marker_digest:
        raise ValueError("SEMANTIC_CORRELATION_MARKER_HASH_MISMATCH")
    return {"payload": value, "binding": binding, "match": match, "marker": marker}


def inspect_correlated_research_evidence(
    client: Any, *, request_id: str, attempt_id: str, artifact_volume: str,
    semantic_evidence_path: Path,
) -> dict[str, Any]:
    """Verify the exact Recorder tagged by Qlib's native record hook and hash its artifacts."""
    try:
        correlation = _read_semantic_correlation(
            semantic_evidence_path, request_id=request_id, attempt_id=attempt_id,
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": str(exc) or type(exc).__name__}
    match = correlation["match"]
    marker = correlation["marker"]
    experiment_id = str(match.get("qlib_experiment_id", ""))
    run_id = str(match.get("qlib_recorder_run_id", ""))
    experiment = client.get_experiment(experiment_id)
    if experiment is None or str(experiment.experiment_id) != experiment_id:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "CORRELATED_EXPERIMENT_MISSING"}
    expected_experiment_tags = _attempt_tags(request_id, attempt_id, artifact_volume)
    if (
        experiment.name != match.get("qlib_experiment_name")
        or experiment.artifact_location != "file:///qlib-artifacts"
        or any(experiment.tags.get(key) != value for key, value in expected_experiment_tags.items())
    ):
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "CORRELATED_EXPERIMENT_IDENTITY_MISMATCH"}
    runs = client.search_runs([experiment_id], max_results=1000)
    if len(runs) != 1:
        return {
            "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
            "reason": "CORRELATED_EXPERIMENT_RECORDER_NOT_UNIQUE",
            "experiment_id": experiment_id,
            "recorder_ids": sorted(str(run.info.run_id) for run in runs),
        }
    run = runs[0]
    if (
        str(run.info.run_id) != run_id
        or str(run.info.experiment_id) != experiment_id
        or run.info.status != "FINISHED"
        or not _artifact_uri_is_in_volume(run.info.artifact_uri, run_id)
    ):
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "CORRELATED_RECORDER_NOT_FINISHED_OR_MISMATCHED"}
    expected_run_tags = {
        "aq.p12.request_id": request_id,
        "aq.p12.attempt_id": attempt_id,
        "aq.p12.rdagent_experiment_identity_sha256": marker["rdagent_experiment_identity_sha256"],
        "aq.p12.correlation_sha256": marker["correlation_sha256"],
    }
    if any(run.data.tags.get(key) != value for key, value in expected_run_tags.items()):
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "CORRELATED_RECORDER_TAG_MISMATCH"}
    try:
        names = _artifact_files(client, run_id)
        metrics = getattr(run.data, "metrics", {}) or {}
        missing = [name for name, path in _REQUIRED_FILES.items() if path not in names]
        if not _metrics_are_complete(metrics):
            missing.append("native_signal_and_portfolio_metrics")
        if missing:
            return {
                "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
                "reason": "CORRELATED_RECORDER_MISSING_REQUIRED_OUTPUTS",
                "experiment_id": experiment_id, "recorder_id": run_id, "missing": missing,
            }
        artifact_manifest = {
            logical_name: _artifact_content_identity(
                run_id=run_id, artifact_uri=run.info.artifact_uri,
                artifact_path=artifact_path, listed_files=names,
            )
            for logical_name, artifact_path in _REQUIRED_FILES.items()
        }
    except (OSError, ValueError, FileNotFoundError, ArtifactListingDepthExceeded) as exc:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": f"CORRELATED_ARTIFACT_VERIFICATION_FAILED:{type(exc).__name__}"}
    correlation_body = {
        "request_id": request_id, "attempt_id": attempt_id,
        "rdagent_experiment_identity_sha256": marker["rdagent_experiment_identity_sha256"],
        "marker_sha256": marker["correlation_sha256"],
        "receipt_sha256": match["receipt_sha256"],
        "qlib_experiment_id": experiment_id, "qlib_recorder_run_id": run_id,
        "recorder_status": run.info.status,
        "artifact_manifest": artifact_manifest,
    }
    correlation_digest = hashlib.sha256(
        json.dumps(correlation_body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {
        "classification": "RESEARCH_EVIDENCE_COMPLETE",
        "experiment_id": experiment_id,
        "recorder_id": run_id,
        "recorder_status": run.info.status,
        "artifact_uri": run.info.artifact_uri,
        "artifact_volume": artifact_volume,
        "attempt_id": attempt_id,
        "artifacts": sorted(names),
        "artifact_manifest": artifact_manifest,
        "metric_names": sorted(metrics),
        "missing": [],
        "correlation_binding": {
            "status": "VERIFIED",
            **correlation_body,
            "correlation_evidence_sha256": correlation_digest,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking-uri", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--artifact-volume", required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    expected_tracking_uri, expected_volume = _expected_attempt_bindings(
        args.request_id, args.attempt_id
    )
    if args.tracking_uri != expected_tracking_uri or args.artifact_volume != expected_volume:
        print(json.dumps({"classification": "MLFLOW_ATTEMPT_BINDING_MISMATCH"}, sort_keys=True))
        return 2
    import mlflow
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(args.tracking_uri)
    client = MlflowClient(tracking_uri=args.tracking_uri)
    if args.prepare:
        experiment = client.get_experiment_by_name("workflow")
        if experiment is None:
            experiment_id = client.create_experiment(
                "workflow", artifact_location="file:///qlib-artifacts",
                tags=_attempt_tags(args.request_id, args.attempt_id, args.artifact_volume),
            )
            experiment = client.get_experiment(experiment_id)
        if (
            experiment.artifact_location != "file:///qlib-artifacts"
            or any(experiment.tags.get(key) != value for key, value in _attempt_tags(
                args.request_id, args.attempt_id, args.artifact_volume
            ).items())
        ):
            print(json.dumps({"classification": "MLFLOW_ATTEMPT_OR_ARTIFACT_ROOT_MISMATCH"}, sort_keys=True))
            return 2
        print(json.dumps({
            "classification": "MLFLOW_ARTIFACT_ROOT_READY",
            "experiment_id": experiment.experiment_id,
            "artifact_location": experiment.artifact_location,
            "request_id": args.request_id,
            "attempt_id": args.attempt_id,
            "artifact_volume": args.artifact_volume,
        }, sort_keys=True))
        return 0
    semantic_path = Path("/workspace/p12-rdagent-semantic-evidence.json")
    if semantic_path.exists():
        result = inspect_correlated_research_evidence(
            client, request_id=args.request_id, attempt_id=args.attempt_id,
            artifact_volume=args.artifact_volume, semantic_evidence_path=semantic_path,
        )
    else:
        result = inspect_research_evidence(
            client, request_id=args.request_id, attempt_id=args.attempt_id,
            artifact_volume=args.artifact_volume,
        )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["classification"] == "RESEARCH_EVIDENCE_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
