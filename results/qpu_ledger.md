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
| 2026-10-09 00:24 | db438aklf4us73c2547g | ibm_fez | Separable control \|+0⟩ (H only, no CX), Z and X bases | 2×512 | Negative control: exact verdict 0 (det=0), hardware shows ⟨ZZ⟩=0.0508, ⟨XX⟩=-0.0742 — no correlation, consistent with separable | < 1 s (est.) |
| 2026-10-09 00:30 | db43b3imb58s7388js10 | ibm_fez | QCNN source data: 1D cluster state cell CZ\|++⟩ (Cong et al. 2019, arXiv:1810.03787), 3 bases | 3×512 | Paper-vs-Zephirum confrontation: exact verdict 1 (det=-0.5); stabilizers ⟨XZ⟩=0.918, ⟨ZX⟩=0.844, ⟨ZZ⟩=0.012 — cluster signature confirmed | < 1 s (est.) |
| 2026-10-09 00:38 | db43f2kvf2bc73cu0ts0 | ibm_fez | FUSION run: Zephirum-emitted OpenQASM 3 (GHZ prep) absorbed by Qiskit, + separable 3q control | 2×512 | GHZ exact verdict 1: pair stabilizers ⟨ZZI⟩=⟨IZZ⟩=0.965, population 000/111 = 97.9% (⟨ZZZ⟩=0 is correct GHZ+ physics, label fixed in receipt); separable control ⟨ZZZ⟩=-0.09 ≈ 0, verdict 0 | < 1 s (est.) |
| 2026-10-09 00:45 | db43i4qmb58s7388k3mg | ibm_fez | GHZ ladder rungs 4 and 6 via the fusion chain (.zeph → exact verdict → OpenQASM 3 → qasm3.loads → QPU) | 2×512 | GHZ4 exact verdict 1: 95.1% population {0000,1111}; GHZ6 verdict 1: 91.8% {000000,111111} — ladder scaling confirmed | < 2 s (est.) |
| 2026-10-09 00:45 | (see receipt) | ibm_fez | Separable 4q control (exact-vector prepare_state) after emitter fix (qubit[log2(n)] bug, declared and corrected) | 512 | 16 distinct uniform outcomes, parity correlator −0.008 ≈ 0 — verdict 0 confirmed; first run invalid (empty register), replaced honestly | < 1 s (est.) |

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
| 2026-10-09 00:56 | (see receipt) | ibm_fez | GHZ-20 via SPARSE representation (2-entry support decided exactly offline; emitted ry+cx chain executed) | 512 | exact verdict 1; ideal population 39.7% (unmitigated 19-CX routed chain) with 72.3% of shots within Hamming distance 2 of the poles — long-range GHZ structure through decoherence; honest physical dilution recorded | < 1 s (est.) |
