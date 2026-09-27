"""Bounded one-shot runner for the frozen P7 successor research protocol.

``preflight`` is synthetic and never opens real prediction or label values.
``real-execute`` is intentionally unreachable until a separately reviewed,
tracked provenance seal exists and every authority check passes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TASK = "AUTONOMOUS-QUANT-P7-SUCCESSOR-ONE-SHOT-EXECUTION-001"
PROTOCOL_SHA256 = "cb61628ed49ca0f9d9798f92567adedbeb533f6854da098ec3c945b38bdbd76a"
INPUT_CONTRACT_SHA256 = "b9e0c447794c318d7ddc00803e0f2ea5468abc4c77a43752ead2910804b8a7b5"
SIGNAL_CONSTRUCTION_POPULATION_SHA256 = (
    "2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e"
)
EVALUATION_POPULATION_SHA256 = (
    "50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0"
)
LABEL_MASK_SHA256 = "2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf"
QLIB_SOURCE_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"

PROTOCOL = Path(
    "30-research-system/qlib/p7-native-ensemble/"
    "successor-historical-static-ensemble-research-protocol.json"
)
INPUT_CONTRACT = Path(
    "30-research-system/qlib/p7-native-ensemble/"
    "successor-label-observable-input-contract.json"
)
PROVENANCE_SEAL = Path(
    "30-research-system/qlib/p7-native-ensemble/"
    "successor-one-shot-execution-provenance-seal.json"
)
EXECUTION_SCRIPT = Path(
    "30-research-system/qlib/p7-native-ensemble/"
    "execute_successor_historical_static_research.py"
)
OUTPUT_ROOT = Path(
    "/mnt/d/AQ_DATA/P7/"
    "successor-historical-static-ensemble-research-execution-001"
)
RFC8785_PYTHON = Path("/home/zhou/AQ_ENVS/p5-fundamental-intelligence/bin/python")
STATS_PYTHON = Path("/home/zhou/AQ_ENVS/p5-h1-statistics/bin/python")
QLIB_SOURCE_ROOT = Path("/home/zhou/AQ_WORKSPACES/p0-poc-b-qlib-src")
EXPECTED_DEPENDENCIES = {"arch": "8.0.0", "qlib": "0.9.8.dev26", "skfolio": "1.0.6"}


class GateError(RuntimeError):
    """A fail-closed authority or one-shot state-machine rejection."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        self.code = code
        super().__init__(code if detail is None else f"{code}: {detail}")


@dataclass(frozen=True)
class Authorities:
    protocol: dict[str, Any]
    input_contract: dict[str, Any]


