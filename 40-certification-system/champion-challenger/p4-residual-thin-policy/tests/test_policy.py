from __future__ import annotations

import hashlib
import inspect
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from typing import Union

import rfc8785
from jsonschema import Draft202012Validator
from pydantic import TypeAdapter, ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import aq_p4_policy as policy  # noqa: E402


def identity(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


CANDIDATE_ID = identity("synthetic-candidate")


def certification(**changes: object) -> policy.P2CertificationEvidenceV1:
    values: dict[str, object] = {
        "contract_version": "P2CertificationEvidenceV1",
        "authority": "P2",
        "candidate_id": CANDIDATE_ID,
        "protocol_identity": "P2_CERTIFICATION_PROTOCOL_V1",
        "protocol_version": "V1",
        "certification_artifact_identity": identity("certification-artifact"),
        "certification_status": "CERTIFIED",
        "evidence_identity": identity("certification-evidence"),
        "evidence_classification": "TEST_FIXTURE_NOT_REAL_EVIDENCE",
    }
    values.update(changes)
    return policy.P2CertificationEvidenceV1(**values)


def shadow(
    status: policy.ShadowStatus = policy.ShadowStatus.INCOMPLETE,
    **changes: object,
) -> policy.ShadowEvidenceV1:
    cert = certification()
    values: dict[str, object] = {
        "contract_version": "ShadowEvidenceV1",
        "candidate_id": CANDIDATE_ID,
        "certification_evidence_identity": cert.evidence_identity,
        "certification_artifact_identity": cert.certification_artifact_identity,
        "observation_start": date(2026, 1, 2),
        "observation_end": date(2026, 2, 2),
        "calendar_identity": identity("xnys-calendar"),
        "prediction_evidence_identity": identity("prediction"),
        "outcome_return_evidence_identity": identity("outcome"),
        "cost_assumption_identity": identity("costs"),
        "qlib_experiment_id": "synthetic-experiment",
        "qlib_recorder_id": "synthetic-run",
        "mlflow_experiment_id": "synthetic-experiment",
        "mlflow_run_id": "synthetic-run",
        "dvc_reproducibility_identity": identity("dvc"),
        "zero_capital_attestation": True,
        "completion_status": status,
    }
    values.update(changes)
    return policy.ShadowEvidenceV1(**values)


def detector(change: bool = True, **changes: object) -> policy.DetectorEvidenceReferenceV1:
    values: dict[str, object] = {
        "contract_version": "DetectorEvidenceReferenceV1",
        "candidate_id": CANDIDATE_ID,
        "detector_evidence_identity": identity("detector"),
        "metric_observation_stream_identity": identity("observations"),
        "upstream_identity_projection_identity": identity("projection"),
        "metric_kind": "RANK_IC",
        "change_detected": change,
        "change_event_count": 1 if change else 0,
    }
    values.update(changes)
    return policy.DetectorEvidenceReferenceV1(**values)


def financial(adverse: bool = True, **changes: object) -> policy.RankICSummaryEvidenceV1:
    values: dict[str, object] = {
        "contract_version": "RankICSummaryEvidenceV1",
        "candidate_id": CANDIDATE_ID,
        "metric_kind": "RANK_IC",
        "upstream_identity_projection_identity": identity("projection"),
        "reference_evidence_identity": identity("reference-rank-ic"),
        "current_evidence_identity": identity("current-rank-ic"),
        "reference_rank_ic": 0.10,
        "current_rank_ic": 0.02 if adverse else 0.09,
        "reference_sample_count": 100,
        "current_sample_count": 50,
        "persistence_evidence_count": 2,
    }
    values.update(changes)
    return policy.RankICSummaryEvidenceV1(**values)


def test_config() -> policy.FinancialDecayPolicyConfigV1:
    return policy.FinancialDecayPolicyConfigV1(
        contract_version="FinancialDecayPolicyConfigV1",
        status="TEST_ONLY_POLICY_CONFIG",
        metric_kind="RANK_IC",
        minimum_deterioration=0.05,
        minimum_reference_sample_count=80,
        minimum_current_sample_count=40,
        required_change_events=1,
        required_persistence_evidence_count=2,
        corroboration_required=True,
    )


def retirement(authorized: bool = True) -> policy.RetirementAuthorizationV1:
    return policy.RetirementAuthorizationV1(
        contract_version="RetirementAuthorizationV1",
        candidate_id=CANDIDATE_ID,
        authorization_identity=identity("retirement-authorization"),
        authority="TEST_FIXTURE",
        evidence_classification="TEST_ONLY_RETIREMENT_AUTHORIZATION",
        authorized=authorized,
    )


class LifecycleStructureTests(unittest.TestCase):
    def test_exact_six_states(self) -> None:
        self.assertEqual(
            {
                "RESEARCH_CANDIDATE",
                "CERTIFIED",
                "SHADOW",
                "CHAMPION",
                "DEGRADED",
                "RETIRED",
            },
            {state.value for state in policy.LifecycleState},
        )

    def test_all_36_state_pairs_have_exactly_five_edges(self) -> None:
        results = {
            (source, target): policy.is_structurally_authorized_transition(source, target)
            for source in policy.LifecycleState
            for target in policy.LifecycleState
        }
        self.assertEqual(36, len(results))
        self.assertEqual(5, sum(results.values()))
        self.assertEqual(31, len(results) - sum(results.values()))
        self.assertEqual(policy.AUTHORIZED_TRANSITIONS, {pair for pair, ok in results.items() if ok})

    def test_retired_is_terminal_and_bypasses_are_rejected(self) -> None:
        for target in policy.LifecycleState:
            self.assertFalse(
                policy.is_structurally_authorized_transition(
                    policy.LifecycleState.RETIRED, target
                )
            )
        rejected = {
            (policy.LifecycleState.RESEARCH_CANDIDATE, policy.LifecycleState.SHADOW),
            (policy.LifecycleState.RESEARCH_CANDIDATE, policy.LifecycleState.CHAMPION),
            (policy.LifecycleState.CERTIFIED, policy.LifecycleState.CHAMPION),
            (policy.LifecycleState.SHADOW, policy.LifecycleState.DEGRADED),
            (policy.LifecycleState.SHADOW, policy.LifecycleState.RETIRED),
            (policy.LifecycleState.CHAMPION, policy.LifecycleState.RETIRED),
            (policy.LifecycleState.DEGRADED, policy.LifecycleState.CHAMPION),
        }
        self.assertTrue(all(not policy.is_structurally_authorized_transition(*pair) for pair in rejected))

    def test_challenger_is_role_not_state(self) -> None:
        self.assertNotIn("CHALLENGER", {state.value for state in policy.LifecycleState})
        allowed = {state for state in policy.LifecycleState if policy.challenger_role_allowed(state)}
        self.assertEqual(
            {policy.LifecycleState.CERTIFIED, policy.LifecycleState.SHADOW}, allowed
        )
        self.assertFalse(policy.challenger_role_allowed(policy.LifecycleState.CHAMPION))

    def test_no_p4_certify_decision_or_operational_decision(self) -> None:
        kinds = {kind.value for kind in policy.DecisionKind}
        self.assertNotIn("CERTIFY", kinds)
        self.assertFalse(
            kinds.intersection({"RUN_JOB", "RETRY", "WAKE", "SCHEDULE", "DEPLOY", "TRADE"})
        )
        self.assertEqual(
            "P2",
            policy.transition_authority(
                policy.LifecycleState.RESEARCH_CANDIDATE,
                policy.LifecycleState.CERTIFIED,
            ),
        )
        self.assertTrue(
            all(
                authority == "P4"
                for edge, authority in policy.TRANSITION_AUTHORITIES.items()
                if edge
                != (
                    policy.LifecycleState.RESEARCH_CANDIDATE,
                    policy.LifecycleState.CERTIFIED,
                )
            )
        )


class CertificationAndShadowTests(unittest.TestCase):
    def test_certified_admits_incomplete_zero_capital_shadow(self) -> None:
        decision = policy.admit_shadow(
            current_state=policy.LifecycleState.CERTIFIED,
            candidate_id=CANDIDATE_ID,
            certification=certification(),
            shadow=shadow(),
            allow_test_fixture=True,
        )
        self.assertEqual(policy.DecisionKind.ADMIT_SHADOW, decision.decision_kind)
        self.assertEqual(policy.LifecycleState.SHADOW, decision.target_state)

    def test_missing_or_noncertified_p2_evidence_rejected(self) -> None:
        for evidence in (None, certification(certification_status="REJECTED")):
            with self.subTest(evidence=evidence):
                decision = policy.admit_shadow(
                    current_state=policy.LifecycleState.CERTIFIED,
                    candidate_id=CANDIDATE_ID,
                    certification=evidence,
                    shadow=shadow(),
                    allow_test_fixture=True,
                )
                self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, decision.decision_kind)

    def test_test_fixture_is_not_accepted_as_real_evidence(self) -> None:
        decision = policy.admit_shadow(
            current_state=policy.LifecycleState.CERTIFIED,
            candidate_id=CANDIDATE_ID,
            certification=certification(),
            shadow=shadow(),
        )
        self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, decision.decision_kind)

    def test_candidate_mismatch_rejected(self) -> None:
        decision = policy.admit_shadow(
            current_state=policy.LifecycleState.CERTIFIED,
            candidate_id=CANDIDATE_ID,
            certification=certification(candidate_id=identity("other")),
            shadow=shadow(),
            allow_test_fixture=True,
        )
        self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, decision.decision_kind)

    def test_wrong_protocol_self_issuer_and_extra_field_fail_closed(self) -> None:
        base = certification().model_dump(mode="json")
        for key, value in (
            ("protocol_identity", "P4_SELF_CERTIFICATION"),
            ("authority", "P4"),
            ("fabricated", True),
        ):
            candidate = dict(base)
            candidate[key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                policy.P2CertificationEvidenceV1(**candidate)

    def test_candidate_and_certified_bypasses_are_rejected(self) -> None:
        for current, function in (
            (policy.LifecycleState.RESEARCH_CANDIDATE, policy.admit_shadow),
            (policy.LifecycleState.RESEARCH_CANDIDATE, policy.promote_champion),
            (policy.LifecycleState.CERTIFIED, policy.promote_champion),
        ):
            decision = function(
                current_state=current,
                candidate_id=CANDIDATE_ID,
                certification=certification(),
                shadow=shadow(policy.ShadowStatus.COMPLETE_PASS),
                allow_test_fixture=True,
            )
            self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, decision.decision_kind)

    def test_shadow_zero_capital_and_identity_are_fail_closed(self) -> None:
        for evidence in (
            shadow(zero_capital_attestation=False),
            shadow(certification_evidence_identity=identity("wrong-cert")),
        ):
            decision = policy.admit_shadow(
                current_state=policy.LifecycleState.CERTIFIED,
                candidate_id=CANDIDATE_ID,
                certification=certification(),
                shadow=evidence,
                allow_test_fixture=True,
            )
            self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, decision.decision_kind)

    def test_shadow_interval_and_qlib_mlflow_identity_are_fail_closed(self) -> None:
        with self.assertRaises(ValidationError):
            shadow(observation_start=date(2026, 2, 3), observation_end=date(2026, 2, 2))
        with self.assertRaises(ValidationError):
            shadow(mlflow_run_id="different-run")
        with self.assertRaises(ValidationError):
            shadow(dvc_reproducibility_identity="not-a-dvc-identity")

    def test_promotion_requires_complete_pass(self) -> None:
        expected = {
            policy.ShadowStatus.COMPLETE_PASS: policy.DecisionKind.PROMOTE_CHAMPION,
            policy.ShadowStatus.INCOMPLETE: policy.DecisionKind.NO_CHANGE,
            policy.ShadowStatus.COMPLETE_FAIL: policy.DecisionKind.NO_CHANGE,
        }
        for status, decision_kind in expected.items():
            decision = policy.promote_champion(
                current_state=policy.LifecycleState.SHADOW,
                candidate_id=CANDIDATE_ID,
                certification=certification(),
                shadow=shadow(status),
                allow_test_fixture=True,
            )
            self.assertEqual(decision_kind, decision.decision_kind)
            self.assertFalse(decision.live_trading_authorized)
            self.assertFalse(decision.capital_authorized)
            self.assertFalse(decision.production_activation_authorized)
            self.assertTrue(decision.p4_champion_role_is_not_production_authorization)


