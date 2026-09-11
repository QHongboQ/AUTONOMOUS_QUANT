"""CLI composition from the public PIT output to DatasetSnapshot files."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PIT_ROOT = REPOSITORY_ROOT / "10-data-system" / "universe" / "sp500-pit"
sys.path.insert(0, str(PIT_ROOT))

from aq_pit import build_research_ready_universe  # noqa: E402
from aq_dataset_snapshot import export_dataset_snapshot  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    universe = build_research_ready_universe(args.data_root)
    snapshot = export_dataset_snapshot(universe, args.output)
    print(json.dumps(asdict(snapshot), sort_keys=True))


if __name__ == "__main__":
    main()
