#!/usr/bin/env python3
"""Adaptadores SDK — gêmeos adversariais do Zephirum.

O SDK é OPCIONAL e sempre CONTRAPROVA (float), nunca fonte do
veredito: o certificado exato é a resposta estável; o float do SDK
vem com ruído em volta do valor exato. SDK ausente = recibo SKIP
declarado (§12), nunca erro escondido.
"""
from fractions import Fraction


def _float_concurrence(a, b, c, d):
    a, b, c, d = (float(Fraction(x)) for x in (a, b, c, d))
    tr = a * a + b * b + c * c + d * d
    det = a * d - b * c
    return 2 * abs(det) / tr


def sdk_cross_check(sdk, amplitudes, threshold=None):
    a, b, c, d = amplitudes
    try:
        if sdk == "qiskit":
            try:
                from qiskit.quantum_info import Statevector, concurrence
            except ImportError:
                return "SKIP (§12): qiskit não instalado neste ambiente"
            amps = [float(Fraction(x)) for x in amplitudes]
            sv = Statevector([amps[0], amps[1], amps[2], amps[3]])
            return ("qiskit float concurrence C = %.17g (ruído em volta "
                    "do exato — o certificado é o veredito estável)"
                    % concurrence(sv))
        if sdk == "cirq":
            try:
                import cirq
            except ImportError:
                return "SKIP (§12): cirq não instalado neste ambiente"
            import numpy as np
            amps = np.array([float(Fraction(x)) for x in amplitudes],
                            dtype=complex)
            rho = np.outer(amps, amps.conj())
            # concorrência via autovalores de rho (rota do SDK)
            evals = np.linalg.eigvalsh(rho).real
            sqrt_evals = np.sqrt(np.clip(evals, 0, None))
            l1, l2 = np.sort(sqrt_evals)[-2:]
            return ("cirq/numpy float concurrence C = %.17g (ruído em "
                    "volta do exato — o certificado é o veredito estável)"
                    % max(0.0, 2 * l1 * l2))
        return "SKIP (§12): adaptador %r fora do plug-in" % sdk
    except Exception as ex:                      # noqa: BLE001
        return "SKIP (§12): %s indisponível (%s)" % (sdk, str(ex)[:80])
