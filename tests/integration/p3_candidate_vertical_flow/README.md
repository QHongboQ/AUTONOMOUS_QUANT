# Candidate lifecycle vertical integration tests

This is a test-only integration entry point, not a production orchestration
service. It validates the existing P3 Candidate V4 projection and independently
checks current P2 V2 protocol, activation, and frozen-cohort authorities rather
than trusting the Candidate's self-reported eligibility field. P4/P7/P8
fixtures are isolated to `SYNTHETIC_TEST_ONLY`; that mode always leaves P9
execution blocked.

## Real Candidate V4 provenance-only path

Run from WSL with the already-established `rdagent4qlib` environment and the
existing private Candidate/Recorder paths. The command reads the Candidate
record and hashes the four required Recorder files; it does not deserialize
predictions, train, evaluate outcomes, or access sealed OOS.

```bash
AQ_REPO=/path/to/clean/AUTONOMOUS_QUANT/worktree
AQ_CANDIDATE_JSON=/private/path/to/candidate-v4.json
AQ_RECORDER_ARTIFACTS=/private/path/to/finished/recorder/artifacts
PYTHONPATH="$AQ_REPO/30-research-system/candidate-handoff/p3-to-p2:$AQ_REPO/40-certification-system/champion-challenger/p4-residual-thin-policy:$AQ_REPO/30-research-system/qlib/p7-native-ensemble:$AQ_REPO/10-data-system/trading-calendar/xnys/exchange-calendars-adapter:$AQ_RFC8785_RUNTIME" \
  /path/to/existing/rdagent4qlib/bin/python \
  "$AQ_REPO/tests/integration/p3_candidate_vertical_flow/run_candidate_flow.py" \
  --mode REAL_CANDIDATE_V4 \
  --candidate "$AQ_CANDIDATE_JSON" \
  --recorder-artifacts "$AQ_RECORDER_ARTIFACTS"
```

The real path is provenance-only. The integration verifies the pinned V2
protocol digest against the separate activation record, verifies the frozen
cohort digest and 17-member count, and derives the V4 ineligibility from absence
from that V3 cohort. A conflicting Candidate self-report fails closed. This is
an eligibility check, not a P2 certification result.

The current real run validates the existing Candidate V4 / Recorder provenance
and reports its P2 ineligibility. It creates no P4 lifecycle decision, P7
roster, P8 target, or order. Additional real-path blockers are explicit in the
output: the frozen P7 protocol requires Candidate V3 identity, and P8 has no
real Certified input or approved human risk envelope. The P9 field is a
fail-closed permission handoff only; no P9 broker client/interface is invoked.

## Synthetic interface check

```bash
AQ_REPO=/path/to/clean/AUTONOMOUS_QUANT/worktree
PYTHONPATH="$AQ_REPO/40-certification-system/champion-challenger/p4-residual-thin-policy:$AQ_REPO/30-research-system/qlib/p7-native-ensemble:$AQ_REPO/10-data-system/trading-calendar/xnys/exchange-calendars-adapter:$AQ_RFC8785_RUNTIME" \
  /path/to/existing/p5-fundamental-intelligence/bin/python \
  "$AQ_REPO/tests/integration/p3_candidate_vertical_flow/run_candidate_flow.py" \
  --mode SYNTHETIC_TEST_ONLY
cd "$AQ_REPO/tests/integration/p3_candidate_vertical_flow"
python -m unittest -v test_candidate_flow.py
```

Synthetic outputs are labeled as fixtures, never persisted as formal evidence,
and always set P9 execution permission to false. The current P4 decision record
has no native decision-evidence identity, while P7's frozen member contract
requires `authorization_evidence_id` plus immutable external delivery metadata.
The synthetic path therefore reports
`P4_TO_P7_SYNTHETIC_PROVENANCE=NOT_CONNECTED_CONTRACT_GAP` and does not invent
an authorization ID or create a roster. P8 is checked independently as
`SCHEMA_ONLY`: an RFC 8785 0.1.4 content identity is computed for the fixture,
but no portfolio decision is created. No broker package is imported by this
integration.

## Local validation snapshot

The real Candidate V4 path validates the existing `FINISHED` Recorder artifact
hashes and stops at `INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION`, derived from the
current P2 V2 protocol/activation/cohort authorities. The V4 record references
P2 V1, is not in the frozen 17-member V2 Candidate V3 cohort, and its consumed
research Test is not treated as OOS. Candidate self-report conflict fails
closed. Synthetic P4 decisions are exercised, but
`P4_TO_P7_SYNTHETIC_PROVENANCE=NOT_CONNECTED_CONTRACT_GAP`: P4's current decision
evidence has no native evidence identity, while P7 requires a member-level
authorization evidence identity and immutable external delivery metadata. No
roster is created. `P7_TO_P8=SCHEMA_ONLY` validates a fixture with RFC 8785
0.1.4 identities; no TargetPortfolio is created. `P8_TO_P9=PERMISSION_DENIAL_ONLY`.

Validation: Candidate V4 projection 19/19 in the LF-canonical test worktree;
P4 policy 53/53; P7 roster contract/handoff 7/7 and 6/6 in their existing
dependency environments; P8 contract 12/12; the integration suite 3/3 on two
consecutive runs, with identical synthetic CLI output on replay. No sealed OOS
data, training, broker endpoint, or order is accessed by this test entry point.
