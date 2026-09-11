"""Load the immutable, declarative P1 reconciliation fact set."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path

from ..canonical import sha256_hex
from ..domain.models import normalize_ticker


_FACTS_PATH = Path(__file__).with_name("accepted_reconciliation_facts.json")
_FACTS_SHA256 = "c1745a22c17c3a8a35bf56f504c1d96398c787492dce54a60ac85801799a9f62"
_CLASSIFICATIONS = {
    "GENUINE_RENAME",
    "SOURCE_BACKFILL",
    "TICKER_REUSE",
    "MEMBERSHIP_EXIT_REENTRY",
    "CORPORATE_SUCCESSION_NOT_MEMBERSHIP_TRANSFER",
    "FALSE_DIAGNOSTIC_BOUNDARY",
}


@dataclass(frozen=True, slots=True)
class IdentityFact:
    old_ticker: str
    new_ticker: str
    announcement_date: str | None
    effective_session: str
    evidence_id: str


@dataclass(frozen=True, slots=True)
class OverlayCaseFact:
    case_id: str
    old_ticker: str
    new_ticker: str
    effective_session: str
    start_session: str | None


@dataclass(frozen=True, slots=True)
class FindingResolutionFact:
    finding_id: str
    classification: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AcceptedFacts:
    schema_version: str
    identity_events: tuple[IdentityFact, ...]
    overlay_cases: tuple[OverlayCaseFact, ...]
    finding_resolutions: tuple[FindingResolutionFact, ...]
    expected_counts: tuple[tuple[str, int], ...]
    facts_hash: str

    def expected(self, name: str) -> int:
        return dict(self.expected_counts)[name]


def _iso(value: str | None, name: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError(f"invalid {name} in accepted reconciliation facts")


def load_accepted_facts() -> AcceptedFacts:
    """Load and fail closed on any malformed or incomplete accepted fact set."""
    raw = _FACTS_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _FACTS_SHA256:
        raise ValueError("accepted reconciliation facts differ from the frozen P1 authority")
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("schema_version") != "P1AcceptedReconciliationFactsV1":
        raise ValueError("unsupported accepted reconciliation fact schema")

    identities = tuple(IdentityFact(**item) for item in payload["identity_events"])
    overlays = tuple(OverlayCaseFact(**item) for item in payload["overlay_cases"])
    resolutions = tuple(
        FindingResolutionFact(
            finding_id=item["finding_id"],
            classification=item["classification"],
            evidence_ids=tuple(item["evidence_ids"]),
        )
        for item in payload["finding_resolutions"]
    )
    expected = tuple(sorted((str(key), int(value)) for key, value in payload["expected_counts"].items()))

    for item in identities:
        old = normalize_ticker(item.old_ticker)
        new = normalize_ticker(item.new_ticker)
        if old == new or not item.evidence_id:
            raise ValueError("invalid identity fact")
        _iso(item.announcement_date, "announcement_date", optional=True)
        _iso(item.effective_session, "effective_session")
    for item in overlays:
        normalize_ticker(item.old_ticker)
        normalize_ticker(item.new_ticker)
        _iso(item.effective_session, "overlay effective_session")
        _iso(item.start_session, "overlay start_session", optional=True)
    for item in resolutions:
        if len(item.finding_id) != 64 or item.classification not in _CLASSIFICATIONS:
            raise ValueError("invalid finding resolution fact")
        if not item.evidence_ids:
            raise ValueError("finding resolution fact requires evidence metadata")

    if len(identities) != 20 or len(overlays) != 9 or len(resolutions) != 37:
        raise ValueError("accepted reconciliation fact counts differ from the P1 contract")
    if len({(item.old_ticker, item.new_ticker, item.effective_session) for item in identities}) != 20:
        raise ValueError("duplicate accepted identity fact")
    if len({item.case_id for item in overlays}) != 9:
        raise ValueError("duplicate accepted overlay case")
    if len({item.finding_id for item in resolutions}) != 37:
        raise ValueError("duplicate accepted finding resolution")

    return AcceptedFacts(
        schema_version=payload["schema_version"],
        identity_events=identities,
        overlay_cases=overlays,
        finding_resolutions=resolutions,
        expected_counts=expected,
        facts_hash=sha256_hex(payload),
    )
