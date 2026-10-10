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
