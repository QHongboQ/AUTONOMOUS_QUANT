"""Deterministically seal the five authorized private pilot artifact surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def identity(path: Path) -> dict[str, object]:
    files = sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else [path]
    if not files:
        raise ValueError(f"artifact is absent or empty: {path}")
    rows = []
    for item in files:
        payload = item.read_bytes()
        rows.append(
            {
                "path": item.relative_to(path).as_posix() if path.is_dir() else item.name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return {"path": path.as_posix(), "files": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--projection", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--quality", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    artifacts = {
        "pilot_manifest": identity(args.manifest),
        "admitted_sparse_events": identity(args.events),
        "session_projection": identity(args.projection),
        "provenance_sidecar": identity(args.provenance),
        "quality_report": identity(args.quality),
    }
    canonical = json.dumps(artifacts, sort_keys=True, separators=(",", ":")).encode()
    seal = {
        "schema": "P5HybridHistoricalDatasetPilotDvcSealV1",
        "artifact_count": 5,
        "artifacts": artifacts,
        "artifact_set_sha256": hashlib.sha256(canonical).hexdigest(),
        "fsds_bulk_catalog_copied_into_dvc": False,
        "p2_v2_sealed_oos_accessed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
