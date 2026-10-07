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
        "STATUS": "AGUARDANDO",
        "MOTIVO": ("nenhum processador quântico físico acessível a "
                   "este dispositivo (§12); SDKs clássicos instalados "
                   "são SIMULADORES, não QPU; quando um QPU real "
                   "existir no aparelho, o mesmo certificado roteia"),
        "SDKS_CLASSICOS": sdks,
        "DECISAO_CLASSICA": "ATIVA — bytecode Zephirum, exata, "
                            "zero unidades QPU",
        "PRONTO_PARA": "rotear ao QPU sem mudar o caminho de "
                       "certificado (INPUT_HASH/CERT_HASH)",
    }


def standby_receipt(src):
    """Recibo standby: probe honesto + decisão clássica JÁ ativa."""
    from .core import gateway
    receipt, ok = gateway(src)
    probe = qpu_probe()
    receipt["standby"] = probe
    return receipt, ok
