"""Focused tests for the synthetic-only P12 standing-policy admission gate."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

HANDOFF_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HANDOFF_DIR))
sys.path.insert(
    0,
    str(
        HANDOFF_DIR.parents[1]
        / "40-certification-system/champion-challenger/p4-residual-thin-policy"
    ),
)

import aq_p4_policy as p4  # noqa: E402
import standing_policy as gate  # noqa: E402
import p12_research_handoff as handoff  # noqa: E402


class StandingResearchPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = p4.ResearchRequestV1.model_validate(
            handoff.create_synthetic_request()["research_request"]
        )
        self.policy = gate.create_synthetic_test_policy(self.request)
        self.now = datetime(2026, 10, 17, tzinfo=timezone.utc)
        self.evidence = gate.synthetic_admission_evidence(
            now=self.now,
            approval_source_identity=self.policy.approval_source_identity,
        )

    def evaluate(self, *, request=None, policy=None, evidence=None, fixture=True):
        return gate.evaluate_policy_admission(
            request or self.request,
            self.policy if policy is None else policy,
            p4_is_test_fixture=fixture,
            evidence=evidence or self.evidence,
        )["classification"]

    def policy_with(self, **updates):
        fields = self.policy.model_dump(mode="json", exclude={"policy_id"})
        fields.update(updates)
        fields["policy_id"] = gate.policy_identity(fields)
        return gate.P12StandingResearchPolicyV1.model_validate(fields)

    def test_valid_fixture_admits_synthetic_only_and_never_real(self) -> None:
        result = gate.evaluate_policy_admission(
            self.request,
            self.policy,
            p4_is_test_fixture=True,
            evidence=self.evidence,
        )
        self.assertEqual(result["classification"], "ADMITTED_SYNTHETIC_TEST_ONLY")
        self.assertEqual(result["real_dispatch_permission"], "DENIED")
        self.assertFalse(result["hard_worst_case_exposure_guarantee"])
        self.assertEqual(result["spending_enforcement"], "SIMULATED_ONLY_NOT_NATIVE_ENFORCEMENT")

    def test_human_approved_claim_without_trusted_source_is_denied(self) -> None:
        policy = self.policy_with(evidence_classification="HUMAN_APPROVED")
        self.assertEqual(self.evaluate(policy=policy), "DENIED_NO_TRUSTED_APPROVAL_SOURCE")

    def test_real_execution_mode_cannot_use_test_policy(self) -> None:
        evidence = self.evidence.__class__(**{**self.evidence.__dict__, "execution_mode": "REAL"})
        self.assertEqual(self.evaluate(evidence=evidence), "DENIED_TEST_ONLY_POLICY_CANNOT_AUTHORIZE_REAL")

    def test_expired_not_yet_effective_and_revoked_policies_are_denied(self) -> None:
        expired = gate.synthetic_admission_evidence(
            now=datetime(2031, 1, 1, tzinfo=timezone.utc),
            approval_source_identity=self.policy.approval_source_identity,
        )
        future = gate.synthetic_admission_evidence(
            now=datetime(2025, 1, 1, tzinfo=timezone.utc),
            approval_source_identity=self.policy.approval_source_identity,
        )
        revoked = gate.synthetic_admission_evidence(
            now=self.now,
            revocation_status="REVOKED",
            approval_source_identity=self.policy.approval_source_identity,
        )
        self.assertEqual(self.evaluate(evidence=expired), "DENIED_POLICY_EXPIRED")
        self.assertEqual(self.evaluate(evidence=future), "DENIED_POLICY_NOT_YET_EFFECTIVE")
        self.assertEqual(self.evaluate(evidence=revoked), "DENIED_POLICY_REVOKED")

    def test_policy_identity_tampering_is_denied(self) -> None:
        fields = self.policy.model_dump(mode="json")
        fields["maximum_run_spend_usd"] = "0.24"
        self.assertEqual(self.evaluate(policy=fields), "DENIED_POLICY_INVALID")

    def test_request_budget_identity_must_match_policy(self) -> None:
        request = SimpleNamespace(**self.request.model_dump())
        request.research_budget_identity = "sha256:" + "0" * 64
        self.assertEqual(self.evaluate(request=request), "DENIED_BUDGET_IDENTITY_MISMATCH")

    def test_scope_family_provenance_and_approval_source_are_bound(self) -> None:
        request = SimpleNamespace(**self.request.model_dump())
        request.allowed_research_families = ("RD_AGENT", "UNAPPROVED")
        self.assertEqual(self.evaluate(request=request), "DENIED_RESEARCH_FAMILY")
        unknown = gate.synthetic_admission_evidence(
            now=self.now,
            provenance_status="UNKNOWN",
            approval_source_identity=self.policy.approval_source_identity,
        )
        self.assertEqual(self.evaluate(evidence=unknown), "DENIED_REQUEST_PROVENANCE")
        wrong_approval = gate.synthetic_admission_evidence(now=self.now)
        self.assertEqual(self.evaluate(evidence=wrong_approval), "DENIED_APPROVAL_SOURCE_UNVERIFIED")

    def test_provider_spend_and_resource_limits_fail_closed(self) -> None:
        bad_route = gate.LLMRouteV1(provider="other", model="other/model", billing_class="PAID")
        self.assertEqual(
            self.evaluate(evidence=gate.synthetic_admission_evidence(
                now=self.now, approval_source_identity=self.policy.approval_source_identity,
                routes=(bad_route,),
            )),
            "DENIED_MODEL_PROVIDER",
        )
        self.assertEqual(
            self.evaluate(evidence=gate.synthetic_admission_evidence(
                now=self.now, approval_source_identity=self.policy.approval_source_identity,
                estimated_run_spend_usd=Decimal("0.26"),
            )),
            "DENIED_PER_RUN_SPEND_LIMIT",
        )
        self.assertEqual(
            self.evaluate(evidence=gate.synthetic_admission_evidence(
                now=self.now, approval_source_identity=self.policy.approval_source_identity,
                spending_authority_status="UNAVAILABLE",
            )),
            "DENIED_SPENDING_AUTHORITY_UNAVAILABLE",
        )
        self.assertEqual(
            self.evaluate(evidence=gate.synthetic_admission_evidence(
                now=self.now, approval_source_identity=self.policy.approval_source_identity,
                active_run_count=1,
            )),
            "DENIED_CONCURRENCY_LIMIT",
        )
        self.assertEqual(
            self.evaluate(evidence=gate.synthetic_admission_evidence(
                now=self.now, approval_source_identity=self.policy.approval_source_identity,
                runtime_seconds=301,
            )),
            "DENIED_RESOURCE_LIMIT",
        )

    def test_budget_period_and_unknown_cost_are_denied(self) -> None:
        self.assertEqual(
            self.evaluate(evidence=gate.synthetic_admission_evidence(
                now=self.now, approval_source_identity=self.policy.approval_source_identity,
                period_spend_usd=Decimal("0.80"),
                estimated_run_spend_usd=Decimal("0.25"),
            )),
            "DENIED_PERIOD_SPEND_LIMIT",
        )
        self.assertEqual(
            self.evaluate(evidence=gate.synthetic_admission_evidence(
                now=self.now, approval_source_identity=self.policy.approval_source_identity,
                estimated_run_spend_usd=None,
            )),
            "DENIED_SPEND_UNKNOWN",
        )


if __name__ == "__main__":
    unittest.main()
