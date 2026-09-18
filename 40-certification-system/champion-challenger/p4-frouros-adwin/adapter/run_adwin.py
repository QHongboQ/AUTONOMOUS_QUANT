"""Replay one neutral RankIC stream through public Frouros ADWIN."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import frouros
from frouros.detectors.concept_drift import ADWIN, ADWINConfig


OBSERVATION_CONTRACT_VERSION = "MetricObservationStreamV1"
EVIDENCE_CONTRACT_VERSION = "DetectorEvidenceV1"
METRIC_KIND = "RANK_IC"
SOURCE_FORMAT = "QLIB_SIGANA_RIC_PICKLE"
TRANSLATION_KIND = "CONSTANT_ADDITIVE_OFFSET"
TRANSLATION_CONSTANT = 1.0
ORIGINAL_DOMAIN = [-1.0, 1.0]
TRANSLATED_DOMAIN = [0.0, 2.0]
FROUROS_VERSION = "0.9.0"
RUNTIME_FREEZE_SHA256 = (
    "8c66ad3fde0f116d89aa31c0454a093eba00b16fe6d5946ac973bd5850dfb5d5"
)
ADWIN_MODULE_SHA256 = (
    "f3b2c06acf88b6938eac907909ca16b8daa382133eb1247e297a12f299ebd8fd"
)
ADWIN_CONFIG = {
    "clock": 32,
    "delta": 0.002,
    "m": 5,
    "min_num_instances": 10,
    "min_window_size": 5,
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def deterministic_json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize exact bytes deterministically; no semantic-canonical claim."""

    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _validate_runtime_identity(
    expected_version: str = FROUROS_VERSION,
    expected_runtime_freeze_sha256: str = RUNTIME_FREEZE_SHA256,
    expected_module_sha256: str = ADWIN_MODULE_SHA256,
) -> None:
    if expected_version != FROUROS_VERSION or frouros.__version__ != expected_version:
        raise RuntimeError("Frouros version identity mismatch")
    if expected_runtime_freeze_sha256 != RUNTIME_FREEZE_SHA256:
        raise RuntimeError("Frouros runtime-freeze identity mismatch")
    module_path = Path(inspect.getsourcefile(ADWIN) or "").resolve(strict=True)
    actual_module_sha256 = sha256_bytes(module_path.read_bytes())
    if expected_module_sha256 != ADWIN_MODULE_SHA256:
        raise RuntimeError("declared ADWIN module identity mismatch")
    if actual_module_sha256 != expected_module_sha256:
        raise RuntimeError("installed ADWIN module identity mismatch")


