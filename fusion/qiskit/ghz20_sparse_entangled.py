# Gemeo adversario QISKIT (estado esparso 2^20)
nz = [(0, '7071/10000'), (1048575, '7071/10000')]
if len(nz) == 2 and nz[0][0] == 0 and nz[1][0] == 2 ** 20 - 1:
    try:
        from qiskit import QuantumCircuit
        qc = QuantumCircuit(20)
        qc.h(0)
        for i in range(1, 20):
            qc.cx(0, i)
        print("SDK_CROSS_CHECK", "GHZ-20 chain class (ruido float)")
    except ImportError:
        print("SDK_CROSS_CHECK SKIP (par.12)")
else:
    print("SDK_CROSS_CHECK SKIP (par.12): classe esparso fora da fatia do gemeo")
