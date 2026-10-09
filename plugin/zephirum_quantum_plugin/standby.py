#!/usr/bin/env python3
"""MODO STANDBY — o plug-in que AGUARDA a computação quântica.

Direção do dono: instalar nos smartphones do mundo, nos computadores
clássicos, nos sistemas operacionais clássicos — e ficar pronto para
o dia em que o QPU existir. Hoje o serviço ATIVO é a decisão clássica
EXATA em bytecode Zephirum (zero unidades QPU, prova antes de
executar); amanhã, quando houver QPU no aparelho, o MESMO caminho de
certificado roteia — nada muda na arquitetura.

Honestidade (§12): nunca fingimos QPU. O probe olha só o que existe
LOCALMENTE (sem rede) e declara o estado real.
"""
import importlib.util


def qpu_probe():
    """Estado honesto do QPU neste dispositivo — §12: recibo, nunca
    encenação. Sem chamadas de rede: só presença local."""
    sdks = []
    for nome in ("qiskit", "cirq", "pennylane"):
        try:
            if importlib.util.find_spec(nome) is not None:
                sdks.append(nome)
        except (ImportError, ValueError):
            pass
    # Em 2026 nenhum smartphone/PC tem QPU físico acessível —
    # declarado como fato da engenharia, não como promessa.
    return {
        "QPU_REAL": False,
        "STATUS": "AWAITING",
        "MOTIVO": ("no physical quantum processor accessible to this "
                   "device (§12); installed classic SDKs are "
                   "SIMULATORS, not QPUs; the moment a real QPU exists "
                   "on the device, the same certificate routes"),
        "SDKS_CLASSICOS": sdks,
        "DECISAO_CLASSICA": "ACTIVE — Zephirum bytecode, exact, "
                            "zero QPU units",
        "PRONTO_PARA": "route to the QPU without changing the "
                       "certificate path (INPUT_HASH/CERT_HASH)",
    }


def standby_receipt(src):
    """Recibo standby: probe honesto + decisão clássica JÁ ativa."""
    from .core import gateway
    receipt, ok = gateway(src)
    probe = qpu_probe()
    receipt["standby"] = probe
    return receipt, ok

def qpu_probe_remote():
    """Remote QPU reachability — §12 still intact: this NEVER claims
    the local device has a QPU. It reports whether real quantum
    hardware is reachable through a cloud credential, and lists it
    as evidence. No job is submitted: zero QPU time spent."""
    import os
    token = None
    for var in ("ZEPHIRUM_IBM_TOKEN", "IBM_QUANTUM_TOKEN",
                "QISKIT_IBM_TOKEN"):
        token = os.environ.get(var)
        if token:
            break
    if not token:
        return {
            "QPU_LOCAL": False,
            "REMOTE": "NO_CREDENTIALS",
            "STATUS": "AWAITING",
            "MOTIVO": ("no IBM Quantum credential in environment "
                       "(§12): nothing is claimed, nothing is "
                       "faked; set ZEPHIRUM_IBM_TOKEN to probe"),
        }
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        svc = QiskitRuntimeService(token=token,
                                   channel="ibm_quantum_platform")
        backends = svc.backends(simulator=False, operational=True)
        return {
            "QPU_LOCAL": False,
            "REMOTE": "REACHABLE",
            "STATUS": "REMOTE_REACHABLE",
            "BACKENDS": [{"name": b.name, "qubits": b.num_qubits}
                         for b in backends],
            "QPU_UNITS_SPENT": 0,
            "MOTIVO": ("real quantum hardware reachable by cloud "
                       "credential; the device itself still has no "
                       "QPU (§12): cloud access is evidence, not a "
                       "local claim; no job was submitted"),
        }
    except Exception as e:  # honest failure, never a guess
        return {
            "QPU_LOCAL": False,
            "REMOTE": "UNREACHABLE",
            "STATUS": "AWAITING",
            "MOTIVO": ("credential present but cloud unreachable "
                       "(§12): %s" % type(e).__name__),
        }
