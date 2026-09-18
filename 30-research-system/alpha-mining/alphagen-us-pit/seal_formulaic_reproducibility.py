from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


STAGE_NAME = "p3_formulaic_alpha_reproducibility_seal"
ALPHAGEN_SHA = "259687e8f316994426416c530a94842a2fe6405e"
QLIB_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"

DISCOVERY = Path("/mnt/d/AQ_DATA/P3/alphagen-us-pit-factor-discovery-lstsq-run-001")
EVALUATION = Path("/mnt/d/AQ_DATA/P3/alphagen-us-pit-qlib-candidate-evaluation-001")
RUNTIME = Path("/mnt/d/AQ_DATA/P3/formulaic-alpha-dvc-reproducibility-seal-001")
PROVIDER_REPORT = Path("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/reports/build-report.json")
ALPHAGEN_REPOSITORY = Path("/mnt/d/AQ_UPSTREAM/P3/formulaic-alpha/alphagen")
QLIB_REPOSITORY = Path("/home/zhou/AQ_WORKSPACES/p0-poc-b-qlib-src")
REPOSITORY = Path(__file__).resolve().parents[3]

EXPECTED_FILE_HASHES = {
    DISCOVERY / "discovery_summary.json": "5212564ed15b3fa15bde40f14b9fe9a067b725bc5dd472a6046af0013893523a",
    EVALUATION / "frozen_candidate_manifest.json": "de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145",
    EVALUATION / "evaluation_summary.json": "c077196473711ebcbd33e572cb4e3de5a07103dba9e7aa8f88f255a7acf9b6a0",
    EVALUATION / "artifact_manifest_v2.json": "4da1e39480f84c284a7bd7d01bdc921226b4752e1759aff82dbf2d576214e01f",
    PROVIDER_REPORT: "eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142",
    RUNTIME / "runtime_freeze.txt": "1c86d57b148510ccdde19c36edf4c35a8d3915f624bd8d5d2fb65f0ef040fab5",
    RUNTIME / "discovery_pip_freeze.txt": "c31b7313f4d56bd31fd1b8e6fc44bbb7821e25ee0c2794daa8864d9d165730cc",
    RUNTIME / "discovery_conda_explicit.txt": "457d1913d0017cc0c201893bd80fd3c8cee65cd16c19d6f362ea4cf0c80cfa5e",
    RUNTIME / "evaluation_pip_freeze.txt": "dfa33a0e4c6d88da32127c241c1094b278994cf91474e3150d9f7e2903e808b4",
    RUNTIME / "evaluation_conda_explicit.txt": "7a33bfc022c08f118ab463567b108d9ff2b7ecc0bcef582d808ecbc57571cdd7",
    RUNTIME / "runtime_identity.json": "7a8c44e241d9190eee9e0df5ad624ecf205c074dc13003b4d8e4eaa2bad5d898",
    RUNTIME / "runtime_provenance_audit.json": "a3e2d530f5b3e24a8194fa886a8a16977a8fa6b7d27a7cab24211c46ce9967a6",
    RUNTIME / "preseal_authority_check.json": "93d10876b3481b194cfd9571a6961738e79d110c78e119a0bbb2120c39de810b",
    RUNTIME / "dependency_inventory.json": "5d4b07c2875ffe562a547760d46aa79af74c90b34bf24d23b216b3e80b12c97c",
}

EXPECTED_REPOSITORY_HASHES = {
    "30-research-system/alpha-mining/alphagen-us-pit/aq_alphagen_us_pit/data_view.py": "a5b5313a60f847de159ae4c5ac55e4cc429eab62cbc778d92f848aef62361eac",
    "30-research-system/alpha-mining/alphagen-us-pit/aq_alphagen_us_pit/calculator.py": "84d2240046d1fc657429178d0ac2de9838b54a4086fedafec3b0d0598ad0c2e1",
    "30-research-system/alpha-mining/alphagen-us-pit/aq_alphagen_us_pit/feature_mask.py": "f1bafb155e44ae789c8d7900bdb5f6c710e897ffcf80a16f32a48425846a9600",
    "30-research-system/alpha-mining/alphagen-us-pit/aq_alphagen_us_pit/runner.py": "b7b2d813579cf61ca33aef58c48fc85df11a0b42250d4464e3142474d1f68654",
    "30-research-system/alpha-mining/alphagen-us-pit/aq_alphagen_us_pit/research_config.py": "2ba6dd3906f23a1b6a4010db7131fa79f9261fbe1ac2efcfc44e5fc1ea4a36dc",
    "30-research-system/qlib/model-comparison/workflow_config_linear_Alpha158_US.yaml": "865133a279e1cc66c7cc1d7ac20e0977b8f0b5f3ebc5f8fdfe90017186ec38f0",
    "40-certification-system/protocol/p2-certification-protocol-v1.json": "0fc22f259b27499f6d2d344767b179a5fa2c4c55daf15bb593ba0c9001e2289d",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"hash mismatch for {path}: {actual} != {expected}")


