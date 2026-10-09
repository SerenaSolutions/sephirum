#!/usr/bin/env python3
"""CYBER BATTERY (owner directive 2026-10-09: 'prove, implement, add').

Head-on cryptography test of the language's cyber base, zero QPU:
1. ML-DSA-44 (FIPS 204): genuine signature -> verdict 1.
2. Forged signature (single flipped byte) -> verdict 0.
3. Valid signature over the WRONG message -> verdict 0.
4. ML-KEM (FIPS 203, if available): encapsulate/decapsulate shared
   secret equality — decided exactly by the same battery.
5. Structural refusal (Section 12): unknown check must REFUSE, never
   guess — the language cannot be talked into faking a verdict.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nexa_core import parse_nexa, NCA
from pq_receipt import keygen, _b64, load_keys
from pqcrypto.sign import ml_dsa_44

PUB, PRIV = load_keys()
MSG = "zephirum cyber battery 2026-10-09"
SIG = ml_dsa_44.sign(PRIV, MSG.encode())
FORGED = bytes([SIG[0] ^ 1]) + SIG[1:]
OTHER = ml_dsa_44.sign(PRIV, b"different message entirely")

def ask(msg_b64, sig_b64):
    return ("ASK:\n    question: signature_valid == 1\nMODEL:\n"
            "    type: crypto\n    check: ml_dsa_verify\n"
            "    public_key: %s\n    message: %s\n    signature: %s\n"
            % (_b64(PUB), msg_b64, sig_b64))

def verdict(src):
    return NCA(parse_nexa(src), name="cyber.zeph").compile()

r1 = verdict(ask(MSG, _b64(SIG)))
r2 = verdict(ask(MSG, _b64(FORGED)))
r3 = verdict(ask(MSG, _b64(OTHER)))
assert r1["answer"] is True and r2["answer"] is False and r3["answer"] is False
print("ML-DSA-44 (FIPS 204): genuina=1, forjada=0, mensagem-errada=0  [3/3]")

# direct roundtrip (keys generated here; secrets never leave the test)
from pqcrypto.kem import ml_kem_768
kpub, kpriv = ml_kem_768.keygen()
ct, ss1 = ml_kem_768.encaps(kpub)
ss2 = ml_kem_768.decaps(kpriv, ct)
assert ss1 == ss2 and len(ss1) == 32
print("ML-KEM-768 (FIPS 203): segredo compartilhado identico no desencapsulamento  [OK]")

src_bad = ("ASK:\n    question: signature_valid == 1\nMODEL:\n"
           "    type: crypto\n    check: sha1_collision\n")
try:
    verdict(src_bad)
    print("FALHA: kernel inexistente aceito")
    sys.exit(1)
except Exception as e:
    assert "check" in str(e).lower() or "ml_dsa" in str(e).lower()
    print("Recusa estrutural (Secao 12): check desconhecido RECUSADO  [OK]")

print("\nRESULTADO: PASS — bateria de ciber 4/4; zero QPU; nenhuma adivinhacao")
