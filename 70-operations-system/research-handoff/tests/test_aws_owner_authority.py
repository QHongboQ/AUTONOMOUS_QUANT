from __future__ import annotations

import copy
import base64
import hashlib
import sys
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import rfc8785
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

HANDOFF_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HANDOFF_DIR))
sys.path.insert(
    0,
    str(
        HANDOFF_DIR.parents[1]
        / "40-certification-system/champion-challenger/p4-residual-thin-policy"
    ),
)

import aq_p4_policy  # noqa: E402
import aws_owner_authority as cloud  # noqa: E402
import owner_signed_authority  # noqa: E402
import p12_research_handoff as handoff  # noqa: E402
import standing_policy  # noqa: E402
from native_experiment_budget import BudgetBoundaryDenied, NativeExperimentBudgetController  # noqa: E402


NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
KMS_ARN = "arn:aws:kms:us-east-1:123456789012:key/test-ed25519"
OWNER_ROLE = "arn:aws:iam::123456789012:role/AQResearchOwner"


def digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def approved_fixture():
    envelope = handoff.create_synthetic_request()
    request = aq_p4_policy.ResearchRequestV1.model_validate(envelope["research_request"])
    base = standing_policy.create_synthetic_test_policy(request)
    policy = base.model_copy(
        update={
            "evidence_classification": "HUMAN_APPROVED",
            "approval_record_identity": digest("owner-approved-record:" + request.research_budget_identity),
            "effective_at": NOW - timedelta(minutes=1),
            "expires_at": NOW + timedelta(hours=23, minutes=59),
            "maximum_period_spend_usd": Decimal("5.00"),
            "maximum_run_spend_usd": Decimal("5.00"),
            "maximum_concurrent_runs": 1,
            "allowed_universe_scope_identities": (request.asset_universe_scope_identity,),
            "allowed_request_provenance_identities": (request.request_provenance,),
            "allowed_research_families": tuple(request.allowed_research_families),
            "allowed_llm_routes": (
                standing_policy.LLMRouteV1(
                    provider="deepseek", model="deepseek/deepseek-flash", billing_class="PAID"
                ),
                standing_policy.LLMRouteV1(
                    provider="ollama", model="ollama/qwen3-embedding:0.6b", billing_class="LOCAL"
                ),
            ),
        }
    )
    policy_fields = policy.model_dump(mode="json", exclude={"policy_id"})
    return request, policy.model_copy(update={"policy_id": standing_policy.policy_identity(policy_fields)})


