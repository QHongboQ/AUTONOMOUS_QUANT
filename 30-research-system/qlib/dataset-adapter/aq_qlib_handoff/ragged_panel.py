"""Thin frozen-observation handoff into Qlib's upstream CSV dump boundary."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re

import numpy as np


_SECURITY_ID = re.compile(r"^P2AUDITSEC-([0-9a-f]{64})$")
_FIELDS = ("open", "high", "low", "close", "volume")
_OBSERVED_PRIMARY = "OBSERVED_PRIMARY"
_OBSERVED_SECONDARY = "OBSERVED_SECONDARY"
_MASK_REASONS = (
    "KNOWN_PROVIDER_GAP",
    "KNOWN_TERMINAL_SESSION_PROVIDER_GAP",
    "PARTIAL_PROVIDER_COVERAGE",
    "NO_PROVIDER_ASSET",
    "IDENTITY_AMBIGUOUS",
    "TERMINAL_POLICY_UNRESOLVED",
    "UNRESOLVED_ERROR",
)


@dataclass(frozen=True, slots=True)
class RaggedPanelBuildV1:
    schema_version: str
    history_start: str
    history_end: str
    unique_security_identities: int
    instrument_episodes: int
    total_member_session_rows: int
    observed_safe_rows: int
    masked_rows: int
    quantiacs_selected_rows: int
    simfin_selected_rows: int
    rows_by_mask_reason: dict[str, int]
    instruments_file: str
    availability_sidecar: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_line(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def qlib_instrument_id(security_identity: str) -> str:
    """Derive a collision-resistant Qlib symbol only from security identity."""
    match = _SECURITY_ID.fullmatch(security_identity)
    if match is None:
        raise ValueError("unsupported security_identity")
    return "P2SEC" + match.group(1).upper()


def _load_simfin(path: Path) -> dict[tuple[str, str], tuple[float, ...]]:
    result: dict[tuple[str, str], tuple[float, ...]] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter=";"):
            key = (row.get("Ticker", "").strip().upper(), row.get("Date", "").strip())
            try:
                values = tuple(float(row[name]) for name in ("Open", "High", "Low", "Close", "Volume"))
            except (KeyError, TypeError, ValueError):
                continue
            if key[1] and all(math.isfinite(value) for value in values) and values[-1] >= 0:
                if key in result and result[key] != values:
                    raise ValueError(f"conflicting SimFin row: {key}")
                result[key] = values
    return result


def _masked_reason(episode: dict[str, object]) -> str:
    fixed = (
        ("no_provider_asset_rows", "NO_PROVIDER_ASSET"),
        ("identity_ambiguous_rows", "IDENTITY_AMBIGUOUS"),
        ("terminal_policy_unresolved_rows", "TERMINAL_POLICY_UNRESOLVED"),
        ("unresolved_error_rows", "UNRESOLVED_ERROR"),
    )
    for field, reason in fixed:
        if int(episode[field]):
            return reason
    if int(episode["partial_coverage_missing_rows"]):
        return "PARTIAL_PROVIDER_COVERAGE"
    if int(episode["known_terminal_gap_rows"]):
        return "KNOWN_TERMINAL_SESSION_PROVIDER_GAP"
    if int(episode["known_provider_gap_rows"]):
        return "KNOWN_PROVIDER_GAP"
    return "UNRESOLVED_ERROR"


def build_ragged_staging(
    inventory_path: Path,
    quantiacs_source: Path,
    simfin_path: Path,
    output_root: Path,
    *,
    expected_inventory_sha256: str,
    expected_quantiacs_manifest_sha256: str,
    expected_simfin_sha256: str,
    expected_identities: int = 730,
    expected_episodes: int = 745,
    expected_member_rows: int = 1_267_963,
    expected_primary_rows: int = 1_224_658,
    expected_secondary_rows: int = 130,
    market: str = "p2_pit",
) -> RaggedPanelBuildV1:
    """Materialize actual OHLCV or NaN for every accepted member-session."""
    if output_root.exists():
        raise FileExistsError(f"output already exists: {output_root}")
    if _sha256(inventory_path) != expected_inventory_sha256:
        raise ValueError("full-universe inventory hash mismatch")
    if _sha256(quantiacs_source / "source_manifest.json") != expected_quantiacs_manifest_sha256:
        raise ValueError("Quantiacs source manifest hash mismatch")
    if _sha256(simfin_path) != expected_simfin_sha256:
        raise ValueError("SimFin input hash mismatch")

    envelope = json.loads(inventory_path.read_text(encoding="utf-8"))
    episodes = envelope["episodes"]
    if (
        envelope["unique_security_identities"],
        envelope["instrument_episodes"],
        envelope["total_member_session_rows"],
        len(episodes),
    ) != (expected_identities, expected_episodes, expected_member_rows, expected_episodes):
        raise ValueError("full-universe inventory accounting mismatch")

    coordinates = json.loads((quantiacs_source / "coordinates.json").read_text(encoding="utf-8"))
    assets = json.loads((quantiacs_source / "provider_assets.json").read_text(encoding="utf-8"))
    values = np.load(quantiacs_source / "values.npy", mmap_mode="r")
    field_index = {name: index for index, name in enumerate(coordinates["field"])}
    source_fields = tuple(field_index[name] for name in ("open", "high", "low", "close", "vol"))
    dates = list(coordinates["time"])
    date_index = {day: index for index, day in enumerate(dates)}
    asset_index = {asset["id"]: index for index, asset in enumerate(assets)}
    simfin = _load_simfin(simfin_path)
    tickers_by_identity: dict[str, set[str]] = defaultdict(set)
    identities_by_ticker: dict[str, set[str]] = defaultdict(set)
    for episode in episodes:
        identity = str(episode["security_identity"])
        ticker = str(episode["ticker"]).upper()
        tickers_by_identity[identity].add(ticker)
        identities_by_ticker[ticker].add(identity)

    csv_rows: dict[str, list[tuple[object, ...]]] = defaultdict(list)
    ranges: list[tuple[str, str, str, str, str]] = []
    availability: list[dict[str, object]] = []
    identity_rows: dict[str, dict[str, str]] = {}
    counts: Counter[str] = Counter()
    per_year: dict[str, Counter[str]] = defaultdict(Counter)
    seen_member_rows: set[tuple[str, str]] = set()

    for episode in episodes:
        identity = str(episode["security_identity"])
        instrument = qlib_instrument_id(identity)
        episode_counts: Counter[str] = Counter()
        identity_rows[instrument] = {
            "instrument": instrument,
            "security_identity": str(episode["security_identity"]),
        }
        required = [
            day for day in dates
            if str(episode["scope_required_from"]) <= day <= str(episode["scope_required_to"])
        ]
        if len(required) != int(episode["required_sessions"]):
            raise ValueError(f"episode session count mismatch: {episode['episode_id']}")
        ranges.append((
            instrument,
            required[0],
            required[-1],
            str(episode["episode_id"]),
            str(episode["ticker"]),
        ))
        provider_asset = episode.get("provider_asset_identifier")
        provider_column = asset_index.get(str(provider_asset)) if provider_asset is not None else None
        for day in required:
            member_key = (instrument, day)
            if member_key in seen_member_rows:
                raise ValueError(f"overlapping episodes for security identity: {member_key}")
            seen_member_rows.add(member_key)
            row_values: tuple[float, ...] | None = None
            reason: str
            if provider_column is not None:
                vector = tuple(float(values[index, date_index[day], provider_column]) for index in source_fields)
                if all(math.isfinite(value) for value in vector) and vector[-1] >= 0:
                    row_values, reason = vector, _OBSERVED_PRIMARY
            if row_values is None and int(episode["observed_secondary_rows"]):
                secondary = [
                    simfin[(ticker, day)]
                    for ticker in sorted(tickers_by_identity[identity])
                    if identities_by_ticker[ticker] == {identity} and (ticker, day) in simfin
                ]
                if len(secondary) > 1:
                    raise ValueError(f"ambiguous SimFin identity/date: {episode['episode_id']} {day}")
                if secondary:
                    row_values, reason = secondary[0], _OBSERVED_SECONDARY
            if row_values is None:
                reason = _masked_reason(episode)
            if row_values is None:
                row_values = (math.nan,) * 5
            csv_rows[instrument].append((day, *row_values))
            counts[reason] += 1
            episode_counts[reason] += 1
            per_year[day[:4]][reason] += 1
            availability.append({
                "date": day,
                "episode_id": episode["episode_id"],
                "historical_ticker": episode["ticker"],
                "instrument": instrument,
                "reason": reason,
            })
        expected_episode_counts = {
            _OBSERVED_PRIMARY: int(episode["observed_primary_rows"]),
            _OBSERVED_SECONDARY: int(episode["observed_secondary_rows"]),
            "KNOWN_PROVIDER_GAP": int(episode["known_provider_gap_rows"]),
            "KNOWN_TERMINAL_SESSION_PROVIDER_GAP": int(episode["known_terminal_gap_rows"]),
            "PARTIAL_PROVIDER_COVERAGE": int(episode["partial_coverage_missing_rows"]),
            "NO_PROVIDER_ASSET": int(episode["no_provider_asset_rows"]),
            "IDENTITY_AMBIGUOUS": int(episode["identity_ambiguous_rows"]),
            "TERMINAL_POLICY_UNRESOLVED": int(episode["terminal_policy_unresolved_rows"]),
            "UNRESOLVED_ERROR": int(episode["unresolved_error_rows"]),
        }
        if any(episode_counts[key] != value for key, value in expected_episode_counts.items()):
            raise ValueError(f"episode source-selection accounting mismatch: {episode['episode_id']}")

    if len(seen_member_rows) != expected_member_rows or len(csv_rows) != expected_identities:
        raise ValueError("materialized member-session accounting mismatch")
    if counts[_OBSERVED_PRIMARY] != expected_primary_rows or counts[_OBSERVED_SECONDARY] != expected_secondary_rows:
        raise ValueError("frozen source-selection accounting mismatch")
    if sum(counts[reason] for reason in _MASK_REASONS) + counts[_OBSERVED_PRIMARY] + counts[_OBSERVED_SECONDARY] != expected_member_rows:
        raise ValueError("availability accounting mismatch")

    csv_dir = output_root / "staging" / "csv"
    reports_dir = output_root / "reports"
    instruments_dir = output_root / "staging" / "instruments"
    csv_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    instruments_dir.mkdir(parents=True)
    for instrument, rows in sorted(csv_rows.items()):
        rows.sort(key=lambda item: item[0])
        with (csv_dir / f"{instrument.lower()}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(("date", *_FIELDS))
            writer.writerows(rows)

    ranges.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    (instruments_dir / f"{market}.txt").write_text(
        "".join(f"{instrument}\t{start}\t{end}\n" for instrument, start, end, _, _ in ranges),
        encoding="utf-8", newline="",
    )
    (output_root / "staging" / "episode-map.jsonl").write_text(
        "".join(_json_line({
            "episode_id": episode_id,
            "historical_ticker": ticker,
            "instrument": instrument,
            "start": start,
            "end_inclusive": end,
        }) for instrument, start, end, episode_id, ticker in ranges),
        encoding="utf-8", newline="",
    )
    (output_root / "staging" / "instrument-identity.jsonl").write_text(
        "".join(_json_line(identity_rows[key]) for key in sorted(identity_rows)),
        encoding="utf-8", newline="",
    )
    availability.sort(key=lambda row: (row["date"], row["instrument"], row["episode_id"]))
    availability_path = output_root / "staging" / "availability.jsonl.gz"
    with availability_path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                text.writelines(_json_line(row) for row in availability)

    yearly = []
    for year in sorted(per_year):
        year_counts = per_year[year]
        observed = year_counts[_OBSERVED_PRIMARY] + year_counts[_OBSERVED_SECONDARY]
        member = sum(year_counts.values())
        yearly.append({
            "year": int(year),
            "member_rows": member,
            "observed_safe_rows": observed,
            "masked_rows": member - observed,
            "usable_percent": round(observed * 100 / member, 6),
        })
    (reports_dir / "yearly-availability.json").write_text(
        json.dumps(yearly, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n",
    )
    observed = counts[_OBSERVED_PRIMARY] + counts[_OBSERVED_SECONDARY]
    result = RaggedPanelBuildV1(
        schema_version="RaggedPanelBuildV1",
        history_start=str(envelope["frozen_scope_start"]),
        history_end=str(envelope["frozen_scope_end"]),
        unique_security_identities=expected_identities,
        instrument_episodes=expected_episodes,
        total_member_session_rows=expected_member_rows,
        observed_safe_rows=observed,
        masked_rows=expected_member_rows - observed,
        quantiacs_selected_rows=counts[_OBSERVED_PRIMARY],
        simfin_selected_rows=counts[_OBSERVED_SECONDARY],
        rows_by_mask_reason={reason: counts[reason] for reason in _MASK_REASONS},
        instruments_file=f"staging/instruments/{market}.txt",
        availability_sidecar="staging/availability.jsonl.gz",
    )
    (reports_dir / "build-report.json").write_text(
        json.dumps(asdict(result), sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    return result
