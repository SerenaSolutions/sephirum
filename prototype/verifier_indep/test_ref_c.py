#!/usr/bin/env python3
"""
BATERIA ZREF — motor de referência em C puro lê a FONTE e decide.
==================================================================

O passo concreto para EXCLUIR o Python: `verifier_indep/zref` é um
binário autônomo que abre o ficheiro ZEPHIRUM (blocos ASK/CONTRACT/
MODEL), decide a pergunta com aritmética exata própria (__int128)
e emite o recibo normativo (VERDICT/HASH/UNITS).

Esta bateria cruza o motor C contra os oráculos Python em 200 fontes
(gauss, geométrica infinita, média, geométrica finita, emaranhamento):
mesmo veredito, mesmo INPUT_HASH, mesmas unidades normativas. E audita
os MUROS §12 do C: fora do muro o C diz OVERFLOW (nunca mente), recusas
estruturais dizem RECUSA — a mesma honestidade da referência.
"""
import os
import random
import subprocess
import sys
import tempfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from zephirum_boot import boot_decide
from zephirum_boot_b2 import geo_decide, mean_decide
from zephirum_boot_geo_fin import geofin_decide
from zephirum_transpiler_multi import transpile
from nexa_core import parse_nexa, NCA

ZREF = os.path.join(HERE, "zref")
ZSRC = os.path.join(HERE, "zref.c")
OPS = [">", "<", ">=", "<="]


