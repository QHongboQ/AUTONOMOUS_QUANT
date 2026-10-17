"""Thin, fail-closed P3 -> P2 -> P4 -> P7 -> P8 -> P9 integration probe.

This is an integration/test entry point, not a production workflow. Real mode
only verifies the existing Candidate V4 and propagates its P2 ineligibility.
Synthetic mode exercises public contract surfaces with fixture-only inputs and
never emits a real authorization or an order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _emit(result: dict[str, Any]) -> int:
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


def _canonical_text_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _load_p2_v2_authority(
    candidate_id: str,
    candidate_status: str,
    candidate_target_protocol: str,
    repo_root: Path,
) -> dict[str, Any]:
    """Derive the current V2 eligibility boundary from its frozen authorities."""
    protocol_path = (
        repo_root
        / "40-certification-system/protocol/p2-certification-protocol-v2.json"
    )
    activation_path = (
        repo_root
        / "40-certification-system/protocol/p2-certification-protocol-v2-activation.json"
    )
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    cohort_path = repo_root / protocol["candidate_cohort"]["cohort_manifest_path"]
    cohort = json.loads(cohort_path.read_text(encoding="utf-8"))

    protocol_sha = _canonical_text_sha256(protocol_path)
    activation_sha = _canonical_text_sha256(activation_path)
    cohort_sha = _canonical_text_sha256(cohort_path)
    ids = cohort.get("candidate_ids")
    cohort_authority = protocol.get("candidate_cohort", {})
    if protocol.get("protocol_version") != "P2_CERTIFICATION_PROTOCOL_V2":
        raise ValueError("unexpected P2 protocol authority")
    if protocol_sha != activation.get("protocol_sha256"):
        raise ValueError("P2 V2 activation does not bind the frozen protocol")
    if (
        activation_sha
        != "ff3356850e2a6799c1a8827c0c9aa93e1b54e991d54bca10329471f40abcf9ae"
    ):
        raise ValueError("P2 V2 activation identity is not the frozen activation")
    if protocol["candidate_cohort"].get("cohort_manifest_sha256") != cohort_sha:
        raise ValueError("P2 V2 protocol does not bind the frozen cohort")
    if activation.get("protocol_version") != protocol.get("protocol_version"):
        raise ValueError("P2 V2 activation version mismatch")
    if (
        activation.get("sealed_oos_start_session") != "2026-09-18"
        or activation.get("freeze_merge_sha")
        != "9f97c1dc9fd419cadb5bb5a9a304505a5d87411b"
        or activation.get("minimum_sealed_oos_sessions") != 126
        or activation.get("one_shot_release") is not True
    ):
        raise ValueError("P2 V2 activation boundary is not the expected frozen boundary")
    if (
        cohort.get("cohort_version") != "P2_FORMULAIC_ALPHA_CERTIFICATION_COHORT_V2"
        or not isinstance(ids, list)
        or len(ids) != 17
        or len(set(ids)) != 17
        or cohort_authority.get("candidate_count") != len(ids)
        or cohort_authority.get("candidate_contract_version")
        != "P3_CANDIDATE_TO_P2_CONTRACT_V3"
        or cohort_authority.get("addition") != "PROHIBITED"
    ):
        raise ValueError("P2 V2 frozen cohort is malformed")

    # Protocol V2 freezes Candidate V3 membership. A V4 provenance record is
    # not a P2 decision, and any self-reported eligibility disagreement fails
    # closed.
    in_frozen_cohort = candidate_id in ids
    if in_frozen_cohort:
        raise ValueError("Candidate V4 must not enter the frozen V2 Candidate V3 cohort")
    authoritative_status = "INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION"
    if candidate_status != authoritative_status:
        raise ValueError("Candidate self-reported eligibility conflicts with P2 authority")
    return {
        "protocol_version": protocol["protocol_version"],
        "protocol_sha256": protocol_sha,
        "activation_status": "ACTIVE",
        "sealed_oos_start_session": activation["sealed_oos_start_session"],
        "cohort_count": len(ids),
        "candidate_in_frozen_cohort": False,
        "eligibility": authoritative_status,
        "candidate_target_protocol": candidate_target_protocol,
        "candidate_target_protocol_is_current_v2": (
            candidate_target_protocol == protocol["protocol_version"]
        ),
    }


def run_real(candidate_path: Path, recorder_artifacts: Path) -> dict[str, Any]:
    """Validate existing V4 provenance, then stop at its authoritative P2 gate."""
    from project_rdagent_candidate_v4 import project_rdagent_candidate

    candidate_contract_dir = (
        Path(__file__).resolve().parents[3]
        / "30-research-system/candidate-handoff/p3-to-p2"
    )
    raw = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate = project_rdagent_candidate(
        raw, recorder_artifacts, candidate_contract_dir
    )
    p2 = candidate["p2_target_and_eligibility_boundary"]
    if p2.get("eligibility_authority") != "P2_CERTIFICATION":
        raise ValueError("Candidate V4 has no recognized P2 eligibility authority")
    eligibility = p2.get("candidate_eligibility_status")
    repo_root = Path(__file__).resolve().parents[3]
    p2_authority = _load_p2_v2_authority(
        candidate["candidate_id"],
        eligibility,
        p2.get("target_protocol_version", ""),
        repo_root,
    )

    return {
        "mode": "REAL_CANDIDATE_V4",
        "classification": "REAL_PROVENANCE_ONLY_NOT_CERTIFIED",
        "p3": {
            "status": "LOADED_AND_VALIDATED",
            "candidate_id": candidate["candidate_id"],
            "contract": candidate["candidate_contract_version"],
            "producer": "RD_AGENT",
            "rdagent_version": candidate["runtime_identity_bundle"][
                "rdagent_runtime_identity"
            ]["rdagent_version"],
            "rdagent_sha": candidate["runtime_identity_bundle"][
                "rdagent_runtime_identity"
            ]["rdagent_release_git_sha"],
            "qlib_sha": candidate["runtime_identity_bundle"][
                "rdagent_runtime_identity"
            ]["qlib_source_git_sha"],
            "recorder": candidate["qlib_recorder_identity"],
            "model_sha256": candidate["artifact_identity_bundle"][
                "rdagent_artifact_identity"
            ]["serialized_model_artifact"]["sha256"],
            "prediction_sha256": candidate["artifact_identity_bundle"][
                "rdagent_artifact_identity"
            ]["prediction_artifact"]["sha256"],
            "dataset_sha256": candidate["dataset_identity_bundle"][
                "provider_build_report_sha256"
            ],
            "dataset_date_bounds": candidate["dataset_identity_bundle"][
                "date_bounds"
            ],
            "historical_test": p2["historical_research_test_status"],
        },
        "p2": {
            "status": "INELIGIBLE",
            "reason": eligibility,
            "authority": p2["eligibility_authority"],
            "protocol": p2_authority["protocol_version"],
            "authority_verification": p2_authority,
            "evidence_type": "CANDIDATE_V4_BOUNDARY_NOT_CERTIFICATION_DECISION",
        },
        "p4": {"status": "BLOCKED_P2_INELIGIBLE", "decision_created": False},
        "p7": {
            "status": "BLOCKED_P2_INELIGIBLE_AND_P7_REQUIRES_V3",
            "decision_created": False,
            "note": "Frozen P7 protocol requires a valid Candidate V3 identity.",
        },
        "p4_to_p7_synthetic_provenance": "NOT_APPLICABLE_REAL_PATH_BLOCKED",
        "p7_to_p8": "NOT_APPLICABLE_REAL_PATH_BLOCKED",
        "p8": {
            "status": "BLOCKED_NO_CERTIFIED_INPUT_OR_APPROVED_RISK_ENVELOPE",
            "target_portfolio_created": False,
        },
        "p9": {
            "status": "BLOCKED_NO_AUTHORIZED_P8_TARGET",
            "execution_permitted": False,
            "boundary": "STATUS_HANDOFF_ONLY_NO_BROKER_INTERFACE_INVOKED",
            "broker_write_calls": 0,
        },
        "p8_to_p9": "PERMISSION_DENIAL_ONLY",
        "sealed_oos_accessed": False,
        "broker_write_calls": 0,
        "orders": 0,
    }


def run_synthetic() -> dict[str, Any]:
    """Exercise existing P4/P7/P8 public surfaces with fixture-only records."""
    from aq_p4_policy import (
        DecisionKind,
        LifecycleState,
        P2CertificationEvidenceV1,
        ShadowEvidenceV2,
        ShadowStatus,
        admit_shadow,
    )
    from jsonschema import Draft7Validator, FormatChecker
    from time_effective_roster_handoff import RosterMember

    fixture = lambda ch: "sha256:" + ch * 64
    candidate_ids = (fixture("a"), fixture("b"))
    certifications: list[P2CertificationEvidenceV1] = []
    decisions = []
    for index, candidate_id in enumerate(candidate_ids):
        cert = P2CertificationEvidenceV1(
            contract_version="P2CertificationEvidenceV1",
            authority="P2",
            candidate_id=candidate_id,
            protocol_identity="P2_CERTIFICATION_PROTOCOL_V1",
            protocol_version="V1",
            certification_artifact_identity=fixture("c"),
            certification_status="CERTIFIED",
            evidence_identity=fixture("d"),
            evidence_classification="TEST_FIXTURE_NOT_REAL_EVIDENCE",
        )
        shadow = ShadowEvidenceV2(
            contract_version="ShadowEvidenceV2",
            evidence_classification="TEST_FIXTURE_NOT_REAL_SHADOW",
            candidate_id=candidate_id,
            certification_evidence_identity=cert.evidence_identity,
            certification_artifact_identity=cert.certification_artifact_identity,
            observation_start="2025-01-02",
            observation_end="2025-02-28",
            calendar_identity=fixture("e"),
            prediction_evidence_identity=fixture("f"),
            outcome_return_evidence_identity=fixture("1"),
            cost_assumption_identity=fixture("2"),
            qlib_experiment_id="fixture-experiment",
            qlib_recorder_id=f"fixture-run-{index}",
            mlflow_experiment_id="fixture-experiment",
            mlflow_run_id=f"fixture-run-{index}",
            dvc_reproducibility_identity=fixture("3"),
            zero_capital_attestation=True,
            completion_status=ShadowStatus.COMPLETE_PASS,
        )
        decision = admit_shadow(
            current_state=LifecycleState.CERTIFIED,
            candidate_id=candidate_id,
            certification=cert,
            shadow=shadow,
            allow_test_fixture=True,
        )
        if decision.decision_kind != DecisionKind.ADMIT_SHADOW:
            raise AssertionError("P4 public policy rejected its valid synthetic fixture")
        certifications.append(cert)
        decisions.append(decision)
    # P4's immutable decision evidence has no evidence-ID field or native
    # identity constructor. P7 requires per-member authorization_evidence_id
    # plus an external immutable-delivery bundle; do not invent either identity.
    p4_fields = set(type(decisions[0]).model_fields) if decisions else set()
    p7_fields = set(RosterMember.model_fields)
    p4_to_p7_connected = (
        "decision_evidence_identity" in p4_fields
        and "authorization_evidence_id" in p7_fields
    )

    p8_schema_path = (
        Path(__file__).resolve().parents[3]
        / "50-portfolio-system"
        / "contracts"
        / "target_portfolio_v1.schema.json"
    )
    p8_schema = json.loads(p8_schema_path.read_text(encoding="utf-8"))
    import rfc8785

    if rfc8785.__version__ != "0.1.4":
        raise RuntimeError("RFC 8785 runtime identity mismatch")
    target_fixture = {
        "contract_version": "AQ_TARGET_PORTFOLIO_V1",
        "target_portfolio_id": "",
        "effective_time": "2026-10-19T14:00:00Z",
        "provenance": {
            "producer": "QLIB",
            "producer_version": "fixture-only",
            "method_id": "SYNTHETIC_TEST_ONLY",
            "output_artifact": {
                "reference": "fixture://p8/output",
                "sha256": "7" * 64,
            },
        },
        "input_references": [
            {
                "input_kind": "P2_CERTIFIED_CANDIDATE",
                "candidate_id": candidate_id,
                "strategy_artifact": {
                    "reference": f"fixture://candidate/{index}",
                    "sha256": "8" * 64,
                },
                "p2_certification": {
                    "status": "CERTIFIED",
                    "decision": {
                        "reference": f"fixture://p2/decision/{index}",
                        "sha256": "9" * 64,
                    },
                },
            }
            for index, candidate_id in enumerate(candidate_ids)
        ],
        "target_weights": {},
        "cash_target_weight": 1.0,
        "risk_envelope": {
            "contract_version": "AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1",
            "status": "HUMAN_APPROVED",
            "risk_envelope_id": "",
            "effective_from": "2026-10-19T00:00:00Z",
            "effective_until": "2026-10-20T00:00:00Z",
            "human_authority_record": {
                "reference": "fixture://authority",
                "sha256": "b" * 64,
            },
            "risk_limit_set": {
                "reference": "fixture://limits",
                "sha256": "c" * 64,
            },
        },
    }
    risk_identity_payload = dict(target_fixture["risk_envelope"])
    risk_identity_payload.pop("risk_envelope_id")
    target_fixture["risk_envelope"]["risk_envelope_id"] = "sha256:" + hashlib.sha256(
        rfc8785.dumps(risk_identity_payload)
    ).hexdigest()
    target_identity_payload = dict(target_fixture)
    target_identity_payload.pop("target_portfolio_id")
    target_fixture["target_portfolio_id"] = "sha256:" + hashlib.sha256(
        rfc8785.dumps(target_identity_payload)
    ).hexdigest()
    Draft7Validator(
        p8_schema, format_checker=FormatChecker()
    ).validate(target_fixture)

    return {
        "mode": "SYNTHETIC_TEST_ONLY",
        "classification": "FIXTURE_INTERFACE_CONNECTIVITY_ONLY",
        "p3": {"status": "SYNTHETIC_FIXTURE_ONLY", "candidate_count": 2},
        "p2": {"status": "TEST_FIXTURE_NOT_REAL_EVIDENCE", "count": len(certifications)},
        "p4": {
            "status": "PASS_TEST_FIXTURE_ONLY",
            "decisions": [item.decision_kind.value for item in decisions],
        },
        "p7": {
            "status": "CONNECTED" if p4_to_p7_connected else "NOT_CONNECTED_CONTRACT_GAP",
            "roster_created": False,
            "reason": (
                None
                if p4_to_p7_connected
                else "P4 decision evidence exposes no native evidence identity; "
                "P7 requires per-member authorization evidence and immutable delivery metadata."
            ),
            "fabricated_authorization_ids": False,
        },
        "p4_to_p7_synthetic_provenance": (
            "CONNECTED" if p4_to_p7_connected else "NOT_CONNECTED_CONTRACT_GAP"
        ),
        "p7_to_p8": "SCHEMA_ONLY",
        "p8": {
            "status": "PASS_SCHEMA_FIXTURE_ONLY",
            "target_portfolio_created": False,
            "identity": "RFC8785_SHA256_FIXTURE_ID_VALIDATED",
        },
        "p9": {
            "status": "BLOCKED_SYNTHETIC_ONLY",
            "execution_permitted": False,
            "boundary": "FIXTURE_ONLY_NO_BROKER_INTERFACE",
            "broker_write_calls": 0,
        },
        "p8_to_p9": "PERMISSION_DENIAL_ONLY",
        "sealed_oos_accessed": False,
        "broker_write_calls": 0,
        "orders": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("REAL_CANDIDATE_V4", "SYNTHETIC_TEST_ONLY"),
    )
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--recorder-artifacts", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "REAL_CANDIDATE_V4":
            if args.candidate is None or args.recorder_artifacts is None:
                parser.error("real mode requires --candidate and --recorder-artifacts")
            return _emit(run_real(args.candidate, args.recorder_artifacts))
        return _emit(run_synthetic())
    except Exception as exc:  # fail closed; never turn an exception into eligibility
        print(
            json.dumps(
                {
                    "mode": args.mode,
                    "classification": "BLOCKED_VALIDATION_ERROR",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "broker_write_calls": 0,
                    "orders": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
