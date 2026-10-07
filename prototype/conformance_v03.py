#!/usr/bin/env python3
"""
ZEPHIRUM — CONFORMANCE v0.3 (O padrão executável).
==================================================

Este é o executor oficial de conformidade do padrão v0.3 (docs/
ZEPHIRUM_STANDARD_v0.3.md). Uma implementação só afirma "ZEPHIRUM v0.3"
se este script terminar com:

    CONFORMIDADE ZEPHIRUM v0.3: PASS

Cada battery abaixo é NORMATIVA (§6 do padrão): qualquer FALHA rebaixa a
implementação a "não conforme".
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

BATTERIES = [
    ("zephirum_boot.py",       "degrau de Gauss na linguagem (B1-B6)"),
    ("zephirum_boot_b2.py",    "geométrico e média na linguagem (G1-G6, M1-M4)"),
    ("stress_b2.py",           "resistência B2 (ST1-ST6)"),
    ("zephirum_boot_geo_fin.py",
     "geométrico finito na linguagem + ISA DUP/SWAP/POW (GF1-GF6)"),
    ("test_vm.py",             "ISA, muros e faltas da VM"),
    ("test_zephirum_lang.py",  "equivalência linguagem <-> núcleo"),
    ("run_tests.py",           "soundness do motor ZCA"),
    (os.path.join("verifier_indep", "test_verificador_c.py"),
     "verificador independente em C (Python<->C)"),
    ("test_transpiler_multi.py",
     "transpilador multi-alvo: mesma fonte em Python/C/Java/C#/Qiskit/Cirq"),
    ("test_confront.py",
     "confronto clássico x quântico x exato (CC1-CC5, SDKs opcionais)"),
    ("test_qsim_gateway.py",
     "Q-SIM Gateway: emaranhamento decidido no portao, zero unidades QPU"),
]


def run(name, why):
    p = subprocess.run([sys.executable, os.path.join(HERE, name)],
                       capture_output=True, text=True, timeout=1800)
    out = (p.stdout + p.stderr).strip()
    ok = p.returncode == 0
    return ok, out


def main():
    # stress de escala do repositório (veredito por semente)
    p = subprocess.run([sys.executable, os.path.join(HERE, "stress_test.py"),
                        "5000"], capture_output=True, text=True, timeout=1800)
    stress_ok = p.returncode == 0
    if stress_ok:
        print("PASS stress_test 5000 — escala com veredito verificável")
    else:
        print("FALHA stress_test:", (p.stdout + p.stderr)[-300:])

    falhas = 0
    for name, why in BATTERIES:
        ok, out = run(name, why)
        linha = out.splitlines()[-1] if out else "(sem saída)"
        if ok:
            print("PASS %-24s — %s" % (name, why))
        else:
            falhas += 1
            print("FALHA %s — %s" % (name, linha[:200]))

    if falhas == 0 and stress_ok:
        print("\nCONFORMIDADE ZEPHIRUM v0.3: PASS")
        print("Padrão: docs/ZEPHIRUM_STANDARD_v0.3.md · %d batteries + escala"
              % len(BATTERIES))
        return 0
    print("\nCONFORMIDADE ZEPHIRUM v0.3: FALHA (%d batteries reprovadas)"
          % falhas)
    return 1


if __name__ == "__main__":
    sys.exit(main())
