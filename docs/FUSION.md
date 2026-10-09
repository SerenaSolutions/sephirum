# The Fusion: Zephirum Emits, the Quantum World Absorbs

Owner's direction (2026-10-08): make Zephirum part of the Qiskit family
*within this project* — the decision stays with the exact core; the
execution artifacts speak the international standards, so any system
absorbs Zephirum-decided questions easily.

## The contract of the fusion

1. The **verdict is always Zephirum's**: exact rational arithmetic,
   decided without execution, certified (SHA-256 receipt).
2. The transpiler **emits** the same decided question into standard
   targets. Emission is never a substitute for the decision.
3. The SDK (Qiskit, Cirq, ...) is the **adversarial twin**: when
   installed it re-walks the eliminated path in floating point and
   reports the noise around the exact verdict. Absent → SKIP §12.
4. Hardware evidence is empirical (§12); certificates come only from
   the exact core.

## Emitted targets (per .zeph question)

| Target | Status | Notes |
|---|---|---|
| Python (exact, Fraction) | stable | runs standalone |
| Qiskit (adversarial twin) | stable | `fusion/qiskit/*.py`, executed in CI-style checks |
| OpenQASM 3 | stable | `fusion/openqasm/*.qasm`; GHZ-class prep circuits emitted (any N — including sparse(20) GHZ-20 validated on ibm_fez); general vectors carried as exact Fraction comments with prep delegated to the absorbing SDK (§12) |
| Cirq | 2-qubit slice | 3-qubit not covered yet (declared, never faked) |
| C / Java / C# / Lisp | arithmetic families | entanglement 3q declared out of slice |

Fusion artifacts are generated from `examples/*.zeph` by
`prototype/zephirum_transpiler_multi.transpile()` and are committed so
GitHub's language bar reflects the fusion honestly.

## Hardware-validated fusion chain

Zephirum `.zeph` → exact C verdict → emitted `OpenQASM 3` →
`qiskit.qasm3.loads()` → ibm_fez execution. Receipts:
`results/ghz3_fusion_ibm_fez.json`, `results/qpu_ledger.md`.

## Roadmap (owner's queue)

- **Xanadu / PennyLane** — photonic target: emit PennyLane programs
  for decided questions; test against Xanadu's ecosystem when the
  owner opens that door. Not started; no code pretends otherwise.
- OpenQASM general state-prep emitter (beyond Bell/GHZ classes).
- 4-qubit cluster chain (full 1D cluster from Cong et al. 2019).
- Sparse format generalization beyond GHZ-class (W-class prep emitters).
