#!/usr/bin/env python3
"""
BATERIA SPARSE — 13 a 64 qubits por representacao esparsa (zref).
==================================================================
O muro denso de 12 qubits e quebrado HONESTAMENTE: o espaco declarado
e 2^N (N = 1..64) e so o SUPORTE (<= 256 entradas) e enumerado.
Criterio exato: separabilidade plena recursiva sobre o suporte
(menores 2x2 por nivel de achatamento), aritmetica Frac exata.

NUMERO: confrontos C == referencia Python == certificado do transpilador.
GENERO: GHZ-N, W-N (excitacao unica), produtos, fatores adjacentes,
       estados genericos esparsos (oraculo Python).
GRAU: varredura N = 13..64 sem erro (exigencia do dono).
"""
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from nexa_core import parse_nexa, NCA
from zephirum_transpiler_multi import transpile, VMFault

ZREF = os.path.join(HERE, "zref")
random.seed(20261009)


def _run_zref(src):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".zeph",
                                     delete=False) as f:
        f.write(src)
        path = f.name
    try:
        r = subprocess.run([ZREF, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    out = {}
    for line in r.stdout.splitlines():
        if line.startswith("VERDICT"):
            out["verdict"] = int(line.split()[1])
        elif line.startswith("HASH"):
            out["hash"] = line.split()[1]
        elif line.startswith("UNITS"):
            out["units"] = int(line.split()[1])
    return out, r.returncode, r.stderr


def _src(state_s, qline):
    return ("ASK:\n    question: %s\nCONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: entanglement\n    state: %s\n"
            % (qline, state_s))


def _decide_py(src):
    return NCA(parse_nexa(src), "zref").compile()


def main():
    if not os.path.exists(ZREF):
        print("FAIL: zref nao compilado"); return 1
    n_ok = n_oraculo = 0

    def check(state_s, expected, name):
        nonlocal n_ok, n_oraculo
        for qline in ("entangled == 1", "entangled == 0"):
            src = _src(state_s, qline)
            out, rc, err = _run_zref(src)
            assert rc == 0, (name, qline, err[:200])
            res = _decide_py(src)
            py_v = 1 if res["answer"] is True else 0
            assert out["verdict"] == py_v, (name, qline, out, py_v)
            cert = transpile(src)["cert"]
            assert out["hash"] == cert["input_hash"], (name, qline)
            assert out["units"] == cert["units"] == 0
            if expected is not None:
                raw = out["verdict"] if qline == "entangled == 1" \
                    else 1 - out["verdict"]
                assert raw == expected, (name, qline, raw, expected)
            else:
                n_oraculo += 1
            n_ok += 1

    # ---------- GRAU: escada GHZ esparsa 13..64 ----------
    for N in range(13, 65):
        st = "sparse(%d) 0:0.7071, %d:0.7071" % (N, (1 << N) - 1)
        check(st, 1, "GHZ%d" % N)

    # ---------- GENERO 1: W-N (excitacao unica) ----------
    for N in (3, 5, 8, 12, 20):
        ents = ", ".join("%d:1" % (1 << i) for i in range(N))
        check("sparse(%d) %s" % (N, ents), 1, "W%d" % N)

    # ---------- GENERO 2: produtos e fatores ----------
    check("sparse(20) 0:0.5, 1:0.5", 0, "adjacente_0_1")   # |0..0> (x) |+>
    check("sparse(20) 2:0.5, 3:0.5", 0, "adjacente_2_3")   # |0..01> (x) |+>
    check("sparse(20) 123456:1", 0, "produto_unico")      # |bitstring>
    check("sparse(64) 18446744073709551615:1", 0, "produto_64")
    check("sparse(20) 0:3, 5:2, 17:7", 1, "tres_entradas")  # generico 3
    # Bell denso continua (regressao da familia densa)
    check("0.7071,0,0,0.7071", 1, "bell_denso")

    # ---------- NUMERO: genericos esparsos (oraculo) ----------
    for _ in range(30):
        N = random.randint(4, 20)
        k = random.randint(2, 8)
        poss = random.sample(range(1 << min(N, 20)), k)
        ents = ", ".join("%d:%d/%d" % (i, random.randint(1, 9),
                                      random.randint(1, 12)) for i in poss)
        check("sparse(%d) %s" % (N, ents), None, "gen"); n_oraculo -= 1

    # ---------- recusas e muros ----------
    out, rc, err = _run_zref(_src("sparse(20) 0:0.5, 1048576:0.5",
                                  "entangled == 1"))
    assert rc == 2 and "espaco 2^N" in err, err
    try:
        transpile(_src("sparse(20) 0:0.5, 1048576:0.5", "entangled == 1"))
        assert False
    except VMFault:
        pass
    n_ok += 1
    out, rc, err = _run_zref(_src("sparse(4) 0:0.5, 0:0.5", "entangled == 1"))
    assert rc == 2 and "duplicado" in err, err
    try:
        _decide_py(_src("sparse(4) 0:0.5, 0:0.5", "entangled == 1"))
        assert False
    except ValueError:
        pass
    n_ok += 1
    out, rc, err = _run_zref(_src("sparse(65) 0:0.5, 1:0.5", "entangled == 1"))
    assert rc == 2 and "N = 1..64" in err, err
    n_ok += 1
    big = ", ".join("%d:1" % i for i in range(300))
    out, rc, err = _run_zref(_src("sparse(12) %s" % big, "entangled == 1"))
    assert rc == 2 and "256 entradas" in err, err
    n_ok += 1
    out, rc, err = _run_zref(_src("sparse(20) 0:0.70710678, 1:0.5",
                                  "entangled == 1"))
    assert rc == 3 and "OVERFLOW" in err, err
    n_ok += 1

    print("SPARSE C-PURO: %d confrontos PASS (C == referencia Python, "
          "INPUT_HASH == certificado, UNITS 0)" % n_ok)
    print("GRAU: escada GHZ esparsa 13..64 (52 degraus) SEM ERRO — o muro "
          "denso de 12 qubits foi quebrado honestamente")
    print("GENERO: W-N (excitacao unica), produtos de bitstring, fatores "
          "adjacentes, genericos (%d pelo oraculo)" % n_oraculo)
    print("MUROS §12: espaco 2^N (N=1..64), suporte <= 256, duplicatas, "
          "indice fora do espaco, amplitude > 10^4 — todos recusados")
    print("RESULTADO: PASS — decisao exata ate 64 qubits sem enumerar "
          "2^64, sem QPU no caminho")
    return 0


if __name__ == "__main__":
    sys.exit(main())
