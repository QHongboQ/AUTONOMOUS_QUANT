"""Seal bounded upstream-integration report identities for DVC ownership."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-report", required=True, type=Path)
    parser.add_argument("--qlib-report", required=True, type=Path)
    parser.add_argument("--skfolio-report", required=True, type=Path)
    parser.add_argument("--arch-report", required=True, type=Path)
    parser.add_argument("--blocker-ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    provider = load(args.provider_report)
    qlib = load(args.qlib_report)
    skfolio = load(args.skfolio_report)
    arch = load(args.arch_report)
    blockers = load(args.blocker_ledger)

    if provider["total_member_session_rows"] != 1_267_963:
        raise RuntimeError("provider report does not match the accepted P2 row count")
    if qlib["evidence_sha256"] != skfolio["input_sha256"]:
        raise RuntimeError("Qlib-to-skfolio evidence hash mismatch")
    if qlib["evidence_sha256"] != arch["input_sha256"]:
        raise RuntimeError("Qlib-to-arch evidence hash mismatch")
    if blockers["schema_version"] != "P2UpstreamCertificationBlockerLedgerV1":
        raise RuntimeError("unexpected blocker-ledger schema")

    result = {
        "dependency_sha256": {
            "arch_report": sha256(args.arch_report),
            "blocker_ledger": sha256(args.blocker_ledger),
            "provider_report": sha256(args.provider_report),
            "qlib_report": sha256(args.qlib_report),
            "skfolio_report": sha256(args.skfolio_report),
        },
        "p2_blocking_blocker_count": sum(
            bool(item["p2_blocking"]) for item in blockers["blockers"]
        ),
        "schema_version": "P2UpstreamCertificationEvidenceSealV1",
        "status": "PASS_WITH_RECORDED_BLOCKERS" if blockers["blockers"] else "PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
