"""CLI for the public DatasetSnapshot-to-Qlib universe handoff."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from aq_qlib_handoff import prepare_qlib_universe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = prepare_qlib_universe(args.snapshot, args.output)
    print(json.dumps(asdict(result), sort_keys=True))


if __name__ == "__main__":
    main()