class DecayAndRetirementTests(unittest.TestCase):
    def test_production_policy_is_unset_and_cannot_carry_thresholds(self) -> None:
        unset = policy.FinancialDecayPolicyConfigV1(
            contract_version="FinancialDecayPolicyConfigV1",
            status=policy.PRODUCTION_DECAY_POLICY_STATUS,
            metric_kind="RANK_IC",
            corroboration_required=True,
        )
        self.assertIsNone(policy.DEFAULT_PRODUCTION_DECAY_THRESHOLDS)
        with self.assertRaises(ValidationError):
            unset.model_copy(update={"minimum_deterioration": 0.01}, deep=True).__class__(
                **{**unset.model_dump(), "minimum_deterioration": 0.01}
            )

    def test_change_event_alone_does_not_degrade(self) -> None:
        decision = policy.mark_degraded(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(True),
            financial=financial(False),
            config=test_config(),
        )
        self.assertEqual(policy.DecisionKind.NO_CHANGE, decision.decision_kind)

    def test_adverse_financial_evidence_alone_does_not_degrade(self) -> None:
        decision = policy.mark_degraded(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(False),
            financial=financial(True),
            config=test_config(),
        )
        self.assertEqual(policy.DecisionKind.NO_CHANGE, decision.decision_kind)

    def test_missing_or_unregistered_config_fails_closed(self) -> None:
        unset = policy.FinancialDecayPolicyConfigV1(
            contract_version="FinancialDecayPolicyConfigV1",
            status=policy.PRODUCTION_DECAY_POLICY_STATUS,
            metric_kind="RANK_IC",
            corroboration_required=True,
        )
        for config in (None, unset):
            decision = policy.mark_degraded(
                current_state=policy.LifecycleState.CHAMPION,
                candidate_id=CANDIDATE_ID,
                detector=detector(True),
                financial=financial(True),
                config=config,
            )
            self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, decision.decision_kind)
            self.assertEqual(
                policy.DecisionReason.DECAY_POLICY_NOT_PREREGISTERED, decision.reason
            )

    def test_change_and_adverse_test_evidence_mark_degraded(self) -> None:
        decision = policy.mark_degraded(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(True),
            financial=financial(True),
            config=test_config(),
        )
        self.assertEqual(policy.DecisionKind.MARK_DEGRADED, decision.decision_kind)
        self.assertEqual(policy.LifecycleState.DEGRADED, decision.target_state)

    def test_temporary_or_insufficient_evidence_is_no_change(self) -> None:
        decision = policy.mark_degraded(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(True),
            financial=financial(True, persistence_evidence_count=1),
            config=test_config(),
        )
        self.assertEqual(policy.DecisionKind.NO_CHANGE, decision.decision_kind)

    def test_cross_projection_identity_mismatch_fails_closed(self) -> None:
        decision = policy.mark_degraded(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(True),
            financial=financial(
                True, upstream_identity_projection_identity=identity("other-projection")
            ),
            config=test_config(),
        )
        self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, decision.decision_kind)

    def test_retirement_requires_degraded_and_explicit_authorization(self) -> None:
        champion = policy.retire(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            authorization=retirement(),
        )
        no_authority = policy.retire(
            current_state=policy.LifecycleState.DEGRADED,
            candidate_id=CANDIDATE_ID,
            authorization=None,
        )
        denied = policy.retire(
            current_state=policy.LifecycleState.DEGRADED,
            candidate_id=CANDIDATE_ID,
            authorization=retirement(False),
        )
        accepted = policy.retire(
            current_state=policy.LifecycleState.DEGRADED,
            candidate_id=CANDIDATE_ID,
            authorization=retirement(True),
        )
        self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, champion.decision_kind)
        self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, no_authority.decision_kind)
        self.assertEqual(policy.DecisionKind.REJECT_TRANSITION, denied.decision_kind)
        self.assertEqual(policy.DecisionKind.RETIRE, accepted.decision_kind)


