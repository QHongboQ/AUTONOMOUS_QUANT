"""Seal the fail-closed Qlib end-of-calendar blocker without rerunning work."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PROTOCOL_SHA = "a9aed881c229f9eb7f85fa23b866168a55dc9c00be3c3b178d91a4af20451dfb"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_lf_sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8"),
    ).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--activation", required=True, type=Path)
    parser.add_argument("--provider-report", required=True, type=Path)
    parser.add_argument("--qlib-output", required=True, type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    args = parser.parse_args()
    if args.report_output.exists():
        raise FileExistsError(args.report_output)
    args.report_output.mkdir(parents=True)

    if canonical_lf_sha256(args.protocol) != PROTOCOL_SHA:
        raise RuntimeError("Protocol V1 identity mismatch")
    activation_sha = canonical_lf_sha256(args.activation)
    primary_path = args.qlib_output / "primary_pred.pkl"
    control_path = args.qlib_output / "control_pred.pkl"
    primary = pd.read_pickle(primary_path)
    control = pd.read_pickle(control_path)
    portfolio_files = list((args.qlib_output / "portfolio").glob("*.pkl"))
    if portfolio_files:
        raise RuntimeError("an incomplete Qlib strategy run was persisted unexpectedly")

    blocker = {
        "blocking_status": "P2_HISTORICAL_REHEARSAL_BLOCKING",
        "error": "IndexError: index 2516 is out of bounds for axis 0 with size 2516",
        "input": {
            "provider": "D:/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data",
            "provider_history_end": "2024-12-31",
            "rehearsal_start": "2022-01-03",
            "rehearsal_end": "2024-12-31",
            "strategy": "LGB_50_5",
            "cost_scenario": "BASE",
            "benchmark": None,
        },
        "interface": "qlib.backtest.backtest_loop with Qlib Account, Exchange, SimulatorExecutor, and TopkDropoutStrategy",
        "traceback_boundary": "qlib.contrib.strategy.signal_strategy.TopkDropoutStrategy.generate_trade_decision -> qlib.backtest.utils.TradeCalendarManager.get_step_time -> self._calendar[calendar_index + 1]",
        "upstream": "Microsoft Qlib 0.9.8.dev26 @ 2fb9380b342556ddb50a4b24e4fe8655d548b2b8",
        "cause": "The frozen provider calendar ends on the exact frozen rehearsal end session. Qlib requests the next calendar element while generating the final-session decision.",
        "forbidden_workarounds_not_used": [
            "MUTATE_FROZEN_PROVIDER_CALENDAR",
            "CLIP_REHEARSAL_END_TO_2024-12-30",
            "SYNTHETIC_FUTURE_SESSION",
            "PATCH_QLIB_SOURCE",
            "CUSTOM_BACKTESTER",
        ],
        "prior_wrapper_observation": {
            "error": "ValueError: The benchmark ['SH000300'] does not exist. Please provide the right benchmark",
            "explanation": "backtest_daily maps benchmark=None to an empty benchmark config; legacy PortfolioMetrics then applies SH000300",
            "resolved_by_normal_public_configuration": "Account(benchmark_config={'benchmark': None}) composed with Qlib public backtest objects",
        },
    }
    blocker_path = args.qlib_output / "qlib-rehearsal-blocker.json"
    blocker_path.write_text(json.dumps(blocker, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "task": "AUTONOMOUS_QUANT_P2_CERTIFICATION_HISTORICAL_REHEARSAL_001",
        "classification": "BLOCKED_TECHNICAL",
        "protocol_sha256": PROTOCOL_SHA,
        "activation_sha256": activation_sha,
        "provider_report_sha256": sha256(args.provider_report),
        "qlib_primary_model_train": "PASS",
        "qlib_control_model_train": "PASS",
        "primary_prediction_rows": len(primary),
        "control_prediction_rows": len(control),
        "primary_prediction_sha256": sha256(primary_path),
        "control_prediction_sha256": sha256(control_path),
        "base_strategy_runs": 0,
        "qlib_backtest": "BLOCKED",
        "walkforward": "BLOCKED",
        "cpcv": "BLOCKED",
        "spa": "BLOCKED",
        "reality_check": "BLOCKED",
        "stepm": "BLOCKED",
        "mcs": "BLOCKED",
        "cost_stress": "BLOCKED",
        "parameter_robustness": "BLOCKED",
        "regime_evidence": "BLOCKED",
        "pandera_validation": "BLOCKED",
        "xnys_validation": "BLOCKED",
        "historical_rehearsal_gate_pass": "NO",
        "historical_rehearsal_status": "BLOCKED_TECHNICAL",
        "certified_model": "NONE",
        "certified_strategy": "NONE",
        "historical_data_is_pristine_oos": "NO",
        "historical_data_can_certify": "NO",
        "failed_mandatory_gates": [
            "QLIB_BACKTEST_END_OF_FROZEN_CALENDAR_BLOCKED",
            "ALL_DEPENDENT_CERTIFICATION_EVIDENCE_NOT_EXECUTED",
        ],
        "blocker_sha256": sha256(blocker_path),
        "current_next": "P2_CERTIFICATION_HISTORICAL_REHEARSAL_BLOCKER_RESOLUTION_001",
        "non_actions": {
            "protocol_threshold_changes": 0,
            "new_data_provider": False,
            "market_data_network_calls": 0,
            "broker_calls": 0,
            "llm_calls": 0,
            "synthetic_rows": 0,
            "forward_fill": False,
            "provider_mutation": False,
        },
    }
    summary_path = args.report_output / "rehearsal-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
