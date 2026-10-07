#!/usr/bin/env python3
"""
BATERIA DO PLUG-IN EM LINGUAGEM — o algoritmo quântico É ZEPHIRUM.
================================================================
Fatos exigidos (Z1..Z5, SP1, SG1):
  Z1  vereditos/detalhes exatos == referência independente (Fraction
      direta, outra implementação) em 100% dos casos — inclusive
      estados INVÁLIDOS, decididos por flag e determinísticos;
  Z2  o zvm (C puro, SEM Python no runtime) devolve pilha idêntica;
  Z3  UNITS == comprimento (1 LOAD/caractere) nos dois motores;
  Z4  TRACE_HASH idêntico entre motores (determinismo);
  Z5  tripla concordância na CONCORRÊNCIA exata (C = 2|det|/n),
      no determinante e na norma — teoria: Wootters PRL 1998,
      Nielsen & Chuang cap. 2;
  SP1 recibo à mão: Bell Phi+ -> C=1, emaranhado; produto -> C=0;
      parcial (3/5,4/5) -> C=24/25, > 0.9 é 1 e > 0.96 é 0;
  SG1 SINAIS: amplitudes negativas ('-' unário) decidem exatamente
      (Bell Psi- emaranhado, C=1) — o sinal é da linguagem.
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
from zephirum_plugin_lang import (encode, build_plugin_program,
                                  ref_plugin_decision)
from test_vm_c import serialize

ZVM = os.path.join(HERE, "verifier_indep", "zvm")


def _c_run(chars, prog):
    """Roda no zvm. Retorna (fracs, units, trace) ou ("WALL", stderr)
    quando o caso excede o muro C DECLARADO de 10^12 (§12: recusa
    com recibo, nunca silêncio — precisão arbitrária é da referência
    e da VM Python)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".zvm",
                                     delete=False) as f:
        f.write(serialize(chars, len(chars), prog))
        path = f.name
    try:
        r = subprocess.run([ZVM, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    if r.returncode != 0:
        assert "muro" in r.stderr or "10^12" in r.stderr, \
            "falta sem recibo do muro: %s" % r.stderr[:200]
        return ("WALL", r.stderr.strip()[:120])
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


def _mag(ref):
    """Maior magnitude (num/den) dos resultados — decide se o caso
    cabe no muro C de 10^12."""
    m = 1
    for v in (ref["det"], ref["nsq"], ref["C"]):
        m = max(m, abs(v.numerator), v.denominator)
    return m
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
    R2 = "0.70710678118654752"
    casos = [
        ("Bell Phi+", f"{R2},0,0,{R2}", "entangled == 1"),
        ("produto |00>", "1,0,0,0", "entangled == 1"),
        ("separavel superposicao", f"{R2},{R2},0,0", "entangled == 1"),
        ("parcial 3/5-4/5", "0.6,0,0,0.8", "concurrence > 0.9"),
        ("limiar justo acima", "0.6,0,0,0.8", "concurrence > 0.96"),
        ("limiar exato >=", "0.6,0,0,0.8", "concurrence >= 0.96"),
        ("limiar exato ==", "0.6,0,0,0.8", "concurrence == 0.96"),
        ("t negativo", "1,0,0,-1", "concurrence > 0"),
        ("Bell racional (1,0,0,1)", "1,0,0,1", "entangled == 1"),
        ("Bell Psi- racional", "0,1,-1,0", "entangled == 1"),
        ("sinal na 1a amplitude", "-1,0,0,1", "entangled == 1"),
        ("Bell 17 digitos (muro C)", f"{R2},0,0,{R2}",
         "entangled == 1"),
        ("Psi- 17 digitos (muro C)", f"0,{R2},-{R2},0",
         "entangled == 1"),
        ("fracao literal", "1/2,0,0,1/2", "entangled == 1"),
        ("3 amplitudes", "1,2,3", "entangled == 1"),
        ("estado nulo", "0,0,0,0", "entangled == 1"),
    ]
    # SP1: recibo à mão — teoria universal
    assert ref_plugin_decision(f"{R2},0,0,{R2}", "entangled == 1")[
        "C"] == 1
    assert ref_plugin_decision("1,0,0,0", "entangled == 1")["C"] == 0
    r3 = ref_plugin_decision("0.6,0,0,0.8", "concurrence > 0.9")
    assert r3["C"] == Fraction(24, 25) and r3["verdict"] == 1
    assert ref_plugin_decision("0.6,0,0,0.8",
                               "concurrence > 0.96")["verdict"] == 0

    ok = 0
    for nome, st, q in casos:
        chars = encode(st)
        prog = build_plugin_program(chars, q)
        vm = ZephirumVM(chars, len(chars))
        vm.run(prog)
        got = list(vm.last_stack)
        ref = ref_plugin_decision(st, q)
        want = [ref["det"], ref["nsq"], ref["C"], ref["verdict"],
                ref["valid"], Fraction(len([x for x in st.split(",")
                                     if x.strip()]))]
        assert got == want, (nome, got, want)               # Z1
        assert vm.units == len(st), (nome, vm.units)         # Z3
        sig_c = _c_run(chars, prog)
        if _mag(ref) > 10 ** 12:                  # fora do muro C (§12)
            assert sig_c[0] == "WALL", (nome, sig_c)   # recusa com recibo
            assert got == want and vm.units == len(st), nome  # Z1/Z3
            ok += 1
            continue
        assert sig_c[0] != "WALL", (nome, sig_c)
        fracs_c, u_c, th_c = sig_c
        assert fracs_c == got, (nome, fracs_c, got)        # Z2
        assert u_c == vm.units, (nome)                       # Z3
        assert th_c == vm.trace_hash(), (nome)               # Z4
        assert Fraction(fracs_c[2]) == got[2], nome         # Z5
        ok += 1

    # SG1: sinais — Psi- RACIONAL decide emaranhado nos dois motores
    chars = encode("0,1,-1,0")
    prog = build_plugin_program(chars, "entangled == 1")
    vm = ZephirumVM(chars, len(chars))
    vm.run(prog)
    assert vm.last_stack[2] == 1 and vm.last_stack[3] == 1
    sig_c = _c_run(chars, prog)
    assert sig_c[0] != "WALL", sig_c
    assert sig_c[0][2] == 1 and sig_c[0][3] == 1

    print("PLUG-IN EM LINGUAGEM: %d/%d estados quânticos decididos "
          "POR BYTECODE ZEPHIRUM — parse com sinais, determinante de "
          "Schmidt, concorrência exata por multiplicação cruzada "
          "(4·det²·q² ~ p²·n²), comparação por diferença vs 0; "
          "estados inválidos por FLAG, nunca crash" % (ok, ok))
    print("TRIPLO: VM Python == zvm C == referência independente — "
          "pilha (det, n, C, verdict, valid, NV), UNITS == comprimento "
          "e TRACE_HASH idênticos")
    print("Z2: no zvm (C puro) NÃO HÁ PYTHON no runtime — o Python é "
          "só emissor/interpretador, como javac/JVM; estados de 17 "
          "dígitos FALHAM no C com o muro DECLARADO de 10^12 (recibo, "
          "nunca silêncio) e a VM Python decide exata")
    print("SP1+SG1: recibos à mão (Bell C=1, produto C=0, parcial "
          "24/25 nos limiares) e SINAIS negativos exatos (Psi-)")
    print("RESULTADO: PASS — o plug-in quântico agora É Zephirum; a "
          "decisão é da linguagem, o ecossistema é só interprete")


if __name__ == "__main__":
    main()
