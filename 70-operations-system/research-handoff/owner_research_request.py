"""Content-addressed, owner-originated P12 research requests.

This contract is separate from the one-time initial bootstrap and P4 lifecycle.
It creates a reviewable request only; approval and any dispatch remain in the
existing interactive P12 owner one-shot path.
"""

from __future__ import annotations

import hashlib
from typing import Any, Literal

import rfc8785
from pydantic import BaseModel, ConfigDict, Field, model_validator

from owner_bootstrap_request import InputIdentityV1, collect_frozen_us_pit_inputs
from docker_rdagent_target import PINNED_FINQUANT_IMAGE_ID

_IDENTITY = "sha256:"
_MAX_DATA_DATE = "2024-12-31"
_BUDGET_DOMAIN = b"AQ:P12:OWNER_AUTHORIZED_RESEARCH:BUDGET:V1\0"
_PROVENANCE_DOMAIN = b"AQ:P12:OWNER_AUTHORIZED_RESEARCH:PROVENANCE:V1\0"
_ROUTES = ("deepseek/deepseek-flash", "ollama/qwen3-embedding:0.6b")


def _sha(data: bytes) -> str:
    return _IDENTITY + hashlib.sha256(data).hexdigest()


class OwnerResearchRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["P12OwnerResearchRequestV1"]
    request_origin: Literal["OWNER_AUTHORIZED_RESEARCH"]
    request_id: str
    authorization_identity: str
    asset_universe_scope_identity: str
    research_budget_identity: str
    request_provenance: str
    scope: Literal["US/PIT"]
    provider_market: Literal["p2_pit"]
    data_cutoff: Literal["2024-12-31"]
    research_objective: str = Field(min_length=20, max_length=1000)
    maximum_total_spend_usd: Literal["5.00"]
    budget_duration: Literal["NONE"]
    authorization_lifetime_hours: Literal[24]
    maximum_research_runs: Literal[1]
    maximum_concurrent_runs: Literal[1]
    permitted_llm_routes: tuple[Literal["deepseek/deepseek-flash", "ollama/qwen3-embedding:0.6b"], ...]
    input_manifest_identities: tuple[InputIdentityV1, ...]
    allowed_research_families: tuple[Literal["RD_AGENT"], ...]
    p2_certification_authority: Literal["NONE"]
    trading_authority: Literal["NONE"]

    @model_validator(mode="after")
    def validate_identities(self) -> "OwnerResearchRequestV1":
        identities = (
            self.request_id,
            self.authorization_identity,
            self.asset_universe_scope_identity,
            self.research_budget_identity,
            self.request_provenance,
        )
        if any(not isinstance(value, str) or len(value) != 71 or not value.startswith(_IDENTITY)
               or any(ch not in "0123456789abcdef" for ch in value[7:]) for value in identities):
            raise ValueError("owner research identities must be sha256")
        names = tuple(item.name for item in self.input_manifest_identities)
        if not names or names != tuple(sorted(set(names))):
            raise ValueError("input identities must be sorted, unique, and non-empty")
        if self.permitted_llm_routes != _ROUTES or self.allowed_research_families != ("RD_AGENT",):
            raise ValueError("owner research route and family scope are fixed")
        scope_id = _sha(rfc8785.dumps({
            "scope": self.scope,
            "provider_market": self.provider_market,
            "data_cutoff": self.data_cutoff,
            "input_manifest_identities": [item.model_dump(mode="json") for item in self.input_manifest_identities],
            "runtime_image_id": PINNED_FINQUANT_IMAGE_ID,
        }))
        authorization_id = _sha(rfc8785.dumps({
            "request_origin": self.request_origin,
            "scope_identity": scope_id,
            "research_objective": self.research_objective,
        }))
        budget_id = _sha(_BUDGET_DOMAIN + rfc8785.dumps({
            "authorization_identity": authorization_id,
            "maximum_total_spend_usd": self.maximum_total_spend_usd,
            "budget_duration": self.budget_duration,
            "authorization_lifetime_hours": self.authorization_lifetime_hours,
            "maximum_research_runs": self.maximum_research_runs,
            "maximum_concurrent_runs": self.maximum_concurrent_runs,
            "permitted_llm_routes": list(self.permitted_llm_routes),
        }))
        provenance_id = _sha(_PROVENANCE_DOMAIN + rfc8785.dumps({
            "authorization_identity": authorization_id,
            "research_budget_identity": budget_id,
        }))
        if (self.asset_universe_scope_identity, self.authorization_identity,
            self.research_budget_identity, self.request_provenance) != (
            scope_id, authorization_id, budget_id, provenance_id
        ):
            raise ValueError("owner request scope, authorization, budget, or provenance identity mismatch")
        body = self.model_dump(mode="json", exclude={"request_id"})
        if self.request_id != _sha(rfc8785.dumps(body)):
            raise ValueError("owner request_id does not match RFC 8785 identity")
        return self


