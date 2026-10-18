"""Offline, read-only acceptance checks for the pinned P3 runtime image."""

from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


RDAGENT_SHA = "484776c211e4fbbeef03e0ec00d6bbee7362a4f4"
QLIB_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
ENV_ROOT = Path("/opt/conda/envs/rdagent4qlib")
FACTOR_DATA = Path("/data/factor-source")
QLIB_DATA = Path("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data")
QLIB_CALENDAR = Path("/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime")
WORKSPACE = Path("/workspace")
P2_PIT_SHA256 = "e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875"
TEMPLATE_ROOT = Path("/opt/aq/p3/templates/p3-official-us")
EXPECTED_DATES = (
    "2015-01-02",
    "2019-12-31",
    "2020-01-02",
    "2021-12-31",
    "2022-01-03",
    "2024-12-31",
)


def _distribution_version(name: str) -> str:
    return importlib.metadata.version(name)


def _direct_commit(distribution_name: str) -> str:
    raw = importlib.metadata.distribution(distribution_name).read_text("direct_url.json")
    if not raw:
        return ""
    value = json.loads(raw)
    return value.get("vcs_info", {}).get("commit_id", "")


def _qlib_distribution_identity() -> tuple[str, str]:
    code = 'import importlib.metadata as m, json; d=m.distribution("pyqlib"); u=json.loads(d.read_text("direct_url.json")); print(json.dumps({"version":d.version,"commit":u.get("vcs_info",{}).get("commit_id","")}))'
    result = subprocess.run(
        ["conda", "run", "--name", "rdagent4qlib", "--no-capture-output", "python", "-c", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise AssertionError(f"Qlib identity probe failed ({result.returncode}): {result.stderr[-1200:]}")
    value = next(json.loads(line) for line in reversed(result.stdout.splitlines()) if line.startswith("{"))
    return value["version"], value["commit"]


def _qlib_data_probe() -> dict[str, object]:
    code = r'''
import json
import hashlib
from pathlib import Path
import pandas as pd
import qlib
from qlib.config import REG_US
from qlib.data import D

provider = Path("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data")
calendar_provider = Path("/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime")
template = Path("/opt/aq/p3/templates/p3-official-us/factor_template/conf_baseline.yaml")
import yaml
template_text = template.read_text(encoding="utf-8")
native_config = yaml.safe_load(template_text.split("\nmarket:", 1)[0])["qlib_init"]
assert native_config["provider_uri"] == str(provider)
assert native_config["calendar_provider"]["kwargs"]["backend"]["kwargs"]["provider_uri"] == str(calendar_provider)
assert provider.is_dir() and calendar_provider.is_dir()
assert hashlib.sha256((provider / "instruments/p2_pit.txt").read_bytes()).hexdigest() == "e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875"
for rel, expected in (
    ("calendars/day.txt", "d4c0c100af851245f6f894e275e5d494d7e1cbd07f82d342c034cbdf7b7bfa4d"),
    ("calendars/day_future.txt", "3225eab67ebddcd53022bec56d2d8fa99745a2d7990722c36eee57185566937d"),
):
    assert hashlib.sha256((calendar_provider / rel).read_bytes()).hexdigest() == expected

qlib.init(
    provider_uri=native_config["provider_uri"],
    region=REG_US,
    calendar_provider=native_config["calendar_provider"],
    expression_cache=None,
    dataset_cache=None,
)
instrument_config = D.instruments(market="p2_pit")
observed = D.list_instruments(
    instruments=instrument_config,
    start_time="2015-01-02", end_time="2024-12-31", freq="day", as_list=False,
)
reference_rows = [
    line.split() for line in (provider / "instruments/p2_pit.txt").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
reference = {}
for instrument, start, end in reference_rows:
    reference.setdefault(instrument, []).append((start, end))
def normalized(value):
    return pd.Timestamp(value).strftime("%Y-%m-%d")
observed_normalized = {
    instrument: sorted((normalized(start), normalized(end)) for start, end in ranges)
    for instrument, ranges in observed.items()
}
reference_normalized = {instrument: sorted(ranges) for instrument, ranges in reference.items()}
if observed_normalized != reference_normalized:
    raise RuntimeError("native Qlib p2_pit membership differs from frozen provider authority")
calendar = D.calendar(
    start_time="2015-01-02", end_time="2024-12-31", freq="day"
)
dates = {pd.Timestamp(value).strftime("%Y-%m-%d") for value in calendar}
required = (
    "2015-01-02", "2019-12-31", "2020-01-02",
    "2021-12-31", "2022-01-03", "2024-12-31",
)
missing = [value for value in required if value not in dates]
if not observed:
    raise RuntimeError("p2_pit resolved to an empty instrument set")
if len(observed) != 730 or len(reference_rows) != 745 or sum(map(len, observed.values())) != 745:
    raise RuntimeError("native p2_pit membership counts differ from frozen authority (730/745)")
if missing:
    raise RuntimeError("required historical calendar dates are missing: " + ",".join(missing))
sample = "P2SEC00A2606527FADDDA12E3E76CDEA395D253F930C87F0E430726CA4C16E027FBB7"
price = D.features([sample], ["$close"], "2015-12-29", "2015-12-29", disk_cache=0)
if price.empty or price["$close"].isna().all():
    raise RuntimeError("native Qlib historical close feature read returned no observation")
print(json.dumps({
    "classification": "US_PIT_QLIB_DATA_ACCEPTANCE_PASS",
    "region": "US",
    "market": "p2_pit",
    "instrument_count": len(observed),
    "membership_range_count": sum(map(len, observed.values())),
    "membership_matches_frozen_authority": True,
    "reference_sha256": hashlib.sha256((provider / "instruments/p2_pit.txt").read_bytes()).hexdigest(),
    "calendar_count": len(calendar),
    "calendar_start": min(dates),
    "calendar_end": max(dates),
    "required_dates_present": True,
    "historical_feature_read": {"instrument": sample, "date": "2015-12-29", "close_observed": True},
    "provider_uri": str(provider),
    "calendar_provider_uri": str(calendar_provider),
    "training_performed": False,
    "sealed_oos_accessed": False,
}, sort_keys=True))
'''
    result = subprocess.run(
        ["conda", "run", "--name", "rdagent4qlib", "--no-capture-output", "python", "-c", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
        env=os.environ.copy(),
    )
    if result.returncode != 0:
        raise AssertionError(f"Qlib data probe failed ({result.returncode}): {result.stderr[-1200:]}")
    for line in reversed(result.stdout.splitlines()):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if value.get("classification") == "US_PIT_QLIB_DATA_ACCEPTANCE_PASS":
            return value
    raise AssertionError("Qlib data probe did not emit its success record")


class PinnedDockerRuntimeAcceptance(unittest.TestCase):
    def test_worker_is_nonroot_networkless_and_has_dedicated_workspace(self) -> None:
        self.assertNotEqual(os.getuid(), 0)
        self.assertTrue(WORKSPACE.is_dir())
        probe = WORKSPACE / ".runtime-acceptance-write-probe"
        probe.write_text("temporary workspace is writable\n", encoding="utf-8")
        probe.unlink()
        self.assertFalse(Path("/var/run/docker.sock").exists())
        with Path("/proc/net/route").open(encoding="ascii") as stream:
            routes = [line.split() for line in stream.readlines()[1:] if line.split()]
        self.assertFalse(any(fields[1] == "00000000" for fields in routes))

    def test_upstream_runtime_versions_and_source_commits(self) -> None:
        self.assertEqual(_distribution_version("rdagent"), "1.0.0")
        self.assertEqual(_direct_commit("rdagent"), RDAGENT_SHA)
        self.assertEqual(_qlib_distribution_identity(), ("0.9.8.dev26", QLIB_SHA))

    def test_conda_and_native_quant_dependencies(self) -> None:
        self.assertTrue(Path("/opt/conda/condabin/conda").exists())
        self.assertTrue(ENV_ROOT.is_dir())
        result = subprocess.run(
            ["conda", "run", "--name", "rdagent4qlib", "--no-capture-output", "python", "-c", "import qlib; print(qlib.__version__)"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-1200:])
        self.assertIn("0.9.8.dev26", result.stdout)
        checks = {
            "lightgbm": "4.7.0",
            "tables": "3.10.1",
            "torch": "2.14.0+cpu",
            "catboost": "1.2.10",
            "xgboost": "3.2.0",
        }
        code = "import importlib.metadata as m; " + "; ".join(
            f"assert m.version({name!r}) == {version!r}, m.version({name!r})"
            for name, version in checks.items()
        )
        code += "; import lightgbm, tables, torch, catboost, xgboost"
        imports = subprocess.run(
            ["conda", "run", "--name", "rdagent4qlib", "--no-capture-output", "python", "-c", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(imports.returncode, 0, imports.stderr[-1600:])

    def test_rdagent_factor_and_model_environment_resolution(self) -> None:
        self.assertEqual(os.environ.get("MODEL_COSTEER_ENV_TYPE"), "conda")
        self.assertEqual(os.environ.get("CONDA_DEFAULT_ENV"), "rdagent4qlib")
        self.assertEqual(
            os.environ.get("FACTOR_COSTEER_PYTHON_BIN"),
            str(ENV_ROOT / "bin/python"),
        )
        from rdagent.components.coder.factor_coder.config import FACTOR_COSTEER_SETTINGS, get_factor_env
        from rdagent.components.coder.model_coder.conf import MODEL_COSTEER_SETTINGS, get_model_env
        from rdagent.utils.env import QlibCondaEnv

        self.assertEqual(MODEL_COSTEER_SETTINGS.env_type, "conda")
        self.assertEqual(FACTOR_COSTEER_SETTINGS.data_folder, "/data/factor-source/full")
        self.assertEqual(FACTOR_COSTEER_SETTINGS.data_folder_debug, "/data/factor-source/debug")
        factor_env = get_factor_env()
        model_env = get_model_env()
        self.assertEqual(factor_env.conf.conda_env_name, "rdagent4qlib")
        self.assertIn("/opt/conda/envs/rdagent4qlib/bin", factor_env.conf.bin_path)
        self.assertIsInstance(model_env, QlibCondaEnv)
        self.assertEqual(model_env.conf.conda_env_name, "rdagent4qlib")
        self.assertIn("/opt/conda/envs/rdagent4qlib/bin", model_env.conf.bin_path)
        binding = Path("/opt/aq/p3/binding/aq_rdagent_official_us_binding.py")
        templates = Path("/opt/aq/p3/templates/p3-official-us")
        self.assertTrue(binding.is_file())
        self.assertTrue((templates / "factor_template/conf_baseline.yaml").is_file())
        self.assertTrue((templates / "model_template/conf_baseline_factors_model.yaml").is_file())

    def test_only_approved_data_paths_are_present_and_qlib_resolves_us_pit(self) -> None:
        self.assertTrue((FACTOR_DATA / "full").is_dir())
        self.assertTrue((FACTOR_DATA / "debug").is_dir())
        self.assertTrue((QLIB_DATA / "instruments/p2_pit.txt").is_file())
        self.assertTrue((QLIB_CALENDAR / "calendars/day.txt").is_file())
        self.assertTrue((QLIB_CALENDAR / "calendars/day_future.txt").is_file())
        for template in sorted(TEMPLATE_ROOT.glob("*/*.yaml")):
            text = template.read_text(encoding="utf-8")
            self.assertIn(str(QLIB_DATA), text, template.name)
            self.assertIn(str(QLIB_CALENDAR), text, template.name)
        marker = (TEMPLATE_ROOT / "model_template/conf_baseline_factors_model.yaml").read_text(encoding="utf-8")
        self.assertIn("market: &market p2_pit", marker)
        self.assertNotIn("csi300", marker.lower())
        result = _qlib_data_probe()
        self.assertEqual(result["region"], "US")
        self.assertEqual(result["market"], "p2_pit")
        self.assertTrue(result["required_dates_present"])
        self.assertTrue(result["membership_matches_frozen_authority"])
        self.assertEqual(result["instrument_count"], 730)
        self.assertEqual(result["membership_range_count"], 745)
        self.assertEqual(result["reference_sha256"], P2_PIT_SHA256)
        self.assertTrue(result["historical_feature_read"]["close_observed"])
        self.assertEqual(result["provider_uri"], str(QLIB_DATA))
        self.assertEqual(result["calendar_provider_uri"], str(QLIB_CALENDAR))
        self.assertFalse(result["training_performed"])
        self.assertFalse(result["sealed_oos_accessed"])
        print(json.dumps({"qlib_data_probe": result}, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
