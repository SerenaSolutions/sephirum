#!/usr/bin/env python3
"""Parity battery: C core (libzyql.so) vs prototype/nexa_core.py.
Claims tested: same verdict, same ANSWER, same INPUT_HASH,
same sha256_refusal_digest for identical programs."""
import ctypes, json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(os.path.dirname(HERE), os.pardir, "prototype")
sys.path.insert(0, PROTO)
from nexa_core import parse_nexa, NCA  # noqa: E402
import hashlib  # noqa: E402

lib = ctypes.CDLL(os.path.join(HERE, "..", "libzyql.so"))
lib.zyql_decide.restype = ctypes.c_void_p
lib.zyql_receipt.restype = ctypes.c_char_p
lib.zyql_result.restype = ctypes.c_int
lib.zyql_answer.restype = ctypes.c_int

def c_decide(src):
    p = lib.zyql_decide(src.encode())
    if not p: return None, None, None
    return (lib.zyql_result(ctypes.c_void_p(p)),
            lib.zyql_answer(ctypes.c_void_p(p)),
            json.loads(lib.zyql_receipt(ctypes.c_void_p(p))))

def py_decide(src):
    return NCA(parse_nexa(src), name="mission").compile()

KEP = ("ASK:\n    question: period_years <= 12\n"
       "    purpose: verify orbital mechanics\n"
       "MODEL:\n    type: exact\n    check: kepler3\n"
       "    semi_major_axis_au: 5.204\n")
EXPR = ("ASK:\n    question: result == 14\n"
        "MODEL:\n    type: expression\n    expr: 2 + 3 * 4\n")
FRAUD = ("ASK:\n    question: period_years <= 12\n"
         "    purpose: commit fraud\n"
         "MODEL:\n    type: exact\n    check: kepler3\n"
         "    semi_major_axis_au: 5.204\n")
cases = [("kepler3 benigno", KEP), ("expression dobra", EXPR),
         ("portgate fraude", FRAUD)]
fails = 0
for label, src in cases:
    cst, cans, crec = c_decide(src)
    py = py_decide(src)
    ok = True
    if label != "portgate fraude":
        ok &= (cst == 0 and py["status"] == "DECIDED_WITHOUT_EXECUTION")
        ok &= (bool(cans) == bool(py["answer"]))
    else:
        ok &= (cst == 1 and py["status"] == "REFUSED_BEFORE_COMPUTE")
    ok &= crec["INPUT_HASH"] == py["certificate"]["INPUT_HASH"]
    if label == "portgate fraude":
        ok &= crec["EVIDENCE"]["sha256_refusal_digest"] == \
              py["certificate"]["EVIDENCE"]["sha256_refusal_digest"]
        ok &= crec["EVIDENCE"]["canonical_refusal"] == \
              py["certificate"]["EVIDENCE"]["canonical_refusal"]
    print("%s  paridade %s: status/answer/input_hash%s" %
          ("[OK]" if ok else "[FAIL]", label,
           " + digest recusa identico" if label == "portgate fraude" else ""))
    fails += 0 if ok else 1
print("\n%s (C e Python: mesmos vereditos e mesmos hashes)" %
      ("PARIDADE 3/3 OK" if not fails else "PARIDADE FALHOU"))
sys.exit(1 if fails else 0)
