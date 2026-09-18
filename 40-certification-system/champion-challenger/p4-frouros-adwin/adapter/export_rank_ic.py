"""Export one explicit Qlib SigAnaRecord RankIC artifact to a neutral stream."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Literal

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from pydantic import BaseModel, ConfigDict, Field


CONTRACT_VERSION = "MetricObservationStreamV1"
METRIC_KIND = "RANK_IC"
SOURCE_FORMAT = "QLIB_SIGANA_RIC_PICKLE"


class MetricObservationV1(BaseModel):
    """One ordered RankIC observation."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    observation_time: str = Field(min_length=1)
    value: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)


class MetricObservationStreamV1(BaseModel):
    """Closed replay input for the first RankIC-only adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    contract_version: Literal["MetricObservationStreamV1"]
    metric_kind: Literal["RANK_IC"]
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_format: Literal["QLIB_SIGANA_RIC_PICKLE"]
    observations: tuple[MetricObservationV1, ...] = Field(min_length=1)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def deterministic_json_bytes(payload: dict) -> bytes:
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


def load_rank_ic_artifact(
    artifact_path: Path, metric_kind: str = METRIC_KIND
) -> MetricObservationStreamV1:
    """Load and strictly validate one explicitly supplied Qlib ric.pkl."""

    artifact_path = artifact_path.resolve(strict=True)
    if artifact_path.name != "ric.pkl":
        raise ValueError("source artifact must be explicitly named ric.pkl")
    if metric_kind != METRIC_KIND:
        raise ValueError("V1 supports only metric_kind=RANK_IC")

    artifact_bytes = artifact_path.read_bytes()
    artifact = pd.read_pickle(artifact_path)
    if not isinstance(artifact, pd.Series):
        raise TypeError("Qlib SigAnaRecord ric.pkl must contain a pandas Series")
    if artifact.empty:
        raise ValueError("RankIC Series must not be empty")
    if not isinstance(artifact.index, pd.DatetimeIndex):
        raise TypeError("RankIC Series must use a pandas DatetimeIndex")
    if artifact.index.hasnans:
        raise ValueError("RankIC observation timestamps must not contain NaT")
    if not artifact.index.is_unique:
        raise ValueError("RankIC observation timestamps must be unique")
    if not artifact.index.is_monotonic_increasing:
        raise ValueError("RankIC observation timestamps must be strictly increasing")
    if is_bool_dtype(artifact.dtype) or not is_numeric_dtype(artifact.dtype):
        raise TypeError("RankIC observations must be numeric scalars")

    observations: list[MetricObservationV1] = []
    for timestamp, raw_value in artifact.items():
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError("RankIC observations must be finite")
        if not -1.0 <= value <= 1.0:
            raise ValueError("RankIC observations must be within [-1.0, 1.0]")
        observations.append(
            MetricObservationV1(
                observation_time=pd.Timestamp(timestamp).isoformat(),
                value=value,
            )
        )

    return MetricObservationStreamV1(
        contract_version=CONTRACT_VERSION,
        metric_kind=METRIC_KIND,
        source_artifact_sha256=sha256_bytes(artifact_bytes),
        source_format=SOURCE_FORMAT,
        observations=tuple(observations),
    )


def export_rank_ic(artifact_path: Path, output_path: Path) -> dict[str, object]:
    stream = load_rank_ic_artifact(artifact_path=artifact_path)
    output_bytes = deterministic_json_bytes(stream.model_dump(mode="json"))
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as handle:
        handle.write(output_bytes)
    return {
        "contract_version": CONTRACT_VERSION,
        "metric_kind": METRIC_KIND,
        "observation_count": len(stream.observations),
        "output_sha256": sha256_bytes(output_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export one explicit Qlib SigAnaRecord ric.pkl artifact"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export_rank_ic(args.input, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
