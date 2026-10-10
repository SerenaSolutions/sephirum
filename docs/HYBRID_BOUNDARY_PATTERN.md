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
