from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, time, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import exchange_calendars as xcals

REPO = Path(__file__).resolve().parents[3]
for relative in (
    "10-data-system/fundamentals/historical-dataset",
    "20-intelligence-system/fundamental-factors/evidence-contract",
    "20-intelligence-system/fundamental-factors/p5-filing-features",
    "30-research-system/qlib/dataset-adapter",
    "40-certification-system/p5-downstream-composition",
):
    sys.path.insert(0, str(REPO / relative))

from aq_edgartools_full_build import (  # noqa: E402
    TerminalCloseoutError,
    verify_terminal_handoff,
)
from aq_p5_filing_features import (  # noqa: E402
    FilingFeatureObservationV1,
    discover_native_filing_observations,
    seal_historical_filing_features,
)
from aq_qlib_handoff.p5_surfaces import (  # noqa: E402
    CONTROL_FEATURES,
    FILING_FEATURES,
    FUNDAMENTAL_FEATURES,
)
from run_p5_downstream import (  # noqa: E402
    LEAKAGE_GATES,
    P5_ARCH,
    P5_SKFOLIO,
    classify_comparison,
    evaluate_final_policy,
    resolve_handoff_artifact_root,
    run_real,
    verify_runtime_config,
    verify_evidence_bundle,
)

PANDERA_PYTHON = sys.executable
QLIB_PYTHON = "/home/zhou/miniforge3/envs/rdagent4qlib/bin/python"
SCRIPT = REPO / "40-certification-system/p5-downstream-composition/run_p5_downstream.py"


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _win(path: Path) -> str:
    return subprocess.run(
        ["wslpath", "-w", str(path)], check=True, capture_output=True, text=True
    ).stdout.strip()


