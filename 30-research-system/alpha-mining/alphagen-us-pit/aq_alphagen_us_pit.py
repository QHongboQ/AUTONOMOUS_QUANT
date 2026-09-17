"""Thin US PIT boundary for the bounded AlphaGen runtime POC."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from qlib.config import REG_US
from qlib.data import D
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.callbacks import BaseCallback

from alphagen.data.calculator import TensorAlphaCalculator
from alphagen.data.expression import Expression, Feature, Ref
from alphagen.models.linear_alpha_pool import MseAlphaPool
from alphagen.rl.env.wrapper import AlphaEnv, SIZE_OP
from alphagen.rl.policy import LSTMSharedNet
from alphagen.utils import reseed_everything
from alphagen.utils.pytorch_utils import normalize_by_day
from alphagen_qlib.stock_data import FeatureType


PROVIDER_URI = Path("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data")
BUILD_REPORT = Path("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/reports/build-report.json")
BUILD_REPORT_SHA256 = "eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142"
SEALED_OOS_START = pd.Timestamp("2026-09-14")

EVALUATION_START = pd.Timestamp("2024-01-02")
EVALUATION_END = pd.Timestamp("2024-03-28")
INSTRUMENT_COUNT = 32
MAX_BACKTRACK_DAYS = 40
MAX_FUTURE_DAYS = 2
SEED = 0
PPO_N_STEPS = 2048
PPO_BATCH_SIZE = 128
POOL_CAPACITY = 5

FEATURE_FIELDS = (
    (FeatureType.OPEN, "$open"),
    (FeatureType.CLOSE, "$close"),
    (FeatureType.HIGH, "$high"),
    (FeatureType.LOW, "$low"),
    (FeatureType.VOLUME, "$volume"),
)
VWAP_ACTION_INDEX = SIZE_OP + int(FeatureType.VWAP)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def vwap_action_mask(env: Any) -> np.ndarray:
    """Preserve AlphaGen's mask and additionally forbid unavailable VWAP."""
    base_mask = np.asarray(env.action_masks(), dtype=bool).copy()
    if base_mask.shape != (env.action_space.n,):
        raise ValueError("AlphaGen action mask length does not match its action space")
    if not 0 <= VWAP_ACTION_INDEX < len(base_mask):
        raise ValueError("Derived VWAP action index is outside the AlphaGen action space")
    base_mask[VWAP_ACTION_INDEX] = False
    return base_mask


def mask_vwap(env: Any) -> ActionMasker:
    return ActionMasker(env, vwap_action_mask)


@dataclass(frozen=True)
class USPitDataView:
    """The exact duck-typed tensor surface consumed by AlphaGen expressions."""

    data: torch.Tensor
    dates: pd.DatetimeIndex
    stock_ids: pd.Index
    max_backtrack_days: int
    max_future_days: int
    evaluation_start: pd.Timestamp
    evaluation_end: pd.Timestamp
    selection_rule: str

    @property
    def n_days(self) -> int:
        return self.data.shape[0] - self.max_backtrack_days - self.max_future_days

    @property
    def n_stocks(self) -> int:
        return self.data.shape[-1]


class USPitAlphaCalculator(TensorAlphaCalculator):
    """Bind AQ's five-channel view to upstream AlphaGen tensor statistics."""

    def __init__(self, data: USPitDataView, target: Expression):
        self.data = data
        super().__init__(normalize_by_day(target.evaluate(data)))

    def evaluate_alpha(self, expr: Expression) -> torch.Tensor:
        return normalize_by_day(expr.evaluate(self.data))

    @property
    def n_days(self) -> int:
        return self.data.n_days


def authoritative_target() -> Expression:
    close = Feature(FeatureType.CLOSE)
    return Ref(close, -2) / Ref(close, -1) - 1


