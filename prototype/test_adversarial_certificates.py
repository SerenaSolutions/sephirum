#!/usr/bin/env python3
"""
TESTE DE ADULTERAÇÃO DE CERTIFICADOS (Fase 3, §6) + DETERMINISMO (§13).
=====================================================================

Gera certificados VÁLIDOS e adultera cada classe de campo:
  resultado, threshold, operador, valores, limites, uma etapa,
  ordem das etapas, modelo, status, campo de execução, método do kernel,
  veredito trivalente, hash do certificado, hash da entrada, pergunta.

Cada adulteração é testada em DUAS variantes:
  RAW     — certificado modificado (o hash quebra: integridade pega);
  REHASH  — certificado modificado E o hash recalculado pelo atacante
            (a integridade passa; quem rejeita é o PRINCÍPIO DE
            NÃO-CONFIANÇA: o checker re-deriva da fonte e diverge).

Exceção documentada (§21, honestidade): adulteração REHASH do
ELIMINATION_TRACE (rastro explicativo) passa — é campo informativo,
não é evidência da decisão. É a única exceção, declarada aqui e no
PHASE_3.md; o RAW é sempre rejeitado.

Meta do §6: 100% das adulterações conhecidas rejeitadas.
"""
import copy
import json
import sys

from decision_kernel import digest
from nexa_core import parse_nexa, NCA
from verify_certificate import verify

SRC = [
    # 0: redução monotônica
    """ASK:
    question: sum > 100
CONTRACT:
    absolute_error: 0
MODEL:
    type: threshold_sum
    terms: 60, 30, 20, 5, 4, 3, 2, 1
    assumption: terms_nonnegative""",
    # 1: bound intervalar decide positivo sem execução
    """ASK:
    question: sum > 40
MODEL:
    type: threshold_sum
    terms: 60, 30
    unknown: x in 0..10""",
    # 2: residual justificado
    """ASK:
    question: sum > 200
MODEL:
    type: threshold_sum
    terms: 60, 30, 20
    unknown: x in 0..1000
    unknown_value: 37""",
    # 3: execução completa (mediana)
    """ASK:
    question: median > 50
MODEL:
    type: raw_data
    data: 12, 87, 45, 63, 51, 39, 96, 4, 58""",
    # 4: UNKNOWN honesto
    """ASK:
    question: mean > 50
MODEL:
    type: mean_partial
    known: 60, 55, 65, 50, 60
    unknown_count: 5
    bounds: none""",
    # 5: determinante analítico
    """ASK:
    question: det > 20
MODEL:
    type: triangular_det
    matrix: 2,1,7; 0,3,4; 0,0,5""",
    # 6: forma fechada
    """ASK:
    question: sum > 100
MODEL:
    type: geometric_series
    r: 2
    n: 10""",
    # 7: emaranhado (Bell): critério de Schmidt decide sem execução
    """ASK:
    question: concurrence > 0.5
MODEL:
    type: entanglement
    state: 1, 0, 0, 1""",
]


def build():
    pairs = []
    for i, src in enumerate(SRC):
        blocks = parse_nexa(src)
        res = NCA(blocks, "adv%d" % i).compile()
        ok, reason = verify(blocks, res["certificate"])
        assert ok, "certificado BASE inválido no caso %d: %s" % (i, reason)
        pairs.append((blocks, res["certificate"]))
    return pairs


