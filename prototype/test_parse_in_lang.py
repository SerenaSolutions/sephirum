#!/usr/bin/env python3
"""
BATERIA B3.2 — o PARSER de dados NA LINGUAGEM.
=============================================

Fatos exigidos por caso (P1..P4, SP1, FL1):
  P1  os valores exatos (Fraction) parseados em bytecode == os da
      referência independente (mesma gramática, outra implementação);
  P2  o zvm (C puro) devolve a MESMA pilha (pares p/q idênticos);
  P3  UNITS == comprimento (1 LOAD por caractere) nos dois motores;
  P4  TRACE_HASH idêntico entre motores (execução determinística);
  SP1 recibo derivado À MÃO da especificação ("3|1/2" -> [3, 1/2,
      VALID=1, NV=2]) antes do traço;
  FL1 a linguagem RECONHECE ERRO SEM CRASH: '1/0', '1/', '1.',
      '3||2', 'abc', 'café 42', '0.1.2' — tudo decide por flag
      VALID=0, nunca exceção escondida.
"""
import os
import subprocess
import sys
import tempfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "verifier_indep"))

from zephirum_vm import ZephirumVM
from zephirum_parse_lang import encode, build_parse_program, ref_parse
from test_vm_c import serialize

ZVM = os.path.join(HERE, "verifier_indep", "zvm")


def _c_run(chars, prog):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".zvm",
                                     delete=False) as f:
        f.write(serialize(chars, len(chars), prog))
        path = f.name
    try:
        r = subprocess.run([ZVM, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    assert r.returncode == 0, r.stderr[:200]
    fracs, units, trace, grab = [], None, None, False
    for line in r.stdout.splitlines():
        if line.startswith("STACK"):
            grab = True
        elif line.startswith("FRAC") and grab:
            p, q = line.split()[1:3]
            fracs.append(Fraction(int(p), int(q)))
        elif line.startswith("UNITS"):
            units = int(line.split()[1])
        elif line.startswith("TRACE_HASH"):
            trace = line.split()[1]
    return fracs, units, trace


def main():
    casos = ["3|1/2", "1/2|3/4|5", "0.6,0,0,0.8", "42", "1.5|0.25",
             "", "3|", "3||2", "abc", "1/0", "1/3|0.25|7",
             "0.70710678,0,0,0.70710678", "1.", "1/",
             "3.14159|2.71828", "0.1.2", "café 42",
             "9|0.333333333", "1/3|2/3|3/3|4/3|5/3"]

    # SP1: recibo à mão — "3|1/2": valores {3, 1/2}, válido, 2 valores
    assert ref_parse("3|1/2") == [Fraction(3), Fraction(1, 2),
                                  Fraction(1), Fraction(2)]

    ok = 0
    for s in casos:
        chars = encode(s)
        prog = build_parse_program(chars)
        vm = ZephirumVM(chars, len(chars))
        vm.run(prog)
        sig_py = list(vm.last_stack)
        ref = ref_parse(s)                              # P1
        assert sig_py == ref, (s, sig_py, ref)
        assert vm.units == len(s), (s, vm.units)        # P3
        sig_c, u_c, th_c = _c_run(chars, prog)
        assert sig_c == sig_py, (s, sig_c, sig_py)      # P2
        assert u_c == vm.units, (s, u_c)                # P3
        assert th_c == vm.trace_hash(), (s, "trace")    # P4
        ok += 1

    # FL1: erros por FLAG, sem crash — contados e verificados
    erros = ["1/0", "1/", "1.", "3||2", "abc", "café 42", "0.1.2"]
    fl = 0
    for s in erros:
        chars = encode(s)
        vm = ZephirumVM(chars, len(chars))
        vm.run(build_parse_program(chars))             # nenhuma exceção
        assert vm.last_stack[-2] == 0, s               # VALID == 0
        sig_c, _, _ = _c_run(chars, build_parse_program(chars))
        assert sig_c[-2] == 0, s
        fl += 1

    print("B3.2 PARSER NA LINGUAGEM: %d textos de dados do certificado "
          "(inteiros, frações n/d, decimais) INTERPRETADOS em bytecode "
          "— valores exatos (Fraction) na pilha, 100%% conforme a "
          "gramática declarada" % ok)
    print("TRIPLO: VM Python == zvm C == referência independente — "
          "valores (p/q), UNITS (== comprimento) e TRACE_HASH idênticos")
    print("SP1: recibo derivado à mão da especificação (3|1/2 -> "
          "[3, 1/2, 1, 2]) conferiu antes do traço")
    print("FL1: %d/%d entradas inválidas decididas por FLAG VALID=0 "
          "nos dois motores — erro é veredito, nunca crash escondido"
          % (fl, len(erros)))
    print("RESULTADO: PASS — a linguagem agora LÊ e INTERPRETA a "
          "própria entrada de dados; tabela de tokens endereçável "
          "e sinais seguem declarados (§12), B5 mais perto")


if __name__ == "__main__":
    main()
