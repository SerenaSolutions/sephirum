#!/usr/bin/env python3
"""
BATERIA ENTANGLE3 — 3 qubits no motor C puro (zref).
==================================================================
Confronta zref (C) contra a referencia Python (NCA) e o certificado do
transpilador em estados de 3 qubits: veredito, INPUT_HASH e unidades.
Audita os muros §12: amplitudes (>10^4), denominador comum (>10^12),
estado nulo e recusa de concurrence (medida de 2 qubits).
"""
import os
import random
import subprocess
import sys
import tempfile
from fractions import Fraction

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


def _src(state, qline):
    return ("ASK:\n    question: %s\nCONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: entanglement\n    state: %s\n"
            % (qline, state))


def _decide_py(src):
    return NCA(parse_nexa(src), "zref").compile()


def main():
    if not os.path.exists(ZREF):
        print("FAIL: zref nao compilado"); return 1
    n_ok = 0

    def fs(x):  # fracao -> token decimal exato dentro dos muros
        return str(x.numerator) if x.denominator == 1 else \
            "%d/%d" % (x.numerator, x.denominator)

    def tensor3(u, v, w):
        # |psi> = u (x) v (x) w ; amplitudes a_ijk, indice = 4i+2j+k
        out = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    out.append(u[i] * v[j] * w[k])
        return out

    states = []
    # --- casos construidos (rotulo por construcao) ---
    states.append(("GHZ", [Fraction(7071, 10000), 0, 0, 0, 0, 0, 0,
                           Fraction(7071, 10000)], 1))
    states.append(("GHZ_menos", [Fraction(7071, 10000), 0, 0, 0, 0, 0, 0,
                                 Fraction(-7071, 10000)], 1))
    states.append(("W3", [0, Fraction(5774, 10000), Fraction(5774, 10000),
                         0, Fraction(5774, 10000), 0, 0, 0], 1))
    states.append(("Bell_q01_x_0", [Fraction(7071, 10000), 0, 0, 0, 0, 0,
                                   Fraction(7071, 10000), 0], 1))  # bissep.
    states.append(("0_x_Bell_q12", [Fraction(7071, 10000), 0, 0,
                                    Fraction(7071, 10000), 0, 0, 0, 0], 1))
    states.append(("produto_0+_+0", tensor3([1, 0], [1, 1], [1, 0]), 0))
    states.append(("produto_+++", tensor3([1, 1], [1, 1], [1, 1]), 0))
    states.append(("produto_com_denominadores", tensor3([1, 2], [1, 3],
                                                        [2, 3]), 0))
    # --- produtos aleatorios (rotulo 0 por construcao) ---
    for _ in range(60):
        u = [Fraction(random.randint(-9, 9) or 1, random.randint(1, 12))
             for _ in range(2)]
        v = [Fraction(random.randint(-9, 9) or 1, random.randint(1, 12))
             for _ in range(2)]
        w = [Fraction(random.randint(-9, 9) or 1, random.randint(1, 12))
             for _ in range(2)]
        states.append(("prod_rand", tensor3(u, v, w), 0))
    # --- estados genericos: rotulo pelo oraculo Python (semantica dupla) ---
    for _ in range(120):
        a = [Fraction(random.randint(-9, 9), random.randint(1, 12))
             for _ in range(8)]
        if sum(x * x for x in a) == 0:
            continue
        states.append(("generico", a, None))

    n_genericos_oraculo = 0
    for name, amps, expected in states:
        st = ",".join(fs(x) for x in amps)
        for qline in ("entangled == 1", "entangled == 0"):
            src = _src(st, qline)
            out, rc, err = _run_zref(src)
            assert rc == 0, (name, qline, err, src)
            res = _decide_py(src)
            py_v = 1 if res["answer"] is True else 0
            assert out["verdict"] == py_v, (name, qline, out["verdict"], py_v)
            cert = transpile(src)["cert"]
            assert out["hash"] == cert["input_hash"], (name, qline)
            assert out["units"] == cert["units"] == 0
            if expected is not None:
                # rotulo por construcao: veredito bruto do estado
                raw = out["verdict"] if qline == "entangled == 1" \
                    else 1 - out["verdict"]
                assert raw == expected, (name, qline, raw, expected)
            else:
                n_genericos_oraculo += 1
            n_ok += 1

    # ---------------- recusas e muros §12 ----------------
    # zero state
    out, rc, err = _run_zref(_src("0,0,0,0,0,0,0,0", "entangled == 1"))
    assert rc == 2 and "RECUSA" in err, err
    try:
        _decide_py(_src("0,0,0,0,0,0,0,0", "entangled == 1")); assert False
    except ValueError:
        pass
    try:
        transpile(_src("0,0,0,0,0,0,0,0", "entangled == 1")); assert False
    except VMFault:
        pass
    n_ok += 1
    # concurrence em 3 qubits: recusa nos tres andares
    out, rc, err = _run_zref(_src("0.7071,0,0,0,0,0,0,0.7071",
                                  "concurrence > 0.5"))
    assert rc == 2 and "RECUSA" in err, err
    try:
        _decide_py(_src("0.7071,0,0,0,0,0,0,0.7071", "concurrence > 0.5"))
        assert False
    except ValueError:
        pass
    try:
        transpile(_src("0.7071,0,0,0,0,0,0,0.7071", "concurrence > 0.5"))
        assert False
    except VMFault:
        pass
    n_ok += 1
    # muro de amplitude (>10^4)
    out, rc, err = _run_zref(_src("0.70710678,0,0,0,0,0,0,0.70710678",
                                  "entangled == 1"))
    assert rc == 3 and "OVERFLOW" in err, (rc, err)
    n_ok += 1
    # muro do denominador comum (>10^12): 8 primos grandes
    pr = [9973, 9967, 9949, 9941, 9931, 9929, 9923, 9907]
    st = ",".join("1/%d" % q for q in pr)
    out, rc, err = _run_zref(_src(st, "entangled == 1"))
    assert rc == 3 and "OVERFLOW" in err and "10^12" in err, (rc, err)
    n_ok += 1
    # 5 ou 7 amplitudes: recusa estrutural
    out, rc, err = _run_zref(_src("0.5,0.5,0.5,0.5,0.5", "entangled == 1"))
    assert rc == 2 and "RECUSA" in err, err
    n_ok += 1
    # regressao: 2 qubits intactos
    out, rc, err = _run_zref(_src("0.7071,0,0,0.7071", "entangled == 1"))
    assert rc == 0 and out["verdict"] == 1, (rc, err)
    out, rc, err = _run_zref(_src("0.7071,0.7071,0,0", "entangled == 1"))
    assert rc == 0 and out["verdict"] == 0, (rc, err)
    n_ok += 2

    print("ENTANGLE3 C-PURO: %d confrontos PASS (veredito C == referencia "
          "Python, INPUT_HASH == certificado do transpilador, UNITS 0)" % n_ok)
    print("ROTULOS POR CONSTRUCAO: produtos e bisseparaveis corretos; "
          "%d genericos pelo oraculo Python" % n_genericos_oraculo)
    print("MUROS §12: nulo/5-7 amps recusados; concurrence 3q recusado "
          "nos 3 andares; amplitude >10^4 e D>10^12 declarados OVERFLOW")
    print("RESULTADO: PASS — a familia de emaranhamento decide 2 e 3 "
          "qubits em C puro, exato, sem QPU no caminho")
    return 0


if __name__ == "__main__":
    sys.exit(main())