class ResearchRequestTests(unittest.TestCase):
    def _request(self, reason: policy.ChallengerReason) -> policy.ResearchRequestV1:
        state = None if reason == policy.ChallengerReason.NO_CHAMPION else policy.LifecycleState.DEGRADED
        decision = policy.challenger_needed(
            candidate_id=CANDIDATE_ID,
            reason=reason,
            current_champion_state=state,
            source_evidence_identities=(identity("source-b"), identity("source-a")),
            test_fixture=True,
        )
        self.assertEqual(policy.DecisionKind.CHALLENGER_NEEDED, decision.decision_kind)
        return policy.build_research_request(
            challenger_decision=decision,
            asset_universe_scope_identity=identity("universe"),
            allowed_research_families=("FORMULAIC_ALPHA", "RD_AGENT"),
            research_budget_identity=identity("budget"),
            target_protocol_context="P2_FUTURE_PROTOCOL_CONTEXT",
            evidence_cutoff=date(2026, 9, 17),
            request_provenance=identity("provenance"),
        )

    def test_no_champion_and_degraded_champion_create_requests(self) -> None:
        for reason in policy.ChallengerReason:
            request = self._request(reason)
            self.assertEqual(reason, request.reason)

    def test_request_id_is_upstream_rfc8785_sha256(self) -> None:
        request = self._request(policy.ChallengerReason.NO_CHAMPION)
        projection = request.model_dump(mode="json", exclude={"request_id"})
        expected = "sha256:" + hashlib.sha256(rfc8785.dumps(projection)).hexdigest()
        self.assertEqual(expected, request.request_id)

    def test_request_is_producer_neutral_and_closed(self) -> None:
        request = self._request(policy.ChallengerReason.CHAMPION_DEGRADED)
        keys = set(request.model_dump(mode="json"))
        self.assertFalse(
            keys.intersection(
                {
                    "ppo_parameters",
                    "alphagen_pool",
                    "rdagent_prompt",
                    "model_hyperparameters",
                    "training_command",
                    "scheduler_cadence",
                    "promotion_authority",
                }
            )
        )
        with self.assertRaises(ValidationError):
            policy.ResearchRequestV1(**request.model_dump(), ppo_parameters={"steps": 1})

    def test_request_rejects_tampered_identity(self) -> None:
        request = self._request(policy.ChallengerReason.NO_CHAMPION)
        with self.assertRaises(ValidationError):
            policy.ResearchRequestV1(
                **{**request.model_dump(), "request_id": identity("tampered")}
            )

    def test_request_requires_challenger_needed_decision(self) -> None:
        rejected = policy.challenger_needed(
            candidate_id=CANDIDATE_ID,
            reason=policy.ChallengerReason.NO_CHAMPION,
            current_champion_state=policy.LifecycleState.CHAMPION,
            source_evidence_identities=(identity("source"),),
        )
        with self.assertRaises(ValueError):
            policy.build_research_request(
                challenger_decision=rejected,
                asset_universe_scope_identity=identity("universe"),
                allowed_research_families=("FORMULAIC_ALPHA",),
                research_budget_identity=identity("budget"),
                target_protocol_context="P2_CONTEXT",
                evidence_cutoff=date(2026, 9, 17),
                request_provenance=identity("provenance"),
            )


