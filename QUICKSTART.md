# QUICKSTART — your first exact verdict in five minutes

ZYQL is an exact, trivalent decision language: every question ends in `1` (proven
true), `0` (proven false) or `UNKNOWN` (cannot be decided from the declared
data) — and when the engine refuses, it names the violated condition (Section 12
honesty). Decisions are made by closed mathematical criteria over exact
arithmetic, with zero QPU in the decision path; hardware runs, when requested,
are evidence with receipts, never the certificate itself.

Everything below was executed from this repository as shipped — no command or
output is invented.

## 1. Install

Two layers, both dependency-free:

```bash
# Layer 1 — the Python reference (pure stdlib, Python 3)
./install.sh
export PATH="$PATH:$HOME/zephirum/bin"     # if .local/bin is not on PATH

# Layer 2 — the independent C verifier (zref)
gcc -O2 -std=gnu11 prototype/verifier_indep/zref.c -o zref
```

Note: use `-std=gnu11`, not strict `-std=c11` — the verifier uses `strtok_r`,
which is POSIX, not ISO C, and strict C11 hides its declaration.

## 2. Walkthrough — dense two-qubit Bell state (C verifier)

Ask whether Φ⁺ = (|00⟩ + |11⟩)/√2 is entangled:

```bash
cat > bell.zeph << 'EOF'
ASK:
    question: entangled == 1
CONTRACT:
    absolute_error: 0
MODEL:
    type: entanglement
    state: 0.5,0,0,0.5
EOF
./zref bell.zeph
```

Real output:

```
VERDICT 1
HASH b8c6435d3db46d6cb58b23be024452fcb32806e5861620175730550b757ba080
UNITS 0
QPU_UNITS_BILLED 0
ENGINE zref-c11 (exato, §12 muros declarados)
```

The decision is the Schmidt determinant criterion — closed form, exact, no
simulation. The separable control `state: 0.5,0.5,0.5,0.5` answers `VERDICT 0`
with its own certificate hash.

## 3. Walkthrough — sparse 20-qubit GHZ chain

`examples/ghz20_sparse_entangled.zeph` declares the 2²⁰ space but enumerates
only its 2-entry support:

```bash
./zref examples/ghz20_sparse_entangled.zeph
```

Real output:

```
VERDICT 1
HASH 28b0eb18af52eb3ad163d3a3de8ce07cf5de338e098285b715501bc93bbbbcc0
UNITS 0
QPU_UNITS_BILLED 0
ENGINE zref-c11 (exato, §12 muros declarados)
```

2²⁰ ≈ 1.05 million amplitudes are never materialized: the sparse support is
decided exactly, offline, with zero QPU units.

## 4. Walkthrough — a refusal, Section 12 style

A language you can trust is a language that refuses. Put an index outside the
declared space:

```bash
printf 'ASK:\n    question: entangled == 1\nCONTRACT:\n    absolute_error: 0\nMODEL:\n    type: entanglement\n    state: sparse(20) 0:0.5, 1048576:0.5\n' > bad.zeph
./zref bad.zeph
```

Real output (stderr, non-zero exit code):

```
RECUSA (§12): indice alem do espaco 2^N declarado
```

Exit codes: `0` accompanies a decided verdict; every refusal exits non-zero with
the violated condition printed on stderr.

## 5. The two layers — declared walls vs. arbitrary precision

The C verifier declares its walls (amplitude ≤ 10⁴ and friends). The Python
reference carries arbitrary precision. The canonical Bell example with 17
decimals shows the split honestly:

```bash
./zref examples/entangled.zeph        # REFUSED: amplitude beyond the declared C wall
qsim-gateway examples/entangled.zeph  # decides it exactly
```

Real `qsim-gateway` output:

```
Q-SIM GATEWAY — prove before you pay
status                : DECIDED_WITHOUT_EXECUTION
verdict               : 1
independent_check     : (True, 'ok: Schmidt criterion cross-checked (det(MMᵗ)=det(M)²)')
qpu_units_billed      : 0
GATEWAY: decision delivered with ZERO QPU units billed
```

## 6. The signature demo — computation is wrong at any length

```bash
zephirum-decide examples/geometric.zeph
```

Real output:

```
NAIVE 12-term truncation: 4095/2048 < 2 -> TRUE   (wrong at ANY length)

ZEPHIRUM: sum = a/(1-r) = 2 exactly
VERDICT: FALSE
CERTIFIED UNITS: 2 (budget 2) — the certificate is the answer
```

This is the whole thesis of the language in one run: a truncated computation
gives the wrong answer at every finite length, while the closed criterion
decides it exactly, with units budgeted.

## 7. Question families → example files

| Family | Example in this repo |
|---|---|
| `threshold_sum` | `prototype/example.zeph` |
| `geometric_inf` | `examples/geometric.zeph` |
| `entanglement` (dense) | `examples/ghz3_entangled.zeph`, `examples/ghz4_entangled.zeph`, `examples/qcnn_gate_entangled.zeph` |
| `entanglement` (sparse) | `examples/ghz20_sparse_entangled.zeph`, `examples/ghz6_entangled.zeph` |
| `mean_partial` | reference implementation: `prototype/nexa_core.py` (`_mean_partial`) |

## 8. Where to go next

1. `INSTALL.md` — the full local install, including the optional Qiskit
   cross-check (`qsim-gateway prog.zeph --sdk qiskit`).
2. `docs/CHARTER.md` — the language charter and the Section 12 policy.
3. `prototype/conformance_v03.py` — the executable standard: nine batteries,
   pure stdlib, no cloud, no LLM.
