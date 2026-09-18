"""Validate and seal the bounded Formulaic Alpha P2 Protocol V2 freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SEAL_VERSION = "P2FormulaicAlphaProtocolV2FreezeSealV1"
PROTOCOL_VERSION = "P2_CERTIFICATION_PROTOCOL_V2"
COHORT_VERSION = "P2_FORMULAIC_ALPHA_CERTIFICATION_COHORT_V2"
EXPECTED_V1_PROTOCOL_SHA256 = (
    "a9aed881c229f9eb7f85fa23b866168a55dc9c00be3c3b178d91a4af20451dfb"
)
EXPECTED_MATERIALIZATION_SHA256 = (
    "511ef7c25e55afc9cded8d6b2f13ed2715d248705c8cbad71918802d5210b8fd"
)
EXPECTED_VALIDATION_SHA256 = (
    "efbbfd90d5068ddb49a787a08e3f8b5f9da526ae7b22fc326e976adf033473db"
)
EXPECTED_DISCOVERY_MANIFEST_SHA256 = (
    "de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145"
)
EXPECTED_FORMULAIC_SEAL_SHA256 = (
    "60e5d0b271fa6e5a074f329a752ea5d80abfe2a1cb49dd89d1ed33609052fecb"
)
EXPECTED_FORMULAIC_STAGE_IDENTITY = (
    "sha256:659b1ae448be57c915d5f096fa3b112afef0232f69739fb4eaa7ab267c301df1"
)
EXPECTED_PROVIDER_REPORT_SHA256 = (
    "eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142"
)
EXPECTED_CONTROL_CONFIG_SHA256 = (
    "b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1"
)
EXPECTED_STRATEGY_CONFIG_SHA256 = (
    "b96e88cedb0755f36facc0afbc51e38970217582631c2585c645dcbaf7462588"
)
FORBIDDEN_COHORT_KEYS = {
    "annualized_return",
    "historical_test_metrics",
    "ic",
    "information_ratio",
    "pnl",
    "rank_ic",
    "returns",
    "sharpe",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.resolve(strict=True).read_bytes()).hexdigest()


def canonical_text_sha256(path: Path) -> str:
    text = path.resolve(strict=True).read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.resolve(strict=True).read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(collect_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(collect_keys(item) for item in value))
    return set()


def deterministic_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_and_build_seal(
    *,
    protocol_path: Path,
    cohort_path: Path,
    activation_path: Path,
    v1_protocol_path: Path,
    candidate_contract_path: Path,
    candidate_schema_path: Path,
    materialization_manifest_path: Path,
    validation_report_path: Path,
    formulaic_dvc_identity_path: Path,
    formulaic_seal_path: Path,
    provider_report_path: Path,
    authority_facts_path: Path,
    control_model_config_path: Path,
    strategy_config_path: Path,
) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    cohort = load_json(cohort_path)
    activation = load_json(activation_path)
    materialization = load_json(materialization_manifest_path)
    validation = load_json(validation_report_path)
    formulaic_dvc = load_json(formulaic_dvc_identity_path)
    provider = load_json(provider_report_path)

    if protocol.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError("unexpected Protocol V2 version")
    if protocol.get("certification_state", {}).get("protocol_status") != (
        "FROZEN_PENDING_MAIN_ACTIVATION"
    ):
        raise ValueError("Protocol V2 is not frozen pending main activation")
    if protocol.get("certification_state", {}).get("protocol_activated") is not False:
        raise ValueError("Protocol V2 must not be activated by the freeze task")
    if canonical_text_sha256(v1_protocol_path) != EXPECTED_V1_PROTOCOL_SHA256:
        raise ValueError("Protocol V1 authority changed")
    if protocol.get("based_on_protocol", {}).get("v1_protocol_sha256") != (
        EXPECTED_V1_PROTOCOL_SHA256
    ):
        raise ValueError("Protocol V2 does not bind Protocol V1 authority")

    cohort_sha256 = canonical_text_sha256(cohort_path)
    if cohort.get("cohort_version") != COHORT_VERSION:
        raise ValueError("unexpected Formulaic cohort version")
    candidate_ids = cohort.get("candidate_ids")
    if not isinstance(candidate_ids, list) or len(candidate_ids) != 17:
        raise ValueError("Formulaic cohort must contain exactly 17 Candidate IDs")
    if candidate_ids != sorted(candidate_ids) or len(set(candidate_ids)) != 17:
        raise ValueError("Formulaic Candidate IDs must be sorted and unique")
    if FORBIDDEN_COHORT_KEYS & collect_keys(cohort):
        raise ValueError("performance fields are prohibited in the cohort manifest")
    if protocol.get("candidate_cohort", {}).get("cohort_manifest_sha256") != cohort_sha256:
        raise ValueError("Protocol V2 cohort identity mismatch")

    if sha256_file(materialization_manifest_path) != EXPECTED_MATERIALIZATION_SHA256:
        raise ValueError("Candidate V3 materialization identity mismatch")
    if sha256_file(validation_report_path) != EXPECTED_VALIDATION_SHA256:
        raise ValueError("Candidate V3 validation identity mismatch")
    materialized_ids = sorted(row["candidate_id"] for row in materialization["candidates"])
    if materialized_ids != candidate_ids:
        raise ValueError("tracked cohort differs from Candidate V3 materialization")
    if validation.get("candidate_count") != 17 or validation.get(
        "candidate_id_unique_count"
    ) != 17:
        raise ValueError("Candidate V3 validation count mismatch")
    if cohort.get("frozen_discovery_candidate_manifest_sha256") != (
        EXPECTED_DISCOVERY_MANIFEST_SHA256
    ):
        raise ValueError("discovery Candidate manifest identity mismatch")

    contract = cohort.get("candidate_contract", {})
    if contract.get("contract_document_sha256") != sha256_file(candidate_contract_path):
        raise ValueError("Candidate Contract V3 document identity mismatch")
    if contract.get("contract_schema_sha256") != sha256_file(candidate_schema_path):
        raise ValueError("Candidate Contract V3 schema identity mismatch")

    activation_sha256 = canonical_text_sha256(activation_path)
    if activation.get("activation_status") != "PENDING_ORIGIN_MAIN_MERGE":
        raise ValueError("Protocol V2 activation placeholder is not pending")
    if activation.get("freeze_merge_sha") != "UNRESOLVED":
        raise ValueError("freeze merge SHA must remain unresolved")
    if activation.get("sealed_oos_start_session") != "UNRESOLVED":
        raise ValueError("sealed OOS start must remain unresolved")
    if activation.get("minimum_sealed_oos_sessions") != 126:
        raise ValueError("minimum sealed OOS sessions changed")
    if protocol.get("activation", {}).get("activation_placeholder_sha256") != (
        activation_sha256
    ):
        raise ValueError("activation placeholder identity mismatch")

    if formulaic_dvc.get("dvc_stage_lock_entry_identity") != (
        EXPECTED_FORMULAIC_STAGE_IDENTITY
    ):
        raise ValueError("Formulaic DVC stage identity mismatch")
    if formulaic_dvc.get("seal_output_sha256") != EXPECTED_FORMULAIC_SEAL_SHA256:
        raise ValueError("Formulaic DVC seal report mismatch")
    if sha256_file(formulaic_seal_path) != EXPECTED_FORMULAIC_SEAL_SHA256:
        raise ValueError("Formulaic DVC seal bytes changed")

    if sha256_file(provider_report_path) != EXPECTED_PROVIDER_REPORT_SHA256:
        raise ValueError("provider report identity mismatch")
    dataset = protocol.get("dataset_authority", {})
    if provider.get("total_member_session_rows") != dataset.get("member_session_rows"):
        raise ValueError("provider member-session count mismatch")
    if sha256_file(authority_facts_path) != dataset.get("authority_fact_sha256"):
        raise ValueError("provider-binding authority changed")
    if canonical_text_sha256(control_model_config_path) != EXPECTED_CONTROL_CONFIG_SHA256:
        raise ValueError("Linear OLS control configuration changed")
    if canonical_text_sha256(strategy_config_path) != EXPECTED_STRATEGY_CONFIG_SHA256:
        raise ValueError("TopkDropoutStrategy configuration changed")

    non_authorizations = protocol.get("non_authorizations", {})
    required_false = {
        "backtest",
        "certification_decision_executed",
        "future_market_data_accessed",
        "historical_test_accessed_this_task",
        "historical_test_performance_accessed",
        "model_training",
        "new_predictions",
        "sealed_oos_accessed",
    }
    if any(non_authorizations.get(key) is not False for key in required_false):
        raise ValueError("Protocol V2 freeze task claimed prohibited execution")

    dependencies = {
        "activation_placeholder": activation_sha256,
        "authority_facts": sha256_file(authority_facts_path),
        "candidate_contract": sha256_file(candidate_contract_path),
        "candidate_contract_schema": sha256_file(candidate_schema_path),
        "candidate_v3_materialization_manifest": sha256_file(
            materialization_manifest_path
        ),
        "candidate_v3_validation_report": sha256_file(validation_report_path),
        "cohort_manifest": cohort_sha256,
        "control_model_config_canonical_lf": canonical_text_sha256(
            control_model_config_path
        ),
        "formulaic_dvc_identity_report": sha256_file(formulaic_dvc_identity_path),
        "formulaic_dvc_seal": sha256_file(formulaic_seal_path),
        "provider_report": sha256_file(provider_report_path),
        "protocol_v1_canonical_lf": canonical_text_sha256(v1_protocol_path),
        "strategy_config_canonical_lf": canonical_text_sha256(strategy_config_path),
    }
    return {
        "candidate_count": 17,
        "candidate_id_unique_count": 17,
        "cohort_manifest_sha256": cohort_sha256,
        "dependency_sha256": dependencies,
        "formulaic_v3_p2_eligibility": "ELIGIBLE_PENDING_PROTOCOL_V2_ACTIVATION",
        "protocol_sha256": canonical_text_sha256(protocol_path),
        "protocol_status": "FROZEN_PENDING_MAIN_ACTIVATION",
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": SEAL_VERSION,
        "sealed_oos_start_session": "UNRESOLVED_PENDING_MAIN_ACTIVATION",
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "protocol",
        "cohort",
        "activation",
        "v1_protocol",
        "candidate_contract",
        "candidate_schema",
        "materialization_manifest",
        "validation_report",
        "formulaic_dvc_identity",
        "formulaic_seal",
        "provider_report",
        "authority_facts",
        "control_model_config",
        "strategy_config",
        "output",
    ):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    seal = validate_and_build_seal(
        **{
            f"{name}_path": getattr(args, name)
            for name in (
                "protocol",
                "cohort",
                "activation",
                "v1_protocol",
                "candidate_contract",
                "candidate_schema",
                "materialization_manifest",
                "validation_report",
                "formulaic_dvc_identity",
                "formulaic_seal",
                "provider_report",
                "authority_facts",
                "control_model_config",
                "strategy_config",
            )
        }
    )
    output = deterministic_json_bytes(seal)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(json.dumps({"output_sha256": hashlib.sha256(output).hexdigest(), **seal}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
