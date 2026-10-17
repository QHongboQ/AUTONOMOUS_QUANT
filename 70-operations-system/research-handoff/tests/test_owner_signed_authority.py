"""TEST_ONLY Ed25519 authority-boundary checks; no real authorization fixtures."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

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

import aq_p4_policy as p4  # noqa: E402
import owner_signed_authority as authority  # noqa: E402
import p12_research_handoff as handoff  # noqa: E402
import standing_policy as policy_gate  # noqa: E402

_DEFAULT = object()


class OwnerSignedAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ephemeral process-local TEST_ONLY key; never serialized to disk.
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        raw_public_key = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.key_id = "sha256:" + hashlib.sha256(raw_public_key).hexdigest()
        self.request = p4.ResearchRequestV1.model_validate(
            handoff.create_synthetic_request()["research_request"]
        )
        self.policy = policy_gate.create_synthetic_test_policy(self.request)
        self.now = datetime(2026, 10, 17, tzinfo=timezone.utc)
        self.approval_id = self.policy.approval_record_identity
        self.epoch = 4
        self.payload = {
            "domain": authority.APPROVAL_DOMAIN,
            "purpose": authority.APPROVAL_PURPOSE,
            "signing_key_id": self.key_id,
            "owner_approval_evidence_identity": self.approval_id,
            "policy_version": "P12StandingResearchPolicyV1",
            "policy_id": self.policy.policy_id,
            "effective_at": self.policy.effective_at.isoformat().replace("+00:00", "Z"),
            "expires_at": self.policy.expires_at.isoformat().replace("+00:00", "Z"),
            "allowed_universe_scope_identities": list(self.policy.allowed_universe_scope_identities),
            "allowed_request_provenance_identities": list(
                self.policy.allowed_request_provenance_identities
            ),
            "allowed_research_families": list(self.policy.allowed_research_families),
            "research_budget_identity": self.policy.research_budget_identity,
            "authority_epoch": self.epoch,
            "evidence_classification": "TEST_ONLY",
        }
        self.snapshot = {
            "domain": authority.REVOCATION_DOMAIN,
            "signing_key_id": self.key_id,
            "authority_epoch": self.epoch,
            "revoked_approval_evidence_identities": [],
        }

    def signed(self, value):
        return {
            "payload": value,
            "signature": base64.b64encode(self.private_key.sign(rfc8785.dumps(value))).decode("ascii"),
        }

    def signed_approval(self, payload=None):
        return self.signed(self.payload if payload is None else payload)

    def signed_snapshot(self, payload=None):
        return self.signed(self.snapshot if payload is None else payload)

    def verify(self, *, approval=None, policy=None, request=None, snapshot=_DEFAULT,
               minimum_epoch=4, source_available=True, public_key=None, key_id=None):
        raw_public = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return authority.verify_signed_research_policy(
            approval if approval is not None else self.signed_approval(),
            policy if policy is not None else self.policy,
            request if request is not None else self.request,
            trusted_public_key_b64=(
                base64.b64encode(raw_public).decode("ascii") if public_key is None else public_key
            ),
            trusted_key_id=self.key_id if key_id is None else key_id,
            revocation_snapshot=self.signed_snapshot() if snapshot is _DEFAULT else snapshot,
            minimum_trusted_epoch=minimum_epoch,
            trusted_source_available=source_available,
            now=self.now,
        )

    def test_valid_test_only_signature_never_grants_real_dispatch(self):
        result = self.verify()
        self.assertEqual(result["classification"], "VERIFIED_TEST_ONLY_SIGNATURE")
        self.assertEqual(result["real_dispatch_permission"], "DENIED")

    def test_p12_admission_gate_requires_and_reports_test_only_verification(self):
        raw_public = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        trust = {
            "trusted_public_key_b64": base64.b64encode(raw_public).decode("ascii"),
            "trusted_key_id": self.key_id,
            "revocation_snapshot": self.signed_snapshot(),
            "minimum_trusted_epoch": self.epoch,
            "trusted_source_available": True,
        }
        evidence = policy_gate.synthetic_admission_evidence(
            now=self.now,
            approval_source_identity=self.policy.approval_source_identity,
        )
        result = policy_gate.evaluate_policy_admission(
            self.request,
            self.policy,
            p4_is_test_fixture=True,
            evidence=evidence,
            signed_approval=self.signed_approval(),
            trusted_authority=trust,
        )
        self.assertEqual(result["classification"], "ADMITTED_SYNTHETIC_TEST_ONLY")
        self.assertEqual(
            result["policy_signature_verification"], "VERIFIED_TEST_ONLY_SIGNATURE"
        )
        self.assertEqual(result["real_dispatch_permission"], "DENIED")

        trust["minimum_trusted_epoch"] = None
        denied = policy_gate.evaluate_policy_admission(
            self.request,
            self.policy,
            p4_is_test_fixture=True,
            evidence=evidence,
            signed_approval=self.signed_approval(),
            trusted_authority=trust,
        )
        self.assertEqual(denied["classification"], "DENIED_ROLLBACK_AUTHORITY_MISSING")

    def test_signed_test_only_policy_flows_through_durable_synthetic_handoff_once(self):
        raw_public = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        trust = {
            "trusted_public_key_b64": base64.b64encode(raw_public).decode("ascii"),
            "trusted_key_id": self.key_id,
            "revocation_snapshot": self.signed_snapshot(),
            "minimum_trusted_epoch": self.epoch,
            "trusted_source_available": True,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path = root / "request.json"
            policy_path = root / "policy.json"
            state_path = root / "state"
            request_path.write_text(json.dumps(handoff.create_synthetic_request()), encoding="utf-8")
            policy_path.write_text(
                json.dumps(self.policy.model_dump(mode="json")), encoding="utf-8"
            )
            first, first_exit = handoff.process_synthetic_request(
                request_path,
                state_path,
                policy_path,
                signed_approval=self.signed_approval(),
                trusted_authority=trust,
            )
            replay, replay_exit = handoff.process_synthetic_request(
                request_path,
                state_path,
                policy_path,
                signed_approval=self.signed_approval(),
                trusted_authority=trust,
            )
            self.assertEqual(first_exit, 0)
            self.assertEqual(first["status"]["policy_signature_verification"], "VERIFIED_TEST_ONLY_SIGNATURE")
            self.assertEqual(first["status"]["real_dispatch_permission"], "DENIED")
            self.assertEqual(replay_exit, 0)
            self.assertEqual(replay["classification"], "REPLAY_TERMINAL_NO_DISPATCH")
            self.assertEqual(replay["dispatch_count_added"], 0)
            self.assertEqual(len(list(state_path.glob("*.dispatch.jsonl"))), 1)

            stale_trust = dict(trust)
            stale_trust["minimum_trusted_epoch"] = self.epoch + 1
            newer_snapshot = dict(self.snapshot)
            newer_snapshot["authority_epoch"] = self.epoch + 1
            stale_trust["revocation_snapshot"] = self.signed_snapshot(newer_snapshot)
            blocked, blocked_exit = handoff.process_synthetic_request(
                request_path,
                state_path,
                policy_path,
                signed_approval=self.signed_approval(),
                trusted_authority=stale_trust,
            )
            self.assertEqual(blocked_exit, 3)
            self.assertEqual(blocked["classification"], "DENIED_OLD_AUTHORIZATION_REPLAY")
            self.assertEqual(len(list(state_path.glob("*.dispatch.jsonl"))), 1)

    def test_invalid_signature_and_wrong_trusted_key_are_denied(self):
        invalid = self.signed_approval()
        invalid["signature"] = base64.b64encode(b"x" * 64).decode("ascii")
        self.assertEqual(self.verify(approval=invalid)["classification"], "DENIED_SIGNATURE_INVALID")
        other_key = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.assertEqual(
            self.verify(public_key=base64.b64encode(other_key).decode("ascii"))["classification"],
            "DENIED_TRUSTED_PUBLIC_KEY_ID_MISMATCH",
        )

    def test_modified_or_different_policy_after_signing_is_denied(self):
        changed_fields = self.policy.model_dump(mode="json", exclude={"policy_id"})
        changed_fields["maximum_run_spend_usd"] = "0.12"
        changed_fields["policy_id"] = policy_gate.policy_identity(changed_fields)
        changed = policy_gate.P12StandingResearchPolicyV1.model_validate(changed_fields)
        self.assertEqual(self.verify(policy=changed)["classification"], "DENIED_SIGNED_POLICY_MISMATCH")
        changed_payload = dict(self.payload)
        changed_payload["research_budget_identity"] = "sha256:" + "c" * 64
        self.assertEqual(
            self.verify(approval=self.signed_approval(changed_payload))["classification"],
            "DENIED_SIGNED_POLICY_MISMATCH",
        )

    def test_purpose_domain_and_key_identity_are_bound(self):
        payload = dict(self.payload)
        payload["purpose"] = "AUTHORIZE_BROKER_TRADING"
        self.assertEqual(
            self.verify(approval=self.signed_approval(payload))["classification"],
            "DENIED_APPROVAL_PURPOSE_OR_DOMAIN",
        )
        self.assertEqual(
            self.verify(key_id="sha256:" + "d" * 64)["classification"],
            "DENIED_SIGNING_KEY_ID_MISMATCH",
        )

    def test_expired_and_future_effective_approvals_are_denied(self):
        expired = dict(self.payload)
        expired.update(effective_at="2020-01-01T00:00:00Z", expires_at="2021-01-01T00:00:00Z")
        future = dict(self.payload)
        future["effective_at"] = "2030-01-01T00:00:00Z"
        self.assertEqual(self.verify(approval=self.signed_approval(expired))["classification"], "DENIED_POLICY_EXPIRED")
        self.assertEqual(
            self.verify(approval=self.signed_approval(future))["classification"],
            "DENIED_POLICY_NOT_YET_EFFECTIVE",
        )

    def test_revoked_approval_and_missing_or_unavailable_source_are_denied(self):
        revoked = dict(self.snapshot)
        revoked["revoked_approval_evidence_identities"] = [self.approval_id]
        self.assertEqual(
            self.verify(snapshot=self.signed_snapshot(revoked))["classification"],
            "DENIED_POLICY_REVOKED",
        )
        self.assertEqual(
            self.verify(snapshot=None)["classification"],
            "DENIED_REVOCATION_AUTHORITY_MISSING",
        )
        self.assertEqual(
            self.verify(minimum_epoch=None)["classification"],
            "DENIED_ROLLBACK_AUTHORITY_MISSING",
        )
        self.assertEqual(
            self.verify(source_available=False)["classification"],
            "DENIED_TRUSTED_SOURCE_UNAVAILABLE",
        )

    def test_older_authorization_replay_and_rolled_back_snapshot_are_denied(self):
        old = dict(self.payload)
        old["authority_epoch"] = 3
        self.assertEqual(
            self.verify(approval=self.signed_approval(old))["classification"],
            "DENIED_OLD_AUTHORIZATION_REPLAY",
        )
        rolled_back = dict(self.snapshot)
        rolled_back["authority_epoch"] = 3
        self.assertEqual(
            self.verify(snapshot=self.signed_snapshot(rolled_back))["classification"],
            "DENIED_AUTHORITY_ROLLBACK",
        )

    def test_incorrect_request_provenance_and_budget_identity_are_denied(self):
        wrong_provenance = SimpleNamespace(**self.request.model_dump())
        wrong_provenance.request_provenance = "sha256:" + "e" * 64
        self.assertEqual(
            self.verify(request=wrong_provenance)["classification"],
            "DENIED_REQUEST_PROVENANCE",
        )
        wrong_budget = SimpleNamespace(**self.request.model_dump())
        wrong_budget.research_budget_identity = "sha256:" + "f" * 64
        self.assertEqual(
            self.verify(request=wrong_budget)["classification"],
            "DENIED_BUDGET_IDENTITY_MISMATCH",
        )

    def test_valid_signature_is_reusable_only_for_unchanged_current_evidence(self):
        signature = self.signed_approval()
        self.assertEqual(self.verify(approval=signature)["classification"], "VERIFIED_TEST_ONLY_SIGNATURE")
        self.assertEqual(self.verify(approval=signature)["classification"], "VERIFIED_TEST_ONLY_SIGNATURE")
        later_snapshot = dict(self.snapshot)
        later_snapshot["authority_epoch"] = 5
        self.assertEqual(
            self.verify(approval=signature, snapshot=self.signed_snapshot(later_snapshot), minimum_epoch=5)[
                "classification"
            ],
            "DENIED_OLD_AUTHORIZATION_REPLAY",
        )


if __name__ == "__main__":
    unittest.main()
