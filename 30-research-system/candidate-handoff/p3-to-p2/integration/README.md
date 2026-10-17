# Candidate lifecycle vertical integration probe

This is a small integration/test entry point, not a production orchestration
service. It validates the existing P3 Candidate V4 projection and passes its
recorded P2 eligibility boundary forward. P4/P7/P8 fixtures are isolated to
`SYNTHETIC_TEST_ONLY`; that mode always leaves P9 execution blocked.

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
  "$AQ_REPO/30-research-system/candidate-handoff/p3-to-p2/integration/run_candidate_flow.py" \
  --mode REAL_CANDIDATE_V4 \
  --candidate "$AQ_CANDIDATE_JSON" \
  --recorder-artifacts "$AQ_RECORDER_ARTIFACTS"
```

The real path is provenance-only. It stops if the P2 status is anything other
than the verified `INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION` state; a different
state requires an actual P2 decision artifact and is deliberately not inferred
here.

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
  "$AQ_REPO/30-research-system/candidate-handoff/p3-to-p2/integration/run_candidate_flow.py" \
  --mode SYNTHETIC_TEST_ONLY
cd "$AQ_REPO/30-research-system/candidate-handoff/p3-to-p2/integration"
python -m unittest -v test_candidate_flow.py
```

Synthetic outputs are labeled as fixtures, never persisted as formal evidence,
and always set P9 execution permission to false. Run the P7 session selector
with the existing `p5-fundamental-intelligence` runtime, which already contains
the pinned `exchange_calendars` 4.13.2 dependency; do not install it into other
environments. P8 validation checks the frozen JSON Schema only; it does not
call a portfolio optimizer or create a TargetPortfolio decision. No broker
package is imported by this integration.

## Local validation snapshot

At implementation review, the current real Candidate V4 path loaded and
validated the existing `FINISHED` Recorder artifact hashes and stopped at
`INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION`. The synthetic integration test passed
twice. Existing focused suites passed: Candidate V4 projection 13/13, P4
policy 52/52, P7 roster contract/handoff 13/13, and P8 contract validation
12/12. No sealed OOS data, training, broker endpoint, or order was accessed.