def _terminal(root: Path) -> dict[str, object]:
    artifact = root / "fundamentals.parquet"
    artifact.write_bytes(b"sealed-synthetic-fundamentals")
    return {
        "schema_version": "P5HistoricalBuildHandoffV1",
        "build_identity": "synthetic-build",
        "manifest_identity": "synthetic-manifest",
        "dvc_identity": "synthetic-dvc",
        "global_accession_count": 36206,
        "source_verifiable_accession_count": 36204,
        "source_unavailable_accession_count": 2,
        "unaccounted_global_accession_count": 0,
        "duplicate_global_accounting_count": 0,
        "terminal_state_counts": {
            "COMPLETE_WITH_EVIDENCE": 36204,
            "COMPLETE_NO_AUTHORIZED_FACTS": 0,
            "COMPLETE_NO_STRUCTURED_FINANCIALS": 0,
            "SKIPPED_OUTSIDE_AUTHORIZED_HISTORY": 0,
            "FAILED_TRANSIENT": 0,
            "FAILED_DETERMINISTIC": 0,
            "FAILED_REQUIRED_ACCESSION": 0,
        },
        "quality": {
            "duplicate_evidence_id_count": 0,
            "early_visibility_count": 0,
            "cross_cik_contamination_count": 0,
            "period_class_mixing_failure_count": 0,
            "source_hash_mismatch_count": 0,
            "fake_source_hash_count": 0,
            "source_unavailable_fake_evidence_count": 0,
        },
        "replay": {
            "reusable_accession_count": 36204,
            "reprocessed_accession_count": 0,
            "network_bytes": 0,
            "status": "PASS",
        },
        "storage": {
            "cache_ceiling_breach_count": 0,
            "transient_assets_evicted": True,
            "persistent_storage_budget_status": "PASS",
            "full_sec_submission_mirror_retained": False,
        },
        "dvc_seal_status": "PASS",
        "output_hash_match": "YES",
        "identities": {
            "build_spec_identity_match": "YES",
            "execution_inventory_identity_match": "YES",
            "source_unavailable_ledger_identity_match": "YES",
        },
        "qlib_full_historical_handoff": "PASS",
        "artifacts": {
            "fundamentals": {
                "path": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        },
    }


def _nested_handoff(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    root = tmp_path / "synthetic-build-root"
    root.mkdir()
    handoff = _terminal(root)
    locations = {
        "bindings": "selective/bindings.parquet",
        "session_grid": "terminal-finalization/projection/episode-session-grid.parquet",
        "base_surface": "evidence/base-surface.parquet",
        "fundamentals_projection": "terminal-finalization/projection/fundamentals-wide.parquet",
    }
    handoff["artifact_root_relative_to_handoff"] = "../.."
    handoff["downstream_paths"] = locations
    handoff["evaluation_config"] = {}
    for name, relative in locations.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"synthetic-{name}".encode())
        handoff["artifacts"][name] = {
            "path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    for relative in ("standardized-events/events.jsonl", "source-manifests/source.json"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    location = root / "terminal-finalization/handoff/p5-historical-build-handoff-v1.json"
    _write(location, handoff)
    return root, location, handoff


def test_nested_handoff_resolves_verified_cross_subdirectory_artifacts(tmp_path: Path) -> None:
    root, location, handoff = _nested_handoff(tmp_path)
    assert resolve_handoff_artifact_root(location, handoff) == root.resolve()
    assert verify_terminal_handoff(handoff, artifact_root=root)["gate_count"] == 26
    assert {Path(row["path"]).parts[0] for row in handoff["artifacts"].values()} >= {
        "evidence", "selective", "terminal-finalization",
    }


@pytest.mark.parametrize("case", ("artifact_escape", "root_escape", "symlink_escape", "missing_root", "hash", "absolute"))
def test_nested_handoff_paths_fail_closed(tmp_path: Path, case: str) -> None:
    root, location, handoff = _nested_handoff(tmp_path)
    outside = tmp_path / "outside.parquet"
    outside.write_bytes(b"external")
    if case == "artifact_escape":
        handoff["artifacts"]["base_surface"]["path"] = "../outside.parquet"
    elif case == "root_escape":
        handoff["artifact_root_relative_to_handoff"] = "../../.."
    elif case == "symlink_escape":
        link = root / "evidence/escaped.parquet"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("symlink creation is unavailable")
        handoff["artifacts"]["base_surface"]["path"] = "evidence/escaped.parquet"
    elif case == "missing_root":
        handoff["artifact_root_relative_to_handoff"] = "../missing"
    elif case == "hash":
        (root / handoff["downstream_paths"]["base_surface"]).write_bytes(b"corrupt")
    else:
        handoff["artifacts"]["base_surface"]["path"] = str(outside)
    with pytest.raises((ValueError, FileNotFoundError, TerminalCloseoutError)):
        verified_root = resolve_handoff_artifact_root(location, handoff)
        verify_terminal_handoff(handoff, artifact_root=verified_root)


def test_explicit_pandera_runtime_is_probed_and_launched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import run_p5_downstream as consumer

    root, location, _handoff = _nested_handoff(tmp_path)
    config = tmp_path / "runtime.json"
    _write(config, {"pandera_python": sys.executable})
    identity = verify_runtime_config(config)
    assert identity["pandera"] == "0.33.1"
    assert all(identity[key] for key in ("configured_executable", "executable", "pandas", "pyarrow"))
    selected = []
    monkeypatch.setattr(consumer, "_stage", lambda *_args, **_kwargs: None)
    def stop_after_compose(python: str, *_args: object) -> None:
        selected.append(python)
        raise subprocess.CalledProcessError(1, python)
    monkeypatch.setattr(consumer, "_native_stage", stop_after_compose)
    result = run_real(location, config, tmp_path / "downstream")
    assert result["status"] == "BLOCKED_QLIB_EVALUATION"
    assert selected == [str(Path(sys.executable).resolve())]
    assert root.exists()


def test_pandera_runtime_absent_or_version_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "runtime.json"
    _write(config, {"pandera_python": str(tmp_path / "missing-python")})
    with pytest.raises(ValueError, match="absent"):
        verify_runtime_config(config)
    _write(config, {"pandera_python": sys.executable})
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_k: subprocess.CompletedProcess(
        [], 0, '{"executable":"python","pandera":"0.32.0","pandas":"2.3.3","pyarrow":"25.0.1"}', ""))
    with pytest.raises(ValueError, match="version"):
        verify_runtime_config(config)


def _dates() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(
        list(pd.bdate_range("2019-10-01", periods=24))
        + list(pd.bdate_range("2021-10-01", periods=12))
        + list(pd.bdate_range("2023-01-03", periods=60))
    )


def _fixture(root: Path) -> dict[str, Path]:
    episodes = tuple(f"EP-{number:02d}" for number in range(49)) + ("EP-X",)
    ciks = {
        episode: (None if episode == "EP-X" else f"{number + 1:010d}")
        for number, episode in enumerate(episodes)
    }
    rows = []
    rng = np.random.default_rng(20260920)
    for day_number, day in enumerate(_dates()):
        for episode_number, episode in enumerate(episodes):
            fundamental_signal = float((episode_number % 9) - 4)
            filing_signal = float(((day_number * 37 + episode_number * 17) % 23) - 11)
            row = {
                "datetime": day,
                "episode_id": episode,
                "cik": ciks[episode],
                "identity_exclusion": episode == "EP-X",
                "label": 0.0,
            }
            for feature in CONTROL_FEATURES:
                row[feature] = float(rng.normal())
            row["label"] = 100.0 * row[CONTROL_FEATURES[0]] + fundamental_signal + 2.0 * filing_signal
            rows.append(row)
    base = pd.DataFrame(rows).sort_values(["datetime", "episode_id"]).reset_index(drop=True)
    fundamentals = base.loc[~base["identity_exclusion"], ["datetime", "episode_id", "cik"]].copy()
    for number, feature in enumerate(FUNDAMENTAL_FEATURES):
        episode_number = fundamentals["episode_id"].str[-2:].astype(int)
        fundamentals[feature] = ((episode_number % 9) - 4) * (number + 1.0)
    fundamentals.loc[fundamentals.index[::11], "Revenue"] = np.nan
    observations = []
    for episode_number, episode in enumerate(episodes[:-1]):
        for day_number, event_day in enumerate(_dates()):
            filing_signal = int((day_number * 37 + episode_number * 17) % 23)
            values = (filing_signal, episode_number % 2, 0, 0, filing_signal)
            for feature, value in zip(FILING_FEATURES, values):
                missing = "VALIDATED_ABSENCE" if feature == FILING_FEATURES[3] else None
                native_type = "CurrentReport"
                if episode_number == day_number == 0 and feature == FILING_FEATURES[3]:
                    value, missing, native_type = None, "NATIVE_OBJECT_UNAVAILABLE", None
                observations.append(FilingFeatureObservationV1.admit(
                    schema_version="FilingFeatureObservationV1", feature_id=feature,
                    source_accession=f"{int(ciks[episode]):010d}-24-{day_number + 1:06d}",
                    cik=ciks[episode], form="8-K",
                    sec_acceptance_datetime=datetime.combine(event_day.date(), time(20), timezone.utc),
                    first_available_xnys_session=event_day.date(),
                    native_edgartools_object_type=native_type, exact_scalar_value=value,
                    missingness_status=missing, amendment_status="ORIGINAL",
                    source_availability_status="AVAILABLE", edgartools_runtime_identity="edgartools==5.58.0",
                ))
    paths = {
        "base": root / "base.parquet",
        "fundamentals": root / "fundamentals.parquet",
        "filing": root / "filing-history" / "filing-session-projection.parquet",
        "ledger": root / "filing-history" / "filing-provenance-ledger.parquet",
    }
    base.to_parquet(paths["base"], index=False)
    fundamentals.to_parquet(paths["fundamentals"], index=False)
    bindings = pd.DataFrame({
        "episode_id": episodes[:-1], "cik": [ciks[item] for item in episodes[:-1]],
        "valid_from": _dates().min(), "valid_to": _dates().max(),
    })
    seal_historical_filing_features(
        observations,
        session_grid=base[["datetime", "episode_id", "cik"]],
        bindings=bindings,
        output_root=root / "filing-history",
    )
    return paths


def _compose(root: Path, paths: dict[str, Path], *, expect_pass: bool) -> Path:
    spec = {f"{name}_path": str(path) for name, path in paths.items()}
    spec["filing_ledger_path"] = spec.pop("ledger_path")
    spec["fundamentals_path"] = spec.pop("fundamentals_path")
    spec["base_path"] = spec.pop("base_path")
    spec["filing_path"] = spec.pop("filing_path")
    spec_path = root / "compose.json"
    _write(spec_path, spec)
    output = root / "surfaces"
    command = [
        PANDERA_PYTHON, str(SCRIPT), "_stage", "--stage", "compose",
        "--input", str(spec_path), "--root", str(output),
        "--output", str(root / "surfaces.json"), "--repo", str(REPO),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    assert (completed.returncode == 0) is expect_pass, completed.stderr
    return output


def _bundle(surfaces: dict[str, dict[str, object]]) -> dict[str, object]:
    runs = {
        name: {
            "recorder_status": "FINISHED",
            "recorder_id": f"run-{name}",
            "surface_artifact_identity": surfaces[name]["artifact_identity"],
            "native_rank_ic": {
                "producer": "qlib.workflow.record_temp.SigAnaRecord",
                "recorder_artifact_path": "sig_analysis/ric.pkl",
                "portable_evidence_sha256": f"rank-{name}",
            },
        }
        for name in surfaces
    }
    arch = {
        "interface_status": "PASS", "policy": P5_ARCH,
        "results": {
            "forward": {"spa_consistent_pvalue": 0.01,
                        "reality_check_consistent_pvalue": 0.01},
            "reverse": {"spa_consistent_pvalue": 0.8,
                        "reality_check_consistent_pvalue": 0.8},
        },
    }
    comparisons = {
        "H1": {
            "control_surface": "S0", "challenger_surface": "S1",
            "s1_artifact_identity": surfaces["S1"]["artifact_identity"],
            "skfolio_status": "PASS", "skfolio": P5_SKFOLIO, "arch": copy.deepcopy(arch),
            "native_rank_ic_evidence": {"producer": "qlib.workflow.record_temp.SigAnaRecord",
                                        "challenger_minus_control_mean": 0.01},
            "required_robustness_evidence": {"hard_gate_status": "NOT_REQUIRED"},
            "required_cost_evidence": {"hard_gate_status": "NOT_REQUIRED"},
            "arch_statistic_identity": "NEGATIVE_NATIVE_QLIB_NET_DAILY_RETURN",
            "evidence_complete": True, "comparable": True,
        },
        "H2": {
            "control_surface": "S1", "challenger_surface": "S2",
            "s1_artifact_identity": surfaces["S1"]["artifact_identity"],
            "skfolio_status": "PASS", "skfolio": P5_SKFOLIO, "arch": copy.deepcopy(arch),
            "native_rank_ic_evidence": {"producer": "qlib.workflow.record_temp.SigAnaRecord",
                                        "challenger_minus_control_mean": 0.01},
            "required_robustness_evidence": {"hard_gate_status": "NOT_REQUIRED"},
            "required_cost_evidence": {"hard_gate_status": "NOT_REQUIRED"},
            "arch_statistic_identity": "NEGATIVE_NATIVE_QLIB_NET_DAILY_RETURN",
            "evidence_complete": True, "comparable": True,
        },
    }
    return {
        "surfaces": surfaces,
        "qlib_runs": runs,
        "comparisons": comparisons,
        "leakage_gates": {name: 0 for name in LEAKAGE_GATES},
    }


def _policy_bundle() -> dict[str, object]:
    return _bundle({name: {"artifact_identity": f"artifact-{name}"}
                    for name in ("S0", "S1", "S2")})


def test_native_discovery_uses_injected_edgartools_surface() -> None:
    class Filing:
        form = "10-K"
        cik = 1
        accession_no = "0000000001-24-000001"
        acceptance_datetime = datetime(2024, 3, 1, 20, tzinfo=timezone.utc)
        period_of_report = datetime(2023, 12, 31).date()

    calls = []

    class Company:
        def __init__(self, cik: int) -> None:
            calls.append(cik)

        def get_filings(self, **kwargs: object) -> list[Filing]:
            assert kwargs == {
                "filing_date": "2024-01-01:2024-12-31",
                "amendments": True,
                "trigger_full_load": True,
            }
            return [Filing()]

    observations = discover_native_filing_observations(
        ["1", "0000000001"], filing_date="2024-01-01:2024-12-31",
        calendar=xcals.get_calendar("XNYS"), company_factory=Company,
    )
    assert calls == [1]
    assert len(observations) == 5
    assert {item.source_accession for item in observations} == {Filing.accession_no}


def test_terminal_closeout_pass_and_four_failure_classes(tmp_path: Path) -> None:
    handoff = _terminal(tmp_path)
    assert verify_terminal_handoff(handoff, artifact_root=tmp_path)["gate_count"] == 26
    mutations = (
        ("global_accession_count", 1),
        ("quality", {**handoff["quality"], "cross_cik_contamination_count": 1}),
        ("dvc_seal_status", "FAIL"),
        ("qlib_full_historical_handoff", "FAIL"),
    )
    for key, value in mutations:
        changed = copy.deepcopy(handoff)
        changed[key] = value
        with pytest.raises(TerminalCloseoutError):
            verify_terminal_handoff(changed, artifact_root=tmp_path)
    changed = copy.deepcopy(handoff)
    changed["artifacts"]["fundamentals"]["sha256"] = "0" * 64
    with pytest.raises(TerminalCloseoutError, match="SHA-256"):
        verify_terminal_handoff(changed, artifact_root=tmp_path)


def test_surface_composition_and_six_negative_contracts(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    output = _compose(tmp_path, paths, expect_pass=True)
    manifests = {name: _read(output / name.lower() / "manifest.json") for name in ("S0", "S1", "S2")}
    assert [manifests[name]["column_count"] for name in ("S0", "S1", "S2")] == [157, 168, 173]

    negative_mutators = []
    negative_mutators.append(lambda frame: pd.concat([frame, frame.iloc[[0]]], ignore_index=True))
    negative_mutators.append(lambda frame: frame[[*frame.columns[:5], frame.columns[6], frame.columns[5], *frame.columns[7:]]])
    for number, mutate in enumerate(negative_mutators):
        case = tmp_path / f"base-neg-{number}"
        case.mkdir()
        bad = mutate(pd.read_parquet(paths["base"]))
        case_paths = dict(paths)
        case_paths["base"] = case / "base.parquet"
        bad.to_parquet(case_paths["base"], index=False)
        _compose(case, case_paths, expect_pass=False)

    case = tmp_path / "unexpected-s1"
    case.mkdir()
    bad = pd.read_parquet(paths["fundamentals"])
    bad["unexpected"] = 1.0
    case_paths = dict(paths)
    case_paths["fundamentals"] = case / "fundamentals.parquet"
    bad.to_parquet(case_paths["fundamentals"], index=False)
    _compose(case, case_paths, expect_pass=False)

    for name, change in (
        ("null-to-zero", lambda x: x.assign(value=x["value"].fillna(0))),
        ("early", lambda x: x.assign(datetime=pd.to_datetime(x["datetime"]) - pd.Timedelta(days=1))),
    ):
        case = tmp_path / name
        case.mkdir()
        bad = change(pd.read_parquet(paths["ledger"]))
        case_paths = dict(paths)
        case_paths["ledger"] = case / "ledger.parquet"
        bad.to_parquet(case_paths["ledger"], index=False)
        _compose(case, case_paths, expect_pass=False)

    case = tmp_path / "current-ticker"
    case.mkdir()
    bad = pd.read_parquet(paths["filing"]).rename(columns={"episode_id": "ticker"})
    case_paths = dict(paths)
    case_paths["filing"] = case / "filing.parquet"
    bad.to_parquet(case_paths["filing"], index=False)
    _compose(case, case_paths, expect_pass=False)

    case = tmp_path / "cross-cik"
    case.mkdir()
    bad = pd.read_parquet(paths["filing"])
    bad.loc[0, "cik"] = "0000000999"
    case_paths = dict(paths)
    case_paths["filing"] = case / "filing.parquet"
    bad.to_parquet(case_paths["filing"], index=False)
    _compose(case, case_paths, expect_pass=False)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_bundle_four_negative_contracts_and_final_policy(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    _compose(tmp_path, paths, expect_pass=True)
    surfaces = _read(tmp_path / "surfaces.json")
    bundle = _bundle(surfaces)
    assert verify_evidence_bundle(bundle)["status"] == "PASS"
    policy = evaluate_final_policy(bundle)
    assert policy["status"] == "COMPLETE"
    assert policy["p5_h1_result"] == policy["p5_h2_result"] == "INCREMENTAL_VALUE_SUPPORTED"

    changed = copy.deepcopy(bundle)
    changed["qlib_runs"]["S0"].pop("recorder_id")
    with pytest.raises(ValueError, match="Recorder"):
        verify_evidence_bundle(changed)
    changed = copy.deepcopy(bundle)
    changed["comparisons"]["H2"]["s1_artifact_identity"] = "wrong"
    with pytest.raises(ValueError, match="same frozen S1"):
        verify_evidence_bundle(changed)
    changed = copy.deepcopy(bundle)
    changed["leakage_gates"][LEAKAGE_GATES[0]] = 1
    with pytest.raises(ValueError, match="leakage"):
        verify_evidence_bundle(changed)
    changed = copy.deepcopy(bundle)
    changed["comparisons"]["H1"]["arch"] = {}
    with pytest.raises(ValueError, match="arch"):
        verify_evidence_bundle(changed)


@pytest.mark.parametrize(
    ("h1", "h2", "complete"),
    (
        ("supported", "supported", True),
        ("supported", "none", True),
        ("none", "degraded", True),
        ("degraded", "supported", True),
        ("inconclusive", "supported", False),
        ("supported", "inconclusive", False),
    ),
)
def test_final_phase_policy_matrix(
    tmp_path: Path, h1: str, h2: str, complete: bool,
) -> None:
    del tmp_path
    bundle = _policy_bundle()

    def set_case(name: str, case: str) -> None:
        evidence = bundle["comparisons"][name]
        if case == "none":
            evidence["arch"]["results"]["forward"] = {
                "spa_consistent_pvalue": 0.2, "reality_check_consistent_pvalue": 0.2}
        elif case == "degraded":
            evidence["native_rank_ic_evidence"]["challenger_minus_control_mean"] = -0.01
            evidence["arch"]["results"]["forward"] = {
                "spa_consistent_pvalue": 0.8, "reality_check_consistent_pvalue": 0.8}
            evidence["arch"]["results"]["reverse"] = {
                "spa_consistent_pvalue": 0.01, "reality_check_consistent_pvalue": 0.01}
        elif case == "inconclusive":
            evidence["evidence_complete"] = False

    set_case("H1", h1)
    set_case("H2", h2)
    result = evaluate_final_policy(bundle)
    assert result["p5_phase_complete"] is complete
    assert result["p5_exit_condition_satisfied"] is complete


def test_statistical_policy_failure_modes(tmp_path: Path) -> None:
    del tmp_path
    base = _policy_bundle()["comparisons"]["H1"]
    for key in ("spa_consistent_pvalue", "reality_check_consistent_pvalue"):
        case = copy.deepcopy(base)
        case["arch"]["results"]["forward"][key] = 0.051
        assert classify_comparison(case) == "NO_MEASURABLE_INCREMENTAL_VALUE"
    case = copy.deepcopy(base)
    case["arch"]["results"]["forward"].pop("spa_consistent_pvalue")
    assert classify_comparison(case) == "INCONCLUSIVE"
    case = copy.deepcopy(base)
    case["native_rank_ic_evidence"]["challenger_minus_control_mean"] = 0.0
    assert classify_comparison(case) == "NO_MEASURABLE_INCREMENTAL_VALUE"


def test_native_qlib_three_surface_interface(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    surfaces = _compose(tmp_path, paths, expect_pass=True)
    for name in ("s0", "s1", "s2"):
        command = [
            QLIB_PYTHON, str(SCRIPT), "_stage", "--stage", "qlib",
            "--input", str(surfaces / name), "--root", str(tmp_path / "qlib" / name),
            "--output", str(tmp_path / "qlib" / name / "stage-result.json"),
            "--repo", str(REPO),
        ]
        subprocess.run(command, check=True)
        report = _read(tmp_path / "qlib" / name / "run.json")
        assert report["recorder_status"] == "FINISHED"
        assert report["signal_record"] == report["sigana_record"] == "PASS"
    surface_manifests = _read(tmp_path / "surfaces.json")
    comparison_spec = {
        "surfaces": surface_manifests,
        "runs": {
            name.upper(): {
                "predictions": str(tmp_path / "qlib" / name / "predictions.parquet"),
                "native_rank_ic_path": str(tmp_path / "qlib" / name / "native-rank-ic.parquet"),
                "native_rank_ic": _read(tmp_path / "qlib" / name / "run.json")["native_rank_ic"],
                "recorder_id": _read(tmp_path / "qlib" / name / "run.json")["recorder_id"],
                "portana_record_interface": "READY_NOT_EXECUTED_SYNTHETIC",
            }
            for name in ("s0", "s1", "s2")
        },
    }
    _write(tmp_path / "comparison-spec.json", comparison_spec)
    subprocess.run(
        [
            sys.executable, str(SCRIPT), "_stage", "--stage", "compare",
            "--input", str(tmp_path / "comparison-spec.json"),
            "--root", str(tmp_path / "comparisons"),
            "--output", str(tmp_path / "comparisons.json"), "--repo", str(REPO),
        ],
        check=True,
    )
    comparisons = _read(tmp_path / "comparisons.json")
    for name in ("H1", "H2"):
        evidence = tmp_path / "comparisons" / name.lower() / "upstream-interface-evidence.csv"
        frame = pd.read_csv(evidence)
        pd.concat([frame] * 10, ignore_index=True).to_csv(evidence, index=False, lineterminator="\n")
        comparisons[name]["evidence_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
        skfolio = tmp_path / "robustness" / name.lower() / "skfolio"
        arch = tmp_path / "robustness" / name.lower() / "arch"
        subprocess.run(
            [
                "/mnt/d/AQ_ENVS/skfolio/Scripts/python.exe",
                _win(REPO / "40-certification-system/upstream-stack-integration/skfolio_probe.py"),
                "--input", _win(evidence), "--output", _win(skfolio), "--p5-authority",
            ],
            check=True,
        )
        subprocess.run(
            [
                "/mnt/d/AQ_ENVS/arch/Scripts/python.exe",
                _win(REPO / "40-certification-system/upstream-stack-integration/arch_probe.py"),
                "--input", _win(evidence), "--output", _win(arch), "--spa-reality-only",
                "--p5-confirmatory",
            ],
            check=True,
        )
        comparisons[name]["skfolio_status"] = "PASS"
        comparisons[name]["skfolio"] = _read(skfolio / "skfolio-report.json")
        comparisons[name]["required_robustness_evidence"] = {
            "hard_gate_status": "NOT_REQUIRED"}
        comparisons[name]["arch"] = _read(arch / "arch-report.json")
    bundle = {
        "surfaces": surface_manifests,
        "qlib_runs": {
            name.upper(): _read(tmp_path / "qlib" / name / "run.json")
            for name in ("s0", "s1", "s2")
        },
        "comparisons": comparisons,
        "leakage_gates": {name: 0 for name in LEAKAGE_GATES},
    }
    assert verify_evidence_bundle(bundle)["status"] == "PASS"
    assert evaluate_final_policy(bundle)["status"] == "INCONCLUSIVE"
