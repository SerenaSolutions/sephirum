"""ZEPHIRUM QUANTUM PLUGIN — prova antes de executar.

Plug-in do algoritmo Zephirum para o mundo quântico: decisão EXATA
de emaranhamento (Fraction, critério de Schmidt) com certificado
verificável, ZERO unidades QPU, e SDKs (Qiskit/Cirq) como gêmeos
adversariais OPCIONAIS de contraprova float.
"""
from .core import gateway, verify, certify, decide, parse_nexa
from .standby import qpu_probe, standby_receipt

__version__ = "0.4.0"
__all__ = ["gateway", "verify", "certify", "decide", "parse_nexa", "qpu_probe", "standby_receipt"]
