"""Project explicit RD-Agent and Qlib evidence into Candidate V3."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import rfc8785
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


RDAGENT_SOURCE_SHA = "32b3d395e73d9db5eee3fe9063d69aec0fdc83bd"
_NON_ID_FIELDS = {
    "candidate_contract_version",
    "research_producer_identity",
    "qlib_recorder_identity",
    "artifact_identity_bundle",
    "dataset_identity_bundle",
    "runtime_identity_bundle",
    "p2_target_and_eligibility_boundary",
}
_RECORDER_ARTIFACTS = ("task", "params.pkl", "dataset", "pred.pkl")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_id(candidate: dict[str, Any]) -> str:
    projection = {key: value for key, value in candidate.items() if key != "candidate_id"}
    if set(projection) != _NON_ID_FIELDS:
        raise ValueError("Candidate V3 identity projection must contain exactly seven non-ID fields")
    return "sha256:" + hashlib.sha256(rfc8785.dumps(projection)).hexdigest()


def _validator(schema_root: Path) -> Draft202012Validator:
    base = "https://qhongboq.github.io/AUTONOMOUS_QUANT/"
    schemas = {
        name: json.loads((schema_root / name).read_text(encoding="utf-8"))
        for name in (
            "candidate-contract-v1.schema.json",
            "candidate-contract-v2.schema.json",
            "candidate-contract-v3.schema.json",
        )
    }
    registry = Registry().with_resources(
        (base + name, Resource.from_contents(value)) for name, value in schemas.items()
    )
    return Draft202012Validator(schemas["candidate-contract-v3.schema.json"], registry=registry)


def validate_candidate(candidate: dict[str, Any], schema_root: Path) -> None:
    errors = sorted(_validator(schema_root).iter_errors(candidate), key=lambda error: list(error.path))
    if errors:
        raise ValueError(f"Candidate V3 schema rejection: {errors[0].message}")
    if candidate.get("candidate_id") != candidate_id(candidate):
        raise ValueError("Candidate V3 identity mismatch")


def project_rdagent_candidate(
    source: dict[str, Any], recorder_artifacts: Path, schema_root: Path
) -> dict[str, Any]:
    """Return a validated Candidate V3 without owning training or Recorder lifecycle."""
    candidate = copy.deepcopy(source)
    supplied_id = candidate.pop("candidate_id", None)
    if set(candidate) != _NON_ID_FIELDS:
        raise ValueError("Candidate V3 source must contain exactly seven non-ID fields")
    producer_kinds = {
        candidate["research_producer_identity"].get("producer_kind"),
        candidate["artifact_identity_bundle"].get("producer_kind"),
        candidate["runtime_identity_bundle"].get("producer_kind"),
    }
    if producer_kinds != {"RD_AGENT"}:
        raise ValueError("Candidate V3 source is not the RD_AGENT producer branch")
    runtime = candidate["runtime_identity_bundle"]["rdagent_runtime_identity"]
    if runtime.get("rdagent_source_git_sha") != RDAGENT_SOURCE_SHA:
        raise ValueError("RD-Agent source identity mismatch")
    if candidate["qlib_recorder_identity"].get("status") != "FINISHED":
        raise ValueError("Qlib Recorder is not FINISHED")
    paths = {name: recorder_artifacts / name for name in _RECORDER_ARTIFACTS}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ValueError(f"missing Qlib Recorder artifact: {missing[0]}")
    artifacts = candidate["artifact_identity_bundle"]["rdagent_artifact_identity"]
    artifacts["serialized_model_artifact"]["sha256"] = _sha256(paths["params.pkl"])
    artifacts["prediction_artifact"]["sha256"] = _sha256(paths["pred.pkl"])
    candidate["candidate_id"] = candidate_id(candidate)
    if supplied_id is not None and supplied_id != candidate["candidate_id"]:
        raise ValueError("supplied Candidate V3 identity mismatch")
    validate_candidate(candidate, schema_root)
    return candidate
