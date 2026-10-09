# TECHNICAL STUDY — Biomedicine & Cybersecurity Bases Under Test

ZEPHIRUM / Zephyrum OS — study ZYQL-TR-2026-10-09, published 2026-10-09.
Editorial rules of the house: scientific tone, primary sources by
journal (no personal names), evidence before velocity, numbers
checkable. Every claim below was executed, not projected.

## 1. Molecular base — exact legs (zero QPU)

### 1.1 Real H2, STO-3G minimal basis (`model: h2_sto3g`)

The exact core diagonalizes the published 2-qubit tapered hydrogen
Hamiltonian (source: PRL 116, 023004 (2016), Table I; coefficients
extracted from the published PDF — no personal names cited, per the
owner's editorial rule).

Construction audited 2026-10-09 against the canonical Pauli form
(Z0 = Z(x)I, Z1 = I(x)Z, Z0Z1 = Z(x)Z, YY with -1 corners). Two
defects were caught and fixed by the audit itself: a scrambled
Z-assignment (wrong by +0.005 Ha) and a sign-flipped YY term (wrong
by +0.021 Ha). The final kernel reproduces the canonical ground
state exactly.

Results (dense exact diagonalization, certificates attached):

| bond (A) | exact ground (Ha) |
|----------|-------------------|
| 0.50     | -1.0654           |
| 0.75     | -1.1456           |
| 0.85     | -1.1366           |

Minimum at equilibrium (0.75 A), correct dissociation trend. Decided
question: `ground_state_energy <= -1.10` at bond 0.75 → TRUE,
DECIDED_WITHOUT_EXECUTION, zero QPU.

### 1.2 Hubbard chain (`model: hubbard`) — the DNA/charge-transport bridge

The standard effective model for charge/hole transport in molecular
wires, including the DNA pi-stack — hole transport is the chemistry of
DNA oxidative damage, the entry point of the molecular base into
genomic-biology questions (cancer, viral genomes as future fusion
targets). Full spinful Fock space, exact diagonalization, sites 2..5.

Verified against closed forms (3/3 exact, no tolerance beyond 1e-9):

| case | analytic | kernel |
|------|----------|--------|
| L=2, t=1, U=0 (two electrons, bonding orbital) | -2.000000 | -2.000000 |
| L=2, t=1, U=4 (one electron dominates)         | -1.000000 | -1.000000 |
| L=2, t=1, U=8                                  | -1.000000 | -1.000000 |

Two fermionic-sign defects were caught by the analytic checks and
fixed: an endpoint-included parity mask and a double-counted hopping
bond (effective 2t).

### 1.3 Honest scope (registered, not overclaimed)

Drug discovery at disease scale (DNA-level, viral proteases, tumor
metabolism) needs molecule-scale electronic structure — fault-tolerant
era, or near-term via the fusion targets (Qiskit Nature / PennyLane)
that consume the same .zeph question. What the language guarantees
TODAY: exact certified verdicts for the models it accepts (H2, Hubbard
clusters), and Section 12 refusals for anything beyond. This study
registers the protocols now; it does not claim a cure, a drug, or a
discovery. It claims exactness where exactness holds.

## 2. Molecular base — empirical leg (real QPU)

One lot on ibm_fez (job db4jmrcvf2bc73cunclg), pre-flight gate clean:
the exact verdict was decided with certificate BEFORE submission.

- Exact certified ground (offline): -1.1456 Ha
- QPU estimate (Ry+CX+X analytic prep, 3-basis tomography ZZ/XX/YY,
  2048 shots per basis): -1.0048 Ha
- Deviation: +0.1408 Ha

Verdict (honest): PIPELINE POSITIVE / PRECISION NEUTRAL. The end-to-end
chain (exact decision → ground-state preparation → tomography → signed
receipt) executed correctly; the deviation is dominated by unmitigated
NISQ noise (2-qubit gate + readout; shot error is ~0.03 Ha). The exact
core remains the verifier; the QPU leg is the measured witness, and
its limits are reported, not hidden. Receipt signed with ML-DSA-44
(FIPS 204): results/h2_energy_qpu_study.json.

## 3. Cybersecurity base — head-on battery (zero QPU by design)

Battery results (prototype/test_cyber_battery.py, 4/4 PASS):

1. ML-DSA-44 (FIPS 204): genuine signature → verdict 1; forged
   signature (one flipped byte) → verdict 0; valid signature over the
   wrong message → verdict 0. 3/3.
2. ML-KEM-768 (FIPS 203): encapsulate/decapsulate shared secret
   equality. OK.
3. Section 12: an unknown check (`sha1_collision`) is REFUSED — the
   language cannot be talked into faking a verdict.

The cyber base closes its own loop: the same primitive (ML-DSA-44)
that signs every receipt also DECIDES artifact authenticity inside the
language. On the OS side, the cyber base is declared in
zephyrum_c/src/security.h (PQ-PROTECT posture, trivalent integrity
verdict) and refuses honestly in standby — never a fake OK.

## 4. Operating system under test (same day)

Zephyrum OS kernel test suite: PASS (Bell 20/200, GHZ, Grover,
gate validation, invalid operations rejected, measurement). Kernel
builds clean under gcc -std=c11 -Wall -Wextra.

## 5. Doctrine and limitations

- Exact decisions where the kernel is exact; refusals where it is not.
- QPU usage is a witness, never the decider; every hardware job obeys
  the pre-flight gate and the budget directives (15 s/lot).
- No growth theater in science either: negative/neutral results are
  published as they are (see the +0.1408 Ha deviation above).
- Sources by journal, no personal names (house editorial rule).
