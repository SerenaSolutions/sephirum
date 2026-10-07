#!/usr/bin/env python3
"""
FALSIFICATION EXPERIMENT — 200 problemas adversariais, 4 familias (50 cada).

Meta do charter: 0 certificados falsos. Politica soundness-first:
falso negativo (UNKNOWN onde dava pra decidir) e tolerado e CONTADO;
UM falso positivo (decisao errada certificada) derruba o experimento (exit 1).

Verdade-terreno INDEPENDENTE por metodo diferente do motor:
- threshold_sum : aritmetica inteira exata (bigint)
- mean_partial  : Fraction exata (o motor usa float -> alvo favorito)
- triangular_det: algoritmo de Bareiss (o motor usa Laplace/produto)
- geo           : somatorio direto (o motor usa forma fechada)

Armadilhas incluidas de proposito: igualdades exatas nos limiares,
limites degenerados (lo==hi), valores enormes que quebram float,
operadores nao-">' com incognita, suposicao mentirosa, fora de dominio.
"""
import json
import sys
from fractions import Fraction

from nexa_core import parse_nexa, NCA
from nexa_checker import verify


def det_bareiss(M):
    """Determinante exato por Bareiss (fracao inteira) — metodo != Laplace."""
    M = [row[:] for row in M]
    n, sign, prev = len(M), 1, 1
    if n == 0:
        return 1
    for k in range(n - 1):
        if M[k][k] == 0:
            swap = next((i for i in range(k + 1, n) if M[i][k] != 0), None)
            if swap is None:
                return 0
            M[k], M[swap] = M[swap], M[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                M[i][j] = (M[i][j] * M[k][k] - M[i][k] * M[k][j]) // prev
            M[i][k] = 0
        prev = M[k][k]
    return sign * M[n - 1][n - 1]


CASES = []


def add(family, name, src, mode, truth):
    CASES.append({"family": family, "name": name, "src": src,
                  "mode": mode, "truth": truth})


def src_sum(terms, thr, op=">", unk=None, x_val=None, assumption=True):
    s = ("ASK:\n    question: sum %s %s\nCONTRACT:\n    absolute_error: 0\n"
         "MODEL:\n    type: threshold_sum\n    terms: %s\n" %
         (op, thr, ", ".join(map(str, terms))))
    if assumption:
        s += "    assumption: terms_nonnegative\n"
    if unk:
        s += "    unknown: x in %d..%d\n" % unk
        if x_val is not None:
            s += "    unknown_value: %d\n" % x_val
    return s


def src_mean(known, u, bounds, thr, op=">"):
    s = ("ASK:\n    question: mean %s %s\nMODEL:\n    type: mean_partial\n"
         "    known: %s\n    unknown_count: %d\n" %
         (op, thr, ", ".join(map(str, known)), u))
    s += "    bounds: %s\n" % bounds if bounds != "none" else "    bounds: none\n"
    return s


def src_det(M, thr, op=">"):
    return ("ASK:\n    question: det %s %s\nMODEL:\n    type: triangular_det\n"
            "    matrix: %s\n" %
            (op, thr, "; ".join(",".join(map(str, r)) for r in M)))


def src_geo(r, n, thr, op=">"):
    return ("ASK:\n    question: sum %s %s\nMODEL:\n    type: geometric_series\n"
            "    r: %s\n    n: %d\n" % (op, thr, r, n))


# ══ F1: threshold_sum ══════════════════════════════════════════════
def f1():
    fam = "threshold_sum"
    # igualdades e vizinhanças exatas do limiar
    t = [5, 3, 8]
    add(fam, "eq", src_sum(t, 16), "decided", False)          # 16 > 16 = F
    add(fam, "minus1", src_sum(t, 15), "decided", True)
    add(fam, "plus1", src_sum(t, 17), "decided", False)
    add(fam, "geq_eq", src_sum(t, 16, ">="), "decided", True)
    add(fam, "geq_above", src_sum(t, 17, ">="), "decided", False)
    add(fam, "lt_above", src_sum(t, 17, "<"), "decided", True)
    add(fam, "eq_plain", src_sum([5, 5], 10, "=="), "decided", True)
    add(fam, "leq_plain", src_sum([5, 5], 10, "<="), "decided", True)
    # zeros e negativos
    add(fam, "zeros_eq", src_sum([0, 0, 0], 0), "decided", False)
    add(fam, "zeros_neg", src_sum([0, 0, 0], -1), "decided", True)
    add(fam, "zero_mid", src_sum([0, 5, 0], 4), "decided", True)
    add(fam, "negthr", src_sum([1, 2], -5), "decided", True)
    add(fam, "no_assumption_neg", src_sum([-5, -3], -10, assumption=False),
        "decided", True)
    # gigantes exatos (bigint)
    H = [10 ** 15, 10 ** 15, 7]
    add(fam, "huge_eq", src_sum(H, 2000000000000007), "decided", False)
    add(fam, "huge_minus", src_sum(H, 2000000000000006), "decided", True)
    # termo único e parada antecipada
    add(fam, "single", src_sum([7], 6), "decided", True)
    add(fam, "single_eq", src_sum([7], 7), "decided", False)
    add(fam, "long_early", src_sum([1, 2, 3, 0, 0, 0, 0, 0], 5), "decided", True)
    add(fam, "deep_zero", src_sum([9, 0, 0, 0], 8), "decided", True)
    add(fam, "geq_partial_eq", src_sum([5, 5, 0], 10, ">="), "decided", True)
    # incógnita degenerada e limiares de bound
    b = [10, 20]
    add(fam, "unk_degen_T", src_sum(b, 34, unk=(5, 5)), "decided", True)
    add(fam, "unk_degen_F", src_sum(b, 35, unk=(5, 5)), "decided", False)
    add(fam, "unk_lo_boundary", src_sum(b, 34, unk=(5, 9)), "decided", True)
    add(fam, "unk_hi_boundary", src_sum(b, 39, unk=(5, 9)), "decided", False)
    add(fam, "unk_zero_range_T", src_sum([5, 5], 9, unk=(0, 0)), "decided", True)
    add(fam, "unk_zero_range_F", src_sum([5, 5], 10, unk=(0, 0)), "decided", False)
    # straddle sem oráculo: UNKNOWN é o ÚNICO acerto
    for i, (tt, lo, hi, thr) in enumerate([
            ([1, 1], 0, 10, 5), ([2, 2, 2, 2], 0, 1, 8), ([50], 10, 60, 80),
            ([1, 2, 3], 4, 9, 10), ([7], 0, 3, 7), ([1000000], 0, 1000000000, 1000005)]):
        add(fam, "straddle_%d" % i, src_sum(tt, thr, unk=(lo, hi)),
            "undecidable", None)
    # straddle com oráculo
    add(fam, "oracle_lo", src_sum([2, 2, 2, 2], 8, unk=(0, 1), x_val=0),
        "decided", False)
    add(fam, "oracle_hi", src_sum([2, 2, 2, 2], 8, unk=(0, 1), x_val=1),
        "decided", True)
    add(fam, "oracle_eq", src_sum([5, 5], 10, unk=(0, 10), x_val=0),
        "decided", False)
    add(fam, "oracle_mid", src_sum([5, 5], 10, unk=(0, 10), x_val=5),
        "decided", True)
    add(fam, "oracle_huge", src_sum([1000000], 1000005, unk=(0, 10**12), x_val=0),
        "decided", False)
    # bound já decide antes do residual (oráculo irrelevante)
    add(fam, "bounds_decide_F", src_sum([5, 5], 20, unk=(0, 4), x_val=7),
        "decided", False)
    add(fam, "bounds_decide_T", src_sum([5, 5], 9, unk=(10, 20), x_val=1),
        "decided", True)
    # ARMADILHAS: operadores não-">' com incógnita — o motor antigo
    # ignorava a incógnita e decidia pela soma parcial
    add(fam, "geq_unk_negx", src_sum([10], 10, ">=", unk=(-5, -1)),
        "decided", False)     # verdade: soma+x em 5..9 < 10
    add(fam, "lt_unk_straddle", src_sum([3, 4], 8, "<", unk=(0, 10)),
        "undecidable", None)  # verdade: 7<8 mas 17 não
    add(fam, "eq_unk", src_sum([7], 7, "==", unk=(0, 10)),
        "undecidable", None)
    add(fam, "geq_unk_decide_T", src_sum([10, 10], 25, ">=", unk=(5, 9)),
        "decided", True)      # verdade: base+lo = 25 >= 25
    # suposição mentirosa: o checker tem que rejeitar o certificado
    add(fam, "lying_assumption", src_sum([5, -100], 4), "decided", False)
    add(fam, "neg_below", src_sum([1], -2, unk=(0, 3)), "decided", True)
    add(fam, "unk_wide_T", src_sum([100, 200], 50, unk=(0, 1000)), "decided", True)
    add(fam, "unk_wide_F", src_sum([1, 1], 5000, unk=(0, 100)), "decided", False)
    add(fam, "big_oracle_eq", src_sum([10**9, 10**9], 2*10**9, unk=(0, 10), x_val=0),
        "decided", False)
    add(fam, "zeros_partial", src_sum([0, 3, 0], 2), "decided", True)
    add(fam, "neg_terms_eq", src_sum([-1, -1], -2, assumption=False), "decided", False)


# ══ F2: mean_partial ═══════════════════════════════════════════════
def mean_truth(known, u, lo, hi, thr):
    """Verdade exata por Fraction; o motor usa float."""
    tot, N = sum(known), len(known) + u
    if lo is None:
        return "undecidable", None
    m_lo = Fraction(tot + u * lo, N)
    m_hi = Fraction(tot + u * hi, N)
    if m_lo > thr:
        return "decided", True
    if m_hi <= thr:
        return "decided", False
    return "undecidable", None


def f2():
    fam = "mean_partial"
    # bounds none: UNKNOWN é o único acerto
    for i, k in enumerate([[40, 50, 60], [10, 20], [55], [30, 40, 50, 60], [1, 2, 3]]):
        add(fam, "none_%d" % i, src_mean(k, 5, "none", 50), "undecidable", None)
    # contorno exato
    add(fam, "hi_eq_thr", src_mean([40, 50], 5, "45..55", 50), "decided", False)
    add(fam, "lo_eq_thr_straddle", src_mean([41, 50], 5, "45..55", 50),
        "undecidable", None)
    add(fam, "degen_eq_thr", src_mean([45, 55], 5, "50..50", 50), "decided", False)
    add(fam, "degen_above", src_mean([45, 55], 5, "51..51", 50), "decided", True)
    add(fam, "degen_below", src_mean([45, 55], 5, "49..49", 50), "decided", False)
    add(fam, "hi_eq_thr_neg", src_mean([-40, -50], 5, "-55..-45", -50),
        "decided", False)
    # decisões normais (float e Fraction concordam)
    for i, (k, u, bs, thr, m, tv) in enumerate([
            ([60, 70, 80], 5, "50..60", 50, "decided", True),
            ([60, 70, 80], 5, "10..20", 50, "decided", False),
            ([10, 20, 30], 2, "80..90", 50, "decided", False),
            ([10, 20, 30], 2, "1..2", 50, "decided", False),
            ([100], 9, "0..10", 20, "decided", False),
            ([100], 9, "30..40", 20, "decided", True),
            ([0, 0, 0], 5, "-10..-5", -3, "decided", False),
            ([0, 0, 0], 5, "-10..10", 0, "undecidable", None),
            ([5, 5, 5, 5, 5, 5, 5], 3, "4..6", 5, "undecidable", None),
            ([5, 5, 5, 5, 5, 5, 5], 3, "6..8", 5, "decided", True),
            ([5, 5, 5, 5, 5, 5, 5], 3, "1..2", 5, "decided", False)]):
        mode, truth = (m, tv) if m != "undecidable" else mean_truth(k, u, 1, 2, 50)
        add(fam, "norm_%d" % i, src_mean(k, u, bs, thr), m, tv)
    # pequenas frações exatas (N=7, dízimas): float e Fraction devem concordar
    add(fam, "seventh_above", src_mean([1, 1, 1, 1, 1, 1], 1, "2..3", 1),
        "decided", True)      # media min = 8/7 > 1
    add(fam, "seventh_below", src_mean([1, 1, 1, 1, 1, 1], 1, "0..1", 1),
        "decided", False)     # media max = 7/7 <= 1
    add(fam, "seventh_straddle", src_mean([0, 0, 0, 0, 0, 0], 1, "0..7", 1),
        "decided", False)
    # ARMADILHAS DE PRECISÃO: N=3, magnitude ~1e16, float perde o dígito que decide
    T16 = 10 ** 16
    # (a) media real = T16 + 1/3 (verdade T); float: (3e16+1)->3e16, /3 = T16 -> decide F
    add(fam, "trap_float_F", src_mean([T16, T16 + 1], 1,
                                      "10000000000000000..10000000000000000", T16),
        "decided", True)
    # (b) media real = T16 - 1/3 (verdade F); float tambem decide F — concordam
    add(fam, "trap_float_ok", src_mean([T16 - 1, T16], 1,
                                       "10000000000000000..10000000000000000", T16),
        "decided", False)
    # (c) media real = T16 + 5/3 (verdade T); float = T16 + 4/3 -> tambem T
    add(fam, "trap_float_T", src_mean([T16, T16], 1,
                                      "10000000000000005..10000000000000005", T16),
        "decided", True)
    # u = 0 (tudo conhecido): verdade decidível; UNKNOWN é falso negativo tolerado
    add(fam, "u0_mean", src_mean([80, 90, 100], 0, "0..10", 50), "decided", True)
    add(fam, "u0_eq", src_mean([50, 50], 0, "0..10", 50), "decided", False)
    # operador ">=": motor só trata ">": UNKNOWN (falso negativo tolerado)
    add(fam, "geq_decidable", src_mean([80, 90], 5, "60..70", 50, ">="),
        "decided", True)
    add(fam, "geq_refutable", src_mean([10, 20], 5, "1..2", 50, ">="),
        "decided", False)
    add(fam, "none_more1", src_mean([60, 70], 5, "none", 50), "undecidable", None)
    add(fam, "none_more2", src_mean([49, 51], 5, "none", 50), "undecidable", None)
    add(fam, "none_more3", src_mean([0, 0], 5, "none", 0), "undecidable", None)
    add(fam, "b1", src_mean([10, 20, 30], 3, "30..40", 40), "decided", False)
    add(fam, "b2", src_mean([10, 20, 30], 3, "80..90", 40), "decided", True)
    add(fam, "b3", src_mean([1, 2, 3, 4], 4, "5..8", 10), "decided", False)
    add(fam, "b4", src_mean([9, 9, 9, 9], 4, "8..9", 10), "decided", False)
    add(fam, "b5", src_mean([9, 9, 9, 9], 4, "11..12", 10), "decided", True)
    add(fam, "b6", src_mean([9, 9, 9, 9], 4, "11..13", 10), "undecidable", None)
    add(fam, "b7", src_mean([2, 4, 6, 8], 2, "60..70", 20), "decided", True)
    add(fam, "b8", src_mean([100, 200, 300], 5, "0..100", 150), "decided", False)
    add(fam, "b9", src_mean([100, 200, 300], 5, "150..200", 150), "decided", True)
    add(fam, "b10", src_mean([100, 200, 300], 5, "100..300", 150), "undecidable", None)
    add(fam, "b11", src_mean([5], 1, "16..17", 10), "decided", True)
    add(fam, "b12", src_mean([5], 1, "13..14", 10), "decided", False)
    add(fam, "b13", src_mean([5], 1, "15..16", 10), "undecidable", None)
    add(fam, "b14", src_mean([0], 1, "10..10", 4), "decided", True)
    add(fam, "b15", src_mean([0, 0, 0, 0], 2, "20..20", 10), "decided", False)


# ══ F3: triangular_det ═════════════════════════════════════════════
def f3():
    fam = "triangular_det"
    I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    add(fam, "identity_eq", src_det(I3, 1), "decided", False)   # det=1
    add(fam, "identity_T", src_det(I3, 0), "decided", True)
    S3 = [[2, 0, 0], [0, 0, 0], [0, 0, 3]]                       # singular
    add(fam, "singular_eq", src_det(S3, 0), "decided", False)
    add(fam, "singular_T", src_det(S3, -1), "decided", True)
    U3 = [[2, 1, 7], [0, 3, 4], [0, 0, 5]]                       # det=30
    add(fam, "upper_eq", src_det(U3, 30), "decided", False)
    add(fam, "upper_T", src_det(U3, 29), "decided", True)
    L3 = [[4, 0, 0], [1, 5, 0], [2, 3, 6]]                       # det=120
    add(fam, "lower_eq", src_det(L3, 120), "decided", False)
    add(fam, "lower_T", src_det(L3, 119), "decided", True)
    add(fam, "lower_geq", src_det(L3, 120, ">="), "decided", True)
    N3 = [[-2, 0, 0], [0, -3, 0], [0, 0, -4]]                    # det=-24
    add(fam, "neg_det_F", src_det(N3, 0), "decided", False)
    add(fam, "neg_det_T", src_det(N3, -25), "decided", True)
    add(fam, "neg_det_eq", src_det(N3, -24), "decided", False)
    mixed = [[1, 2, 3], [4, 5, 6], [7, 8, 10]]                   # det calculado (Bareiss)
    dm = det_bareiss(mixed)
    add(fam, "nont1_eq", src_det(mixed, dm), "decided", False)
    add(fam, "nont1_T", src_det(mixed, dm - 1), "decided", True)
    nont2 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]                    # det=0
    add(fam, "nont2_eq", src_det(nont2, 0), "decided", False)
    add(fam, "nont2_neg", src_det(nont2, -1), "decided", True)
    # 1x1
    add(fam, "one_eq", src_det([[7]], 7), "decided", False)
    add(fam, "one_T", src_det([[7]], 6), "decided", True)
    add(fam, "one_neg", src_det([[-5]], -6), "decided", True)
    # grandes inteiros exatos
    G3 = [[10 ** 9, 5, 7], [0, 10 ** 9, 9], [0, 0, 10 ** 9]]
    add(fam, "big_eq", src_det(G3, 10 ** 27), "decided", False)
    add(fam, "big_T", src_det(G3, 10 ** 27 - 1), "decided", True)
    # mais casos de matrices gerais 3x3/4x4/5x5
    mats = [
        [[3, 1], [1, 2]], [[5, 7], [2, 4]], [[6, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[2, 0, 1], [0, 3, 0], [1, 0, 2]], [[1, 1, 1], [1, 2, 3], [1, 3, 6]],
        [[9, 8, 7], [6, 5, 4], [3, 2, 1]],
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 17]],
        [[2, 1, 0, 0], [1, 2, 1, 0], [0, 1, 2, 1], [0, 0, 1, 2]],
        [[1, 0, 0, 0], [0, 2, 0, 0], [0, 0, 3, 0], [0, 0, 0, 4]],
        [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15],
         [16, 17, 18, 19, 20], [21, 22, 23, 24, 26]],
        [[0, 1, 2], [3, 4, 5], [6, 7, 9]], [[-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[7, 3], [2, 1]], [[100, 1], [1, 100]],
        [[1, 1], [1, 0]], [[4, 1, 1], [1, 4, 1], [1, 1, 4]],
        [[2, 3, 5], [7, 11, 13], [17, 19, 23]],
        [[1, 0, 5], [0, 1, 0], [0, 0, 1]], [[8, 0, 0, 0], [1, 8, 0, 0],
                                           [0, 1, 8, 0], [0, 0, 1, 8]],
        [[3, 1, 1, 1], [1, 3, 1, 1], [1, 1, 3, 1], [1, 1, 1, 3]],
    ]
    def _n():
        return len([c for c in CASES if c["family"] == fam])
    for i, M in enumerate(mats):
        if _n() >= 45:
            break
        d = det_bareiss(M)
        add(fam, "m%02d_eq" % i, src_det(M, d), "decided", False)
        add(fam, "m%02d_T" % i, src_det(M, d - 1), "decided", True)
    # fechando 50: tres armadilhas extras de sinal
    for i, M in enumerate([[[0, 1], [1, 0]], [[0, 2], [3, 0]], [[5, -1], [-2, 3]]]):
        d = det_bareiss(M)
        add(fam, "swap%d_eq" % i, src_det(M, d), "decided", False)
    add(fam, "one_geq", src_det([[7]], 7, ">="), "decided", True)
    add(fam, "one_leq", src_det([[-5]], -5, "<="), "decided", True)


