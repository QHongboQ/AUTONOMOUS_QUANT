"""Deterministic adapter for the pinned fja05680/sp500 snapshot CSV."""

from __future__ import annotations

from datetime import date
import hashlib
import io

import pandas as pd

from ..canonical import canonical_bytes, deterministic_id, sha256_hex
from ..contracts import (
    AmbiguityState,
    IndexMembershipEventV1,
    MembershipAction,
    SessionBoundary,
    SnapshotObservationV1,
    SourceManifestV1,
    SourceRole,
    TickerEpisodeOverlayV1,
    TickerIdentityEventV1,
    normalize_ticker,
)
from ..overlays import ResolvedObservation, apply_ticker_overlays
from ..schema.pandera import (
    validate_membership_event_table,
    validate_snapshot_observation_table,
    validate_fja_source_table,
)


FJA_ADAPTER_VERSION = "fja-sp500-snapshot-adapter-v1"
RECONCILED_DERIVATION_VERSION = "identity-aware-resolved-snapshot-difference-v1"


def raw_sha256(raw_bytes: bytes) -> str:
    """Hash exact upstream bytes without canonical re-encoding."""

    return hashlib.sha256(raw_bytes).hexdigest()


def _read_rows(raw_bytes: bytes) -> tuple[tuple[str, tuple[str, ...]], ...]:
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("FJA source must be UTF-8 CSV") from exc
    try:
        frame = pd.read_csv(
            io.StringIO(text, newline=""),
            dtype="string",
            keep_default_na=False,
        )
    except (pd.errors.ParserError, UnicodeError, ValueError) as exc:
        raise ValueError("FJA source must be a two-column CSV table") from exc
    if "date" in frame:
        frame["date"] = frame["date"].str.strip()
    validate_fja_source_table(frame.to_dict(orient="records"))
    rows: list[tuple[str, tuple[str, ...]]] = []
    for line_number, row in enumerate(frame.itertuples(index=False), start=2):
        session = row.date
        raw_tickers = row.tickers.split(",")
        tickers = tuple(sorted(normalize_ticker(item) for item in raw_tickers if item.strip()))
        if not tickers or len(tickers) != len(set(tickers)):
            raise ValueError(f"invalid FJA roster on line {line_number}")
        rows.append((session, tickers))
    return tuple(rows)


def build_fja_manifest(
    raw_bytes: bytes,
    *,
    commit: str,
    source_file: str,
    retrieved_at: str,
) -> SourceManifestV1:
    """Create the immutable historical-seed manifest from exact bytes."""

    rows = _read_rows(raw_bytes)
    raw_hash = raw_sha256(raw_bytes)
    source_id = deterministic_id("P1SRC-", {
        "adapter_version": FJA_ADAPTER_VERSION,
        "commit": commit,
        "repo": "fja05680/sp500",
        "source_file": source_file,
        "sha256": raw_hash,
    })
    return SourceManifestV1(
        source_id=source_id,
        source_role=SourceRole.HISTORICAL_SEED,
        source_type="pinned_repository_csv_snapshot_history",
        source_url_or_repo="https://github.com/fja05680/sp500",
        source_commit_or_revision=commit,
        retrieved_at=retrieved_at,
        media_type="text/csv",
        byte_length=len(raw_bytes),
        sha256=raw_hash,
        license_observation="MIT (repository LICENSE at pinned commit)",
        coverage_start=rows[0][0],
        coverage_end=rows[-1][0],
        ancestry=(),
        adapter_version=FJA_ADAPTER_VERSION,
    )


