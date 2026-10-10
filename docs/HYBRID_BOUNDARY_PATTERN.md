# The Hybrid Boundary Pattern

Owner directive 2026-10-10, from the heterogeneous quantum-classical
stack theme (pauta archived per Evidence Before Velocity: no repo, no
primary source; universal literature carries the foundation —
Preskill, Quantum 2, 79 (2018); Peruzzo et al., Nat. Commun. 5, 4213
(2014)).

## Contract

A QPU is not an accelerator that receives a model and returns a faster
answer. It is a specialized witness resource inside a larger
heterogeneous system. The classical side decides which part of the
workload crosses the classical-quantum boundary — and the exact core
decides BEFORE any crossing.

## Four stages (explicit in every certificate)

1. CLASSICAL_PREP — data preparation / transpilation. Never crosses.
2. EXACT_DECISION — core verdict, offline, zero QPU.
3. QPU_WITNESS — crosses the boundary; budget-gated (15 s/lot cap,
   supervisor directive); shots and measurement bases declared.
4. RECEIPT — ML-DSA (FIPS 204) signature closes the loop.

## Routing rules (language and OS, mirrored)

- Pure classical workload: CLASSICAL route, boundary never crossed.
- Witness requested, budget in [1, 15] s: WITNESS route, 4 stages,
  1 crossing, receipt required.
- Witness with zero budget or above the cap: REFUSED.
- Unknown check: REFUSED (Section 12) — the pattern refuses to guess,
  including the fantasy that the QPU is an accelerator.

Batteries: prototype/test_hybrid_boundary.py (5/5 PASS, language);
tests/test_hybrid.c (4/4 PASS, Zephyrum OS).

## Hardware evidence (2026-10-10, ibm_marrakesh)

The pattern executed end to end on real hardware, in order:

1. CLASSICAL_PREP: transpile for the backend.
2. EXACT_DECISION: the language decided before any crossing — Bell
   entangled (True), separable (False), GHZ-3 entangled (True); the
   plan itself validated by `type: hybrid` (15 s accepted, 30 s
   refused by the supervisor cap).
3. QPU_WITNESS: one lot, 4 circuits x 1024 shots, job
   db4qv0imb58s7389iq60. Cost 3 s (234 s -> 237 s of 600 s).
4. RECEIPT: signed ML-DSA-44 (FIPS 204); genuine receipt VERIFIED,
   tampered receipt REFUSED (INVALID SIGNATURE).

Measured (deviations as observed, no mitigation):

| Observable | Measured |
|---|---|
| Bell <ZZ> | 0.9609 |
| Bell <XX> | 0.9336 |
| GHZ-3 P(000)+P(111) | 0.9688 |
| GHZ-3 pair ZZ(0,1) / ZZ(1,2) | 0.9609 / 0.9668 |
| GHZ-3 <XXX> | 0.9160 |
| GHZ-3 fidelity lower bound F >= (P + <XXX>)/2 | 0.9424 |

F > 1/2 witnesses genuine tripartite entanglement (Bourennane et
al., PRL 92, 087902 (2004)).

Audit note (self-correction): the first draft of the script stated an
"ideal +1" for the GHZ <ZZZ> parity. That was wrong: the ideal GHZ
state has <ZZZ> = 0 (outcomes |000> and |111> have opposite 3-bit
parity). The measured 0.0488 is consistent with that. The observable
was corrected to pair correlations and the fidelity bound, computed
from the raw counts with no extra QPU. Errors found by our own audit
are published, not hidden.
