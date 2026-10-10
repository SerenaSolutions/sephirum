#!/usr/bin/env python3
"""CHSH/QKD BATTERY — cybersecurity study ZYQL-TR-2026-10-10.

Entanglement-based key distribution (QKD) witnessed through the CHSH
game. Three legs, the discipline of the house:

1. CLASSICAL BOUND (exact, zero QPU): all 16 deterministic local
   strategies enumerated — the classical bound S <= 2 is an arithmetic
   fact decided by the kernel.
2. TSIRELSON BOUND (exact to 28 digits, disclosed truncation of the
   irrational sqrt(2)): the quantum ceiling 2*sqrt(2) ~= 2.8284.
3. WITNESS legs: the kernel decides 'S > 2' EXACTLY over declared
   counts. Negative control (uniform counts -> S = 0 -> FALSE) and
   simulated positive control (ideal Bell correlations -> S = 2*sqrt(2)
   -> TRUE). The hardware leg (ibm_kingston) feeds real QPU counts
   through the SAME witness path — see qpu_chsh_qkd.py.

The QPU never judges: it only supplies counts. The language decides.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction
from nexa_core import parse_nexa, NCA


def run(src):
    return NCA(parse_nexa(src), name="chsh_qkd.zeph").compile()


ok = 0

# ── Leg 1: classical bound — arithmetic fact ────────────────────────
r = run("ASK:\n    question: classical_max <= 2\nMODEL:\n    type: exact\n"
        "    check: chsh_bound\n    mode: classical\n")
ev = r["certificate"]["EVIDENCE"]
assert r["answer"] is True and ev["classical_max_abs_S"] == 2
assert r["certificate"]["STATUS"] == "DECIDED_WITHOUT_EXECUTION"
ok += 1
print("CLSSICO  CHSH: 16 estrategias locais enumeradas, |S|max = %d "
      "(FATO aritmetico, zero QPU)" % ev["classical_max_abs_S"])

# the quantum ceiling EXCEEDS the classical bound — decided offline
r = run("ASK:\n    question: tsirelson > 2\nMODEL:\n    type: exact\n"
        "    check: chsh_bound\n    mode: tsirelson\n")
ev = r["certificate"]["EVIDENCE"]
assert r["answer"] is True and abs(ev["tsirelson_bound"] - 2.8284271247461903) < 1e-12
ok += 1
print("TSIRELSON CHSH: 2*sqrt(2) = %.13f > 2 — teto quantico decidido "
      "offline (truncamento de 28 digitos declarado, §12)"
      % ev["tsirelson_bound"])

# ── Leg 2: witness — negative control (uniform counts) ────────────────
r = run("ASK:\n    question: S > 2\nMODEL:\n    type: exact\n"
        "    check: chsh_bound\n    mode: witness\n"
        "    a0b0: 500,500\n    a0b1: 500,500\n"
        "    a1b0: 500,500\n    a1b1: 500,500\n")
assert r["answer"] is False
ok += 1
print("TESTEMUNHA (controle negativo): contagens uniformes -> S = 0 -> "
      "FALSE — sem emaranhamento, sem QKD; recusa honesta de violacao")

# ── Leg 3: witness — simulated positive control (ideal Bell) ─────────
# Ideal Bell correlations: E = +1/sqrt(2) (a0b0, a0b1, a1b0), -1/sqrt(2)
# (a1b1) -> S = 2*sqrt(2). Counts sampled as declared integers.
p_same = (1 + 0.7071067811865475) / 2          # ~0.853553
n = 2000
same = int(round(n * p_same))
r = run("ASK:\n    question: S > 2\nMODEL:\n    type: exact\n"
        "    check: chsh_bound\n    mode: witness\n"
        "    a0b0: %d,%d\n    a0b1: %d,%d\n    a1b0: %d,%d\n    a1b1: %d,%d\n"
        % (same, n - same, same, n - same, same, n - same,
           n - same, same))
ev = r["certificate"]["EVIDENCE"]
assert r["answer"] is True and ev["S_float"] > 2.82, ev["S_float"]
ok += 1
print("TESTEMUNHA (controle positivo simulado): S = %.4f > 2 -> TRUE — "
      "certificado violacao classica; simulado, rotulado, sem QPU real"
      % ev["S_float"])

# ── Leg 4: structural refusals (§12) ─────────────────────────────────
for bad in ("0,0\n    a0b1: 500,500\n    a1b0: 500,500\n    a1b1: 500,500",
            "500,500\n    a0b1: 500,500\n    a1b0: 500,500\n    a1b1: 500",
            "x,y\n    a0b1: 500,500\n    a1b0: 500,500\n    a1b1: 500,500"):
    try:
        run("ASK:\n    question: S > 2\nMODEL:\n    type: exact\n"
            "    check: chsh_bound\n    mode: witness\n    a0b0: " + bad + "\n")
    except (ValueError, Exception) as e:
        assert "structural" in str(e) or "int" in str(e) or "positive" in str(e), e
    else:
        raise AssertionError("malformed witness accepted: %r" % bad)
ok += 1
print("ESTRUTURAL: contagens malformadas sao erro explicito (3/3), §12")

print("\nRESULT: CHSH/QKD battery PASS (%d legs) — classical bound, "
      "Tsirelson ceiling and witness discipline certified offline; "
      "hardware leg ready (qpu_chsh_qkd.py)." % ok)
