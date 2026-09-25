from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import qlib
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP
from qlib.data.dataset.loader import StaticDataLoader

FEATURES = ["macro_v1_cpiaucsl_d2_log", "macro_v1_unrate_d1"]
QLIB_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"


def digest(frame: pd.DataFrame) -> str:
    data = frame.sort_index().sort_index(axis=1).to_json(
        orient="table", date_format="iso", date_unit="ns", double_precision=15
    ).encode()
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--qlib-source", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    sha = subprocess.run(
        ["git", "-C", str(args.qlib_source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if qlib.__version__ != "0.9.8.dev26" or sha != QLIB_SHA:
        raise RuntimeError("pinned Qlib runtime/source mismatch")
    expected = pd.read_parquet(args.input).set_index(["datetime", "instrument"])[FEATURES].sort_index()
    start, end = expected.index.get_level_values("datetime").min(), expected.index.get_level_values("datetime").max()
    loader = StaticDataLoader({"feature": expected})
    loaded = loader.load().sort_index()["feature"][FEATURES]
    handler = DataHandlerLP(
        instruments=None, start_time=start, end_time=end, data_loader=loader,
        infer_processors=[], learn_processors=[], shared_processors=[],
        process_type=DataHandlerLP.PTYPE_A,
    )
    dataset = DatasetH(handler=handler, segments={"canary": (start, end)})
    actual = dataset.prepare("canary", col_set="feature", data_key=DataHandlerLP.DK_I).sort_index()[FEATURES]
    pd.testing.assert_frame_equal(loaded, expected, check_exact=True)
    pd.testing.assert_frame_equal(actual, expected, check_exact=True)
    result = {
        "status": "PASS", "qlib_version": qlib.__version__, "qlib_source_identity": sha,
        "static_data_loader": "PASS", "data_handler_lp": "PASS", "dataset_h": "PASS",
        "roundtrip_equality": "PASS", "row_count": len(actual),
        "input_sha256": digest(expected), "output_sha256": digest(actual),
        "model_training_count": 0, "prediction_count": 0, "backtest_count": 0,
    }
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
