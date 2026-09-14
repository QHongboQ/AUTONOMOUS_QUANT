"""Materialize the pinned RD-Agent factor HDF contract from frozen P2 inputs."""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import numpy as np
import pandas as pd


FIELDS = ("$open", "$close", "$high", "$low", "$volume")
OUTPUT_FIELDS = (*FIELDS, "$factor")
OBSERVED_PRIMARY = "OBSERVED_PRIMARY"
OBSERVED_SECONDARY = "OBSERVED_SECONDARY"
MASKED_REASONS = {
    "KNOWN_PROVIDER_GAP",
    "KNOWN_TERMINAL_SESSION_PROVIDER_GAP",
    "PARTIAL_PROVIDER_COVERAGE",
    "NO_PROVIDER_ASSET",
    "IDENTITY_AMBIGUOUS",
    "TERMINAL_POLICY_UNRESOLVED",
    "UNRESOLVED_ERROR",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def provider_invariant(root: Path, market: str) -> dict[str, object]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    tree = hashlib.sha256()
    total_bytes = 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        file_hash = sha256(path)
        total_bytes += size
        tree.update(f"{relative}\0{size}\0{file_hash}\n".encode())
    calendar = root / "calendars" / "day.txt"
    instruments = root / "instruments" / f"{market}.txt"
    if not calendar.is_file() or not instruments.is_file():
        raise FileNotFoundError("P2 provider calendar or market instruments file missing")
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "tree_manifest_sha256": tree.hexdigest(),
        "calendar_sha256": sha256(calendar),
        "market_instruments_sha256": sha256(instruments),
    }


def load_episode_authority(
    inventory_path: Path,
    episode_map_path: Path,
    expected_inventory_sha256: str,
) -> dict[str, dict[str, object]]:
    if sha256(inventory_path) != expected_inventory_sha256:
        raise ValueError("full-universe inventory hash mismatch")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if (
        inventory["unique_security_identities"] != 730
        or inventory["instrument_episodes"] != 745
        or inventory["total_member_session_rows"] != 1_267_963
        or len(inventory["episodes"]) != 745
    ):
        raise ValueError("full-universe inventory accounting mismatch")
    episodes = {str(item["episode_id"]): item for item in inventory["episodes"]}
    if len(episodes) != 745:
        raise ValueError("duplicate episode authority")

    mapped: dict[str, dict[str, object]] = {}
    with episode_map_path.open(encoding="utf-8") as stream:
        for line in stream:
            item = json.loads(line)
            episode_id = str(item["episode_id"])
            if episode_id in mapped or episode_id not in episodes:
                raise ValueError("duplicate or unknown episode map entry")
            episode = episodes[episode_id]
            if (
                item["start"] != episode["scope_required_from"]
                or item["end_inclusive"] != episode["scope_required_to"]
                or item["historical_ticker"] != episode["ticker"]
            ):
                raise ValueError(f"episode map mismatch: {episode_id}")
            mapped[episode_id] = {**episode, "instrument": str(item["instrument"]).upper()}
    if mapped.keys() != episodes.keys():
        raise ValueError("episode map is incomplete")
    return mapped


