# APPLICATION FAMILIES — Biomedicine & Cybersecurity Bases

Owner directive (2026-10-09, IBM window): leave inside the language and
the OS the base definitions for (1) drug discovery in biomedicine and
(2) cybersecurity. Executed as two exact MODEL families — both decide
OFFLINE, with certificates, zero QPU in the decision path.

## 1. `molecular` — the biomedicine base

Drug discovery is, at bottom, asking exact questions about quantum
many-body ground states — molecular energies, reaction thresholds,
binding verdicts. The family seed is live in the exact core today:

```zeph
ASK:
    question: ground_state_energy <= -0.7
MODEL:
    type: molecular
    model: heisenberg
    sites: 2
    coupling: 1
```

- Kernel: `EXACT_DIAGONALIZATION` — dense exact diagonalization on the
  full Hilbert space (2..12 sites, up to 4096-dim), no approximation,
  no sampling, decided with certificate.
- Verified: the 2-site dimer (the H2 analog) returns exactly -3J/4 =
  -0.750000, matching the analytic singlet energy; a 4-site open chain
  returns -1.616025.
- Honest scope (Evidence Before Velocity): this kernel decides small
  active spaces exactly. Molecule-scale drug discovery needs the
  fault-tolerant era. The scaling path is fusion: the same .zeph
  question flows to Qiskit Nature / PennyLane (third fusion target),
  which consume geometry/basis and scale under their own solvers.
  What the language guarantees TODAY: exact verdicts for the models it
  accepts, and a refusal (Section 12) for anything beyond the kernel.

## 2. `crypto` — the cybersecurity base

The cyber question that matters first: *is this artifact authentic?*
The language answers it exactly, against FIPS 204 (ML-DSA-44), on
classical hardware — zero QPU:

```zeph
ASK:
    question: signature_valid == 1
MODEL:
    type: crypto
    check: ml_dsa_verify
    public_key: <b64 ML-DSA-44 public key>
    message: <plain text>
    signature: <b64 ML-DSA-44 signature>
```

- Kernel: `ML_DSA_VERIFY` — genuine signatures decide 1; forged ones
  (single flipped byte) decide 0. Verified 2/2.
- This is the same primitive that signs every ZEPHIRUM receipt
  (`pq_receipt.py`), so the cyber base closes the loop: the language
  that emits signed receipts can also *decide* whether a receipt is
  authentic.
- OS counterpart: the Zephyrum OS cyber base (PQ-PROTECT measured boot,
  ML-DSA-verified kernel/modules, verdict path through qdev) — see
  `docs/CYBER_BASE.md` in the OS repository.

## Doctrine (unchanged)

Both families obey the standing rules: the kernel decides, refusals
travel untouched (Section 12), certificates seal every verdict, and
no claim is made beyond what executes. Health and security claims
especially: evidence before velocity, always.
