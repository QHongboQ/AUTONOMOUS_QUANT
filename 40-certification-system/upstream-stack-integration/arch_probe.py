"""Use arch public multiple-comparison interfaces on Qlib-derived losses."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import arch
from arch.bootstrap import MCS, SPA, RealityCheck, StepM
import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_value(value):
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def _spa_reality(benchmark: np.ndarray, model: np.ndarray, *, p5_confirmatory: bool) -> dict[str, object]:
    kwargs = ({"block_size": 10, "reps": 5000, "bootstrap": "stationary", "seed": 20260913}
              if p5_confirmatory else {"block_size": 4, "reps": 99})
    spa = SPA(benchmark, model, **({**kwargs, "seed": kwargs.get("seed", 5101)}))
    spa.compute()
    reality = RealityCheck(benchmark, model, **({**kwargs, "seed": kwargs.get("seed", 5102)}))
    reality.compute()
    return {
        "spa_pvalues": json_value(spa.pvalues),
        "spa_consistent_pvalue": float(spa.pvalues.loc["consistent"]),
        "reality_check_pvalues": json_value(reality.pvalues),
        "reality_check_consistent_pvalue": float(reality.pvalues.loc["consistent"]),
    }


def run_interfaces(frame: pd.DataFrame, *, spa_reality_only: bool = False, p5_confirmatory: bool = False) -> dict[str, object]:
    benchmark = frame["benchmark_loss"].to_numpy(dtype=float)
    model = frame[["model_loss"]].to_numpy(dtype=float)
    loss_matrix = np.column_stack((benchmark, model[:, 0]))

    if p5_confirmatory:
        result = {"forward": _spa_reality(benchmark, model, p5_confirmatory=True),
                  "reverse": _spa_reality(model[:, 0], benchmark[:, None], p5_confirmatory=True)}
    else:
        result = _spa_reality(benchmark, model, p5_confirmatory=False)
    if spa_reality_only:
        return result
    stepm = StepM(benchmark, model, block_size=4, reps=99, seed=5103)
    stepm.compute()
    mcs = MCS(loss_matrix, size=0.10, block_size=4, reps=99, seed=5104)
    mcs.compute()
    result.update({
        "mcs_excluded": json_value(mcs.excluded),
        "mcs_included": json_value(mcs.included),
        "stepm_superior_models": json_value(stepm.superior_models),
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--spa-reality-only", action="store_true")
    parser.add_argument("--p5-confirmatory", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)

    frame = pd.read_csv(args.input)
    columns = ["benchmark_loss", "model_loss"]
    if len(frame) < 50 or not np.isfinite(frame[columns].to_numpy(dtype=float)).all():
        raise RuntimeError("Qlib-derived loss evidence is not finite")
    first = run_interfaces(frame, spa_reality_only=args.spa_reality_only, p5_confirmatory=args.p5_confirmatory)
    second = run_interfaces(frame, spa_reality_only=args.spa_reality_only, p5_confirmatory=args.p5_confirmatory)
    if first != second:
        raise RuntimeError("seeded arch results are not reproducible")

    report = {
        "arch_version": arch.__version__,
        "input_rows": len(frame),
        "input_sha256": sha256(args.input),
        "interface_status": "PASS",
        "policy": ({"alpha": 0.05, "bootstrap": "stationary", "block_size": 10, "reps": 5000, "seed": 20260913}
                   if args.p5_confirmatory else {"block_size": 4, "reps": 99, "spa_seed": 5101, "reality_check_seed": 5102}),
        "reality_check": "PASS",
        "reproducibility": "PASS",
        "results": first,
        "spa": "PASS",
    }
    if not args.spa_reality_only:
        report.update({"mcs": "PASS", "stepm": "PASS"})
    path = args.output / "arch-report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
