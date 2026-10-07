#!/usr/bin/env python3
"""
TESTE DE MODELOS COMPUTACIONAIS MÚLTIPLOS (Fase 4, fatia 2).
============================================================

O MESMO problema executado por modelos distintos:
  exact   — Fraction (a aritmética do kernel)
  float64 — ponto flutuante binário

Hipóteses medidas:
  M1  na faixa de valor comum (< 2^53), os modelos CONCORDAM
  M2  na zona de precisão (valores ~ 2^53 e além), o float64 DIVERGE
      do exato — e o exato é quem está certo (verdade por construção)
  M3  modelos registrados e não implementados (gpu/hpc/qpu) falham
      EXPLICITAMENTE — nunca silêncio, nunca fingimento (§12)

Esta é a razão arquitetural da aritmética exata do ZEPHIRUM,
transformada em evidência medida.
"""
import sys

from nexa_core import parse_nexa
from zephirum_simulator import MODELS, ModelNotAvailable, simulate_full


def _both(src):
    blocks = parse_nexa(src)
    e = simulate_full(blocks, "exact")
    f = simulate_full(blocks, "float64")
    return e, f


def main():
    # M1 — faixa comum: 10.000 casos, concordância total
    import random
    random.seed(77)
    agree = disagree = 0
    for _ in range(10000):
        terms = [random.randint(1, 1000) for _ in range(random.randint(3, 10))]
        thr = random.randint(1, sum(terms) + 500)
        src = ("ASK:\n    question: sum > %d\nMODEL:\n    type: threshold_sum\n"
               "    terms: %s\n" % (thr, ", ".join(map(str, terms))))
        e, f = _both(src)
        assert e["status"] == "DECIDED" == f["status"]
        if e["answer"] == f["answer"]:
            agree += 1
        else:
            disagree += 1
    assert disagree == 0, "float64 divergiu na faixa comum?!"
    print("M1 faixa comum: 10.000 casos, exact == float64 (%d/%d)"
          % (agree, agree + disagree))

    # M2 — zona de precisão: o float64 troca os pés
    BIG = 10 ** 16
    trap_sum = ("ASK:\n    question: sum > %d\nMODEL:\n    type: threshold_sum\n"
                "    terms: %d, %d\n" % (BIG, BIG, 1))
    # soma exata: 10^16 + 1 > 10^16 é VERDADEIRO; float64: 1e16 + 1
    # colapsa para 1e16 e a comparação dá FALSO
    e, f = _both(trap_sum)
    assert e["answer"] is True and f["answer"] is False, (e, f)
    trap_mean = ("ASK:\n    question: mean > %d\nMODEL:\n    type: mean_partial\n"
                 "    known: %d, %d\n    unknown_count: 1\n    bounds: %d..%d\n"
                 % (BIG, BIG, BIG + 1, BIG, BIG))
    e, f = _both(trap_mean)
    assert e["answer"] is True and f["answer"] is False, (e, f)
    print("M2 zona de precisão (1e16): float64 erra onde o exact acerta — "
          "soma e média medidas")

    # M3 — modelos registrados e não implementados: falha explícita
    blocks = parse_nexa("ASK:\n    question: sum > 5\nMODEL:\n    type: "
                        "threshold_sum\n    terms: 1, 2, 3")
    for m in ("gpu", "hpc", "qpu"):
        assert m in MODELS
        try:
            simulate_full(blocks, m)
            raise AssertionError("modelo %r fingiu execução!" % m)
        except ModelNotAvailable as e:
            assert m in str(e)
    try:
        simulate_full(blocks, "analógico")
        raise AssertionError("modelo desconhecido aceito")
    except ValueError as e:
        assert "unknown computational model" in str(e)
    print("M3 modelos gpu/hpc/qpu: registrados, falham EXPLICITAMENTE "
          "(ModelNotAvailable); desconhecido: ValueError")

    print("RESULTADO: PASS — múltiplos modelos são evidência medida, "
          "não promessa")
    return 0


if __name__ == "__main__":
    sys.exit(main())
