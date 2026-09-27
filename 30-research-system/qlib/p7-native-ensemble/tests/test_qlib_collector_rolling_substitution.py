from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import qlib
from pandas.testing import assert_frame_equal
from qlib.model.ens.ensemble import SingleKeyEnsemble
from qlib.model.ens.group import RollingGroup
from qlib.workflow import R
from qlib.workflow.online.utils import OnlineToolR
from qlib.workflow.task.collect import MergeCollector, RecorderCollector

MODULE_PATH = Path(__file__).parents[1] / "time_effective_roster_handoff.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("time_effective_roster_handoff", MODULE_PATH)
assert SPEC and SPEC.loader
handoff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = handoff
SPEC.loader.exec_module(handoff)

QLIB_VERSION = "0.9.8.dev26"
QLIB_SOURCE_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
EXPERIMENT = "p7-qlib-collector-rolling-substitution-poc"
EVIDENCE_ENV = "AQ_P7_COLLECTOR_POC_ROOT"


def identity(number: int) -> str:
    return f"sha256:{number:064x}"


def frame_sha256(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(float_format="%.17g", lineterminator="\n").encode()
    return hashlib.sha256(payload).hexdigest()


class QlibCollectorRollingSubstitutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if qlib.__version__ != QLIB_VERSION:
            raise RuntimeError(f"unexpected Qlib version: {qlib.__version__}")

        retained_root = os.environ.get(EVIDENCE_ENV)
        cls._temporary_root = None
        if retained_root:
            cls.root = Path(retained_root)
            cls.root.mkdir(parents=True, exist_ok=False)
        else:
            cls._temporary_root = tempfile.TemporaryDirectory()
            cls.root = Path(cls._temporary_root.name)

        cls._prior_cwd = Path.cwd()
        os.chdir(cls.root)
        provider = cls.root / "empty-provider"
        provider.mkdir()
        cls.tracking_uri = f"sqlite:///{cls.root / 'mlflow.db'}"
        qlib.init(
            provider_uri=str(provider),
            expression_cache=None,
            dataset_cache=None,
        )

        cls.sessions = pd.to_datetime(
            [
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-08",
                "2024-01-09",
            ]
        )
        cls.instruments = ["SYNTH_A", "SYNTH_B", "SYNTH_C"]
        cls.eligible_index = pd.MultiIndex.from_product(
            [cls.sessions, cls.instruments], names=["datetime", "instrument"]
        )
        cls.members = {
            number: handoff.RosterMember(
                candidate_id=identity(number),
                authorization_evidence_id=identity(100 + number),
            )
            for number in range(1, 6)
        }
        cls.selected = {
            cls.sessions[0].date().isoformat(): tuple(cls.members[i] for i in (1, 2, 3)),
            cls.sessions[1].date().isoformat(): tuple(cls.members[i] for i in (1, 2, 3)),
            cls.sessions[2].date().isoformat(): tuple(cls.members.values()),
            cls.sessions[3].date().isoformat(): tuple(cls.members.values()),
            cls.sessions[4].date().isoformat(): tuple(cls.members[i] for i in (4, 5)),
            cls.sessions[5].date().isoformat(): tuple(cls.members[i] for i in (4, 5)),
        }

        cls.frames = cls._build_rolling_frames()
        cls.recorders = cls._record_fixture_artifacts()
        cls.native_predictions, cls.raw_keys = cls._collect_native_predictions()
        cls.manual_predictions = cls._manual_roll_predictions()

        tool = OnlineToolR(default_exp_name=EXPERIMENT)
        latest_recorders = [
            max(
                (rec for rec in cls.recorders if rec.list_tags()["candidate_id"] == identity(i)),
                key=lambda rec: rec.list_tags()["rolling_version"],
            )
            for i in range(1, 6)
        ]
        old_recorders = [rec for rec in cls.recorders if rec not in latest_recorders]
        tool.set_online_tag(OnlineToolR.OFFLINE_TAG, old_recorders)
        tool.set_online_tag(OnlineToolR.ONLINE_TAG, latest_recorders)
        with R.uri_context(cls.tracking_uri):
            online_recorders = tool.online_models(EXPERIMENT)
        cls.runtime_ready = frozenset(
            rec.list_tags()["candidate_id"] for rec in online_recorders
        )

        cls.current_output, cls.current_report = handoff.combine_selected_roster_predictions(
            selected=cls.selected,
            predictions=cls.manual_predictions,
            runtime_ready_candidates=cls.runtime_ready,
            eligible_index=cls.eligible_index,
        )
        cls.native_output, cls.native_report = handoff.combine_selected_roster_predictions(
            selected=cls.selected,
            predictions=cls.native_predictions,
            runtime_ready_candidates=cls.runtime_ready,
            eligible_index=cls.eligible_index,
        )
        cls._write_private_evidence()

    @classmethod
    def tearDownClass(cls) -> None:
        os.chdir(cls._prior_cwd)
        if cls._temporary_root is not None:
            cls._temporary_root.cleanup()

    @classmethod
    def _frame(
        cls,
        candidate: int,
        rolling_version: str,
        sessions: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        patterns = {
            1: [1.0, 2.0, 3.0],
            2: [3.0, 1.0, 2.0],
            3: [2.0, 3.0, 1.0],
            4: [1.0, 3.0, 2.0],
            5: [2.0, 1.0, 3.0],
        }
        offset = 10.0 if rolling_version == "R2" else 0.0
        index = pd.MultiIndex.from_product(
            [sessions, cls.instruments], names=["datetime", "instrument"]
        )
        values = [value + offset for _ in sessions for value in patterns[candidate]]
        return pd.DataFrame({"score": values}, index=index)

    @classmethod
    def _build_rolling_frames(cls) -> dict[tuple[int, str], pd.DataFrame]:
        return {
            (1, "R1"): cls._frame(1, "R1", cls.sessions[:3]),
            (1, "R2"): cls._frame(1, "R2", cls.sessions[2:4]),
            (2, "R1"): cls._frame(2, "R1", cls.sessions[:3]),
            (2, "R2"): cls._frame(2, "R2", cls.sessions[2:4]),
            (3, "R1"): cls._frame(3, "R1", cls.sessions[:4]),
            (4, "R1"): cls._frame(4, "R1", cls.sessions[2:]),
            (5, "R1"): cls._frame(5, "R1", cls.sessions[2:]),
        }

    @classmethod
    def _record_fixture_artifacts(cls) -> list[object]:
        recorders = []
        for (candidate, version), frame in cls.frames.items():
            with R.start(
                experiment_name=EXPERIMENT,
                recorder_name=f"C{candidate}-{version}",
                uri=cls.tracking_uri,
            ):
                recorder = R.get_recorder()
                recorder.save_objects(**{"pred.pkl": frame})
                recorder.set_tags(
                    candidate_id=identity(candidate),
                    rolling_version=version,
                    evidence_classification="TEST_FIXTURE_NOT_REAL_EVIDENCE",
                )
            recorders.append(recorder)
        return recorders

    @staticmethod
    def _recorder_key(recorder: object) -> tuple[str, str]:
        tags = recorder.list_tags()
        return tags["candidate_id"], tags["rolling_version"]

    @classmethod
    def _collect_native_predictions(cls) -> tuple[dict[str, pd.DataFrame], set[tuple[str, str]]]:
        raw_collector = RecorderCollector(
            lambda: cls.recorders,
            rec_key_func=cls._recorder_key,
            artifacts_path={"pred": "pred.pkl"},
        )
        raw = raw_collector.collect()["pred"]

        collectors = {}
        for candidate in range(1, 6):
            candidate_id = identity(candidate)
            candidate_recorders = [
                rec
                for rec in cls.recorders
                if rec.list_tags()["candidate_id"] == candidate_id
            ]
            collectors[candidate_id] = RecorderCollector(
                lambda recs=candidate_recorders: recs,
                process_list=[RollingGroup(), SingleKeyEnsemble()],
                rec_key_func=cls._recorder_key,
                artifacts_path={"pred": "pred.pkl"},
            )

        merged = MergeCollector(
            collectors,
            merge_func=lambda candidate_id, artifact: candidate_id
            if artifact == "pred"
            else (candidate_id, artifact),
        )()
        return merged, set(raw)

    @classmethod
    def _manual_roll_predictions(cls) -> dict[str, pd.DataFrame]:
        rolled = {}
        for candidate in range(1, 6):
            pieces = [
                frame
                for (number, _), frame in cls.frames.items()
                if number == candidate
            ]
            frame = pd.concat(pieces)
            rolled[identity(candidate)] = frame[
                ~frame.index.duplicated(keep="last")
            ].sort_index()
        return rolled

    @classmethod
    def _write_private_evidence(cls) -> None:
        if EVIDENCE_ENV not in os.environ:
            return
        artifact_rows = []
        for recorder in cls.recorders:
            path = Path(recorder.download_artifact("pred.pkl"))
            tags = recorder.list_tags()
            artifact_rows.append(
                {
                    "candidate_id": tags["candidate_id"],
                    "rolling_version": tags["rolling_version"],
                    "recorder_id": recorder.id,
                    "pred_artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        result = {
            "classification": "TEST_FIXTURE_NOT_REAL_EVIDENCE",
            "qlib_version": QLIB_VERSION,
            "qlib_source_sha": QLIB_SOURCE_SHA,
            "synthetic_recorder_count": len(cls.recorders),
            "candidate_count": len(cls.native_predictions),
            "roster_sequence": [3, 5, 2],
            "recorder_key_preserves_candidate_and_rolling_version": True,
            "rolling_overlap_latest_prediction_wins": True,
            "runtime_readiness_owner": "QLIB_ONLINETOOLR_SYNTHETIC_TAGS",
            "authorization_owner": "EXTERNAL_P2_P4_OR_RESEARCH_AUTHORITY",
            "qlib_online_tag_is_certification_authority": False,
            "current_path_output_sha256": frame_sha256(cls.current_output),
            "native_chain_output_sha256": frame_sha256(cls.native_output),
            "exact_output_match": cls.current_output.equals(cls.native_output),
            "exact_report_match": cls.current_report.equals(cls.native_report),
            "real_training_count": 0,
            "real_prediction_generation_count": 0,
            "real_ensemble_count": 0,
            "backtest_count": 0,
            "p2_sealed_oos_accessed": False,
            "recorders": artifact_rows,
        }
        result_path = cls.root / "poc-result.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checksum = hashlib.sha256(result_path.read_bytes()).hexdigest()
        (cls.root / "checksums.json").write_text(
            json.dumps({"poc-result.json": checksum}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_recorder_keys_preserve_candidate_and_rolling_version(self) -> None:
        expected = {
            (identity(candidate), version) for candidate, version in self.frames
        }
        self.assertEqual(self.raw_keys, expected)
        self.assertEqual(len(self.recorders), 7)

    def test_rolling_overlap_uses_later_window_prediction(self) -> None:
        overlap = pd.Timestamp("2024-01-04")
        for candidate in (1, 2):
            actual = self.native_predictions[identity(candidate)].xs(
                overlap, level="datetime"
            )
            expected = self.frames[(candidate, "R2")].xs(overlap, level="datetime")
            assert_frame_equal(actual, expected)

    def test_merge_collector_produces_candidate_to_rolled_prediction(self) -> None:
        self.assertEqual(set(self.native_predictions), {identity(i) for i in range(1, 6)})
        for prediction in self.native_predictions.values():
            self.assertEqual(list(prediction.columns), ["score"])
            self.assertFalse(prediction.index.has_duplicates)

    def test_native_chain_matches_current_handoff_exactly(self) -> None:
        assert_frame_equal(self.native_output, self.current_output, check_exact=True)
        assert_frame_equal(self.native_report, self.current_report, check_exact=True)
        self.assertEqual(
            self.native_report["authorized_member_count"].tolist(),
            [3, 3, 5, 5, 2, 2],
        )

    def test_runtime_ready_but_unauthorized_candidate_does_not_contribute(self) -> None:
        first_session = self.sessions[0].date().isoformat()
        authorized = {member.candidate_id for member in self.selected[first_session]}
        self.assertTrue({identity(4), identity(5)} <= self.runtime_ready - authorized)
        assert_frame_equal(self.native_output, self.current_output, check_exact=True)

    def test_authorized_but_not_runtime_ready_fails_at_runtime_boundary(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "authorized Candidate is not runtime-ready"):
            handoff.combine_selected_roster_predictions(
                selected=self.selected,
                predictions=self.native_predictions,
                runtime_ready_candidates=self.runtime_ready - {identity(2)},
                eligible_index=self.eligible_index,
            )

    def test_collection_and_replay_are_deterministic(self) -> None:
        replay, replay_keys = self._collect_native_predictions()
        self.assertEqual(replay_keys, self.raw_keys)
        self.assertEqual(set(replay), set(self.native_predictions))
        for candidate_id in replay:
            assert_frame_equal(
                replay[candidate_id], self.native_predictions[candidate_id], check_exact=True
            )

    def test_private_evidence_is_non_scientific_when_retained(self) -> None:
        if EVIDENCE_ENV in os.environ:
            result = json.loads((self.root / "poc-result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["classification"], "TEST_FIXTURE_NOT_REAL_EVIDENCE")
            self.assertEqual(result["real_training_count"], 0)
            self.assertEqual(result["backtest_count"], 0)


if __name__ == "__main__":
    unittest.main()