def _parse_observation_stream(payload: Any) -> dict[str, Any]:
    required = {
        "contract_version",
        "metric_kind",
        "observations",
        "source_artifact_sha256",
        "source_format",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("invalid MetricObservationStreamV1 fields")
    if payload["contract_version"] != OBSERVATION_CONTRACT_VERSION:
        raise ValueError("unsupported observation contract version")
    if payload["metric_kind"] != METRIC_KIND:
        raise ValueError("V1 supports only metric_kind=RANK_IC")
    if payload["source_format"] != SOURCE_FORMAT:
        raise ValueError("unsupported source format")
    if not isinstance(payload["source_artifact_sha256"], str) or not _SHA256.fullmatch(
        payload["source_artifact_sha256"]
    ):
        raise ValueError("invalid source artifact SHA256")
    observations = payload["observations"]
    if not isinstance(observations, list) or not observations:
        raise ValueError("observation stream must be a non-empty list")

    prior_time: datetime | None = None
    for observation in observations:
        if not isinstance(observation, dict) or set(observation) != {
            "observation_time",
            "value",
        }:
            raise ValueError("invalid observation fields")
        time_text = observation["observation_time"]
        if not isinstance(time_text, str):
            raise TypeError("observation_time must be a string")
        try:
            parsed_time = datetime.fromisoformat(time_text.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("observation_time must be ISO-8601") from error
        if prior_time is not None and parsed_time <= prior_time:
            raise ValueError("observation timestamps must be unique and increasing")
        prior_time = parsed_time

        value = observation["value"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("RankIC observations must be numeric scalars")
        if not math.isfinite(value):
            raise ValueError("RankIC observations must be finite")
        if not -1.0 <= value <= 1.0:
            raise ValueError("RankIC observations must be within [-1.0, 1.0]")
    return payload


def load_observation_stream(
    input_path: Path, expected_input_sha256: str
) -> tuple[dict[str, Any], str]:
    if not _SHA256.fullmatch(expected_input_sha256):
        raise ValueError("expected input SHA256 must be lowercase hexadecimal")
    input_bytes = input_path.resolve(strict=True).read_bytes()
    actual_sha256 = sha256_bytes(input_bytes)
    if actual_sha256 != expected_input_sha256:
        raise ValueError("observation-stream SHA256 mismatch")
    return _parse_observation_stream(json.loads(input_bytes)), actual_sha256


def translate_rank_ic(
    value: float,
    translation_kind: str = TRANSLATION_KIND,
    translation_constant: float = TRANSLATION_CONSTANT,
) -> float:
    if translation_kind != TRANSLATION_KIND:
        raise ValueError("unsupported translation kind")
    if translation_constant != TRANSLATION_CONSTANT:
        raise ValueError("unsupported translation constant")
    translated = value + translation_constant
    if not TRANSLATED_DOMAIN[0] <= translated <= TRANSLATED_DOMAIN[1]:
        raise ValueError("translated value outside [0.0, 2.0]")
    return translated


def _validate_detector_evidence(evidence: dict[str, Any]) -> None:
    required = {
        "change_detected",
        "change_indices",
        "contract_version",
        "detector_config",
        "detector_kind",
        "detector_project",
        "detector_version",
        "first_observation_time",
        "installed_adwin_module_sha256",
        "last_observation_time",
        "metric_kind",
        "observation_count",
        "original_domain",
        "source_artifact_sha256",
        "source_observation_stream_sha256",
        "state_authority",
        "translated_domain",
        "translation_constant",
        "translation_kind",
        "frouros_runtime_freeze_sha256",
    }
    if set(evidence) != required:
        raise ValueError("invalid DetectorEvidenceV1 fields")
    if evidence["contract_version"] != EVIDENCE_CONTRACT_VERSION:
        raise ValueError("unsupported detector evidence version")
    if evidence["metric_kind"] != METRIC_KIND:
        raise ValueError("unsupported detector evidence metric")
    if evidence["detector_project"] != "FROUROS":
        raise ValueError("detector project identity mismatch")
    if evidence["detector_version"] != FROUROS_VERSION:
        raise ValueError("detector version identity mismatch")
    if evidence["detector_kind"] != "ADWIN":
        raise ValueError("detector kind identity mismatch")
    if evidence["frouros_runtime_freeze_sha256"] != RUNTIME_FREEZE_SHA256:
        raise ValueError("runtime-freeze identity mismatch")
    if evidence["installed_adwin_module_sha256"] != ADWIN_MODULE_SHA256:
        raise ValueError("ADWIN module identity mismatch")
    if evidence["detector_config"] != ADWIN_CONFIG:
        raise ValueError("ADWIN config identity mismatch")
    if evidence["translation_kind"] != TRANSLATION_KIND:
        raise ValueError("translation identity mismatch")
    if evidence["translation_constant"] != TRANSLATION_CONSTANT:
        raise ValueError("translation constant mismatch")
    if evidence["original_domain"] != ORIGINAL_DOMAIN:
        raise ValueError("original domain mismatch")
    if evidence["translated_domain"] != TRANSLATED_DOMAIN:
        raise ValueError("translated domain mismatch")
    if evidence["state_authority"] != "REPLAY_FROM_IMMUTABLE_OBSERVATIONS":
        raise ValueError("state authority mismatch")
    indices = evidence["change_indices"]
    if not isinstance(indices, list) or any(
        isinstance(index, bool) or not isinstance(index, int) or index < 0
        for index in indices
    ):
        raise ValueError("invalid change indices")
    if evidence["change_detected"] is not bool(indices):
        raise ValueError("change_detected must agree with change_indices")


def run_adwin(
    input_path: Path,
    expected_input_sha256: str,
    output_path: Path,
) -> dict[str, Any]:
    _validate_runtime_identity()
    stream, stream_sha256 = load_observation_stream(
        input_path=input_path, expected_input_sha256=expected_input_sha256
    )
    config = ADWINConfig(
        clock=ADWIN_CONFIG["clock"],
        delta=ADWIN_CONFIG["delta"],
        m=ADWIN_CONFIG["m"],
        min_window_size=ADWIN_CONFIG["min_window_size"],
        min_num_instances=ADWIN_CONFIG["min_num_instances"],
    )
    detector = ADWIN(config=config)
    change_indices: list[int] = []
    for index, observation in enumerate(stream["observations"]):
        detector.update(value=translate_rank_ic(float(observation["value"])))
        if detector.drift:
            change_indices.append(index)

    evidence = {
        "change_detected": bool(change_indices),
        "change_indices": change_indices,
        "contract_version": EVIDENCE_CONTRACT_VERSION,
        "detector_config": dict(ADWIN_CONFIG),
        "detector_kind": "ADWIN",
        "detector_project": "FROUROS",
        "detector_version": FROUROS_VERSION,
        "first_observation_time": stream["observations"][0]["observation_time"],
        "frouros_runtime_freeze_sha256": RUNTIME_FREEZE_SHA256,
        "installed_adwin_module_sha256": ADWIN_MODULE_SHA256,
        "last_observation_time": stream["observations"][-1]["observation_time"],
        "metric_kind": METRIC_KIND,
        "observation_count": len(stream["observations"]),
        "original_domain": list(ORIGINAL_DOMAIN),
        "source_artifact_sha256": stream["source_artifact_sha256"],
        "source_observation_stream_sha256": stream_sha256,
        "state_authority": "REPLAY_FROM_IMMUTABLE_OBSERVATIONS",
        "translated_domain": list(TRANSLATED_DOMAIN),
        "translation_constant": TRANSLATION_CONSTANT,
        "translation_kind": TRANSLATION_KIND,
    }
    _validate_detector_evidence(evidence)
    output_bytes = deterministic_json_bytes(evidence)
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as handle:
        handle.write(output_bytes)
    return {
        "change_detected": evidence["change_detected"],
        "change_indices": evidence["change_indices"],
        "contract_version": EVIDENCE_CONTRACT_VERSION,
        "output_sha256": sha256_bytes(output_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay MetricObservationStreamV1 through Frouros ADWIN"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            run_adwin(args.input, args.input_sha256, args.output), sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
