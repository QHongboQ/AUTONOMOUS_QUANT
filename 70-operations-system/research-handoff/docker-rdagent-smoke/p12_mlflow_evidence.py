"""Read native MLflow/Qlib evidence without loading serialized artifacts."""

from __future__ import annotations

import argparse
import json
from typing import Any


_REQUIRED_ARTIFACTS = {
    "task": {"task", "task.pkl", "task.yaml"},
    "dataset": {"dataset", "dataset.pkl"},
    "model": {"model", "model.pkl"},
    "prediction": {"pred.pkl", "prediction.pkl", "predictions.pkl"},
    "portfolio_evaluation": {"portfolio_analysis"},
    "signal_evaluation": {"sig_analysis", "signal_analysis"},
}


def _artifact_names(client: Any, run_id: str, path: str = "", depth: int = 0) -> set[str]:
    if depth > 8:
        return set()
    found: set[str] = set()
    for item in client.list_artifacts(run_id, path or None):
        name = item.path.rsplit("/", 1)[-1]
        found.add(name)
        if item.is_dir:
            child_path = f"{path}/{name}".strip("/")
            found.update(_artifact_names(client, run_id, child_path, depth + 1))
    return found


def inspect_research_evidence(client: Any, experiment_name: str = "workflow") -> dict[str, Any]:
    """Require a FINISHED Recorder and native Qlib research outputs.

    Only MLflow metadata and artifact listings are read; artifact contents are
    never downloaded or deserialized.
    """
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "MLFLOW_EXPERIMENT_MISSING"}
    runs = client.search_runs([experiment.experiment_id], max_results=1000)
    finished = [run for run in runs if run.info.status == "FINISHED"]
    if not finished:
        return {"classification": "RESEARCH_EVIDENCE_INCOMPLETE", "reason": "NO_FINISHED_RECORDER"}

    candidates = []
    for run in finished:
        try:
            names = _artifact_names(client, run.info.run_id)
        except Exception:
            continue
        metrics = getattr(run.data, "metrics", {}) or {}
        missing = [
            category for category, names_for_category in _REQUIRED_ARTIFACTS.items()
            if not (names & names_for_category)
        ]
        if not metrics:
            missing.append("evaluation_metrics")
        candidates.append((run, names, metrics, missing))
        if not missing:
            return {
                "classification": "RESEARCH_EVIDENCE_COMPLETE",
                "recorder_id": run.info.run_id,
                "recorder_status": run.info.status,
                "artifact_uri": run.info.artifact_uri,
                "artifacts": sorted(names),
                "metric_names": sorted(metrics),
                "missing": [],
            }
    run, names, metrics, missing = candidates[0]
    return {
        "classification": "RESEARCH_EVIDENCE_INCOMPLETE",
        "reason": "FINISHED_RECORDER_MISSING_REQUIRED_OUTPUTS",
        "recorder_id": run.info.run_id,
        "recorder_status": run.info.status,
        "artifact_uri": run.info.artifact_uri,
        "artifacts": sorted(names),
        "metric_names": sorted(metrics),
        "missing": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking-uri", required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    import mlflow
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(args.tracking_uri)
    client = MlflowClient(tracking_uri=args.tracking_uri)
    if args.prepare:
        experiment = client.get_experiment_by_name("workflow")
        if experiment is None:
            experiment_id = client.create_experiment(
                "workflow", artifact_location="file:///qlib-artifacts"
            )
            experiment = client.get_experiment(experiment_id)
        if experiment.artifact_location != "file:///qlib-artifacts":
            print(json.dumps({"classification": "MLFLOW_ARTIFACT_ROOT_MISMATCH"}, sort_keys=True))
            return 2
        print(json.dumps({
            "classification": "MLFLOW_ARTIFACT_ROOT_READY",
            "experiment_id": experiment.experiment_id,
            "artifact_location": experiment.artifact_location,
        }, sort_keys=True))
        return 0
    result = inspect_research_evidence(client)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["classification"] == "RESEARCH_EVIDENCE_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
