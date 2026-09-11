"""Run the single active P1 PIT research-ready composition path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aq_pit.canonical import canonical_bytes
from aq_pit.thin_runtime import build_research_ready_universe


def run(data_root: Path, output_path: Path) -> dict[str, object]:
    universe = build_research_ready_universe(data_root)
    payload = {
        "schema_version": "P1ResearchReadyUniverseV1",
        "research_ready": universe.gate.research_ready,
        "facts_hash": universe.facts.facts_hash,
        "output_hash": universe.compilation.output_hash,
        "rows": universe.rows,
        "metrics": dict(universe.gate.metrics),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(payload) + b"\n")
    temporary.replace(output_path)
    summary = {key: value for key, value in payload.items() if key != "rows"}
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.data_root, args.output)


if __name__ == "__main__":
    main()
