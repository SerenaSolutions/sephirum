#!/usr/bin/env python3
"""
BATERIA ENTANGLE-N — 4 a 12 qubits no motor C puro (zref).
==================================================================
Confronta zref (C) contra a referencia Python (NCA) e o certificado
do transpilador em estados de N qubits: veredito, INPUT_HASH, UNITS.
Audita muros §12: 2^N (N<=12), amplitudes, denominador comum,
estado nulo, concurrence.
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
random.seed(20261008)


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


def fs(x):
    return str(x.numerator) if x.denominator == 1 else \
        "%d/%d" % (x.numerator, x.denominator)


def tensorN(singles):
    amps = [Fraction(1)]
    for u in singles:                       # u (x) v (x) ... (ordem q0..qN-1)
        amps = [a * b for a in amps for b in u]
    return amps


def main():
    if not os.path.exists(ZREF):
        print("FAIL: zref nao compilado"); return 1
    n_ok = 0
    n_oraculo = 0

    def check(state, expected=None, name=""):
        nonlocal n_ok, n_oraculo
        st = ",".join(fs(x) for x in state)
        for qline in ("entangled == 1", "entangled == 0"):
            src = _src(st, qline)
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
                pass  # rotulo pelo oraculo Python (duplicado acima)
            n_ok += 1

    # ---------- degraus construidos ----------
    for N in (4, 5, 6):
        ghz = [Fraction(0)] * (2 ** N)
        ghz[0] = ghz[-1] = Fraction(7071, 10000)
        check(ghz, 1, "GHZ%d" % N)
        # produto de N single-qubit states
        prod = tensorN([[Fraction(1), Fraction(1)],
                        [Fraction(1, 2), Fraction(1, 2)],
                        [Fraction(1, 3), Fraction(2, 3)],
                        [Fraction(1, 4), Fraction(3, 4)],
                        [Fraction(2, 3), Fraction(1, 3)],
                        [Fraction(3, 4), Fraction(1, 4)]][:N])
        check(prod, 0, "prod%d" % N)
        # bisseparavel: Bell(q0,q1) (x) |0...0>
        bis = [Fraction(0)] * (2 ** N)
        bis[0] = Fraction(7071, 10000)
        bis[(1 << (N - 1)) | (1 << (N - 2))] = Fraction(7071, 10000)
        check(bis, 1, "bell_prod%d" % N)
        # genericos aleatorios (rotulo via oraculo)
        for _ in range(12):
            a = [Fraction(random.randint(-9, 9) or 1,
                          random.randint(1, 12)) for _ in range(2 ** N)]
            check(a, None, "gen%d" % N); n_oraculo += 1

    # ---------- CIENCIA REAL: quimica, fisica de particulas, espaco ----------
    # H2 em base minima (STO-3G, setor de numero de particula):
    # estrutura |0101> + c|1010> (Kandala et al., Nature 549, 2017);
    # parametros do modelo (nao constantes medidas).
    # Ligacao covalente = emaranhamento; limite ionico = produto.
    h2_eq = [Fraction(0)] * 16
    h2_eq[0b0101] = Fraction(995, 1000)      # adiacao covalente dominante
    h2_eq[0b1010] = Fraction(998, 10000)      # dupla excitacao (ionica)
    check(h2_eq, 1, "H2_equilibrio(covalente)")
    h2_diss = [Fraction(0)] * 16
    h2_diss[0b0101] = h2_diss[0b1010] = Fraction(7071, 10000)
    check(h2_diss, 1, "H2_dissolucao(maximamente_emaranhado)")
    h2_ion = [Fraction(0)] * 16
    h2_ion[0b0101] = Fraction(1)             # limite ionico puro: produto
    check(h2_ion, 0, "H2_limito_ionico(separavel)")
    # Neutrino ("particula fantasma"): par nu-nubar do decaimento Z0,
    # emaranhamento em espaco de flavor (estrutura dos estudos de
    # pares nu-nubar): Bell de flavor (|nue nubare> + |numu nubarmu>)/raiz2
    nu = [Fraction(7071, 10000), 0, 0, Fraction(7071, 10000)]
    check(nu, 1, "par_nu_nubar_Z0(flavor_Bell)")
    # Teste espacial: Bell Phi+ e a classe distribuida por 1200 km no
    # teste de Bell satelital Micius (Yin et al., Science 356, 1140, 2017)
    micius = [Fraction(7071, 10000), 0, 0, Fraction(7071, 10000)]
    check(micius, 1, "Bell_Phi+_classe_Micius(Yin_2017)")

    # ---------- VARREDURA SEM ERRO: N = 4..12 (exigencia do dono) ----------
    for N in range(4, 13):
        ghz = [Fraction(0)] * (2 ** N)
        ghz[0] = ghz[-1] = Fraction(7071, 10000)
        check(ghz, 1, "sweep_GHZ%d" % N)
        prod = tensorN([[Fraction(1, 2), Fraction(1, 2)]] * N)
        check(prod, 0, "sweep_prod%d" % N)

    # ---------- muro: 12 qubits ----------
    ghz12 = [Fraction(0)] * 4096
    ghz12[0] = ghz12[-1] = Fraction(7071, 10000)
    check(ghz12, 1, "GHZ12")
    prod12 = tensorN([[Fraction(1, 2), Fraction(1, 2)]] * 12)
    check(prod12, 0, "prod12")

    # ---------- recusas e muros ----------
    out, rc, err = _run_zref(_src(",".join(["0.5"] * 20), "entangled == 1"))
    assert rc == 2 and "2^N" in err, err
    try:
        transpile(_src(",".join(["0.5"] * 20), "entangled == 1"))
        assert False
    except VMFault:
        pass
    n_ok += 1
    out, rc, err = _run_zref(_src(",".join(["0"] * 4096), "entangled == 1"))
    assert rc == 2 and "nulo" in err, err
    try:
        _decide_py(_src(",".join(["0"] * 4096), "entangled == 1"))
        assert False
    except ValueError:
        pass
    n_ok += 1
    ghz12s = ",".join(["0.7071"] + ["0"] * 4094 + ["0.7071"])
    out, rc, err = _run_zref(_src(ghz12s, "concurrence > 0.5"))
    assert rc == 2 and "N qubits" in err, err
    n_ok += 1
    pr = [9973, 9967, 9949, 9941, 9931, 9929, 9923, 9907]
    st = ",".join("1/%d" % q for q in pr)
    out, rc, err = _run_zref(_src(st + "," + ",".join(["0"] * 8),
                                  "entangled == 1"))
    assert rc == 3 and "10^12" in err, (rc, err)
    n_ok += 1
    out, rc, err = _run_zref(_src(",".join(["0.70710678"] * 16),
                                  "entangled == 1"))
    assert rc == 3 and "OVERFLOW" in err, err
    n_ok += 1

    print("ENTANGLE-N C-PURO: %d confrontos PASS (C == referencia Python, "
          "INPUT_HASH == certificado, UNITS 0)" % n_ok)
    print("DEGRAUS: GHZ/produto/bisseparavel corretos em N=4,5,6 e "
          "GHZ12/prod12 no muro de 12 qubits; %d genericos pelo oraculo"
          % n_oraculo)
    print("CIENCIA REAL: H2 covalente/ionico (quimica), par nu-nubar do Z0 "
          "(neutrino), classe Bell do teste espacial Micius — todos "
          "decididos exatos")
    print("VARREDURA 4..12: GHZ e produto em TODOS os N sem erro (dono: "
          "nao dar erro conforme os qubits aumentam)")
    print("MUROS §12: 2^N (N<=12), estado nulo, concurrence-N recusado, "
          "amplitude >10^4 e D>10^12 declarados OVERFLOW")
    print("RESULTADO: PASS — a escada de eliminacao sobe exata ate "
          "12 qubits, sem QPU no caminho")
    return 0


if __name__ == "__main__":
    sys.exit(main())
