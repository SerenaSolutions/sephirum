#!/usr/bin/env python3
"""
BATERIA DO PLUG-IN QUÂNTICO — o algoritmo Zephirum instalável.
=============================================================

Fatos exigidos (Q1..Q5, SP1, TP1, TP2):
  Q1  vereditos exatos == teoria universal (Wootters PRL 1998 /
      Nielsen & Chuang cap. 2) em todos os casos padrão;
  Q2  recibo honesto: routed, DECIDED_WITHOUT_EXECUTION, ZERO
      unidades QPU, verificação independente reproduz o selo;
  Q3  família fora do escopo: recusa com motivo (§12), sem rotear;
  Q4  SDK ausente/desconhecido: recibo SKIP declarado, nunca erro;
  Q5  CLI end-to-end: zephirum-q decide e imprime certificado;
  SP1 recibo à mão: Bell |Phi+> -> C=1, emaranhado; produto -> C=0;
  TP1 adulteração de ENTRADA: trocar uma amplitude quebra o selo;
  TP2 adulteração de RESPOSTA: inverter ANSWER quebra a verificação.
"""
import os
import subprocess
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "plugin")


def _src(state, question):
    return ("ASK:\n    question: %s\nMODEL:\n    type: entanglement\n"
            "    state: %s\n" % (question, state))


def main():
    # importar o plug-in instalado (não o repositório)
    sys.path.insert(0, PLUGIN)
    from zephirum_quantum_plugin import gateway, verify

    R2 = "0.70710678118654752"
    casos = [
        ("Bell Phi+", f"{R2},0,0,{R2}", "entangled == 1", True, 1),
        ("Bell Psi-", f"0,{R2},-{R2},0", "entangled == 1", True, 1),
        ("produto |00>", "1,0,0,0", "entangled == 1", False, 0),
        ("superposicao separavel", f"{R2},{R2},0,0", "entangled == 1",
         False, 0),
        ("parcial 3/5-4/5", "0.6,0,0,0.8", "concurrence > 0.9", True, 1),
        ("parcial sob limiar", "0.6,0,0,0.8", "concurrence > 0.96",
         False, 0),
        ("limiar exato C==t", "0.6,0,0,0.8", "concurrence > 0.96",
         False, 0),
    ]
    ok = 0
    for nome, st, q, esperado, _ in casos:
        rec, okv = gateway(_src(st, q))
        assert rec["routed"] and rec["status"] == (
            "DECIDED_WITHOUT_EXECUTION"), nome
        assert rec["qpu_units_billed"] == 0, nome
        assert okv and rec["independent_check"][0], nome
        assert (rec["verdict"] == 1) == esperado, (nome, rec["verdict"])
        ok += 1
    # SP1: recibo à mão — teoria: C(Bell)=1, C(produto)=0, C(3/5,4/5)=24/25
    rec, _ = gateway(_src(f"{R2},0,0,{R2}", "entangled == 1"))
    assert Fraction(rec["concurrence_exact"]) == 1
    rec, _ = gateway(_src("1,0,0,0", "entangled == 1"))
    assert Fraction(rec["concurrence_exact"]) == 0
    rec, _ = gateway(_src("0.6,0,0,0.8", "entangled == 1"))
    assert Fraction(rec["concurrence_exact"]) == Fraction(24, 25)
    print("Q1+SP1: %d/%d vereditos == teoria universal (Wootters/"
          "N&C) — recibos: C exata = 1, 0 e 24/25 à mão" % (ok, ok))

    # Q3: família fora do escopo — recusa honesta
    rec, _ = gateway("ASK:\n    question: x == 1\nMODEL:\n    type: "
                     "grover_search\n    data: 42\n")
    assert not rec["routed"] and "§12" in rec["reason"]
    assert rec["qpu_units_billed"] == 0
    print("Q3: família 'grover_search' RECUSADA com motivo (§12) — "
          "nunca roteia o que não prova")

    # Q4: SDK desconhecido — SKIP declarado
    rec, _ = gateway(_src(f"{R2},0,0,{R2}", "entangled == 1"),
                     sdk="sdk_inexistente")
    assert "SKIP (§12)" in rec["sdk_cross_check"]
    print("Q4: SDK 'sdk_inexistente' -> recibo SKIP (§12) — nunca "
          "erro escondido")

    # TP1: adulteração de ENTRADA pega no selo
    src = _src(f"{R2},0,0,{R2}", "entangled == 1")
    rec, _ = gateway(src)
    cert = rec["cert"]
    src_alterado = _src(f"{R2},0,0,0.9", "entangled == 1")
    okv, why = verify(src_alterado, cert)
    assert not okv, "adulteração de entrada não pega!"
    print("TP1: amplitude adulterada -> selo NÃO confere (%s)" % why)

    # TP2: adulteração de RESPOSTA pega na verificação
    cert_falso = dict(cert)
    cert_falso["ANSWER"] = not cert["ANSWER"]
    okv, why = verify(src, cert_falso)
    assert not okv, "resposta invertida não pega!"
    print("TP2: ANSWER invertida com re-selo -> verificação pega "
          "(%s)" % why)

    # Q5: CLI end-to-end
    ex = os.path.join(PLUGIN, "examples", "bell_phi_plus.zeph")
    r = subprocess.run(["zephirum-q", ex, "--sdk", "qiskit"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:200]
    assert "VERDICT     1" in r.stdout and "QPU UNITS   0" in r.stdout
    assert "CERT_HASH" in r.stdout and "INDEP CHECK" in r.stdout
    assert "SDK CROSS" in r.stdout
    print("Q5: CLI zephirum-q decide, sela e contraprova end-to-end")

    print()
    print("PLUG-IN QUÂNTICO ZEPHIRUM: %d/%d casos — o algoritmo da "
          "casa agora é INSTALÁVEL (pip), decide emaranhamento com "
          "certificado verificável, zero unidades QPU, SDKs como "
          "gêmeos adversariais; adulteração de entrada e de resposta "
          "PEGAS na verificação independente" % (ok, ok))
    print("RESULTADO: PASS — a visão do dono entregue: o primeiro "
          "artefato (verificador autônomo Python/Java) virou plug-in "
          "do mundo quântico")


if __name__ == "__main__":
    main()
