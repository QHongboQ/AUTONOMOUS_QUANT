"""Frozen public contract values for the Trial Ledger runtime foundation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Capability(StrEnum):
    TRIAL_REGISTER = "TRIAL_REGISTER"
    EXECUTION_APPEND = "EXECUTION_APPEND"
    RESULT_ATTACH = "RESULT_ATTACH"
    ARTIFACT_ATTACH = "ARTIFACT_ATTACH"
    SNAPSHOT_READ = "SNAPSHOT_READ"
    ACTOR_ADMIN = "ACTOR_ADMIN"
    CAPABILITY_ADMIN = "CAPABILITY_ADMIN"
    FAMILY_POLICY_ADMIN = "FAMILY_POLICY_ADMIN"
    PROTOCOL_VIOLATION_RECORD = "PROTOCOL_VIOLATION_RECORD"
    ANCHOR_CREATE = "ANCHOR_CREATE"
    MAINTENANCE_ENTER = "MAINTENANCE_ENTER"


P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1 = "P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1"


@dataclass(frozen=True)
class ResearchSpec:
    canonical_research_spec_sha256: str


@dataclass(frozen=True)
class ActorIdentity:
    actor_id: str
    actor_type: str
    actor_version: str
    display_name: str
    credential_binding: str
    authentication_method: str
    created_at: str
    metadata_schema_version: str = "V1"


@dataclass(frozen=True)
class FamilyPolicySpec:
    family_policy_id: str
    family_policy_version: str
    policy_schema_version: str
    policy_rules_hash: str
    effective_from: str
    registered_at: str
    registered_by: str
    canonical_policy_hash: str


@dataclass(frozen=True)
class TrialRegistration:
    trial_id: str
    canonical_research_spec_sha256: str
    trial_family_id: str
    parent_trial_id: str | None
    trial_kind: str
    registration_actor: str
    registered_at: str
    family_policy_id: str
    family_policy_version: str
    schema_version: str = "1"


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    trial_id: str
    execution_kind: str
    original_execution_id: str | None
    created_at: str
    actor_id: str


@dataclass(frozen=True)
class ResultReference:
    reference_id: str
    trial_id: str
    execution_id: str
    reference_type: str
    locator: str
    content_hash: str | None
    created_at: str
    actor_id: str


@dataclass(frozen=True)
class ArtifactReference(ResultReference):
    pass


@dataclass(frozen=True)
class LedgerAnchorManifestPayload:
    ledger_id: str
    as_of_ledger_sequence: int
    global_event_hash: str
    schema_version: str
    created_at: str
    created_by: str
    manifest_schema_version: str = "1"
    canonicalization_version: str = "AQ_LEDGER_ANCHOR_CANONICAL_V1"


@dataclass(frozen=True)
class LedgerAnchorManifest:
    payload: LedgerAnchorManifestPayload
    manifest_sha256: str


@dataclass(frozen=True)
class TrialHistorySnapshot:
    ledger_id: str
    schema_version: str
    as_of_ledger_sequence: int
    global_event_hash: str
    content_hash: str
    evidence: bytes
