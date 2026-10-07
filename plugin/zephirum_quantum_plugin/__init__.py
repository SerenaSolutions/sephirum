"""ZEPHIRUM QUANTUM PLUGIN — prova antes de executar.

Plug-in do algoritmo Zephirum para o mundo quântico: decisão EXATA
de emaranhamento (Fraction, critério de Schmidt) com certificado
verificável, ZERO unidades QPU, e SDKs (Qiskit/Cirq) como gêmeos
adversariais OPCIONAIS de contraprova float.
"""
from .core import gateway, verify, certify, decide, parse_nexa
from .standby import qpu_probe, standby_receipt
from . import pqprotect
from .pqprotect import pq_protect, pq_verify, self_seal, verify_seal

__version__ = "0.5.0"
__all__ = ["gateway", "verify", "certify", "decide", "parse_nexa", "qpu_probe", "standby_receipt", "pqprotect", "pq_protect", "pq_verify", "self_seal", "verify_seal"]
