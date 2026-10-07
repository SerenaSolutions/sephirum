#!/usr/bin/env python3
"""
BATERIA DO MODO STANDBY — o plug-in que AGUARDA o QPU.
====================================================
Direção do dono: instalar nos smartphones do mundo, em computadores
e sistemas operacionais clássicos; o serviço ativo é a decisão
clássica EXATA em bytecode Zephirum; quando o QPU chegar, o mesmo
certificado roteia.

Fatos exigidos (SB1..SB4):
  SB1 probe honesto: QPU_REAL=False, STATUS=AGUARDANDO, motivo §12 —
      NUNCA encena conexão quântica; SDKs listados como SIMULADORES;
  SB2 decisão clássica ativa SEM SDK: gateway sem argumento sdk não
      importa numpy/qiskit/cirq no processo (runtime puro de stdlib —
      apto a smartphones);
  SB3 paridade standby: o recibo standby carrega a MESMA decisão e o
      MESMO certificado que o caminho normal (CERT_HASH idêntico);
  SB4 arquitetura QPU-ready: o certificado não depende da presença
      de SDK ou QPU — quando houver QPU, só o probe muda.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugin"))

R2 = "0.70710678118654752"
SRC = ("ASK:\n    question: entangled == 1\nMODEL:\n    type: "
       "entanglement\n    state: %s,0,0,%s\n" % (R2, R2))


def main():
    # SB1: probe honesto — nunca encena QPU
    from zephirum_quantum_plugin import qpu_probe
    pr = qpu_probe()
    assert pr["QPU_REAL"] is False, pr
    assert pr["STATUS"] == "AWAITING", pr
    assert "§12" in pr["MOTIVO"], pr
    assert "SIMULATORS" in pr["MOTIVO"], pr
    assert "without changing the certificate path" in pr["PRONTO_PARA"], pr
    print("SB1: probe honesto — QPU REAL: FALSO, STATUS: AGUARDANDO, "
          "SDKs declarados SIMULADORES (§12), roteamento futuro sem "
          "mudar o caminho de certificado")

    # SB2: decisão clássica SEM SDK — runtime puro de stdlib
    code = ("import sys; sys.path.insert(0, %r); "
            "from zephirum_quantum_plugin import gateway; "
            "r, ok = gateway(%r); "
            "assert ok and r['verdict'] == 1; "
            "assert not any(m.split('.')[0] in ('numpy', 'qiskit', "
            "'cirq') for m in sys.modules); "
            "print('puro')" % (os.path.join(HERE, "..", "plugin"), SRC))
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "puro" in r.stdout, r.stderr[:300]
    print("SB2: decisão clássica ativa SEM importar numpy/qiskit/cirq "
          "(runtime stdlib puro — apto a smartphones do mundo todo)")

    # SB3: paridade standby — mesmo certificado
    from zephirum_quantum_plugin import gateway, standby_receipt
    rec_normal, _ = gateway(SRC)
    rec_sb, ok = standby_receipt(SRC)
    assert ok and rec_sb["cert"]["CERT_HASH"] == \
        rec_normal["cert"]["CERT_HASH"]
    assert rec_sb["verdict"] == rec_normal["verdict"] == 1
    assert rec_sb["standby"]["STATUS"] == "AWAITING"
    print("SB3: recibo standby carrega a MESMA decisão e o MESMO "
          "CERT_HASH do caminho normal — standby é estado, não "
          "degradação")

    # SB4: CLI do standby end-to-end
    ex = os.path.join(HERE, "..", "plugin", "examples",
                      "bell_phi_plus.zeph")
    r = subprocess.run(["zephirum-q", ex, "--standby"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:200]
    assert "AWAITING" in r.stdout and "VERDICT     1" in r.stdout
    r = subprocess.run(["zephirum-q", "--qpu-probe"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "AWAITING" in r.stdout, r.stdout
    print("SB4: CLI --standby e --qpu-probe end-to-end — o plug-in "
          "que o mundo instala HOJE e o QPU encontra pronto AMANHÃ")

    print()
    print("MODO STANDBY: PASS — plug-in quântico instalável nos "
          "smartphones/computadores clássicos do mundo, decisão "
          "clássica exata ATIVA (bytecode Zephirum, zero QPU), "
          "QPU AGUARDANDO com recibo honesto (§12); arquitetura "
          "QPU-ready: quando o hardware chegar, o mesmo certificado "
          "roteia")


if __name__ == "__main__":
    main()
