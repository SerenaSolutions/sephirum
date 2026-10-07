#!/usr/bin/env python3
"""
BATERIA B3.1 — o LEXER de assinatura NA LINGUAGEM.
================================================

Fatos exigidos por caso (L1..L4, SP1, WR1):
  L1  a assinatura léxica em bytecode == referência independente
      (mesma semântica, outra implementação) em 100% dos casos;
  L2  o zvm (C puro) devolve a MESMA assinatura (byte a byte);
  L3  UNITS == comprimento do texto (1 LOAD por caractere) nos
      dois motores — ler o dado custa o dado, nem mais nem menos;
  L4  TRACE_HASH idêntico entre motores (execução determinística);
  SP1 caso derivado À MÃO da especificação ("3|1/2" -> [2? não:
      3 tokens, soma 6, 2 ops]) — o recibo antes do traço;
  WR1 o muro de bit é VERIFICADO, não assumido: "999999999999"
      acumula mod 2^32 e a bateria prova o wrap igual em todos
      os três caminhos.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "verifier_indep"))

from zephirum_vm import ZephirumVM
from zephirum_lex_lang import encode, build_lex_program, ref_lex
from test_vm_c import serialize

ZVM = os.path.join(HERE, "verifier_indep", "zvm")


def _c_stack_and_meta(chars, prog):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".zvm",
                                     delete=False) as f:
        f.write(serialize(chars, len(chars), prog))
        path = f.name
    try:
        r = subprocess.run([ZVM, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    assert r.returncode == 0, r.stderr[:200]
    stack, units, trace = [], None, None
    grab = False
    for line in r.stdout.splitlines():
        if line.startswith("STACK"):
            grab = True
        elif line.startswith("FRAC") and grab:
            stack.append(int(line.split()[1]))
        elif line.startswith("UNITS"):
            units = int(line.split()[1])
        elif line.startswith("TRACE_HASH"):
            trace = line.split()[1]
    return stack, units, trace


def main():
    casos = ["3|1/2", "gauss_series: n=10", "",
             "a + b - 42 = 99!", "0.70710678,0,0,0.70710678",
             "   ", "999999999999", "café 42",
             "ZEPHIRUM 0.3 (fatia B3)",
             "linha1|linha2,3.14|x<y>=z"]

    # SP1: recibo derivado A MAO da especificacao — "3|1/2":
    # tokens {3, 1, 2} -> n_tok=3, soma=6; ops {|, /} -> 2; resto zero
    assert ref_lex("3|1/2") == [3, 6, 2, 0, 0, 0], ref_lex("3|1/2")

    ok = 0
    for s in casos:
        chars = encode(s)
        prog = build_lex_program(chars)
        vm = ZephirumVM(chars, len(chars))
        vm.run(prog)
        sig_py = [int(v) for v in vm.last_stack]
        ref = ref_lex(s)
        assert sig_py == ref, (s, sig_py, ref)          # L1
        assert vm.units == len(s), (s, vm.units)         # L3
        sig_c, u_c, th_c = _c_stack_and_meta(chars, prog)
        assert sig_c == sig_py, (s, sig_c, sig_py)      # L2
        assert u_c == vm.units, (s, u_c, vm.units)      # L3
        assert th_c == vm.trace_hash(), (s, "trace")    # L4
        ok += 1

    # WR1: o muro de bit VERIFICADO — 999999999999 mod 2^32
    #   = 999999999999 - 232*4294967296 = 3525163521... calculado:
    wrap = 999999999999 % 4294967296
    assert ref_lex("999999999999")[1] == wrap
    chars = encode("999999999999")
    vm = ZephirumVM(chars, len(chars))
    vm.run(build_lex_program(chars))
    assert int(vm.last_stack[1]) == wrap               # wrap igual
    sig_c, _, _ = _c_stack_and_meta(
        chars, build_lex_program(chars))
    assert sig_c[1] == wrap                             # nos 3 caminhos

    print("B3.1 LEXER NA LINGUAGEM: %d textos LIDOS EM BYTECODE "
          "(classificação por máscaras 0/1, tokens numéricos com "
          "MUL 10/ADD, fecho em EOF) — assinatura léxica de 6 valores "
          "exata em 100%% dos casos" % ok)
    print("TRIPLO: VM Python == zvm C == referência independente — "
          "assinatura, UNITS (== comprimento) e TRACE_HASH idênticos")
    print("SP1: recibo derivado à mão da especificação (3|1/2 -> "
          "[3,6,2,0,0,0]) conferiu antes do traço")
    print("WR1: muro de bit VERIFICADO — 12 dígitos dão wrap mod 2^32 "
          "idêntico nos três caminhos (%d), nunca silêncio" % wrap)
    print("RESULTADO: PASS — a linguagem agora LÊ a própria entrada de "
          "dados; a codificação texto->inteiros segue no hospedeiro "
          "(§12), a LÓGICA léxica é da linguagem")


if __name__ == "__main__":
    main()
