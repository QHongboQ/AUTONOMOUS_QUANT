"""One artifact-driven entrypoint for the frozen P5 downstream composition."""
# ruff: noqa: E701
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
LEAKAGE_GATES = tuple("ACCEPTANCE_TIME_LEAKAGE_COUNT REPORT_PERIOD_LEAKAGE_COUNT AMENDMENT_BACKWARD_LEAKAGE_COUNT CROSS_CIK_CONTAMINATION_COUNT EPISODE_MEMBERSHIP_LEAKAGE_COUNT CURRENT_TICKER_LEAKAGE_COUNT SOURCE_UNAVAILABLE_SUBSTITUTION_COUNT FUTURE_FILING_VISIBILITY_COUNT".split())
AUTHORIZED_RESULTS = {"INCREMENTAL_VALUE_SUPPORTED", "NO_MEASURABLE_INCREMENTAL_VALUE", "DEGRADED", "INCONCLUSIVE"}
P5_SKFOLIO = {"walkforward_test_size": 63, "walkforward_train_size": 504, "walkforward_purged_size": 2, "walkforward_expand_train": False, "walkforward_reduce_test": False, "cpcv_n_folds": 10, "cpcv_n_test_folds": 2, "cpcv_purged_size": 2, "cpcv_embargo_size": 2}
P5_ARCH = {"alpha": 0.05, "bootstrap": "stationary", "block_size": 10, "reps": 5000, "seed": 20260913}
WSL_P5_PYTHON = "/home/zhou/AQ_ENVS/p5-fundamental-intelligence/bin/python"
WSL_QLIB_PYTHON = "/home/zhou/miniforge3/envs/rdagent4qlib/bin/python"
def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
def _add_paths(repo: Path) -> None:
    paths = ("10-data-system/fundamentals/historical-dataset", "20-intelligence-system/fundamental-factors/evidence-contract",
             "20-intelligence-system/fundamental-factors/p5-filing-features", "30-research-system/qlib/dataset-adapter")
    for relative in paths:
        sys.path.insert(0, str(repo / relative))
def verify_evidence_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    surfaces = bundle.get("surfaces", {})
    runs = bundle.get("qlib_runs", {})
    if set(surfaces) != {"S0", "S1", "S2"} or set(runs) != {"S0", "S1", "S2"}:
        raise ValueError("three surface and Qlib run identities are required")
    for surface_id in surfaces:
        run = runs[surface_id]
        if run.get("recorder_status") != "FINISHED" or not run.get("recorder_id"): raise ValueError("missing finished Qlib Recorder artifact")
        if run.get("surface_artifact_identity") != surfaces[surface_id].get("artifact_identity"): raise ValueError("Qlib run/surface identity mismatch")
        rank_ic = run.get("native_rank_ic", {})
        if rank_ic.get("producer") != "qlib.workflow.record_temp.SigAnaRecord" or rank_ic.get("recorder_artifact_path") != "sig_analysis/ric.pkl" or not rank_ic.get("portable_evidence_sha256"): raise ValueError("missing Qlib-native Rank IC evidence")
    comparisons = bundle.get("comparisons", {})
    if comparisons.get("H1", {}).get("control_surface") != "S0" or comparisons.get("H1", {}).get("challenger_surface") != "S1":
        raise ValueError("H1 contract mismatch")
    if comparisons.get("H2", {}).get("control_surface") != "S1" or comparisons.get("H2", {}).get("challenger_surface") != "S2":
        raise ValueError("H2 contract mismatch")
    s1_ids = {comparisons[name].get("s1_artifact_identity") for name in ("H1", "H2")}
    if s1_ids != {surfaces["S1"].get("artifact_identity")}:
        raise ValueError("H1/H2 did not reuse the same frozen S1 artifact")
    for name in ("H1", "H2"):
        evidence = comparisons[name]
        skfolio = evidence.get("skfolio", {})
        if evidence.get("skfolio_status") != "PASS" or any(skfolio.get(key) != value for key, value in P5_SKFOLIO.items()): raise ValueError(f"{name} required skfolio evidence is missing")
        arch = evidence.get("arch", {})
        if arch.get("interface_status") != "PASS" or any(arch.get("policy", {}).get(key) != value for key, value in P5_ARCH.items()): raise ValueError(f"{name} required arch evidence is missing")
        for direction in ("forward", "reverse"):
            values = arch.get("results", {}).get(direction, {})
            if not all(isinstance(values.get(key), (int, float)) for key in ("spa_consistent_pvalue", "reality_check_consistent_pvalue")): raise ValueError(f"{name} arch statistical results are missing")
        rank_ic = evidence.get("native_rank_ic_evidence", {})
        if rank_ic.get("producer") != "qlib.workflow.record_temp.SigAnaRecord" or not isinstance(rank_ic.get("challenger_minus_control_mean"), (int, float)): raise ValueError(f"{name} native Rank IC comparison is missing")
        for required in ("required_robustness_evidence", "required_cost_evidence"):
            if required not in evidence: raise ValueError(f"{name} {required} is missing")
    leakage = bundle.get("leakage_gates", {})
    if set(leakage) != set(LEAKAGE_GATES) or any(int(leakage[name]) for name in LEAKAGE_GATES):
        raise ValueError("nonzero or incomplete P5 leakage gates")
    result = {"schema_version": "P5EvidenceBundleValidationV1", "status": "PASS",
              "surface_count": 3, "comparison_count": 2, "leakage_gate_count": 8}
    result["validation_identity"] = _sha(result)
    return result