@dataclass(frozen=True)
class RuntimeAuthority:
    current_head: str
    origin_main_head: str
    worktree_clean: bool
    seal_last_change_commit: str
    seal_worktree_git_equivalent_to_head: bool
    execution_commit_on_current_head: bool
    execution_commit_on_origin_main: bool
    execution_commit_script_sha256: str
    current_head_script_sha256: str
    worktree_script_git_equivalent_to_head: bool
    raw_worktree_script_sha256: str
    dependency_versions: dict[str, str]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GateError("JSON_OBJECT_REQUIRED", str(path))
    return value


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def write_json(path: Path, value: Any, *, replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise GateError("IMMUTABLE_ARTIFACT_ALREADY_EXISTS", str(path))
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(json_safe(value), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def rfc8785_sha256(path: Path) -> str:
    code = (
        "import hashlib,json,rfc8785,sys;"
        "value=json.load(open(sys.argv[1],encoding='utf-8'));"
        "print(hashlib.sha256(rfc8785.dumps(value)).hexdigest())"
    )
    return subprocess.check_output(
        [str(RFC8785_PYTHON), "-c", code, str(path)], text=True
    ).strip()


def load_authorities(repo: Path) -> Authorities:
    protocol_path = repo / PROTOCOL
    contract_path = repo / INPUT_CONTRACT
    if rfc8785_sha256(protocol_path) != PROTOCOL_SHA256:
        raise GateError("PROTOCOL_IDENTITY_MISMATCH")
    if rfc8785_sha256(contract_path) != INPUT_CONTRACT_SHA256:
        raise GateError("INPUT_CONTRACT_IDENTITY_MISMATCH")
    protocol = read_json(protocol_path)
    contract = read_json(contract_path)
    frozen = protocol["input_contract"]
    construction = contract["signal_construction_population"]
    evaluation = contract["evaluation_population"]
    checks = {
        "protocol input contract": (
            frozen["successor_input_contract_sha256"],
            INPUT_CONTRACT_SHA256,
        ),
        "protocol construction population": (
            frozen["signal_construction_population_index_sha256"],
            SIGNAL_CONSTRUCTION_POPULATION_SHA256,
        ),
        "protocol evaluation population": (
            frozen["evaluation_population_index_sha256"],
            EVALUATION_POPULATION_SHA256,
        ),
        "protocol label mask": (frozen["label_validity_mask_sha256"], LABEL_MASK_SHA256),
        "contract construction population": (
            construction["ordered_index_sha256"],
            SIGNAL_CONSTRUCTION_POPULATION_SHA256,
        ),
        "contract evaluation population": (
            evaluation["ordered_index_sha256"], EVALUATION_POPULATION_SHA256
        ),
        "contract label mask": (
            contract["label_validity_mask"]["semantic_sha256"],
            LABEL_MASK_SHA256,
        ),
        "Candidate count": (contract["candidate_snapshot"]["candidate_count"], 17),
        "construction row count": (construction["row_count"], 374591),
        "evaluation row count": (evaluation["row_count"], 374477),
        "evaluation session count": (evaluation["session_count"], 751),
        "evaluation instrument count": (evaluation["instrument_count"], 547),
    }
    for label, (actual, expected) in checks.items():
        if actual != expected:
            raise GateError("FROZEN_AUTHORITY_MISMATCH", label)
    if protocol["protocol_status"] != "FROZEN_PRE_EXECUTION_CODE_REBASE_REQUIRED":
        raise GateError("PROTOCOL_STATUS_MISMATCH")
    return Authorities(protocol=protocol, input_contract=contract)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def synthetic_qlib_preflight(repo: Path, authorities: Authorities) -> dict[str, Any]:
    import qlib
    from qlib.backtest import backtest_loop
    from qlib.contrib.eva.alpha import calc_ic
    from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

    if qlib.__version__ != EXPECTED_DEPENDENCIES["qlib"]:
        raise GateError("QLIB_VERSION_MISMATCH", qlib.__version__)
    source_sha = subprocess.check_output(
        ["git", "-C", str(QLIB_SOURCE_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if source_sha != QLIB_SOURCE_SHA:
        raise GateError("QLIB_SOURCE_IDENTITY_MISMATCH", source_sha)
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    index = pd.MultiIndex.from_product(
        [dates, ["A", "B", "C"]], names=["datetime", "instrument"]
    )
    frames = {
        "one": pd.DataFrame(
            {"score": [1.0, 2.0, 3.0, 3.0, 2.0, 1.0]}, index=index
        ),
        "two": pd.DataFrame(
            {"score": [2.0, 1.0, 3.0, 1.0, 3.0, 2.0]}, index=index
        ),
    }
    router = load_module(
        repo / "30-research-system/qlib/p7-native-ensemble/session_local_router.py",
        "p7_successor_synthetic_router",
    )
    combined, qualification = router.combine_session_local_nonconstant(frames)
    label = pd.Series([1.0, 2.0, 3.0, 3.0, 2.0, 1.0], index=index, name="label")
    _, rank_ic = calc_ic(combined["score"], label, dropna=False)
    if len(combined) != 6 or len(rank_ic) != 2 or not np.isfinite(rank_ic).all():
        raise GateError("SYNTHETIC_QLIB_VALUE_PATH_FAILED")
    if qualification["active_component_count"].tolist() != [2, 2]:
        raise GateError("SYNTHETIC_SESSION_ROUTER_FAILED")
    portfolio = authorities.protocol["portfolio_projection"]
    strategy = TopkDropoutStrategy(
        signal=combined["score"], topk=portfolio["topk"], n_drop=portfolio["n_drop"]
    )
    if strategy is None or not callable(backtest_loop):
        raise GateError("SYNTHETIC_QLIB_PORTFOLIO_PATH_FAILED")
    return {
        "qlib_version": qlib.__version__,
        "qlib_source_sha": source_sha,
        "synthetic_qlib_ensemble": "PASS",
        "synthetic_qlib_rankic": "PASS",
        "synthetic_qlib_portfolio_path": "PASS",
    }


def synthetic_statistics_preflight(authorities: Authorities) -> dict[str, Any]:
    payload = {
        "cpcv": authorities.protocol["temporal_robustness"]["cpcv"],
        "mcs": authorities.protocol["component_family_diagnostics"]["procedure_parameters"],
        "session_count": authorities.protocol["input_contract"]["session_count"],
        "spa": authorities.protocol["primary_endpoint"]["inference"]["procedure_parameters"],
        "walkforward": authorities.protocol["temporal_robustness"]["walkforward"],
    }
    code = r'''import json,sys,numpy as np,arch,skfolio
from arch.bootstrap import MCS,SPA
from skfolio.model_selection import WalkForward,CombinatorialPurgedCV
p=json.loads(sys.argv[1]); r=np.random.default_rng(20260913)
x=r.normal(size=p['session_count'])
w=p['walkforward']; c=p['cpcv']; s=p['spa']; m=p['mcs']
wf=list(WalkForward(test_size=w['test_size'],train_size=w['train_size'],purged_size=w['purged_size'],expand_train=w['expand_train'],reduce_test=w['reduce_test']).split(x))
cp=list(CombinatorialPurgedCV(n_folds=c['n_folds'],n_test_folds=c['n_test_folds'],purged_size=c['purged_size'],embargo_size=c['embargo_size']).split(x))
spa=SPA(-x,-x[:,None],block_size=s['block_size'],reps=s['reps'],bootstrap=s['bootstrap'],studentize=s['studentize'],nested=s['nested'],seed=s['seed']); spa.compute()
mcs=MCS(r.normal(size=(p['session_count'],18)),size=m['size'],reps=m['reps'],block_size=m['block_size'],method=m['method'],bootstrap=m['bootstrap'],seed=m['seed']); mcs.compute()
assert list(spa.pvalues.index)==['lower','consistent','upper']
print(json.dumps({'arch_version':arch.__version__,'skfolio_version':skfolio.__version__,'spa_keys':list(spa.pvalues.index),'mcs_column_count':18,'walkforward_count':len(wf),'cpcv_count':len(cp)}))'''
    report = json.loads(
        subprocess.check_output(
            [str(STATS_PYTHON), "-c", code, json.dumps(payload, sort_keys=True)],
            text=True,
        )
    )
    expected = {
        "arch_version": EXPECTED_DEPENDENCIES["arch"],
        "skfolio_version": EXPECTED_DEPENDENCIES["skfolio"],
        "spa_keys": ["lower", "consistent", "upper"],
        "mcs_column_count": 18,
        "walkforward_count": 3,
        "cpcv_count": 45,
    }
    if report != expected:
        raise GateError("SYNTHETIC_STATISTICS_PREFLIGHT_FAILED", repr(report))
    return report


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def commit_is_ancestor(repo: Path, commit: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, descendant],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def git_blob_sha256(repo: Path, commit: str, path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{path.as_posix()}"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise GateError("EXECUTION_COMMIT_SCRIPT_MISSING")
    return hashlib.sha256(result.stdout).hexdigest()


def git_blob_oid(repo: Path, commit: str, path: Path) -> str:
    return git(repo, "rev-parse", f"{commit}:{path.as_posix()}")


def worktree_filtered_blob_oid(repo: Path, path: Path) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "hash-object",
            f"--path={path.as_posix()}",
            str((repo / path).resolve()),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GateError("WORKTREE_TRACKED_TEXT_HASH_FAILED", path.as_posix())
    return result.stdout.strip()


def worktree_git_equivalent_to_head(repo: Path, path: Path) -> bool:
    if not (repo / path).is_file():
        return False
    try:
        head_oid = git_blob_oid(repo, "HEAD", path)
    except subprocess.CalledProcessError:
        return False
    return worktree_filtered_blob_oid(repo, path) == head_oid


def runtime_authority(
    repo: Path,
    seal: Mapping[str, Any],
) -> RuntimeAuthority:
    import qlib

    head = git(repo, "rev-parse", "HEAD")
    origin_main = git(repo, "rev-parse", "origin/main")
    execution_commit = str(seal.get("execution_code_commit_sha", ""))
    stats_versions = json.loads(
        subprocess.check_output(
            [
                str(STATS_PYTHON),
                "-c",
                "import json,arch,skfolio;print(json.dumps({'arch':arch.__version__,'skfolio':skfolio.__version__}))",
            ],
            text=True,
        )
    )
    versions = {"qlib": qlib.__version__, **stats_versions}
    qlib_source = subprocess.check_output(
        ["git", "-C", str(QLIB_SOURCE_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if qlib_source != QLIB_SOURCE_SHA:
        raise GateError("QLIB_SOURCE_IDENTITY_MISMATCH", qlib_source)
    return RuntimeAuthority(
        current_head=head,
        origin_main_head=origin_main,
        worktree_clean=not bool(git(repo, "status", "--porcelain", "--untracked-files=all")),
        seal_last_change_commit=git(
            repo, "log", "-1", "--format=%H", "--", PROVENANCE_SEAL.as_posix()
        ),
        seal_worktree_git_equivalent_to_head=worktree_git_equivalent_to_head(
            repo, PROVENANCE_SEAL
        ),
        execution_commit_on_current_head=commit_is_ancestor(
            repo, execution_commit, head
        ),
        execution_commit_on_origin_main=commit_is_ancestor(
            repo, execution_commit, "origin/main"
        ),
        execution_commit_script_sha256=git_blob_sha256(
            repo, execution_commit, EXECUTION_SCRIPT
        ),
        current_head_script_sha256=git_blob_sha256(repo, "HEAD", EXECUTION_SCRIPT),
        worktree_script_git_equivalent_to_head=worktree_git_equivalent_to_head(
            repo, EXECUTION_SCRIPT
        ),
        raw_worktree_script_sha256=file_sha256(repo / EXECUTION_SCRIPT),
        dependency_versions=versions,
    )


def load_provenance_seal(repo: Path) -> dict[str, Any]:
    path = repo / PROVENANCE_SEAL
    if not path.is_file():
        raise GateError("EXECUTION_PROVENANCE_SEAL_MISSING")
    tracked = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "ls-files",
            "--error-unmatch",
            PROVENANCE_SEAL.as_posix(),
        ],
        check=False,
        capture_output=True,
    )
    if tracked.returncode != 0:
        raise GateError("EXECUTION_PROVENANCE_SEAL_NOT_TRACKED")
    return read_json(path)


def validate_provenance_seal(
    authorities: Authorities,
    seal: Mapping[str, Any],
    runtime: RuntimeAuthority,
) -> None:
    if "authority_commit_sha" in seal:
        raise GateError("SELF_REFERENTIAL_AUTHORITY_COMMIT_FORBIDDEN")
    sealed_dependencies = seal.get("expected_dependency_versions")
    comparisons = (
        ("PROTOCOL_MISMATCH", seal.get("successor_protocol_sha256"), PROTOCOL_SHA256),
        (
            "INPUT_CONTRACT_MISMATCH",
            seal.get("successor_input_contract_sha256"),
            INPUT_CONTRACT_SHA256,
        ),
        (
            "SIGNAL_CONSTRUCTION_POPULATION_MISMATCH",
            seal.get("signal_construction_population_index_sha256"),
            SIGNAL_CONSTRUCTION_POPULATION_SHA256,
        ),
        (
            "EVALUATION_POPULATION_MISMATCH",
            seal.get("evaluation_population_index_sha256"),
            EVALUATION_POPULATION_SHA256,
        ),
        ("LABEL_MASK_MISMATCH", seal.get("label_validity_mask_sha256"), LABEL_MASK_SHA256),
        ("QLIB_SOURCE_MISMATCH", seal.get("qlib_source_sha"), QLIB_SOURCE_SHA),
        (
            "SEALED_DEPENDENCY_AUTHORITY_MISMATCH",
            sealed_dependencies,
            EXPECTED_DEPENDENCIES,
        ),
        (
            "RUNTIME_DEPENDENCY_VERSION_MISMATCH",
            runtime.dependency_versions,
            sealed_dependencies,
        ),
        (
            "EXECUTION_COMMIT_SCRIPT_HASH_MISMATCH",
            runtime.execution_commit_script_sha256,
            seal.get("execution_script_sha256"),
        ),
        (
            "CURRENT_HEAD_SCRIPT_HASH_MISMATCH",
            runtime.current_head_script_sha256,
            seal.get("execution_script_sha256"),
        ),
    )
    for code, actual, expected in comparisons:
        if actual != expected:
            raise GateError(code)
    if runtime.current_head != runtime.origin_main_head:
        raise GateError("HEAD_NOT_EXACT_ORIGIN_MAIN")
    if runtime.seal_last_change_commit != runtime.current_head:
        raise GateError("SEAL_LAST_CHANGE_NOT_CURRENT_HEAD")
    if not runtime.seal_worktree_git_equivalent_to_head:
        raise GateError("SEAL_WORKTREE_HEAD_MISMATCH")
    if not runtime.worktree_script_git_equivalent_to_head:
        raise GateError("WORKTREE_SCRIPT_HEAD_MISMATCH")
    if not runtime.worktree_clean:
        raise GateError("DIRTY_WORKTREE_FORBIDDEN")
    if not runtime.execution_commit_on_current_head:
        raise GateError("EXECUTION_COMMIT_NOT_ANCESTOR_OF_CURRENT_HEAD")
    if not runtime.execution_commit_on_origin_main:
        raise GateError("EXECUTION_COMMIT_NOT_ON_ORIGIN_MAIN")
    _validate_artifact_authority(authorities, seal)


def _validate_artifact_authority(
    authorities: Authorities, seal: Mapping[str, Any]
) -> None:
    artifacts = seal.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise GateError("ARTIFACT_AUTHORITY_MISSING")
    candidates = artifacts.get("candidates")
    if not isinstance(candidates, list):
        raise GateError("CANDIDATE_ARTIFACT_AUTHORITY_MISSING")
    expected = {
        item["slot"]: item["source_prediction_sha256"]
        for item in authorities.input_contract["candidate_snapshot"]["bindings"]
    }
    actual = {item.get("slot"): item.get("sha256") for item in candidates}
    if actual != expected:
        raise GateError("CANDIDATE_ARTIFACT_BINDING_MISMATCH")
    control = artifacts.get("control", {})
    label = artifacts.get("label", {})
    construction_population = artifacts.get("signal_construction_population", {})
    evaluation_population = artifacts.get("evaluation_population", {})
    contract = authorities.input_contract
    if control.get("sha256") != contract["control"]["source_prediction_sha256"]:
        raise GateError("CONTROL_ARTIFACT_BINDING_MISMATCH")
    if label.get("sha256") != contract["label_authority"]["label_artifact_sha256"]:
        raise GateError("LABEL_ARTIFACT_BINDING_MISMATCH")
    construction_byte_sha = construction_population.get("sha256")
    if (
        not isinstance(construction_byte_sha, str)
        or len(construction_byte_sha) != 64
        or any(character not in "0123456789abcdef" for character in construction_byte_sha)
    ):
        raise GateError("SIGNAL_CONSTRUCTION_POPULATION_ARTIFACT_BINDING_MISSING")
    if (
        evaluation_population.get("sha256")
        != contract["evaluation_population"]["artifact_byte_sha256"]
    ):
        raise GateError("EVALUATION_POPULATION_ARTIFACT_BINDING_MISMATCH")


def verify_artifact_files(seal: Mapping[str, Any]) -> None:
    artifacts = seal["artifacts"]
    items = list(artifacts["candidates"]) + [
        artifacts["control"],
        artifacts["label"],
        artifacts["signal_construction_population"],
        artifacts["evaluation_population"],
    ]
    for item in items:
        path = Path(item["path"])
        if not path.is_file() or file_sha256(path) != item["sha256"]:
            raise GateError("ARTIFACT_FILE_IDENTITY_MISMATCH", str(path))


def pre_outcome_manifest(
    seal: Mapping[str, Any], runtime: RuntimeAuthority
) -> dict[str, Any]:
    artifacts = seal["artifacts"]
    return {
        "task": TASK,
        "state": "PRE_OUTCOME_PREFLIGHT",
        "created_at_utc": utc_now(),
        "protocol_sha256": PROTOCOL_SHA256,
        "input_contract_sha256": INPUT_CONTRACT_SHA256,
        "signal_construction_population_index_sha256": (
            SIGNAL_CONSTRUCTION_POPULATION_SHA256
        ),
        "evaluation_population_index_sha256": EVALUATION_POPULATION_SHA256,
        "label_validity_mask_sha256": LABEL_MASK_SHA256,
        "candidate_artifact_hashes": {
            item["slot"]: item["sha256"] for item in artifacts["candidates"]
        },
        "ols_artifact_hash": artifacts["control"]["sha256"],
        "label_artifact_hash": artifacts["label"]["sha256"],
        "signal_construction_population_artifact_hash": artifacts[
            "signal_construction_population"
        ]["sha256"],
        "evaluation_population_artifact_hash": artifacts["evaluation_population"][
            "sha256"
        ],
        "qlib_source_sha": QLIB_SOURCE_SHA,
        "dependency_versions": runtime.dependency_versions,
        "execution_commit_sha": seal["execution_code_commit_sha"],
        "execution_script_sha256": runtime.current_head_script_sha256,
        "raw_worktree_script_sha256_diagnostic": (
            runtime.raw_worktree_script_sha256
        ),
        "seal_last_change_commit": runtime.seal_last_change_commit,
        "current_head": runtime.current_head,
        "clean_worktree": runtime.worktree_clean,
        "real_outcome_access_started": False,
    }


def begin_one_shot(output: Path, manifest: dict[str, Any]) -> None:
    if output.exists():
        if (output / "outcome-access-started.json").exists():
            raise GateError("SECOND_REAL_EXECUTION_FORBIDDEN")
        raise GateError("OUTCOME_ROOT_ALREADY_EXISTS")
    output.mkdir(parents=True)
    write_json(output / "attempt-manifest.json", manifest)
    write_json(
        output / "outcome-access-started.json",
        {
            "state": "OUTCOME_ACCESS_STARTED",
            "started_at_utc": utc_now(),
            "real_outcome_access_started": True,
            "real_outcome_execution_attempt_count": 1,
            "protocol_sha256": PROTOCOL_SHA256,
        },
    )


def seal_post_marker_failure(output: Path, exc: BaseException) -> None:
    write_json(
        output / "failure.json",
        {
            "state": "FAILED_SEALED_INCONCLUSIVE",
            "failed_at_utc": utc_now(),
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "traceback": traceback.format_exc(),
        },
    )
    write_json(
        output / "final-result.json",
        {
            "state": "FAILED_SEALED_INCONCLUSIVE",
            "result_classification": "STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE",
            "reason": "POST_MARKER_REQUIRED_METHOD_OR_INTEGRITY_FAILURE",
            "real_outcome_access_started": True,
            "real_outcome_execution_attempt_count": 1,
        },
    )
    seal_checksums(output)


def seal_checksums(output: Path) -> None:
    files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name != "checksums.json"
    )
    write_json(
        output / "checksums.json",
        {str(path.relative_to(output)).replace("\\", "/"): file_sha256(path) for path in files},
        replace=True,
    )


def run_one_shot(
    output: Path,
    manifest: dict[str, Any],
    runner: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    begin_one_shot(output, manifest)
    try:
        result = runner()
        result.update(
            state="COMPLETED",
            real_outcome_access_started=True,
            real_outcome_execution_attempt_count=1,
        )
        write_json(output / "final-result.json", result)
        seal_checksums(output)
        return result
    except BaseException as exc:
        seal_post_marker_failure(output, exc)
        raise


def ordered_index_sha256(index: pd.MultiIndex) -> str:
    hashed = pd.util.hash_pandas_object(index, index=True).to_numpy().tobytes()
    return hashlib.sha256(hashed).hexdigest()


def load_population(
    path: Path, specification: Mapping[str, Any], name: str
) -> pd.MultiIndex:
    frame = pd.read_parquet(path, columns=["datetime", "instrument"])
    frame["datetime"] = pd.to_datetime(frame["datetime"])
    index = pd.MultiIndex.from_frame(frame, names=["datetime", "instrument"])
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise GateError(f"{name}_POPULATION_ORDER_INVALID")
    if ordered_index_sha256(index) != specification["ordered_index_sha256"]:
        raise GateError(f"{name}_POPULATION_SEMANTIC_IDENTITY_MISMATCH")
    dimensions = (
        len(index),
        index.get_level_values("datetime").nunique(),
        index.get_level_values("instrument").nunique(),
    )
    expected_dimensions = [specification["row_count"]]
    if "session_count" in specification:
        expected_dimensions.append(specification["session_count"])
    if "instrument_count" in specification:
        expected_dimensions.append(specification["instrument_count"])
    if tuple(expected_dimensions) != dimensions[: len(expected_dimensions)]:
        raise GateError(f"{name}_POPULATION_DIMENSION_MISMATCH")
    return index


def normalize_score(value: Any, name: str, population: pd.MultiIndex) -> pd.DataFrame:
    if isinstance(value, pd.Series):
        value = value.rename("score").to_frame()
    if not isinstance(value, pd.DataFrame) or value.shape[1] != 1:
        raise GateError("PREDICTION_SHAPE_INVALID", name)
    frame = value.rename(columns={value.columns[0]: "score"})
    if frame.index.has_duplicates or not population.isin(frame.index).all():
        raise GateError("PREDICTION_POPULATION_COVERAGE_INVALID", name)
    frame = frame.loc[population]
    values = frame["score"].to_numpy(dtype=float, copy=False)
    if not frame.index.equals(population) or not np.isfinite(values).all():
        raise GateError("PREDICTION_POPULATION_PROJECTION_INVALID", name)
    return frame


def project_score(
    frame: pd.DataFrame, name: str, population: pd.MultiIndex
) -> pd.DataFrame:
    if frame.index.has_duplicates or not population.isin(frame.index).all():
        raise GateError("PREDICTION_EVALUATION_COVERAGE_INVALID", name)
    projected = frame.loc[population]
    if not projected.index.equals(population) or not np.isfinite(
        projected["score"].to_numpy(dtype=float, copy=False)
    ).all():
        raise GateError("PREDICTION_EVALUATION_PROJECTION_INVALID", name)
    return projected


def normalize_label(value: Any, population: pd.MultiIndex) -> pd.Series:
    if isinstance(value, pd.DataFrame):
        if value.shape[1] != 1:
            raise GateError("LABEL_SHAPE_INVALID")
        value = value.iloc[:, 0]
    if not isinstance(value, pd.Series):
        raise GateError("LABEL_SHAPE_INVALID")
    if value.index.has_duplicates or not population.isin(value.index).all():
        raise GateError("LABEL_SUCCESSOR_COVERAGE_INVALID")
    label = value.loc[population].rename("label")
    if not label.index.equals(population) or not np.isfinite(
        label.to_numpy(dtype=float, copy=False)
    ).all():
        raise GateError("LABEL_SUCCESSOR_FINITE_GATE_FAILED")
    return label


def rank_ic(prediction: pd.Series, label: pd.Series, *, required: bool) -> pd.Series:
    from qlib.contrib.eva.alpha import calc_ic

    _, result = calc_ic(prediction, label, dropna=False)
    if required and (len(result) != 751 or result.isna().any()):
        raise GateError("RANKIC_REQUIRED_SESSION_INVALID")
    return result


def summarize_component_rank_ic(values: pd.Series) -> dict[str, float | int | None]:
    finite = values[np.isfinite(values.to_numpy(dtype=float, copy=False))]
    if finite.empty:
        return {
            "finite_valid_session_count": 0,
            "mean_over_finite_sessions": None,
            "median_over_finite_sessions": None,
            "positive_fraction_over_finite_sessions": None,
        }
    return {
        "finite_valid_session_count": int(len(finite)),
        "mean_over_finite_sessions": float(finite.mean()),
        "median_over_finite_sessions": float(finite.median()),
        "positive_fraction_over_finite_sessions": float((finite > 0).mean()),
    }


def primary_statistics(
    frame_path: Path, protocol: dict[str, Any], output: Path
) -> dict[str, Any]:
    payload_path = output / "statistics-protocol.json"
    write_json(
        payload_path,
        {
            "classification": protocol["classification"],
            "primary": protocol["primary_endpoint"],
            "temporal": protocol["temporal_robustness"],
        },
    )
    destination = output / "statistics-result.json"
    code = r'''import json,sys,numpy as np,pandas as pd,arch,skfolio
from arch.bootstrap import SPA
from skfolio.model_selection import WalkForward,CombinatorialPurgedCV
frame=pd.read_pickle(sys.argv[1]); p=json.load(open(sys.argv[2])); t=p['temporal']; primary=p['primary']
delta=frame['ENSEMBLE_MINUS_OLS']; w=t['walkforward']; c=t['cpcv']
wf=list(WalkForward(test_size=w['test_size'],train_size=w['train_size'],purged_size=w['purged_size'],expand_train=w['expand_train'],reduce_test=w['reduce_test']).split(frame.to_numpy()))
cp=list(CombinatorialPurgedCV(n_folds=c['n_folds'],n_test_folds=c['n_test_folds'],purged_size=c['purged_size'],embargo_size=c['embargo_size']).split(frame.to_numpy()))
wv=[float(delta.iloc[test].mean()) for _,test in wf]; cv=[float(delta.iloc[np.sort(np.concatenate(groups))].mean()) for _,groups in cp]
s=primary['inference']['procedure_parameters']; spa=SPA(-frame['OLS_ALPHA158_CONTROL'],-frame[['STATIC_17_ENSEMBLE']],block_size=s['block_size'],reps=s['reps'],bootstrap=s['bootstrap'],studentize=s['studentize'],nested=s['nested'],seed=s['seed']); spa.compute()
result={'arch_version':arch.__version__,'skfolio_version':skfolio.__version__,'spa':{k:float(spa.pvalues.loc[k]) for k in ('lower','consistent','upper')},'walkforward':{'fold_count':len(wv),'positive_fraction':float(np.mean(np.array(wv)>0)),'median_mean_delta':float(np.median(wv))},'cpcv':{'split_count':len(cv),'positive_fraction':float(np.mean(np.array(cv)>0)),'median_mean_delta':float(np.median(cv))}}
open(sys.argv[3],'w').write(json.dumps(result,indent=2,sort_keys=True)+'\n')'''
    subprocess.run(
        [str(STATS_PYTHON), "-c", code, str(frame_path), str(payload_path), str(destination)],
        check=True,
    )
    return read_json(destination)


def mcs_result(
    component_daily: pd.DataFrame,
    ensemble_daily: pd.Series,
    protocol: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    loss_frame = pd.concat(
        {"STATIC_17_ENSEMBLE": ensemble_daily, **component_daily.to_dict("series")},
        axis=1,
    )
    if not np.isfinite(loss_frame.to_numpy(dtype=float, copy=False)).all():
        return {
            "status": "NOT_AVAILABLE_SECONDARY_INCOMPLETE_LOSS_MATRIX",
            "primary_classification_effect": "NONE",
        }
    input_path = output / "mcs-input.pkl"
    output_path = output / "mcs-result.json"
    loss_frame.to_pickle(input_path)
    parameters = protocol["component_family_diagnostics"]["procedure_parameters"]
    code = r'''import json,sys,pandas as pd
from arch.bootstrap import MCS
frame=pd.read_pickle(sys.argv[1]); p=json.loads(sys.argv[2])
mcs=MCS(-frame,size=p['size'],reps=p['reps'],block_size=p['block_size'],method=p['method'],bootstrap=p['bootstrap'],seed=p['seed']); mcs.compute()
print(json.dumps({'status':'PASS','included_models':[str(x) for x in mcs.included],'excluded_models':[str(x) for x in mcs.excluded],'primary_classification_effect':'NONE'}))'''
    try:
        report = json.loads(
            subprocess.check_output(
                [str(STATS_PYTHON), "-c", code, str(input_path), json.dumps(parameters)],
                text=True,
            )
        )
    except BaseException as exc:
        report = {
            "status": "FAILED_SECONDARY",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "primary_classification_effect": "NONE",
        }
    write_json(output_path, report)
    return report


def run_mcs_secondary(
    component_daily: pd.DataFrame,
    ensemble_daily: pd.Series,
    protocol: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    try:
        return mcs_result(component_daily, ensemble_daily, protocol, output)
    except BaseException as exc:
        return {
            "status": "FAILED_SECONDARY",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "primary_classification_effect": "NONE",
        }


def classify(protocol: Mapping[str, Any], mean_delta: float, stats: Mapping[str, Any]) -> tuple[str, dict[str, bool]]:
    pvalue_rule = protocol["primary_endpoint"]["inference"][
        "consistent_pvalue_gate"
    ]
    prefix = "LESS_THAN_OR_EQUAL_TO_"
    if not pvalue_rule.startswith(prefix):
        raise GateError("CLASSIFICATION_PROTOCOL_UNSUPPORTED")
    pvalue_limit = float(pvalue_rule.removeprefix(prefix).replace("_", "."))
    values = {
        "FULL_PERIOD_MEAN_DAILY_RANK_IC_DELTA_GREATER_THAN_ZERO": mean_delta > 0,
        "ARCH_SPA_CONSISTENT_PVALUE_LESS_THAN_OR_EQUAL_TO_0_05": stats["spa"]["consistent"] <= pvalue_limit,
        "WALKFORWARD_POSITIVE_FOLD_FRACTION_GREATER_THAN_OR_EQUAL_TO_0_6": stats["walkforward"]["positive_fraction"] >= protocol["temporal_robustness"]["walkforward"]["positive_fold_fraction_minimum"],
        "WALKFORWARD_MEDIAN_FOLD_MEAN_DELTA_GREATER_THAN_ZERO": stats["walkforward"]["median_mean_delta"] > 0,
        "CPCV_POSITIVE_SPLIT_FRACTION_GREATER_THAN_OR_EQUAL_TO_0_6": stats["cpcv"]["positive_fraction"] >= protocol["temporal_robustness"]["cpcv"]["positive_split_fraction_minimum"],
        "CPCV_MEDIAN_SPLIT_MEAN_DELTA_GREATER_THAN_ZERO": stats["cpcv"]["median_mean_delta"] > 0,
    }
    required = protocol["classification"]["supportive_when_all"]
    if set(required) != set(values):
        raise GateError("CLASSIFICATION_PROTOCOL_UNSUPPORTED")
    gates = {name: values[name] for name in required}
    result = (
        "STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE"
        if all(gates.values())
        else "STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE"
    )
    if result not in protocol["classification"]["result_classifications"]:
        raise GateError("CLASSIFICATION_VOCABULARY_MISMATCH")
    return result, gates


def record_lineage(
    output: Path,
    classification: str,
    mean_delta: float,
    authorities: Authorities,
) -> str:
    import mlflow

    tracking = output / "mlflow" / "mlflow.db"
    tracking.parent.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri("sqlite:///" + str(tracking))
    mlflow.set_experiment("p7_successor_historical_static_ensemble_research")
    with mlflow.start_run(run_name="frozen-successor-static-17-vs-ols") as run:
        mlflow.log_params(
            {
                "protocol_sha256": PROTOCOL_SHA256,
                "input_contract_sha256": INPUT_CONTRACT_SHA256,
                "signal_construction_population_index_sha256": (
                    SIGNAL_CONSTRUCTION_POPULATION_SHA256
                ),
                "evaluation_population_index_sha256": EVALUATION_POPULATION_SHA256,
                "candidate_count": authorities.protocol["candidate_snapshot"][
                    "candidate_count"
                ],
                "classification": classification,
            }
        )
        mlflow.log_metric("mean_daily_rank_ic_delta", mean_delta)
        return run.info.run_id


def record_lineage_secondary(
    output: Path,
    classification: str,
    mean_delta: float,
    authorities: Authorities,
) -> dict[str, Any]:
    try:
        return {
            "status": "PASS",
            "run_id": record_lineage(
                output, classification, mean_delta, authorities
            ),
            "primary_classification_effect": "NONE",
        }
    except BaseException as exc:
        return {
            "status": "FAILED_SECONDARY",
            "run_id": None,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "primary_classification_effect": "NONE",
        }


def run_portfolio(
    prediction: pd.Series,
    protocol: Mapping[str, Any],
    seal: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    import qlib
    from qlib.backtest import backtest_loop, get_exchange
    from qlib.backtest.account import Account
    from qlib.backtest.executor import SimulatorExecutor
    from qlib.backtest.utils import CommonInfrastructure
    from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

    qlib.init(
        provider_uri=str(seal["qlib_provider_path"]),
        region="us",
        expression_cache=None,
        dataset_cache=None,
    )
    p = protocol["portfolio_projection"]
    account = Account(init_cash=p["account"], benchmark_config={"benchmark": p["benchmark"]})
    exchange = get_exchange(
        freq="day",
        start_time=p["start"],
        end_time=p["end"],
        codes="all",
        **p["exchange"],
    )
    common = CommonInfrastructure(trade_account=account, trade_exchange=exchange)
    strategy = TopkDropoutStrategy(signal=prediction, topk=p["topk"], n_drop=p["n_drop"])
    executor = SimulatorExecutor(time_per_step="day", generate_portfolio_metrics=True)
    strategy.reset_common_infra(common)
    executor.reset_common_infra(common)
    portfolio_metrics, _ = backtest_loop(p["start"], p["end"], strategy, executor)
    report, positions = portfolio_metrics["1day"]
    report_path = output / "portfolio-report.pkl"
    positions_path = output / "portfolio-positions.pkl"
    report.to_pickle(report_path)
    pd.to_pickle(positions, positions_path)
    return {
        "status": "PASS",
        "executed": True,
        "report_rows": len(report),
        "report_sha256": file_sha256(report_path),
        "positions_sha256": file_sha256(positions_path),
        "classification_role": p["classification_role"],
        "primary_classification_effect": "NONE",
    }


def run_portfolio_secondary(
    prediction: pd.Series,
    protocol: Mapping[str, Any],
    seal: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    try:
        return run_portfolio(prediction, protocol, seal, output)
    except BaseException as exc:
        return {
            "status": "FAILED_SECONDARY",
            "executed": False,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "primary_classification_effect": "NONE",
        }


def construct_then_project_ensemble(
    raw_predictions: Mapping[str, Any],
    construction_population: pd.MultiIndex,
    evaluation_population: pd.MultiIndex,
    router: Any,
) -> tuple[
    pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame
]:
    predictions = {
        name: normalize_score(value, name, construction_population)
        for name, value in raw_predictions.items()
    }
    ensemble, qualification = router.combine_session_local_nonconstant(predictions)
    evaluation_predictions = {
        name: project_score(frame, name, evaluation_population)
        for name, frame in predictions.items()
    }
    evaluation_ensemble = project_score(
        ensemble, "STATIC_17_ENSEMBLE", evaluation_population
    )
    return ensemble, evaluation_ensemble, evaluation_predictions, qualification


def real_outcome_runner(
    repo: Path,
    output: Path,
    authorities: Authorities,
    seal: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = seal["artifacts"]
    contract = authorities.input_contract
    construction_population = load_population(
        Path(artifacts["signal_construction_population"]["path"]),
        contract["signal_construction_population"],
        "SIGNAL_CONSTRUCTION",
    )
    evaluation_population = load_population(
        Path(artifacts["evaluation_population"]["path"]),
        contract["evaluation_population"],
        "EVALUATION",
    )
    if not evaluation_population.isin(construction_population).all():
        raise GateError("EVALUATION_POPULATION_NOT_CONTAINED_IN_CONSTRUCTION")
    raw_predictions = {
        item["slot"]: pd.read_pickle(item["path"])
        for item in artifacts["candidates"]
    }
    control = normalize_score(
        pd.read_pickle(artifacts["control"]["path"]),
        "control",
        evaluation_population,
    )
    label = normalize_label(
        pd.read_pickle(artifacts["label"]["path"]), evaluation_population
    )
    router = load_module(
        repo / "30-research-system/qlib/p7-native-ensemble/session_local_router.py",
        "p7_successor_real_router",
    )
    ensemble, evaluation_ensemble, evaluation_predictions, qualification = (
        construct_then_project_ensemble(
            raw_predictions,
            construction_population,
            evaluation_population,
            router,
        )
    )
    ensemble_path = output / "ensemble-prediction.pkl"
    ensemble.to_pickle(ensemble_path)
    qualification.to_pickle(output / "active-component-qualification.pkl")
    primary_daily = pd.concat(
        {
        "STATIC_17_ENSEMBLE": rank_ic(
            evaluation_ensemble["score"], label, required=True
        ),
        "OLS_ALPHA158_CONTROL": rank_ic(control["score"], label, required=True),
        },
        axis=1,
    )
    primary_daily["ENSEMBLE_MINUS_OLS"] = (
        primary_daily["STATIC_17_ENSEMBLE"]
        - primary_daily["OLS_ALPHA158_CONTROL"]
    )
    primary_columns = [
        "STATIC_17_ENSEMBLE",
        "OLS_ALPHA158_CONTROL",
        "ENSEMBLE_MINUS_OLS",
    ]
    if not np.isfinite(
        primary_daily[primary_columns].to_numpy(dtype=float, copy=False)
    ).all():
        raise GateError("PRIMARY_RANKIC_REQUIRED_SESSION_INVALID")
    primary_daily_path = output / "primary-daily-rank-ic.pkl"
    primary_daily.to_pickle(primary_daily_path)
    stats = primary_statistics(primary_daily_path, authorities.protocol, output)
    mean_delta = float(primary_daily["ENSEMBLE_MINUS_OLS"].mean())
    classification, gates = classify(authorities.protocol, mean_delta, stats)
    primary_classification_locked = True

    bindings = {
        item["slot"]: item["candidate_id"]
        for item in authorities.input_contract["candidate_snapshot"]["bindings"]
    }
    component_columns = list(bindings.values())
    try:
        component_daily = pd.concat(
            {
                bindings[slot]: rank_ic(frame["score"], label, required=False)
                for slot, frame in evaluation_predictions.items()
            },
            axis=1,
        )
        component_summaries: dict[str, Any] = {
            candidate_id: summarize_component_rank_ic(component_daily[candidate_id])
            for candidate_id in component_columns
        }
        component_summary_status = "PASS"
    except BaseException as exc:
        component_summaries = {
            "status": "FAILED_SECONDARY",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
        component_summary_status = "FAILED_SECONDARY"
        component_daily = pd.DataFrame(index=primary_daily.index)
    daily = pd.concat([primary_daily, component_daily], axis=1)
    daily_path = output / "daily-rank-ic.pkl"
    daily.to_pickle(daily_path)
    if component_summary_status == "PASS":
        mcs = run_mcs_secondary(
            component_daily,
            primary_daily["STATIC_17_ENSEMBLE"],
            authorities.protocol,
            output,
        )
    else:
        mcs = {
            "status": "NOT_AVAILABLE_SECONDARY_COMPONENT_RANKIC_FAILURE",
            "primary_classification_effect": "NONE",
        }
    portfolio = run_portfolio_secondary(
        ensemble["score"], authorities.protocol, seal, output
    )
    lineage = record_lineage_secondary(
        output, classification, mean_delta, authorities
    )
    return {
        "task": TASK,
        "result_classification": classification,
        "primary_mean_daily_rank_ic_delta": mean_delta,
        "classification_gates": gates,
        "primary_statistics": stats,
        "primary_classification_locked": primary_classification_locked,
        "component_summary_status": component_summary_status,
        "component_summaries": component_summaries,
        "mcs": mcs,
        "portfolio": portfolio,
        "run_lineage": lineage,
        "ensemble_prediction_sha256": file_sha256(ensemble_path),
        "daily_rank_ic_sha256": file_sha256(daily_path),
        "pristine_oos": False,
        "p2_certification_evidence": False,
        "p7_dynamic_roster_evidence": False,
        "p7_exit_condition_evidence": False,
        "production_authorization": False,
        "p2_v2_sealed_oos_accessed": False,
        "p2_v2_cohort_modified": False,
    }


def preflight(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    authorities = load_authorities(repo)
    report = {
        "state": "PRE_OUTCOME_PREFLIGHT",
        **synthetic_qlib_preflight(repo, authorities),
        **synthetic_statistics_preflight(authorities),
        "real_execution_provenance_seal_present": (repo / PROVENANCE_SEAL).is_file(),
        "real_execution_ready": "NO_PENDING_POST_MERGE_PROVENANCE_SEAL",
        "real_outcome_access_started": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


def real_execute(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    authorities = load_authorities(repo)
    seal = load_provenance_seal(repo)
    runtime = runtime_authority(repo, seal)
    validate_provenance_seal(authorities, seal, runtime)
    verify_artifact_files(seal)
    manifest = pre_outcome_manifest(seal, runtime)
    result = run_one_shot(
        args.output,
        manifest,
        lambda: real_outcome_runner(repo, args.output, authorities, seal),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("mode", choices=("preflight", "real-execute"))
    result.add_argument("--repo", required=True, type=Path)
    result.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    return result


def main() -> None:
    args = parser().parse_args()
    try:
        {"preflight": preflight, "real-execute": real_execute}[args.mode](args)
    except GateError as exc:
        print(json.dumps({"status": "REJECTED", "classification": exc.code}), file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
