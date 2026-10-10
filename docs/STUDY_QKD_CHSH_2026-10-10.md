# TECHNICAL STUDY — QKD Witness via CHSH (cybersecurity base)

ZEPHIRUM / Zephyrum OS — study ZYQL-TR-2026-10-10, started 2026-10-10.
Editorial rules of the house: scientific tone, primary sources by
journal (no personal names), evidence before velocity, numbers
checkable. Labels: every claim below is FACT (executed), INFERENCE or
PROTOTYPE status, per the project's epistemic standard.

## 1. Domain and motivation

Cybersecurity: entanglement-based quantum key distribution (QKD). The
CHSH game is the operational core of device-insecurity testing for
entanglement: a channel whose correlators violate the classical bound
(S > 2) carries entanglement that no local classical strategy can
counterfeit (Bell's theorem, Phys. Rev. Lett. 115, 250801 (2015) big
loophole-free test; CHSH original: Phys. Lett. A 37, 95 (1975)).

The question the language must answer:

    ASK: is this entanglement channel QKD-grade? (S > 2)

## 2. Offline legs (executed, certificates attached, zero QPU)

### 2.1 Classical bound — arithmetic FACT

MODEL: `exact`, check: `chsh_bound`, mode: `classical`. The kernel
enumerates ALL 16 deterministic local strategies (A0, A1, B0, B1 in
{-1,+1}) and decides `classical_max <= 2` — TRUE,
DECIDED_WITHOUT_EXECUTION. No statistics, no sampling: the bound is a
finite arithmetic fact.

### 2.2 Tsirelson ceiling — exact to 28 digits, disclosed truncation

mode: `tsirelson` decides `tsirelson > 2` — TRUE, S = 2*sqrt(2) =
2.8284271247461903... The irrationality of sqrt(2) is disclosed (§12):
Decimal context of 28 significant digits, never faked exact.

### 2.3 Witness discipline — the hardware never judges

mode: `witness` computes the correlators E(a,b) and S EXACTLY in
Fractions over DECLARED counts ("same,diff" per setting) and answers
the threshold question. Provenance is the operator's receipt; the
kernel is exact over declared data (same discipline as legal deadline
counting). Negative control executed: uniform counts give S = 0 and
the language answers FALSE — an honest refusal to certify.
Structural refusals: malformed counts are explicit errors (3/3).

Battery: `test_chsh_qkd.py` — 5 legs, PASS. Conformance v0.3 now runs
21 batteries: PASS.

## 3. Hardware leg (pre-registered protocol, ibm_kingston)

Runner: `qpu_chsh_qkd.py`. Settings on |Phi+>: a0 = 0 (Z), a1 = pi/2
(X), b0 = pi/4, b1 = -pi/4. Circuit design validated locally by exact
statevector simulation: S = 2.828427, error 1.33e-15 against the
Tsirelson ceiling (PROTOTYPE validation, labeled simulated).

Protocol (house discipline, unchanged):

1. Pre-flight gate: offline certificates (2.1, 2.2) asserted BEFORE
   any submission; the QPU is authorized as WITNESS only.
2. Single lot, ceiling 15 s, 2048 shots per setting, budget floor
   120 s, usage recorded before/after.
3. Counts fed into `check: chsh_bound, mode: witness` — the LANGUAGE
   decides `S > 2` over the QPU's raw counts.
4. Receipt signed with ML-DSA-44 (FIPS 204), first post-quantum
   signature of the study; stored in `results/chsh_qkd_kingston.json`.

## 5. Hardware result (executed 2026-10-10, ibm_kingston, job
db50dg84qg6s73c2qatg)

2048 shots per setting, single lot. Receipted counts (same,diff):
a0b0 1397,651 · a0b1 1433,615 · a1b0 1332,716 · a1b1 801,1247.

LANGUAGE VERDICT over the QPU counts: S = 1.2822 (exact Fraction
over the counts) — `S > 2` answered FALSE. DECIDED_WITHOUT_EXECUTION
over declared data; certificate hash in the receipt.

HONEST READING: no CHSH violation was certified on this lot. All
four correlators are attenuated to ~50% of the ideal pattern (signs
match +,+,+,-; ideal S = 2*sqrt(2)). The attenuation is consistent
with hardware noise on the transpiled pair (no directed-pair
selection, no error mitigation in this first lot). The language
REFUSED to certify the channel as QKD-grade — exactly the §12
discipline the study set out to demonstrate: the hardware supplied
counts, the language decided, and a negative verdict is published as
promptly as a positive one.

Receipt: results/chsh_qkd_kingston.json, signed ML-DSA-44 (FIPS
204), signature verified. Follow-up lot (optional, pre-registered):
directed best pair by CX error + readout mitigation, same ceiling.

STATUS: hardware leg EXECUTED. First lot: no violation certified
(honest refusal).

## 4. Thesis position

This is the pattern the language sells to the quantum-security
community: the security BOUND is decided offline with a certificate
(classical max = 2, arithmetic); the hardware supplies only raw
witness counts; the language, never the QPU, emits the verdict. Same
discipline as the Bell/GHZ/cluster witnesses already receipted on
kingston — now aimed at a deployed application family (QKD).
