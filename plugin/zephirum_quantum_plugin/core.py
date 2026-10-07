#!/usr/bin/env python3
"""ZEPHIRUM QUANTUM PLUGIN — core de decisão (self-contained).

O algoritmo Zephirum de emaranhamento, encapsulado a partir do
primeiro artefato da casa (o verificador autônomo transpilado em
Python/C/Java): PROVA ANTES DE EXECUTAR.

Fórmula (matéria universal — não de autores individuais):
  estado puro de 2 qubits  M = [[a, b], [c, d]]
  det(M) = 0  <=>  estado produto (posto de Schmidt 1)
  concorrência C = 2|det| / <psi|psi>   (Wootters, PRL 80, 2245,
  1998; Schmidt 1906; Nielsen & Chuang, cap. 2)

Decisão EXATA em Fraction (o quadrado elimina a raiz):
  C ~ t  <=>  4·det² ~ t²·n²,  n = <psi|psi> > 0
Zero unidades QPU: o critério analítico elimina o vetor de estado +
autodecomposição (8 unidades) do caminho SDK.
"""
import hashlib
import json
from fractions import Fraction


def parse_nexa(src):
    """NEXA source -> blocos (ASK / MODEL / CONTRACT / BUDGET)."""
    blocks, current = {}, None
    for raw in src.strip().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head = line[:-1].strip() if line.endswith(":") else ""
        if head in ("ASK", "CONTRACT", "MODEL", "BUDGET", "REQUIRE"):
            current = head
            blocks[current] = {}
        elif current is not None and ":" in line:
            k, v = line.split(":", 1)
            blocks[current][k.strip()] = v.strip()
        else:
            raise SyntaxError("linha fora de bloco: %r" % line)
    for req in ("ASK", "MODEL"):
        if req not in blocks:
            raise SyntaxError("bloco %s ausente" % req)
    return blocks


def decide(blocks):
    """Decisão EM ZEPHIRUM: a pergunta e o estado são COMPILADOS para
    bytecode da linguagem e executados pela VM — o algoritmo é da
    linguagem; Python é só emissor/interpretador (javac/JVM), e com
    o zvm C não há Python no runtime."""
    from .zephirum_plugin_lang import (encode as _enc,
                                        build_plugin_program)
    from .zephirum_vm import ZephirumVM
    model = blocks["MODEL"]
    if model.get("type", "") != "entanglement":
        raise ValueError("família %r fora do plug-in (§12): este "
                         "plug-in decide emaranhamento de 2 qubits "
                         "puros" % model.get("type", ""))
    state = model["state"]
    q = blocks["ASK"]["question"].strip()
    parts = q.rsplit(" ", 2)
    if len(parts) != 3:
        raise ValueError("pergunta %r malformada" % q)
    target, op, thr_s = parts
    chars = _enc(state)
    prog = build_plugin_program(chars, q)
    vm = ZephirumVM(chars, len(chars))
    vm.run(prog)
    det, nsq, c_ex, vd, valid, nv = (x for x in vm.last_stack)
    if valid != 1:
        raise ValueError("estado %r inválido (§12): exija 4 "
                         "amplitudes e norma > 0" % state)
    return {
        "answer": bool(vd == 1), "target": target, "op": op,
        "threshold": thr_s,
        "amplitudes": [x.strip() for x in state.split(",")],
        "det": str(det), "norm_sq": str(nsq),
        "concurrence": str(c_ex), "question": q,
        "algorithm": "ZEPHIRUM BYTECODE (Schmidt det criterion)",
        "units": vm.units,
    }


