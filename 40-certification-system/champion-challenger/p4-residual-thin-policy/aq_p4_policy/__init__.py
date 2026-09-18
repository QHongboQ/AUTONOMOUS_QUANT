"""Closed P4 lifecycle contracts and pure policy; no I/O or state ownership."""

from __future__ import annotations

import hashlib
from datetime import date
from enum import Enum
from typing import Annotated, Literal

import rfc8785
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Sha256Identity = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
NonEmptyIdentity = Annotated[str, StringConstraints(min_length=1)]
PRODUCTION_DECAY_POLICY_STATUS = "UNSET_REQUIRES_PREREGISTRATION"
DEFAULT_PRODUCTION_DECAY_THRESHOLDS = None


class LifecycleState(str, Enum):
    RESEARCH_CANDIDATE = "RESEARCH_CANDIDATE"
    CERTIFIED = "CERTIFIED"
    SHADOW = "SHADOW"
    CHAMPION = "CHAMPION"
    DEGRADED = "DEGRADED"
    RETIRED = "RETIRED"


AUTHORIZED_TRANSITIONS = frozenset(
    {
        (LifecycleState.RESEARCH_CANDIDATE, LifecycleState.CERTIFIED),
        (LifecycleState.CERTIFIED, LifecycleState.SHADOW),
        (LifecycleState.SHADOW, LifecycleState.CHAMPION),
        (LifecycleState.CHAMPION, LifecycleState.DEGRADED),
        (LifecycleState.DEGRADED, LifecycleState.RETIRED),
    }
)
TRANSITION_AUTHORITIES = {
    edge: ("P2" if edge[1] == LifecycleState.CERTIFIED else "P4")
    for edge in AUTHORIZED_TRANSITIONS
}


