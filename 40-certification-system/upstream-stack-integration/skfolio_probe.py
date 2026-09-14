"""Use skfolio public temporal-CV interfaces on Qlib-derived evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import skfolio
from skfolio.model_selection import CombinatorialPurgedCV, WalkForward


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)

    frame = pd.read_csv(args.input)
    values = frame[["score", "label", "benchmark_loss", "model_loss"]].to_numpy(dtype=float)
    if len(values) < 50 or not np.isfinite(values).all():
        raise RuntimeError("Qlib-derived evidence is not a finite bounded matrix")

    walk_forward = WalkForward(test_size=10, train_size=30, purged_size=2)
    walk_splits = list(walk_forward.split(values))
    if not walk_splits or any(set(train) & set(test) for train, test in walk_splits):
        raise RuntimeError("WalkForward did not return disjoint train/test indices")

    cpcv = CombinatorialPurgedCV(
        n_folds=5, n_test_folds=2, purged_size=2, embargo_size=2,
    )
    cpcv_splits = list(cpcv.split(values))
    if not cpcv_splits:
        raise RuntimeError("CombinatorialPurgedCV returned no splits")
    for train, test_groups in cpcv_splits:
        combined_test = np.concatenate(test_groups)
        if set(train) & set(combined_test):
            raise RuntimeError("CPCV returned overlapping train/test indices")

    evidence = {
        "cpcv": "PASS",
        "cpcv_embargo_size": 2,
        "cpcv_n_folds": 5,
        "cpcv_n_test_folds": 2,
        "cpcv_purged_size": 2,
        "cpcv_split_count": len(cpcv_splits),
        "input_rows": len(frame),
        "input_sha256": sha256(args.input),
        "purge_embargo_upstream_owner": "SKFOLIO",
        "skfolio_version": skfolio.__version__,
        "walkforward": "PASS",
        "walkforward_purged_size": 2,
        "walkforward_split_count": len(walk_splits),
        "walkforward_test_size": 10,
        "walkforward_train_size": 30,
    }
    path = args.output / "skfolio-report.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