def classify_comparison(evidence: dict[str, Any]) -> str:
    """Apply only the frozen four-state P5 comparison policy."""
    if not evidence.get("evidence_complete") or not evidence.get("comparable"): return "INCONCLUSIVE"
    if evidence.get("arch_statistic_identity") != "NEGATIVE_NATIVE_QLIB_NET_DAILY_RETURN": return "INCONCLUSIVE"
    rank_ic = evidence.get("native_rank_ic_evidence", {})
    delta = rank_ic.get("challenger_minus_control_mean")
    arch = evidence.get("arch", {}).get("results", {})
    forward, reverse = arch.get("forward", {}), arch.get("reverse", {})
    values = [delta, forward.get("spa_consistent_pvalue"), forward.get("reality_check_consistent_pvalue"), reverse.get("spa_consistent_pvalue"), reverse.get("reality_check_consistent_pvalue")]
    if not all(isinstance(value, (int, float)) for value in values): return "INCONCLUSIVE"
    gates = [evidence.get(name, {}).get("hard_gate_status") for name in ("required_robustness_evidence", "required_cost_evidence")]
    if any(gate == "FAIL_CONTROL_PASSES" for gate in gates): return "DEGRADED"
    if any(gate not in {"PASS", "NOT_REQUIRED"} for gate in gates): return "INCONCLUSIVE"
    alpha = P5_ARCH["alpha"]
    forward_supported = delta > 0 and all(value <= alpha for value in values[1:3])
    reverse_supported = delta < 0 and all(value <= alpha for value in values[3:5])
    if forward_supported: return "INCREMENTAL_VALUE_SUPPORTED"
    if reverse_supported: return "DEGRADED"
    return "NO_MEASURABLE_INCREMENTAL_VALUE"


def evaluate_final_policy(bundle: dict[str, Any]) -> dict[str, Any]:
    """Preserve H1/H2 results and close P5 only when both are conclusive."""
    verify_evidence_bundle(bundle)
    results = {name: classify_comparison(bundle["comparisons"][name]) for name in ("H1", "H2")}
    if not set(results.values()) <= AUTHORIZED_RESULTS:
        raise ValueError("unauthorized P5 comparison result")
    complete = "INCONCLUSIVE" not in results.values()
    states = {"INCREMENTAL_VALUE_SUPPORTED": "ELIGIBLE_FOR_LATER_RESEARCH_COMPOSITION", "INCONCLUSIVE": "NO_PROMOTION_DECISION", "NO_MEASURABLE_INCREMENTAL_VALUE": "NOT_PROMOTED_BY_P5_EVIDENCE", "DEGRADED": "NOT_PROMOTED_BY_P5_EVIDENCE"}
    eligibility = {"exact_11_fundamentals": states[results["H1"]], "exact_5_filing_features": states[results["H2"]]}
    result = {"schema_version": "P5FinalPolicyV1", "status": "COMPLETE" if complete else "INCONCLUSIVE",
              "p5_h1_result": results["H1"], "p5_h2_result": results["H2"],
              "p5_phase_complete": complete, "p5_exit_condition_satisfied": complete,
              "feature_research_eligibility": eligibility,
              "production_authorized": False, "p2_certified": False, "p4_champion": False}
    result["final_policy_identity"] = _sha(result)
    return result