def parse_fja_snapshots(
    raw_bytes: bytes,
    manifest: SourceManifestV1,
    *,
    start_date: str,
    end_date: str,
    start_session: str | None = None,
    index_id: str = "SP500",
) -> tuple[SnapshotObservationV1, ...]:
    """Normalize source snapshots, optionally carrying the as-of seed to a session."""

    if manifest.source_role is not SourceRole.HISTORICAL_SEED:
        raise ValueError("FJA snapshots require a HISTORICAL_SEED manifest")
    if raw_sha256(raw_bytes) != manifest.sha256 or len(raw_bytes) != manifest.byte_length:
        raise ValueError("FJA source bytes do not match the pinned manifest")
    date.fromisoformat(start_date)
    date.fromisoformat(end_date)
    if start_date > end_date:
        raise ValueError("requested snapshot range is reversed")
    rows = _read_rows(raw_bytes)
    selected: list[tuple[str, str, tuple[str, ...]]] = []
    if start_session is not None:
        date.fromisoformat(start_session)
        if not start_date <= start_session <= end_date:
            raise ValueError("start session must be inside the requested range")
        seeds = [row for row in rows if row[0] <= start_session]
        if not seeds:
            raise ValueError("no FJA as-of seed exists on or before start session")
        source_session, tickers = seeds[-1]
        selected.append((start_session, source_session, tickers))
        selected.extend(
            (session, session, row_tickers)
            for session, row_tickers in rows
            if start_session < session <= end_date
        )
    else:
        selected.extend(
            (session, session, tickers)
            for session, tickers in rows
            if start_date <= session <= end_date
        )
    observations: list[SnapshotObservationV1] = []
    for session, source_session, tickers in selected:
        evidence_hash = sha256_hex({
            "raw_source_sha256": manifest.sha256,
            "source_session": source_session,
            "session": session,
            "tickers": tickers,
        })
        identity = {
            "index_id": index_id,
            "session": session,
            "source_id": manifest.source_id,
            "tickers": tickers,
        }
        observations.append(SnapshotObservationV1(
            observation_id=deterministic_id("P1OBS-", identity),
            index_id=index_id,
            effective_session=session,
            tickers=tickers,
            source_id=manifest.source_id,
            evidence_hash=evidence_hash,
        ))
    if not observations:
        raise ValueError("no FJA snapshots in requested range")
    result = tuple(observations)
    validate_snapshot_observation_table(result)
    return result


def build_membership_event_manifest(
    seed_manifest: SourceManifestV1,
    observations: tuple[SnapshotObservationV1, ...],
) -> SourceManifestV1:
    """Manifest the exact-set-difference event stream as a derived lineage."""

    if not observations:
        raise ValueError("derived event manifest requires observations")
    logical = {
        "algorithm": "consecutive-snapshot-exact-set-difference-v1",
        "observations": observations,
        "seed_manifest_hash": seed_manifest.manifest_hash,
    }
    normalized_hash = sha256_hex(logical)
    return SourceManifestV1(
        source_id=deterministic_id("P1SRC-", logical),
        source_role=SourceRole.PRECISE_MEMBERSHIP_EVENTS,
        source_type="derived_consecutive_snapshot_set_difference",
        source_url_or_repo=seed_manifest.source_url_or_repo,
        source_commit_or_revision=seed_manifest.source_commit_or_revision,
        retrieved_at=seed_manifest.retrieved_at,
        media_type="application/vnd.aq.pit-membership-events+json",
        byte_length=len(canonical_bytes(logical)),
        sha256=normalized_hash,
        license_observation=seed_manifest.license_observation,
        coverage_start=observations[0].effective_session,
        coverage_end=observations[-1].effective_session,
        ancestry=(seed_manifest.source_id,),
        adapter_version="consecutive-snapshot-exact-set-difference-v1",
    )


def derive_membership_events(
    observations: tuple[SnapshotObservationV1, ...],
    event_manifest: SourceManifestV1,
) -> tuple[IndexMembershipEventV1, ...]:
    """Derive REMOVE then ADD events from exact consecutive snapshot set differences."""

    if event_manifest.source_role is not SourceRole.PRECISE_MEMBERSHIP_EVENTS:
        raise ValueError("derived events require a PRECISE_MEMBERSHIP_EVENTS manifest")
    ordered = tuple(sorted(observations, key=lambda item: (item.effective_session, item.observation_id)))
    validate_snapshot_observation_table(ordered)
    events: list[IndexMembershipEventV1] = []
    for prior, current in zip(ordered, ordered[1:]):
        if prior.index_id != current.index_id:
            raise ValueError("cannot diff observations from different indexes")
        prior_set = set(prior.tickers)
        current_set = set(current.tickers)
        transitions = (
            *((MembershipAction.REMOVE, ticker) for ticker in sorted(prior_set - current_set)),
            *((MembershipAction.ADD, ticker) for ticker in sorted(current_set - prior_set)),
        )
        transition_hash = sha256_hex({
            "prior_observation": prior,
            "current_observation": current,
            "removed": tuple(sorted(prior_set - current_set)),
            "added": tuple(sorted(current_set - prior_set)),
        })
        for action, ticker in transitions:
            identity = {
                "action": action,
                "effective_session": current.effective_session,
                "index_id": current.index_id,
                "source_id": event_manifest.source_id,
                "ticker": ticker,
            }
            events.append(IndexMembershipEventV1(
                event_id=deterministic_id("P1MEM-", identity),
                index_id=current.index_id,
                action=action,
                source_ticker=ticker,
                announcement_date=None,
                effective_date=current.effective_session,
                effective_session=current.effective_session,
                boundary_semantics=SessionBoundary.SOURCE_DEFINED,
                source_id=event_manifest.source_id,
                evidence_hash=transition_hash,
                reason="exact consecutive FJA snapshot set difference",
            ))
    result = tuple(events)
    validate_membership_event_table(result)
    return result