def load_quantiacs_source(
    source: Path,
    expected_manifest_sha256: str,
) -> tuple[dict[str, int], dict[str, int], np.ndarray, dict[str, object]]:
    manifest_path = source / "source_manifest.json"
    if sha256(manifest_path) != expected_manifest_sha256:
        raise ValueError("Quantiacs source manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, evidence in manifest["artifacts"].items():
        artifact = source / name
        if not artifact.is_file() or sha256(artifact) != evidence["sha256"]:
            raise ValueError(f"Quantiacs frozen artifact mismatch: {name}")
    coordinates = json.loads((source / "coordinates.json").read_text(encoding="utf-8"))
    assets = json.loads((source / "provider_assets.json").read_text(encoding="utf-8"))
    asset_ids = [str(item["id"]) for item in assets]
    if coordinates["asset"] != asset_ids or "split_cumprod" not in coordinates["field"]:
        raise ValueError("Quantiacs coordinate/asset identity mismatch")
    values = np.load(source / "values.npy", mmap_mode="r")
    if values.shape != (len(coordinates["field"]), len(coordinates["time"]), len(asset_ids)):
        raise ValueError("Quantiacs values shape mismatch")
    return (
        {str(day): index for index, day in enumerate(coordinates["time"])},
        {asset: index for index, asset in enumerate(asset_ids)},
        values,
        manifest,
    )


def load_qlib_ohlcv(provider: Path, market: str, start: str, end: str) -> pd.DataFrame:
    import qlib
    from qlib.data import D

    if qlib.__version__ != "0.9.8.dev26":
        raise ValueError("Qlib runtime version mismatch")
    qlib.init(
        provider_uri=str(provider),
        region="us",
        expression_cache=None,
        dataset_cache=None,
    )
    instruments = D.instruments(market=market)
    frame = D.features(
        instruments,
        list(FIELDS),
        start_time=start,
        end_time=end,
        freq="day",
        disk_cache=False,
    )
    if list(frame.columns) != list(FIELDS) or list(frame.index.names) != ["instrument", "datetime"]:
        raise ValueError("unexpected Qlib OHLCV contract")
    frame = frame.swaplevel().sort_index()
    frame.index = frame.index.set_names(["datetime", "instrument"])
    if frame.index.has_duplicates:
        raise ValueError("duplicate datetime/instrument rows from Qlib")
    return frame


def attach_frozen_factors(
    frame: pd.DataFrame,
    availability_path: Path,
    episodes: dict[str, dict[str, object]],
    date_index: dict[str, int],
    asset_index: dict[str, int],
    source_values: np.ndarray,
    split_field_index: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    if list(frame.index.names) != ["datetime", "instrument"] or list(frame.columns) != list(FIELDS):
        raise ValueError("input frame is not the native canonical contract")
    if frame.index.has_duplicates:
        raise ValueError("duplicate datetime/instrument rows")

    factor = np.full(len(frame), np.nan, dtype=np.float64)
    ohlcv = frame.to_numpy(copy=False)
    frame_dates = frame.index.get_level_values("datetime")
    frame_instruments = frame.index.get_level_values("instrument")
    counts: Counter[str] = Counter()
    episode_counts: dict[str, Counter[str]] = {key: Counter() for key in episodes}
    first_non_one: dict[str, object] | None = None
    processed = 0

    with gzip.open(availability_path, "rt", encoding="utf-8") as stream:
        for position, line in enumerate(stream):
            processed = position + 1
            if position >= len(frame):
                raise ValueError("availability has more rows than Qlib")
            row = json.loads(line)
            episode_id = str(row["episode_id"])
            episode = episodes.get(episode_id)
            if episode is None:
                raise ValueError("availability references unknown episode")
            day = str(row["date"])
            instrument = str(row["instrument"]).upper()
            if (
                instrument != episode["instrument"]
                or pd.Timestamp(day) != frame_dates[position]
                or instrument != str(frame_instruments[position]).upper()
            ):
                raise ValueError("availability/Qlib/episode identity ordering mismatch")
            reason = str(row["reason"])
            counts[reason] += 1
            episode_counts[episode_id][reason] += 1
            values = ohlcv[position]
            complete = bool(np.isfinite(values).all())
            all_missing = bool(pd.isna(values).all())
            if reason in {OBSERVED_PRIMARY, OBSERVED_SECONDARY}:
                if not complete:
                    raise ValueError("selected observation is not complete in Qlib")
            elif reason in MASKED_REASONS:
                if not all_missing:
                    raise ValueError("masked observation contains Qlib values")
            else:
                raise ValueError(f"unexpected provider-selection state: {reason}")

            if reason == OBSERVED_PRIMARY:
                provider_asset = episode.get("provider_asset_identifier")
                if provider_asset not in asset_index or day not in date_index:
                    raise ValueError("proven Quantiacs row lacks exact frozen identity join")
                authoritative = float(
                    source_values[
                        split_field_index,
                        date_index[day],
                        asset_index[str(provider_asset)],
                    ]
                )
                if not math.isfinite(authoritative) or authoritative <= 0:
                    raise ValueError("invalid authoritative split_cumprod")
                factor[position] = authoritative
                if first_non_one is None and not math.isclose(authoritative, 1.0, rel_tol=0, abs_tol=1e-12):
                    first_non_one = {
                        "episode_id": episode_id,
                        "instrument": instrument,
                        "provider_asset_identifier": provider_asset,
                        "date": day,
                        "adjusted_close": float(values[1]),
                        "split_cumprod": authoritative,
                        "restored_close": float(values[1]) / authoritative,
                    }

    if processed != len(frame):
        raise ValueError("availability has fewer rows than Qlib")
    for episode_id, episode in episodes.items():
        actual = episode_counts[episode_id]
        expected = {
            OBSERVED_PRIMARY: int(episode["observed_primary_rows"]),
            OBSERVED_SECONDARY: int(episode["observed_secondary_rows"]),
            "KNOWN_PROVIDER_GAP": int(episode["known_provider_gap_rows"]),
            "KNOWN_TERMINAL_SESSION_PROVIDER_GAP": int(episode["known_terminal_gap_rows"]),
            "PARTIAL_PROVIDER_COVERAGE": int(episode["partial_coverage_missing_rows"]),
            "NO_PROVIDER_ASSET": int(episode["no_provider_asset_rows"]),
            "IDENTITY_AMBIGUOUS": int(episode["identity_ambiguous_rows"]),
            "TERMINAL_POLICY_UNRESOLVED": int(episode["terminal_policy_unresolved_rows"]),
            "UNRESOLVED_ERROR": int(episode["unresolved_error_rows"]),
        }
        if any(actual[key] != value for key, value in expected.items()):
            raise ValueError(f"episode provider-selection accounting mismatch: {episode_id}")

    result = frame.copy()
    result["$factor"] = factor
    finite = factor[np.isfinite(factor)]
    report = {
        "total_daily_pv_rows": len(result),
        "quantiacs_backed_rows": counts[OBSERVED_PRIMARY],
        "simfin_only_rows": counts[OBSERVED_SECONDARY],
        "factor_non_null_rows": int(len(finite)),
        "factor_nan_rows": int(np.isnan(factor).sum()),
        "factor_unique_count": int(len(np.unique(finite))),
        "factor_nonconstant_count": int((np.abs(finite - 1.0) > 1e-12).sum()),
        "fake_factor_rows": 0,
        "constant_one_fallback_rows": 0,
        "first_non_one_factor_proof": first_non_one,
        "rows_by_reason": dict(sorted(counts.items())),
    }
    if report["factor_non_null_rows"] != report["quantiacs_backed_rows"]:
        raise ValueError("factor authority accounting mismatch")
    if report["factor_nan_rows"] != len(result) - report["quantiacs_backed_rows"]:
        raise ValueError("factor missingness accounting mismatch")
    if report["factor_nonconstant_count"] == 0 or first_non_one is None:
        raise ValueError("frozen source did not prove nonconstant factor semantics")
    return result, report


def debug_subset(full: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    instruments = sorted(set(full.index.get_level_values("instrument")))[:100]
    dates = full.index.get_level_values("datetime")
    selected = (
        dates.to_series(index=full.index).between("2018-01-01", "2019-12-31").to_numpy()
        & full.index.get_level_values("instrument").isin(instruments)
    )
    debug = full.loc[selected].copy()
    return debug, {
        "selection": "first 100 instrument IDs in lexicographic identity order; 2018-01-01 through 2019-12-31",
        "instrument_count": len(instruments),
        "row_count": len(debug),
        "start": "2018-01-01",
        "end": "2019-12-31",
    }


def validate_hdf(path: Path, expected_rows: int) -> pd.DataFrame:
    with pd.HDFStore(path, mode="r") as store:
        if store.keys() != ["/data"]:
            raise ValueError("HDF key contract mismatch")
    frame = pd.read_hdf(path, key="data")
    if (
        len(frame) != expected_rows
        or list(frame.index.names) != ["datetime", "instrument"]
        or list(frame.columns) != list(OUTPUT_FIELDS)
        or frame.index.has_duplicates
    ):
        raise ValueError("RD-Agent native HDF contract mismatch")
    return frame


def write_hdf_from_pickle(pickle_path: Path, hdf_path: Path, audit_path: Path) -> None:
    frame = pd.read_pickle(pickle_path)
    frame.to_hdf(hdf_path, key="data", mode="w", format="fixed")
    validated = validate_hdf(hdf_path, len(frame))
    audit_path.write_text(
        json.dumps({
            "rows": len(validated),
            "columns": list(validated.columns),
            "index_names": list(validated.index.names),
            "duplicates": bool(validated.index.has_duplicates),
        }, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_hdf_with_existing_runtime(
    frame: pd.DataFrame,
    hdf_path: Path,
    hdf_python: Path,
    temporary: Path,
) -> None:
    stem = hdf_path.parent.name
    pickle_path = temporary / f".{stem}.pickle"
    audit_path = temporary / f".{stem}-hdf-audit.json"
    frame.to_pickle(pickle_path)
    subprocess.check_call((
        str(hdf_python),
        str(Path(__file__).resolve()),
        "--hdf-helper",
        str(pickle_path),
        str(hdf_path),
        str(audit_path),
    ))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    expected = {
        "rows": len(frame),
        "columns": list(OUTPUT_FIELDS),
        "index_names": ["datetime", "instrument"],
        "duplicates": False,
    }
    if audit != expected:
        raise ValueError("external HDF writer contract mismatch")
    pickle_path.unlink()
    audit_path.unlink()


def write_readme(upstream_readme: Path, destination: Path) -> None:
    content = upstream_readme.read_text(encoding="utf-8").rstrip() + "\n\n"
    content += """## AQ P3 frozen-source note

This private derivative uses the already-frozen P2 US research authority.
`$factor` is populated only from the exact frozen Quantiacs `split_cumprod`
observation selected for the date-valid security episode. It remains NaN for
SimFin-only or otherwise unproven restoration authority. No missing factor is
synthesized, filled, or inferred.
"""
    destination.write_text(content, encoding="utf-8", newline="\n")


def materialize(args: argparse.Namespace) -> dict[str, object]:
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise FileExistsError(f"refusing to replace existing P3 factor source: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_root.with_name(f".{output_root.name}.tmp-{uuid.uuid4().hex}")
    temporary.mkdir()
    original_cwd = Path.cwd()
    try:
        before = provider_invariant(args.provider, args.market)
        source_sha = subprocess.check_output(
            ("git", "-C", str(args.qlib_source), "rev-parse", "HEAD"), text=True,
        ).strip()
        if source_sha != args.expected_qlib_sha:
            raise ValueError("Qlib source SHA mismatch")
        rdagent_sha = subprocess.check_output(
            ("git", "-C", str(args.rdagent_source), "rev-parse", "HEAD"), text=True,
        ).strip()
        if rdagent_sha != args.expected_rdagent_sha:
            raise ValueError("RD-Agent source SHA mismatch")

        episodes = load_episode_authority(
            args.inventory,
            args.staging / "episode-map.jsonl",
            args.expected_inventory_sha256,
        )
        date_index, asset_index, source_values, source_manifest = load_quantiacs_source(
            args.quantiacs_source,
            args.expected_quantiacs_manifest_sha256,
        )
        split_field_index = source_manifest["fields"].index("split_cumprod")
        os.chdir(temporary)
        qlib_frame = load_qlib_ohlcv(args.provider, args.market, args.start, args.end)
        if len(qlib_frame) != 1_267_963:
            raise ValueError("Qlib member-session count mismatch")
        full, accounting = attach_frozen_factors(
            qlib_frame,
            args.staging / "availability.jsonl.gz",
            episodes,
            date_index,
            asset_index,
            source_values,
            split_field_index,
        )
        debug, debug_rule = debug_subset(full)
        full_dir = temporary / "full"
        debug_dir = temporary / "debug"
        full_dir.mkdir()
        debug_dir.mkdir()
        full_path = full_dir / "daily_pv.h5"
        debug_path = debug_dir / "daily_pv.h5"
        write_hdf_with_existing_runtime(full, full_path, args.hdf_python, temporary)
        write_hdf_with_existing_runtime(debug, debug_path, args.hdf_python, temporary)
        write_readme(args.rdagent_readme, full_dir / "README.md")
        write_readme(args.rdagent_readme, debug_dir / "README.md")
        max_session = full.index.get_level_values("datetime").max()
        if max_session > pd.Timestamp("2024-12-31") or max_session >= pd.Timestamp("2026-09-14"):
            raise ValueError("sealed-OOS isolation violated")

        after = provider_invariant(args.provider, args.market)
        if before != after:
            raise ValueError("P2 Qlib provider changed during materialization")
        report = {
            "schema": "RDAGENTUSFactorSourceMaterializationV1",
            "qlib_source_sha": source_sha,
            "rdagent_source_sha": rdagent_sha,
            "provider_path": str(args.provider),
            "provider_invariant_before": before,
            "provider_invariant_after": after,
            "provider_mutated": False,
            "inventory_path": str(args.inventory),
            "inventory_sha256": sha256(args.inventory),
            "availability_sha256": sha256(args.staging / "availability.jsonl.gz"),
            "episode_map_sha256": sha256(args.staging / "episode-map.jsonl"),
            "instrument_identity_sha256": sha256(args.staging / "instrument-identity.jsonl"),
            "quantiacs_source_path": str(args.quantiacs_source),
            "quantiacs_source_manifest_sha256": sha256(args.quantiacs_source / "source_manifest.json"),
            "identity_join": "episode_id -> frozen provider_asset_identifier + exact session -> split_cumprod",
            "ticker_only_identity_join": False,
            "accounting": accounting,
            "debug_rule": debug_rule,
            "full_daily_pv_sha256": sha256(full_path),
            "debug_daily_pv_sha256": sha256(debug_path),
            "full_readme_sha256": sha256(full_dir / "README.md"),
            "debug_readme_sha256": sha256(debug_dir / "README.md"),
            "max_session": max_session.date().isoformat(),
            "sealed_oos_isolation": "PASS",
        }
        (temporary / "materialization-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.chdir(original_cwd)
        os.replace(temporary, output_root)
        return report
    except BaseException:
        os.chdir(original_cwd)
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--quantiacs-source", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--qlib-source", required=True, type=Path)
    parser.add_argument("--rdagent-source", required=True, type=Path)
    parser.add_argument("--rdagent-readme", required=True, type=Path)
    parser.add_argument("--hdf-python", required=True, type=Path)
    parser.add_argument("--expected-inventory-sha256", required=True)
    parser.add_argument("--expected-quantiacs-manifest-sha256", required=True)
    parser.add_argument("--expected-qlib-sha", required=True)
    parser.add_argument("--expected-rdagent-sha", required=True)
    parser.add_argument("--market", default="p2_pit")
    parser.add_argument("--start", default="2015-01-02")
    parser.add_argument("--end", default="2024-12-31")
    return parser.parse_args()


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--hdf-helper":
        write_hdf_from_pickle(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        print(json.dumps(materialize(parse_args()), sort_keys=True))
