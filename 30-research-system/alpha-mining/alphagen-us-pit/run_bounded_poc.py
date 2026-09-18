"""Evidence-only reproduction of the accepted 2048-step AlphaGen POC."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from stable_baselines3.common.callbacks import BaseCallback

from alphagen.data.expression import Feature, Ref
from alphagen.rl.env.wrapper import SIZE_OP
from alphagen_qlib.stock_data import FeatureType

from aq_alphagen_us_pit import (
    AlphaGenRunConfig,
    FEATURE_FIELDS,
    VWAP_ACTION_INDEX,
    load_authoritative_target,
    load_us_pit_view,
    membership_covering_instruments,
    run_alphagen,
)


EVALUATION_START = pd.Timestamp("2024-01-02")
EVALUATION_END = pd.Timestamp("2024-03-28")
INSTRUMENT_COUNT = 32
MAX_BACKTRACK_DAYS = 40
MAX_FUTURE_DAYS = 2
CONFIG = AlphaGenRunConfig(
    seed=0,
    pool_capacity=5,
    ic_lower_bound=None,
    l1_alpha=5e-3,
    total_timesteps=2048,
    n_steps=2048,
    batch_size=128,
    gamma=1.0,
    entropy_coefficient=0.01,
    lstm_layers=2,
    lstm_model_dim=128,
    lstm_dropout=0.1,
)
DEFAULT_OUTPUT_ROOT = Path("/mnt/d/AQ_DATA/P3/alphagen-us-pit-integration-001")


class _ActionAuditCallback(BaseCallback):
    """POC evidence only; it does not participate in action selection."""

    def __init__(self) -> None:
        super().__init__(verbose=0)
        self.vwap_action_selection_count = 0
        self.action_count = 0

    def _on_step(self) -> bool:
        actions = np.asarray(self.locals.get("actions", []), dtype=np.int64).reshape(-1)
        self.action_count += int(actions.size)
        self.vwap_action_selection_count += int((actions == VWAP_ACTION_INDEX).sum())
        return True


def select_bounded_instruments(candidates: list[str], count: int) -> list[str]:
    """POC-only deterministic sample selection; not research-selection policy."""
    selected = sorted(candidates)[:count]
    if len(selected) != count:
        raise ValueError("Deterministic POC membership inventory is too small")
    return selected


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_bounded_parity(output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, object]:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"Refusing to overwrite integration evidence: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    instruments = select_bounded_instruments(
        membership_covering_instruments(EVALUATION_START, EVALUATION_END),
        INSTRUMENT_COUNT,
    )
    data = load_us_pit_view(
        instruments=instruments,
        start_time=EVALUATION_START,
        end_time=EVALUATION_END,
        max_backtrack_days=MAX_BACKTRACK_DAYS,
        max_future_days=MAX_FUTURE_DAYS,
        device=device,
    )
    authority = load_authoritative_target()
    callback = _ActionAuditCallback()
    result = run_alphagen(
        data,
        authority.expression,
        CONFIG,
        device=device,
        callback=callback,
    )

    close_channel = data.data[:, int(FeatureType.CLOSE), :]
    start = data.max_backtrack_days
    target_actual = authority.expression.evaluate(data)
    target_expected = close_channel[
        start + 2 : start + 2 + data.n_days
    ] / close_channel[start + 1 : start + 1 + data.n_days] - 1
    target_alignment = bool(torch.allclose(target_actual, target_expected, equal_nan=True))
    fixture = Ref(Feature(FeatureType.CLOSE), 5)
    fixture_alignment = bool(
        torch.allclose(
            fixture.evaluate(data),
            close_channel[start - 5 : start - 5 + data.n_days],
            equal_nan=True,
        )
    )

    admitted: list[dict[str, object]] = []
    for index in range(result.pool.size):
        expression = result.pool.exprs[index]
        if expression is None:
            continue
        admitted.append(
            {
                "expression": str(expression),
                "rank_ic": float(result.calculator.calc_single_rIC_ret(expression)),
                "training_ic": float(result.pool.single_ics[index]),
                "weight": float(result.pool.weights[index]),
            }
        )
    report: dict[str, object] = {
        "task": "AUTONOMOUS-QUANT-P3-ALPHAGEN-US-PIT-INTEGRATION-001",
        "classification": "STRUCTURAL_PARITY_PASS" if result.pool.size > 0 else "STRUCTURAL_PARITY_PASS_NO_POOL_ADMISSION",
        "alphagen_sha": "259687e8f316994426416c530a94842a2fe6405e",
        "device": str(device),
        "evaluation_start": str(data.evaluation_start.date()),
        "evaluation_end": str(data.evaluation_end.date()),
        "instrument_count": data.n_stocks,
        "evaluation_sessions": data.n_days,
        "evaluation_rows": data.n_days * data.n_stocks,
        "feature_channels": [feature.name for feature, _ in FEATURE_FIELDS],
        "missing_values_by_channel": {
            feature.name: int(torch.isnan(data.data[:, int(feature), :]).sum().item())
            for feature, _ in FEATURE_FIELDS
        },
        "target_protocol": authority.protocol_version,
        "target_protocol_sha256": authority.protocol_sha256,
        "target_expression": authority.source_expression,
        "target_horizon_sessions": authority.lookahead_sessions,
        "target_alignment": "PASS" if target_alignment else "FAIL",
        "expression_fixture": "PASS" if fixture_alignment else "FAIL",
        "seed": CONFIG.seed,
        "total_timesteps": CONFIG.total_timesteps,
        "pool_capacity": CONFIG.pool_capacity,
        "runtime_seconds": result.runtime_seconds,
        "expressions_generated": result.expressions_generated,
        "expressions_evaluated": result.expressions_evaluated,
        "pool_admission_count": int(result.pool.size),
        "admitted_alphas": admitted,
        "size_op": int(SIZE_OP),
        "vwap_action_index": VWAP_ACTION_INDEX,
        "action_space_size": result.action_space_size,
        "mask_diff_indices_at_reset": list(result.mask_diff_indices_at_reset),
        "observed_action_count": callback.action_count,
        "vwap_action_selection_count": callback.vwap_action_selection_count,
        "vwap_expression_count": sum("$vwap" in str(item["expression"]).lower() for item in admitted),
        "synthetic_values": 0,
        "forward_fill": False,
        "sealed_oos_rows_accessed": 0,
        "research_evidence": False,
    }
    _write_json(output_root / "runtime_parity_report.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(run_bounded_parity(), indent=2, sort_keys=True))
