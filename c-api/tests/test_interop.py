#!/usr/bin/env python3
"""Interop matrix proof: Zephyron -> OQ3 -> C bridge -> any quantum
backend; and the reverse: their OQ3 exports -> our C gate -> our
kernel. Python here is ONLY the test driver (like sqlite3's harness);
the bridge core is pure C (zyql.c) per the CEO mandate: no Python,
Qiskit, C#, Julia or Rust in the core."""
import ctypes, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/app/conversations/6aad759a5d5b4135aea3780a/zephyrum")
from oq3 import to_openqasm3, from_openqasm3          # noqa: E402
from programs import bell                              # noqa: E402

lib = ctypes.CDLL(os.path.join(HERE, "..", "libzyql.so"))
lib.zyql_gate_circuit.restype = ctypes.c_void_p
lib.zyql_receipt.restype = ctypes.c_char_p
fails = 0

def gate(purpose, src):
    d = lib.zyql_gate_circuit(purpose.encode(), src.encode())
    return json.loads(lib.zyql_receipt(ctypes.c_void_p(d)))

# 1) Zephyron (our language) -> OQ3 (their lingua franca) -> C gate
qc, _ = bell(shots=1)
oq3_src = to_openqasm3(qc.gates_applied, qc.n)
r1 = gate("research entanglement statistics", oq3_src)
ok = r1["STATUS"] == "PASSED_PORTGATE"
print("[OK]  Zephyron -> OQ3 -> ponte C: PASSED_PORTGATE | hash", r1["CIRCUIT_SHA256"][:16]
      if ok else "[FAIL] gate"); fails += 0 if ok else 1

# 2) round-trip: our OQ3 re-enters our kernel and runs (bridge idempotence)
prog, _ = from_openqasm3(oq3_src)
res = prog.measure_all(shots=1024)
ok = res.get("|00>", 0) > 460 and res.get("|11>", 0) > 460 and \
     all(k in ("|00>", "|11>") for k in res)
print("[OK]  round-trip kernel: %s (so 00/11)" % res if ok else "[FAIL] round-trip")
fails += 0 if ok else 1

# 3) THEIR circuit (Qiskit/Cirq/PennyLane-style OQ3 export) -> our C gate
foreign = ('OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[3] q;\nbit[3] c;\n'
           'h q[0];\ncx q[0], q[1];\ncx q[1], q[2];\nc = measure q;\n')
r2 = gate("demonstrate GHZ cross-check", foreign)
ok = r2["STATUS"] == "PASSED_PORTGATE"
print("[OK]  circuito DELES na nossa porta: PASSED_PORTGATE" if ok else "[FAIL]"); fails += 0 if ok else 1

# 4) same circuit, prohibited purpose -> refused before execution
r3 = gate("commit fraud", foreign)
ok = r3["STATUS"] == "REFUSED_BEFORE_COMPUTE" and \
     len(r3["EVIDENCE"]["sha256_refusal_digest"]) == 64
print("[OK]  proposito proibido: REFUSED_BEFORE_COMPUTE com digest SHA-256" if ok
      else "[FAIL]"); fails += 0 if ok else 1

# 5) their circuit also runs in OUR kernel (import path)
prog2, _ = from_openqasm3(foreign)
res2 = prog2.measure_all(shots=1024)
ok = res2.get("|000>", 0) > 460 and res2.get("|111>", 0) > 460
print("[OK]  circuito deles roda no kernel ZYQL: %s" % res2 if ok else "[FAIL] import")
fails += 0 if ok else 1

print("\n%s (5/5)" % ("INTEROP OK" if not fails else "INTEROP FALHOU"))
sys.exit(1 if fails else 0)
