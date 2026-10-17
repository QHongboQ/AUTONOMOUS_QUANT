"""AQ-specific standing research policy contract and test-only admission gate.

No trusted owner-approval store or real spending enforcer is wired here.
Consequently this module can admit only synthetic test fixtures; it cannot
authorize a real P3 call.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal

import rfc8785
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class LLMRouteV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    billing_class: Literal["LOCAL", "PAID"]


class P12StandingResearchPolicyV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["P12StandingResearchPolicyV1"]
    policy_id: str
    authorization_status: Literal["APPROVED", "DENIED"]
    evidence_classification: Literal["HUMAN_APPROVED", "TEST_ONLY"]
    approval_source_identity: str
    approval_record_identity: str
    effective_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    allowed_universe_scope_identities: tuple[str, ...]
    allowed_request_provenance_identities: tuple[str, ...]
    allowed_research_families: tuple[str, ...]
    allowed_llm_routes: tuple[LLMRouteV1, ...]
    research_budget_identity: str
    maximum_period_spend_usd: Decimal = Field(gt=Decimal("0"))
    maximum_run_spend_usd: Decimal = Field(gt=Decimal("0"))
    spending_reset_window_seconds: int = Field(gt=0)
    spending_limit_semantics: Literal["TRACKED_SPEND_LIMIT_ONLY", "HARD_WORST_CASE_EXPOSURE"]
    maximum_concurrent_runs: int = Field(gt=0)
    maximum_runtime_seconds: int = Field(gt=0)
    maximum_memory_mb: int = Field(gt=0)
    maximum_storage_bytes: int = Field(gt=0)

    @field_validator(
        "policy_id",
        "approval_source_identity",
        "approval_record_identity",
        "research_budget_identity",
        mode="before",
    )
    @classmethod
    def validate_sha256_identity(cls, value: Any) -> str:
        if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
            raise ValueError("sha256 identity required")
        return value

    @field_validator("allowed_universe_scope_identities", "allowed_request_provenance_identities")
    @classmethod
    def validate_identity_list(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values or tuple(sorted(set(values))) != values:
            raise ValueError("identity lists must be non-empty, sorted, and unique")
        if any(not _SHA256_RE.fullmatch(value) for value in values):
            raise ValueError("identity lists must contain sha256 identities")
        return values

    @field_validator("allowed_research_families")
    @classmethod
    def validate_families(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values or tuple(sorted(set(values))) != values:
            raise ValueError("research families must be non-empty, sorted, and unique")
        return values

    @field_validator("allowed_llm_routes")
    @classmethod
    def validate_routes(cls, values: tuple[LLMRouteV1, ...]) -> tuple[LLMRouteV1, ...]:
        route_keys = tuple(sorted((item.provider, item.model, item.billing_class) for item in values))
        if not values or len(set(route_keys)) != len(route_keys):
            raise ValueError("LLM routes must be non-empty and unique")
        return values

    @field_validator("effective_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("policy times must include a timezone")
        return value

    @field_validator("revoked_at")
    @classmethod
    def require_aware_revocation_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("revocation time must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_policy(self) -> "P12StandingResearchPolicyV1":
        if self.expires_at <= self.effective_at:
            raise ValueError("policy expiration must follow its effective time")
        if self.maximum_run_spend_usd > self.maximum_period_spend_usd:
            raise ValueError("per-run spend limit cannot exceed period spend limit")
        expected = policy_identity(self.model_dump(mode="json", exclude={"policy_id"}))
        if self.policy_id != expected:
            raise ValueError("policy_id does not match RFC 8785 identity")
        return self


def policy_identity(fields: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(fields)).hexdigest()


@dataclass(frozen=True)
class AdmissionEvidence:
    """Facts required at the gate; only synthetic fixture evidence is available."""

    now: datetime
    execution_mode: Literal["SYNTHETIC_ONLY", "REAL"]
    approval_source_status: Literal["TEST_FIXTURE", "TRUSTED_OWNER_SOURCE", "UNAVAILABLE"]
    approval_source_identity: str | None
    revocation_status: Literal["ACTIVE", "REVOKED", "UNKNOWN"]
    provenance_status: Literal["TEST_FIXTURE_VERIFIED", "TRUSTED_SOURCE_VERIFIED", "UNKNOWN"]
    spending_authority_status: Literal["SIMULATED_TEST_ONLY", "VERIFIED_NATIVE", "UNKNOWN", "UNAVAILABLE"]
    period_spend_usd: Decimal | None
    estimated_run_spend_usd: Decimal | None
    active_run_count: int | None
    routes: tuple[LLMRouteV1, ...] | None
    runtime_seconds: int | None
    memory_mb: int | None
    storage_bytes: int | None


def synthetic_admission_evidence(
    *,
    now: datetime | None = None,
    revocation_status: Literal["ACTIVE", "REVOKED", "UNKNOWN"] = "ACTIVE",
    spending_authority_status: Literal[
        "SIMULATED_TEST_ONLY", "VERIFIED_NATIVE", "UNKNOWN", "UNAVAILABLE"
    ] = "SIMULATED_TEST_ONLY",
    period_spend_usd: Decimal | None = Decimal("0.00"),
    estimated_run_spend_usd: Decimal | None = Decimal("0.05"),
    active_run_count: int | None = 0,
    routes: tuple[LLMRouteV1, ...] | None = None,
    runtime_seconds: int | None = 30,
    memory_mb: int | None = 256,
    storage_bytes: int | None = 1_048_576,
    approval_source_identity: str | None = None,
    provenance_status: Literal[
        "TEST_FIXTURE_VERIFIED", "TRUSTED_SOURCE_VERIFIED", "UNKNOWN"
    ] = "TEST_FIXTURE_VERIFIED",
) -> AdmissionEvidence:
    return AdmissionEvidence(
        now=now or datetime.now(timezone.utc),
        execution_mode="SYNTHETIC_ONLY",
        approval_source_status="TEST_FIXTURE",
        approval_source_identity=approval_source_identity,
        revocation_status=revocation_status,
        provenance_status=provenance_status,
        spending_authority_status=spending_authority_status,
        period_spend_usd=period_spend_usd,
        estimated_run_spend_usd=estimated_run_spend_usd,
        active_run_count=active_run_count,
        routes=routes
        if routes is not None
        else (
            LLMRouteV1(
                provider="deepseek", model="deepseek/deepseek-chat", billing_class="PAID"
            ),
            LLMRouteV1(
                provider="ollama",
                model="ollama/qwen3-embedding:0.6b",
                billing_class="LOCAL",
            ),
        ),
        runtime_seconds=runtime_seconds,
        memory_mb=memory_mb,
        storage_bytes=storage_bytes,
    )


def evaluate_policy_admission(
    request: Any,
    policy_value: P12StandingResearchPolicyV1 | dict[str, Any] | None,
    *,
    p4_is_test_fixture: bool,
    evidence: AdmissionEvidence,
    signed_approval: dict[str, Any] | None = None,
    trusted_authority: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an admission classification; this gate can never permit real P3."""
    if policy_value is None:
        return {"classification": "DENIED_POLICY_MISSING"}
    try:
        policy = (
            policy_value
            if isinstance(policy_value, P12StandingResearchPolicyV1)
            else P12StandingResearchPolicyV1.model_validate(policy_value)
        )
    except (ValidationError, TypeError, ValueError):
        return {"classification": "DENIED_POLICY_INVALID"}

    signature_result: dict[str, Any] | None = None
    if signed_approval is not None:
        if not isinstance(trusted_authority, dict):
            return {"classification": "DENIED_TRUSTED_SOURCE_UNAVAILABLE"}
        # Import lazily so the existing TEST_ONLY synthetic handoff does not
        # require signature material or change its stable baseline.
        try:
            import owner_signed_authority

            signature_result = owner_signed_authority.verify_signed_research_policy(
                signed_approval,
                policy,
                request,
                trusted_public_key_b64=trusted_authority.get("trusted_public_key_b64"),
                trusted_key_id=trusted_authority.get("trusted_key_id"),
                revocation_snapshot=trusted_authority.get("revocation_snapshot"),
                minimum_trusted_epoch=trusted_authority.get("minimum_trusted_epoch"),
                trusted_source_available=trusted_authority.get("trusted_source_available") is True,
            )
        except (ImportError, TypeError, ValueError):
            return {"classification": "DENIED_SIGNATURE_VERIFIER_UNAVAILABLE"}
        if signature_result["classification"] != "VERIFIED_TEST_ONLY_SIGNATURE":
            return {
                "classification": signature_result["classification"],
                "real_dispatch_permission": "DENIED",
            }

    if policy.authorization_status != "APPROVED":
        return {"classification": "DENIED_POLICY_NOT_APPROVED", "policy_id": policy.policy_id}
    if policy.evidence_classification != "TEST_ONLY":
        return {
            "classification": "DENIED_NO_TRUSTED_APPROVAL_SOURCE",
            "policy_id": policy.policy_id,
            "trusted_approval_source_available": False,
        }
    if not p4_is_test_fixture or evidence.execution_mode != "SYNTHETIC_ONLY":
        return {
            "classification": "DENIED_TEST_ONLY_POLICY_CANNOT_AUTHORIZE_REAL",
            "policy_id": policy.policy_id,
            "real_dispatch_permission": "DENIED",
        }
    if evidence.approval_source_status != "TEST_FIXTURE" or (
        evidence.approval_source_identity != policy.approval_source_identity
    ):
        return {"classification": "DENIED_APPROVAL_SOURCE_UNVERIFIED", "policy_id": policy.policy_id}
    if evidence.revocation_status == "REVOKED" or (
        policy.revoked_at is not None and policy.revoked_at <= evidence.now
    ):
        return {"classification": "DENIED_POLICY_REVOKED", "policy_id": policy.policy_id}
    if evidence.revocation_status != "ACTIVE":
        return {"classification": "DENIED_REVOCATION_STATUS_UNKNOWN", "policy_id": policy.policy_id}
    if evidence.now < policy.effective_at:
        return {"classification": "DENIED_POLICY_NOT_YET_EFFECTIVE", "policy_id": policy.policy_id}
    if evidence.now >= policy.expires_at:
        return {"classification": "DENIED_POLICY_EXPIRED", "policy_id": policy.policy_id}
    if (
        evidence.provenance_status != "TEST_FIXTURE_VERIFIED"
        or request.request_provenance not in policy.allowed_request_provenance_identities
    ):
        return {"classification": "DENIED_REQUEST_PROVENANCE", "policy_id": policy.policy_id}
    if request.asset_universe_scope_identity not in policy.allowed_universe_scope_identities:
        return {"classification": "DENIED_RESEARCH_UNIVERSE", "policy_id": policy.policy_id}
    if not set(request.allowed_research_families).issubset(policy.allowed_research_families):
        return {"classification": "DENIED_RESEARCH_FAMILY", "policy_id": policy.policy_id}
    if request.research_budget_identity != policy.research_budget_identity:
        return {"classification": "DENIED_BUDGET_IDENTITY_MISMATCH", "policy_id": policy.policy_id}
    if evidence.routes is None:
        return {"classification": "DENIED_MODEL_PROVIDER_UNKNOWN", "policy_id": policy.policy_id}
    allowed_routes = {
        (route.provider, route.model, route.billing_class) for route in policy.allowed_llm_routes
    }
    if not evidence.routes or any(
        (route.provider, route.model, route.billing_class) not in allowed_routes
        for route in evidence.routes
    ):
        return {"classification": "DENIED_MODEL_PROVIDER", "policy_id": policy.policy_id}
    if evidence.spending_authority_status in {"UNKNOWN", "UNAVAILABLE"}:
        return {"classification": "DENIED_SPENDING_AUTHORITY_UNAVAILABLE", "policy_id": policy.policy_id}
    if evidence.spending_authority_status != "SIMULATED_TEST_ONLY":
        return {"classification": "DENIED_REAL_SPENDING_ENFORCEMENT_NOT_PROVEN", "policy_id": policy.policy_id}
    if evidence.period_spend_usd is None or evidence.estimated_run_spend_usd is None:
        return {"classification": "DENIED_SPEND_UNKNOWN", "policy_id": policy.policy_id}
    spend_values = (evidence.period_spend_usd, evidence.estimated_run_spend_usd)
    if any(
        not isinstance(value, Decimal) or not value.is_finite() or value < 0
        for value in spend_values
    ):
        return {"classification": "DENIED_SPEND_EVIDENCE_INVALID", "policy_id": policy.policy_id}
    if evidence.estimated_run_spend_usd > policy.maximum_run_spend_usd:
        return {"classification": "DENIED_PER_RUN_SPEND_LIMIT", "policy_id": policy.policy_id}
    if evidence.period_spend_usd + evidence.estimated_run_spend_usd > policy.maximum_period_spend_usd:
        return {"classification": "DENIED_PERIOD_SPEND_LIMIT", "policy_id": policy.policy_id}
    if evidence.active_run_count is None:
        return {"classification": "DENIED_CONCURRENCY_UNKNOWN", "policy_id": policy.policy_id}
    if evidence.active_run_count < 0 or evidence.active_run_count >= policy.maximum_concurrent_runs:
        return {"classification": "DENIED_CONCURRENCY_LIMIT", "policy_id": policy.policy_id}
    requested_resources = (evidence.runtime_seconds, evidence.memory_mb, evidence.storage_bytes)
    if any(value is None or value <= 0 for value in requested_resources):
        return {"classification": "DENIED_RESOURCE_LIMIT_UNKNOWN", "policy_id": policy.policy_id}
    if (
        evidence.runtime_seconds > policy.maximum_runtime_seconds
        or evidence.memory_mb > policy.maximum_memory_mb
        or evidence.storage_bytes > policy.maximum_storage_bytes
    ):
        return {"classification": "DENIED_RESOURCE_LIMIT", "policy_id": policy.policy_id}
    return {
        "classification": "ADMITTED_SYNTHETIC_TEST_ONLY",
        "policy_id": policy.policy_id,
        "policy_signature_verification": (
            signature_result["classification"] if signature_result is not None else "NOT_PROVIDED"
        ),
        "owner_approval_evidence_identity": (
            signature_result.get("owner_approval_evidence_identity")
            if signature_result is not None
            else None
        ),
        "real_dispatch_permission": "DENIED",
        "spending_enforcement": "SIMULATED_ONLY_NOT_NATIVE_ENFORCEMENT",
        "hard_worst_case_exposure_guarantee": False,
    }


