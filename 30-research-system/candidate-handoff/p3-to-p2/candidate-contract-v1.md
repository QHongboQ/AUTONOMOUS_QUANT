# P3 Candidate-to-P2 Identity Contract V1

## Status and scope

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V1
CONTRACT_DEFINITION = MATERIALIZED
REAL_CANDIDATE_INSTANCE = DEFERRED_UNTIL_REAL_RUN
AQ_REQUIRED_IDENTITY_FIELD_COUNT = 8
CUSTOM_REGISTRY_REQUIRED = NO
CUSTOM_RUNTIME_VALIDATOR_REQUIRED = NO
```

This document and its JSON Schema define the static identity boundary between
one completed P3 research result and P2 Certification. They do not create a
Candidate instance, execute RD-Agent or Qlib, validate performance, confer
eligibility, or issue certification.

The normative machine-readable contract is
`candidate-contract-v1.schema.json`. A producer must reject rather than emit a
partially populated object. Run IDs, DVC hashes, model hashes, and prediction
hashes may only come from a real completed execution.

## Exact top-level contract

A Candidate instance has exactly these eight required top-level fields and no
ninth field:

1. `candidate_contract_version`
2. `candidate_id`
3. `rdagent_research_identity`
4. `qlib_recorder_identity`
5. `artifact_identity_bundle`
6. `dataset_identity_bundle`
7. `runtime_identity_bundle`
8. `p2_target_and_eligibility_boundary`

Every nested identity object is closed to undeclared properties. Required
identity values are immutable content, source, DVC, or upstream run
identifiers; operational paths and display-only metadata are excluded.

## Candidate ID

`candidate_id` is computed from exactly seven fields, in this projection:

1. `candidate_contract_version`
2. `rdagent_research_identity`
3. `qlib_recorder_identity`
4. `artifact_identity_bundle`
5. `dataset_identity_bundle`
6. `runtime_identity_bundle`
7. `p2_target_and_eligibility_boundary`

The `candidate_id` field is excluded from its own projection. The normative
calculation is:

```text
candidate_id =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8(
        RFC_8785_JCS(projected_object)
      )
    )
  )
```

```text
CANDIDATE_ID_INPUT_FIELD_COUNT = 7
CANONICALIZATION = RFC 8785 JSON Canonicalization Scheme (JCS)
ENCODING = UTF-8
DIGEST = SHA-256
HEX_CASE = lowercase
```

JCS determines object-member ordering. Arrays that represent collections must
be sorted before canonicalization as follows:

- content identities: `logical_role`, then `sha256`;
- parent lineage: `relation`, then `parent_research_sha256`;
- selected templates: `relative_name`, then `sha256`;
- artifact identities: `logical_role`, then `sha256`, then DVC algorithm and
  value;
- DVC dependencies: `logical_role`, then DVC algorithm and value.

This contract does not implement a project-owned canonicalization library.
Candidate producers and consumers must use a conforming RFC 8785
implementation.

## Ownership of identity bundles

### RD-Agent research identity

The research identity content-binds the selected research mode and scenario
family, hypothesis content, task content, experiment structure, generated
factor/model code, and parent/based-experiment lineage. Workspace paths,
workspace UUIDs, loop/step/trace indices, and temporary directory names cannot
serve as identity.

### Qlib Recorder / MLflow identity

The recorder identity contains the exact Qlib/MLflow `experiment_id`, exact
`run_id`, and terminal status. The only valid status is `FINISHED`. Names and
"latest" selection are not execution identities.

### Artifact identity

The artifact bundle binds:

- DVC stage `p3_rdagent_us_quant_research`;
- the exact DVC lock file and stage-entry content identities;
- the DVC run-root output identity;
- only the static templates selected by the real run;
- the rendered per-run Qlib configuration;
- generated research code;
- the serialized model artifact;
- the prediction artifact.

Paths alone are never artifact identity. The five permitted static template
name/hash pairs are frozen in the JSON Schema. A Candidate lists only the
subset actually selected by its real execution.

### Dataset identity

The dataset bundle freezes the audited P2 provider-build, calendar,
instrument, PIT membership, date-bound, and row-count identities. It also
requires the relevant DVC dependency identities from the actual P3 run. It
does not copy provider files or create another dataset hashing engine.

### Runtime identity

The runtime bundle binds exact RD-Agent source, installed wheel, environment
freeze, and Qlib source identities. Version strings and absolute installation
paths are not sufficient authority.

### P2 target and eligibility

The P2 boundary binds Protocol V1 content, activation, freeze authority,
candidate eligibility, and the sealed-OOS boundary. P2 Certification is the
sole protocol-freeze and eligibility authority. A future instance must state
one of:

- `ELIGIBLE_UNDER_TARGET_PROTOCOL`;
- `INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION`.

Because Protocol V1 already freezes its Candidate inventory, a new P3
Candidate cannot silently claim eligibility. P3 cannot change eligibility,
edit the protocol, promote to production, issue `CERTIFIED`, or attest that it
avoided sealed OOS if it accessed that boundary.

The schema therefore requires:

```text
sealed_oos_accessed_by_p3 = false
p3_can_issue_certified = false
p3_can_edit_protocol = false
p3_can_promote_to_production = false
```

## Identity exclusions

The Candidate ID input excludes timestamps, wall-clock durations, hostnames,
machine names, absolute paths, temporary directories, workspace UUIDs as sole
identity, display names, metrics, returns, Sharpe, IC, win rate, PnL,
statistical-gate outcomes, and certification results. Such values may exist in
their upstream systems as diagnostics or evidence, but not in these seven
immutable identity bundles.

## Fail-closed handoff

P2 must reject a handoff if the schema fails, the recomputed RFC 8785 Candidate
ID differs, any upstream or content identity is absent or mismatched, the run
is not `FINISHED`, a required model or prediction is absent, the DVC stage or
lock identity differs, the Candidate is not eligible for its target protocol,
or sealed-OOS access is indicated.

Schema conformance establishes identity shape only. It does not establish
that the declared hashes match external bytes; that comparison remains with
the authoritative upstream and DVC owners. No Candidate registry, trial
ledger, experiment database, runtime recorder, certification engine, or
generic validator service is introduced.

## Materialization boundary

No Candidate object or synthetic example is committed with this contract.
The first real instance remains blocked until a separately authorized P3 run
produces a `FINISHED` Qlib/MLflow run, a P3 DVC lock entry, and real generated
code, model, prediction, dataset-dependency, and run-root output identities.

```text
REAL_CANDIDATE_INSTANCE_CREATED = NO
FAKE_CANDIDATE_INSTANCE_CREATED = NO
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_INSTANCE_001
```
