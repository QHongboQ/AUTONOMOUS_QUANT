from __future__ import annotations

import hashlib
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from typing import Union

from jsonschema import Draft202012Validator
from pydantic import ValidationError
from pydantic import TypeAdapter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import aq_p4_policy as policy  # noqa: E402


CONFIG_PATH = ROOT / "config" / "financial_decay_policy_v2.json"


def identity(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


CANDIDATE_ID = identity("synthetic-production-policy-candidate")


def production_config() -> policy.FinancialDecayPolicyConfigV2:
    return policy.FinancialDecayPolicyConfigV2.model_validate_json(
        CONFIG_PATH.read_bytes()
    )


def detector(change: bool = True) -> policy.DetectorEvidenceReferenceV1:
    return policy.DetectorEvidenceReferenceV1(
        contract_version="DetectorEvidenceReferenceV1",
        candidate_id=CANDIDATE_ID,
        detector_evidence_identity=identity("synthetic-detector"),
        metric_observation_stream_identity=identity("synthetic-observations"),
        upstream_identity_projection_identity=identity("synthetic-projection"),
        metric_kind="RANK_IC",
        change_detected=change,
        change_event_count=1 if change else 0,
    )


def financial(**changes: object) -> policy.RankICSummaryEvidenceV2:
    config = production_config()
    values: dict[str, object] = {
        "contract_version": "RankICSummaryEvidenceV2",
        "candidate_id": CANDIDATE_ID,
        "policy_id": config.policy_id,
        "metric_kind": "RANK_IC",
        "upstream_identity_projection_identity": identity("synthetic-projection"),
        "reference_evidence_identity": identity("synthetic-reference-rank-ic"),
        "current_evidence_identity": identity("synthetic-current-rank-ic"),
        "reference_rank_ic": 0.06,
        "current_rank_ic": 0.01,
        "reference_sample_count": 252,
        "current_sample_count": 63,
        "reference_sample_sessions": 252,
        "current_sample_sessions": 63,
        "policy_evaluation_cadence_sessions": 21,
        "reference_window_start": date(2025, 10, 1),
        "reference_window_end": date(2026, 9, 30),
        "current_window_start": date(2026, 10, 1),
        "current_window_end": date(2026, 12, 30),
        "evidence_cutoff": date(2026, 12, 30),
        "persistence_evidence_count": 3,
        "evidence_classification": "TEST_FIXTURE_NOT_REAL_EVIDENCE",
    }
    values.update(changes)
    return policy.RankICSummaryEvidenceV2(**values)


def decide(
    *,
    detector_evidence: policy.DetectorEvidenceReferenceV1 | None = None,
    financial_evidence: policy.RankICSummaryEvidenceV2 | None = None,
    config: policy.FinancialDecayPolicyConfigV2 | None = None,
) -> policy.LifecycleDecisionEvidenceV1:
    return policy.mark_degraded(
        current_state=policy.LifecycleState.CHAMPION,
        candidate_id=CANDIDATE_ID,
        detector=detector_evidence or detector(),
        financial=financial_evidence or financial(),
        config=production_config() if config is None else config,
    )


class FinancialDecayPolicyV2Tests(unittest.TestCase):
    def test_v2_schema_snapshot_is_valid_and_exact(self) -> None:
        schema_path = ROOT / "schemas" / "p4_policy_contracts_v2.schema.json"
        schema = json.loads(schema_path.read_bytes())
        Draft202012Validator.check_schema(schema)
        contracts = Union[
            policy.P2CertificationEvidenceV1,
            policy.ShadowEvidenceV1,
            policy.ShadowEvidenceV2,
            policy.DetectorEvidenceReferenceV1,
            policy.RankICSummaryEvidenceV1,
            policy.RankICSummaryEvidenceV2,
            policy.FinancialDecayPolicyConfigV1,
            policy.FinancialDecayPolicyConfigV2,
            policy.RetirementAuthorizationV1,
            policy.LifecycleDecisionEvidenceV1,
            policy.ResearchRequestV1,
        ]
        generated = TypeAdapter(contracts).json_schema(union_format="any_of")
        generated.update(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:autonomous-quant:P4ResidualThinPolicyContractsV2",
                "title": "P4 Residual Thin Policy Contracts V2",
            }
        )
        self.assertEqual(schema, generated)

    def test_production_config_valid_frozen_and_identity_reproducible(self) -> None:
        config = production_config()
        non_id_fields = config.model_dump(mode="json", exclude={"policy_id"})
        self.assertEqual(
            config.policy_id,
            policy.financial_decay_policy_identity(non_id_fields),
        )
        self.assertEqual(config.metric_kind, "RANK_IC")
        self.assertEqual(config.effective_epoch, date(2026, 10, 1))
        with self.assertRaises(ValidationError):
            config.minimum_deterioration = 0.01

    def test_policy_id_tampering_is_rejected_by_config(self) -> None:
        values = json.loads(CONFIG_PATH.read_bytes())
        values["minimum_deterioration"] = 0.02
        with self.assertRaisesRegex(ValidationError, "policy_id"):
            policy.FinancialDecayPolicyConfigV2(**values)

    def test_missing_preregistration_fails_closed(self) -> None:
        decision = policy.mark_degraded(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(),
            financial=financial(),
            config=None,
        )
        self.assertEqual(decision.decision_kind, policy.DecisionKind.REJECT_TRANSITION)
        self.assertEqual(decision.reason, policy.DecisionReason.DECAY_POLICY_NOT_PREREGISTERED)

    def test_wrong_policy_id_fails_closed(self) -> None:
        decision = decide(financial_evidence=financial(policy_id=identity("wrong-policy")))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.REJECT_TRANSITION)
        self.assertEqual(decision.reason, policy.DecisionReason.DECAY_POLICY_NOT_PREREGISTERED)

    def test_current_window_before_effective_epoch_fails_closed(self) -> None:
        evidence = financial(
            reference_window_start=date(2025, 7, 1),
            reference_window_end=date(2026, 6, 30),
            current_window_start=date(2026, 7, 1),
            current_window_end=date(2026, 9, 30),
            evidence_cutoff=date(2026, 9, 30),
        )
        decision = decide(financial_evidence=evidence)
        self.assertEqual(decision.decision_kind, policy.DecisionKind.REJECT_TRANSITION)
        self.assertEqual(decision.reason, policy.DecisionReason.DECAY_POLICY_NOT_PREREGISTERED)

    def test_adwin_change_only_does_not_degrade(self) -> None:
        decision = decide(financial_evidence=financial(current_rank_ic=0.05))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.NO_CHANGE)

    def test_financial_deterioration_only_does_not_degrade(self) -> None:
        decision = decide(detector_evidence=detector(change=False))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.NO_CHANGE)
        self.assertEqual(decision.reason, policy.DecisionReason.STATISTICAL_CHANGE_NOT_DETECTED)

    def test_improvement_with_adwin_change_does_not_degrade(self) -> None:
        decision = decide(financial_evidence=financial(current_rank_ic=0.09))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.NO_CHANGE)

    def test_temporary_shock_without_persistence_does_not_degrade(self) -> None:
        decision = decide(financial_evidence=financial(persistence_evidence_count=1))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.NO_CHANGE)

    def test_persistent_material_deterioration_marks_degraded(self) -> None:
        decision = decide()
        self.assertEqual(decision.decision_kind, policy.DecisionKind.MARK_DEGRADED)
        self.assertEqual(decision.target_state, policy.LifecycleState.DEGRADED)

    def test_persistent_sign_reversal_marks_degraded_without_special_branch(self) -> None:
        decision = decide(financial_evidence=financial(current_rank_ic=-0.03))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.MARK_DEGRADED)

    def test_insufficient_reference_samples_do_not_degrade(self) -> None:
        decision = decide(financial_evidence=financial(reference_sample_count=251))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.NO_CHANGE)

    def test_insufficient_current_samples_do_not_degrade(self) -> None:
        decision = decide(financial_evidence=financial(current_sample_count=62))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.NO_CHANGE)

    def test_insufficient_persistence_does_not_degrade(self) -> None:
        decision = decide(financial_evidence=financial(persistence_evidence_count=2))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.NO_CHANGE)

    def test_window_semantics_mismatch_fails_closed(self) -> None:
        decision = decide(financial_evidence=financial(current_sample_sessions=42))
        self.assertEqual(decision.decision_kind, policy.DecisionKind.REJECT_TRANSITION)
        self.assertEqual(
            decision.reason,
            policy.DecisionReason.FINANCIAL_CORROBORATION_NOT_ADVERSE,
        )


if __name__ == "__main__":
    unittest.main()
