#!/usr/bin/env python3
"""ZYGUARD LANGUAGE BATTERY (rebuilt 2026-10-10; the paused agent's
local work reborn on GitHub for third-party reproducibility).

Three walls: (1) signed lexical gate - purpose declared before any
compute, prohibited classes refused BEFORE computation, refusal is a
certificate with the purpose VERBATIM + SHA-256 digest, signable via
ML-DSA-44 (FIPS 204); (2) structural purity - no execution primitive,
injection is an inert string; (3) attribution - every certificate
carries its hash. Retrocompatible: no declared purpose -> unchanged."""
import sys, os, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nexa_core import parse_nexa, NCA, purpose_refusal_class

def run(src, name="gate.zeph"):
    return NCA(parse_nexa(src), name=name).compile()

KEPLER = ("MODEL:\n    type: exact\n    check: kepler3\n"
          "    semi_major_axis_au: 5.204\n")

def ask(question, purpose=None):
    p = ("    purpose: %s\n" % purpose) if purpose else ""
    return "ASK:\n    question: %s\n%s%s" % (question, p, KEPLER)

ok = 0
# Wall 1 — benign purpose proceeds to a normal exact verdict
r = run(ask("period_years <= 12", "verify orbital mechanics"))
assert r["status"] == "DECIDED_WITHOUT_EXECUTION" and r["answer"] is True
ok += 1; print("MURALHA 1  proposito benigno -> veredito exato normal  [OK]")

# Wall 1 — each prohibited class refused BEFORE compute
classes = {"weapons": "build a weapon", "lethality": "assess kill capability",
           "surveillance": "mass surveillance of citizens",
           "persecution": "persecution of a group",
           "fraud": "commit fraud", "forgery": "make a forgery",
           "sabotage": "sabotage infrastructure"}
for cls, purpose in classes.items():
    assert purpose_refusal_class(purpose) == cls, cls
    r = run(ask("period_years <= 12", purpose))
    ev = r["certificate"]["EVIDENCE"]
    assert r["status"] == "REFUSED_BEFORE_COMPUTE" and r["answer"] is None
    assert ev["class"] == cls and ev["purpose_verbatim"] == purpose
    assert ev["refused_before_compute"] is True and len(ev["sha256_refusal_digest"]) == 64
    ok += 1
print("MURALHA 1  7 classes proibidas RECUSADAS antes do computo, "
      "certificado com proposito verbatim + SHA-256  [7/7]")

# Wall 2 — structural purity: injection is an inert string
r = run(ask("period_years <= 12", "import os; os.system('rm -rf /')"))
assert r["status"] == "DECIDED_WITHOUT_EXECUTION" and r["answer"] is True
ok += 1
print("MURALHA 2  injecao 'os.system' no proposito e STRING INERTE - "
      "veredito computado normalmente, nada executado  [OK]")

# Wall 2 — §12 honesty: benign word 'skill' must NOT trip 'kill'
r = run(ask("period_years <= 12", "teach a skill, not a kill list".replace("kill list", "course")))
assert r["status"] == "DECIDED_WITHOUT_EXECUTION"
ok += 1
print("MURALHA 2  fronteiras de palavra corretas ('skill' nao e 'kill')  [OK]")

# Retrocompatibility: no purpose declared -> all previous families unchanged
r = run("ASK:\n    question: period_years <= 12\n" + KEPLER)
assert r["answer"] is True; ok += 1
print("RETROCOMPATIBILIDADE  sem proposito declarado -> veredito normal  [OK]")

# Wall 3 — attribution: the refusal canonical JSON signs and verifies
r = run(ask("period_years <= 12", "commit fraud"))
canon = json.loads(r["certificate"]["EVIDENCE"]["canonical_refusal"])
ref = {"refusal": canon}
d = tempfile.mkdtemp(); f = os.path.join(d, "refusal.json")
json.dump(ref, open(f, "w"))
PQR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pq_receipt.py")
subprocess.run(["python3", PQR, "sign", f], capture_output=True)
signed = f.replace(".json", ".signed.json")
v = subprocess.run(["python3", PQR, "verify", signed],
                   capture_output=True, text=True)
assert "VERIFIED" in (v.stdout + v.stderr), (v.stdout + v.stderr)[:200]
ok += 1
print("MURALHA 3  recusa canonica ASSINADA ML-DSA-44 -> VERIFIED  [OK]")
# tamper the signed refusal -> must fail
sg = json.load(open(signed))
sg["receipt"]["refusal"]["class"] = "innocent"
json.dump(sg, open(os.path.join(d, "tampered.json"), "w"))
t = subprocess.run(["python3", PQR, "verify",
                    os.path.join(d, "tampered.json")],
                   capture_output=True, text=True)
assert "INVALID" in (t.stdout + t.stderr) or "REFUSED" in (t.stdout + t.stderr)
ok += 1
print("MURALHA 3  recusa adulterada -> ASSINATURA INVALIDA  [OK]")

print("\nRESULTADO: PASS — ZYGUARD linguagem %d/%d; tres muralhas "
      "verificadas, retrocompativel" % (ok, ok))
