#!/usr/bin/env python3
"""
STRESS TEST — A SIFR/NCA funciona mesmo?
500 problemas aleatorios, 4 familias, ground truth por forca bruta.
Mede: decisoes corretas, taxa de eliminacao, NetBenefit agregado,
e SOUNDNESS: 0 certificados falsos aceitos; N certificados forjados rejeitados.
Resultado gravado em stress_results.json (para o capitulo 6 do livro).
"""
import json
import random
import sys

from nexa_core import parse_nexa, NCA
from nexa_checker import verify

import os
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
random.seed(42)  # reprodutibilidade


def make_case():
    r = random.random()
    terms = [random.randint(1, 100) for _ in range(random.randint(3, 12))]
    if r < 0.40:
        kind = "plain"          # soma com limiar, termos conhecidos
        thr = random.randint(1, sum(terms) + 10)
        return kind, terms, None, thr, None
    if r < 0.70:
        kind = "oracle"         # incognita com oraculo (residuo executavel)
        lo = random.randint(0, 50)
        hi = lo + random.randint(10, 500)
        true_x = random.randint(lo, hi)
        thr = random.randint(1, sum(terms) + lo + 5)
        return kind, terms, (lo, hi), thr, true_x
    if r < 0.90:
        kind = "blind"          # incognita sem oraculo (UNKNOWN possivel)
        lo = random.randint(0, 50)
        hi = lo + random.randint(10, 800)
        thr = random.randint(1, sum(terms) + lo + 5)
        return kind, terms, (lo, hi), thr, None
    known = [random.randint(30, 80) for _ in range(5)]
    if random.random() < 0.5:
        return "mean_none", known, None, 50, None   # impossivel: UNKNOWN esperado
    blo = random.randint(40, 55)
    bhi = blo + random.randint(1, 8)
    return "mean_bounds", known, (blo, bhi), 50, None


def build_src(kind, terms, unk, thr, x_val):
    if kind in ("plain", "oracle", "blind"):
        s = ("ASK:\n    question: sum > %d\nCONTRACT:\n    absolute_error: 0\n"
             "MODEL:\n    type: threshold_sum\n    terms: %s\n"
             "    assumption: terms_nonnegative\n"
             % (thr, ", ".join(map(str, terms))))
        if unk:
            s += "    unknown: x in %d..%d\n" % unk
            if x_val is not None:
                s += "    unknown_value: %d\n" % x_val
        return s
    if kind == "mean_none":
        return ("ASK:\n    question: mean > %d\nMODEL:\n    type: mean_partial\n"
                "    known: %s\n    unknown_count: 5\n    bounds: none\n"
                % (thr, ", ".join(map(str, terms))))
    return ("ASK:\n    question: mean > %d\nMODEL:\n    type: mean_partial\n"
            "    known: %s\n    unknown_count: 5\n    bounds: %d..%d\n"
            % (thr, ", ".join(map(str, terms)), unk[0], unk[1]))


def ground_truth(kind, terms, unk, thr, x_val):
    """Verdade por forca bruta; para casos 'blind', tolera UNKNOWN."""
    if kind == "plain":
        return ("decided", sum(terms) > thr)
    if kind == "oracle":
        return ("decided", sum(terms) + x_val > thr)
    if kind == "blind":
        lo_truth = sum(terms) + unk[0] > thr
        hi_truth = sum(terms) + unk[1] > thr
        if lo_truth == hi_truth:
            return ("decided", lo_truth)
        return ("undecidable", None)  # UNKNOWN e o UNICO acerto possivel
    if kind == "mean_none":
        return ("undecidable", None)
    lo_m = (sum(terms) + 5 * unk[0]) / 10.0
    hi_m = (sum(terms) + 5 * unk[1]) / 10.0
    if lo_m > thr:
        return ("decided", True)
    if hi_m <= thr:
        return ("decided", False)
    return ("undecidable", None)


