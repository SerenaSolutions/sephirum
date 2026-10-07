#!/usr/bin/env python3
"""
PASSO 7 — TRUST: assinatura Ed25519 de emitente (bateria T1-T6).
=====================================================================

T1  contraprova independente: cryptography e PyNaCl produzem a MESMA
    assinatura (Ed25519 determinístico) e verificam a assinatura
    uma da outra — duas implementações independentes se validam
  T2  assinatura -> verificação completa do pipeline (hash + schema +
    recomputação + assinatura + registro)
  T3  adulteração de QUALQUER campo do payload quebra a assinatura
  T4  emitente forjado: chave própria + ISSUER próprio => fora do
    registro => REJECT; ISSUER roubado com assinatura de outra chave
    => REJECT
  T5  compatibilidade: certificado NÃO assinado segue verificável
    (a camada de confiança é aditiva, não destrutiva)
  T6  registro em arquivo: load/save do trusted_issuers.txt
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nexa_core import NCA, parse_nexa
from verify_certificate import verify
import zephirum_trust as trust


SRC = """ASK:
    question: sum > 10
MODEL:
    type: threshold_sum
    terms: 4, 3, 2, 1
    threshold: 10
"""


def main():
    blocks = parse_nexa(SRC)
    res = NCA(blocks, "t7").compile()
    cert = res["certificate"]
    ok, _ = verify(blocks, cert)
    assert ok, "baseline unsigned quebrou?!"

    # ---------- T1: contraprova independente ----------
    sk, pk = trust.gen_issuer()
    payload_msg = trust.payload_of(cert)
    s1 = trust.sign_certificate(cert, sk, backend="cryptography")
    s2 = trust.sign_certificate(cert, sk, backend="pynacl")
    assert s1["SIGNATURE"] == s2["SIGNATURE"], \
        "implementações discordam na assinatura!"
    assert s1["ISSUER"] == s2["ISSUER"] == pk
    # verificação cruzada: cada biblioteca confere a assinatura da outra
    o1, _ = trust.verify_trust(s1, {pk}, backend="cryptography")
    o2, _ = trust.verify_trust(s2, {pk}, backend="pynacl")
    o3, _ = trust.verify_trust(s1, {pk}, backend="pynacl")
    o4, _ = trust.verify_trust(s2, {pk}, backend="cryptography")
    assert o1 and o2 and o3 and o4
    print("T1 contraprova: cryptography == PyNaCl (assinatura idêntica, "
          "verificação cruzada 4/4) — duas implementações independentes "
          "concordam")

    # ---------- T2: pipeline completo assinado ----------
    signed = trust.sign_certificate(cert, sk)
    ok, reason = verify(blocks, signed, trusted_issuers={pk})
    assert ok, reason
    print("T2 pipeline completo: hash + schema + recomputação da fonte + "
          "assinatura Ed25519 + registro — ACCEPT")

    # ---------- T3: adulteração quebra a assinatura ----------
    for field, tamper in [("ANSWER", lambda c: not c["ANSWER"]),
                         ("STATUS", lambda c: "FULL_SUM"),
                         ("EVIDENCE", lambda c: dict(
                             c["EVIDENCE"], witness_sum=999)),
                         ("COST_ESTIMATE", lambda c: dict(
                             c["COST_ESTIMATE"], original=0)),
                         ("ELIMINATION_TRACE", lambda c:
                             c["ELIMINATION_TRACE"] + ["FORGED"])]:
        bad = copy.deepcopy(signed)
        bad[field] = tamper(bad)
        ok, reason = verify(blocks, bad, trusted_issuers={pk})
        assert not ok and "signature" in reason, (field, reason)
    print("T3 adulteração: ANSWER/STATUS/EVIDENCE/COST_ESTIMATE/"
          "ELIMINATION_TRACE => assinatura invalidada => REJECT em todos")

    # ---------- T4: emitente forjado ----------
    ask_sk, ask_pk = trust.gen_issuer()          # chave do atacante
    forged = trust.sign_certificate(cert, ask_sk)
    ok, reason = verify(blocks, forged, trusted_issuers={pk})
    assert not ok and "untrusted issuer" in reason, reason
    stolen = copy.deepcopy(forged)
    stolen["ISSUER"] = pk                        # ISSUER roubado
    ok, reason = verify(blocks, stolen, trusted_issuers={pk})
    assert not ok and "signature" in reason, reason
    print("T4 forjado: chave própria => fora do registro => REJECT; "
          "ISSUER roubado com assinatura de outra chave => REJECT")

    # ---------- T5: compatibilidade (camada aditiva) ----------
    ok, reason = verify(blocks, cert, trusted_issuers={pk})
    assert ok, reason
    onlysig = dict(cert, SIGNATURE="00" * 64)
    ok, reason = verify(blocks, onlysig, trusted_issuers={pk})
    assert not ok and "incomplete" in reason, reason
    print("T5 compatibilidade: certificado não assinado segue verificável; "
          "SIGNATURE sem ISSUER => REJECT explícito")

    # ---------- T6: registro em arquivo ----------
    reg = Path(trust.TRUSTED_FILE)
    backup = reg.read_text() if reg.exists() else None
    try:
        reg.write_text(pk + "\n")
        loaded = trust.load_trusted()
        assert loaded == {pk}
        ok, reason = verify(blocks, signed)      # registro default do arquivo
        assert ok, reason
        reg.write_text("")
        ok, reason = verify(blocks, signed)
        assert not ok and "untrusted issuer" in reason, reason
    finally:
        if backup is None:
            reg.unlink(missing_ok=True)
        else:
            reg.write_text(backup)
    print("T6 registro: trusted_issuers.txt carregado; registro vazio => "
          "emitente fora => REJECT")

    print("RESULTADO: PASS — o ciclo de confiança fecha: integridade "
          "(hash) + autenticidade (Ed25519 + registro de emitentes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
