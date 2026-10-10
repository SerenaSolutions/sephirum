#!/usr/bin/env python3
"""zyql_python.py — ctypes binding: any Python can call the C core.
Parity-proven against prototype/nexa_core.py (tests/parity_nexa.py)."""
import ctypes, json, os

_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "libzyql.so"))
_lib.zyql_decide.restype = ctypes.c_void_p
_lib.zyql_receipt.restype = ctypes.c_char_p
_lib.zyql_message.restype = ctypes.c_char_p

def decide(src: str) -> dict:
    """One program, one decision, full receipt (JSON dict)."""
    p = _lib.zyql_decide(src.encode())
    if not p:
        raise MemoryError("zyql: allocation failed")
    h = ctypes.c_void_p(p)
    rec = json.loads(_lib.zyql_receipt(h))
    _lib.zyql_close(h)
    return rec

if __name__ == "__main__":
    r = decide("ASK:\n    question: period_years <= 12\n"
               "    purpose: verify orbital mechanics\n"
               "MODEL:\n    type: exact\n    check: kepler3\n"
               "    semi_major_axis_au: 5.204\n")
    print(r["STATUS"], "| ANSWER:", r["ANSWER"],
          "| INPUT_HASH:", r["INPUT_HASH"][:16], "...")