def main():
    counts = {"DECIDED_WITHOUT_EXECUTION": 0, "DECIDED_BY_REDUCTION": 0,
              "RESIDUAL_COMPUTATION_REQUIRED": 0, "FULL_EXECUTION_REQUIRED": 0,
              "UNKNOWN": 0}
    total_original = total_required = total_eliminated = 0
    net_total = 0.0
    wrong_answers = 0
    certs_ok = certs_bad = 0
    forged = []

    for i in range(N):
        kind, terms, unk, thr, x_val = make_case()
        blocks = parse_nexa(build_src(kind, terms, unk, thr, x_val))
        res = NCA(blocks, "case_%03d" % i).compile()
        ok, reason = verify(blocks, res["certificate"])
        if ok:
            certs_ok += 1
        else:
            certs_bad += 1
            print("CERT REJECTED (case %d, %s): %s" % (i, kind, reason))

        mode, truth = ground_truth(kind, terms, unk, thr, x_val)
        if mode == "decided":
            if res["answer"] != truth:
                wrong_answers += 1
                print("WRONG ANSWER case %d (%s): engine=%s truth=%s status=%s"
                      % (i, kind, res["answer"], truth, res["status"]))
        else:  # undecidable: UNKNOWN e o unico acerto
            if res["status"] != "UNKNOWN":
                wrong_answers += 1
                print("FALSE DECISION case %d (%s): status=%s (deveria ser UNKNOWN)"
                      % (i, kind, res["status"]))

        counts[res["status"]] += 1
        if res["status"] != "UNKNOWN":
            total_original += res["original"]
            total_required += res["required"]
            total_eliminated += res["eliminated"]
        net_total += res["net_benefit"]

        # coleta certificados forjaveis (com evidencia numerica)
        if len(forged) < 40 and res["status"] in (
                "DECIDED_BY_REDUCTION", "DECIDED_WITHOUT_EXECUTION"):
            forged.append((blocks, res["certificate"]))

    # ATAQUE DE SOUNDNESS: forjar 20 certificados validos
    import copy
    tamper_keys = ("witness_sum", "base_sum", "mean_lo", "mean_hi",
                   "witness_terms", "evaluated_value")
    attacks = forged[:20]
    rejected = 0
    for blocks, cert in attacks:
        t = copy.deepcopy(cert)
        for k in tamper_keys:
            if k in t["EVIDENCE"]:
                if k == "witness_terms":
                    t["EVIDENCE"][k] = [v + 1 for v in t["EVIDENCE"][k]]
                else:
                    t["EVIDENCE"][k] = t["EVIDENCE"][k] + 1
                break
        ok, _ = verify(blocks, t)
        rejected += 0 if ok else 1

    decided = N - counts["UNKNOWN"]
    elim_ratio = (100.0 * total_eliminated / total_original
                  if total_original else 0.0)
    results = {
        "seed": 42, "N": N,
        "counts": counts,
        "decided": decided,
        "wrong_answers": wrong_answers,
        "certificates_verified": certs_ok, "certificates_rejected": certs_bad,
        "forged_attacks": len(attacks), "forged_rejected": rejected,
        "total_original_units": total_original,
        "total_executed_units": total_required,
        "total_eliminated_units": total_eliminated,
        "elimination_ratio_pct": round(elim_ratio, 2),
        "aggregate_net_benefit": round(net_total, 2),
        "false_elimination_rate": (wrong_answers / N),
    }
    with open("stress_results_%d.json" % N, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))
    verdict = (wrong_answers == 0 and certs_bad == 0
               and rejected == len(attacks))
    print("\nVEREDICTO:", "SOUNDNESS CONFIRMADA - 0 respostas erradas,"
          " 0 certificados falsos, %d/%d forjados rejeitados"
          % (rejected, len(attacks)) if verdict else
          "!!! FALSIFICADA: revisar casos acima !!!")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
