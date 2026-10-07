#!/usr/bin/env python3
"""
PROPERTY-BASED TESTING (Fase 3, §11) + SEGURANÇA CONTRA INCONSISTÊNCIA (§12).
============================================================================

Propriedades matemáticas (§11), geradas automaticamente (seed fixo):
  P1  lower_bound > threshold  =>  resposta TRUE decidida
  P2  upper_bound < threshold =>  resposta FALSE decidida
  P3  limiares dentro do intervalo => NENHUMA decisão sem prova adicional
      (UNKNOWN honesto; nunca True/False inventado)
  P4  operadores {>, <, >=, <=, ==} na família de expressões exatas
  P5  extremos: 0, 1, -1, limites iguais (lo==hi), negativos, 10^15

Segurança (§12) — o sistema deve falhar EXPLICITAMENTE (nunca UNKNOWN
silencioso) para: modelo desconhecido, intervalo invertido, inf/nan,
valor não numérico, expressão não dobrável, certificado incompleto,
campo extra sem rehash.
"""
import copy
import random
import sys

from nexa_core import parse_nexa, NCA
from verify_certificate import verify

random.seed(311)
T15 = 10 ** 15


def src_sum(terms, thr, unk=None):
    s = ("ASK:\n    question: sum > %d\nCONTRACT:\n    absolute_error: 0\n"
         "MODEL:\n    type: threshold_sum\n    terms: %s\n"
         "    assumption: terms_nonnegative\n" % (thr, ", ".join(map(str, terms))))
    if unk:
        s += "    unknown: x in %d..%d\n" % unk
    return s


def src_mean(known, u, lo, hi, thr):
    return ("ASK:\n    question: mean > %d\nMODEL:\n    type: mean_partial\n"
            "    known: %s\n    unknown_count: %d\n    bounds: %d..%d\n"
            % (thr, ", ".join(map(str, known)), u, lo, hi))


def run(src, name="p"):
    blocks = parse_nexa(src)
    res = NCA(blocks, name).compile()
    return res


def p_bounds_threshold():
    """P1/P2/P3 sobre threshold_sum com incógnita."""
    ok = 0
    for i in range(400):
        terms = [random.randint(0, 100) for _ in range(random.randint(1, 6))]
        base = sum(terms)
        lo = random.randint(0, 50)
        hi = lo + random.randint(0, 100)
        mode = i % 3
        if mode == 0:      # P1: bound inferior já decide TRUE
            thr = base + lo - random.randint(1, 10) - 1
            res = run(src_sum(terms, thr, (lo, hi)), "p1")
            assert res["answer"] is True and res["required"] == 0, (thr, lo, hi)
        elif mode == 1:    # P2: bound superior já refuta FALSE
            thr = base + hi + random.randint(0, 10)
            res = run(src_sum(terms, thr, (lo, hi)), "p2")
            assert res["answer"] is False and res["required"] == 0, (thr, lo, hi)
        else:              # P3: straddle => UNKNOWN, nunca decidido sem prova
            if hi == lo:      # degenerado é decidível — não serve para P3
                hi += 1
            thr = base + lo + random.randint(0, hi - lo - 1)
            res = run(src_sum(terms, thr, (lo, hi)), "p3")
            assert res["status"] == "UNKNOWN", (base, thr, lo, hi, res["status"])
        ok += 1
    return ok


def p_bounds_mean():
    """P1/P2/P3 sobre mean_partial — inclui a armadilha 1e16 (Float vs Fraction)."""
    ok = 0
    for i in range(400):
        known = [random.randint(0, 80) for _ in range(random.randint(1, 5))]
        u = random.randint(1, 5)
        tot = sum(known)
        n = len(known) + u
        # limiar construído como múltiplo exato: mean_lo/hi com margem limpa
        mode = i % 3
        if mode == 0:      # P1: média mínima > limiar => TRUE sem execução
            lo = random.randint(10, 60); hi = lo + random.randint(0, 40)
            thr = (tot + u * lo) // n - random.randint(1, 5) - 1
            res = run(src_mean(known, u, lo, hi, thr), "m1")
            assert res["answer"] is True, (known, u, lo, hi, thr)
        elif mode == 1:    # P2: média máxima <= limiar => FALSE
            lo = random.randint(0, 40); hi = lo + random.randint(0, 40)
            thr = (tot + u * hi) // n + random.randint(0, 5) + 1
            res = run(src_mean(known, u, lo, hi, thr), "m2")
            assert res["answer"] is False, (known, u, lo, hi, thr)
        else:              # P3: straddle => UNKNOWN honesto
            lo = random.randint(10, 50); hi = lo + random.randint(5, 40)
            # limiar entre as duas médias: média mín < thr < média máx
            m_lo = (tot + u * lo) / n
            m_hi = (tot + u * hi) / n
            if m_hi - m_lo < 2:
                continue
            thr = int(m_lo) + 1
            if not (m_lo <= thr < m_hi):
                continue
            res = run(src_mean(known, u, lo, hi, thr), "m3")
            assert res["status"] == "UNKNOWN", (known, u, lo, hi, thr, res["status"])
        ok += 1
    # armadilha de precisão: motor tem que decidir COMO a Fraction, não como o float
    res = run(src_mean([10 ** 16, 10 ** 16 + 1], 1, 10 ** 16, 10 ** 16, 10 ** 16),
              "trap16")
    assert res["answer"] is True, "armadilha 1e16: float venceu a exatidão"
    return ok + 1