def create_synthetic_test_policy(request: Any) -> P12StandingResearchPolicyV1:
    """Create a TEST_ONLY policy fixture; it is not a human approval record."""
    source_identity = "sha256:" + hashlib.sha256(b"p12-test-policy-source-v1").hexdigest()
    record_identity = "sha256:" + hashlib.sha256(b"p12-test-policy-record-v1").hexdigest()
    fields: dict[str, Any] = {
        "contract_version": "P12StandingResearchPolicyV1",
        "authorization_status": "APPROVED",
        "evidence_classification": "TEST_ONLY",
        "approval_source_identity": source_identity,
        "approval_record_identity": record_identity,
        "effective_at": "2026-01-01T00:00:00Z",
        "expires_at": "2030-01-01T00:00:00Z",
        "revoked_at": None,
        "allowed_universe_scope_identities": [request.asset_universe_scope_identity],
        "allowed_request_provenance_identities": [request.request_provenance],
        "allowed_research_families": list(request.allowed_research_families),
        "allowed_llm_routes": [
            {"provider": "deepseek", "model": "deepseek/deepseek-chat", "billing_class": "PAID"},
            {
                "provider": "ollama",
                "model": "ollama/qwen3-embedding:0.6b",
                "billing_class": "LOCAL",
            },
        ],
        "research_budget_identity": request.research_budget_identity,
        "maximum_period_spend_usd": "1.00",
        "maximum_run_spend_usd": "0.25",
        "spending_reset_window_seconds": 3600,
        "spending_limit_semantics": "TRACKED_SPEND_LIMIT_ONLY",
        "maximum_concurrent_runs": 1,
        "maximum_runtime_seconds": 300,
        "maximum_memory_mb": 1024,
        "maximum_storage_bytes": 104857600,
    }
    fields["allowed_universe_scope_identities"].sort()
    fields["allowed_request_provenance_identities"].sort()
    fields["allowed_research_families"].sort()
    fields["allowed_llm_routes"].sort(key=lambda item: (item["provider"], item["model"]))
    fields["policy_id"] = policy_identity(fields)
    return P12StandingResearchPolicyV1.model_validate(fields)