def load_bounded_us_pit_view(device: torch.device) -> USPitDataView:
    if _sha256(BUILD_REPORT) != BUILD_REPORT_SHA256:
        raise ValueError("P2 ragged-panel build authority hash mismatch")
    if EVALUATION_END >= SEALED_OOS_START:
        raise ValueError("Bounded POC interval reaches sealed OOS")

    import qlib

    qlib.init(provider_uri=str(PROVIDER_URI), region=REG_US)
    calendar = pd.DatetimeIndex(D.calendar(freq="day"))
    start_index = int(calendar.searchsorted(EVALUATION_START))
    end_index = int(calendar.searchsorted(EVALUATION_END, side="right") - 1)
    if calendar[start_index] != EVALUATION_START or calendar[end_index] != EVALUATION_END:
        raise ValueError("POC boundaries must be exact Qlib sessions")
    load_start_index = start_index - MAX_BACKTRACK_DAYS
    load_end_index = end_index + MAX_FUTURE_DAYS
    if load_start_index < 0 or load_end_index >= len(calendar):
        raise ValueError("Insufficient authoritative history for POC buffers")
    loaded_dates = calendar[load_start_index : load_end_index + 1]

    market = D.instruments("p2_pit")
    active_start = set(
        D.list_instruments(
            market,
            start_time=EVALUATION_START,
            end_time=EVALUATION_START,
            as_list=True,
        )
    )
    active_end = set(
        D.list_instruments(
            market,
            start_time=EVALUATION_END,
            end_time=EVALUATION_END,
            as_list=True,
        )
    )
    instruments = sorted(active_start & active_end)[:INSTRUMENT_COUNT]
    if len(instruments) != INSTRUMENT_COUNT:
        raise ValueError("Deterministic membership intersection is too small")

    fields = [field for _, field in FEATURE_FIELDS]
    frame = D.features(
        instruments,
        fields,
        start_time=loaded_dates[0],
        end_time=loaded_dates[-1],
        freq="day",
    )
    channels = []
    for expected_index, (_, field) in enumerate(FEATURE_FIELDS):
        if int(FEATURE_FIELDS[expected_index][0]) != expected_index:
            raise ValueError("AlphaGen feature indices 0-4 do not match AQ channel order")
        wide = frame[field].unstack(level="instrument")
        wide = wide.reindex(index=loaded_dates, columns=instruments)
        channels.append(wide.to_numpy(dtype=np.float32))
    tensor = torch.as_tensor(np.stack(channels, axis=1), device=device)
    return USPitDataView(
        data=tensor,
        dates=loaded_dates,
        stock_ids=pd.Index(instruments),
        max_backtrack_days=MAX_BACKTRACK_DAYS,
        max_future_days=MAX_FUTURE_DAYS,
        evaluation_start=EVALUATION_START,
        evaluation_end=EVALUATION_END,
        selection_rule=(
            "lexicographically first 32 security identities in the intersection "
            "of p2_pit membership on 2024-01-02 and 2024-03-28"
        ),
    )


