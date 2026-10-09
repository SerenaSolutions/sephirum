#!/usr/bin/env python3
"""
POST-QUANTUM SIGNED RECEIPTS for Zephirum verdicts (FIPS 204 / ML-DSA-44).

Thesis: a verdict receipt must survive the arrival of a cryptographically
relevant quantum computer. Shor's algorithm forges classical ECDSA/RSA
receipts retroactively ("harvest now, decrypt later" applies to integrity
too). ML-DSA (FIPS 204, from CRYSTALS-Dilithium) is a lattice signature:
no known quantum attack breaks it.

Design (charter honesty):
- The signature covers the CANONICAL JSON of the receipt: sorted keys,
  no whitespace, UTF-8. Any field change breaks it.
- The PRIVATE key never leaves the operator's machine (pq_keys/ is
  gitignored; only the public verification key is committed).
- The signed receipt is self-describing: payload + algorithm + public
  key + signature, verifiable by anyone with this module and no
  network access.
- The signature is EVIDENCE OF AUTHORSHIP, not evidence of physics:
  it proves the receipt was produced by the key holder and was not
  altered. The physics is proven by the exact core, as always.

Usage:
  python3 pq_receipt.py keygen                # generate pq_keys/
  python3 pq_receipt.py sign receipt.json      # -> receipt.signed.json
  python3 pq_receipt.py verify receipt.signed.json
  python3 pq_receipt.py selftest               # keygen+sign+verify+tamper
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KEYDIR = os.path.join(HERE, "pq_keys")
ALG = "ML-DSA-44"

try:
    from pqcrypto.sign import ml_dsa_44
except ImportError:
    sys.exit("pqcrypto missing: pip install pqcrypto")


def _b64(b):
    return base64.b64encode(b).decode()


def _unb64(s):
    return base64.b64decode(s)


def canonical(payload):
    """Canonical bytes of a JSON payload: sorted keys, no whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def keygen():
    """Generate a keypair. Returns (public_key, private_key)."""
    return ml_dsa_44.keygen()


def save_keys(pub, priv):
    os.makedirs(KEYDIR, exist_ok=True)
    with open(os.path.join(KEYDIR, "ml_dsa_44.pub"), "wb") as f:
        f.write(pub)
    with open(os.path.join(KEYDIR, "ml_dsa_44.priv"), "wb") as f:
        f.write(priv)
    gitignore = os.path.join(HERE, "pq_keys", ".gitignore")
    with open(gitignore, "w") as f:
        f.write("# private key never leaves the operator's machine\n"
                "ml_dsa_44.priv\n")


def load_keys():
    with open(os.path.join(KEYDIR, "ml_dsa_44.pub"), "rb") as f:
        pub = f.read()
    with open(os.path.join(KEYDIR, "ml_dsa_44.priv"), "rb") as f:
        priv = f.read()
    return pub, priv


def sign_receipt(receipt, priv):
    sig = ml_dsa_44.sign(priv, canonical(receipt))
    return {"receipt": receipt,
            "algorithm": ALG,
            "fips": "204",
            "public_key": _b64(load_keys()[0]) if priv else None,
            "signature": _b64(sig)}


def verify_receipt(signed, pub=None):
    if signed.get("algorithm") != ALG:
        return False, "algorithm mismatch"
    if pub is None:
        pub = _unb64(signed["public_key"])
    try:
        ml_dsa_44.verify(pub, canonical(signed["receipt"]),
                         _unb64(signed["signature"]))
        return True, "verified"
    except Exception:
        return False, "INVALID SIGNATURE"


def selftest():
    # 1. fresh keypair + sign + verify
    pub, priv = keygen()
    receipt = {"engine": "zref-c11",
               "question": "entangled == 1",
               "input_hash": "b8c6435d3db46d6cb58b23be024452fcb"
                             "32806e5861620175730550b757ba080",
               "verdict": 1,
               "units": 0,
               "qpu_units_billed": 0}
    os.environ["PQTEST"] = "1"
    # sign with explicit keys (no disk dependency for the selftest)
    sig = ml_dsa_44.sign(priv, canonical(receipt))
    signed = {"receipt": receipt, "algorithm": ALG, "fips": "204",
              "public_key": _b64(pub), "signature": _b64(sig)}
    ok, msg = verify_receipt(signed)
    assert ok, msg
    # 2. tamper detection: flip one verdict bit
    tampered = json.loads(json.dumps(signed))
    tampered["receipt"]["verdict"] = 0
    ok2, msg2 = verify_receipt(tampered)
    assert not ok2, "TAMPER NOT DETECTED — soundness hole"
    # 3. wrong key must fail
    other_pub, _ = keygen()
    ok3, _ = verify_receipt(signed, pub=other_pub)
    assert not ok3, "WRONG KEY ACCEPTED — soundness hole"
    return ("SELFTEST PASS: sign ok, verify ok, tamper detected, "
            "foreign key rejected (FIPS 204 / ML-DSA-44)")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "keygen":
        pub, priv = keygen()
        save_keys(pub, priv)
        print("keypair written to pq_keys/ (private key gitignored)")
    elif cmd == "sign":
        with open(sys.argv[2]) as f:
            receipt = json.load(f)
        _, priv = load_keys()
        signed = {"receipt": receipt, "algorithm": ALG, "fips": "204",
                  "public_key": _b64(load_keys()[0]),
                  "signature": _b64(ml_dsa_44.sign(priv, canonical(receipt)))}
        out = sys.argv[2].replace(".json", ".signed.json")
        with open(out, "w") as f:
            json.dump(signed, f, indent=1, ensure_ascii=False)
        print("signed receipt ->", out)
    elif cmd == "verify":
        with open(sys.argv[2]) as f:
            signed = json.load(f)
        ok, msg = verify_receipt(signed)
        print(("VERIFIED" if ok else "REFUSED") + ":", msg)
        sys.exit(0 if ok else 2)
    elif cmd == "selftest":
        print(selftest())
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
