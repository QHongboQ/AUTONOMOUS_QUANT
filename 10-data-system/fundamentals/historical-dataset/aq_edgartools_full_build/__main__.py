"""DVC-invoked, project-bounded P5 transformation stage entrypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bulk import build_bulk


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("bulk",))
    parser.add_argument("--binding", required=True, type=Path)
    parser.add_argument("--exclusion", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build_bulk(args.output, binding_path=args.binding, exclusion_path=args.exclusion)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