def _run_zref(src):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".zeph",
                                     delete=False) as f:
        f.write(src)
        path = f.name
    try:
        r = subprocess.run([ZREF, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    out = {}
    for line in r.stdout.splitlines():
        if line.startswith("VERDICT"):
            out["verdict"] = int(line.split()[1])
        elif line.startswith("HASH"):
            out["hash"] = line.split()[1]
        elif line.startswith("UNITS"):
            out["units"] = int(line.split()[1])
    return out, r.returncode, r.stderr


def main():
    if not os.path.exists(ZREF) or \
            os.path.getmtime(ZSRC) > os.path.getmtime(ZREF):
        subprocess.run(["gcc", "-O2", "-std=gnu11", "-o", ZREF, ZSRC],
                      check=True)
    random.seed(31416)
    n_ok = n_refusa = n_overflow = 0

    # ---------------- gauss (40)
    for _ in range(40):
        n = random.randint(3, 400)
        op = random.choice(OPS)
        S = Fraction(n * (n + 1), 2)
        thr = random.randint(max(0, int(S // 3) - 2), int(S * 2) + 10)
        src = ("ASK:\n    question: sum %s %d\nCONTRACT:\n    "
               "absolute_error: 0\nMODEL:\n    type: gauss_series\n"
               "    n: %d\n" % (op, thr, n))
        _, boot, _ = boot_decide(n, op, thr)
        out, rc, err = _run_zref(src)
        assert rc == 0, err
        assert out["verdict"] == (1 if boot["answer"] is True else 0)
        assert out["hash"] == boot["input_hash"]
        assert out["units"] == boot["units"] == 2
        n_ok += 1

    # ---------------- média (40)
    for _ in range(40):
        n = random.randint(2, 200)
        op = random.choice(OPS)
        S = Fraction(n + 1, 2)
        thr = random.randint(max(0, int(S // 3) - 2), int(S * 2) + 10)
        src = ("ASK:\n    question: mean %s %d\nCONTRACT:\n    "
               "absolute_error: 0\nMODEL:\n    type: arithmetic_mean\n"
               "    n: %d\n" % (op, thr, n))
        _, boot, _ = mean_decide(n, op, thr)
        out, rc, err = _run_zref(src)
        assert rc == 0, err
        assert out["verdict"] == (1 if boot["answer"] is True else 0)
        assert out["hash"] == boot["input_hash"]
        assert out["units"] == boot["units"] == 1
        n_ok += 1

    # ---------------- geométrica infinita (40)
    for _ in range(40):
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
        thr = random.randint(t_lo, t_hi)
        src = ("ASK:\n    question: sum_inf %s %d\nCONTRACT:\n    "
               "absolute_error: 0\nMODEL:\n    type: geometric_inf\n"
               "    a: %s\n    r: %s\n" % (op, thr, a, r))
        _, boot, _ = geo_decide(a, r, op, thr)
        out, rc, err = _run_zref(src)
        assert rc == 0, err
        assert out["verdict"] == (1 if boot["answer"] is True else 0)
        assert out["hash"] == boot["input_hash"]
        assert out["units"] == boot["units"] == 2
        n_ok += 1

    # ---------------- geométrica finita (40) — dentro do muro 64 bits
    for _ in range(40):
        q = random.randint(1, 5)
        p = random.choice([x for x in range(-15, 16) if x != q])
        r = Fraction(p, q)
        n = random.randint(2, 12)
        S = sum(r ** k for k in range(n + 1))
        thr = random.randint(int(S) - 6, int(S) + 6)
        op = random.choice(OPS)
        src = ("ASK:\n    question: sum %s %d\nCONTRACT:\n    "
               "absolute_error: 0\nMODEL:\n    type: geometric_fin\n"
               "    r: %s\n    n: %d\n" % (op, thr, r, n))
        _, boot, _ = geofin_decide(r, n, op, thr)
        out, rc, err = _run_zref(src)
        assert rc == 0, (err, src)
        assert out["verdict"] == (1 if boot["answer"] is True else 0)
        assert out["hash"] == boot["input_hash"]
        assert out["units"] == boot["units"] == 2
        n_ok += 1

    # ---------------- emaranhamento (40) — Schmidt em C, sem raiz
    for i in range(40):
        if i < 8:      # produto: det = 0 exato
            a0, a1 = Fraction(random.randint(1, 9)), \
                     Fraction(random.randint(-9, 9))
            b0, b1 = Fraction(random.randint(1, 9)), \
                     Fraction(random.randint(1, 9))
            amp = (a0 * b0, a0 * b1, a1 * b0, a1 * b1)
        else:
            amp = tuple(Fraction(random.randint(-99, 99),
                       random.randint(1, 99)) for _ in range(4))
        if sum(x * x for x in amp) == 0:
            amp = (Fraction(1), Fraction(0), Fraction(0), Fraction(0))
        st = ",".join(str(x) for x in amp)
        if i % 2:
            qline = "concurrence %s %s" % (random.choice(OPS),
                       random.choice(["0", "0.5", "0.25", "1", "0.75"]))
        else:
            qline = "entangled %s %s" % (random.choice(OPS),
                                         random.choice(["0", "1"]))
        src = ("ASK:\n    question: %s\nCONTRACT:\n    "
               "absolute_error: 0\nMODEL:\n    type: entanglement\n"
               "    state: %s\n" % (qline, st))
        res = NCA(parse_nexa(src), "zref").compile()
        cert = transpile(src)["cert"]
        out, rc, err = _run_zref(src)
        assert rc == 0, (err, src)
        assert out["verdict"] == (1 if res["answer"] is True else 0), \
            (st, qline, out["verdict"], res["answer"])
        assert out["hash"] == cert["input_hash"], (st, qline)
        assert out["units"] == cert["units"] == 0
        n_ok += 1

    # ---------------- recusas e muros §12 do C (honestidade auditada)
    # estado nulo e r=1: RECUSA (exit 2), nunca veredito
    for src in [
        "ASK:\n    question: entangled > 0\nCONTRACT:\n    "
        "absolute_error: 0\nMODEL:\n    type: entanglement\n    "
        "state: 0,0,0,0\n",
        "ASK:\n    question: sum > 3\nCONTRACT:\n    absolute_error: 0\n"
        "MODEL:\n    type: geometric_fin\n    r: 1\n    n: 5\n",
        "ASK:\n    question: sum_inf > 10\nCONTRACT:\n    "
        "absolute_error: 0\nMODEL:\n    type: geometric_inf\n"
        "    a: 1\n    r: 3/2\n",
    ]:
        out, rc, err = _run_zref(src)
        assert rc == 2 and "RECUSA (§12)" in err, (err[:120],)
        n_refusa += 1
    # fora do muro: OVERFLOW declarado (exit 3), nunca mentira
    out, rc, err = _run_zref(
        "ASK:\n    question: sum > 3\nCONTRACT:\n    absolute_error: 0\n"
        "MODEL:\n    type: gauss_series\n    n: 9999999999999999\n")
    assert rc == 3 and "OVERFLOW" in err
    n_overflow += 1
    out, rc, err = _run_zref(
        "ASK:\n    question: concurrence > 0.5\nCONTRACT:\n    "
        "absolute_error: 0\nMODEL:\n    type: entanglement\n    "
        "state: 9007199254740993,0,0,9007199254740992\n")
    assert rc == 3 and "OVERFLOW" in err, err[:200]
    n_overflow += 1

    print("ZREF C-PURO: %d fontes ZEPHIRUM decididas direto em C "
          "(gcc, __int128, sem Python em execução): veredito, INPUT_HASH "
          "e unidades IDÊNTICOS aos oráculos em todas as 5 famílias "
          "(gauss 40, média 40, geo_inf 40, geo_fin 40, emaranhamento 40)"
          % n_ok)
    print("MUROS §12: %d recusas estruturais (nulo/r=1/|r|>=1) e %d "
          "OVERFLOW declarados além do muro (2^53 da fronteira INCLUSIVE "
          "— o C diz o muro, não mente; a precisão arbitrária segue na "
          "referência)" % (n_refusa, n_overflow))
    print("RESULTADO: PASS — o padrão ZEPHIRUM decide de fonte em C puro; "
          "o Python deixou de ser necessário para decidir, certificar e "
          "recusar")


if __name__ == "__main__":
    main()
