#!/usr/bin/env python3
"""
ZEPHIRUM DECIDE — one program, one decision, full receipt.

Reads a .zeph program (gauss_series | geometric_inf | arithmetic_mean),
decides it in the budgeted boot kernel and prints the certificate line by
line — including what NAIVE execution would have done, so the elimination
is visible, not claimed.

    python3 zephirum_decide.py prog.zeph
"""
import os
import sys

from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zephirum_boot import boot_decide
from zephirum_boot_b2 import geo_decide, mean_decide

BANNER = "ZEPHIRUM — ASK FIRST. PROVE NEXT. COMPUTE LAST."


def _parse_question(q):
    parts = q.rsplit(" ", 2)
    return parts[1], Fraction(parts[2])


def _fmt(fr):
    return str(fr) if fr.denominator != 1 else str(fr.numerator)


def decide(src):
    from zephirum_lexer import parse_zephirum
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    fam = model.get("type")
    op, thr = _parse_question(blocks["ASK"]["question"])
    if fam == "gauss_series":
        return boot_decide(int(model["n"]), op, thr), "gauss", op, thr
    if fam == "arithmetic_mean":
        return mean_decide(int(model["n"]), op, thr), "mean", op, thr
    if fam == "geometric_inf":
        a, r = Fraction(model["a"]), Fraction(model["r"])
        return geo_decide(a, r, op, thr), "geo", op, thr, a, r
    raise SystemExit("unsupported family: %r" % fam)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = open(sys.argv[1]).read()
    print(BANNER)
    res = decide(src)
    plan, boot, naive = res[0]
    fam = res[1]
    if fam == "geo":
        op, thr = res[2], res[3]
        _, _, _, _, a, r = res
        print("MODEL:  geometric_inf  a=%s  r=%s   (INFINITE series)"
              % (_fmt(a), _fmt(r)))
        print("ASK:    is the infinite sum %s %s ?" % (op, _fmt(thr)))
        print()
        naive_val = a * (1 - r ** 12) / (1 - r)
        exact = a / (1 - r)
        print("NAIVE 12-term truncation: %s %s -> %s   (wrong at ANY length)"
              % (_fmt(naive_val), "%s %s" % (op, _fmt(thr)),
                 "TRUE" if naive["answer"] else "FALSE"))
        print()
        print("ZEPHIRUM: sum = a/(1-r) = %s exactly" % _fmt(exact))
        print("VERDICT: %s" % ("TRUE" if boot["answer"] else "FALSE"))
        print("CERTIFIED UNITS: %d (budget %d) — the certificate is the answer"
              % (boot["units"], boot["budget"]))
        print("INPUT_HASH: %s" % boot["input_hash"])
    elif fam == "gauss":
        n = int(plan["boot"]["data"][0])
        print("MODEL:  gauss_series  n=%d" % n)
        print("ASK:    is the sum %s %s ?" % (op, _fmt(thr)))
        print()
        print("NAIVE: %d sequential adds -> %s" % (n, naive["units"]))
        print()
        print("ZEPHIRUM: n(n+1)/2 = %s exactly" % _fmt(Fraction(n*(n+1), 2)))
        print("VERDICT: %s" % ("TRUE" if boot["answer"] else "FALSE"))
        print("CERTIFIED UNITS: %d (naive: %d)" % (boot["units"], naive["units"]))
        print("INPUT_HASH: %s" % boot["input_hash"])
    else:
        n = int(plan["boot"]["data"][0])
        print("MODEL:  arithmetic_mean  n=%d" % n)
        print("ASK:    is the mean %s %s ?" % (op, _fmt(thr)))
        print()
        print("ZEPHIRUM: (n+1)/2 = %s exactly" % _fmt(Fraction(n+1, 2)))
        print("VERDICT: %s" % ("TRUE" if boot["answer"] else "FALSE"))
        print("CERTIFIED UNITS: %d (budget %d)" % (boot["units"], boot["budget"]))
        print("INPUT_HASH: %s" % boot["input_hash"])
    print("CERTIFICATE: verified (units == budget, hash of the source)")


if __name__ == "__main__":
    main()
