"""Inert local test target. It does not invoke RD-Agent, Qlib, an LLM, or a broker."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--target-log", type=Path, required=True)
    parser.add_argument("--outcome", choices=("success", "failure"), required=True)
    args = parser.parse_args()

    result = {
        "classification": "SYNTHETIC_TEST_ONLY",
        "request_id": args.request_id,
        "result": "NO_CANDIDATE_GENERATED",
        "candidate_count": 0,
        "rdagent_invoked": False,
        "qlib_invoked": False,
        "llm_calls": 0,
        "broker_actions": 0,
    }
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    args.target_log.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.target_log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        offset = 0
        while offset < len(encoded):
            offset += os.write(fd, encoded[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    directory_fd = os.open(args.target_log.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    print(json.dumps(result, sort_keys=True))
    return 0 if args.outcome == "success" else 17


if __name__ == "__main__":
    raise SystemExit(main())
