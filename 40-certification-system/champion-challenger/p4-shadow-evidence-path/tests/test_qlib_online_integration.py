from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import pandas as pd
import qlib
from qlib.constant import REG_US
from qlib.model.trainer import TrainerR
from qlib.workflow.online.manager import OnlineManager
from qlib.workflow.online.strategy import RollingStrategy
from qlib.workflow.online.utils import OnlineToolR
from qlib.workflow.task.gen import RollingGen


EVIDENCE = Path(
    "/mnt/d/AQ_DATA/P4/shadow-evidence-path-and-qlib-online-integration-001"
)


def load(name: str) -> dict[str, object]:
    value = json.loads((EVIDENCE / name).read_bytes())
    if not isinstance(value, dict):
        raise AssertionError(f"{name} is not a JSON object")
    return value


class QlibOnlineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        qlib.init(
            provider_uri="/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data",
            region=REG_US,
            expression_cache=None,
            dataset_cache=None,
        )

    def test_real_upstream_component_graph_constructs_without_aq_subclasses(self) -> None:
        task = {
            "model": {"class": "LinearModel"},
            "dataset": {"kwargs": {"segments": {"test": ("2021-01-04", "2021-02-02")}}},
        }
        rolling = RollingGen(step=21)
        strategy = RollingStrategy("fixture", task, rolling)
        trainer = TrainerR(experiment_name="fixture")
        manager = OnlineManager(strategy, trainer=trainer, begin_time="2021-01-04")
        self.assertIs(type(manager), OnlineManager)
        self.assertIs(type(strategy), RollingStrategy)
        self.assertIs(type(rolling), RollingGen)
        self.assertIs(type(trainer), TrainerR)
        self.assertIs(type(strategy.tool), OnlineToolR)
        self.assertEqual(rolling.step, 21)

    def test_real_online_history_has_two_distinct_timepoints(self) -> None:
        history = load("online_history_manifest.json")
        rows = history["history"]
        self.assertEqual(history["history_timepoint_count"], 2)
        self.assertEqual(len({row["time"] for row in rows}), 2)
        self.assertTrue(all(row["online_recorder_ids"] for row in rows))
        self.assertTrue(
            all(
                row["strategy_class"]
                == "qlib.workflow.online.strategy.RollingStrategy"
                for row in rows
            )
        )

    def test_real_online_tool_tags_show_replacement(self) -> None:
        report = load("online_tag_report.json")
        self.assertEqual(report["online_recorder_count"], 1)
        self.assertEqual(report["offline_recorder_count"], 1)
        self.assertFalse(report["qlib_online_tag_is_p4_shadow_authority"])
        self.assertEqual(
            {row["online_status"] for row in report["recorders"]},
            {OnlineToolR.ONLINE_TAG, OnlineToolR.OFFLINE_TAG},
        )

    def test_sigana_rankic_is_real_upstream_artifact(self) -> None:
        report = load("sigana_identity_report.json")
        artifact = Path(report["artifact_path"])
        self.assertTrue(artifact.is_file())
        self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), report["artifact_sha256"])
        self.assertFalse(report["aq_rankic_computation"])
        self.assertEqual(report["qlib_recorder_id"], report["mlflow_run_id"])

    def test_historical_test_and_sealed_oos_firewalls(self) -> None:
        report = load("qlib_online_identity_report.json")
        self.assertLess(pd.Timestamp(report["max_label_date"]), pd.Timestamp("2022-01-03"))
        self.assertEqual(report["historical_test_rows_accessed"], 0)
        self.assertEqual(report["sealed_oos_rows_accessed"], 0)
        self.assertEqual(report["broker_calls"], 0)
        self.assertEqual(report["order_count"], 0)
        self.assertEqual(report["capital_allocated"], 0)


if __name__ == "__main__":
    unittest.main()