class FakeKms:
    def __init__(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.key_id = KMS_ARN
        self.calls = []

    def get_public_key(self, *, KeyId):
        self.calls.append(("GetPublicKey", KeyId))
        public = self.private_key.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return {
            "KeyId": self.key_id,
            "KeySpec": cloud.KEY_SPEC,
            "KeyUsage": cloud.KEY_USAGE,
            "SigningAlgorithms": [cloud.SIGNING_ALGORITHM],
            "PublicKey": public,
        }

    def sign(self, *, KeyId, Message, MessageType, SigningAlgorithm):
        self.calls.append(("Sign", KeyId))
        if KeyId != self.key_id or MessageType != "RAW" or SigningAlgorithm != cloud.SIGNING_ALGORITHM:
            raise ValueError("wrong KMS parameters")
        return {
            "KeyId": self.key_id,
            "SigningAlgorithm": cloud.SIGNING_ALGORITHM,
            "Signature": self.private_key.sign(Message),
        }


class FakeTable:
    def __init__(self):
        self.items = {}
        self.calls = []
        self.fail_next_update = False

    def get_item(self, *, Key, ConsistentRead):
        self.calls.append(("GetItem", ConsistentRead))
        if ConsistentRead is not True:
            raise AssertionError("authority reads must be strongly consistent")
        identity = Key[cloud.APPROVAL_KEY]
        row = self.items.get(identity)
        return {} if row is None else {"Item": copy.deepcopy(row)}

    def put_item(self, *, Item, ConditionExpression):
        self.calls.append(("PutItem", ConditionExpression))
        identity = Item[cloud.APPROVAL_KEY]
        if ConditionExpression != "attribute_not_exists(research_budget_identity)" or identity in self.items:
            raise RuntimeError("conditional put failed")
        self.items[identity] = copy.deepcopy(Item)
        return {}

    def update_item(self, *, Key, UpdateExpression, ConditionExpression, ExpressionAttributeValues):
        self.calls.append(("UpdateItem", ConditionExpression))
        identity = Key[cloud.APPROVAL_KEY]
        row = self.items.get(identity)
        values = ExpressionAttributeValues
        if self.fail_next_update:
            self.fail_next_update = False
            raise RuntimeError("simulated conditional epoch race")
        if (
            row is None
            or row.get("authority_epoch") != values[":expected"]
            or row.get("current_status") != values[":approved"]
            or row.get(cloud.APPROVAL_KEY) != values[":identity"]
            or "SET authority_epoch = :next" not in UpdateExpression
        ):
            raise RuntimeError("conditional update failed")
        row["authority_epoch"] = values[":next"]
        row["current_status"] = values[":revoked"]
        row["revocation_snapshot"] = values[":snapshot"]
        row["updated_at"] = values[":updated"]
        return {"Attributes": copy.deepcopy(row)}


class FakeSts:
    def __init__(self, arn="arn:aws:sts::123456789012:assumed-role/AQResearchOwner/session"):
        self.arn = arn

    def get_caller_identity(self):
        account = self.arn.split(":")[4]
        return {"Account": account, "Arn": self.arn}


class FakeNativeApi:
    def __init__(self):
        self.calls = []

    def request(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class AwsOwnerAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.request, self.policy = approved_fixture()
        self.table = FakeTable()
        self.kms = FakeKms()
        self.sts = FakeSts()
        self.writer = cloud.OwnerAuthorityWriter(
            self.table, self.kms, self.sts,
            kms_key_arn=KMS_ARN, owner_role_arn=OWNER_ROLE, now=lambda: NOW,
        )
        self.source = cloud.RuntimeAuthoritySource(
            self.table, self.kms, expected_kms_key_arn=KMS_ARN, now=lambda: NOW
        )

    def approve(self):
        return self.writer.approve(
            self.request, self.policy, confirm_owner_approval=True
        )

    def test_valid_owner_approval_is_signed_and_read_from_current_epoch(self):
        created = self.approve()
        self.assertEqual(created["authority_epoch"], 1)
        result = self.source.verify_current(self.request, self.policy)
        self.assertEqual(result["classification"], "OWNER_AUTHORITY_VERIFIED_CURRENT")
        self.assertEqual(result["native_experiment_user_id"], handoff.experiment_user_id(self.request.research_budget_identity))
        self.assertEqual(result["real_dispatch_permission"], "DENIED")
        self.assertIn(("GetItem", True), self.table.calls)

    def test_owner_writer_requires_explicit_authenticated_confirmation(self):
        with self.assertRaisesRegex(cloud.AuthorityDenied, "CONFIRMATION_REQUIRED"):
            self.writer.approve(self.request, self.policy, confirm_owner_approval=False)
        self.assertFalse(self.table.items)
        bad_sts = FakeSts("arn:aws:sts::123456789012:assumed-role/AQResearchRuntime/session")
        writer = cloud.OwnerAuthorityWriter(
            self.table, self.kms, bad_sts,
            kms_key_arn=KMS_ARN, owner_role_arn=OWNER_ROLE, now=lambda: NOW,
        )
        with self.assertRaisesRegex(cloud.AuthorityDenied, "OWNER_AUTHENTICATION"):
            writer.approve(self.request, self.policy, confirm_owner_approval=True)

    def test_reapproval_cannot_allocate_a_second_experiment_budget(self):
        self.approve()
        with self.assertRaisesRegex(cloud.AuthorityDenied, "ALREADY_EXISTS"):
            self.approve()
        self.assertEqual(len([call for call in self.table.calls if call[0] == "PutItem"]), 1)

    def test_revoked_approval_is_denied_by_current_signed_snapshot(self):
        self.approve()
        revoked = self.writer.revoke(
            self.request.research_budget_identity,
            self.policy.approval_record_identity,
            expected_epoch=1,
        )
        self.assertEqual(revoked["authority_epoch"], 2)
        result = self.source.verify_current(self.request, self.policy)
        self.assertEqual(result["classification"], "DENIED_POLICY_REVOKED")

    def test_expired_approval_is_denied(self):
        self.approve()
        self.source._now = lambda: NOW + timedelta(hours=24)
        result = self.source.verify_current(self.request, self.policy)
        self.assertEqual(result["classification"], "DENIED_POLICY_EXPIRED")

    def test_old_snapshot_and_advanced_epoch_fail_closed(self):
        self.approve()
        row = self.table.items[self.request.research_budget_identity]
        row["authority_epoch"] = 2
        result = self.source.verify_current(self.request, self.policy)
        self.assertEqual(result["classification"], "DENIED_AUTHORITY_ROLLBACK")

    def test_stale_approval_is_denied_when_authority_epoch_advances(self):
        self.approve()
        row = self.table.items[self.request.research_budget_identity]
        old_ids = []
        snapshot_payload = cloud._revocation_payload(
            row["approval"]["payload"]["signing_key_id"], 2, old_ids
        )
        row["authority_epoch"] = 2
        row["revocation_snapshot"] = cloud._sign_payload(self.kms, KMS_ARN, snapshot_payload)
        result = self.source.verify_current(self.request, self.policy)
        self.assertEqual(result["classification"], "DENIED_OLD_AUTHORIZATION_REPLAY")

    def test_wrong_kms_identity_and_missing_or_unavailable_authority_are_denied(self):
        self.approve()
        self.kms.key_id = "arn:aws:kms:us-east-1:123456789012:key/wrong"
        result = self.source.verify_current(self.request, self.policy)
        self.assertEqual(result["classification"], "DENIED_KMS_KEY_IDENTITY_OR_ALGORITHM")
        missing = cloud.RuntimeAuthoritySource(
            FakeTable(), self.kms, expected_kms_key_arn=KMS_ARN, now=lambda: NOW
        ).verify_current(self.request, self.policy)
        self.assertEqual(missing["classification"], "DENIED_AUTHORITY_MISSING")

        class UnavailableTable(FakeTable):
            def get_item(self, **kwargs):
                raise OSError("simulated AWS unavailable")

        unavailable = cloud.RuntimeAuthoritySource(
            UnavailableTable(), self.kms, expected_kms_key_arn=KMS_ARN, now=lambda: NOW
        ).verify_current(self.request, self.policy)
        self.assertEqual(unavailable["classification"], "DENIED_AWS_AUTHORITY_UNAVAILABLE")

    def test_experiment_identity_and_native_user_binding_must_match(self):
        self.approve()
        row = self.table.items[self.request.research_budget_identity]
        row["native_experiment_user_id"] = "aq-p12-exp-other"
        result = self.source.verify_current(self.request, self.policy)
        self.assertEqual(result["classification"], "DENIED_AUTHORITY_EXPERIMENT_BINDING_MISMATCH")

    def test_conditional_epoch_write_rejects_race_and_keeps_old_state(self):
        self.approve()
        self.table.fail_next_update = True
        with self.assertRaisesRegex(cloud.AuthorityDenied, "CONDITIONAL_EPOCH_UPDATE"):
            self.writer.revoke(
                self.request.research_budget_identity,
                self.policy.approval_record_identity,
                expected_epoch=1,
            )
        self.assertEqual(self.table.items[self.request.research_budget_identity]["authority_epoch"], 1)
        update_call = next(call for call in self.table.calls if call[0] == "UpdateItem")
        self.assertIn("authority_epoch = :expected", update_call[1])

    def test_runtime_adapter_has_read_only_surface_and_never_signs_or_writes(self):
        self.approve()
        before_table = len(self.table.calls)
        before_kms = len(self.kms.calls)
        self.source.verify_current(self.request, self.policy)
        self.assertEqual([x[0] for x in self.table.calls[before_table:]], ["GetItem"])
        self.assertEqual([x[0] for x in self.kms.calls[before_kms:]], ["GetPublicKey"])
        self.assertFalse(hasattr(self.source, "approve"))
        self.assertFalse(hasattr(self.source, "revoke"))

    def test_verified_owner_approval_does_not_enable_p12_dispatch(self):
        self.approve()
        row = self.table.items[self.request.research_budget_identity]
        raw_public, key_id = cloud._kms_public_identity(self.kms, KMS_ARN)
        result = standing_policy.evaluate_policy_admission(
            self.request,
            self.policy,
            p4_is_test_fixture=False,
            evidence=standing_policy.synthetic_admission_evidence(),
            signed_approval=row["approval"],
            trusted_authority={
                "trusted_public_key_b64": base64.b64encode(raw_public).decode(),
                "trusted_key_id": key_id,
                "revocation_snapshot": row["revocation_snapshot"],
                "minimum_trusted_epoch": row["authority_epoch"],
                "trusted_source_available": True,
            },
        )
        self.assertEqual(result["classification"], "DENIED_OWNER_AUTHORITY_NOT_WIRED_TO_REAL_DISPATCH")
        self.assertEqual(result["real_dispatch_permission"], "DENIED")

    def test_p12_replay_cannot_issue_another_paid_key(self):
        self.approve()
        api = FakeNativeApi()
        controller = NativeExperimentBudgetController(api)
        with self.assertRaisesRegex(BudgetBoundaryDenied, "OWNER_AUTHORIZATION_UNVERIFIED"):
            controller.issue_real_key(
                owner_authorization=self.source.verify_current(self.request, self.policy)
            )
        self.assertEqual(api.calls, [])


if __name__ == "__main__":
    unittest.main()
