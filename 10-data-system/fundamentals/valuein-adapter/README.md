# P5 Valuein thin adapter

Ownership boundary:

- Capability: P5 historical identity and covered historical fundamentals acquisition.
- Upstream owner: Valuein, with EdgarTools as the exact historical fallback.
- Ownership mode: upstream leaf/whole where the upstream evidence satisfies the existing contracts.
- Upstream already deployed: yes.
- AQ implementation allowed: yes, limited to direct mapping, contract validation, project-specific admission, fixed source precedence, and provenance projection.
- Custom engine required: no.

`aq_valuein_adapter` is deliberately a single direct module. It does not own P1 identity, SEC retrieval, a security master, provider routing, or generic schema translation. Compatible, partial, ambiguous, conflicting, and absent Valuein identity candidates never become authority automatically. Fundamental rows are admitted only when accession, time, metric, value, amendment, and immutable SEC-source provenance satisfy `FundamentalEvidenceV1`; otherwise the existing EdgarTools path remains authoritative.
