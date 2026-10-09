#!/usr/bin/env python3
# Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM — ALVO qiskit.
# Família: entanglement · 3 qubits · separabilidade plena.
# O veredito EXATO é do ZEPHIRUM (Fraction, ZERO execução);
# o SDK é o gêmeo adversarial; ausente => SKIP §12.
import hashlib
from fractions import Fraction

AMPS = [Fraction('1/2'), Fraction('1/2'), Fraction('0'), Fraction('0'), Fraction('1/2'), Fraction('1/2'), Fraction('0'), Fraction('0')]
DATA = '1/2|1/2|0|0|1/2|1/2|0|0'
OP = '=='

# Família: entanglement (3 qubits) · pergunta: entangled == 1
# TOTALMENTE SEPARÁVEL <=> posto 1 do achatamento (q0) E det2=0
R0, R1 = AMPS[:4], AMPS[4:]
rank1 = all(R0[j]*R1[k] == R0[k]*R1[j]
            for j in range(4) for k in range(j+1, 4))
if rank1:
    phi = R0 if any(R0) else R1
    ent = (phi[0]*phi[3] - phi[1]*phi[2]) != 0
else:
    ent = True
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
    M = np.asarray(sv.data).reshape(2, 4)
    print("SDK_CROSS_CHECK", "qiskit flatten rank = %d (ruído float em torno do veredito exato)"
          % np.linalg.matrix_rank(M, tol=1e-9))
except ImportError:
    print("SDK_CROSS_CHECK SKIP (§12): qiskit não instalado neste ambiente — o gateway nunca finge")
except Exception as e:
    print("SDK_CROSS_CHECK FAIL (§12): o SDK não representa este estado:", e)
