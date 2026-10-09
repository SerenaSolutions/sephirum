# The QCNN Bridge: Necessity Compilation Applied to Quantum Machine Learning

*Zephirum × IBM Quantum hardware × Quantum Convolutional Neural Networks*

## The gap in the QCNN literature

Quantum Convolutional Neural Networks (Cong, Choi & Lukin, *Quantum
convolutional neural networks*, Nature Physics 15, 1276–1283, 2019)
inherit a hierarchical convolve/pool structure from classical CNNs and
are promising for quantum phase recognition and quantum data
classification. The known blockers are well documented: barren plateaus
in training landscapes (McClean et al., Nature Communications 9, 4812,
2018), data-encoding costs, measurement overhead, and an unclear
advantage over strong classical methods — classical ML is provably
efficient for many learning tasks on quantum states and measurements
(Huang, Kueng & Preskill, 2022).

The field optimizes the circuit *before* asking the prior question:
is this training run necessary at all?

## The Zephirum gate (pre-flight, exact, classical)

Zephirum decides, with exact integer/rational arithmetic and a
verifiable SHA-256 certificate, whether the input state of a QML
pipeline is entangled (Schmidt determinant ≠ 0) or separable
(determinant = 0) — zero QPU units, before any training shot is spent.

The routing rule is derived from the definition, not from heuristics:

1. `entangled == 0` — the input is a product state. Its measurement
   statistics factor into local marginals and are classically
   simulable by construction; a QCNN gains nothing provable here.
   Route classical. Training on quantum hardware is unnecessary.
2. `entangled == 1` — genuine quantum correlations exist in the data.
   QCNN treatment is a candidate (quantum phase recognition,
   many-body classification). The training question remains open —
   but now it is asked honestly, with the necessity established.

This is *necessity compilation* applied to QML: the decision layer
runs before execution, exactly, on commodity hardware.

## Hardware evidence (IBM Quantum, ibm_fez — Heron 156 qubits)

The exact verdicts above were confronted with reality in a paired
control experiment on a real QPU (free Open Plan, each run < 1 s):

| Gate case | Exact C verdict | QPU evidence (empirical) |
|---|---|---|
| Bell Φ+ input (`examples/qcnn_gate_entangled.zeph`) | 1 — entangled | ⟨ZZ⟩ = 0.886, ⟨XX⟩ = 0.909 (correlation in both bases) |
| Separable \|+0⟩ input (`examples/qcnn_gate_separable.zeph`) | 0 — separable | ⟨ZZ⟩ = 0.051, ⟨XX⟩ = −0.074 (no correlation) |
| QCNN paper source cell: 1D cluster state CZ\|++⟩ (`examples/qcnn_cluster_state.zeph`) | 1 — entangled (det = −0.5) | stabilizers ⟨XZ⟩ = 0.918, ⟨ZX⟩ = 0.844; ⟨ZZ⟩ = 0.012 — the cluster signature, distinct from both Bell and separable |

A product state cannot show both correlations near 1; a Bell state
cannot show both near 0. The hardware agrees with the exact decision
in both directions. Receipts: `results/bell_phi_plus_ibm_fez.json`,
`results/qcnn_cluster_ibm_fez.json`,
`results/separable_control_ibm_fez.json`; full usage ledger:
`results/qpu_ledger.md`.

## §12 honesty

The QPU evidence is empirical, not a certificate. The certificate is
the SHA-256 receipt produced by the exact C core (`zref`), decided
without execution. The two layers are never conflated.

## Reproduce

```
prototype/verifier_indep/zref examples/qcnn_gate_entangled.zeph   # VERDICT 1
prototype/verifier_indep/zref examples/qcnn_gate_separable.zeph  # VERDICT 0
```
