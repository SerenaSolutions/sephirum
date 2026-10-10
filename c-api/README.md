# ZYQL C API — the bridge

One C99 file (`zyql.c`), one header (`zyql.h`), zero dependencies — the
SQLite pattern. Qiskit opened beyond Python through a C API (2026); ZYQL
does the same for verified decisions: the C API is the bridge, and every
language plugs into it.

## What it does
- PORTGATE: signed lexical purpose gate — 7 prohibited classes refused
  BEFORE compute, refusal is a certificate (purpose VERBATIM + SHA-256).
- Families: `kepler3` (Kepler III closed form), `expression` (constant
  fold). Structural errors fail explicitly, never silently.
- Receipts: JSON certificates with the same field names as the Python
  core.

## Parity (evidence, not claim)
`tests/parity_nexa.py` proves the C core and `prototype/nexa_core.py`
produce the SAME verdict, the SAME ANSWER, the SAME INPUT_HASH and the
SAME sha256_refusal_digest for identical programs (3/3 OK).
`tests/test_c_api.c`: ZYGUARD battery 12/12 OK (incl. NIST SHA-256 vector
and injection-is-inert-string wall).

## Build
    cc -std=c99 -O2 -c zyql.c -o zyql.o
    cc -std=c99 -O2 -fPIC -shared zyql.c -o libzyql.so -lm
    cc -std=c99 -O2 tests/test_c_api.c zyql.c -o test_c_api -lm && ./test_c_api
    python3 tests/parity_nexa.py

## v0.2 — the bridge: quantum languages + language models
- `zyql_gate_circuit(purpose, openqasm3_src)`: ANY quantum language that
  can emit text (OpenQASM 3, QIR/Q# output, Silq/Cirq exports) passes the
  SAME purpose gate BEFORE any backend executes it. ZYQL gates and never
  executes. Refusal digest is byte-identical to the Python core (parity
  re-verified for the bridge).
- `zyql_verify_receipt(receipt_json)`: language models / agents verify a
  quoted receipt in pure C — 1 valid, 0 tampered, -1 malformed.
- Battery: tests/test_bridge.c — 5/5 OK (Bell passes, fraud refused
  before execution, original receipt valid, tampered receipt invalid,
  malformed rejected).

## Bindings
- C: native (zyql.h).
- C++: `bindings/zyql.hpp` (RAII) — tested (tests/test_cpp.cpp).
- Python: `bindings/zyql_python.py` (ctypes) — parity-proven.
- C#: `bindings/Zyql.cs` (P/Invoke) — provided, NOT yet executed here.

## Honest scope
v0.1.0 implements a subset of the nexa_core.py ladder (kepler3,
expression). The full ladder (entanglement, molecular, crypto, hybrid
...) remains Python-side; the C core grows rung by rung, each rung
landing only with a parity test. The purpose string is DATA, never
executed: the language has no execution primitive at all.

## v0.3 — interop with the quantum ecosystem (proven 5/5)
`tests/test_interop.py` proves both directions of the bridge:
1. Zephyron -> OpenQASM 3 -> C gate -> ANY backend that ingests OQ3
   (Qiskit, Cirq, PennyLane, Braket); QIR is gateable the same way —
   the gate takes text, so every quantum language plugs in.
2. Their OQ3 exports -> our C gate -> our kernel (round-trip: Bell
   511/513, GHZ 495/529 — only the expected states).
Python appears only as the TEST DRIVER (like sqlite3's harness); the
bridge core is pure C — no Python, Qiskit, C#, Julia or Rust inside
`zyql.c` (CEO mandate, 2026-10-10). Next rung: the Zephyron->OQ3
transpiler itself ported to C.
