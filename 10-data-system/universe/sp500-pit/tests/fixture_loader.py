from __future__ import annotations

import hashlib
import json
from pathlib import Path


FIXTURE_ROOT = Path(__file__).with_name("fixtures")


def _portable_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def load_fixture(name: str) -> dict[str, object]:
    manifest = json.loads((FIXTURE_ROOT / "sha256_manifest.json").read_text(encoding="utf-8"))
    path = FIXTURE_ROOT / name
    actual = hashlib.sha256(_portable_bytes(path)).hexdigest()
    expected = manifest["files"][name]
    if actual != expected:
        raise ValueError(f"frozen PIT fixture hash mismatch: {name}")
    return json.loads(path.read_text(encoding="utf-8"))
