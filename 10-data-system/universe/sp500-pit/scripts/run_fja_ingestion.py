"""Materialize the pinned 2010-2024 FJA ingestion and diagnostic evidence."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from aq_pit.canonical import canonical_bytes, deterministic_id, sha256_hex
from aq_pit.compiler import compile_universe
from aq_pit.contracts import (
    AmbiguityState,
    CompilePolicyV1,
    FindingType,
    MembershipAction,
    SessionBoundary,
    SourceManifestV1,
    SourceRole,
    TickerIdentityEventV1,
)
from aq_pit.overlays import detect_future_ticker_backfill
from aq_pit.schema.pandera import validate_identity_event_table
from aq_pit.sources.fja_sp500 import (
    build_fja_manifest,
    build_membership_event_manifest,
    derive_membership_events,
    parse_fja_snapshots,
)


FJA_COMMIT = "a2430f2af0c79ddf0748e91de11bdeb1616ab5a7"
PITINDEX_COMMIT = "2df030e5c9be7c83cf4b28c3d8597d74d274757e"
PITINDEX_REPOSITORY = "arielNacamulli/pitindex"
WIKIPEDIA_REVISION = "1265285344"
WIKIPEDIA_TIMESTAMP = "2024-12-26T04:36:28Z"
FJA_SOURCE_FILE = "S&P 500 Historical Components & Changes (Updated).csv"
WINDOW_START = "2010-01-01"
WINDOW_END = "2024-12-31"
FIRST_TRADING_SESSION = "2010-01-04"
SELECTED_DATES = (
    "2010-06-30", "2012-06-29", "2014-06-30", "2016-06-30",
    "2018-06-29", "2020-06-30", "2022-06-30", "2024-06-28",
)

# Frozen Project Brain regression boundaries used only as generic detector inputs.
# They never enter compile_universe and do not authorize a correction.
IDENTITY_AUDIT_PROBES = (
    ("FB", "META", "2022-06-09"),
    ("CDAY", "DAY", "2024-02-01"),
    ("RE", "EG", "2023-07-10"),
    ("WLTW", "WTW", "2022-01-10"),
    ("KORS", "CPRI", "2019-01-02"),
    ("Q", "IQV", "2017-11-15"),
    ("DLPH", "APTV", "2017-12-05"),
)
MEMBERSHIP_SUCCESSION_AUDIT_PROBES = (
    ("DISCK", "WBD", "2022-04-11"),
)


@dataclass(frozen=True, slots=True)
class DiagnosticRenameCandidate:
    old_ticker: str
    new_ticker: str
    boundary: str
    source_ids: tuple[str, ...]
    frozen_probe: bool = False


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_hash(files: tuple[Path, ...], root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_length = 0
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        raw = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
        byte_length += len(raw)
    return digest.hexdigest(), byte_length


def _write_canonical(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    temporary.replace(path)


def _write_jsonl(path: Path, values: tuple[object, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        for value in values:
            handle.write(canonical_bytes(value) + b"\n")
    temporary.replace(path)


def _parse_terminal_symbols(raw: bytes) -> tuple[str, ...]:
    text = raw.decode("utf-8")
    start = text.index('id="constituents"')
    end = text.index("\n|}", start)
    table = text[start:end]
    symbols = re.findall(
        r"\{\{(?:(?:Nyse|Nasdaq)Symbol|BZX link)\|([^}|]+)", table,
    )
    roster = tuple(sorted(symbol.strip().upper().replace("-", ".") for symbol in symbols))
    return roster


def _terminal_roster(raw: bytes) -> tuple[str, ...]:
    roster = _parse_terminal_symbols(raw)
    if len(roster) != len(set(roster)) or len(roster) < 500:
        raise ValueError("terminal Wikipedia roster did not parse as a unique S&P 500 set")
    return roster


def _terminal_manifest(raw: bytes, retrieved_at: str) -> SourceManifestV1:
    digest = hashlib.sha256(raw).hexdigest()
    return SourceManifestV1(
        source_id=deterministic_id("P1SRC-", {
            "repo": "Wikipedia/List_of_S%26P_500_companies",
            "revision": WIKIPEDIA_REVISION,
            "sha256": digest,
        }),
        source_role=SourceRole.DIAGNOSTIC_REFERENCE,
        source_type="pinned_historical_wikipedia_revision_wikitext",
        source_url_or_repo="https://en.wikipedia.org/wiki/Special:PermanentLink/1265285344",
        source_commit_or_revision=WIKIPEDIA_REVISION,
        retrieved_at=retrieved_at,
        media_type="text/x-wiki",
        byte_length=len(raw),
        sha256=digest,
        license_observation="CC BY-SA 4.0 / GFDL page content terms observed",
        coverage_start="2024-12-26",
        coverage_end="2024-12-31",
        ancestry=(),
        adapter_version="wikipedia-constituents-table-parser-v1",
    )


def _pitindex_manifest(repo: Path, retrieved_at: str, fja_source_id: str) -> SourceManifestV1:
    files = (
        repo / "pitindex" / "data" / "build_metadata.json",
        repo / "pitindex" / "data" / "sp500_seed.csv",
        repo / "pitindex" / "data" / "sp500_changes.csv",
        repo / "data" / "ticker_renames.csv",
    )
    digest, byte_length = _tree_hash(files, repo)
    metadata = json.loads(files[0].read_text(encoding="utf-8"))
    sp500_metadata = metadata["indices"]["sp500"]
    return SourceManifestV1(
        source_id=deterministic_id("P1SRC-", {
            "files_sha256": digest,
            "repo": PITINDEX_REPOSITORY,
            "revision": PITINDEX_COMMIT,
        }),
        source_role=SourceRole.DIAGNOSTIC_REFERENCE,
        source_type="pinned_repository_diagnostic_bundle",
        source_url_or_repo=f"https://github.com/{PITINDEX_REPOSITORY}",
        source_commit_or_revision=PITINDEX_COMMIT,
        retrieved_at=retrieved_at,
        media_type="text/csv",
        byte_length=byte_length,
        sha256=digest,
        license_observation="MIT (repository LICENSE at pinned commit)",
        coverage_start=sp500_metadata["start_date"],
        coverage_end=sp500_metadata["end_date"],
        ancestry=(fja_source_id,),
        adapter_version="pitindex-diagnostic-replay-v1",
    )


def _pitindex_roster(repo: Path, as_of: str) -> tuple[str, ...]:
    seed_path = repo / "pitindex" / "data" / "sp500_seed.csv"
    changes_path = repo / "pitindex" / "data" / "sp500_changes.csv"
    with seed_path.open(encoding="utf-8-sig", newline="") as handle:
        roster = {
            row["ticker"].strip().upper()
            for row in csv.DictReader(handle)
            if row["effective_date"] <= as_of
        }
    changes: list[tuple[str, int, str]] = []
    with changes_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["date"] <= as_of:
                action = row["action"].strip().lower()
                changes.append((row["date"], 0 if action == "removed" else 1, row["ticker"].strip().upper()))
    for _, priority, ticker in sorted(changes):
        if priority == 0:
            roster.discard(ticker)
        else:
            roster.add(ticker)
    return tuple(sorted(roster))


def _observation_on_or_before(observations, session: str):
    matches = [item for item in observations if item.effective_session <= session]
    if not matches:
        raise ValueError(f"no FJA observation on or before {session}")
    return matches[-1]


def _load_pitindex_rename_candidates(
    path: Path,
    source_id: str,
) -> tuple[DiagnosticRenameCandidate, ...]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["date", "old_ticker", "new_ticker", "reason"]:
            raise ValueError("unexpected pitindex ticker_renames.csv schema")
        candidates = []
        for row in reader:
            boundary = row["date"].strip()
            date.fromisoformat(boundary)
            if not WINDOW_START <= boundary <= WINDOW_END:
                continue
            old_ticker = row["old_ticker"].strip().upper()
            new_ticker = row["new_ticker"].strip().upper()
            candidates.append(DiagnosticRenameCandidate(
                old_ticker, new_ticker, boundary, (source_id,), False,
            ))
    return tuple(candidates)


def _merge_diagnostic_candidates(
    pitindex_candidates: tuple[DiagnosticRenameCandidate, ...],
) -> tuple[DiagnosticRenameCandidate, ...]:
    merged: dict[tuple[str, str, str], dict[str, object]] = {}
    for candidate in pitindex_candidates:
        key = (candidate.old_ticker, candidate.new_ticker, candidate.boundary)
        merged[key] = {
            "source_ids": set(candidate.source_ids),
            "frozen_probe": False,
        }
    for old_ticker, new_ticker, boundary in IDENTITY_AUDIT_PROBES:
        key = (old_ticker, new_ticker, boundary)
        item = merged.setdefault(key, {"source_ids": set(), "frozen_probe": False})
        item["source_ids"].add("project-brain-frozen-audit-probes")
        item["frozen_probe"] = True
    return tuple(
        DiagnosticRenameCandidate(
            old_ticker=key[0],
            new_ticker=key[1],
            boundary=key[2],
            source_ids=tuple(sorted(item["source_ids"])),
            frozen_probe=bool(item["frozen_probe"]),
        )
        for key, item in sorted(merged.items())
    )


def _candidate_events(
    candidates: tuple[DiagnosticRenameCandidate, ...],
) -> tuple[TickerIdentityEventV1, ...]:
    result = []
    for candidate in candidates:
        logical = {
            "old": candidate.old_ticker,
            "new": candidate.new_ticker,
            "boundary": candidate.boundary,
            "sources": candidate.source_ids,
            "role": "diagnostic-only-rename-candidate",
        }
        result.append(TickerIdentityEventV1(
            event_id=deterministic_id("P1PROBE-", logical),
            old_ticker=candidate.old_ticker,
            new_ticker=candidate.new_ticker,
            announcement_date=None,
            effective_date=candidate.boundary,
            effective_session=candidate.boundary,
            boundary_semantics=SessionBoundary.EFFECTIVE_SESSION,
            source_id="diagnostic-only-rename-scan",
            evidence_hash=sha256_hex(logical),
            identity_anchor=None,
            ambiguity_state=AmbiguityState.CLEAR,
        ))
    events = tuple(result)
    validate_identity_event_table(events)
    return events


def _issue(kind: str, tickers: tuple[str, ...], first: str, last: str, source_ids: tuple[str, ...], leads: tuple[str, ...], *, blocking: bool = True) -> dict:
    payload = {
        "blocking": "YES" if blocking else "NO",
        "candidate_evidence_leads": tuple(sorted(leads)),
        "finding_type": kind,
        "first_affected_date": first,
        "last_affected_date": last,
        "source_ids": tuple(sorted(source_ids)),
        "tickers": tuple(sorted(tickers)),
    }
    return {"finding_id": deterministic_id("P1UNRES-", payload), **payload}


def _diagnostic_rename_report(observations, candidates, fja_source_id: str):
    probe_events = _candidate_events(candidates)
    detector = detect_future_ticker_backfill(observations, probe_events)
    observation_dates = {item.observation_id: item.effective_session for item in observations}
    event_map = {item.event_id: item for item in probe_events}
    candidate_map = {
        (item.old_ticker, item.new_ticker, item.boundary): item
        for item in candidates
    }
    grouped: dict[tuple[str, str], list[str]] = {}
    for finding in detector:
        event_id = next(item for item in finding.affected_ids if item in event_map)
        observation_id = next(item for item in finding.affected_ids if item in observation_dates)
        grouped.setdefault((event_id, finding.finding_type.value), []).append(observation_dates[observation_id])
    ledger = []
    for (event_id, runtime_kind), dates in sorted(grouped.items()):
        event = event_map[event_id]
        candidate = candidate_map[(event.old_ticker, event.new_ticker, event.effective_session)]
        kind = "FUTURE_TICKER_BACKFILL" if runtime_kind == FindingType.FUTURE_TICKER_BEFORE_RENAME.value else "STALE_PREDECESSOR_TICKER"
        ledger.append(_issue(
            kind, (event.old_ticker, event.new_ticker), min(dates), max(dates),
            (fja_source_id, *candidate.source_ids),
            ("official S&P constituent-change notice", "issuer/SEC identity evidence", "pinned pitindex row as non-independent locator"),
        ))
    behavior = {}
    for candidate, event in zip(candidates, probe_events):
        if not candidate.frozen_probe:
            continue
        old_dates = [item.effective_session for item in observations if event.old_ticker in item.tickers]
        new_dates = [item.effective_session for item in observations if event.new_ticker in item.tickers]
        key = f"{event.old_ticker}_{event.new_ticker}"
        behavior[key] = {
            "boundary_probe": event.effective_session,
            "old_first": min(old_dates) if old_dates else None,
            "old_last": max(old_dates) if old_dates else None,
            "new_first": min(new_dates) if new_dates else None,
            "new_last": max(new_dates) if new_dates else None,
            "correction_applied": False,
        }
        ledger.append(_issue(
            "TICKER_RENAME_EVIDENCE_REQUIRED", (event.old_ticker, event.new_ticker),
            min((*old_dates, *new_dates)), max((*old_dates, *new_dates)),
            (fja_source_id, *candidate.source_ids),
            ("official effective-date notice", "issuer/SEC identity evidence"),
        ))
    return detector, behavior, ledger


def _boundary_disagreements(
    pitindex_candidates: tuple[DiagnosticRenameCandidate, ...],
) -> tuple[dict, ...]:
    frozen = {(old, new): boundary for old, new, boundary in IDENTITY_AUDIT_PROBES}
    return tuple(
        {
            "old_ticker": candidate.old_ticker,
            "new_ticker": candidate.new_ticker,
            "frozen_boundary": frozen[(candidate.old_ticker, candidate.new_ticker)],
            "pitindex_boundary": candidate.boundary,
            "authority_change": "NONE",
        }
        for candidate in pitindex_candidates
        if (candidate.old_ticker, candidate.new_ticker) in frozen
        and candidate.boundary != frozen[(candidate.old_ticker, candidate.new_ticker)]
    )


def _deduplicate_issues(issues: list[dict]) -> list[dict]:
    grouped: dict[tuple[object, ...], dict[str, set[str]]] = {}
    for item in issues:
        key = (
            item["finding_type"], tuple(item["tickers"]),
            item["first_affected_date"], item["last_affected_date"], item["blocking"],
        )
        merged = grouped.setdefault(key, {"source_ids": set(), "leads": set()})
        merged["source_ids"].update(item["source_ids"])
        merged["leads"].update(item["candidate_evidence_leads"])
    result = [
        _issue(
            key[0], key[1], key[2], key[3], tuple(sorted(value["source_ids"])),
            tuple(sorted(value["leads"])), blocking=key[4] == "YES",
        )
        for key, value in grouped.items()
    ]
    return sorted(result, key=lambda item: item["finding_id"])


def run(args: argparse.Namespace) -> dict:
    data_root = Path(args.data_root)
    fja_path = data_root / "raw" / "fja_sp500" / "repo" / FJA_SOURCE_FILE
    terminal_path = data_root / "raw" / "terminal_reference" / "wikipedia-sp500-oldid-1265285344.wikitext"
    pitindex_repo = data_root / "raw" / "pitindex_reference" / "repo"
    raw = fja_path.read_bytes()
    terminal_raw = terminal_path.read_bytes()
    seed_manifest = build_fja_manifest(
        raw, commit=FJA_COMMIT, source_file=FJA_SOURCE_FILE, retrieved_at=args.retrieved_at,
    )
    observations = parse_fja_snapshots(
        raw, seed_manifest, start_date=WINDOW_START, end_date=WINDOW_END,
        start_session=FIRST_TRADING_SESSION,
    )
    event_manifest = build_membership_event_manifest(seed_manifest, observations)
    events = derive_membership_events(observations, event_manifest)
    terminal_manifest = _terminal_manifest(terminal_raw, args.retrieved_at)
    pitindex_manifest = _pitindex_manifest(pitindex_repo, args.retrieved_at, seed_manifest.source_id)
    pitindex_candidates = _load_pitindex_rename_candidates(
        pitindex_repo / "data" / "ticker_renames.csv", pitindex_manifest.source_id,
    )
    diagnostic_candidates = _merge_diagnostic_candidates(pitindex_candidates)
    boundary_disagreements = _boundary_disagreements(pitindex_candidates)
    manifests = (seed_manifest, event_manifest, terminal_manifest, pitindex_manifest)
    compile_manifests = (seed_manifest, event_manifest)
    start_session = observations[0].effective_session
    policy = CompilePolicyV1(
        "SP500", start_session, "2025-01-01",
        "FJA-source-session-calendar-v1", "p1-real-source-ingestion-v1",
    )
    compile_args = {
        "policy": policy,
        "manifests": compile_manifests,
        "observations": observations,
        "membership_events": events,
    }
    first_compile = compile_universe(**compile_args)
    second_compile = compile_universe(**compile_args)
    if first_compile != second_compile:
        raise RuntimeError("real-data compile was not deterministic")

    terminal_roster = _terminal_roster(terminal_raw)
    actual_terminal = observations[-1].tickers
    terminal_only_actual = tuple(sorted(set(actual_terminal) - set(terminal_roster)))
    terminal_only_expected = tuple(sorted(set(terminal_roster) - set(actual_terminal)))
    detector, probe_behavior, ledger = _diagnostic_rename_report(
        observations, diagnostic_candidates, seed_manifest.source_id,
    )

    if terminal_only_actual or terminal_only_expected:
        ledger.append(_issue(
            "TERMINAL_SET_DIFFERENCE",
            tuple(sorted((*terminal_only_actual, *terminal_only_expected))),
            observations[-1].effective_session, "2024-12-31",
            (seed_manifest.source_id, terminal_manifest.source_id),
            ("pinned Wikipedia revision 1265285344", "official late-December 2024 roster"),
        ))

    compiler_types = {}
    for finding in first_compile.findings:
        compiler_types[finding.finding_type.value] = compiler_types.get(finding.finding_type.value, 0) + 1
        ledger.append(_issue(
            "MEMBERSHIP_EVENT_CONFLICT" if finding.finding_type in {FindingType.ADD_PRESENT, FindingType.REMOVE_ABSENT} else "OTHER",
            (), start_session, observations[-1].effective_session,
            (seed_manifest.source_id, event_manifest.source_id), (finding.message,),
        ))

    by_ticker: dict[str, list] = {}
    for event in events:
        by_ticker.setdefault(event.source_ticker, []).append(event)
    for ticker, ticker_events in sorted(by_ticker.items()):
        ordered = sorted(ticker_events, key=lambda item: (item.effective_session, item.event_id))
        for left, right in zip(ordered, ordered[1:]):
            if left.action is MembershipAction.REMOVE and right.action is MembershipAction.ADD:
                ledger.append(_issue(
                    "TICKER_REUSE_REVIEW_REQUIRED", (ticker,), left.effective_session, right.effective_session,
                    (event_manifest.source_id,),
                    ("official membership notices", "permanent security identity evidence"),
                ))

    year_findings = []
    for year in range(2010, 2024):
        prior = [item for item in observations if item.effective_session.startswith(f"{year}-")][-1]
        following = [item for item in observations if item.effective_session.startswith(f"{year + 1}-")][0]
        boundary_events = [item for item in events if item.effective_session == following.effective_session]
        rebuilt = set(prior.tickers)
        for event in boundary_events:
            if event.action is MembershipAction.REMOVE:
                rebuilt.discard(event.source_ticker)
            else:
                rebuilt.add(event.source_ticker)
        if rebuilt != set(following.tickers):
            year_findings.append((year, year + 1))
            ledger.append(_issue(
                "SOURCE_GAP", tuple(sorted(rebuilt ^ set(following.tickers))),
                prior.effective_session, following.effective_session,
                (seed_manifest.source_id, event_manifest.source_id),
                ("inspect exact FJA boundary snapshots",),
            ))

    # Membership-succession probes are data, not symbol branches, and never imply identity.
    for predecessor, successor, boundary in MEMBERSHIP_SUCCESSION_AUDIT_PROBES:
        predecessor_dates = [
            item.effective_session for item in observations
            if predecessor in item.tickers
        ]
        successor_dates = [
            item.effective_session for item in observations
            if successor in item.tickers
        ]
        probe_behavior[f"{predecessor}_{successor}"] = {
            "boundary_probe": boundary,
            "classification": "membership REMOVE/ADD only; corporate identity unresolved",
            "predecessor_first": min(predecessor_dates) if predecessor_dates else None,
            "predecessor_last": max(predecessor_dates) if predecessor_dates else None,
            "successor_first": min(successor_dates) if successor_dates else None,
            "successor_last": max(successor_dates) if successor_dates else None,
            "correction_applied": False,
        }

    comparisons = []
    for session in SELECTED_DATES:
        fja_roster = set(_observation_on_or_before(observations, session).tickers)
        pitindex_roster = set(_pitindex_roster(pitindex_repo, session))
        comparisons.append({
            "date": session,
            "fja_count": len(fja_roster),
            "pitindex_count": len(pitindex_roster),
            "intersection_count": len(fja_roster & pitindex_roster),
            "fja_only": tuple(sorted(fja_roster - pitindex_roster)),
            "pitindex_only": tuple(sorted(pitindex_roster - fja_roster)),
            "independent_confirmation": False,
        })

    ledger = _deduplicate_issues(ledger)
    normalized_input_hash = sha256_hex({
        "manifests": compile_manifests,
        "observations": observations,
        "membership_events": events,
    })
    add_count = sum(item.action is MembershipAction.ADD for item in events)
    remove_count = sum(item.action is MembershipAction.REMOVE for item in events)
    future_count = sum(item.finding_type is FindingType.FUTURE_TICKER_BEFORE_RENAME for item in detector)
    stale_count = sum(item.finding_type is FindingType.STALE_OLD_TICKER_AFTER_RENAME for item in detector)
    future_range_count = sum(item["finding_type"] == "FUTURE_TICKER_BACKFILL" for item in ledger)
    stale_range_count = sum(item["finding_type"] == "STALE_PREDECESSOR_TICKER" for item in ledger)
    summary = {
        "schema_version": "P1PitSourceIngestionEvidenceV1",
        "fja": {
            "commit": FJA_COMMIT,
            "source_file": FJA_SOURCE_FILE,
            "source_hash": seed_manifest.sha256,
            "source_size": seed_manifest.byte_length,
        },
        "coverage": {"requested_start": WINDOW_START, "requested_end": WINDOW_END},
        "compile": {
            "add_present_count": compiler_types.get(FindingType.ADD_PRESENT.value, 0),
            "compilation_hash": first_compile.output_hash,
            "compile_twice_identical": True,
            "duplicate_count": compiler_types.get(FindingType.DUPLICATE_EVENT.value, 0),
            "normalized_input_hash": normalized_input_hash,
            "overlap_count": compiler_types.get(FindingType.OVERLAPPING_TICKER_EPISODES.value, 0),
            "remove_absent_count": compiler_types.get(FindingType.REMOVE_ABSENT.value, 0),
        },
        "counts": {
            "derived_add": add_count,
            "derived_remove": remove_count,
            "diagnostic_rename_candidate_count": len(pitindex_candidates),
            "diagnostic_rename_candidate_count_with_frozen_probes": len(diagnostic_candidates),
            "future_ticker_backfill_occurrences": future_count,
            "future_ticker_backfill_ranges": future_range_count,
            "snapshot_count": len(observations),
            "stale_ticker_occurrences": stale_count,
            "stale_ticker_ranges": stale_range_count,
            "unresolved_ledger_records": len(ledger),
            "year_continuity_findings": len(year_findings),
        },
        "diagnostic_boundary_disagreements": boundary_disagreements,
        "manifests": manifests,
        "probe_behavior": probe_behavior,
        "rosters": {
            "start_count": len(observations[0].tickers),
            "start_session": start_session,
            "terminal_count": len(actual_terminal),
            "terminal_reference_count": len(terminal_roster),
            "terminal_session": observations[-1].effective_session,
            "terminal_only_fja": terminal_only_actual,
            "terminal_only_reference": terminal_only_expected,
        },
        "safety": {
            "market_data_collected": False,
            "silent_corrections": 0,
            "symbol_specific_runtime_conditions": 0,
        },
        "terminal_reference": {
            "revision": WIKIPEDIA_REVISION,
            "revision_timestamp": WIKIPEDIA_TIMESTAMP,
            "sha256": terminal_manifest.sha256,
        },
    }
    _write_canonical(data_root / "normalized" / "source_manifests" / "source_manifests.json", manifests)
    _write_jsonl(data_root / "normalized" / "observations" / "fja_observations_2010_2024.jsonl", observations)
    _write_jsonl(data_root / "normalized" / "membership_events" / "fja_membership_events_2010_2024.jsonl", events)
    _write_canonical(data_root / "audit" / "unresolved_findings" / "unresolved_findings.json", ledger)
    _write_canonical(data_root / "audit" / "comparisons" / "fja_vs_pitindex.json", comparisons)
    _write_canonical(data_root / "audit" / "compilation_summary.json", summary)
    print(json.dumps({
        "summary": summary,
        "comparison_count": len(comparisons),
        "output_files": {
            "observations_sha256": _file_hash(data_root / "normalized" / "observations" / "fja_observations_2010_2024.jsonl"),
            "events_sha256": _file_hash(data_root / "normalized" / "membership_events" / "fja_membership_events_2010_2024.jsonl"),
            "ledger_sha256": _file_hash(data_root / "audit" / "unresolved_findings" / "unresolved_findings.json"),
            "comparisons_sha256": _file_hash(data_root / "audit" / "comparisons" / "fja_vs_pitindex.json"),
        },
    }, default=lambda value: value.value if hasattr(value, "value") else asdict(value), indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--retrieved-at", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
