"""Immutable P12 owner-initial research request and frozen-input binding.

This is an AQ-owned admission contract, not a P4 lifecycle event or a
research/workflow engine. It can produce review-only input; approval remains
an explicit local interactive action in ``owner_oneshot_research``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

import rfc8785
from pydantic import BaseModel, ConfigDict, Field, model_validator

from docker_rdagent_target import FINQUANT_DATA_MOUNTS, PINNED_FINQUANT_IMAGE_ID

_IDENTITY = re.compile(r"^sha256:[0-9a-f]{64}$")
_MAX_DATA_DATE = "2024-12-31"
_TEMPLATES = (
    "30-research-system/rd-agent/templates/p3-official-us/factor_template/conf_baseline.yaml",
    "30-research-system/rd-agent/templates/p3-official-us/factor_template/conf_combined_factors.yaml",
    "30-research-system/rd-agent/templates/p3-official-us/factor_template/conf_combined_factors_sota_model.yaml",
    "30-research-system/rd-agent/templates/p3-official-us/model_template/conf_baseline_factors_model.yaml",
    "30-research-system/rd-agent/templates/p3-official-us/model_template/conf_sota_factors_model.yaml",
)
_BUDGET_DOMAIN = b"AQ:P12:OWNER_INITIAL_BOOTSTRAP:BUDGET:V1\0"
_PROVENANCE_DOMAIN = b"AQ:P12:OWNER_INITIAL_BOOTSTRAP:PROVENANCE:V1\0"


class InputIdentityV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    sha256: str

    @model_validator(mode="after")
    def valid_sha(self) -> "InputIdentityV1":
        if not _IDENTITY.fullmatch(self.sha256):
            raise ValueError("input source identity must be sha256")
        return self


class OwnerInitialBootstrapRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["P12OwnerInitialBootstrapRequestV1"]
    request_origin: Literal["OWNER_INITIAL_BOOTSTRAP"]
    request_id: str
    asset_universe_scope_identity: str
    research_budget_identity: str
    request_provenance: str
    scope: Literal["US/PIT"]
    provider_market: Literal["p2_pit"]
    data_cutoff: Literal["2024-12-31"]
    maximum_total_spend_usd: Literal["5.00"]
    budget_duration: Literal["NONE"]
    authorization_lifetime_hours: Literal[24]
    maximum_research_runs: Literal[1]
    maximum_concurrent_runs: Literal[1]
    permitted_llm_routes: tuple[Literal["deepseek/deepseek-flash", "ollama/qwen3-embedding:0.6b"], ...]
    input_manifest_identities: tuple[InputIdentityV1, ...]
    allowed_research_families: tuple[Literal["RD_AGENT"], ...]
    trading_authority: Literal["NONE"]

    @model_validator(mode="after")
    def canonical_identities(self) -> "OwnerInitialBootstrapRequestV1":
        for value in (self.request_id, self.asset_universe_scope_identity,
                      self.research_budget_identity, self.request_provenance):
            if not _IDENTITY.fullmatch(value):
                raise ValueError("bootstrap identity must be sha256")
        names = tuple(item.name for item in self.input_manifest_identities)
        if not names or names != tuple(sorted(set(names))):
            raise ValueError("input identities must be sorted, unique, and non-empty")
        if self.allowed_research_families != ("RD_AGENT",):
            raise ValueError("bootstrap permits only RD_AGENT research")
        scope_body = {
            "scope": self.scope,
            "provider_market": self.provider_market,
            "data_cutoff": self.data_cutoff,
            "input_manifest_identities": [item.model_dump(mode="json") for item in self.input_manifest_identities],
            "runtime_image_id": PINNED_FINQUANT_IMAGE_ID,
        }
        scope_id = _sha_bytes(rfc8785.dumps(scope_body))
        budget_body = {
            "scope_identity": scope_id,
            "maximum_total_spend_usd": self.maximum_total_spend_usd,
            "budget_duration": self.budget_duration,
            "authorization_lifetime_hours": self.authorization_lifetime_hours,
            "maximum_research_runs": self.maximum_research_runs,
            "maximum_concurrent_runs": self.maximum_concurrent_runs,
            "permitted_llm_routes": list(self.permitted_llm_routes),
        }
        if self.permitted_llm_routes != ("deepseek/deepseek-flash", "ollama/qwen3-embedding:0.6b"):
            raise ValueError("bootstrap model routes are fixed and ordered")
        budget_id = _sha_bytes(_BUDGET_DOMAIN + rfc8785.dumps(budget_body))
        provenance = _sha_bytes(_PROVENANCE_DOMAIN + rfc8785.dumps({"scope": scope_id, "budget": budget_id}))
        if (
            self.asset_universe_scope_identity != scope_id
            or self.research_budget_identity != budget_id
            or self.request_provenance != provenance
        ):
            raise ValueError("bootstrap scope, budget, or provenance identity mismatch")
        body = self.model_dump(mode="json", exclude={"request_id"})
        expected = "sha256:" + hashlib.sha256(rfc8785.dumps(body)).hexdigest()
        if self.request_id != expected:
            raise ValueError("bootstrap request_id does not match RFC8785 identity")
        return self


def _sha_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _host_path(value: str) -> Path:
    """Translate the P3 manifest's WSL D: paths when running on Windows."""
    if value.startswith("/mnt/d/") and not Path("/mnt/d").exists():
        return Path("D:/") / value.removeprefix("/mnt/d/")
    return Path(value)


