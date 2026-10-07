#!/usr/bin/env python3
"""
ZEPHIRUM × SDK QUÂNTICO — interoperabilidade (Fase de conjunto).
=====================================================================

A arquitetura prevê o par antitético TRABALHANDO JUNTO:

  ZEPHIRUM: pergunta -> escada -> ANALYTIC (critério de Schmidt exato)
            -> resposta CERTIFICADA com ZERO unidades de execução.
  SDK (Qiskit/Cirq/PennyLane): executa o que a escada eliminou —
            statevector, matriz densidade, autovalores de ρ_A —
            como gêmeo adversarial numérico da decisão certificada.

O SDK NÃO é mecanismo decisório no ZEPHIRUM (regra da Fase 3): ele é
validação independente (e, no futuro, backend do residual de execução
quântica genuína, quando houver hardware).

Registro honesto (§12): cada adapter declara disponibilidade real —
import falhou => ModelNotAvailable explícito, nunca fingimento.
"""
import sys

from nexa_core import NCA, parse_nexa


class ModelNotAvailable(Exception):
    pass


# ------------------------------------------------------------- adapters
def try_import(name):
    try:
        return __import__(name)
    except ImportError:
        return None


class QiskitBackend:
    """Adapter Qiskit: statevector + concurrence + autovalores de ρ_A."""
    name = "qiskit"

    def __init__(self):
        qi = try_import("qiskit")
        if qi is None or not hasattr(qi, "quantum_info"):
            raise ModelNotAvailable("qiskit not installed")
        self.qi = qi.quantum_info

    def concurrence(self, amps):
        sv = self.qi.Statevector(amps)
        return float(self.qi.concurrence(sv))

    def rho_a_eigenvalues(self, amps):
        sv = self.qi.Statevector(amps)
        rho = self.qi.partial_trace(sv, [1])       # traço sobre o qubit 2
        import numpy as np
        return sorted(np.linalg.eigvalsh(rho.data).real, reverse=True)


class CirqBackend:
    name = "cirq"

    def __init__(self):
        raise ModelNotAvailable("cirq not installed in this sandbox "
                                "(registrado, não instalado — §12)")


class PennyLaneBackend:
    name = "pennylane"

    def __init__(self):
        raise ModelNotAvailable("pennylane (Xanadu) not installed in "
                                "this sandbox (registrado, §12)")


BACKENDS = {"qiskit": QiskitBackend, "cirq": CirqBackend,
            "pennylane": PennyLaneBackend}


def get_backend(name="qiskit"):
    if name not in BACKENDS:
        raise ValueError("unknown SDK %r (registro: %s)"
                         % (name, ", ".join(BACKENDS)))
    return BACKENDS[name]()


# ----------------------------------------------------- pergunta ZEPHIRUM
def zephirum_decide(state_csv, question, i="q"):
    """Pergunta de emaranhado via ZEPHIRUM: decisão certificada,
    verificada, ZERO unidades de execução."""
    src = ("ASK:\n    question: %s\nMODEL:\n    type: entanglement\n"
           "    state: %s\n" % (question, state_csv))
    blocks = parse_nexa(src)
    res = NCA(blocks, "q%s" % i).compile()
    return res


def main():
    print(__doc__)


if __name__ == "__main__":
    main()
