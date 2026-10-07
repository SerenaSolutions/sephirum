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
    """Decisão exata de emaranhamento -> dict de evidência."""
    model = blocks["MODEL"]
    fam = model.get("type", "")
    if fam != "entanglement":
        raise ValueError("família %r fora do plug-in (§12): este plug-in "
                         "decide emaranhamento de 2 qubits puros" % fam)
    q = blocks["ASK"]["question"].strip()
    parts = q.rsplit(" ", 2)
    if len(parts) != 3:
        raise ValueError("pergunta %r malformada — use 'entangled == 1' "
                         "ou 'concurrence > t'" % q)
    target, op, thr_s = parts
    toks = [x.strip() for x in model["state"].split(",")]
    if len(toks) != 4:
        raise ValueError("estado de emaranhamento exige 4 amplitudes")
    a, b, c, d = (Fraction(t) for t in toks)   # decimal exato, não float
    n = a * a + b * b + c * c + d * d
    if n == 0:
        raise ValueError("estado nulo não é estado quântico (§12)")
    det = a * d - b * c
    C = 2 * abs(det) / n                     # Fraction exata
    if target == "entangled":
        if op != "==":
            raise ValueError("'entangled' responde com '== 1'")
        ans = (det != 0) == (thr_s == "1")
    elif target == "concurrence":
        t = Fraction(thr_s)
        sq, tsq = 4 * det * det, t * t * n * n
        if op == ">":
            ans = True if t < 0 else sq > tsq
        elif op == ">=":
            ans = True if t <= 0 else sq >= tsq
        elif op == "<":
            ans = False if t <= 0 else sq < tsq
        elif op == "<=":
            ans = False if t < 0 else sq <= tsq
        elif op == "==":
            ans = sq == tsq
        else:
            raise ValueError("operador %r não suportado (§12)" % op)
    else:
        raise ValueError("alvo %r fora do plug-in: 'entangled' ou "
                         "'concurrence'" % target)
    return {
        "answer": bool(ans), "target": target, "op": op,
        "threshold": thr_s, "amplitudes": toks,
        "det": str(det), "norm_sq": str(n), "concurrence": str(C),
        "question": q,
    }


def certify(ev):
    """Certificado Zephirum: INPUT_HASH + selo CERT_HASH (SHA-256
    canônico do documento inteiro)."""
    state_str = ",".join(ev["amplitudes"])
    input_hash = hashlib.sha256(state_str.encode()).hexdigest()
    cert = {
        "PLUGIN": "zephirum-quantum-plugin",
        "ALGORITHM": "ZEPHIRUM SCHMIDT_DET_CRITERION",
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
    return cert


def verify(src, cert):
    """Verificação INDEPENDENTE do certificado: refaz a decisão e
    confere o selo. Retorna (ok, motivo)."""
    try:
        ev = decide(parse_nexa(src))
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
    return True, "decisão reproduzida e selo confere"


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
    receipt = {
        "routed": True,
        "status": cert["STATUS"],
        "verdict": 1 if ev["answer"] else 0,
        "concurrence_exact": ev["concurrence"],
        "cert": cert,
        "independent_check": (ok, why),
        "qpu_units_billed": 0,
    }
    if sdk:
        from .adapters import sdk_cross_check
        receipt["sdk_cross_check"] = sdk_cross_check(
            sdk, ev["amplitudes"], ev["threshold"])
    return receipt, ok
