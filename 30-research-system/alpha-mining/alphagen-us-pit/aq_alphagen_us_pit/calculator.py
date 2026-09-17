"""AlphaGen calculator bound to the frozen P2 label-temporal authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import torch

from alphagen.data.calculator import TensorAlphaCalculator
from alphagen.data.expression import Expression, Feature, Ref
from alphagen.utils.pytorch_utils import normalize_by_day
from alphagen_qlib.stock_data import FeatureType

from .data_view import USPitDataView


PROTOCOL_PATH = (
    Path(__file__).resolve().parents[4]
    / "40-certification-system"
    / "protocol"
    / "p2-certification-protocol-v1.json"
)
EXPECTED_PROTOCOL_VERSION = "P2_CERTIFICATION_PROTOCOL_V1"
EXPECTED_TARGET_EXPRESSION = "Ref($close, -2)/Ref($close, -1) - 1"
EXPECTED_LOOKAHEAD_SESSIONS = 2


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class TargetAuthority:
    expression: Expression
    source_expression: str
    lookahead_sessions: int
    protocol_version: str
    protocol_path: Path
    protocol_sha256: str


class USPitAlphaCalculator(TensorAlphaCalculator):
    """Bind AQ's five-channel view to upstream AlphaGen tensor statistics."""

    def __init__(self, data: USPitDataView, target: Expression):
        self.data = data
        super().__init__(_normalize_preserving_missing(target.evaluate(data)))

    def evaluate_alpha(self, expr: Expression) -> torch.Tensor:
        return _normalize_preserving_missing(expr.evaluate(self.data))

    @property
    def n_days(self) -> int:
        return self.data.n_days


def _normalize_preserving_missing(raw: torch.Tensor) -> torch.Tensor:
    """Delegate normalization upstream, then restore authoritative missingness."""
    missing = torch.isnan(raw)
    normalized = normalize_by_day(raw)
    normalized[missing] = torch.nan
    return normalized


def load_authoritative_target(protocol_path: Path = PROTOCOL_PATH) -> TargetAuthority:
    """Bind the one frozen P2 label expression; fail closed on protocol drift."""
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    temporal = protocol["label_temporal_policy"]
    if protocol["protocol_version"] != EXPECTED_PROTOCOL_VERSION:
        raise ValueError("Unexpected certification protocol version")
    if temporal["expression"] != EXPECTED_TARGET_EXPRESSION:
        raise ValueError("Unsupported certification target expression")
    if temporal["effective_lookahead_sessions"] != EXPECTED_LOOKAHEAD_SESSIONS:
        raise ValueError("Unsupported certification target horizon")
    close = Feature(FeatureType.CLOSE)
    return TargetAuthority(
        expression=Ref(close, -2) / Ref(close, -1) - 1,
        source_expression=temporal["expression"],
        lookahead_sessions=temporal["effective_lookahead_sessions"],
        protocol_version=protocol["protocol_version"],
        protocol_path=protocol_path,
        protocol_sha256=_sha256(protocol_path),
    )