def build_reconciled_membership_event_manifest(
    seed_manifest: SourceManifestV1,
    observations: tuple[SnapshotObservationV1, ...],
    resolved_observations: tuple[ResolvedObservation, ...],
    ticker_events: tuple[TickerIdentityEventV1, ...],
    overlays: tuple[TickerEpisodeOverlayV1, ...],
) -> SourceManifestV1:
    """Manifest the distinct identity-aware reconciled derivation path."""

    if not observations or not resolved_observations:
        raise ValueError("reconciled event manifest requires observations")
    if seed_manifest.source_role is not SourceRole.HISTORICAL_SEED:
        raise ValueError("reconciled derivation requires a HISTORICAL_SEED manifest")
    if any(item.source_id != seed_manifest.source_id for item in observations):
        raise ValueError("raw observations do not belong to the seed manifest")
    raw_ids = {item.observation_id for item in observations}
    if raw_ids != {item.observation_id for item in resolved_observations}:
        raise ValueError("resolved observations must map exactly to raw observations")
    canonical_resolution = apply_ticker_overlays(observations, ticker_events, overlays)
    if tuple(sorted(resolved_observations, key=lambda item: item.observation_id)) != tuple(sorted(
        canonical_resolution.observations,
        key=lambda item: item.observation_id,
    )):
        raise ValueError(
            "resolved observations are not the deterministic output of raw observations and overlays"
        )
    overlay_map = {item.overlay_id: item for item in overlays}
    applied_ids = {
        overlay_id
        for item in resolved_observations
        for overlay_id in item.applied_overlay_ids
    }
    if not applied_ids <= set(overlay_map):
        raise ValueError("resolved observation references an unknown overlay")
    logical = {
        "algorithm": RECONCILED_DERIVATION_VERSION,
        "raw_observations": tuple(sorted(observations, key=lambda item: item.observation_id)),
        "resolved_observations": tuple(sorted(resolved_observations, key=lambda item: item.observation_id)),
        "ticker_events": tuple(sorted(ticker_events, key=lambda item: item.event_id)),
        "applied_overlays": tuple(sorted(
            (overlay_map[item] for item in applied_ids),
            key=lambda item: item.overlay_id,
        )),
        "seed_manifest_hash": seed_manifest.manifest_hash,
    }
    normalized_hash = sha256_hex(logical)
    ancestry = tuple(sorted({
        seed_manifest.source_id,
        *(item.source_id for item in ticker_events),
    }))
    return SourceManifestV1(
        source_id=deterministic_id("P1SRC-", logical),
        source_role=SourceRole.PRECISE_MEMBERSHIP_EVENTS,
        source_type="derived_identity_aware_resolved_snapshot_difference",
        source_url_or_repo=seed_manifest.source_url_or_repo,
        source_commit_or_revision=seed_manifest.source_commit_or_revision,
        retrieved_at=seed_manifest.retrieved_at,
        media_type="application/vnd.aq.pit-reconciled-membership-events+json",
        byte_length=len(canonical_bytes(logical)),
        sha256=normalized_hash,
        license_observation=seed_manifest.license_observation,
        coverage_start=min(item.effective_session for item in observations),
        coverage_end=max(item.effective_session for item in observations),
        ancestry=ancestry,
        adapter_version=RECONCILED_DERIVATION_VERSION,
    )