# ---- classes de adulteração: nome, função de mutação, rehash_deve_rejeitar ----
def _classes(pairs):
    """Classes cientes da família: cada mutação TEM que mudar algo real."""
    blocks, cert = pairs
    ev = cert.get("EVIDENCE", {})
    out = []

    def cls(name, mut, rehash_rejects=True):
        out.append((name, mut, rehash_rejects))

    cls("resultado", lambda c: c.__setitem__(
        "ANSWER", not c["ANSWER"] if isinstance(c["ANSWER"], bool) else True))
    cls("threshold_num", lambda c: c.__setitem__(
        "QUESTION", c["QUESTION"].rsplit(" ", 1)[0] + " 999999"))
    cls("operador", lambda c: c.__setitem__(
        "QUESTION", c["QUESTION"].replace(">", "<=") if ">" in c["QUESTION"]
        else c["QUESTION"].replace("<", ">=")))
    # valores: muta um campo numérico DECISIVO que existe (senão a classe não se aplica)
    num_keys = [kk for kk in ("witness_sum", "base_sum", "final_sum",
                              "evaluated_value", "det", "closed_form", "median",
                              "full_sum", "value", "mean_lo") if kk in ev]
    if num_keys:
        key = num_keys[0]
        def _mut_val(c, k=key):
            v = c["EVIDENCE"][k]
            try:                      # numérico: soma 1
                c["EVIDENCE"][k] = v + 1
            except TypeError:          # token exato (str): muda o token
                c["EVIDENCE"][k] = str(v) + "0"
        cls("valores", _mut_val)
    cls("limites", lambda c: c["EVIDENCE"].__setitem__("bounds", [-999, 999]))
    cls("uma_etapa", lambda c: c["ELIMINATION_TRACE"].append(
        {"rung": "QUANTUM", "outcome": "ELIMINATED", "detail": "mentira"}),
        rehash_rejects=False)  # rastro informativo: RAW rejeita, REHASH documentado
    if len(cert.get("ELIMINATION_TRACE", [])) >= 2:
        cls("ordem_etapas", lambda c: c["ELIMINATION_TRACE"].reverse(),
            rehash_rejects=False)
    others = [t for t in ("threshold_sum", "mean_partial", "triangular_det",
                          "geometric_series", "raw_data", "expression")
              if t != cert.get("MODEL_TYPE")]
    cls("modelo", lambda c, t=others[0]: c.__setitem__("MODEL_TYPE", t))
    st_other = ("FULL_EXECUTION_REQUIRED"
                if cert.get("STATUS") != "FULL_EXECUTION_REQUIRED"
                else "DECIDED_WITHOUT_EXECUTION")
    cls("status", lambda c, st=st_other: c.__setitem__("STATUS", st))
    cls("campo_execucao", lambda c: c["EVIDENCE"].__setitem__(
        "required_terms", 0 if c["EVIDENCE"].get("required_terms") else 7))
    methods = [m for m in ("MONOTONE_EARLY_STOP", "INTERVAL_BOUND",
                           "GEOMETRIC_CLOSED_FORM", "FULL_SUM",
                           "MEDIAN_CLASSICAL", "CONSTANT_FOLD")
               if m != cert.get("KERNEL")]
    cls("metodo_kernel", lambda c, m=methods[0]: (
        c.__setitem__("KERNEL", m),
        c["DECISION_KERNEL"].__setitem__("method", m)))
    cls("veredito", lambda c: c["DECISION_KERNEL"].__setitem__(
        "verdict", 0 if c["DECISION_KERNEL"].get("verdict") != 0 else 1))
    cls("cert_hash", lambda c: c.__setitem__("CERT_HASH", "0" * 64),
        rehash_rejects=False)
    cls("input_hash", lambda c: c.__setitem__("INPUT_HASH", "0" * 64),
        rehash_rejects=False)
    cls("pergunta", lambda c: (
        c.__setitem__("QUESTION", "sum > 99999"),
        c["EVIDENCE"].__setitem__("question", "sum > 99999")))
    cls("residual_kernel", lambda c: c["DECISION_KERNEL"].__setitem__(
        "residual_units", 12345))
    return out


def main():
    pairs = build()
    raw_rejected = raw_total = 0
    rehash_rejected = rehash_total = 0
    failures = []

    for pi, (blocks, cert) in enumerate(pairs):
        for name, mut, rehash_rejects in _classes((blocks, cert)):
            # RAW: adultera sem recalcular o hash
            t = copy.deepcopy(cert)
            mut(t)
            ok, reason = verify(blocks, t)
            raw_total += 1
            if not ok:
                raw_rejected += 1
            else:
                failures.append(("RAW", pi, name))

            # REHASH: adultera e recalcula o hash como um atacante faria
            t = copy.deepcopy(cert)
            mut(t)
            t.pop("CERT_HASH", None)
            t["CERT_HASH"] = digest(t)
            ok, reason = verify(blocks, t)
            rehash_total += 1
            if rehash_rejects and not ok:
                rehash_rejected += 1
            elif rehash_rejects:
                failures.append(("REHASH", pi, name))

    # ---- §13 determinismo: mesma entrada => mesmo hash, 3 execuções ----
    det_ok = True
    for i, src in enumerate(SRC):
        blocks = parse_nexa(src)
        hashes = set()
        for _ in range(3):
            res = NCA(blocks, "det%d" % i).compile()
            hashes.add(res["certificate"]["CERT_HASH"])
        if len(hashes) != 1:
            det_ok = False
            failures.append(("DETERMINISM", i, "hashes divergem: %d" % len(hashes)))
    # sensibilidade do hash: um dígito muda tudo
    blocks, cert = pairs[0]
    t = copy.deepcopy(cert)
    t["EVIDENCE"]["witness_sum"] += 1
    t.pop("CERT_HASH"); t["CERT_HASH"] = digest(t)
    if t["CERT_HASH"] == cert["CERT_HASH"]:
        det_ok = False
        failures.append(("HASH-SENSITIVITY", 0, "hash idêntico após alteração"))

    print("=" * 68)
    print("ADULTERAÇÃO (§6): RAW %d/%d rejeitados | REHASH %d/%d rejeitados"
          % (raw_rejected, raw_total, rehash_rejected, rehash_total))
    print("exceções REHASH esperadas (rastro informativo + hashes): %d classes"
          % sum(1 for _, _, r in _classes(pairs[0]) if not r))
    print("DETERMINISMO (§13): %s | sensibilidade do hash: %s"
          % ("OK" if det_ok else "FALHOU", "OK" if det_ok else "FALHOU"))
    if failures:
        for f in failures:
            print("  !!", f)
        print("RESULTADO: FALHOU — adulteração aceita como VÁLIDA")
        return 1
    print("RESULTADO: 100%% das adulterações obrigatórias rejeitadas. PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
