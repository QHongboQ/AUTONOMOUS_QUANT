"""P12-specific Ed25519 verification for signed research-policy evidence.

This module verifies signatures only. It does not create approval records,
provide a trusted authority source, enforce spending, or grant real dispatch.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
from datetime import datetime, timezone
from typing import Any

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

APPROVAL_DOMAIN = "AUTONOMOUS_QUANT:P12:RESEARCH_POLICY_APPROVAL:V1"
APPROVAL_PURPOSE = "AUTHORIZE_RESEARCH_REQUEST"
REVOCATION_DOMAIN = "AUTONOMOUS_QUANT:P12:RESEARCH_POLICY_REVOCATION:V1"

_APPROVAL_FIELDS = {
    "domain",
    "purpose",
    "signing_key_id",
    "owner_approval_evidence_identity",
    "policy_version",
    "policy_id",
    "effective_at",
    "expires_at",
    "allowed_universe_scope_identities",
    "allowed_request_provenance_identities",
    "allowed_research_families",
    "research_budget_identity",
    "authority_epoch",
    "evidence_classification",
}


def _result(classification: str, **details: Any) -> dict[str, Any]:
    return {"classification": classification, "real_dispatch_permission": "DENIED", **details}


def _decode_b64(value: Any, expected_size: int) -> bytes:
    if not isinstance(value, str):
        raise ValueError("base64 value required")
    decoded = base64.b64decode(value, validate=True)
    if len(decoded) != expected_size:
        raise ValueError("unexpected decoded length")
    return decoded


def _aware_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return parsed.astimezone(timezone.utc)


def verify_signed_research_policy(
    approval: Any,
    policy: Any,
    request: Any,
    *,
    trusted_public_key_b64: str | None,
    trusted_key_id: str | None,
    revocation_snapshot: Any,
    minimum_trusted_epoch: int | None,
    trusted_source_available: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify a P12 policy signature and testable revocation/epoch evidence.

    ``minimum_trusted_epoch`` must come from independent owner-controlled
    monotonic state. Passing no floor, or an unavailable source, fails closed.
    A valid TEST_ONLY signature is evidence integrity only and can never grant
    real research permission.
    """
    if not trusted_source_available:
        return _result("DENIED_TRUSTED_SOURCE_UNAVAILABLE")
    if minimum_trusted_epoch is None:
        return _result("DENIED_ROLLBACK_AUTHORITY_MISSING")
    if not isinstance(minimum_trusted_epoch, int) or minimum_trusted_epoch < 0:
        return _result("DENIED_TRUSTED_EPOCH_INVALID")
    if not isinstance(approval, dict) or set(approval) != {"payload", "signature"}:
        return _result("DENIED_APPROVAL_MALFORMED")
    payload = approval["payload"]
    if not isinstance(payload, dict) or set(payload) != _APPROVAL_FIELDS:
        return _result("DENIED_APPROVAL_MALFORMED")
    if not isinstance(revocation_snapshot, dict) or set(revocation_snapshot) != {
        "payload",
        "signature",
    }:
        return _result("DENIED_REVOCATION_AUTHORITY_MISSING")
    snapshot = revocation_snapshot["payload"]
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "domain",
        "signing_key_id",
        "authority_epoch",
        "revoked_approval_evidence_identities",
    }:
        return _result("DENIED_REVOCATION_AUTHORITY_INVALID")
    if not isinstance(trusted_public_key_b64, str) or not isinstance(trusted_key_id, str):
        return _result("DENIED_TRUSTED_PUBLIC_KEY_MISSING")
    if payload["signing_key_id"] != trusted_key_id or snapshot["signing_key_id"] != trusted_key_id:
        return _result("DENIED_SIGNING_KEY_ID_MISMATCH")
    if payload["domain"] != APPROVAL_DOMAIN or payload["purpose"] != APPROVAL_PURPOSE:
        return _result("DENIED_APPROVAL_PURPOSE_OR_DOMAIN")
    if snapshot["domain"] != REVOCATION_DOMAIN:
        return _result("DENIED_REVOCATION_DOMAIN")

    try:
        public_key_bytes = _decode_b64(trusted_public_key_b64, 32)
        if trusted_key_id != "sha256:" + hashlib.sha256(public_key_bytes).hexdigest():
            return _result("DENIED_TRUSTED_PUBLIC_KEY_ID_MISMATCH")
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(
            _decode_b64(approval["signature"], 64), rfc8785.dumps(payload)
        )
        public_key.verify(
            _decode_b64(revocation_snapshot["signature"], 64), rfc8785.dumps(snapshot)
        )
    except (InvalidSignature, ValueError, TypeError, binascii.Error):
        return _result("DENIED_SIGNATURE_INVALID")

    epoch = payload["authority_epoch"]
    source_epoch = snapshot["authority_epoch"]
    if not isinstance(epoch, int) or not isinstance(source_epoch, int) or epoch < 0 or source_epoch < 0:
        return _result("DENIED_TRUSTED_EPOCH_INVALID")
    if source_epoch < minimum_trusted_epoch:
        return _result("DENIED_AUTHORITY_ROLLBACK")
    evidence_id = payload["owner_approval_evidence_identity"]
    revoked = snapshot["revoked_approval_evidence_identities"]
    if not isinstance(revoked, list) or any(not isinstance(item, str) for item in revoked):
        return _result("DENIED_REVOCATION_AUTHORITY_INVALID")
    if evidence_id in revoked:
        return _result("DENIED_POLICY_REVOKED")
    if epoch < minimum_trusted_epoch or epoch < source_epoch:
        return _result("DENIED_OLD_AUTHORIZATION_REPLAY")
    if epoch != source_epoch:
        return _result("DENIED_AUTHORITY_EPOCH_MISMATCH")
    try:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        effective_at = _aware_datetime(payload["effective_at"])
        expires_at = _aware_datetime(payload["expires_at"])
    except (ValueError, TypeError, OverflowError):
        return _result("DENIED_APPROVAL_TIME_INVALID")
    if current < effective_at:
        return _result("DENIED_POLICY_NOT_YET_EFFECTIVE")
    if current >= expires_at:
        return _result("DENIED_POLICY_EXPIRED")

    expected = {
        "owner_approval_evidence_identity": policy.approval_record_identity,
        "policy_id": policy.policy_id,
        "effective_at": policy.effective_at.isoformat().replace("+00:00", "Z"),
        "expires_at": policy.expires_at.isoformat().replace("+00:00", "Z"),
        "allowed_universe_scope_identities": list(policy.allowed_universe_scope_identities),
        "allowed_request_provenance_identities": list(policy.allowed_request_provenance_identities),
        "allowed_research_families": list(policy.allowed_research_families),
        "research_budget_identity": policy.research_budget_identity,
    }
    policy_fields = policy.model_dump(mode="json", exclude={"policy_id"})
    recomputed_policy_id = "sha256:" + hashlib.sha256(rfc8785.dumps(policy_fields)).hexdigest()
    if policy.policy_id != recomputed_policy_id:
        return _result("DENIED_POLICY_INVALID")
    if any(payload[field] != value for field, value in expected.items()):
        return _result("DENIED_SIGNED_POLICY_MISMATCH")
    if (
        payload["policy_version"] != "P12StandingResearchPolicyV1"
        or payload["evidence_classification"] != "TEST_ONLY"
    ):
        return _result("DENIED_POLICY_CLASSIFICATION")
    if request.asset_universe_scope_identity not in payload["allowed_universe_scope_identities"]:
        return _result("DENIED_RESEARCH_UNIVERSE")
    if request.request_provenance not in payload["allowed_request_provenance_identities"]:
        return _result("DENIED_REQUEST_PROVENANCE")
    if request.research_budget_identity != payload["research_budget_identity"]:
        return _result("DENIED_BUDGET_IDENTITY_MISMATCH")
    if not set(request.allowed_research_families).issubset(payload["allowed_research_families"]):
        return _result("DENIED_RESEARCH_FAMILY")
    return _result(
        "VERIFIED_TEST_ONLY_SIGNATURE",
        policy_id=policy.policy_id,
        owner_approval_evidence_identity=evidence_id,
        signing_key_id=payload["signing_key_id"],
        authority_epoch=epoch,
        signed_payload_sha256="sha256:" + hashlib.sha256(rfc8785.dumps(payload)).hexdigest(),
        signed_approval_fingerprint="sha256:"
        + hashlib.sha256(rfc8785.dumps(approval)).hexdigest(),
        cryptographic_integrity="VERIFIED_TEST_ONLY",
    )
