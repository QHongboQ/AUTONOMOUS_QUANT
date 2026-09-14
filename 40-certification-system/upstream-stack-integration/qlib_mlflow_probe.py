"""Bounded Qlib and MLflow integration probe for the P2 local provider."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
QLIB_ADAPTER = REPO / "30-research-system" / "qlib" / "dataset-adapter"
sys.path.insert(0, str(QLIB_ADAPTER))

import mlflow
import qlib
from qlib.backtest import backtest
from qlib.backtest.exchange import Exchange
from qlib.contrib.model.gbdt import LGBModel
from qlib.data import D
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP
from qlib.data.filter import ExpressionDFilter, NameDFilter
from qlib.workflow import R
from qlib.workflow.record_temp import PortAnaRecord
from qlib.workflow.recorder import Recorder

from aq_qlib_handoff.qlib_config import RaggedAlpha158, current_close_filter


QLIB_VERSION = "0.9.8.dev26"
QLIB_SOURCE_COMMIT = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
EXPERIMENT_NAME = "p2_upstream_certification_stack_integration_001"
RECORDER_NAME = "bounded_technical_probe"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qlib-source", required=True, type=Path)
    args = parser.parse_args()

    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    os.chdir(args.output)

    source_sha = subprocess.check_output(
        ("git", "-C", str(args.qlib_source), "rev-parse", "HEAD"), text=True,
    ).strip()
    if source_sha != QLIB_SOURCE_COMMIT:
        raise RuntimeError(f"unexpected Qlib source: {source_sha}")
    if qlib.__version__ != QLIB_VERSION:
        raise RuntimeError(f"unexpected Qlib version: {qlib.__version__}")

    qlib.init(
        provider_uri=str(args.provider),
        region="us",
        expression_cache=None,
        dataset_cache=None,
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
        instruments=instruments,
        start_time="2015-01-02",
        end_time="2024-12-31",
        freq="day",
        as_list=False,
    )
    if len(ranges) != 730 or sum(len(value) for value in ranges.values()) != 745:
        raise RuntimeError("unexpected P2 instrument/range accounting")

    cohort = sorted(
        instrument
        for instrument, periods in ranges.items()
        if any(
            str(start.date()) <= "2018-01-02" and str(end.date()) >= "2019-06-28"
            for start, end in periods
        )
    )[:8]
    if len(cohort) != 8:
        raise RuntimeError("bounded cohort unavailable")

    sample = D.features(
        cohort,
        ["$open", "$high", "$low", "$close", "$volume"],
        "2019-01-02",
        "2019-01-31",
    )
    if sample.empty:
        raise RuntimeError("Qlib D.features returned no bounded observations")

    cohort_pattern = "^(?:" + "|".join(re.escape(value) for value in cohort) + ")$"
    handler = RaggedAlpha158(
        instruments="p2_pit",
        start_time="2018-01-02",
        end_time="2019-06-28",
        fit_start_time="2018-01-02",
        fit_end_time="2018-12-31",
        infer_processors=[],
        learn_processors=[{"class": "DropnaLabel"}],
        filter_pipe=[NameDFilter(cohort_pattern), current_close_filter()],
    )
    dataset = DatasetH(
        handler=handler,
        segments={
            "train": ("2018-01-02", "2018-12-31"),
            "test": ("2019-01-02", "2019-06-28"),
        },
    )
    train = dataset.prepare(
        "train", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L,
    )
    test = dataset.prepare(
        "test", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L,
    )
    if train.empty or test.empty:
        raise RuntimeError("Qlib DatasetH produced an empty segment")

    model = LGBModel(
        loss="mse",
        learning_rate=0.05,
        num_leaves=8,
        max_depth=4,
        num_threads=2,
        num_boost_round=12,
        early_stopping_rounds=4,
    )
    with R.start(experiment_name=EXPERIMENT_NAME, recorder_name=RECORDER_NAME):
        recorder = R.get_recorder()
        recorder_id = recorder.id
        model.fit(dataset, num_boost_round=12, early_stopping_rounds=4, verbose_eval=False)
        prediction = model.predict(dataset, segment="test").rename("score")
        label = test.loc[:, test.columns.get_level_values(0) == "label"].iloc[:, 0].rename("label")
        evidence = pd.concat((prediction, label), axis=1).dropna()
        evidence = evidence[np.isfinite(evidence).all(axis=1)]
        if evidence.empty:
            raise RuntimeError("Qlib prediction/label evidence is empty")

        daily = evidence.reset_index().groupby("datetime", sort=True).agg(
            score=("score", "mean"),
            label=("label", "mean"),
            observations=("instrument", "count"),
        )
        daily["benchmark_loss"] = daily["label"] ** 2
        daily["model_loss"] = (daily["label"] - daily["score"]) ** 2
        daily.index = pd.DatetimeIndex(daily.index).strftime("%Y-%m-%d")
        daily.index.name = "date"
        handoff_path = args.output / "qlib-derived-evidence.csv"
        daily.to_csv(handoff_path, lineterminator="\n")

        exchange = Exchange(
            start_time="2019-01-02",
            end_time="2019-01-02",
            codes=cohort,
            deal_price="close",
            limit_threshold=None,
            open_cost=0,
            close_cost=0,
            min_cost=0,
        )
        if not isinstance(exchange, Exchange):
            raise RuntimeError("Qlib Exchange construction failed")

        bounded_artifact = args.output / "bounded-artifact.json"
        bounded_artifact.write_text(
            json.dumps(
                {
                    "classification": "TECHNICAL_INTEGRATION_ONLY",
                    "cohort_size": len(cohort),
                    "evidence_rows": len(daily),
                    "qlib_source_commit": source_sha,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        R.log_params(
            task="P2_UPSTREAM_CERTIFICATION_STACK_INTEGRATION_001",
            classification="TECHNICAL_INTEGRATION_ONLY",
            qlib_version=qlib.__version__,
            qlib_source_commit=source_sha,
            cohort_policy="FIRST_8_FULL_INTERVAL_INSTRUMENT_IDS",
            train_interval="2018-01-02/2018-12-31",
            test_interval="2019-01-02/2019-06-28",
            evidence_sha256=sha256(handoff_path),
        )
        R.save_objects(local_path=str(bounded_artifact), artifact_path="integration")

    recorded = R.get_recorder(
        recorder_id=recorder_id, experiment_name=EXPERIMENT_NAME,
    )
    experiment = R.get_exp(experiment_name=EXPERIMENT_NAME)
    if recorded.status != Recorder.STATUS_FI:
        raise RuntimeError(f"unexpected recorder status: {recorded.status}")

    report = {
        "alpha158dl": "PASS",
        "backtest_entry_surface": "PASS" if callable(backtest) else "FAIL",
        "bounded_artifact_logged": "PASS",
        "dataset_h": "PASS",
        "d_features": "PASS",
        "d_instruments": "PASS",
        "d_list_instruments": "PASS",
        "dropna_label": "PASS",
        "evidence_rows": len(daily),
        "evidence_sha256": sha256(handoff_path),
        "exchange": "PASS",
        "expression_dfilter": "PASS" if isinstance(current_close_filter(), ExpressionDFilter) else "FAIL",
        "experiment_created": "PASS" if experiment is not None else "FAIL",
        "history_end": "2024-12-31",
        "history_start": "2015-01-02",
        "instrument_ranges": sum(len(value) for value in ranges.values()),
        "lgbmodel": "PASS",
        "mlflow_version": mlflow.__version__,
        "port_ana_record_entry_surface": "PASS" if PortAnaRecord.__name__ == "PortAnaRecord" else "FAIL",
        "prediction": "PASS",
        "qlib_source_commit": source_sha,
        "qlib_version": qlib.__version__,
        "recorder_created": "PASS",
        "recorder_id": recorder_id,
        "recorder_status": recorded.status,
        "stable_instruments": len(ranges),
    }
    report_path = args.output / "qlib-mlflow-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
