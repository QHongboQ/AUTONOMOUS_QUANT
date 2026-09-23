"""DVC entry point for the Qlib-native P5 dataset handoff check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aq_p5_qlib_handoff import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate_dataset(
        projection_root=args.projection, selection_path=args.selection, output=args.output,
    ), sort_keys=True))


if __name__ == "__main__":
    main()
