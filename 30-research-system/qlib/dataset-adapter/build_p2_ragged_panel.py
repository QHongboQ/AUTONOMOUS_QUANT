"""CLI for the frozen P2 observations-to-Qlib staging boundary."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from aq_qlib_handoff.ragged_panel import build_ragged_staging


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--quantiacs-source", required=True, type=Path)
    parser.add_argument("--simfin", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build_ragged_staging(
        args.inventory,
        args.quantiacs_source,
        args.simfin,
        args.output,
        expected_inventory_sha256="3c73a9ec0260a3187529a557b271fe5c34ba332427ae41ed713f5459a28395c2",
        expected_quantiacs_manifest_sha256="80f42e07b80dbc2fbe211d9b44ab4b6a0e5e9db3943098effb3976b92a49e73b",
        expected_simfin_sha256="3a7c21afefc044a9c28f5a1f1069840fe092d7f44b937c7d9b489bcc5c9fd2a9",
    )
    print(json.dumps(asdict(result), sort_keys=True))


if __name__ == "__main__":
    main()