def certify(ev):
    """Certificado Zephirum: INPUT_HASH + selo CERT_HASH (SHA-256
    canônico do documento inteiro)."""
    state_str = ",".join(ev["amplitudes"])
    input_hash = hashlib.sha256(state_str.encode()).hexdigest()
    cert = {
        "PLUGIN": "zephirum-quantum-plugin",
        "ALGORITHM": "ZEPHIRUM BYTECODE: SCHMIDT_DET_CRITERION",
        "ENCAPSULATION": "função pura: sem rede, sem I/O, sem eval — superfície mínima (S12)",
        "INPUT_HASH": input_hash,
        "QUESTION": ev["question"],
        "ANSWER": ev["answer"],
        "CONCURRENCE_EXACT": ev["concurrence"],
        "DETERMINANT_EXACT": ev["det"],
        "NORM_SQ_EXACT": ev["norm_sq"],
        "QPU_UNITS_BILLED": 0,
        "ELIMINATED_SDK_PATH": "statevector + eigendecomposition "
                               "(8 unidades — critério fechado)",
        "STATUS": "DECIDED_WITHOUT_EXECUTION",
    }
    cert["CERT_HASH"] = hashlib.sha256(
        json.dumps(cert, sort_keys=True).encode()).hexdigest()
    from .pqprotect import pq_protect
    return pq_protect(cert)


def verify(src, cert):
    """Verificação INDEPENDENTE do certificado: refaz a decisão e
    confere o selo. Retorna (ok, motivo)."""
    try:
        blocks = parse_nexa(src)
        from .zephirum_plugin_lang import ref_plugin_decision
        r = ref_plugin_decision(blocks["MODEL"]["state"],
                                blocks["ASK"]["question"])
        if r["valid"] != 1:
            return False, "referência reprova o estado (§12)"
        ev = {
            "answer": r["verdict"] == 1,
            "target": blocks["ASK"]["question"].rsplit(" ", 2)[0],
            "op": blocks["ASK"]["question"].rsplit(" ", 2)[1],
            "threshold": blocks["ASK"]["question"].rsplit(" ", 2)[2],
            "amplitudes": [x.strip() for x in
                           blocks["MODEL"]["state"].split(",")],
            "det": str(r["det"]), "norm_sq": str(r["nsq"]),
            "concurrence": str(r["C"]),
            "question": blocks["ASK"]["question"],
        }
    except Exception as ex:                       # noqa: BLE001
        return False, "decisão não reproduz: %s" % ex
    rebuilt = certify(ev)
    if rebuilt["ANSWER"] != cert.get("ANSWER"):
        return False, "resposta diverge do certificado"
    if rebuilt["CONCURRENCE_EXACT"] != cert.get("CONCURRENCE_EXACT"):
        return False, "concorrência exata diverge"
    if rebuilt["CERT_HASH"] != cert.get("CERT_HASH"):
        return False, "selo CERT_HASH não confere (adulteração)"
    if rebuilt["INPUT_HASH"] != cert.get("INPUT_HASH"):
        return False, "INPUT_HASH não confere (entrada trocada)"
    from .pqprotect import pq_verify
    okq, whyq = pq_verify(cert)
    if not okq:
        return False, whyq
    return True, "decisão reproduzida, selo e assinatura pós-quântica conferem"


def gateway(src, sdk=None, sdk_check=None):
    """API principal do plug-in: fonte NEXA -> recibo honesto.
    sdk: nome do gêmeo adversarial ('qiskit'/'cirq') para
    contraprova float OPCIONAL (nunca obrigatória)."""
    blocks = parse_nexa(src)
    try:
        ev = decide(blocks)
    except ValueError as ex:
        return {
            "routed": False,
            "reason": str(ex),
            "qpu_units_billed": 0,
            "advice": "rode direto no SDK — nada provável aqui (§12)",
        }, False
    cert = certify(ev)
    ok, why = verify(src, cert)
    from .pqprotect import pq_verify
    receipt = {
        "routed": True,
        "status": cert["STATUS"],
        "verdict": 1 if ev["answer"] else 0,
        "concurrence_exact": ev["concurrence"],
        "cert": cert,
        "independent_check": (ok, why),
        "pq_protect": pq_verify(cert),
        "qpu_units_billed": 0,
    }
    if sdk:
        from .adapters import sdk_cross_check
        receipt["sdk_cross_check"] = sdk_cross_check(
            sdk, ev["amplitudes"], ev["threshold"])
    return receipt, ok
