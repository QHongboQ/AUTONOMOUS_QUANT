"""AQ's thin evidence and fail-closed policy boundary over DuckDB relations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import re

import duckdb
import pandas as pd
import pandera.pandas as pa


_HASH = re.compile(r"^[0-9a-f]{64}$")
_FIGI = re.compile(r"^[A-Z0-9]{12}$")
_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_EPISODE = re.compile(r"^P1EP-[0-9a-f]{64}$")
_AUTHORITY_SCHEMA_VERSION = "P2AcceptedProviderBindingFactsV1"
_AUTHORITY_FACT_COUNT = 12
_AUTHORITY_FILE_SHA256 = (
    "3cd9b13a1424609120a4e069ac2cf9f9b9aa61e2df919aa48cf51eeac616bc69"
)
_AUTHORITY_SOURCE_SHA256 = (
    "aaa2693823abdba72c0d4b564214217cc49bd28e6c0eb3ac1a659f3b4bef81c2"
)
_AUTHORITY_FACT_FIELDS = {
    "decision_role",
    "episode_id",
    "evidence_hashes",
    "fact_id",
    "forward_fill",
    "historical_ticker",
    "issuer_name_only_binding",
    "price_continuity_only_binding",
    "provider",
    "provider_asset_identifier",
    "provider_symbol",
    "scope",
    "successor_price_substitution",
    "synthetic_row",
    "ticker_text_only_binding",
    "valid_from",
    "valid_to",
}
_NO_FIELDS = {
    "forward_fill",
    "issuer_name_only_binding",
    "price_continuity_only_binding",
    "successor_price_substitution",
    "synthetic_row",
    "ticker_text_only_binding",
}


@dataclass(frozen=True, slots=True)
class OpenFigiEvidence:
    figi: str
    mapping_identifier: str

    def __post_init__(self) -> None:
        if self.figi.lower().startswith("tts-") or not _FIGI.fullmatch(self.figi):
            raise ValueError("OpenFIGI evidence requires a standard 12-character FIGI")


@dataclass(frozen=True, slots=True)
class SecEvidence:
    cik: int
    accession: str
    filing_type: str
    filed_date: date
    effective_date: date
    content_hash: str
    decision_role: str

    @classmethod
    def from_edgartools(
        cls, filing: object, *, effective_date: date, content_hash: str,
        decision_role: str,
    ) -> "SecEvidence":
        from edgar import Filing

        if not isinstance(filing, Filing):
            raise TypeError("SEC evidence must originate from edgartools")
        return cls(
            cik=int(filing.cik), accession=str(filing.accession_no),
            filing_type=str(filing.form),
            filed_date=date.fromisoformat(str(filing.filing_date)),
            effective_date=effective_date, content_hash=content_hash,
            decision_role=decision_role,
        )

    def __post_init__(self) -> None:
        if self.cik <= 0 or not _ACCESSION.fullmatch(self.accession):
            raise ValueError("invalid SEC filing identity")
        if not _HASH.fullmatch(self.content_hash) or not self.decision_role.strip():
            raise ValueError("invalid SEC decision evidence")


_SCHEMAS = {
    "binding_episodes": pa.DataFrameSchema({
        "case_id": pa.Column(str, unique=True),
        "episode_id": pa.Column(str, unique=True),
        "valid_from": pa.Column("datetime64[ns]"),
        "valid_to": pa.Column("datetime64[ns]"),
        "required_sessions": pa.Column(int, checks=pa.Check.ge(1)),
    }, strict=True),
    "binding_candidates": pa.DataFrameSchema({
        "case_id": pa.Column(str),
        "provider": pa.Column(str),
        "provider_asset_identifier": pa.Column(str),
        "provider_symbol": pa.Column(str),
        "provider_identity_supported": pa.Column(bool),
        "sec_identity_supported": pa.Column(bool),
        "openfigi_supported": pa.Column(bool),
    }, strict=True),
    "binding_observations": pa.DataFrameSchema({
        "provider_asset_identifier": pa.Column(str),
        "session_date": pa.Column("datetime64[ns]"),
        "close": pa.Column(float, nullable=False),
    }, strict=True),
    "binding_sessions": pa.DataFrameSchema({
        "case_id": pa.Column(str),
        "session_date": pa.Column("datetime64[ns]"),
    }, strict=True),
    "binding_authority_facts": pa.DataFrameSchema({
        "fact_id": pa.Column(str, unique=True),
        "episode_id": pa.Column(str),
        "provider": pa.Column(str),
        "provider_asset_identifier": pa.Column(str),
        "valid_from": pa.Column("datetime64[ns]"),
        "valid_to": pa.Column("datetime64[ns]"),
    }, strict=True),
}


def load_provider_binding_authority(path: Path | None = None) -> pd.DataFrame:
    """Load the one frozen, bounded provider-binding authority relation."""
    authority_path = path or Path(__file__).with_name(
        "accepted_provider_binding_facts.json"
    )
    raw = authority_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _AUTHORITY_FILE_SHA256:
        raise ValueError("provider-binding authority file hash mismatch")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("invalid provider-binding authority JSON") from error

    if set(payload) != {
        "expected_count", "facts", "schema_version",
        "source_private_artifact_sha256",
    }:
        raise ValueError("invalid provider-binding authority envelope")
    if payload["schema_version"] != _AUTHORITY_SCHEMA_VERSION:
        raise ValueError("unsupported provider-binding authority schema")
    if payload["source_private_artifact_sha256"] != _AUTHORITY_SOURCE_SHA256:
        raise ValueError("provider-binding authority source hash mismatch")
    facts = payload["facts"]
    if payload["expected_count"] != _AUTHORITY_FACT_COUNT or len(facts) != _AUTHORITY_FACT_COUNT:
        raise ValueError("provider-binding authority fact count mismatch")

    seen_fact_ids: set[str] = set()
    seen_bindings: set[tuple[str, str]] = set()
    rows = []
    for fact in facts:
        if not isinstance(fact, dict) or set(fact) != _AUTHORITY_FACT_FIELDS:
            raise ValueError("invalid provider-binding authority fact schema")
        if not _EPISODE.fullmatch(fact["episode_id"]):
            raise ValueError("invalid provider-binding episode identity")
        if fact["scope"] != "PROVIDER_BINDING_ONLY":
            raise ValueError("unsupported provider-binding authority scope")
        if any(fact[field] != "NO" for field in _NO_FIELDS):
            raise ValueError("unsafe provider-binding authority fact")
        if not all(
            isinstance(fact[field], str) and fact[field].strip()
            for field in (
                "decision_role", "fact_id", "historical_ticker", "provider",
                "provider_asset_identifier", "provider_symbol",
            )
        ):
            raise ValueError("incomplete provider-binding authority fact")
        hashes = fact["evidence_hashes"]
        if not isinstance(hashes, list) or not hashes or not all(
            isinstance(value, str) and _HASH.fullmatch(value) for value in hashes
        ):
            raise ValueError("invalid provider-binding authority evidence hash")
        try:
            valid_from = date.fromisoformat(fact["valid_from"])
            valid_to = date.fromisoformat(fact["valid_to"])
        except (TypeError, ValueError) as error:
            raise ValueError("invalid provider-binding authority date") from error
        if valid_from >= valid_to:
            raise ValueError("invalid provider-binding authority interval")
        binding_key = (fact["episode_id"], fact["provider"])
        if fact["fact_id"] in seen_fact_ids or binding_key in seen_bindings:
            raise ValueError("duplicate provider-binding authority fact")
        seen_fact_ids.add(fact["fact_id"])
        seen_bindings.add(binding_key)
        rows.append({
            "fact_id": fact["fact_id"],
            "episode_id": fact["episode_id"],
            "provider": fact["provider"],
            "provider_asset_identifier": fact["provider_asset_identifier"],
            "valid_from": pd.Timestamp(valid_from),
            "valid_to": pd.Timestamp(valid_to),
        })
    return _SCHEMAS["binding_authority_facts"].validate(pd.DataFrame(rows))


def evaluate_provider_bindings(
    connection: duckdb.DuckDBPyConnection,
    *, episodes: pd.DataFrame, candidates: pd.DataFrame,
    observations: pd.DataFrame, sessions: pd.DataFrame,
    authority_path: Path | None = None,
) -> pd.DataFrame:
    """Validate public relations, then delegate their composition to DuckDB."""
    tables = {
        "binding_episodes": episodes,
        "binding_candidates": candidates,
        "binding_observations": observations,
        "binding_sessions": sessions,
        "binding_authority_facts": load_provider_binding_authority(authority_path),
    }
    for name, frame in tables.items():
        connection.register(name, _SCHEMAS[name].validate(frame))
    sql = Path(__file__).with_name("binding.sql").read_text(encoding="utf-8")
    for statement in sql.split(";"):
        if statement.strip():
            connection.execute(statement)
    return connection.sql("SELECT * FROM binding_decisions ORDER BY case_id").df()
