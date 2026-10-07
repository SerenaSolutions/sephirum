"""ZEPHIRUM QUANTUM PLUGIN — prova antes de executar.

Plug-in do algoritmo Zephirum para o mundo quântico: decisão EXATA
de emaranhamento (Fraction, critério de Schmidt) com certificado
verificável, ZERO unidades QPU, e SDKs (Qiskit/Cirq) como gêmeos
adversariais OPCIONAIS de contraprova float.
"""
from .core import gateway, verify, certify, decide, parse_nexa

__version__ = "0.3.0"
__all__ = ["gateway", "verify", "certify", "decide", "parse_nexa"]