def _internal(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    _add_paths(repo)
    if args.stage == "filing":
        import exchange_calendars as xcals
        import pandas as pd
        from aq_p5_filing_features import discover_native_filing_observations, seal_historical_filing_features
        spec = _read(Path(args.input))
        bindings = pd.read_parquet(spec["bindings_path"])
        sessions = pd.read_parquet(spec["session_grid_path"])
        observations = discover_native_filing_observations(
            bindings["cik"].dropna().astype(str),
            filing_date="1994-01-01:2024-12-31", calendar=xcals.get_calendar("XNYS"))
        result = seal_historical_filing_features(observations, session_grid=sessions,
                                                 bindings=bindings, output_root=Path(args.root))
    elif args.stage == "compose":
        from aq_qlib_handoff.p5_surfaces import compose_surfaces
        spec = _read(Path(args.input))
        result = compose_surfaces(base_path=Path(spec["base_path"]), fundamentals_path=Path(spec["fundamentals_path"]),
            filing_path=Path(spec["filing_path"]), filing_ledger_path=Path(spec["filing_ledger_path"]),
            output_root=Path(args.root))
    elif args.stage == "qlib":
        from aq_qlib_handoff.p5_surfaces import evaluate_surface
        config = _read(Path(args.config)) if args.config else {}
        result = evaluate_surface(Path(args.input), Path(args.root),
            provider_uri=config.get("provider_uri"), benchmark=config.get("benchmark"))
    elif args.stage == "compare":
        import pandas as pd
        spec = _read(Path(args.input))
        result = {}
        for comparison, control, challenger in (("H1", "S0", "S1"), ("H2", "S1", "S2")):
            control_run, challenger_run = spec["runs"][control], spec["runs"][challenger]
            control_rank = pd.read_parquet(control_run["native_rank_ic_path"])
            challenger_rank = pd.read_parquet(challenger_run["native_rank_ic_path"])
            paired_rank = control_rank.merge(challenger_rank, on="datetime", suffixes=("_control", "_challenger"), validate="one_to_one")
            paired_rank = paired_rank.dropna(subset=["rank_ic_control", "rank_ic_challenger"])
            if paired_rank.empty: raise ValueError("paired Qlib-native Rank IC evidence is empty")
            if "daily_net_return" in control_run:
                control_daily, challenger_daily = pd.read_parquet(control_run["daily_net_return"]), pd.read_parquet(challenger_run["daily_net_return"])
                paired_daily = control_daily.merge(challenger_daily, on="date", suffixes=("_control", "_challenger"), validate="one_to_one")
                daily = pd.DataFrame({"score": paired_daily["net_return_challenger"], "label": paired_daily["net_return_control"], "benchmark_loss": -paired_daily["net_return_control"], "model_loss": -paired_daily["net_return_challenger"]})
                statistic, complete = "NEGATIVE_NATIVE_QLIB_NET_DAILY_RETURN", True
            else:
                control_frame, challenger_frame = pd.read_parquet(control_run["predictions"]), pd.read_parquet(challenger_run["predictions"])
                keys = ["datetime", "instrument"]
                paired = control_frame.merge(challenger_frame, on=keys, suffixes=("_control", "_challenger"), validate="one_to_one")
                if not paired["label_control"].equals(paired["label_challenger"]): raise ValueError("paired Qlib labels differ")
                paired["benchmark_loss"] = (paired["label_control"] - paired["score_control"]) ** 2
                paired["model_loss"] = (paired["label_challenger"] - paired["score_challenger"]) ** 2
                daily = paired.groupby("datetime", sort=True).agg(score=("score_challenger", "mean"), label=("label_challenger", "mean"), benchmark_loss=("benchmark_loss", "mean"), model_loss=("model_loss", "mean")).reset_index(drop=True)
                statistic, complete = "SYNTHETIC_PREDICTION_LOSS_INTERFACE_ONLY", False
            directory = Path(args.root) / comparison.lower()
            directory.mkdir(parents=True)
            path = directory / "upstream-interface-evidence.csv"
            daily.to_csv(path, index=False, lineterminator="\n")
            result[comparison] = {
                "control_surface": control, "challenger_surface": challenger,
                "s1_artifact_identity": spec["surfaces"]["S1"]["artifact_identity"],
                "evidence_path": str(path), "evidence_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "arch_statistic_identity": statistic, "evidence_complete": complete, "comparable": True,
                "qlib_recorders": {"control": control_run["recorder_id"], "challenger": challenger_run["recorder_id"]},
                "native_rank_ic_evidence": {
                    "producer": "qlib.workflow.record_temp.SigAnaRecord",
                    "control": control_run["native_rank_ic"], "challenger": challenger_run["native_rank_ic"],
                    "paired_observation_count": len(paired_rank),
                    "challenger_minus_control_mean": float((paired_rank["rank_ic_challenger"] - paired_rank["rank_ic_control"]).mean()),
                },
                "required_cost_evidence": {
                    "control_portana_status": control_run.get("portana_record_interface"), "challenger_portana_status": challenger_run.get("portana_record_interface"), "hard_gate_status": "NOT_REQUIRED"},
            }
    else:
        raise ValueError(args.stage)
    _write(Path(args.output), result)
def _wsl(path: Path) -> str:
    completed = subprocess.run(["wsl.exe", "-d", "Ubuntu-24.04", "--", "wslpath", "-a", str(path.resolve())],
                               check=True, capture_output=True, text=True)
    return completed.stdout.strip()
def _stage(python: str, script: Path, stage: str, input_path: Path, root: Path,
           output: Path, repo: Path, config: Path | None = None) -> None:
    command = [
        "wsl.exe", "-d", "Ubuntu-24.04", "--", python, _wsl(script), "_stage",
        "--stage", stage, "--input", _wsl(input_path), "--root", _wsl(root),
        "--output", _wsl(output), "--repo", _wsl(repo),
    ]
    if config is not None:
        command.extend(["--config", _wsl(config)])
    subprocess.run(command, check=True)
def _native_stage(python: str, script: Path, stage: str, input_path: Path, root: Path, output: Path, repo: Path) -> None:
    subprocess.run([python, str(script), "_stage", "--stage", stage, "--input", str(input_path),
                    "--root", str(root), "--output", str(output), "--repo", str(repo)], check=True)


def resolve_handoff_artifact_root(handoff_path: Path, handoff: dict[str, Any]) -> Path:
    """Resolve only the frozen nested handoff-to-build-root relationship."""
    relation = handoff.get("artifact_root_relative_to_handoff")
    if not isinstance(relation, str) or not relation or Path(relation).is_absolute():
        raise ValueError("handoff artifact-root relationship is absent or absolute")
    parent = handoff_path.parent
    if parent.name != "handoff" or parent.parent.name != "terminal-finalization":
        raise ValueError("handoff is outside the frozen terminal-finalization layout")
    expected = parent.parent.parent.resolve(strict=True)
    root = (parent / relation).resolve(strict=True)
    if root != expected or not root.is_dir() or not handoff_path.resolve(strict=True).is_relative_to(root):
        raise ValueError("declared artifact root escapes the build hierarchy")
    return root


def verify_runtime_config(path: Path) -> dict[str, str]:
    """Validate the explicit operational Pandera interpreter, not data identity."""
    config = _read(path)
    raw = config.get("pandera_python") if isinstance(config, dict) else None
    if not isinstance(raw, str) or not raw:
        raise ValueError("pandera_python must be explicit")
    executable = Path(raw)
    if not executable.is_absolute() or not executable.is_file():
        raise ValueError("configured Pandera executable is absent")
    probe = (
        "import importlib.metadata as m,json,sys; import pandera.pandas; "
        "print(json.dumps({'executable':sys.executable,'pandera':m.version('pandera'),"
        "'pandas':m.version('pandas'),'pyarrow':m.version('pyarrow')}))"
    )
    completed = subprocess.run([str(executable), "-c", probe], check=True, capture_output=True, text=True)
    versions = json.loads(completed.stdout.strip())
    if not isinstance(versions, dict) or versions.get("pandera") != "0.33.1" or not all(versions.get(name) for name in ("executable", "pandas", "pyarrow")):
        raise ValueError("Pandera runtime version or dependency identity mismatch")
    return {"configured_executable": str(executable.resolve()), **versions}


def run_real(handoff_path: Path, runtime_config_path: Path, output_root: Path) -> dict[str, Any]:
    """Run from one sealed handoff; all failures stop at their stage boundary."""
    if not handoff_path.is_file(): return {"status": "WAITING_FOR_INPUT"}
    if output_root.exists(): raise FileExistsError(output_root)
    repo = Path(__file__).resolve().parents[2]
    _add_paths(repo)
    from aq_edgartools_full_build import TerminalCloseoutError, verify_terminal_handoff
    try:
        handoff = _read(handoff_path)
        artifact_root = resolve_handoff_artifact_root(handoff_path, handoff)
        terminal = verify_terminal_handoff(handoff, artifact_root=artifact_root)
        paths = handoff.get("downstream_paths")
        artifacts = handoff.get("artifacts")
        if not isinstance(paths, dict) or not isinstance(artifacts, dict): raise ValueError("downstream artifact identities are absent")
        resolved = {}
        for name in ("bindings", "session_grid", "base_surface", "fundamentals_projection"):
            raw = paths.get(name)
            if not isinstance(artifacts.get(name), dict) or artifacts[name].get("path") != raw:
                raise ValueError(f"{name} is not bound to a verified artifact")
            resolved[name] = artifact_root / raw
    except (FileNotFoundError, KeyError, TypeError, ValueError, AttributeError, TerminalCloseoutError) as exc:
        return {"status": "BLOCKED_INPUT_IDENTITY", "reason": str(exc)}
    try:
        runtime = verify_runtime_config(runtime_config_path)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return {"status": "BLOCKED_RUNTIME_AUTHORITY", "reason": str(exc)}
    output_root.mkdir(parents=True)
    _write(output_root / "terminal-closeout.json", terminal)
    filing_root = output_root / "filing-history"
    filing_spec = {"bindings_path": str(resolved["bindings"]),
                   "session_grid_path": str(resolved["session_grid"])}
    _write(output_root / "filing-spec.json", filing_spec)
    try:
        _stage(WSL_P5_PYTHON, Path(__file__), "filing", output_root / "filing-spec.json", filing_root, output_root / "filing-stage.json", repo)
    except subprocess.CalledProcessError:
        return {"status": "BLOCKED_FILING_MATERIALIZATION"}
    spec = {"base_path": str(resolved["base_surface"]),
        "fundamentals_path": str(resolved["fundamentals_projection"]),
        "filing_path": str(filing_root / "filing-session-projection.parquet"),
        "filing_ledger_path": str(filing_root / "filing-provenance-ledger.parquet")}
    _write(output_root / "composition-spec.json", spec)
    evaluation_config = handoff.get("evaluation_config")
    if not isinstance(evaluation_config, dict): return {"status": "BLOCKED_INPUT_IDENTITY"}
    _write(output_root / "evaluation-config.json", evaluation_config)
    try:
        _native_stage(runtime["configured_executable"], Path(__file__), "compose", output_root / "composition-spec.json", output_root / "surfaces", output_root / "surfaces.json", repo)
        for surface in ("s0", "s1", "s2"):
            _stage(WSL_QLIB_PYTHON, Path(__file__), "qlib", output_root / "surfaces" / surface, output_root / "qlib" / surface, output_root / "qlib" / surface / "stage-result.json", repo, output_root / "evaluation-config.json")
    except subprocess.CalledProcessError:
        return {"status": "BLOCKED_QLIB_EVALUATION"}
    surfaces = _read(output_root / "surfaces.json")
    runs = {name: _read(output_root / "qlib" / name.lower() / "run.json") for name in ("S0", "S1", "S2")}
    comparison_spec = {"surfaces": surfaces, "runs": {name: {
                "predictions": str(output_root / "qlib" / name.lower() / "predictions.parquet"),
                "daily_net_return": str(output_root / "qlib" / name.lower() / "daily-net-return.parquet"),
                "native_rank_ic_path": str(output_root / "qlib" / name.lower() / "native-rank-ic.parquet"),
                "native_rank_ic": runs[name]["native_rank_ic"],
                "recorder_id": runs[name]["recorder_id"],
                "portana_record_interface": runs[name]["portana_record_interface"]}
            for name in runs}}
    _write(output_root / "comparison-spec.json", comparison_spec)
    try:
        _stage(WSL_P5_PYTHON, Path(__file__), "compare", output_root / "comparison-spec.json", output_root / "comparisons", output_root / "comparisons.json", repo)
    except subprocess.CalledProcessError:
        return {"status": "BLOCKED_QLIB_EVALUATION"}
    comparisons = _read(output_root / "comparisons.json")
    for name in ("H1", "H2"):
        evidence = output_root / "comparisons" / name.lower() / "upstream-interface-evidence.csv"
        skfolio_root = output_root / "robustness" / name.lower() / "skfolio"
        arch_root = output_root / "robustness" / name.lower() / "arch"
        try:
            subprocess.run([r"D:\AQ_ENVS\skfolio\Scripts\python.exe", str(repo / "40-certification-system/upstream-stack-integration/skfolio_probe.py"), "--input", str(evidence), "--output", str(skfolio_root), "--p5-authority"], check=True)
            subprocess.run([r"D:\AQ_ENVS\arch\Scripts\python.exe", str(repo / "40-certification-system/upstream-stack-integration/arch_probe.py"), "--input", str(evidence), "--output", str(arch_root), "--spa-reality-only", "--p5-confirmatory"], check=True)
        except subprocess.CalledProcessError:
            return {"status": "INCONCLUSIVE", "reason": "REQUIRED_UPSTREAM_STATISTICAL_EVIDENCE_FAILED"}
        comparisons[name]["skfolio_status"] = "PASS"
        comparisons[name]["skfolio"] = _read(skfolio_root / "skfolio-report.json")
        comparisons[name]["required_robustness_evidence"] = {"skfolio_report_sha256": hashlib.sha256((skfolio_root / "skfolio-report.json").read_bytes()).hexdigest(), "hard_gate_status": "NOT_REQUIRED"}
        comparisons[name]["arch"] = _read(arch_root / "arch-report.json")
    bundle: dict[str, Any] = {"schema_version": "P5EvidenceBundleV1",
        "terminal_closeout": _read(output_root / "terminal-closeout.json"),
        "surfaces": surfaces, "qlib_runs": runs, "comparisons": comparisons,
        "leakage_gates": handoff.get("leakage_gates", {}),
        "source_identities": handoff.get("identities", {}),
        "execution_runtime": runtime}
    try:
        bundle["validation"] = verify_evidence_bundle(bundle)
    except ValueError as exc:
        return {"status": "INCONCLUSIVE", "reason": str(exc)}
    policy = evaluate_final_policy(bundle)
    bundle["phase"] = {"leakage_gates": bundle["leakage_gates"], "p5_h1_result": policy["p5_h1_result"], "p5_h2_result": policy["p5_h2_result"], "p5_phase_complete": policy["p5_phase_complete"], "p5_exit_condition_satisfied": policy["p5_exit_condition_satisfied"]}
    bundle["bundle_identity"] = _sha(bundle)
    policy["evidence_bundle_identity"] = bundle["bundle_identity"]
    policy["final_policy_identity"] = _sha({key: value for key, value in policy.items() if key != "final_policy_identity"})
    _write(output_root / "p5-evidence-bundle.json", bundle)
    _write(output_root / "p5-final-policy.json", policy)
    return policy
def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    real = sub.add_parser("real")
    real.add_argument("--handoff", required=True, type=Path)
    real.add_argument("--runtime-config", required=True, type=Path)
    real.add_argument("--output", required=True, type=Path)
    internal = sub.add_parser("_stage", help=argparse.SUPPRESS)
    internal.add_argument("--stage", required=True, choices=("filing", "compose", "qlib", "compare"))
    internal.add_argument("--input", required=True)
    internal.add_argument("--root", required=True)
    internal.add_argument("--output", required=True)
    internal.add_argument("--repo", required=True)
    internal.add_argument("--config")
    args = parser.parse_args()
    if args.command == "_stage":
        _internal(args)
    else:
        print(json.dumps(run_real(args.handoff, args.runtime_config, args.output), sort_keys=True))
if __name__ == "__main__":
    main()
