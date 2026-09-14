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


def run_interfaces(frame: pd.DataFrame) -> dict[str, object]:
    benchmark = frame["benchmark_loss"].to_numpy(dtype=float)
    model = frame[["model_loss"]].to_numpy(dtype=float)
    loss_matrix = np.column_stack((benchmark, model[:, 0]))

    spa = SPA(benchmark, model, block_size=4, reps=99, seed=5101)
    spa.compute()
    reality = RealityCheck(benchmark, model, block_size=4, reps=99, seed=5102)
    reality.compute()
    stepm = StepM(benchmark, model, block_size=4, reps=99, seed=5103)
    stepm.compute()
    mcs = MCS(loss_matrix, size=0.10, block_size=4, reps=99, seed=5104)
    mcs.compute()
    return {
        "mcs_excluded": json_value(mcs.excluded),
        "mcs_included": json_value(mcs.included),
        "reality_check_pvalues": json_value(reality.pvalues),
        "spa_pvalues": json_value(spa.pvalues),
        "stepm_superior_models": json_value(stepm.superior_models),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)

    frame = pd.read_csv(args.input)
    columns = ["benchmark_loss", "model_loss"]
    if len(frame) < 50 or not np.isfinite(frame[columns].to_numpy(dtype=float)).all():
        raise RuntimeError("Qlib-derived loss evidence is not finite")
    first = run_interfaces(frame)
    second = run_interfaces(frame)
    if first != second:
        raise RuntimeError("seeded arch results are not reproducible")

    report = {
        "arch_version": arch.__version__,
        "input_rows": len(frame),
        "input_sha256": sha256(args.input),
        "mcs": "PASS",
        "reality_check": "PASS",
        "reproducibility": "PASS",
        "results": first,
        "spa": "PASS",
        "stepm": "PASS",
    }
    path = args.output / "arch-report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
