#!/usr/bin/env python3
"""ZEPHIRUM KATAS — graded exercises in the exact-decision language.

Rustlings-style: each kata in katas/ has a question whose answer you
must PREDICT. Replace the ??? with 1 or 0 and the runner decides it
against the exact core. Wrong predictions are structural refusals
(Section 12) — the language will not guess for you.

    python3 katas/run_katas.py            # score all katas
    python3 katas/run_katas.py 3          # score only kata 3

Solved is only what the exact core decides. Evidence before velocity.
"""
import sys, os, io, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype"))
from nexa_core import parse_nexa, NCA

KATAS = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KATAS, "..", "prototype"))

# ground truth, verified against the exact core by run_katas_selftest
TRUTH = {
    1: (True,  "constant folding"),
    2: (True,  "threshold sum"),
    3: (True,  "entanglement, Bell Phi+"),
    4: (True,  "entanglement, W class"),
    5: (False, "forged ML-DSA signature"),
    6: (True,  "molecular, H2 dimer"),
}


def load_key():
    """The crypto kata needs a real ML-DSA keypair; the runner signs
    the message at load so the kata file stays small."""
    from pq_receipt import keygen, _b64
    from pqcrypto.sign import ml_dsa_44
    pub, priv = keygen()
    msg = "release zephyrum v0.9.0"
    sig = ml_dsa_44.sign(priv, msg.encode())
    bad = bytes([sig[0] ^ 1]) + sig[1:]          # single flipped byte
    return _b64(pub), _b64(bad), msg             # FORGED on purpose


def run(knum):
    path = os.path.join(KATAS, "kata%02d.zeph" % knum)
    src = open(path).read()
    if knum == 5:
        pub, bad, msg = load_key()
        src = src.replace("{{PUB}}", pub).replace("{{SIG}}", bad).replace("{{MSG}}", msg)
    try:
        r = NCA(parse_nexa(src), name="kata%02d.zeph" % knum).compile()
    except Exception as e:
        return "UNFINISHED", str(e).splitlines()[0][:70]
    want, _ = TRUTH[knum]
    if r["answer"] is None:
        return "UNFINISHED", "status=%s" % r["status"]
    return (("SOLVED", "the exact core agrees with you") if r["answer"] is want
            else ("WRONG", "the exact core rejected your prediction"))


def main():
    sel = [int(a) for a in sys.argv[1:]] or list(TRUTH)
    solved = 0
    for k in sel:
        st, why = run(k)
        solved += st == "SOLVED"
        print("kata %d [%s] %s" % (k, st, why))
    print("\n%d/%d solved" % (solved, len(sel)))
    print("A language that refuses to guess, teaches you to think.")


if __name__ == "__main__":
    main()
