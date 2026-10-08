#!/usr/bin/env python3
"""C-core cross-check: the C decision core vs the Python reference
engine, over a large generated corpus. Soundness-first: any verdict
mismatch (decided/decided or UNKNOWN/decided) is a failure (exit 1).
The Python engine is the reference (nexa_core.py)."""
import json, random, subprocess, sys, tempfile, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "prototype"))
from nexa_core import parse_nexa, NCA

random.seed(42)
BIN = os.path.join(os.path.dirname(__file__), "..", "src", "nexa_core")

def src_sum(terms, thr, op, unk=None, assume=True):
    s = ("ASK:\n    question: sum %s %s\nCONTRACT:\n    absolute_error: 0\n"
         "MODEL:\n    type: threshold_sum\n    terms: %s\n" % (op, thr, ", ".join(map(str, terms))))
    if assume: s += "    assumption: terms_nonnegative\n"
    if unk: s += "    unknown: x in %d..%d\n" % unk
    return s

def src_mean(known, u, bounds, thr, op):
    return ("ASK:\n    question: mean %s %s\nMODEL:\n    type: mean_partial\n"
            "    known: %s\n    unknown_count: %d\n    bounds: %s\n"
            % (op, thr, ", ".join(map(str, known)), u, bounds))

def src_geo(r, n, thr, op):
    return ("ASK:\n    question: sum %s %s\nMODEL:\n    type: geometric_series\n"
            "    r: %s\n    n: %d\n" % (op, thr, r, n))

def oracle(src):
    blocks = parse_nexa(src)
    r = NCA(blocks).compile()
    return r["answer"]  # True / False / None

def ccore(src):
    with tempfile.NamedTemporaryFile("w", suffix=".zeph", delete=False) as f:
        f.write(src); p = f.name
    out = subprocess.run([BIN, p], capture_output=True, text=True).stdout
    os.unlink(p)
    return json.loads(out)["answer"]  # 1 / 0 / None

mismatch, total = [], 0
stats = {}
cases = []
ops = [">", "<", ">=", "<=", "=="]
for _ in range(150):  # threshold_sum
    n = random.randint(1, 8)
    terms = [random.randint(-20, 60) for _ in range(n)]
    op = random.choice(ops); thr = random.randint(-50, 300)
    unk = None
    if random.random() < 0.3:
        unk = (random.randint(-10, 30), random.randint(-10, 30))
        if unk[0] > unk[1]: unk = (unk[1], unk[0])
    cases.append(("threshold_sum", src_sum(terms, thr, op, unk)))
for _ in range(150):  # mean_partial
    m = random.randint(0, 8)
    known = [random.randint(-20, 60) for _ in range(m)]
    u = random.randint(1, 5)
    lo = random.randint(-30, 40); hi = random.randint(lo, lo + 90)
    op = random.choice(ops); thr = random.randint(-40, 300)
    cases.append(("mean_partial", src_mean(known, u, "%d..%d" % (lo, hi), thr, op)))
for _ in range(150):  # geometric_series
    r = random.choice([2, 3, 1, 0, -2, "1/2", "2/3", "-1/2"])
    n = random.randint(0, 12)
    op = random.choice(ops); thr = random.randint(-30, 3000)
    cases.append(("geometric_series", src_geo(r, n, thr, op)))

for fam, src in cases:
    total += 1
    try: o = oracle(src)
    except Exception: continue  # structural error: engine rejects, out of C scope
    c = ccore(src)
    st = stats.setdefault(fam, {"n": 0, "mismatch": 0, "o_unk": 0, "c_unk": 0})
    st["n"] += 1
    if o is None: st["o_unk"] += 1
    if c is None: st["c_unk"] += 1
    if (o is None) != (c is None) or (o is not None and int(o) != int(c)):
        mismatch.append((fam, src, o, c)); st["mismatch"] += 1

for fam, st in stats.items():
    print("%-18s n=%3d mismatch=%d oracle_UNKNOWN=%d c_UNKNOWN=%d"
          % (fam, st["n"], st["mismatch"], st["o_unk"], st["c_unk"]))
print("TOTAL %d cases, %d mismatches (target: 0)" % (total, len(mismatch)))
if mismatch:
    for fam, src, o, c in mismatch[:3]:
        print("--- MISMATCH", fam, "oracle:", o, "C:", c); print(src)
    sys.exit(1)
print("PASS: C core verdict-identical to the Python reference engine")