# ══ F4: geo ═══════════════════════════════════════════════════════
def geo_truth(r, n):
    """Somatorio direto exato — metodo != forma fechada do motor."""
    return sum(r ** i for i in range(n + 1))


def f4():
    fam = "geo"
    plan = []
    # r=1: soma = n+1
    for n in [0, 1, 5, 10, 100]:
        plan.append((1, n))
    # r=2: soma = 2^(n+1)-1
    for n in [0, 1, 4, 10, 20, 40]:
        plan.append((2, n))
    # r=3 grandes
    for n in [1, 5, 25, 100, 500]:
        plan.append((3, n))
    # r=0: soma = 1
    plan += [(0, 0), (0, 5), (0, 50)]
    # r=-1: paridade
    plan += [(-1, 0), (-1, 1), (-1, 10), (-1, 101), (-1, 100)]
    # r=-2
    plan += [(-2, 1), (-2, 2), (-2, 5), (-2, 10)]
    # r grandes exatos
    plan += [(10 ** 6, 3), (10 ** 9, 2)]
    # operadores variados
    plan += [(2, 5), (3, 3), (-1, 3), (5, 4), (7, 6)]
    seen = set()
    for i, (r, n) in enumerate(plan):
        if len([c for c in CASES if c["family"] == fam]) >= 40:
            break
        if (r, n) in seen:
            continue
        seen.add((r, n))
        s = geo_truth(r, n)
        add(fam, "g%02d_eq" % i, src_geo(r, n, s), "decided", False)      # eq
        add(fam, "g%02d_T" % i, src_geo(r, n, s - 1), "decided", True)
    # >= e ==
    add(fam, "geq_eq", src_geo(2, 4, 31, ">="), "decided", True)
    add(fam, "geq_above", src_geo(2, 4, 32, ">="), "decided", False)
    add(fam, "eqs", src_geo(3, 3, 40, "=="), "decided", True)
    add(fam, "eqs_wrong", src_geo(3, 3, 41, "=="), "decided", False)
    add(fam, "lt", src_geo(2, 10, 2048, "<"), "decided", True)
    add(fam, "geq3_eq", src_geo(1, 9, 10, ">="), "decided", True)
    add(fam, "lte", src_geo(2, 5, 64, "<="), "decided", True)
    add(fam, "eq_neg", src_geo(-1, 100, 1, "=="), "decided", True)
    add(fam, "lt_zero", src_geo(-1, 99, 0, "<"), "decided", False)
    add(fam, "geq_r0", src_geo(0, 7, 1, ">="), "decided", True)