class ShadowStatus(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    COMPLETE_PASS = "COMPLETE_PASS"
    COMPLETE_FAIL = "COMPLETE_FAIL"


class DecisionKind(str, Enum):
    NO_CHANGE = "NO_CHANGE"
    ADMIT_SHADOW = "ADMIT_SHADOW"
    PROMOTE_CHAMPION = "PROMOTE_CHAMPION"
    MARK_DEGRADED = "MARK_DEGRADED"
    RETIRE = "RETIRE"
    CHALLENGER_NEEDED = "CHALLENGER_NEEDED"
    RESEARCH_REQUESTED = "RESEARCH_REQUESTED"
    REJECT_TRANSITION = "REJECT_TRANSITION"


class DecisionReason(str, Enum):
    STRUCTURALLY_UNAUTHORIZED = "STRUCTURALLY_UNAUTHORIZED"
    VALID_P2_CERTIFICATION_REQUIRED = "VALID_P2_CERTIFICATION_REQUIRED"
    SHADOW_EVIDENCE_INVALID = "SHADOW_EVIDENCE_INVALID"
    SHADOW_ADMISSION_ELIGIBLE = "SHADOW_ADMISSION_ELIGIBLE"
    SHADOW_EVIDENCE_NOT_COMPLETE_PASS = "SHADOW_EVIDENCE_NOT_COMPLETE_PASS"
    CHAMPION_PROMOTION_ELIGIBLE = "CHAMPION_PROMOTION_ELIGIBLE"
    DECAY_POLICY_NOT_PREREGISTERED = "DECAY_POLICY_NOT_PREREGISTERED"
    STATISTICAL_CHANGE_NOT_DETECTED = "STATISTICAL_CHANGE_NOT_DETECTED"
    FINANCIAL_CORROBORATION_NOT_ADVERSE = "FINANCIAL_CORROBORATION_NOT_ADVERSE"
    FINANCIAL_DECAY_CORROBORATED = "FINANCIAL_DECAY_CORROBORATED"
    RETIREMENT_AUTHORIZATION_REQUIRED = "RETIREMENT_AUTHORIZATION_REQUIRED"
    RETIREMENT_AUTHORIZED = "RETIREMENT_AUTHORIZED"
    NO_CHAMPION = "NO_CHAMPION"
    CHAMPION_DEGRADED = "CHAMPION_DEGRADED"


class ChallengerReason(str, Enum):
    NO_CHAMPION = "NO_CHAMPION"
    CHAMPION_DEGRADED = "CHAMPION_DEGRADED"


class P2CertificationEvidenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["P2CertificationEvidenceV1"]
    authority: Literal["P2"]
    candidate_id: Sha256Identity
    protocol_identity: Literal["P2_CERTIFICATION_PROTOCOL_V1"]
    protocol_version: Literal["V1"]
    certification_artifact_identity: Sha256Identity
    certification_status: Literal[
        "CERTIFIED", "REJECTED", "NOT_ELIGIBLE_NO_PRISTINE_OOS"
    ]
    evidence_identity: Sha256Identity
    evidence_classification: Literal[
        "REAL_P2_CERTIFICATION_EVIDENCE", "TEST_FIXTURE_NOT_REAL_EVIDENCE"
    ]


class ShadowEvidenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["ShadowEvidenceV1"]
    candidate_id: Sha256Identity
    certification_evidence_identity: Sha256Identity
    certification_artifact_identity: Sha256Identity
    observation_start: date
    observation_end: date
    calendar_identity: Sha256Identity
    prediction_evidence_identity: Sha256Identity
    outcome_return_evidence_identity: Sha256Identity | None
    cost_assumption_identity: Sha256Identity
    qlib_experiment_id: NonEmptyIdentity
    qlib_recorder_id: NonEmptyIdentity
    mlflow_experiment_id: NonEmptyIdentity
    mlflow_run_id: NonEmptyIdentity
    dvc_reproducibility_identity: Sha256Identity
    zero_capital_attestation: bool
    completion_status: ShadowStatus

    @model_validator(mode="after")
    def validate_boundary(self) -> "ShadowEvidenceV1":
        if self.observation_end < self.observation_start:
            raise ValueError("Shadow observation interval is reversed")
        if self.qlib_experiment_id != self.mlflow_experiment_id:
            raise ValueError("Qlib and MLflow experiment identities differ")
        if self.qlib_recorder_id != self.mlflow_run_id:
            raise ValueError("Qlib Recorder and MLflow run identities differ")
        return self


class DetectorEvidenceReferenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["DetectorEvidenceReferenceV1"]
    candidate_id: Sha256Identity
    detector_evidence_identity: Sha256Identity
    metric_observation_stream_identity: Sha256Identity
    upstream_identity_projection_identity: Sha256Identity
    metric_kind: Literal["RANK_IC"]
    change_detected: bool
    change_event_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_change_count(self) -> "DetectorEvidenceReferenceV1":
        if self.change_detected != (self.change_event_count > 0):
            raise ValueError("change flag and count disagree")
        return self


class RankICSummaryEvidenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["RankICSummaryEvidenceV1"]
    candidate_id: Sha256Identity
    metric_kind: Literal["RANK_IC"]
    upstream_identity_projection_identity: Sha256Identity
    reference_evidence_identity: Sha256Identity
    current_evidence_identity: Sha256Identity
    reference_rank_ic: float = Field(ge=-1.0, le=1.0)
    current_rank_ic: float = Field(ge=-1.0, le=1.0)
    reference_sample_count: int = Field(ge=1)
    current_sample_count: int = Field(ge=1)
    persistence_evidence_count: int = Field(ge=0)


class FinancialDecayPolicyConfigV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["FinancialDecayPolicyConfigV1"]
    status: Literal["UNSET_REQUIRES_PREREGISTRATION", "TEST_ONLY_POLICY_CONFIG"]
    metric_kind: Literal["RANK_IC"]
    minimum_deterioration: float | None = Field(default=None, gt=0.0, le=2.0)
    minimum_reference_sample_count: int | None = Field(default=None, ge=1)
    minimum_current_sample_count: int | None = Field(default=None, ge=1)
    required_change_events: int | None = Field(default=None, ge=1)
    required_persistence_evidence_count: int | None = Field(default=None, ge=1)
    corroboration_required: Literal[True]

    @model_validator(mode="after")
    def validate_status(self) -> "FinancialDecayPolicyConfigV1":
        values = (
            self.minimum_deterioration,
            self.minimum_reference_sample_count,
            self.minimum_current_sample_count,
            self.required_change_events,
            self.required_persistence_evidence_count,
        )
        if self.status == PRODUCTION_DECAY_POLICY_STATUS and any(v is not None for v in values):
            raise ValueError("unregistered production policy cannot carry thresholds")
        if self.status == "TEST_ONLY_POLICY_CONFIG" and any(v is None for v in values):
            raise ValueError("test policy must supply every condition")
        return self


class RetirementAuthorizationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["RetirementAuthorizationV1"]
    candidate_id: Sha256Identity
    authorization_identity: Sha256Identity
    authority: Literal["HUMAN_AUTHORITY", "TEST_FIXTURE"]
    evidence_classification: Literal[
        "HUMAN_AUTHORITY_RETIREMENT_AUTHORIZATION",
        "TEST_ONLY_RETIREMENT_AUTHORIZATION",
    ]
    authorized: bool

    @model_validator(mode="after")
    def validate_authority(self) -> "RetirementAuthorizationV1":
        expected = (
            "HUMAN_AUTHORITY_RETIREMENT_AUTHORIZATION"
            if self.authority == "HUMAN_AUTHORITY"
            else "TEST_ONLY_RETIREMENT_AUTHORIZATION"
        )
        if self.evidence_classification != expected:
            raise ValueError("retirement authority and classification differ")
        return self


class LifecycleDecisionEvidenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["LifecycleDecisionEvidenceV1"]
    candidate_id: Sha256Identity
    current_state: LifecycleState | None
    target_state: LifecycleState | None
    decision_kind: DecisionKind
    reason: DecisionReason
    source_evidence_identities: tuple[Sha256Identity, ...]
    evidence_classification: Literal[
        "REAL_EXTERNAL_EVIDENCE", "TEST_FIXTURE_NOT_REAL_EVIDENCE"
    ]
    live_trading_authorized: Literal[False]
    capital_authorized: Literal[False]
    production_activation_authorized: Literal[False]
    p4_champion_role_is_not_production_authorization: Literal[True]

    @model_validator(mode="after")
    def validate_decision_shape(self) -> "LifecycleDecisionEvidenceV1":
        expected = {
            DecisionKind.NO_CHANGE: None,
            DecisionKind.ADMIT_SHADOW: LifecycleState.SHADOW,
            DecisionKind.PROMOTE_CHAMPION: LifecycleState.CHAMPION,
            DecisionKind.MARK_DEGRADED: LifecycleState.DEGRADED,
            DecisionKind.RETIRE: LifecycleState.RETIRED,
            DecisionKind.CHALLENGER_NEEDED: None,
            DecisionKind.RESEARCH_REQUESTED: None,
        }
        if self.decision_kind in expected and self.target_state != expected[self.decision_kind]:
            raise ValueError("decision kind and target state disagree")
        if tuple(sorted(set(self.source_evidence_identities))) != self.source_evidence_identities:
            raise ValueError("decision source identities must be sorted and unique")
        return self


class ResearchRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["ResearchRequestV1"]
    request_id: Sha256Identity
    reason: ChallengerReason
    source_evidence_identities: tuple[Sha256Identity, ...]
    asset_universe_scope_identity: Sha256Identity
    allowed_research_families: tuple[NonEmptyIdentity, ...]
    research_budget_identity: Sha256Identity
    target_protocol_context: NonEmptyIdentity
    evidence_cutoff: date
    request_provenance: Sha256Identity

    @model_validator(mode="after")
    def validate_identity(self) -> "ResearchRequestV1":
        if not self.source_evidence_identities or not self.allowed_research_families:
            raise ValueError("request evidence and research families are required")
        if tuple(sorted(set(self.source_evidence_identities))) != self.source_evidence_identities:
            raise ValueError("source identities must be sorted and unique")
        if tuple(sorted(set(self.allowed_research_families))) != self.allowed_research_families:
            raise ValueError("research families must be sorted and unique")
        if self.request_id != _request_id(self.model_dump(mode="json", exclude={"request_id"})):
            raise ValueError("request_id does not match RFC 8785 identity")
        return self


def is_structurally_authorized_transition(
    current_state: LifecycleState, target_state: LifecycleState
) -> bool:
    return (current_state, target_state) in AUTHORIZED_TRANSITIONS


def transition_authority(
    current_state: LifecycleState, target_state: LifecycleState
) -> Literal["P2", "P4"] | None:
    return TRANSITION_AUTHORITIES.get((current_state, target_state))


def challenger_role_allowed(state: LifecycleState) -> bool:
    return state in {LifecycleState.CERTIFIED, LifecycleState.SHADOW}


def _request_id(fields: dict[str, object]) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(fields)).hexdigest()