def git_head(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aq-head", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if git_head(REPOSITORY) != args.aq_head:
        raise RuntimeError("AQ repository HEAD no longer matches the authorized seal head")
    if git_head(ALPHAGEN_REPOSITORY) != ALPHAGEN_SHA:
        raise RuntimeError("AlphaGen source identity mismatch")
    if git_head(QLIB_REPOSITORY) != QLIB_SHA:
        raise RuntimeError("Qlib source identity mismatch")

    for path, expected in EXPECTED_FILE_HASHES.items():
        require_hash(path, expected)
    for relative, expected in EXPECTED_REPOSITORY_HASHES.items():
        require_hash(REPOSITORY / relative, expected)

    frozen_manifest = json.loads((EVALUATION / "frozen_candidate_manifest.json").read_text(encoding="utf-8"))
    candidates = frozen_manifest["candidates"]
    if frozen_manifest["candidate_count"] != 17 or len(candidates) != 17:
        raise RuntimeError("frozen candidate count is not 17")

    run_configs = []
    recorders = []
    predictions = []
    for number in range(1, 18):
        candidate_id = f"candidate-{number:03d}"
        candidate_root = EVALUATION / candidate_id
        run_config = candidate_root / "run_config.json"
        recorder_path = candidate_root / "qlib_recorder_identity.json"
        prediction_path = candidate_root / "prediction_identity.json"

        run_payload = json.loads(run_config.read_text(encoding="utf-8"))
        recorder = json.loads(recorder_path.read_text(encoding="utf-8"))
        prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
        if run_payload["candidate_id"] != candidate_id:
            raise RuntimeError(f"run config candidate mismatch: {candidate_id}")
        if recorder["status"] != "FINISHED" or recorder["recorder_name"] != candidate_id:
            raise RuntimeError(f"recorder is not FINISHED: {candidate_id}")

        durable_prediction = Path(prediction["artifact_path"])
        require_hash(durable_prediction, prediction["artifact_sha256"])
        run_configs.append({"candidate_id": candidate_id, "sha256": sha256(run_config)})
        recorders.append(
            {
                "candidate_id": candidate_id,
                "experiment_id": str(recorder["experiment_id"]),
                "run_id": recorder["recorder_id"],
                "status": recorder["status"],
            }
        )
        predictions.append(
            {
                "candidate_id": candidate_id,
                "artifact_sha256": prediction["artifact_sha256"],
            }
        )

    seal = {
        "seal_version": "P3_FORMULAIC_ALPHA_REPRODUCIBILITY_SEAL_V1",
        "stage_name": STAGE_NAME,
        "aq_repository_head": args.aq_head,
        "source_identity": {
            "alphagen_git_sha": ALPHAGEN_SHA,
            "qlib_git_sha": QLIB_SHA,
        },
        "runtime_freeze_hashes": {
            path.name: expected
            for path, expected in EXPECTED_FILE_HASHES.items()
            if path.parent == RUNTIME
        },
        "provider_build_report_sha256": EXPECTED_FILE_HASHES[PROVIDER_REPORT],
        "discovery_summary_sha256": EXPECTED_FILE_HASHES[DISCOVERY / "discovery_summary.json"],
        "frozen_candidate_manifest_sha256": EXPECTED_FILE_HASHES[
            EVALUATION / "frozen_candidate_manifest.json"
        ],
        "evaluation_summary_sha256": EXPECTED_FILE_HASHES[EVALUATION / "evaluation_summary.json"],
        "artifact_manifest_sha256": EXPECTED_FILE_HASHES[EVALUATION / "artifact_manifest_v2.json"],
        "candidate_count": 17,
        "finished_recorder_count": len(recorders),
        "prediction_artifact_count": len(predictions),
        "qlib_native_rendered_config": "ABSENT_NOT_FABRICATED",
        "qlib_execution_config_authority": "DETERMINISTIC_RUN_CONFIG_JSON",
        "qlib_execution_config_identities": run_configs,
        "qlib_recorder_identities": recorders,
        "prediction_artifact_identities": predictions,
        "historical_research_test_accessed": True,
        "historical_research_test_status": "CONSUMED_AS_RESEARCH_EVIDENCE",
        "sealed_oos_accessed": False,
        "serialized_model_artifact": "ABSENT_UPSTREAM_EXECUTION_DID_NOT_PERSIST",
        "current_p2_protocol_eligibility": "INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION",
    }
    rendered = json.dumps(seal, indent=2, sort_keys=True, allow_nan=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    os.replace(temporary, args.output)


if __name__ == "__main__":
    main()