f1(); f2(); f3(); f4()
assert len(CASES) == 200, "esperado 200 casos, obtidos %d" % len(CASES)


def main():
    wrong, false_neg, caught, unknown_ok = [], [], [], 0
    fam_stats = {}
    total_orig = total_req = 0
    certs_ok = certs_bad = 0
    for c in CASES:
        fam = c["family"]
        st = fam_stats.setdefault(fam, {"n": 0, "wrong": 0, "false_neg": 0,
                                        "caught": 0, "unknown_ok": 0})
        st["n"] += 1
        blocks = parse_nexa(c["src"])
        res = NCA(blocks, c["name"]).compile()
        ok, reason = verify(blocks, res["certificate"])
        cert = res.get("certificate", {})
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
    print("FALSIFICATION EXPERIMENT — 200 problemas adversariais, 4 famílias")
    print("=" * 70)
    for fam, st in fam_stats.items():
        print("%-15s n=%3d  falsos=%d  falsos-neg=%d  checker-caught=%d  UNKNOWN-ok=%d"
              % (fam, st["n"], st["wrong"], st["false_neg"], st["caught"], st["unknown_ok"]))
    print("-" * 70)
    print("certificados verificados: %d/200 | rejeitados (defesa agiu): %d"
          % (certs_ok, certs_bad))
    print("eliminação: %.1f%%  (orig=%d req=%d)" % (elim, total_orig, total_req))
    print("FALSOS CERTIFICADOS: %d   <- meta: 0" % len(wrong))
    for w in wrong:
        print("  !!", w)
    print("falsos negativos (tolerados): %d" % len(false_neg))
    print("mentiras capturadas pelo checker: %d" % len(caught))
    json.dump({"per_family": fam_stats, "wrong": [list(map(str, w)) for w in wrong],
               "false_negatives": [list(map(str, f)) for f in false_neg],
               "caught_by_checker": [list(map(str, cch)) for cch in caught],
               "certs_verified": certs_ok, "certs_rejected": certs_bad,
               "elimination_pct": round(elim, 2)},
              open("falsification_results_200.json", "w"), indent=1, ensure_ascii=False)
    print("\nresultado gravado em falsification_results_200.json")
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
