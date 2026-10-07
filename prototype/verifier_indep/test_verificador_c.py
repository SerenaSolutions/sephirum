#!/usr/bin/env python3
"""
ZEPHIRUM — BATERIA DO VERIFICADOR INDEPENDENTE (C).
====================================================

A ponte entre a referência Python e o verificador zverify.c:

  1. gera casos REAIS a partir dos recibos da VM Python (boot e naive);
  2. o verificador C re-deriva cada veredito, recalcula cada INPUT_HASH
     (SHA-256 próprio) e audita os custos normativos §5;
  3. certificados FORJADOS são apresentados — e têm de ser rejeitados.

Concordância entre linguagens = o padrão atravessa compiladores e
máquinas ("além do espaço"). Se Python e C discordam, é FALHA do padrão.
"""
import os
import random
import subprocess
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(HERE)
sys.path.insert(0, PROTO)

from zephirum_boot import boot_decide            # gauss (fatia 1)
from zephirum_boot_b2 import geo_decide, mean_decide  # fatia 2
from zephirum_boot_b2 import _input_hash

BIN = os.path.join(HERE, "zverify")
SRC = os.path.join(HERE, "zverify.c")


def _build():
    if not os.path.exists(BIN) or os.path.getmtime(SRC) > os.path.getmtime(BIN):
        r = subprocess.run(["gcc", "-O2", "-std=c11", "-Wall", "-Wextra",
                            "-o", BIN, SRC], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("gcc falhou: %s" % r.stderr[:400])


def tsv(family, op, thr, p1, p2, lane, expected, input_hash,
        units, budget, data_string):
    return "\t".join([family, op, str(thr), p1, p2, lane,
                      "1" if expected is True else "0",
                      input_hash, str(units), str(budget), data_string])


def data_str(values):
    return "|".join(str(v) for v in values)


def main():
    _build()
    random.seed(777)
    OPS = [">", "<", ">=", "<="]
    honest = []

    # ---- 150 casos gauss (boot + alguns naive) de recibos REAIS
    for i in range(150):
        n = random.randint(3, 400)
        op = random.choice(OPS)
        total = Fraction(n * (n + 1), 2)
        thr = random.randint(max(0, int(total // 3) - 2), int(total * 2) + 10)
        plan, boot, naive = boot_decide(n, op, thr)
        rec = boot if i % 3 else naive
        lane = "b" if i % 3 else "n"
        honest.append(tsv("gauss", op, thr, str(n), "", lane,
                          rec["answer"], rec["input_hash"],
                          rec["units"], rec["budget"],
                          data_str(plan[("boot" if lane == "b"
                                         else "naive")]["data"])))
    # ---- 100 casos geométricos (boot)
    for i in range(100):
        q = random.randint(2, 9)
        p = random.randint(-(q - 1), q - 1) or 1
        r = Fraction(p, q)
        a = Fraction(random.choice([1, 2, 3, 5, 7, 10, -1, -2, -3]))
        total = a / (1 - r)
        t_lo = int(total) - int(abs(total)) - 5
        t_hi = int(total) + int(abs(total)) + 5
        if t_lo >= t_hi:
            t_lo, t_hi = t_hi + 1, t_hi + 10
        op = random.choice(OPS)
        for _ in range(200):
            thr = random.randint(t_lo, t_hi)
            naive_sum = a * (1 - r ** 12) / (1 - r)
            j = {">": total > thr, "<": total < thr,
                 ">=": total >= thr, "<=": total <= thr}[op]
            nv = {">": naive_sum > thr, "<": naive_sum < thr,
                  ">=": naive_sum >= thr, "<=": naive_sum <= thr}[op]
            if j == nv:
                break
        else:
            continue
        plan, boot, _ = geo_decide(a, r, op, thr)
        honest.append(tsv("geo", op, thr, "%d/%d" % (a.numerator, a.denominator),
                          "%d/%d" % (r.numerator, r.denominator), "b",
                          boot["answer"], boot["input_hash"],
                          boot["units"], boot["budget"],
                          data_str(plan["boot"]["data"])))
    # ---- 100 casos média (boot) + 50 naive
    for i in range(100):
        n = random.randint(2, 200)
        op = random.choice(OPS)
        total = Fraction(n + 1, 2)
        thr = random.randint(max(0, int(total // 3) - 2), int(total * 2) + 10)
        plan, boot, naive = mean_decide(n, op, thr)
        honest.append(tsv("mean", op, thr, str(n), "", "b",
                          boot["answer"], boot["input_hash"],
                          boot["units"], boot["budget"],
                          data_str(plan["boot"]["data"])))
    for i in range(50):
        n = random.randint(2, 40)
        op = random.choice(OPS)
        total = Fraction(n + 1, 2)
        thr = random.randint(max(0, int(total // 3) - 2), int(total * 2) + 10)
        plan, boot, naive = mean_decide(n, op, thr)
        honest.append(tsv("mean", op, thr, str(n), "", "n",
                          naive["answer"], naive["input_hash"],
                          naive["units"], naive["budget"],
                          data_str(plan["naive"]["data"])))

    honest_file = os.path.join(HERE, "casos_honestos.tsv")
    with open(honest_file, "w", encoding="utf-8") as fh:
        fh.write("\n".join(honest) + "\n")
    p = subprocess.run([BIN, honest_file], capture_output=True, text=True)
    total_casos = len(honest)
    if p.returncode != 0:
        print(p.stdout[-800:])
        raise SystemExit("HONESTOS: verificador C rejeitou caso legítimo")
    ok_line = [l for l in p.stdout.splitlines() if l.startswith("RESUMO")]
    print("HONESTOS: %s — concordância Python<->C integral"
          % ok_line[0].replace("RESUMO: ", ""))

    # ---- certificados forjados: cada um TEM de ser rejeitado
    forjados = [
        # veredito invertido
        tsv("gauss", ">", 10, "5", "", "b", False,
            _input_hash([5]), 2, 2, "5"),
        # INPUT_HASH trocado (fonte adulterada)
        tsv("mean", ">", 5, "10", "", "b", True,
            _input_hash([11]), 1, 1, "10"),
        # orçamento furado: 3 unidades sob certificado de 2
        tsv("geo", ">", 1, "1/1", "1/2", "b", True,
            _input_hash([Fraction(1), Fraction(1, 2)]), 3, 2,
            "1|1/2"),
        # custo normativo violado: boot de gauss com 3 unidades
        tsv("gauss", ">", 10, "5", "", "b", True,
            _input_hash([5]), 3, 5, "5"),
        # série divergente apresentada como legítima
        tsv("geo", ">", 1, "1/1", "3/2", "b", True,
            _input_hash([Fraction(1), Fraction(3, 2)]), 2, 2,
            "1|3/2"),
    ]
    forge_file = os.path.join(HERE, "casos_forjados.tsv")
    with open(forge_file, "w", encoding="utf-8") as fh:
        fh.write("\n".join(forjados) + "\n")
    rejeitados = 0
    for i in range(len(forjados)):
        one = os.path.join(HERE, "_forge_%d.tsv" % i)
        with open(one, "w", encoding="utf-8") as fh:
            fh.write(forjados[i] + "\n")
        p = subprocess.run([BIN, one], capture_output=True, text=True)
        if p.returncode != 0:
            rejeitados += 1
        os.remove(one)
    assert rejeitados == len(forjados), \
        "FORJADOS: %d/%d rejeitados — algum passou!" % (rejeitados, len(forjados))
    print("FORJADOS: %d/%d rejeitados pelo verificador C"
          % (rejeitados, len(forjados)))

    os.remove(honest_file)
    os.remove(forge_file)
    print("RESULTADO: PASS — verificador independente C concorda com a "
          "referência Python em %d casos e rejeita %d/%d forjados"
          % (total_casos, rejeitados, len(forjados)))


if __name__ == "__main__":
    main()