def derive_reconciled_membership_events(
    observations: tuple[SnapshotObservationV1, ...],
    resolved_observations: tuple[ResolvedObservation, ...],
    ticker_events: tuple[TickerIdentityEventV1, ...],
    event_manifest: SourceManifestV1,
    *,
    seed_manifest: SourceManifestV1,
    overlays: tuple[TickerEpisodeOverlayV1, ...],
) -> tuple[IndexMembershipEventV1, ...]:
    """Derive actual membership churn after applying identity transitions.

    The raw exact-difference function above remains unchanged and authoritative as
    source evidence.  This distinct path consumes a resolved view and transforms
    the prior roster through clear same-session identity events before diffing.
    """

    if (
        event_manifest.source_role is not SourceRole.PRECISE_MEMBERSHIP_EVENTS
        or event_manifest.adapter_version != RECONCILED_DERIVATION_VERSION
    ):
        raise ValueError("reconciled events require the reconciled derivation manifest")
    expected_manifest = build_reconciled_membership_event_manifest(
        seed_manifest,
        observations,
        resolved_observations,
        ticker_events,
        overlays,
    )
    if event_manifest != expected_manifest:
        raise ValueError("reconciled derivation manifest does not match the exact reconciliation context")
    raw_ordered = tuple(sorted(
        observations,
        key=lambda item: (item.effective_session, item.observation_id),
    ))
    validate_snapshot_observation_table(raw_ordered)
    resolved_by_id = {item.observation_id: item for item in resolved_observations}
    if len(resolved_by_id) != len(resolved_observations) or set(resolved_by_id) != {
        item.observation_id for item in raw_ordered
    }:
        raise ValueError("resolved observations must map exactly to raw observations")
    for raw in raw_ordered:
        resolved = resolved_by_id[raw.observation_id]
        if (
            resolved.index_id != raw.index_id
            or resolved.effective_session != raw.effective_session
            or resolved.source_id != raw.source_id
            or resolved.evidence_hash != raw.evidence_hash
        ):
            raise ValueError("resolved observation provenance does not match raw observation")

    for event in ticker_events:
        if (
            event.boundary_semantics is SessionBoundary.AMBIGUOUS
            or event.ambiguity_state is AmbiguityState.AMBIGUOUS
        ):
            raise ValueError("ambiguous identity event cannot drive reconciled derivation")
    events: list[IndexMembershipEventV1] = []
    for prior_raw, current_raw in zip(raw_ordered, raw_ordered[1:]):
        if prior_raw.index_id != current_raw.index_id:
            raise ValueError("cannot diff observations from different indexes")
        prior = resolved_by_id[prior_raw.observation_id]
        current = resolved_by_id[current_raw.observation_id]
        transformed = set(prior.tickers)
        identities = tuple(sorted(
            (
                item for item in ticker_events
                if prior.effective_session < item.effective_session <= current.effective_session
            ),
            key=lambda item: (item.effective_session, item.event_id),
        ))
        for session in sorted({item.effective_session for item in identities}):
            identity_symbols = [
                normalize_ticker(symbol)
                for item in identities
                if item.effective_session == session
                for symbol in (item.old_ticker, item.new_ticker)
            ]
            if len(identity_symbols) != len(set(identity_symbols)):
                raise ValueError("ambiguous same-session identity transitions")
        for identity in identities:
            old = normalize_ticker(identity.old_ticker)
            new = normalize_ticker(identity.new_ticker)
            if old not in transformed:
                continue
            if new in transformed:
                raise ValueError("identity transition overlaps an active successor")
            transformed.remove(old)
            transformed.add(new)

        current_set = set(current.tickers)
        removed = tuple(sorted(transformed - current_set))
        added = tuple(sorted(current_set - transformed))
        transition_hash = sha256_hex({
            "algorithm": RECONCILED_DERIVATION_VERSION,
            "event_manifest_hash": event_manifest.manifest_hash,
            "raw_prior_observation": prior_raw,
            "raw_current_observation": current_raw,
            "resolved_prior_observation": prior,
            "resolved_current_observation": current,
            "identity_events": identities,
            "removed": removed,
            "added": added,
        })
        transitions = (
            *((MembershipAction.REMOVE, ticker) for ticker in removed),
            *((MembershipAction.ADD, ticker) for ticker in added),
        )
        for action, ticker in transitions:
            identity = {
                "algorithm": RECONCILED_DERIVATION_VERSION,
                "action": action,
                "effective_session": current.effective_session,
                "index_id": current.index_id,
                "source_id": event_manifest.source_id,
                "ticker": ticker,
                "raw_prior_observation_id": prior_raw.observation_id,
                "raw_current_observation_id": current_raw.observation_id,
                "applied_overlay_ids": tuple(sorted({
                    *prior.applied_overlay_ids,
                    *current.applied_overlay_ids,
                })),
                "ticker_identity_event_ids": tuple(item.event_id for item in identities),
            }
            events.append(IndexMembershipEventV1(
                event_id=deterministic_id("P1MEMR-", identity),
                index_id=current.index_id,
                action=action,
                source_ticker=ticker,
                announcement_date=None,
                effective_date=current.effective_session,
                effective_session=current.effective_session,
                boundary_semantics=SessionBoundary.SOURCE_DEFINED,
                source_id=event_manifest.source_id,
                evidence_hash=transition_hash,
                reason=f"{RECONCILED_DERIVATION_VERSION} from immutable source observations",
            ))
    result = tuple(events)
    validate_membership_event_table(result)
    return result
