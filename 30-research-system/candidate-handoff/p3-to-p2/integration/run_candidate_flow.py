"""Thin, fail-closed P3 -> P2 -> P4 -> P7 -> P8 -> P9 integration probe.

This is an integration/test entry point, not a production workflow. Real mode
only verifies the existing Candidate V4 and propagates its P2 ineligibility.
Synthetic mode exercises public contract surfaces with fixture-only inputs and
never emits a real authorization or an order.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _emit(result: dict[str, Any]) -> int:
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


def run_real(candidate_path: Path, recorder_artifacts: Path) -> dict[str, Any]:
    """Validate existing V4 provenance, then stop at its authoritative P2 gate."""
    from project_rdagent_candidate_v4 import project_rdagent_candidate

    integration_dir = Path(__file__).resolve().parents[1]
    raw = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate = project_rdagent_candidate(
        raw, recorder_artifacts, integration_dir
    )
    p2 = candidate["p2_target_and_eligibility_boundary"]
    if p2.get("eligibility_authority") != "P2_CERTIFICATION":
        raise ValueError("Candidate V4 has no recognized P2 eligibility authority")
    eligibility = p2.get("candidate_eligibility_status")
    if eligibility != "INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION":
        raise ValueError(
            "Real integration only admits the verified current ineligible state; "
            "other P2 states require an actual P2 decision artifact"
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
            "protocol": p2["target_protocol_version"],
            "evidence_type": "CANDIDATE_V4_BOUNDARY_NOT_CERTIFICATION_DECISION",
        },
        "p4": {"status": "BLOCKED_P2_INELIGIBLE", "decision_created": False},
        "p7": {
            "status": "BLOCKED_P2_INELIGIBLE_AND_P7_REQUIRES_V3",
            "decision_created": False,
            "note": "Frozen P7 protocol requires a valid Candidate V3 identity.",
        },
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
    from time_effective_roster_handoff import (
        RosterMember,
        build_roster,
        select_effective_rosters,
    )

    fixture = lambda ch: "sha256:" + ch * 64
    candidate_ids = (fixture("a"), fixture("b"))
    certifications: list[P2CertificationEvidenceV1] = []
    decisions = []
    members = []
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
        if decision.decision_kind == DecisionKind.ADMIT_SHADOW:
            members.append(
                RosterMember(
                    candidate_id=candidate_id,
                    authorization_evidence_id=fixture("4" if index == 0 else "5"),
                )
            )

    cutoff = datetime(2026, 10, 16, 23, 0, tzinfo=timezone.utc)
    roster = build_roster(
        use_scope="SYNTHETIC_TEST_ONLY",
        source_decision_bundle_identity=fixture("6"),
        evidence_cutoff=cutoff,
        effective_session="2026-10-19",
        supersedes_roster_id=None,
        members=members,
    )
    if len(roster.members) != 2:
        raise AssertionError("P7 public roster contract did not retain both fixture members")
    selected = select_effective_rosters(
        rosters=(roster,),
        sessions=("2026-10-19",),
        decision_cutoffs={"2026-10-19": cutoff},
    )
    if len(selected["2026-10-19"]) != 2:
        raise AssertionError("P7 public handoff did not retain both fixture members")
    p7_members = selected["2026-10-19"]

    p8_schema_path = (
        Path(__file__).resolve().parents[4]
        / "50-portfolio-system"
        / "contracts"
        / "target_portfolio_v1.schema.json"
    )
    p8_schema = json.loads(p8_schema_path.read_text(encoding="utf-8"))
    target_fixture = {
        "contract_version": "AQ_TARGET_PORTFOLIO_V1",
        "target_portfolio_id": fixture("7"),
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
            for index, member in enumerate(p7_members)
            for candidate_id in (member.candidate_id,)
        ],
        "target_weights": {},
        "cash_target_weight": 1.0,
        "risk_envelope": {
            "contract_version": "AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1",
            "status": "HUMAN_APPROVED",
            "risk_envelope_id": fixture("a"),
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
            "status": "PASS_TEST_FIXTURE_ONLY",
            "roster_member_count": len(roster.members),
            "effective_session_selection": "PASS",
        },
        "p8": {
            "status": "PASS_SCHEMA_FIXTURE_ONLY",
            "target_portfolio_created": False,
        },
        "p9": {
            "status": "BLOCKED_SYNTHETIC_ONLY",
            "execution_permitted": False,
            "boundary": "FIXTURE_ONLY_NO_BROKER_INTERFACE",
            "broker_write_calls": 0,
        },
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
