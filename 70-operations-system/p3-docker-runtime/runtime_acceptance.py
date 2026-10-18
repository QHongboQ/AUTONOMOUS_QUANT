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
QLIB_DATA = Path("/data/qlib")
WORKSPACE = Path("/workspace")
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
import pandas as pd
import qlib
from qlib.config import REG_US
from qlib.data import D

qlib.init(provider_uri="/data/qlib", region=REG_US)
instruments = D.instruments(market="p2_pit")
calendar = D.calendar(
    start_time="2015-01-02", end_time="2024-12-31", freq="day"
)
dates = {pd.Timestamp(value).strftime("%Y-%m-%d") for value in calendar}
required = (
    "2015-01-02", "2019-12-31", "2020-01-02",
    "2021-12-31", "2022-01-03", "2024-12-31",
)
missing = [value for value in required if value not in dates]
if not instruments:
    raise RuntimeError("p2_pit resolved to an empty instrument set")
if missing:
    raise RuntimeError("required historical calendar dates are missing: " + ",".join(missing))
print(json.dumps({
    "classification": "US_PIT_QLIB_INIT_PASS",
    "region": "US",
    "market": "p2_pit",
    "instrument_count": len(instruments),
    "calendar_count": len(calendar),
    "calendar_start": min(dates),
    "calendar_end": max(dates),
    "required_dates_present": True,
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
        if value.get("classification") == "US_PIT_QLIB_INIT_PASS":
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
        marker = (Path("/opt/aq/p3/templates/p3-official-us/model_template/conf_baseline_factors_model.yaml")).read_text(encoding="utf-8")
        self.assertIn("market: &market p2_pit", marker)
        self.assertNotIn("csi300", marker.lower())
        result = _qlib_data_probe()
        self.assertEqual(result["region"], "US")
        self.assertEqual(result["market"], "p2_pit")
        self.assertTrue(result["required_dates_present"])
        self.assertFalse(result["training_performed"])
        self.assertFalse(result["sealed_oos_accessed"])
        print(json.dumps({"qlib_data_probe": result}, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
