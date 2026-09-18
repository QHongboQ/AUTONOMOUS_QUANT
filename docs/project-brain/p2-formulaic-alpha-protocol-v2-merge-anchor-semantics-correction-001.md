# P2 Formulaic Alpha Protocol V2 Merge-Anchor Semantics Correction 001

Status: **PASS — AUTHORITY INTERPRETATION CORRECTED, PROTOCOL BYTES UNCHANGED**

Date: 2026-09-18

## Decision

```text
TASK = P2_FORMULAIC_ALPHA_PROTOCOL_V2_MERGE_ANCHOR_SEMANTICS_CORRECTION_001
CORRECTION_CLASS = AUTHORITY_INTERPRETATION_ONLY
PROTOCOL_V2_MODIFIED = NO
COHORT_MANIFEST_MODIFIED = NO
DVC_PROTOCOL_V2_FREEZE_SEAL_MODIFIED = NO
PROTOCOL_V2_ACTIVATED = NO
SEALED_OOS_START_SESSION = UNRESOLVED_PENDING_MAIN_ACTIVATION
```

The prior read-only merge-gate interpretation treated the pre-merge branch
head

```text
6c7f7cd7449a6d421489f9c90eea44490e608aad
```

as if that exact SHA had to become an ancestor of `origin/main`. That
interpretation is **superseded**. It was stricter than the established P2 V1
precedent and would unnecessarily conflict with this repository's linear-history
and squash-merge workflow.

## V1 precedent

Protocol V1 was preregistered through PR #44.

```text
V1_PR_HEAD_SHA =
22de40e1b8b2d5905d9c64df9edf40dd8a93231e

V1_MAIN_SQUASH_COMMIT_SHA =
8cd703b4108d2e377d146de8384b63c0355e93a6
```

The V1 activation authority records:

```text
freeze_merge_sha =
8cd703b4108d2e377d146de8384b63c0355e93a6

sealed_oos_start_session =
2026-09-14
```

Therefore V1 did **not** require the original PR head SHA to survive as a main
ancestor. The authoritative freeze anchor was the main-side commit that first
contained the exact frozen protocol content after merge.

## V2 corrected interpretation

Protocol V2 keeps its existing frozen start rule:

```text
THE_FIRST_XNYS_SESSION_STRICTLY_AFTER_THE_PROTOCOL_V2_FREEZE_COMMIT_BECOMES_PART_OF_ORIGIN_MAIN
```

For V2, `PROTOCOL_V2_FREEZE_COMMIT` is interpreted consistently with V1 as:

> the first `origin/main` commit that is proven to contain the exact frozen
> Protocol V2 bytes and exact frozen Formulaic Alpha cohort bytes.

The pre-merge branch head remains provenance for the frozen work, but it is
**not required** to survive as a main ancestor.

```text
V2_BRANCH_FREEZE_HEAD =
6c7f7cd7449a6d421489f9c90eea44490e608aad

V2_BRANCH_FREEZE_HEAD_MUST_BE_MAIN_ANCESTOR =
NO

V2_PROTOCOL_SHA256 =
18b80277b6529422298e43681bb344e54199a58477cdba20d96fd8220bdc950a

V2_COHORT_MANIFEST_SHA256 =
53920302856592fb43bbffb011423731893ac0a995a04194541c39d69ecfde70
```

## Repository merge policy

The existing repository policy may remain unchanged:

```text
ALLOW_MERGE_COMMIT = false
ALLOW_SQUASH_MERGE = true
ALLOW_REBASE_MERGE = true
REQUIRED_LINEAR_HISTORY = true
REPOSITORY_POLICY_CHANGE_REQUIRED = NO
```

The authorized V2 path is a normal PR followed by **squash merge**.

No temporary weakening of main protection or linear-history policy is required.

## Post-merge activation requirements

After squash merge, a separate activation task must:

1. fetch the new `origin/main`;
2. identify the main-side squash commit that introduced the frozen V2 content;
3. verify exact Protocol V2 SHA-256:
   `18b80277b6529422298e43681bb344e54199a58477cdba20d96fd8220bdc950a`;
4. verify exact cohort-manifest SHA-256:
   `53920302856592fb43bbffb011423731893ac0a995a04194541c39d69ecfde70`;
5. verify the frozen V2 DVC seal/cohort authorities are present and consistent;
6. record that verified main-side squash commit as `freeze_merge_sha`;
7. resolve the first XNYS session strictly after that main merge event;
8. create the immutable V2 activation record;
9. start the 126-session sealed-OOS clock from that resolved session;
10. count zero pre-activation sessions retroactively.

Content equivalence must be proven by the frozen hashes. A merge commit is not
required.

## Non-actions

```text
PROTOCOL_V2_BYTES_CHANGED = NO
COHORT_BYTES_CHANGED = NO
PROTOCOL_V1_CHANGED = NO
V1_ACTIVATION_CHANGED = NO
V2_ACTIVATED = NO
SEALED_OOS_ACCESSED = NO
CERTIFICATION_DECISION_EXECUTED = NO
CERTIFIED_CANDIDATE_COUNT = 0
REPOSITORY_SETTINGS_CHANGED = NO
PR_CREATED = NO
MERGED = NO
```

## Next

```text
CURRENT_NEXT =
P2_FORMULAIC_ALPHA_PROTOCOL_V2_MAIN_SQUASH_MERGE_001_PENDING_USER_AUTHORIZATION
```

That merge task may create the PR and perform the normal squash merge only after
explicit user authorization. The subsequent activation task must independently
verify the main-side frozen hashes before starting the V2 sealed-OOS clock.
