# Zephirum Quantum Plugin

The **Zephirum algorithm** plugin for the quantum world — v0.5.0: THE
DECISION IS ZEPHIRUM BYTECODE (Python is only the emitter/interpreter;
the zvm C runtime contains no Python) — born from the house's first
artifact (the autonomous verifier transpiled to Python/C/Java):
**prove before executing**.

It decides entanglement of 2-qubit pure states with **exact
arithmetic** (Fraction — the closed Schmidt criterion), issues a
**verifiable certificate** (INPUT_HASH + CERT_HASH seal in SHA-256,
plus the post-quantum PQ-PROTECT signature), charges **zero QPU
units**, and treats the SDKs (Qiskit/Cirq) as **optional adversarial
twins** for float counter-evidence — never as the source of the
verdict.

The grounding is universal literature: Wootters concurrence (PRL 80,
2245, 1998), the Schmidt decomposition (1906), Nielsen & Chuang
(ch. 2). No individual social-media authors.

## Install

```
pip install .
# with the adversarial twin:
pip install .[qiskit]
```

## Usage

```
$ zephirum-q examples/bell_phi_plus.zeph --sdk qiskit
STATUS      DECIDED_WITHOUT_EXECUTION
VERDICT     1
CONCURRENCE 1 (exact)
QPU UNITS   0 (billed)
INPUT_HASH  ...
CERT_HASH   ...
INDEP CHECK decision reproduced, seal and post-quantum signature match
SDK CROSS   qiskit float concurrence C = 0.99999... (noise around the exact value)
```

Python API:

```python
from zephirum_quantum_plugin import gateway

receipt, ok = gateway(open("examples/separable.zeph").read(),
                      sdk="cirq")
```

## PQ-PROTECT (post-quantum self-protection)

Hash-based Lamport signature (FIPS 205 family) on the certificate,
SHA-256 self-integrity seal of the plugin's own files, pure
encapsulated core (no network/I/O/process) — verified in battery 20
with active blockades and tampering caught in TWO independent layers.

## Honesty (§12)

1. Zero QPU units: the analytic criterion ELIMINATES the SDK path
   (state vector + self-decomposition, 8 units).
2. The SDK float is noise around the exact value — the certificate
   is the stable verdict.
3. Missing SDK = `SKIP (§12)` receipt, never a hidden error.
4. Family outside the plugin = refusal with a reason, no routing.
5. The certificate is INDEPENDENTLY verifiable: `verify()`
   re-derives the decision and checks the seal — tampering is caught
   by CERT_HASH.
