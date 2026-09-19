"""Direct, fail-closed Valuein projections into existing P5 contracts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
import math
from typing import Any, Literal

from aq_episode_sec_cik_binding import EpisodeSecCikBindingV1
from aq_fundamental_evidence import FundamentalEvidenceV1, canonical_decimal_value

IdentityClassification = Literal[
    "EXACT",
    "COMPATIBLE_CANDIDATE",
    "PARTIAL",
    "AMBIGUOUS",
    "NO_MATCH",
    "CONFLICT",
]

FROZEN_VALUEIN_METRIC_MAP = {
    "Revenue": "TotalRevenue",
    "NetIncome": "NetIncome",
    "Assets": "TotalAssets",
    "Liabilities": "TotalLiabilities",
    "CommonEquity": "StockholdersEquity",
    "NetCashFromOperatingActivities": "OperatingCashFlow",
    "CashAndCashEquivalents": "CashAndEquivalents",
    "CurrentAssetsTotal": "CurrentAssets",
    "CurrentLiabilitiesTotal": "TotalCurrentLiabilities",
    "ShortTermDebt": "ShortTermDebt",
    "LongTermDebt": "LongTermDebt",
}
_VALUEIN_TO_FROZEN = {value: key for key, value in FROZEN_VALUEIN_METRIC_MAP.items()}


def _missing(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _required(row: Mapping[str, Any], name: str) -> object:
    value = row.get(name)
    if _missing(value) or str(value).strip() == "":
        raise ValueError(f"Valuein row is missing {name}")
    return value


def _iso_date(value: object, name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValueError(f"Valuein {name} is not an ISO date") from exc


def _utc(value: object, name: str) -> datetime:
    if isinstance(value, datetime):
        result = value
    else:
        try:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Valuein {name} is not an ISO datetime") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"Valuein {name} must be timezone-aware")
    return result.astimezone(timezone.utc)


def _cik(value: object) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())
    if not digits or len(digits) > 10:
        raise ValueError("Valuein CIK is invalid")
    return digits.zfill(10)


def _episode_field(episode: object, name: str) -> object:
    if isinstance(episode, Mapping):
        return _required(episode, name)
    value = getattr(episode, name, None)
    if value is None:
        raise ValueError(f"P1 episode is missing {name}")
    return value


@dataclass(frozen=True, slots=True)
class ValueinIdentityDecision:
    episode_id: str
    ticker: str
    episode_valid_from: date
    episode_valid_to: date
    classification: IdentityClassification
    candidates: tuple[Mapping[str, Any], ...]
    membership_intervals: tuple[Mapping[str, Any], ...]
    candidate_ciks: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "ticker": self.ticker,
            "episode_valid_from": self.episode_valid_from.isoformat(),
            "episode_valid_to": self.episode_valid_to.isoformat(),
            "classification": self.classification,
            "candidate_count": len(self.candidates),
            "candidate_ciks": list(self.candidate_ciks),
            "candidates": [dict(row) for row in self.candidates],
            "membership_intervals": [dict(row) for row in self.membership_intervals],
            "reason": self.reason,
        }


def classify_valuein_identity(
    episode: object,
    security_rows: Iterable[Mapping[str, Any]],
    membership_rows: Iterable[Mapping[str, Any]],
    *,
    accepted_cik: str | None = None,
) -> ValueinIdentityDecision:
    """Classify exact-symbol historical rows without creating binding authority."""

    episode_id = str(_episode_field(episode, "episode_id"))
    ticker = str(_episode_field(episode, "normalized_ticker")).strip().upper()
    episode_from = _iso_date(_episode_field(episode, "valid_from"), "valid_from")
    episode_to = _iso_date(_episode_field(episode, "valid_to"), "valid_to")
    if episode_from >= episode_to:
        raise ValueError("P1 episode interval is empty")

    candidates: list[Mapping[str, Any]] = []
    for row in security_rows:
        if str(row.get("symbol") or "").strip().upper() != ticker:
            continue
        start = date.min if _missing(row.get("valid_from")) else _iso_date(row["valid_from"], "valid_from")
        end = date.max if _missing(row.get("valid_to")) else _iso_date(row["valid_to"], "valid_to")
        if start <= episode_to and episode_from <= end:
            candidates.append(row)

    if not candidates:
        return ValueinIdentityDecision(
            episode_id, ticker, episode_from, episode_to, "NO_MATCH", (), (), (),
            "no exact-symbol historical Valuein security interval overlaps the P1 episode",
        )

    identities: set[tuple[str, str, str]] = set()
    invalid_identity = False
    for row in candidates:
        try:
            identities.add(
                (
                    str(_required(row, "security_id")),
                    str(_required(row, "entity_id")),
                    _cik(_required(row, "cik")),
                )
            )
        except ValueError:
            invalid_identity = True
    candidate_ciks = tuple(sorted({identity[2] for identity in identities}))
    relevant_membership = tuple(
        row
        for row in membership_rows
        if not _missing(row.get("cik")) and _cik(row["cik"]) in candidate_ciks
    )

    normalized_accepted = _cik(accepted_cik) if accepted_cik is not None else None
    if invalid_identity or (normalized_accepted and candidate_ciks != (normalized_accepted,)):
        classification: IdentityClassification = "CONFLICT"
        reason = "candidate identity is incomplete or conflicts with accepted episode authority"
    elif len(identities) != 1 or len(candidates) != 1:
        classification = "AMBIGUOUS"
        reason = "more than one security-level Valuein identity overlaps the episode"
    else:
        candidate = candidates[0]
        start = date.min if _missing(candidate.get("valid_from")) else _iso_date(candidate["valid_from"], "valid_from")
        end = date.max if _missing(candidate.get("valid_to")) else _iso_date(candidate["valid_to"], "valid_to")
        if start == episode_from and end == episode_to:
            classification = "EXACT"
            reason = "one security-level identity exactly matches the P1 episode interval"
        elif start <= episode_from and end >= episode_to:
            classification = "COMPATIBLE_CANDIDATE"
            reason = "one identity contains the episode but is not automatic binding authority"
        else:
            classification = "PARTIAL"
            reason = "one identity overlaps but does not contain the full P1 episode"

    return ValueinIdentityDecision(
        episode_id,
        ticker,
        episode_from,
        episode_to,
        classification,
        tuple(candidates),
        relevant_membership,
        candidate_ciks,
        reason,
    )


def admit_exact_valuein_binding(
    decision: ValueinIdentityDecision,
    *,
    authoritative_episodes: Iterable[object],
    episode: object,
    snapshot_identity: str,
) -> EpisodeSecCikBindingV1:
    """Admit only an exact, membership-consistent Valuein relation."""

    if len(snapshot_identity) != 64 or any(
        character not in "0123456789abcdef" for character in snapshot_identity
    ):
        raise ValueError("Valuein snapshot_identity must be an exact SHA-256")
    if decision.classification != "EXACT" or len(decision.candidates) != 1:
        raise ValueError("only an EXACT Valuein relation may be admitted")
    candidate = decision.candidates[0]
    cik = _cik(_required(candidate, "cik"))
    if decision.candidate_ciks != (cik,):
        raise ValueError("exact Valuein relation lacks one unambiguous CIK")
    supporting = []
    for row in decision.membership_intervals:
        start = date.min if _missing(row.get("effective_date")) else _iso_date(row["effective_date"], "effective_date")
        end = date.max if _missing(row.get("removal_date")) else _iso_date(row["removal_date"], "removal_date")
        if _cik(_required(row, "cik")) == cik and start <= decision.episode_valid_from and end >= decision.episode_valid_to:
            supporting.append(row)
    if not supporting:
        raise ValueError("exact Valuein relation lacks containing historical membership evidence")
    membership = sorted(
        supporting,
        key=lambda row: (
            str(row.get("effective_date") or ""),
            str(row.get("removal_date") or ""),
            str(row.get("source") or ""),
        ),
    )[0]
    provenance_hash = str(_episode_field(episode, "provenance_hash"))
    evidence = (
        f"P1_PROVENANCE:{provenance_hash}",
        f"VALUEIN_SNAPSHOT_SHA256:{snapshot_identity}",
        "VALUEIN_SECURITY:"
        f"{_required(candidate, 'security_id')}:{_required(candidate, 'entity_id')}:"
        f"{cik}:{decision.episode_valid_from.isoformat()}:{decision.episode_valid_to.isoformat()}",
        "VALUEIN_MEMBERSHIP:"
        f"{membership.get('source') or 'UNKNOWN'}:{cik}:"
        f"{membership.get('effective_date')}:{membership.get('removal_date')}",
    )
    return EpisodeSecCikBindingV1.admit(
        authoritative_episodes=authoritative_episodes,
        episode_id=decision.episode_id,
        cik=cik,
        valid_from=decision.episode_valid_from,
        valid_to=decision.episode_valid_to,
        binding_classification="PASS_EXACT",
        evidence_source_identities=evidence,
    )


def map_valuein_metric(standard_concept: object) -> str:
    """Map exactly one of the frozen Valuein concepts; infer no synonyms."""

    try:
        return _VALUEIN_TO_FROZEN[str(standard_concept)]
    except KeyError as exc:
        raise ValueError("Valuein metric is outside the frozen 11-metric mapping") from exc


def materialize_valuein_fact(
    filing: Mapping[str, Any],
    fact: Mapping[str, Any],
    *,
    source_document_sha256: str,
    valuein_sdk_version: str,
    upstream_identity: str,
) -> FundamentalEvidenceV1:
    """Project one provenance-complete Valuein row into FundamentalEvidenceV1."""

    accession = str(_required(filing, "accession_id"))
    if str(_required(fact, "accession_id")) != accession:
        raise ValueError("Valuein filing and fact accessions differ")
    cik = _cik(_required(filing, "entity_id"))
    if _cik(_required(fact, "entity_id")) != cik:
        raise ValueError("Valuein filing and fact CIKs differ")
    filing_accepted = _utc(_required(filing, "accepted_at"), "filing accepted_at")
    fact_accepted = _utc(_required(fact, "accepted_at"), "fact accepted_at")
    if filing_accepted != fact_accepted:
        raise ValueError("Valuein filing and fact accepted_at differ")
    if len(source_document_sha256) != 64 or any(character not in "0123456789abcdef" for character in source_document_sha256):
        raise ValueError("exact SEC source_document_sha256 is required")

    map_valuein_metric(_required(fact, "standard_concept"))
    raw_value = _required(fact, "value")
    if isinstance(raw_value, bool) or not isinstance(raw_value, (str, int, Decimal)):
        raise ValueError("Valuein numeric value must avoid binary float")
    canonical_value = canonical_decimal_value(str(raw_value))
    concept = str(_required(fact, "concept"))
    if ":" not in concept:
        raise ValueError("Valuein concept must retain its taxonomy namespace")
    taxonomy_namespace, concept_name = concept.split(":", 1)
    period_end = _iso_date(_required(fact, "period_end"), "period_end")
    period_start = None if _missing(fact.get("period_start")) else _iso_date(fact["period_start"], "period_start")
    is_amendment = bool(filing.get("is_amendment")) or str(_required(filing, "form_type")).endswith("/A")

    fact_period = (
        {"period_start": period_start, "period_end": period_end, "instant": None}
        if period_start is not None
        else {"period_start": None, "period_end": None, "instant": period_end}
    )
    return FundamentalEvidenceV1.admit(
        schema_version="FundamentalEvidenceV1",
        entity={"cik": cik, "issuer_name": filing.get("issuer_name")},
        filing={
            "accession": accession,
            "form": str(_required(filing, "form_type")),
            "filing_date": _iso_date(_required(filing, "filing_date"), "filing_date"),
            "report_period_end": _iso_date(_required(filing, "report_date"), "report_date"),
            "acceptance_datetime": filing_accepted,
            "amendment_status": "AMENDMENT" if is_amendment else "ORIGINAL",
            "filing_vintage_role": "AMENDED_FILING" if is_amendment else "ORIGINAL_FILING",
        },
        availability={"first_available_at": filing_accepted},
        source={
            "authoritative_source": "SEC_EDGAR",
            "source_document_identity": f"SEC_FULL_SUBMISSION:{accession}",
            "source_document_url": filing.get("filing_url"),
            "source_document_sha256": source_document_sha256,
        },
        fact={
            "taxonomy_namespace": taxonomy_namespace,
            "concept": concept_name,
            "value": canonical_value,
            "unit": str(_required(fact, "unit")),
            "currency": fact.get("reporting_currency"),
            **fact_period,
            "context_identity": fact.get("fact_id"),
            "dimensions": None,
            "statement_classification": fact.get("statement_type"),
        },
        upstream={
            "parser_provider": "VALUEIN",
            "valuein_sdk_version": valuein_sdk_version,
            "upstream_identity": upstream_identity,
        },
    )


def prefer_exact_valuein_or_edgartools(
    *,
    valuein_evidence: FundamentalEvidenceV1 | None,
    edgartools_evidence: FundamentalEvidenceV1 | None,
) -> FundamentalEvidenceV1:
    """Apply the fixed two-source precedence without a router abstraction."""

    if valuein_evidence is None:
        if edgartools_evidence is None:
            raise ValueError("neither exact Valuein nor EdgarTools evidence is available")
        return edgartools_evidence
    if edgartools_evidence is not None:
        if (
            valuein_evidence.entity.cik != edgartools_evidence.entity.cik
            or valuein_evidence.filing.accession != edgartools_evidence.filing.accession
            or valuein_evidence.filing.form != edgartools_evidence.filing.form
            or valuein_evidence.filing.acceptance_datetime
            != edgartools_evidence.filing.acceptance_datetime
            or valuein_evidence.source.source_document_sha256
            != edgartools_evidence.source.source_document_sha256
        ):
            raise ValueError("Valuein and EdgarTools exact evidence disagree")
    return valuein_evidence


__all__ = [
    "FROZEN_VALUEIN_METRIC_MAP",
    "IdentityClassification",
    "ValueinIdentityDecision",
    "admit_exact_valuein_binding",
    "classify_valuein_identity",
    "map_valuein_metric",
    "materialize_valuein_fact",
    "prefer_exact_valuein_or_edgartools",
]
