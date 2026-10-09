#!/usr/bin/env python3
"""
FALSIFICATION EXPERIMENT — 2000 problemas adversariais (4 familias x 500).

Escala da bateria falsification_200.py (que permanece intocada e é
importada aqui como base: seus 200 casos originais entram nos 2000).
Novos 1800 casos são GERADOS de forma determinística (semente fixa),
com verdade-terreno independente por metodo diferente do motor:

- threshold_sum : aritmetica inteira exata (bigint)
- mean_partial  : Fraction exata
- triangular_det: Bareiss (o motor usa Laplace/produto)
- geo           : somatorio direto (o motor usa forma fechada)

Politica inalterada: UM falso positivo (decisao errada certificada)
derruba o experimento (exit 1). Falsos negativos sao tolerados e
contados. Meta do charter: 0 certificados falsos.
"""
import json
import random
import sys
from fractions import Fraction

import falsification_200 as base
from falsification_200 import add, src_sum, src_mean, src_det, src_geo

RNG = random.Random(20261009)   # semente fixa: bateria reproduzível
OPS_MONO = (">", ">=")          # ops monotônicos p/ incógnita (sem ambiguidade)
OPS_ALL = (">", ">=", "<", "<=")


def op_truth(op, val, thr):
    if op == ">":
        return val > thr
    if op == ">=":
        return val >= thr
    if op == "<":
        return val < thr
    if op == "<=":
        return val <= thr
    if op == "==":
        return val == thr
    raise ValueError(op)


# ══ F1x: threshold_sum gerado ══════════════════════════════════════
def f1x():
    fam = "threshold_sum"
    for i in range(450):
        name = "g1_%03d" % i
        n_terms = RNG.randint(1, 12)
        big = i % 25 == 0
        terms = [RNG.randint(1, 10 ** 4) for _ in range(n_terms)]
        if big:  # bigint exato
            terms = [RNG.randint(10 ** 14, 10 ** 15) for _ in range(3)]
        neg = (i % 7 == 0)
        if neg:
            terms = [RNG.randint(-100, 100) for _ in range(n_terms)]
        s = sum(terms)
        op = RNG.choice(OPS_ALL)
        mode = i % 10
        if mode in (0, 1):                      # limiar exato e vizinho (armadilha)
            thr = s if mode == 0 else s + RNG.choice([1, -1])
        else:
            thr = s + RNG.randint(-5000, 5000)
        if not neg and i % 3 == 0:              # com incógnita (monotônica)
            lo = RNG.randint(-100, 100)
            hi = lo + RNG.randint(0, 200)
            op = RNG.choice(OPS_MONO)
            all_t = op_truth(op, s + lo, thr) and op_truth(op, s + hi, thr)
            all_f = (not op_truth(op, s + lo, thr)) and (not op_truth(op, s + hi, thr))
            if all_t:
                add(fam, name, src_sum(terms, thr, op, unk=(lo, hi)), "decided", True)
            elif all_f:
                add(fam, name, src_sum(terms, thr, op, unk=(lo, hi)), "decided", False)
            else:
                add(fam, name, src_sum(terms, thr, op, unk=(lo, hi)), "undecidable", None)
        elif not neg and i % 5 == 2:            # oráculo fixa x
            lo = RNG.randint(-50, 50)
            hi = lo + RNG.randint(0, 100)
            xv = RNG.randint(lo, hi)
            thr = s + xv + RNG.choice([0, 1, -1])
            op = RNG.choice(OPS_MONO)
            add(fam, name, src_sum(terms, thr, op, unk=(lo, hi), x_val=xv),
                "decided", op_truth(op, s + xv, thr))
        else:                                   # sem incógnita
            truth = op_truth(op, s, thr)
            add(fam, name, src_sum(terms, thr, op, assumption=not neg),
                "decided", truth)


# ══ F2x: mean_partial gerado ══════════════════════════════════════
def f2x():
    fam = "mean_partial"
    for i in range(450):
        name = "g2_%03d" % i
        known = [RNG.randint(-100, 100) for _ in range(RNG.randint(1, 8))]
        u = RNG.randint(1, 5)
        if i % 9 == 0:                          # bounds none => UNKNOWN obrigatório
            add(fam, name, src_mean(known, u, "none", RNG.randint(-100, 100)),
                "undecidable", None)
            continue
        lo = RNG.randint(-100, 100)
        hi = lo + RNG.randint(0, 100)
        tot, N = sum(known), len(known) + u
        m_lo = Fraction(tot + u * lo, N)
        m_hi = Fraction(tot + u * hi, N)
        if i % 4 == 0:                          # contorno exato (armadilha)
            thr = m_hi if i % 8 == 0 else m_lo
            if thr.denominator != 1:            # thr inteiro p/ src_mean
                thr = int(thr) + 1
            thr = int(thr)
        else:
            thr = RNG.randint(-100, 100)
        mode, truth = base.mean_truth(known, u, lo, hi, thr)
        if mode == "undecidable":
            add(fam, name, src_mean(known, u, "%d..%d" % (lo, hi), thr),
                "undecidable", None)
        else:
            add(fam, name, src_mean(known, u, "%d..%d" % (lo, hi), thr),
                "decided", truth)


