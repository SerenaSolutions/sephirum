# QPU Ledger — every quantum-hardware action, documented

This ledger records every use of the IBM Quantum cloud with the owner's
credential. Policy: minimal usage, evidence-grade jobs only, no load
testing, nothing that could stress the free Open Plan. Each job below
also appears automatically in the owner's IBM Quantum Platform dashboard
(Workloads page). Future jobs are tagged `zephirum-validation` for easy
filtering.

| Date (UTC) | Job ID | Backend | Circuit | Shots | Purpose | QPU time |
|---|---|---|---|---|---|---|
| 2026-10-09 00:17 | db4350o4qg6s73c1ivcg | ibm_fez | Bell Φ+ (H, CX), Z and X bases | 2×2048 | Empirical evidence of entanglement: ⟨ZZ⟩=0.8857, ⟨XX⟩=0.9092, consistent with the exact Zephirum verdict (det≠0, decided without execution) | < 1 s (est.) |
| 2026-10-09 00:18 | db435mclf4us73c25180 | ibm_fez | Bell Φ+ (H, CX), Z basis | 512 | End-to-end plugin validation (`--validate-remote-bell`, opt-in): ⟨ZZ⟩=0.8828 | < 1 s (est.) |

## Interpretation (§12 honesty)

The Zephirum core decides on the SPECIFIED state with exact integer
arithmetic and never consults the QPU for the verdict. Cloud runs are
EMPIRICAL EVIDENCE only: they confirm the physical plausibility of the
exact decision. Evidence is never presented as a certificate.

## Credential hygiene

The token lives only as an environment secret; it is never committed,
logged, or printed. The public plugin reads it from `ZEPHIRUM_IBM_TOKEN`
and probes cloud reachability WITHOUT submitting jobs (`--qpu-probe-remote`,
zero QPU time). Job submission is opt-in only (`--validate-remote-bell`).