class ContractAndPurityTests(unittest.TestCase):
    def test_materialized_schema_is_valid_and_models_are_closed(self) -> None:
        schema = json.loads((ROOT / "schemas" / "p4_policy_contracts_v1.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        expected_models = {
            "P2CertificationEvidenceV1",
            "ShadowEvidenceV1",
            "DetectorEvidenceReferenceV1",
            "RankICSummaryEvidenceV1",
            "FinancialDecayPolicyConfigV1",
            "RetirementAuthorizationV1",
            "LifecycleDecisionEvidenceV1",
            "ResearchRequestV1",
        }
        self.assertTrue(expected_models.issubset(schema["$defs"]))
        for name in expected_models:
            self.assertFalse(schema["$defs"][name]["additionalProperties"])

        contracts = Union[
            policy.P2CertificationEvidenceV1,
            policy.ShadowEvidenceV1,
            policy.DetectorEvidenceReferenceV1,
            policy.RankICSummaryEvidenceV1,
            policy.FinancialDecayPolicyConfigV1,
            policy.RetirementAuthorizationV1,
            policy.LifecycleDecisionEvidenceV1,
            policy.ResearchRequestV1,
        ]
        generated = TypeAdapter(contracts).json_schema(union_format="any_of")
        generated.update(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:autonomous-quant:P4ResidualThinPolicyContractsV1",
                "title": "P4 Residual Thin Policy Contracts V1",
            }
        )
        self.assertEqual(schema, generated)

    def test_policy_is_deterministic_and_decisions_are_frozen(self) -> None:
        arguments = dict(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(True),
            financial=financial(True),
            config=test_config(),
        )
        first = policy.mark_degraded(**arguments)
        second = policy.mark_degraded(**arguments)
        self.assertEqual(first.model_dump(mode="json"), second.model_dump(mode="json"))
        with self.assertRaises(ValidationError):
            first.decision_kind = policy.DecisionKind.NO_CHANGE

    def test_decision_contract_rejects_kind_target_contradiction(self) -> None:
        decision = policy.mark_degraded(
            current_state=policy.LifecycleState.CHAMPION,
            candidate_id=CANDIDATE_ID,
            detector=detector(True),
            financial=financial(True),
            config=test_config(),
        )
        with self.assertRaises(ValidationError):
            policy.LifecycleDecisionEvidenceV1(
                **{
                    **decision.model_dump(),
                    "decision_kind": "PROMOTE_CHAMPION",
                    "target_state": "DEGRADED",
                }
            )

    def test_module_has_no_runtime_or_persistence_dependencies(self) -> None:
        source = inspect.getsource(policy)
        prohibited = (
            "import requests",
            "import sqlite",
            "import mlflow",
            "import qlib",
            "import frouros",
            "import random",
            "datetime.now",
            "time.time",
            "subprocess",
            "open(",
        )
        self.assertTrue(all(token not in source for token in prohibited))


if __name__ == "__main__":
    unittest.main()