def p_ops_expression():
    """P4/P5: todos os operadores, valores extremos, aritmética exata."""
    ops = [">", "<", ">=", "<=", "=="]
    vals = [0, 1, -1, 7, -13, 10 ** 15, -(10 ** 15)]
    ok = 0
    for op in ops:
        for v in vals:
            for thr in (0, 1, -1, 10 ** 15):
                expr = str(v)
                src = ("ASK:\n    question: value %s %d\nMODEL:\n"
                       "    type: expression\n    expr: %s\n" % (op, thr, expr))
                res = run(src, "op")
                truth = {" >": v > thr}.get(" ") or None
                expected = {">": v > thr, "<": v < thr, ">=": v >= thr,
                            "<=": v <= thr, "==": v == thr}[op]
                assert res["answer"] == expected, (op, v, thr, res["answer"])
                ok += 1
    return ok


def p_equal_bounds():
    """P5: limites degenerados lo == hi equivalem ao valor conhecido."""
    ok = 0
    for _ in range(50):
        terms = [random.randint(0, 50) for _ in range(3)]
        base = sum(terms)
        x = random.randint(0, 100)
        thr = base + x - random.choice([-1, 0, 1])
        res = run(src_sum(terms, thr, (x, x)), "eq")
        assert res["answer"] == (base + x > thr), (base, x, thr)
        assert res["status"] != "UNKNOWN", "lo==hi é sempre decidível"
        ok += 1
    return ok


def robustness():
    """§12: erros estruturais falham EXPLICITAMENTE (ValueError), nunca UNKNOWN."""
    def must_raise(src, frag):
        try:
            run(src, "bad")
        except ValueError as e:
            assert frag in str(e), (frag, str(e))
            return
        raise AssertionError("esperava ValueError (%s) — virou decisão/UNKNOWN?" % frag)

    must_raise("ASK:\n    question: sum > 5\nMODEL:\n    type: nonsense\n",
               "unsupported model type")
    must_raise(src_sum([1, 2], 5, (10, 3)), "inverted bounds")
    must_raise("ASK:\n    question: sum > inf\nMODEL:\n    type: threshold_sum\n"
               "    terms: 1, 2\n    assumption: terms_nonnegative\n",
               "non-finite")
    must_raise("ASK:\n    question: sum > nan\nMODEL:\n    type: threshold_sum\n"
               "    terms: 1, 2\n", "non-finite")
    must_raise("ASK:\n    question: value > 5\nMODEL:\n    type: expression\n"
               "    expr: a + 1\n", "not foldable")
    must_raise("ASK:\n    question: sum > 5\nMODEL:\n    type: threshold_sum\n"
               "    terms: um, dois\n", "could not convert")  # não numérico
    # certificado incompleto: rejeitado, nunca aceito
    blocks = parse_nexa(src_sum([5, 5], 7))
    res = NCA(blocks, "inc").compile()
    for missing in ("INPUT_HASH", "STATUS", "ANSWER", "KERNEL", "CERT_HASH"):
        t = copy.deepcopy(res["certificate"])
        t.pop(missing, None)
        ok, _ = verify(blocks, t)
        assert ok is False, "certificado sem %s foi ACEITO" % missing
    # campo extra sem rehash: integridade pega
    t = copy.deepcopy(res["certificate"])
    t["EXTRA"] = "campo malformado"
    ok, _ = verify(blocks, t)
    assert ok is False, "campo extra aceito sem quebra de hash"
    return 10


def main():
    n = p_bounds_threshold()
    n += p_bounds_mean()
    n += p_ops_expression()
    n += p_equal_bounds()
    r = robustness()
    print("(§11) propriedades matemáticas: %d casos OK" % n)
    print("(§12) robustez estrutural: %d checagens OK — erros explícitos, "
          "nunca UNKNOWN silencioso" % r)
    print("RESULTADO: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
