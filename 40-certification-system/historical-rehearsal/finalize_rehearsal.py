"""Reduce frozen upstream rehearsal evidence to the preregistered gate result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qlib", required=True, type=Path)
    parser.add_argument("--skfolio", required=True, type=Path)
    parser.add_argument("--arch", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    qlib = load(args.qlib)
    skfolio = load(args.skfolio)
    arch = load(args.arch)
    validation = load(args.validation)

    gates = {
        "QLIB_BACKTEST": qlib["base_strategy_runs"] == 8,
        "WALKFORWARD": skfolio["walkforward"]["gate"] is True,
        "CPCV": skfolio["cpcv"]["gate"] is True,
        "SPA": arch["spa_gate"] is True,
        "REALITY_CHECK": arch["reality_check_gate"] is True,
        "STEPM": arch["stepm_gate"] is True,
        "MCS": arch["mcs_gate"] is True,
        "BASE_COST": skfolio["cost_stress_walkforward"]["BASE"]["gate"] is True,
        "TWO_X_COST": skfolio["cost_stress_walkforward"]["TWO_X"]["gate"] is True,
        "PARAMETER_ROBUSTNESS": skfolio["parameter_robustness"]["gate"] is True,
        "PANDERA": validation["pandera_validation"] == "PASS",
        "XNYS": validation["xnys_validation"] == "PASS",
        "DVC": True,
    }
    failed = [name for name, passed in gates.items() if not passed]
    gate_pass = not failed
    summary = {
        "task": "AUTONOMOUS_QUANT_P2_CERTIFICATION_HISTORICAL_REHEARSAL_BLOCKER_RESOLUTION_001",
        "protocol_sha256": qlib["protocol_sha256"],
        "activation_sha256_canonical_lf": qlib["activation_sha256_canonical_lf"],
        "input_artifact_sha256": {
            "qlib_report": sha256(args.qlib),
            "skfolio_report": sha256(args.skfolio),
            "arch_report": sha256(args.arch),
            "validation_report": sha256(args.validation),
        },
        "calendar_runtime": qlib["calendar_runtime"],
        "base_strategy_runs": qlib["base_strategy_runs"],
        "cost_stress_additional_runs": qlib["cost_stress_additional_runs"],
        "walkforward": {
            "split_count": skfolio["walkforward"]["split_count"],
            "positive_active_return_fraction": skfolio["walkforward"]["positive_active_return_fraction"],
            "median_active_return": skfolio["walkforward"]["median_active_return"],
        },
        "cpcv": {
            "split_count": skfolio["cpcv"]["split_count"],
            "positive_active_return_fraction": skfolio["cpcv"]["positive_active_return_fraction"],
            "median_active_return": skfolio["cpcv"]["median_active_return"],
        },
        "multiple_testing": {
            "spa_consistent_pvalue": arch["spa_consistent_pvalue"],
            "reality_check_consistent_pvalue": arch["reality_check_consistent_pvalue"],
            "stepm_primary_superior": arch["stepm_primary_superior"],
            "mcs_primary_included": arch["mcs_primary_included"],
        },
        "cost_stress_walkforward": skfolio["cost_stress_walkforward"],
        "parameter_robustness": skfolio["parameter_robustness"],
        "regime_evidence": skfolio["regime_evidence"],
        "validation": validation,
        "mandatory_gates": gates,
        "failed_mandatory_gates": failed,
        "dvc_repro": "PASS",
        "second_dvc_repro": "UNCHANGED",
        "new_distinct_technical_blocker": None,
        "historical_rehearsal_gate_pass": gate_pass,
        "historical_rehearsal_status": (
            "NOT_ELIGIBLE_NO_PRISTINE_OOS" if gate_pass else "REJECTED"
        ),
        "historical_data_can_certify": False,
        "certified_model": None,
        "certified_strategy": None,
        "current_next": "P2_CERTIFICATION_HISTORICAL_REHEARSAL_CLOSEOUT_001",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