def _decision(
    candidate_id: str,
    current: LifecycleState | None,
    target: LifecycleState | None,
    kind: DecisionKind,
    reason: DecisionReason,
    sources: tuple[str, ...] = (),
    test: bool = False,
) -> LifecycleDecisionEvidenceV1:
    return LifecycleDecisionEvidenceV1(
        contract_version="LifecycleDecisionEvidenceV1",
        candidate_id=candidate_id,
        current_state=current,
        target_state=target,
        decision_kind=kind,
        reason=reason,
        source_evidence_identities=tuple(sorted(set(sources))),
        evidence_classification=(
            "TEST_FIXTURE_NOT_REAL_EVIDENCE" if test else "REAL_EXTERNAL_EVIDENCE"
        ),
        live_trading_authorized=False,
        capital_authorized=False,
        production_activation_authorized=False,
        p4_champion_role_is_not_production_authorization=True,
    )


def _certification_valid(
    candidate_id: str,
    evidence: P2CertificationEvidenceV1 | None,
    allow_test_fixture: bool,
) -> bool:
    return evidence is not None and evidence.candidate_id == candidate_id and (
        evidence.certification_status == "CERTIFIED"
    ) and (
        evidence.evidence_classification == "REAL_P2_CERTIFICATION_EVIDENCE"
        or (
            allow_test_fixture
            and evidence.evidence_classification == "TEST_FIXTURE_NOT_REAL_EVIDENCE"
        )
    )


