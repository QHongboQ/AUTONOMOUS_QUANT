from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import exchange_calendars
import pandas as pd
import pandera
import pandera.pandas as pa
import pyarrow
import vintage as v
import aq_xnys_calendar
from aq_xnys_calendar import sessions_in_range

SERIES = ("CPIAUCSL", "UNRATE")
FEATURES = ("macro_v1_cpiaucsl_d2_log", "macro_v1_unrate_d1")
VINTAGE_SHA = "c55b6d5bd801a21e5844600fc6110de4a3c8dd4b"
QLIB_SOURCE_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
OBS_START, AS_OF = "2014-12-01", "2024-12-31"
SESSION_START, SESSION_END = "2015-04-01", "2024-12-31"


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def logical_sha(frame: pd.DataFrame) -> str:
    normalized = frame.sort_index().sort_index(axis=1)
    data = normalized.to_json(
        orient="table", date_format="iso", date_unit="ns", double_precision=15
    ).encode()
    return hashlib.sha256(data).hexdigest()


def evidence_id(row: pd.Series) -> str:
    values = [
        row["entity"], row["field"], str(row["observed_at"].date()),
        str(row["known_at"].date()), format(row["value"], ".17g"),
        row["source"], row["source_url"], row["vintage"],
    ]
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def runtime_check(vintage_source: Path) -> None:
    if v.__version__ != "0.9.0" or duckdb.__version__ != "1.5.5":
        raise RuntimeError("pinned upstream runtime mismatch")
    sha = subprocess.run(
        ["git", "-C", str(vintage_source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if sha != VINTAGE_SHA:
        raise RuntimeError("Vintage source identity mismatch")


def load_evidence() -> pd.DataFrame:
    frames = []
    for series in SERIES:
        raw = v.macro(series, start=OBS_START, end=AS_OF, as_of=AS_OF).reset_index()
        raw = raw.rename(columns={series: "value"})
        raw["series_id"] = series
        frames.append(raw)
    frame = pd.concat(frames, ignore_index=True)
    keep = [
        "entity", "field", "series_id", "observed_at", "known_at", "value",
        "source", "source_url", "vintage",
    ]
    frame = frame[keep].copy()
    frame["observed_at"] = pd.to_datetime(frame["observed_at"])
    frame["known_at"] = pd.to_datetime(frame["known_at"])
    frame["value"] = pd.to_numeric(frame["value"], errors="raise").astype(float)
    if frame["known_at"].max() > pd.Timestamp(AS_OF):
        raise RuntimeError("Vintage returned evidence after SOURCE_AS_OF")
    frame["evidence_id"] = frame.apply(evidence_id, axis=1)
    return frame.sort_values(["series_id", "observed_at", "known_at", "evidence_id"])


def validate(evidence: pd.DataFrame, state: pd.DataFrame, provenance: pd.DataFrame) -> None:
    pa.DataFrameSchema({
        "series_id": pa.Column(str, pa.Check.isin(SERIES)),
        "observed_at": pa.Column(pa.DateTime), "known_at": pa.Column(pa.DateTime),
        "value": pa.Column(float, nullable=False),
        "evidence_id": pa.Column(str, pa.Check.str_length(64, 64), unique=True),
    }, strict=False, coerce=True).validate(evidence, lazy=True)
    pa.DataFrameSchema(
        {name: pa.Column(float, nullable=True) for name in FEATURES},
        index=pa.Index(pa.DateTime, name="session", unique=True),
        checks=[pa.Check(lambda data: data.index.is_monotonic_increasing),
                pa.Check(lambda data: data.index.min() == pd.Timestamp(SESSION_START)
                         and data.index.max() == pd.Timestamp(SESSION_END))],
        strict=True, ordered=True, coerce=True,
    ).validate(state, lazy=True)
    pa.DataFrameSchema({
        "feature_id": pa.Column(str, pa.Check.isin(FEATURES)),
        "state_effective_session": pa.Column(pa.DateTime),
        "dependency_position": pa.Column(int),
        "upstream_evidence_identity": pa.Column(str, pa.Check.str_length(64, 64)),
    }, checks=[pa.Check(lambda data: not data.duplicated([
        "feature_id", "state_effective_session", "dependency_position"
    ]).any())], strict=False, coerce=True).validate(provenance, lazy=True)
    counts = provenance.groupby(["feature_id", "state_effective_session"]).size()
    expected = counts.index.get_level_values(0).map({FEATURES[0]: 3, FEATURES[1]: 2})
    if not (counts.to_numpy() == expected.to_numpy()).all():
        raise RuntimeError("provenance dependency count mismatch")


def write_frame(frame: pd.DataFrame, path: Path, index: bool) -> None:
    frame.to_parquet(path, engine="pyarrow", compression="zstd", index=index)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sql", type=Path, default=Path(__file__).with_name("macro_v1.sql"))
    parser.add_argument("--vintage-source", type=Path, required=True)
    args = parser.parse_args()
    runtime_check(args.vintage_source)
    if not os.environ.get("FRED_API_KEY"):
        raise RuntimeError("FRED credential unavailable")
    args.output.mkdir(parents=True, exist_ok=True)
    evidence = load_evidence()
    all_sessions = pd.DataFrame({"session": pd.to_datetime(sessions_in_range("2014-01-02", AS_OF))})
    target_sessions = pd.DataFrame({"session": pd.to_datetime(sessions_in_range(SESSION_START, SESSION_END))})
    con = duckdb.connect(":memory:")
    con.register("evidence_input", evidence)
    con.register("all_sessions", all_sessions)
    con.register("target_sessions", target_sessions)
    con.execute(args.sql.read_text(encoding="utf-8"))
    evidence_out = con.execute("SELECT * FROM mapped_evidence ORDER BY series_id, observed_at, known_at, evidence_id").fetchdf()
    state = con.execute("SELECT * FROM macro_state ORDER BY session").fetchdf().set_index("session")
    provenance = con.execute("SELECT * FROM provenance").fetchdf()
    validate(evidence_out, state, provenance)
    paths = {name: args.output / name for name in ("evidence.parquet", "macro-state.parquet", "provenance.parquet")}
    write_frame(evidence_out, paths["evidence.parquet"], False)
    write_frame(state, paths["macro-state.parquet"], True)
    write_frame(provenance, paths["provenance.parquet"], False)
    manifest = {
        "schema_version": 1, "source_authority": "OFFICIAL_FRED_ALFRED",
        "vintage_version": v.__version__, "vintage_source_identity": VINTAGE_SHA,
        "duckdb_version": duckdb.__version__, "pandera_version": pandera.__version__,
        "pyarrow_version": pyarrow.__version__, "pandas_version": pd.__version__,
        "exchange_calendars_version": exchange_calendars.__version__,
        "exchange_calendars_authority": "aq_xnys_calendar",
        "exchange_calendars_authority_sha256": sha_file(Path(aq_xnys_calendar.__file__).with_name("adapter.py")),
        "source_observed_start": OBS_START, "source_as_of": AS_OF,
        "session_start": SESSION_START, "session_end": SESSION_END,
        "feature_ids": list(FEATURES), "transform_codes": {FEATURES[0]: 6, FEATURES[1]: 2},
        "row_counts": {"evidence": len(evidence_out), "macro_state": len(state), "provenance": len(provenance)},
        "null_counts": {key: int(value) for key, value in state.isna().sum().items()},
        "logical_sha256": {"evidence": logical_sha(evidence_out), "macro_state": logical_sha(state), "provenance": logical_sha(provenance)},
        "physical_sha256": {name: sha_file(path) for name, path in paths.items()},
        "known_at_precision": "DATE_ONLY", "same_day_visibility": "PROHIBITED",
        "revision_policy": "LATEST_VISIBLE_PER_OBSERVED_AT",
        "session_state_carry_forward": True,
        "upstream_missing_observation_imputation": False, "interpolation": False, "backfill": False,
        "canonical_storage_grain": "SESSION_GLOBAL", "permanent_instrument_broadcast_storage": False,
        "runtime_identity": {"python": sys.version.split()[0], "executable": str(Path(sys.executable))},
        "p2_v2_sealed_oos_accessed": False,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