def _provider_manifest(root: Path) -> dict[str, Any]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    tree = hashlib.sha256()
    total_bytes = 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        total_bytes += size
        file_hash = _sha_file(path).removeprefix("sha256:")
        tree.update(f"{relative}\0{size}\0{file_hash}\n".encode())
    calendar = root / "calendars" / "day.txt"
    instruments = root / "instruments" / "p2_pit.txt"
    if not calendar.is_file() or not instruments.is_file():
        raise ValueError("frozen P2 provider calendar or p2_pit instruments are missing")
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "tree_manifest_sha256": tree.hexdigest(),
        "calendar_sha256": _sha_file(calendar).removeprefix("sha256:"),
        "market_instruments_sha256": _sha_file(instruments).removeprefix("sha256:"),
    }


def collect_frozen_us_pit_inputs(repo_root: Path) -> tuple[InputIdentityV1, ...]:
    """Verify mounted-source manifests against current files without OOS reads."""
    factor_root, provider_root, calendar_root = (_host_path(path) for path in FINQUANT_DATA_MOUNTS.values())
    for root in (factor_root, provider_root, calendar_root):
        if not root.is_dir():
            raise ValueError(f"approved frozen US/PIT input is missing: {root}")

    report_path = factor_root / "materialization-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        report.get("schema") != "RDAGENTUSFactorSourceMaterializationV1"
        or report.get("provider_mutated") is not False
        or report.get("sealed_oos_isolation") != "PASS"
        or report.get("max_session", "9999") > _MAX_DATA_DATE
        or report.get("provider_path") != "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data"
        or report.get("inventory_path") != "/mnt/d/AQ_DATA/P2/certification-coverage-frontier-audit-001/full_universe_inventory.json"
        or report.get("quantiacs_source_path") != "/mnt/d/AQ_DATA/P2/frozen-certification-dataset-build-001/source/quantiacs"
        or report.get("provider_invariant_before") != report.get("provider_invariant_after")
    ):
        raise ValueError("P3 materialization report does not prove the approved frozen research inputs")

    for subpath, report_key in (("full/daily_pv.h5", "full_daily_pv_sha256"),
                                ("debug/daily_pv.h5", "debug_daily_pv_sha256")):
        if _sha_file(factor_root / subpath).removeprefix("sha256:") != report.get(report_key):
            raise ValueError("P3 materialized factor source identity mismatch")

    observed_provider = _provider_manifest(provider_root)
    if observed_provider != report["provider_invariant_after"]:
        raise ValueError("frozen P2 Qlib provider manifest changed")
    quantiacs_manifest = _host_path(report["quantiacs_source_path"]) / "source_manifest.json"
    inventory = _host_path(report["inventory_path"])
    if (
        not quantiacs_manifest.is_file()
        or _sha_file(quantiacs_manifest).removeprefix("sha256:") != report.get("quantiacs_source_manifest_sha256")
        or not inventory.is_file()
        or _sha_file(inventory).removeprefix("sha256:") != report.get("inventory_sha256")
    ):
        raise ValueError("frozen source manifest or PIT inventory identity mismatch")

    identities: dict[str, str] = {
        "p3_materialization_report": _sha_file(report_path),
        "p3_factor_source_full": "sha256:" + report["full_daily_pv_sha256"],
        "p3_factor_source_debug": "sha256:" + report["debug_daily_pv_sha256"],
        "p2_source_manifest": _sha_file(quantiacs_manifest),
        "p2_pit_inventory": _sha_file(inventory),
        "p2_qlib_provider_tree": "sha256:" + observed_provider["tree_manifest_sha256"],
        "p2_qlib_provider_calendar": "sha256:" + observed_provider["calendar_sha256"],
        "p2_pit_membership": "sha256:" + observed_provider["market_instruments_sha256"],
        "p2_runtime_calendar_day": _sha_file(calendar_root / "calendars/day.txt"),
        "p2_runtime_calendar_future": _sha_file(calendar_root / "calendars/day_future.txt"),
        "rdagent_qlib_pinned_image": _sha_bytes(PINNED_FINQUANT_IMAGE_ID.encode("ascii")),
    }
    for relative in _TEMPLATES:
        template = repo_root / relative
        if not template.is_file():
            raise ValueError(f"frozen P3 template is missing: {relative}")
        identities["template:" + relative] = _sha_file(template)
    return tuple(InputIdentityV1(name=name, sha256=value) for name, value in sorted(identities.items()))