def _shadow_valid(
    candidate_id: str,
    certification: P2CertificationEvidenceV1,
    shadow: ShadowEvidenceV1,
) -> bool:
    return (
        shadow.candidate_id == candidate_id
        and shadow.certification_evidence_identity == certification.evidence_identity
        and shadow.certification_artifact_identity
        == certification.certification_artifact_identity
        and shadow.zero_capital_attestation
    )


def _shadow_sources(
    certification: P2CertificationEvidenceV1 | None, shadow: ShadowEvidenceV1
) -> tuple[str, ...]:
    return (shadow.dvc_reproducibility_identity,) + (
        () if certification is None else (certification.evidence_identity,)
    )


def admit_shadow(
    *, current_state: LifecycleState, candidate_id: str,
    certification: P2CertificationEvidenceV1 | None, shadow: ShadowEvidenceV1,
    allow_test_fixture: bool = False,
) -> LifecycleDecisionEvidenceV1:
    test = certification is not None and certification.evidence_classification.startswith("TEST_")
    sources = _shadow_sources(certification, shadow)
    if not is_structurally_authorized_transition(current_state, LifecycleState.SHADOW):
        return _decision(candidate_id, current_state, LifecycleState.SHADOW, DecisionKind.REJECT_TRANSITION, DecisionReason.STRUCTURALLY_UNAUTHORIZED, sources, test)
    if not _certification_valid(candidate_id, certification, allow_test_fixture):
        return _decision(candidate_id, current_state, LifecycleState.SHADOW, DecisionKind.REJECT_TRANSITION, DecisionReason.VALID_P2_CERTIFICATION_REQUIRED, sources, test)
    if not _shadow_valid(candidate_id, certification, shadow):
        return _decision(candidate_id, current_state, LifecycleState.SHADOW, DecisionKind.REJECT_TRANSITION, DecisionReason.SHADOW_EVIDENCE_INVALID, sources, test)
    return _decision(candidate_id, current_state, LifecycleState.SHADOW, DecisionKind.ADMIT_SHADOW, DecisionReason.SHADOW_ADMISSION_ELIGIBLE, sources, test)