# ══ F3x: triangular_det gerado ════════════════════════════════════
def f3x():
    fam = "triangular_det"
    for i in range(450):
        name = "g3_%03d" % i
        n = RNG.randint(1, 6)
        kind = i % 4
        M = [[0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                if kind == 0:                   # superior
                    M[r][c] = RNG.randint(-20, 20) if c >= r else 0
                elif kind == 1:                 # inferior
                    M[r][c] = RNG.randint(-20, 20) if c <= r else 0
                elif kind == 2:                 # diagonal
                    M[r][c] = RNG.randint(-20, 20) if c == r else 0
                else:                          # geral
                    M[r][c] = RNG.randint(-20, 20)
        if i % 20 == 0:                         # bigint diagonal
            n = 3
            M = [[10 ** 9 if c == r else 0 for c in range(n)] for r in range(n)]
        d = base.det_bareiss(M)
        op = RNG.choice(OPS_ALL)
        mode = i % 6
        if mode == 0:
            thr = d                             # limiar exato (armadilha)
        elif mode == 1:
            thr = d + RNG.choice([1, -1])
        else:
            thr = d + RNG.randint(-500, 500)
        add(fam, name, src_det(M, thr, op), "decided", op_truth(op, d, thr))


# ══ F4x: geo gerado ═══════════════════════════════════════════════
def f4x():
    fam = "geo"
    rs = [-2, -1, 0, 1, 2, 3, 5, 7, -3, 10, 10 ** 6]
    for i in range(450):
        name = "g4_%03d" % i
        r = RNG.choice(rs) if i % 10 else 10 ** 9
        n = RNG.randint(0, 150) if abs(r) <= 10 else RNG.randint(0, 6)
        g = base.geo_truth(r, n)
        op = RNG.choice(OPS_ALL + ("==",))
        mode = i % 5
        if mode == 0:
            thr = g                             # limiar exato (armadilha)
        elif mode == 1:
            thr = g + RNG.choice([1, -1])
        else:
            thr = g + RNG.randint(-10 ** 6, 10 ** 6)
        add(fam, name, src_geo(r, n, thr, op), "decided", op_truth(op, g, thr))


f1x(); f2x(); f3x(); f4x()

TOTAL = len(base.CASES)
assert TOTAL == 2000, "esperado 2000 casos, obtidos %d" % TOTAL


def main():
    from nexa_core import parse_nexa, NCA
    from verify_certificate import verify

    wrong, false_neg, caught, unknown_ok = [], [], [], 0
    fam_stats, gen_stats = {}, {}
    total_orig = total_req = 0
    certs_ok = certs_bad = 0
    for c in base.CASES:
        fam = c["family"]
        st = fam_stats.setdefault(fam, {"n": 0, "wrong": 0, "false_neg": 0,
                                        "caught": 0, "unknown_ok": 0})
        st["n"] += 1
        blocks = parse_nexa(c["src"])
        res = NCA(blocks, c["name"]).compile()
        ok, reason = verify(blocks, res["certificate"])
        total_orig += res["original"] or 0
        total_req += res["required"] or 0
        if ok:
            certs_ok += 1
        else:
            certs_bad += 1
        decided = res["status"] != "UNKNOWN"
        if c["mode"] == "undecidable":
            if decided:
                wrong.append((c["name"], fam, "DECIDED onde era indecidível",
                              res["answer"], c["src"]))
                st["wrong"] += 1
            else:
                unknown_ok += 1
                st["unknown_ok"] += 1
        else:
            if not decided:
                false_neg.append((c["name"], fam, res["status"]))
                st["false_neg"] += 1
            elif res["answer"] != c["truth"]:
                if not ok:
                    caught.append((c["name"], fam, reason))
                    st["caught"] += 1
                else:
                    wrong.append((c["name"], fam, "certificado FALSO aceito",
                                  res["answer"], c["truth"], c["src"]))
                    st["wrong"] += 1
            else:
                if not ok:
                    caught.append((c["name"], fam, reason))
                    st["caught"] += 1
    elim = (100.0 * (total_orig - total_req) / total_orig) if total_orig else 0.0
    print("=" * 70)
    print("FALSIFICATION EXPERIMENT — 2000 problemas adversariais, 4 famílias")
    print("(200 originais + 1800 gerados determinísticos, semente 20261009)")
    print("=" * 70)
    for fam, st in fam_stats.items():
        print("%-15s n=%4d  falsos=%d  falsos-neg=%d  checker-caught=%d  UNKNOWN-ok=%d"
              % (fam, st["n"], st["wrong"], st["false_neg"], st["caught"], st["unknown_ok"]))
    print("-" * 70)
    print("certificados verificados: %d/2000 | rejeitados (defesa agiu): %d"
          % (certs_ok, certs_bad))
    print("eliminação: %.1f%%  (orig=%d req=%d)" % (elim, total_orig, total_req))
    print("FALSOS CERTIFICADOS: %d   <- meta: 0" % len(wrong))
    for w in wrong:
        print("  !!", w)
    print("falsos negativos (tolerados): %d" % len(false_neg))
    print("mentiras capturadas pelo checker: %d" % len(caught))
    json.dump({"per_family": fam_stats,
               "wrong": [list(map(str, w)) for w in wrong],
               "false_negatives": [list(map(str, f)) for f in false_neg],
               "caught_by_checker": [list(map(str, cch)) for cch in caught],
               "certs_verified": certs_ok, "certs_rejected": certs_bad,
               "elimination_pct": round(elim, 2), "total": TOTAL,
               "seed": 20261009},
              open("falsification_results_2000.json", "w"), indent=1, ensure_ascii=False)
    print("\nresultado gravado em falsification_results_2000.json")
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
