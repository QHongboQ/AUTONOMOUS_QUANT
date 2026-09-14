"""Seal preregistered protocol dependencies for DVC reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_text_sha256(path: Path) -> str:
    data = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--provider-report", required=True, type=Path)
    parser.add_argument("--qlib-report", required=True, type=Path)
    parser.add_argument("--skfolio-report", required=True, type=Path)
    parser.add_argument("--arch-report", required=True, type=Path)
    parser.add_argument("--validation-report", required=True, type=Path)
    parser.add_argument("--blocker-ledger", required=True, type=Path)
    parser.add_argument("--authority-facts", required=True, type=Path)
    parser.add_argument("--ragged-alpha-config", required=True, type=Path)
    parser.add_argument("--primary-model-config", required=True, type=Path)
    parser.add_argument("--control-model-config", required=True, type=Path)
    parser.add_argument("--strategy-config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    protocol = load(args.protocol)
    provider = load(args.provider_report)

    if protocol["protocol_version"] != "P2_CERTIFICATION_PROTOCOL_V1":
        raise RuntimeError("unexpected protocol version")
    dataset = protocol["dataset_authority"]
    if provider["total_member_session_rows"] != dataset["member_session_rows"]:
        raise RuntimeError("provider row count differs from frozen protocol")
    if provider["observed_safe_rows"] != dataset["observed_safe_rows"]:
        raise RuntimeError("provider observed row count differs from frozen protocol")
    if provider["masked_rows"] != dataset["masked_rows"]:
        raise RuntimeError("provider masked row count differs from frozen protocol")
    if sha256(args.provider_report) != dataset["provider_build_report_sha256"]:
        raise RuntimeError("provider report identity differs from frozen protocol")
    if sha256(args.authority_facts) != dataset["authority_fact_sha256"]:
        raise RuntimeError("authority-fact identity differs from frozen protocol")
    upstream = dataset["upstream_stack_evidence"]
    expected_upstream_hashes = {
        "arch_report_sha256": sha256(args.arch_report),
        "blocker_ledger_canonical_lf_sha256": canonical_text_sha256(
            args.blocker_ledger
        ),
        "qlib_report_sha256": sha256(args.qlib_report),
        "skfolio_report_sha256": sha256(args.skfolio_report),
        "validation_report_sha256": sha256(args.validation_report),
    }
    for key, actual in expected_upstream_hashes.items():
        if upstream[key] != actual:
            raise RuntimeError(f"upstream-stack identity mismatch: {key}")

    expected_text_hashes = {
        "control_model_config": "b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1",
        "primary_model_config": "c6e6c4882adeb053d58e91b27d7d796fd9886dc1946d1d0540d5d9637f42ccaf",
        "ragged_alpha_config": "577ad2c76dd8d16881e240dba876e0b68e617624f6b69ab29ef0c7cea0b12b84",
        "strategy_config": "b96e88cedb0755f36facc0afbc51e38970217582631c2585c645dcbaf7462588",
    }
    actual_text_hashes = {
        "control_model_config": canonical_text_sha256(args.control_model_config),
        "primary_model_config": canonical_text_sha256(args.primary_model_config),
        "ragged_alpha_config": canonical_text_sha256(args.ragged_alpha_config),
        "strategy_config": canonical_text_sha256(args.strategy_config),
    }
    if actual_text_hashes != expected_text_hashes:
        raise RuntimeError("candidate configuration identity mismatch")

    result = {
        "dependency_sha256": {
            "authority_facts": sha256(args.authority_facts),
            "control_model_config_canonical_lf": actual_text_hashes["control_model_config"],
            "primary_model_config_canonical_lf": actual_text_hashes["primary_model_config"],
            "provider_report": sha256(args.provider_report),
            "qlib_report": sha256(args.qlib_report),
            "ragged_alpha_config_canonical_lf": actual_text_hashes["ragged_alpha_config"],
            "skfolio_report": sha256(args.skfolio_report),
            "strategy_config_canonical_lf": actual_text_hashes["strategy_config"],
            "validation_report": sha256(args.validation_report),
            "arch_report": sha256(args.arch_report),
            "blocker_ledger_canonical_lf": canonical_text_sha256(
                args.blocker_ledger
            ),
        },
        "protocol_sha256": sha256(args.protocol),
        "protocol_version": protocol["protocol_version"],
        "schema_version": "P2CertificationProtocolFreezeSealV1",
        "status": "PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
