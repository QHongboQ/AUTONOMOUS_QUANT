"""DVC entry point for the bounded P5 session projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aq_p5_projection import build_projection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bulk", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_projection(
        bulk_root=args.bulk,
        episodes_path=args.episodes,
        binding_path=args.bindings,
        output=args.output,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