def build_owner_research_request(
    inputs: tuple[InputIdentityV1, ...], research_objective: str,
) -> OwnerResearchRequestV1:
    """Build a fresh bounded request; repeated identical input is the same ID."""
    if not isinstance(research_objective, str):
        raise ValueError("research objective must be text")
    objective = " ".join(research_objective.split())
    if not 20 <= len(objective) <= 1000:
        raise ValueError("research objective must contain 20 to 1000 normalized characters")
    scope_body = {
        "scope": "US/PIT", "provider_market": "p2_pit", "data_cutoff": _MAX_DATA_DATE,
        "input_manifest_identities": [item.model_dump(mode="json") for item in inputs],
        "runtime_image_id": PINNED_FINQUANT_IMAGE_ID,
    }
    scope_id = _sha(rfc8785.dumps(scope_body))
    authorization_id = _sha(rfc8785.dumps({
        "request_origin": "OWNER_AUTHORIZED_RESEARCH",
        "scope_identity": scope_id,
        "research_objective": objective,
    }))
    budget_id = _sha(_BUDGET_DOMAIN + rfc8785.dumps({
        "authorization_identity": authorization_id,
        "maximum_total_spend_usd": "5.00", "budget_duration": "NONE",
        "authorization_lifetime_hours": 24, "maximum_research_runs": 1,
        "maximum_concurrent_runs": 1, "permitted_llm_routes": list(_ROUTES),
    }))
    provenance_id = _sha(_PROVENANCE_DOMAIN + rfc8785.dumps({
        "authorization_identity": authorization_id,
        "research_budget_identity": budget_id,
    }))
    fields: dict[str, Any] = {
        "contract_version": "P12OwnerResearchRequestV1",
        "request_origin": "OWNER_AUTHORIZED_RESEARCH",
        "authorization_identity": authorization_id,
        "asset_universe_scope_identity": scope_id,
        "research_budget_identity": budget_id,
        "request_provenance": provenance_id,
        "scope": "US/PIT", "provider_market": "p2_pit", "data_cutoff": _MAX_DATA_DATE,
        "research_objective": objective,
        "maximum_total_spend_usd": "5.00", "budget_duration": "NONE",
        "authorization_lifetime_hours": 24, "maximum_research_runs": 1,
        "maximum_concurrent_runs": 1, "permitted_llm_routes": list(_ROUTES),
        "input_manifest_identities": [item.model_dump(mode="json") for item in inputs],
        "allowed_research_families": ["RD_AGENT"],
        "p2_certification_authority": "NONE", "trading_authority": "NONE",
    }
    fields["request_id"] = _sha(rfc8785.dumps(fields))
    return OwnerResearchRequestV1.model_validate(fields)


def validate_owner_research_envelope(envelope: dict[str, Any]) -> OwnerResearchRequestV1:
    if set(envelope) != {"owner_research_request"}:
        raise ValueError("owner research envelope must not contain P4, bootstrap, or synthetic evidence")
    return OwnerResearchRequestV1.model_validate(envelope["owner_research_request"])


def verify_current_frozen_inputs(request: OwnerResearchRequestV1, repo_root: Any) -> None:
    if collect_frozen_us_pit_inputs(repo_root) != request.input_manifest_identities:
        raise ValueError("owner request no longer matches current frozen US/PIT inputs")
