# P5 Valuein identity evidence leaf

Ownership boundary:

- Capability: bounded historical identity evidence.
- Upstream owner: Valuein as an exact-only external evidence leaf.
- Ownership mode: upstream leaf.
- Upstream already deployed: yes.
- AQ implementation allowed: yes, limited to direct identity classification and exact contract admission.
- Custom engine required: no.

`aq_valuein_adapter` is deliberately a single direct identity module. It does not own P1 identity, SEC retrieval, fundamentals, a security master, provider routing, or generic schema translation. Compatible, partial, ambiguous, conflicting, and absent Valuein identity candidates never become authority automatically.

Valuein fundamentals and the audited 11-metric correspondence are oracle evidence only. They have no tracked production admission path. `FundamentalEvidenceV1` remains EdgarTools-only and EdgarTools remains the exact fundamentals authority.
