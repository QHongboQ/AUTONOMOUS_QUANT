"""Bounded real-data integration probe for the Qlib-native P2 ragged panel."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd


LEAF = Path(__file__).parents[1]
sys.path.insert(0, str(LEAF))

import qlib
from qlib.backtest.decision import Order
from qlib.backtest.exchange import Exchange
from qlib.contrib.model.gbdt import LGBModel
from qlib.data import D
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP

from aq_qlib_handoff.qlib_config import RaggedAlpha158


OBSERVED = {"OBSERVED_PRIMARY", "OBSERVED_SECONDARY"}
CONTROL_TICKERS = {"ARNC", "HWM", "BBBY", "DOW", "DISCK", "ANTM", "ELV", "ABC", "COR", "COG", "CTRA", "UTX", "RTX"}


def key_set(index: pd.MultiIndex) -> set[tuple[str, str]]:
    result = set()
    for entry in index:
        values = dict(zip(index.names, entry))
        result.add((str(values["instrument"]).upper(), pd.Timestamp(values["datetime"]).date().isoformat()))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qlib-source", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)

    source_sha = subprocess.check_output(
        ("git", "-C", str(args.qlib_source), "rev-parse", "HEAD"), text=True,
    ).strip()
    assert source_sha == "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
    assert qlib.__version__ == "0.9.8.dev26"

    per_ticker: dict[str, Counter[str]] = defaultdict(Counter)
    ticker_instruments: dict[str, set[str]] = defaultdict(set)
    instrument_periods: dict[str, Counter[str]] = defaultdict(Counter)
    masked_train: set[tuple[str, str]] = set()
    arnc_missing: tuple[str, str] | None = None
    observed_control: tuple[str, str] | None = None
    availability_path = args.staging / "availability.jsonl.gz"
    with gzip.open(availability_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            instrument = row["instrument"].upper()
            day = row["date"]
            reason = row["reason"]
            ticker = row["historical_ticker"]
            if ticker in CONTROL_TICKERS:
                per_ticker[ticker][reason] += 1
                ticker_instruments[ticker].add(instrument)
            if "2015-01-02" <= day <= "2019-12-31":
                instrument_periods[instrument]["member"] += 1
                instrument_periods[instrument]["observed"] += int(reason in OBSERVED)
                instrument_periods[instrument]["masked"] += int(reason not in OBSERVED)
            if ticker == "ARNC" and reason == "PARTIAL_PROVIDER_COVERAGE":
                arnc_missing = arnc_missing or (instrument, day)
            if observed_control is None and reason in OBSERVED:
                observed_control = (instrument, day)

    # Deterministic, performance-agnostic smoke cohort: first 20 lexicographic
    # instruments with complete 2015-2019 observations, plus the ARNC mask control.
    complete = sorted(
        instrument for instrument, counts in instrument_periods.items()
        if counts["member"] >= 1_200 and counts["masked"] == 0
    )[:20]
    assert len(complete) == 20 and arnc_missing is not None and observed_control is not None
    arnc_instrument = arnc_missing[0]
    smoke_instruments = sorted(set((*complete, arnc_instrument)))

    with gzip.open(availability_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if (
                row["instrument"].upper() in smoke_instruments
                and "2015-01-02" <= row["date"] <= "2018-12-31"
                and row["reason"] not in OBSERVED
            ):
                masked_train.add((row["instrument"].upper(), row["date"]))

    qlib.init(
        provider_uri=str(args.provider), region="us",
        expression_cache=None, dataset_cache=None,
        exp_manager={
            "class": "MLflowExpManager",
            "module_path": "qlib.workflow.expm",
            "kwargs": {
                "uri": "sqlite:///" + str(args.output / "mlflow.db"),
                "default_exp_name": "Experiment",
            },
        },
    )
    instruments = D.instruments(market="p2_pit")
    ranges = D.list_instruments(
        instruments=instruments, start_time="2015-01-02", end_time="2024-12-31",
        freq="day", as_list=False,
    )
    assert len(ranges) == 730 and sum(len(value) for value in ranges.values()) == 745

    observed_frame = D.features([observed_control[0]], ["$close"], observed_control[1], observed_control[1])
    missing_frame = D.features([arnc_missing[0]], ["$close"], arnc_missing[1], arnc_missing[1])
    assert observed_frame["$close"].notna().all()
    assert len(missing_frame) == 1 and missing_frame["$close"].isna().all()

    handler = RaggedAlpha158(
        instruments=smoke_instruments,
        start_time="2015-01-02", end_time="2019-12-31",
        fit_start_time="2015-01-02", fit_end_time="2018-12-31",
        infer_processors=[], learn_processors=[{"class": "DropnaLabel"}],
    )
    dataset = DatasetH(handler=handler, segments={
        "train": ("2015-01-02", "2018-12-31"),
        "valid": ("2019-01-02", "2019-06-28"),
        "test": ("2019-07-01", "2019-12-31"),
    })
    infer_train = dataset.prepare("train", col_set=["feature", "label"], data_key=DataHandlerLP.DK_I)
    learn_train = dataset.prepare("train", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)
    assert isinstance(infer_train, pd.DataFrame) and isinstance(learn_train, pd.DataFrame)
    label_columns = learn_train.columns.get_level_values(0) == "label"
    assert not learn_train.loc[:, label_columns].isna().any(axis=None)
    masked_unusable = len(key_set(learn_train.index) & masked_train)
    assert masked_unusable == 0 and len(masked_train) > 0
    feature_columns = infer_train.columns.get_level_values(0) == "feature"
    feature_values = infer_train.loc[:, feature_columns]
    feature_nan_count = int(feature_values.isna().sum().sum())

    model = LGBModel(
        loss="mse", learning_rate=0.05, num_leaves=8, max_depth=4,
        num_threads=2, num_boost_round=20, early_stopping_rounds=5,
    )
    model.fit(dataset, num_boost_round=20, early_stopping_rounds=5, verbose_eval=False)
    predictions = model.predict(dataset, segment="test")
    assert len(predictions) > 0 and np.isfinite(predictions.to_numpy()).all()

    exchange = Exchange(
        start_time=arnc_missing[1], end_time=arnc_missing[1], codes=[arnc_missing[0]],
        deal_price="close", limit_threshold=None, open_cost=0, close_cost=0, min_cost=0,
    )
    real_suspended = exchange.check_stock_suspended(arnc_missing[0], pd.Timestamp(arnc_missing[1]), pd.Timestamp(arnc_missing[1]))
    real_buy = exchange.is_stock_tradable(arnc_missing[0], pd.Timestamp(arnc_missing[1]), pd.Timestamp(arnc_missing[1]), Order.BUY)
    real_sell = exchange.is_stock_tradable(arnc_missing[0], pd.Timestamp(arnc_missing[1]), pd.Timestamp(arnc_missing[1]), Order.SELL)
    synthetic = Exchange.__new__(Exchange)
    synthetic.quote_df = pd.DataFrame({"$close": [np.nan]})
    synthetic._update_limit(None)
    synthetic_blocked = bool(synthetic.quote_df.loc[0, "limit_buy"] and synthetic.quote_df.loc[0, "limit_sell"])
    assert real_suspended and not real_buy and not real_sell and synthetic_blocked

    assert per_ticker["ARNC"]["PARTIAL_PROVIDER_COVERAGE"] == 455
    assert per_ticker["DISCK"]["KNOWN_TERMINAL_SESSION_PROVIDER_GAP"] == 1
    assert len(ticker_instruments["DOW"]) == 2
    for ticker in CONTROL_TICKERS - {"DOW"}:
        assert ticker_instruments[ticker], ticker

    report = {
        "alpha158_compatible_feature_count": int(feature_values.shape[1]),
        "control_case_counts": {ticker: dict(per_ticker[ticker]) for ticker in sorted(CONTROL_TICKERS)},
        "dataset_h": "PASS",
        "dropna_label": "PASS",
        "feature_nan_count": feature_nan_count,
        "feature_total_values": int(feature_values.size),
        "lgbmodel_smoke": "PASS",
        "masked_rows_in_smoke_training_input": len(masked_train),
        "masked_unusable_rows_in_training": masked_unusable,
        "nan_tradability": "PASS",
        "prediction_rows": len(predictions),
        "prediction_smoke": "PASS",
        "qlib_init": "PASS",
        "qlib_source_commit": source_sha,
        "qlib_version": qlib.__version__,
        "real_missing_control": {"instrument": arnc_missing[0], "date": arnc_missing[1]},
        "stable_instruments": len(ranges),
        "instrument_ranges": sum(len(value) for value in ranges.values()),
        "trainable_label_rows": len(learn_train),
    }
    (args.output / "integration-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
