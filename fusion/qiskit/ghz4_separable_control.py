#!/usr/bin/env python3
# Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM — ALVO qiskit.
# Familia: entanglement · 16 qubits · separabilidade plena.
# O veredito EXATO e do ZEPHIRUM (Fraction, ZERO execucao).
import hashlib
from fractions import Fraction

AMPS = [Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2'), Fraction('1/2')]
DATA = '1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2|1/2'
OP = '=='

# Familia: entanglement (N qubits) — separabilidade plena recursiva
def _sep(v):
    L = len(v)
    if L == 2: return True
    h = L // 2
    R0, R1 = v[:h], v[h:]
    if any(R0[j]*R1[k] != R0[k]*R1[j]
           for j in range(h) for k in range(j+1, h)):
        return False
    return _sep(R0 if any(R0) else R1)
ent = not _sep(AMPS)
THR = Fraction('1')
v = Fraction(1 if ent else 0)
verdict = {">": v > THR, "<": v < THR, ">=": v >= THR,
           "<=": v <= THR, "==": v == THR}[OP]
print("VERDICT", 1 if verdict else 0)
print("HASH", hashlib.sha256(DATA.encode()).hexdigest())
print("UNITS", 0)
print("QPU_UNITS_BILLED", 0)

try:
    import numpy as np
    from qiskit.quantum_info import Statevector
    sv = Statevector([float(x) for x in AMPS])
    M = np.asarray(sv.data).reshape(2, len(AMPS)//2)
    print("SDK_CROSS_CHECK", "qiskit flatten rank = %d (ruido float em torno do veredito exato)"
          % np.linalg.matrix_rank(M, tol=1e-9))
except ImportError:
    print("SDK_CROSS_CHECK SKIP (§12): qiskit nao instalado neste ambiente — o gateway nunca finge")
except Exception as e:
    print("SDK_CROSS_CHECK FAIL (§12): o SDK nao representa este estado:", e)
