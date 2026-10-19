"""Thin AWS KMS/DynamoDB source for P12 owner research approvals.

The module uses boto3 clients/resources supplied by the caller. The owner
writer signs only through KMS; the runtime source only reads DynamoDB and the
KMS public key. Verification never grants P12 real dispatch.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

HANDOFF_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HANDOFF_DIR / "docker-rdagent-smoke"))
sys.path.insert(
    0,
    str(
        HANDOFF_DIR.parents[1]
        / "40-certification-system/champion-challenger/p4-residual-thin-policy"
    ),
)

import rfc8785
from cryptography.hazmat.primitives import serialization

import aq_p4_policy
import owner_signed_authority
import standing_policy
from native_experiment_budget import experiment_user_id


AUTHORITY_KIND = "AQ_P12_RESEARCH_APPROVAL_V1"
APPROVAL_KEY = "research_budget_identity"
KEY_SPEC = "ECC_NIST_EDWARDS25519"
KEY_USAGE = "SIGN_VERIFY"
SIGNING_ALGORITHM = "ED25519_SHA_512"
ALLOWED_ROUTES = frozenset(
    {
        ("deepseek", "deepseek/deepseek-flash", "PAID"),
        ("ollama", "ollama/qwen3-embedding:0.6b", "LOCAL"),
    }
)
OWNER_TOTAL_USD = Decimal("5.00")
MAX_AUTHORIZATION_LIFETIME = timedelta(hours=24)
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class AuthorityDenied(RuntimeError):
    def __init__(self, classification: str):
        super().__init__(classification)
        self.classification = classification


def _identity(value: Any) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise AuthorityDenied("DENIED_EXPERIMENT_IDENTITY_INVALID")
    return value


def _policy_mapping(policy: Any) -> dict[str, Any]:
    if isinstance(policy, standing_policy.P12StandingResearchPolicyV1):
        return policy.model_dump(mode="json")
    if isinstance(policy, dict):
        return policy
    raise AuthorityDenied("DENIED_POLICY_INVALID")


def _request_mapping(request: Any) -> dict[str, Any]:
    if isinstance(request, dict):
        return request
    if hasattr(request, "model_dump"):
        value = request.model_dump(mode="json")
        if isinstance(value, dict):
            return value
    raise AuthorityDenied("DENIED_REQUEST_INVALID")


def _policy_and_request(policy_value: Any, request_value: Any):
    try:
        policy = standing_policy.P12StandingResearchPolicyV1.model_validate(
            _policy_mapping(policy_value)
        )
        request = request_value
        if not hasattr(request, "research_budget_identity"):
            request = aq_p4_policy.ResearchRequestV1.model_validate(
                _request_mapping(request_value)
            )
    except Exception as exc:
        raise AuthorityDenied("DENIED_POLICY_OR_REQUEST_INVALID") from exc
    if request.research_budget_identity != policy.research_budget_identity:
        raise AuthorityDenied("DENIED_EXPERIMENT_IDENTITY_MISMATCH")
    _identity(policy.research_budget_identity)
    return policy, request


def _validate_owner_scope(policy: Any, request: Any) -> None:
    routes = frozenset(
        (route.provider, route.model, route.billing_class)
        for route in policy.allowed_llm_routes
    )
    if (
        policy.authorization_status != "APPROVED"
        or policy.evidence_classification != "HUMAN_APPROVED"
        or policy.maximum_period_spend_usd != OWNER_TOTAL_USD
        or policy.maximum_run_spend_usd != OWNER_TOTAL_USD
        or policy.maximum_concurrent_runs != 1
        or policy.allowed_universe_scope_identities
        != (request.asset_universe_scope_identity,)
        or policy.allowed_request_provenance_identities != (request.request_provenance,)
        or policy.allowed_research_families != tuple(request.allowed_research_families)
        or routes != ALLOWED_ROUTES
    ):
        raise AuthorityDenied("DENIED_OWNER_APPROVAL_SCOPE_MISMATCH")


def _kms_public_identity(kms: Any, key_arn: str) -> tuple[bytes, str]:
    response = kms.get_public_key(KeyId=key_arn)
    key_spec = response.get("KeySpec", response.get("CustomerMasterKeySpec"))
    if (
        response.get("KeyId") != key_arn
        or key_spec != KEY_SPEC
        or response.get("KeyUsage") != KEY_USAGE
        or SIGNING_ALGORITHM not in response.get("SigningAlgorithms", [])
    ):
        raise AuthorityDenied("DENIED_KMS_KEY_IDENTITY_OR_ALGORITHM")
    try:
        public_key = serialization.load_der_public_key(response["PublicKey"])
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthorityDenied("DENIED_KMS_PUBLIC_KEY_INVALID") from exc
    if len(public_bytes) != 32:
        raise AuthorityDenied("DENIED_KMS_PUBLIC_KEY_INVALID")
    key_id = "sha256:" + hashlib.sha256(public_bytes).hexdigest()
    return public_bytes, key_id


def _sign_payload(kms: Any, key_arn: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = kms.sign(
        KeyId=key_arn,
        Message=rfc8785.dumps(payload),
        MessageType="RAW",
        SigningAlgorithm=SIGNING_ALGORITHM,
    )
    if (
        response.get("KeyId") != key_arn
        or response.get("SigningAlgorithm") != SIGNING_ALGORITHM
        or not isinstance(response.get("Signature"), bytes)
        or len(response["Signature"]) != 64
    ):
        raise AuthorityDenied("DENIED_KMS_SIGNATURE_RESPONSE_INVALID")
    return {
        "payload": payload,
        "signature": base64.b64encode(response["Signature"]).decode("ascii"),
    }


def _approval_payload(policy: Any, signing_key_id: str, epoch: int) -> dict[str, Any]:
    return {
        "domain": owner_signed_authority.APPROVAL_DOMAIN,
        "purpose": owner_signed_authority.APPROVAL_PURPOSE,
        "signing_key_id": signing_key_id,
        "owner_approval_evidence_identity": policy.approval_record_identity,
        "policy_version": "P12StandingResearchPolicyV1",
        "policy_id": policy.policy_id,
        "effective_at": policy.effective_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "expires_at": policy.expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "allowed_universe_scope_identities": list(policy.allowed_universe_scope_identities),
        "allowed_request_provenance_identities": list(policy.allowed_request_provenance_identities),
        "allowed_research_families": list(policy.allowed_research_families),
        "research_budget_identity": policy.research_budget_identity,
        "authority_epoch": epoch,
        "evidence_classification": "HUMAN_APPROVED",
    }


def _revocation_payload(signing_key_id: str, epoch: int, revoked_ids: list[str]) -> dict[str, Any]:
    return {
        "domain": owner_signed_authority.REVOCATION_DOMAIN,
        "signing_key_id": signing_key_id,
        "authority_epoch": epoch,
        "revoked_approval_evidence_identities": sorted(set(revoked_ids)),
    }


def _owner_role_name(owner_role_arn: str) -> tuple[str, str]:
    match = re.fullmatch(r"arn:aws:iam::([0-9]{12}):role/(.+)", owner_role_arn)
    if not match:
        raise AuthorityDenied("DENIED_OWNER_ROLE_CONFIGURATION_INVALID")
    return match.group(1), match.group(2).rsplit("/", 1)[-1]


class OwnerAuthorityWriter:
    """Owner-only KMS/DynamoDB writes; no private key enters this process."""

    def __init__(
        self,
        table: Any,
        kms: Any,
        sts: Any,
        *,
        kms_key_arn: str,
        owner_role_arn: str,
        now=None,
    ):
        self._table = table
        self._kms = kms
        self._sts = sts
        self._kms_key_arn = kms_key_arn
        self._owner_role_arn = owner_role_arn
        self._now = now or (lambda: datetime.now(timezone.utc))

    def _require_owner_session(self) -> None:
        account, role_name = _owner_role_name(self._owner_role_arn)
        caller = self._sts.get_caller_identity()
        expected_prefix = f"arn:aws:sts::{account}:assumed-role/{role_name}/"
        if caller.get("Account") != account or not str(caller.get("Arn", "")).startswith(expected_prefix):
            raise AuthorityDenied("DENIED_OWNER_AUTHENTICATION_REQUIRED")

    def approve(self, request_value: Any, policy_value: Any, *, confirm_owner_approval: bool) -> dict[str, Any]:
        if confirm_owner_approval is not True:
            raise AuthorityDenied("DENIED_EXPLICIT_OWNER_CONFIRMATION_REQUIRED")
        self._require_owner_session()
        policy, request = _policy_and_request(policy_value, request_value)
        _validate_owner_scope(policy, request)
        now = self._now().astimezone(timezone.utc)
        if (
            now < policy.effective_at.astimezone(timezone.utc)
            or now >= policy.expires_at.astimezone(timezone.utc)
            or policy.expires_at.astimezone(timezone.utc)
            - policy.effective_at.astimezone(timezone.utc)
            > MAX_AUTHORIZATION_LIFETIME
        ):
            raise AuthorityDenied("DENIED_OWNER_APPROVAL_TIME_INVALID")
        identity = policy.research_budget_identity
        existing = self._table.get_item(
            Key={APPROVAL_KEY: identity}, ConsistentRead=True
        ).get("Item")
        if existing is not None:
            raise AuthorityDenied("DENIED_EXPERIMENT_AUTHORITY_ALREADY_EXISTS")
        _, signing_key_id = _kms_public_identity(self._kms, self._kms_key_arn)
        epoch = 1
        approval = _sign_payload(
            self._kms, self._kms_key_arn, _approval_payload(policy, signing_key_id, epoch)
        )
        revocation = _sign_payload(
            self._kms,
            self._kms_key_arn,
            _revocation_payload(signing_key_id, epoch, []),
        )
        item = {
            "authority_kind": AUTHORITY_KIND,
            APPROVAL_KEY: identity,
            "request_id": request.request_id,
            "policy_id": policy.policy_id,
            "native_experiment_user_id": experiment_user_id(identity),
            "kms_key_arn": self._kms_key_arn,
            "authority_epoch": epoch,
            "current_status": "APPROVED",
            "approval": approval,
            "revocation_snapshot": revocation,
            "updated_at": now.isoformat().replace("+00:00", "Z"),
        }
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(research_budget_identity)",
            )
        except Exception as exc:
            raise AuthorityDenied("DENIED_EXPERIMENT_AUTHORITY_CONDITIONAL_CREATE") from exc
        return {
            "classification": "OWNER_APPROVAL_RECORDED",
            "research_budget_identity": identity,
            "native_experiment_user_id": item["native_experiment_user_id"],
            "authority_epoch": epoch,
            "real_dispatch_permission": "DENIED",
        }

    def revoke(
        self,
        research_budget_identity: str,
        approval_evidence_identity: str,
        *,
        expected_epoch: int,
    ) -> dict[str, Any]:
        self._require_owner_session()
        identity = _identity(research_budget_identity)
        if not isinstance(expected_epoch, int) or expected_epoch < 1:
            raise AuthorityDenied("DENIED_EXPECTED_EPOCH_INVALID")
        row = self._table.get_item(
            Key={APPROVAL_KEY: identity}, ConsistentRead=True
        ).get("Item")
        if not isinstance(row, dict):
            raise AuthorityDenied("DENIED_AUTHORITY_MISSING")
        approval = row.get("approval")
        payload = approval.get("payload") if isinstance(approval, dict) else None
        if (
            row.get("authority_kind") != AUTHORITY_KIND
            or row.get(APPROVAL_KEY) != identity
            or row.get("kms_key_arn") != self._kms_key_arn
            or row.get("authority_epoch") != expected_epoch
            or row.get("current_status") != "APPROVED"
            or not isinstance(payload, dict)
            or payload.get("owner_approval_evidence_identity") != approval_evidence_identity
        ):
            raise AuthorityDenied("DENIED_AUTHORITY_EPOCH_OR_IDENTITY_MISMATCH")
        _, signing_key_id = _kms_public_identity(self._kms, self._kms_key_arn)
        prior_snapshot = row.get("revocation_snapshot")
        previous = (
            prior_snapshot.get("payload") if isinstance(prior_snapshot, dict) else None
        )
        if not isinstance(previous, dict):
            raise AuthorityDenied("DENIED_REVOCATION_STATE_INVALID")
        revoked = previous.get("revoked_approval_evidence_identities", [])
        if not isinstance(revoked, list):
            raise AuthorityDenied("DENIED_REVOCATION_STATE_INVALID")
        new_epoch = expected_epoch + 1
        revocation = _sign_payload(
            self._kms,
            self._kms_key_arn,
            _revocation_payload(
                signing_key_id, new_epoch, [*revoked, approval_evidence_identity]
            ),
        )
        now = self._now().astimezone(timezone.utc)
        try:
            self._table.update_item(
                Key={APPROVAL_KEY: identity},
                UpdateExpression=(
                    "SET authority_epoch = :next, current_status = :revoked, "
                    "revocation_snapshot = :snapshot, updated_at = :updated"
                ),
                ConditionExpression=(
                    "authority_epoch = :expected AND current_status = :approved "
                    "AND research_budget_identity = :identity"
                ),
                ExpressionAttributeValues={
                    ":next": new_epoch,
                    ":revoked": "REVOKED",
                    ":snapshot": revocation,
                    ":updated": now.isoformat().replace("+00:00", "Z"),
                    ":expected": expected_epoch,
                    ":approved": "APPROVED",
                    ":identity": identity,
                },
            )
        except Exception as exc:
            raise AuthorityDenied("DENIED_CONDITIONAL_EPOCH_UPDATE") from exc
        return {
            "classification": "OWNER_APPROVAL_REVOKED",
            "research_budget_identity": identity,
            "authority_epoch": new_epoch,
            "real_dispatch_permission": "DENIED",
        }


class RuntimeAuthoritySource:
    """Read-only current authority lookup; no local approval cache or writes."""

    def __init__(self, table: Any, kms: Any, *, expected_kms_key_arn: str, now=None):
        self._table = table
        self._kms = kms
        self._expected_kms_key_arn = expected_kms_key_arn
        self._now = now or (lambda: datetime.now(timezone.utc))

    def verify_current(self, request_value: Any, policy_value: Any) -> dict[str, Any]:
        try:
            policy, request = _policy_and_request(policy_value, request_value)
            _validate_owner_scope(policy, request)
            identity = policy.research_budget_identity
            response = self._table.get_item(
                Key={APPROVAL_KEY: identity}, ConsistentRead=True
            )
            row = response.get("Item")
            if not isinstance(row, dict):
                raise AuthorityDenied("DENIED_AUTHORITY_MISSING")
            if (
                row.get("authority_kind") != AUTHORITY_KIND
                or row.get(APPROVAL_KEY) != identity
                or row.get("request_id") != request.request_id
                or row.get("policy_id") != policy.policy_id
                or row.get("native_experiment_user_id") != experiment_user_id(identity)
                or row.get("kms_key_arn") != self._expected_kms_key_arn
            ):
                raise AuthorityDenied("DENIED_AUTHORITY_EXPERIMENT_BINDING_MISMATCH")
            epoch = row.get("authority_epoch")
            if not isinstance(epoch, int) or epoch < 1:
                raise AuthorityDenied("DENIED_AUTHORITY_EPOCH_INVALID")
            public_bytes, signing_key_id = _kms_public_identity(
                self._kms, self._expected_kms_key_arn
            )
            result = owner_signed_authority.verify_signed_research_policy(
                row.get("approval"),
                policy,
                request,
                trusted_public_key_b64=base64.b64encode(public_bytes).decode("ascii"),
                trusted_key_id=signing_key_id,
                revocation_snapshot=row.get("revocation_snapshot"),
                minimum_trusted_epoch=epoch,
                trusted_source_available=True,
                now=self._now(),
            )
            if result.get("classification") != "VERIFIED_HUMAN_APPROVAL_SIGNATURE":
                raise AuthorityDenied(result.get("classification", "DENIED_OWNER_APPROVAL_INVALID"))
            if row.get("current_status") != "APPROVED":
                raise AuthorityDenied("DENIED_AUTHORITY_NOT_ACTIVE")
            if (
                row["approval"]["payload"].get("authority_epoch") != epoch
                or row["revocation_snapshot"]["payload"].get("authority_epoch") != epoch
            ):
                raise AuthorityDenied("DENIED_AUTHORITY_EPOCH_MISMATCH")
            return {
                **result,
                "classification": "OWNER_AUTHORITY_VERIFIED_CURRENT",
                "research_budget_identity": identity,
                "native_experiment_user_id": row["native_experiment_user_id"],
                "request_id": request.request_id,
                "authority_epoch": epoch,
                "real_dispatch_permission": "DENIED",
            }
        except AuthorityDenied as exc:
            return {
                "classification": exc.classification,
                "real_dispatch_permission": "DENIED",
            }
        except Exception:
            return {
                "classification": "DENIED_AWS_AUTHORITY_UNAVAILABLE",
                "real_dispatch_permission": "DENIED",
            }


def _aws_clients(region: str, table_name: str, profile: str | None = None):
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for AWS authority operations") from exc
    session = boto3.Session(profile_name=profile, region_name=region)
    return (
        session.resource("dynamodb").Table(table_name),
        session.client("kms"),
        session.client("sts"),
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    approve = sub.add_parser("approve")
    approve.add_argument("--request", type=Path, required=True)
    approve.add_argument("--policy", type=Path, required=True)
    approve.add_argument("--confirm-owner-approval", action="store_true")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("--research-budget-identity", required=True)
    revoke.add_argument("--approval-evidence-identity", required=True)
    revoke.add_argument("--expected-epoch", type=int, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--request", type=Path, required=True)
    verify.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--region", default=os.environ.get("AWS_REGION"))
    parser.add_argument("--table", default=os.environ.get("AQ_OWNER_AUTHORITY_TABLE"))
    parser.add_argument("--kms-key-arn", default=os.environ.get("AQ_OWNER_KMS_KEY_ARN"))
    parser.add_argument("--owner-role-arn", default=os.environ.get("AQ_OWNER_ROLE_ARN"))
    parser.add_argument("--profile", default=os.environ.get("AWS_PROFILE"))
    args = parser.parse_args(argv)
    try:
        if not args.region or not args.table or not args.kms_key_arn:
            raise RuntimeError("region, table, and KMS key ARN configuration required")
        table, kms, sts = _aws_clients(args.region, args.table, args.profile)
        if args.command in {"approve", "revoke"}:
            if not args.owner_role_arn:
                raise RuntimeError("owner role ARN required")
            writer = OwnerAuthorityWriter(
                table,
                kms,
                sts,
                kms_key_arn=args.kms_key_arn,
                owner_role_arn=args.owner_role_arn,
            )
            if args.command == "approve":
                envelope = _load_json(args.request)
                request = envelope.get("research_request", envelope)
                result = writer.approve(
                    request,
                    _load_json(args.policy),
                    confirm_owner_approval=args.confirm_owner_approval,
                )
            else:
                result = writer.revoke(
                    args.research_budget_identity,
                    args.approval_evidence_identity,
                    expected_epoch=args.expected_epoch,
                )
        else:
            envelope = _load_json(args.request)
            request = envelope.get("research_request", envelope)
            source = RuntimeAuthoritySource(
                table, kms, expected_kms_key_arn=args.kms_key_arn
            )
            result = source.verify_current(request, _load_json(args.policy))
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("classification") in {
            "OWNER_APPROVAL_RECORDED",
            "OWNER_APPROVAL_REVOKED",
            "OWNER_AUTHORITY_VERIFIED_CURRENT",
        } else 3
    except Exception as exc:
        print(json.dumps({"classification": "DENIED_OWNER_AUTHORITY_OPERATION", "detail": str(exc)}), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
