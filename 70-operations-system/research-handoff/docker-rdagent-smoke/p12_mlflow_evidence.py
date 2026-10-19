"""Read native MLflow/Qlib evidence without loading serialized artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import PurePosixPath
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


def _artifact_files(client: Any, run_id: str, path: str = "", depth: int = 0) -> dict[str, int]:
    if depth > 8:
        return set()
    found: dict[str, int] = {}
    for item in client.list_artifacts(run_id, path or None):
        artifact_path = item.path.strip("/")
        if item.is_dir:
            found.update(_artifact_files(client, run_id, artifact_path, depth + 1))
        else:
            size = getattr(item, "file_size", None)
            if isinstance(size, int) and size > 0:
                found[artifact_path] = size
    return found


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
    """Require a FINISHED Recorder and native Qlib research outputs.

    Only MLflow metadata and artifact listings are read; artifact contents are
    never downloaded or deserialized.
    """
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
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "NO_FINISHED_RECORDER"}

    candidates = []
    for run in finished:
        if not _artifact_uri_is_in_volume(run.info.artifact_uri, run.info.run_id):
            continue
        try:
            names = _artifact_files(client, run.info.run_id)
        except Exception:
            continue
        metrics = getattr(run.data, "metrics", {}) or {}
        missing = [name for name, path in _REQUIRED_FILES.items() if path not in names]
        if not _metrics_are_complete(metrics):
            missing.append("native_signal_and_portfolio_metrics")
        candidates.append((run, names, metrics, missing))
    complete = [candidate for candidate in candidates if not candidate[3]]
    if len(complete) == 1:
        run, names, metrics, _ = complete[0]
        return {
            "classification": "RESEARCH_EVIDENCE_COMPLETE",
            "recorder_id": run.info.run_id,
            "recorder_status": run.info.status,
            "artifact_uri": run.info.artifact_uri,
            "artifact_volume": artifact_volume,
            "attempt_id": attempt_id,
            "artifacts": sorted(names),
            "metric_names": sorted(metrics),
            "missing": [],
        }
    if len(complete) > 1:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "MULTIPLE_COMPLETE_RECORDERS"}
    if not candidates:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "NO_ATTEMPT_BOUND_RECORDER"}
    run, names, metrics, missing = candidates[0]
    return {
        "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
        "reason": "FINISHED_RECORDER_MISSING_REQUIRED_OUTPUTS",
        "recorder_id": run.info.run_id,
        "recorder_status": run.info.status,
        "artifact_uri": run.info.artifact_uri,
        "artifact_volume": artifact_volume,
        "attempt_id": attempt_id,
        "artifacts": sorted(names),
        "metric_names": sorted(metrics),
        "missing": missing,
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
    result = inspect_research_evidence(
        client, request_id=args.request_id, attempt_id=args.attempt_id,
        artifact_volume=args.artifact_volume,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["classification"] == "RESEARCH_EVIDENCE_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