def promote_champion(
    *, current_state: LifecycleState, candidate_id: str,
    certification: P2CertificationEvidenceV1 | None, shadow: ShadowEvidenceV1,
    allow_test_fixture: bool = False,
) -> LifecycleDecisionEvidenceV1:
    test = certification is not None and certification.evidence_classification.startswith("TEST_")
    sources = _shadow_sources(certification, shadow)
    if not is_structurally_authorized_transition(current_state, LifecycleState.CHAMPION):
        return _decision(candidate_id, current_state, LifecycleState.CHAMPION, DecisionKind.REJECT_TRANSITION, DecisionReason.STRUCTURALLY_UNAUTHORIZED, sources, test)
    if not _certification_valid(candidate_id, certification, allow_test_fixture):
        return _decision(candidate_id, current_state, LifecycleState.CHAMPION, DecisionKind.REJECT_TRANSITION, DecisionReason.VALID_P2_CERTIFICATION_REQUIRED, sources, test)
    if not _shadow_valid(candidate_id, certification, shadow):
        return _decision(candidate_id, current_state, LifecycleState.CHAMPION, DecisionKind.REJECT_TRANSITION, DecisionReason.SHADOW_EVIDENCE_INVALID, sources, test)
    if shadow.completion_status != ShadowStatus.COMPLETE_PASS:
        return _decision(candidate_id, current_state, None, DecisionKind.NO_CHANGE, DecisionReason.SHADOW_EVIDENCE_NOT_COMPLETE_PASS, sources, test)
    return _decision(candidate_id, current_state, LifecycleState.CHAMPION, DecisionKind.PROMOTE_CHAMPION, DecisionReason.CHAMPION_PROMOTION_ELIGIBLE, sources, test)


def mark_degraded(
    *, current_state: LifecycleState, candidate_id: str,
    detector: DetectorEvidenceReferenceV1, financial: RankICSummaryEvidenceV1,
    config: FinancialDecayPolicyConfigV1 | None,
) -> LifecycleDecisionEvidenceV1:
    sources = (
        detector.detector_evidence_identity, detector.metric_observation_stream_identity,
        detector.upstream_identity_projection_identity,
        financial.reference_evidence_identity, financial.current_evidence_identity,
    )
    if not is_structurally_authorized_transition(current_state, LifecycleState.DEGRADED):
        return _decision(candidate_id, current_state, LifecycleState.DEGRADED, DecisionKind.REJECT_TRANSITION, DecisionReason.STRUCTURALLY_UNAUTHORIZED, sources)
    identities_match = (
        detector.candidate_id == financial.candidate_id == candidate_id
        and detector.upstream_identity_projection_identity
        == financial.upstream_identity_projection_identity
    )
    if not identities_match:
        return _decision(candidate_id, current_state, LifecycleState.DEGRADED, DecisionKind.REJECT_TRANSITION, DecisionReason.FINANCIAL_CORROBORATION_NOT_ADVERSE, sources)
    if config is None or config.status == PRODUCTION_DECAY_POLICY_STATUS:
        return _decision(candidate_id, current_state, LifecycleState.DEGRADED, DecisionKind.REJECT_TRANSITION, DecisionReason.DECAY_POLICY_NOT_PREREGISTERED, sources)
    if not detector.change_detected or detector.change_event_count < config.required_change_events:
        return _decision(candidate_id, current_state, None, DecisionKind.NO_CHANGE, DecisionReason.STATISTICAL_CHANGE_NOT_DETECTED, sources, True)
    adverse = (
        financial.reference_sample_count >= config.minimum_reference_sample_count
        and financial.current_sample_count >= config.minimum_current_sample_count
        and financial.persistence_evidence_count >= config.required_persistence_evidence_count
        and financial.reference_rank_ic - financial.current_rank_ic
        >= config.minimum_deterioration
        and financial.current_rank_ic < financial.reference_rank_ic
    )
    if not adverse:
        return _decision(candidate_id, current_state, None, DecisionKind.NO_CHANGE, DecisionReason.FINANCIAL_CORROBORATION_NOT_ADVERSE, sources, True)
    return _decision(candidate_id, current_state, LifecycleState.DEGRADED, DecisionKind.MARK_DEGRADED, DecisionReason.FINANCIAL_DECAY_CORROBORATED, sources, True)


