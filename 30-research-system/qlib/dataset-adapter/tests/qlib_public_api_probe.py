"""Tiny synthetic public-API probe executed in the accepted Qlib environment."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import qlib
from qlib.backtest import backtest
from qlib.contrib.data.handler import Alpha158
from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy
from qlib.data import D
from qlib.data.dataset import DatasetH
from qlib.workflow import R
from qlib.workflow.record_temp import PortAnaRecord


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "calendars").mkdir()
    (root / "instruments").mkdir()
    (root / "calendars" / "day.txt").write_text(
        "2020-01-02\n2020-01-03\n2020-01-06\n2020-01-07\n2020-01-08\n2020-01-09\n",
        encoding="utf-8",
    )
    (root / "instruments" / "aq_pit.txt").write_text(
        "TEST\t2020-01-02\t2020-01-03\n"
        "TEST\t2020-01-08\t2020-01-09\n"
        "OTHER\t2020-01-06\t2020-01-09\n",
        encoding="utf-8",
    )
    qlib.init(provider_uri=str(root), region="us", expression_cache=None, dataset_cache=None)
    instruments = D.instruments(market="aq_pit")
    ranges = D.list_instruments(
        instruments=instruments,
        start_time="2020-01-02",
        end_time="2020-01-09",
        freq="day",
        as_list=False,
    )
    assert len(ranges["TEST"]) == 2
    assert str(ranges["TEST"][0][1].date()) == "2020-01-03"
    assert str(ranges["TEST"][1][0].date()) == "2020-01-08"
    print(json.dumps({
        "qlib_version": qlib.__version__,
        "range_count": sum(len(value) for value in ranges.values()),
        "public_apis": [
            DatasetH.__name__, Alpha158.__name__, R.__class__.__name__,
            TopkDropoutStrategy.__name__, backtest.__name__, PortAnaRecord.__name__,
        ],
    }, sort_keys=True))