class _ActionAuditCallback(BaseCallback):
    def __init__(self) -> None:
        super().__init__(verbose=0)
        self.vwap_action_selection_count = 0
        self.action_count = 0

    def _on_step(self) -> bool:
        actions = np.asarray(self.locals.get("actions", []), dtype=np.int64).reshape(-1)
        self.action_count += int(actions.size)
        self.vwap_action_selection_count += int((actions == VWAP_ACTION_INDEX).sum())
        return True


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_bounded_poc(output_root: Path) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"Refusing to overwrite POC evidence: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    reseed_everything(SEED)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    data = load_bounded_us_pit_view(device)
    target_expr = authoritative_target()
    calculator = USPitAlphaCalculator(data, target_expr)
    pool = MseAlphaPool(
        capacity=POOL_CAPACITY,
        calculator=calculator,
        ic_lower_bound=None,
        l1_alpha=5e-3,
        device=device,
    )
    base_env = AlphaEnv(pool=pool, device=device, print_expr=False)
    masked_env = mask_vwap(base_env)

    base_mask = base_env.action_masks()
    effective_mask = masked_env.action_masks()
    mask_diff = np.flatnonzero(base_mask != effective_mask).tolist()
    if any(index != VWAP_ACTION_INDEX for index in mask_diff):
        raise RuntimeError("AQ mask changed a non-VWAP AlphaGen action")
    if effective_mask[VWAP_ACTION_INDEX]:
        raise RuntimeError("VWAP remains selectable after ActionMasker")

    callback = _ActionAuditCallback()
    model = MaskablePPO(
        "MlpPolicy",
        masked_env,
        policy_kwargs={
            "features_extractor_class": LSTMSharedNet,
            "features_extractor_kwargs": {
                "n_layers": 2,
                "d_model": 128,
                "dropout": 0.1,
                "device": device,
            },
        },
        gamma=1.0,
        ent_coef=0.01,
        n_steps=PPO_N_STEPS,
        batch_size=PPO_BATCH_SIZE,
        device=device,
        seed=SEED,
        verbose=0,
    )
    started = time.perf_counter()
    model.learn(total_timesteps=PPO_N_STEPS, callback=callback)
    runtime_seconds = time.perf_counter() - started

    pool_payload = {
        "exprs": [str(expr) for expr in pool.exprs[: pool.size]],
        "weights": [float(weight) for weight in pool.weights],
    }
    admitted = []
    for index in range(pool.size):
        expr = pool.exprs[index]
        if expr is None:
            continue
        admitted.append(
            {
                "expression": str(expr),
                "training_ic": float(pool.single_ics[index]),
                "rank_ic": float(calculator.calc_single_rIC_ret(expr)),
                "weight": float(pool.weights[index]),
            }
        )
    vwap_expression_count = sum("$vwap" in item["expression"].lower() for item in admitted)

    target_raw = target_expr.evaluate(data)
    close_channel = data.data[:, int(FeatureType.CLOSE), :]
    start = data.max_backtrack_days
    expected_target = close_channel[start + 2 : start + 2 + data.n_days] / close_channel[
        start + 1 : start + 1 + data.n_days
    ] - 1
    target_alignment = bool(torch.allclose(target_raw, expected_target, equal_nan=True))
    fixture_expr = Ref(Feature(FeatureType.CLOSE), 5)
    fixture_actual = fixture_expr.evaluate(data)
    fixture_expected = close_channel[
        start - 5 : start - 5 + data.n_days
    ]
    expression_fixture = bool(
        torch.allclose(fixture_actual, fixture_expected, equal_nan=True)
    )

    mask_contract = {
        "sb3_contrib_version": "2.0.0",
        "wrapper": "sb3_contrib.common.wrappers.ActionMasker",
        "vwap_action_derivation": "SIZE_OP + int(FeatureType.VWAP)",
        "size_op": int(SIZE_OP),
        "feature_type_vwap": int(FeatureType.VWAP),
        "vwap_action_index": VWAP_ACTION_INDEX,
        "action_space_size": int(base_env.action_space.n),
    }
    mask_report = {
        "mask_length": len(effective_mask),
        "mask_diff_indices_at_reset": mask_diff,
        "mask_diff_count_max": 1,
        "vwap_action_always_false": True,
        "other_action_semantics_unchanged": True,
        "vwap_action_selection_count": callback.vwap_action_selection_count,
        "observed_action_count": callback.action_count,
    }
    data_report = {
        "provider_uri": str(PROVIDER_URI),
        "build_report_sha256": BUILD_REPORT_SHA256,
        "selection_rule": data.selection_rule,
        "instrument_count": data.n_stocks,
        "evaluation_start": str(data.evaluation_start.date()),
        "evaluation_end": str(data.evaluation_end.date()),
        "evaluation_sessions": data.n_days,
        "evaluation_rows": data.n_days * data.n_stocks,
        "loaded_start": str(data.dates[0].date()),
        "loaded_end": str(data.dates[-1].date()),
        "loaded_rows_with_buffers": len(data.dates) * data.n_stocks,
        "feature_channels": [feature.name for feature, _ in FEATURE_FIELDS],
        "missing_values_by_channel": {
            feature.name: int(torch.isnan(data.data[:, int(feature), :]).sum().item())
            for feature, _ in FEATURE_FIELDS
        },
        "missingness_policy": "preserve authoritative NaN; no fill or synthetic values",
        "sealed_oos_rows_accessed": 0,
    }
    fixture_report = {
        "expression": str(fixture_expr),
        "expression_fixture_test": "PASS" if expression_fixture else "FAIL",
        "target_expression": str(target_expr),
        "target_horizon_sessions": 2,
        "target_alignment_test": "PASS" if target_alignment else "FAIL",
        "vwap_evaluated": False,
    }
    runtime_report = {
        "device": str(device),
        "seed": SEED,
        "n_steps": PPO_N_STEPS,
        "total_timesteps": PPO_N_STEPS,
        "batch_size": PPO_BATCH_SIZE,
        "runtime_seconds": runtime_seconds,
        "rl_env_initialized": True,
        "ppo_learning_executed": True,
        "expressions_generated": int(base_env.unwrapped.eval_cnt),
        "expressions_evaluated": int(pool.eval_cnt),
        "pool_admission_count": int(pool.size),
        "vwap_action_selection_count": callback.vwap_action_selection_count,
        "vwap_expression_count": int(vwap_expression_count),
    }
    summary = {
        "task": "AUTONOMOUS-QUANT-P3-ALPHAGEN-US-PIT-VWAP-ACTION-MASK-POC-001",
        "classification": (
            "PASS" if pool.size > 0 else "RUNTIME_PIPELINE_PASS_NO_POOL_ADMISSION_WITHIN_BUDGET"
        ),
        "alphagen_sha": "259687e8f316994426416c530a94842a2fe6405e",
        "alphagen_upstream_source_modified": False,
        "vwap_feature_space_blocker": "RESOLVED_BY_UPSTREAM_SB3_ACTION_MASKER",
        "data": data_report,
        "mask": mask_report,
        "runtime": runtime_report,
        "target_alignment_test": fixture_report["target_alignment_test"],
        "expression_fixture_test": fixture_report["expression_fixture_test"],
        "admitted_alphas": admitted,
        "aq_new_generic_engine_count": 0,
        "sealed_oos_rows_accessed": 0,
        "current_next": "P3_ALPHAGEN_US_PIT_INTEGRATION_001",
    }
    _write_json(output_root / "mask_contract.json", mask_contract)
    _write_json(output_root / "mask_test_report.json", mask_report)
    _write_json(output_root / "data_view_report.json", data_report)
    _write_json(output_root / "expression_fixture_report.json", fixture_report)
    _write_json(output_root / "ppo_runtime_report.json", runtime_report)
    if pool.size > 0:
        _write_json(output_root / "alpha_pool.json", {"upstream_pool": pool_payload, "details": admitted})
    _write_json(output_root / "poc_summary.json", summary)
    return summary


if __name__ == "__main__":
    result = run_bounded_poc(
        Path("/mnt/d/AQ_DATA/P3/alphagen-us-pit-vwap-action-mask-poc-001")
    )
    print(json.dumps(result, indent=2, sort_keys=True))