def retire(
    *, current_state: LifecycleState, candidate_id: str,
    authorization: RetirementAuthorizationV1 | None,
) -> LifecycleDecisionEvidenceV1:
    sources = () if authorization is None else (authorization.authorization_identity,)
    test = authorization is not None and authorization.authority == "TEST_FIXTURE"
    if not is_structurally_authorized_transition(current_state, LifecycleState.RETIRED):
        return _decision(candidate_id, current_state, LifecycleState.RETIRED, DecisionKind.REJECT_TRANSITION, DecisionReason.STRUCTURALLY_UNAUTHORIZED, sources, test)
    if authorization is None or authorization.candidate_id != candidate_id or not authorization.authorized:
        return _decision(candidate_id, current_state, LifecycleState.RETIRED, DecisionKind.REJECT_TRANSITION, DecisionReason.RETIREMENT_AUTHORIZATION_REQUIRED, sources, test)
    return _decision(candidate_id, current_state, LifecycleState.RETIRED, DecisionKind.RETIRE, DecisionReason.RETIREMENT_AUTHORIZED, sources, test)


def challenger_needed(
    *, candidate_id: str, reason: ChallengerReason,
    current_champion_state: LifecycleState | None,
    source_evidence_identities: tuple[str, ...], test_fixture: bool = False,
) -> LifecycleDecisionEvidenceV1:
    valid = (reason == ChallengerReason.NO_CHAMPION and current_champion_state is None) or (
        reason == ChallengerReason.CHAMPION_DEGRADED
        and current_champion_state == LifecycleState.DEGRADED
    )
    return _decision(
        candidate_id, current_champion_state, None,
        DecisionKind.CHALLENGER_NEEDED if valid else DecisionKind.REJECT_TRANSITION,
        DecisionReason(reason.value) if valid else DecisionReason.STRUCTURALLY_UNAUTHORIZED,
        source_evidence_identities, test_fixture,
    )


def build_research_request(
    *, challenger_decision: LifecycleDecisionEvidenceV1,
    asset_universe_scope_identity: str, allowed_research_families: tuple[str, ...],
    research_budget_identity: str, target_protocol_context: str,
    evidence_cutoff: date, request_provenance: str,
) -> ResearchRequestV1:
    if challenger_decision.decision_kind != DecisionKind.CHALLENGER_NEEDED:
        raise ValueError("ResearchRequestV1 requires CHALLENGER_NEEDED evidence")
    fields = {
        "contract_version": "ResearchRequestV1",
        "reason": ChallengerReason(challenger_decision.reason.value).value,
        "source_evidence_identities": sorted(set(challenger_decision.source_evidence_identities)),
        "asset_universe_scope_identity": asset_universe_scope_identity,
        "allowed_research_families": sorted(set(allowed_research_families)),
        "research_budget_identity": research_budget_identity,
        "target_protocol_context": target_protocol_context,
        "evidence_cutoff": evidence_cutoff.isoformat(),
        "request_provenance": request_provenance,
    }
    return ResearchRequestV1(request_id=_request_id(fields), **fields)
