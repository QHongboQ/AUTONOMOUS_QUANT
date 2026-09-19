# P5 Valuein native identity projection

Ownership boundary:

- Capability: bounded historical security identity.
- Upstream owner: Valuein native `security`, `entity`, `references`, and
  `index_membership` tables.
- Ownership mode: upstream leaf.
- Upstream already deployed: yes.
- AQ implementation allowed: yes, limited to date containment, conflict
  rejection, provenance identity, and direct `EpisodeSecCikBindingV1`
  projection.
- Custom engine required: no.

`aq_valuein_adapter` exposes one fail-closed projection function. A binding is
created only when one exact-symbol Valuein security identity contains the full
P1 episode, the entity and references relations agree on one CIK, and a
containing `index_membership` row has `index_name == "SP500"`. Russell indexes,
fund holdings, current-ticker backfill, partial ticker intervals, and competing
identities cannot satisfy the gate.

P1 owns S&P 500 membership and ticker-episode boundaries. Valuein membership
is an upstream oracle and conflict check; Valuein security lifetime is allowed
to contain rather than equal the P1 episode. The projected binding uses P1's
interval and distinguishes `PASS_EXACT` from `PASS_CORROBORATED`.

The bounded multi-record entry point `project_valuein_native_bindings` adds two
fail-closed cases without ticker branches: a terminal provider boundary may
differ from P1 only when the supplied authoritative XNYS session set proves
zero uncovered sessions, and exactly two contiguous security rows may be
projected only when Valuein supplies one explicit SP500 `successor_cik`
relation. The original singular entry point delegates to this logic and still
rejects any result containing more than one binding record.

Valuein fundamentals and the audited 11-metric correspondence are oracle evidence only. They have no tracked production admission path. `FundamentalEvidenceV1` remains EdgarTools-only and EdgarTools remains the exact fundamentals authority.