def build_owner_bootstrap_request(inputs: tuple[InputIdentityV1, ...]) -> OwnerInitialBootstrapRequestV1:
    """Build deterministic identities from real manifest identities."""
    scope_body = {
        "scope": "US/PIT", "provider_market": "p2_pit", "data_cutoff": _MAX_DATA_DATE,
        "input_manifest_identities": [item.model_dump(mode="json") for item in inputs],
        "runtime_image_id": PINNED_FINQUANT_IMAGE_ID,
    }
    scope_id = _sha_bytes(rfc8785.dumps(scope_body))
    budget_body = {
        "scope_identity": scope_id,
        "maximum_total_spend_usd": "5.00",
        "budget_duration": "NONE",
        "authorization_lifetime_hours": 24,
        "maximum_research_runs": 1,
        "maximum_concurrent_runs": 1,
        "permitted_llm_routes": ["deepseek/deepseek-flash", "ollama/qwen3-embedding:0.6b"],
    }
    budget_id = _sha_bytes(_BUDGET_DOMAIN + rfc8785.dumps(budget_body))
    provenance = _sha_bytes(_PROVENANCE_DOMAIN + rfc8785.dumps({"scope": scope_id, "budget": budget_id}))
    body: dict[str, Any] = {
        "contract_version": "P12OwnerInitialBootstrapRequestV1",
        "request_origin": "OWNER_INITIAL_BOOTSTRAP",
        "asset_universe_scope_identity": scope_id,
        "research_budget_identity": budget_id,
        "request_provenance": provenance,
        "scope": "US/PIT",
        "provider_market": "p2_pit",
        "data_cutoff": _MAX_DATA_DATE,
        "maximum_total_spend_usd": "5.00",
        "budget_duration": "NONE",
        "authorization_lifetime_hours": 24,
        "maximum_research_runs": 1,
        "maximum_concurrent_runs": 1,
        "permitted_llm_routes": ["deepseek/deepseek-flash", "ollama/qwen3-embedding:0.6b"],
        "input_manifest_identities": [item.model_dump(mode="json") for item in inputs],
        "allowed_research_families": ["RD_AGENT"],
        "trading_authority": "NONE",
    }
    body["request_id"] = _sha_bytes(rfc8785.dumps(body))
    return OwnerInitialBootstrapRequestV1.model_validate(body)


def validate_owner_bootstrap_envelope(envelope: dict[str, Any]) -> OwnerInitialBootstrapRequestV1:
    if set(envelope) != {"bootstrap_request"}:
        raise ValueError("owner bootstrap envelope must not contain P4 or synthetic evidence")
    return OwnerInitialBootstrapRequestV1.model_validate(envelope["bootstrap_request"])


def verify_current_frozen_inputs(request: OwnerInitialBootstrapRequestV1, repo_root: Path) -> None:
    current = collect_frozen_us_pit_inputs(repo_root)
    if current != request.input_manifest_identities:
        raise ValueError("bootstrap request no longer matches current frozen US/PIT inputs")
