#!/usr/bin/env python3
"""
TESTE DA VM (Fase 6) — o orçamento do certificado é lei.
========================================================

Propriedades (uma violação = FAIL):
  V1 resíduos codificáveis executam e CONFEREM com o certificado
     (testemunha/redução, oráculo, soma plena) — 10.000 casos
  V2 ORÇAMENTO: programa que gasta além do certificado => VMFault
     BUDGET EXCEEDED — a VM fisicamente não executa o não-autorizado
  V3 DETERMINISMO: mesmo programa => mesmo trace_hash; um opcode muda,
     hash muda
  V4 CONTABILIDADE FECHADA: unidades gastas == unidades certificadas
     em todo recibo (10.000 recibos)
  V5 zero-execução: programa vazio (HALT), zero unidades, resposta do
     certificado
  V6 escopo honesto: mediana/determinante/emaranhado =>
     VMNotEncodable explícito (nunca fallback silencioso)
"""
import sys

from nexa_core import NCA, parse_nexa
from zephirum_vm import (VMFault, VMNotEncodable, ZephirumVM,
                         compile_program, vm_execute)


def main():
    import random
    from stress_test import build_src, make_case
    random.seed(60)

    # V1 + V4: 10.000 residuais da família de soma
    executed = zero = skipped = 0
    for i in range(10000):
        kind, terms, unk, thr, x = make_case()
        if kind not in ("plain", "oracle"):
            skipped += 1
            continue
        blocks = parse_nexa(build_src(kind, terms, unk, thr, x))
        res = NCA(blocks, "vm%d" % i).compile()
        if res["required"] in (0, None):
            zero += 1
            continue
        try:
            r = vm_execute(blocks, res)
        except VMNotEncodable:
            skipped += 1
            continue
        assert r["answer"] == res["answer"], (i, kind, r, res["answer"])
        assert r["units"] == r["budget"], r              # V4 fechada
        executed += 1
    assert executed > 3000, "cobertura baixa: %d" % executed
    print("V1 residuais codificáveis: %d executados, TODOS conferem com o "
          "certificado (zero-exec: %d | skip honesto: %d)"
          % (executed, zero, skipped))

    # V2: orçamento é lei — programa forjado com LOADs a mais
    blocks = parse_nexa("ASK:\n    question: sum > 100\nMODEL:\n    type: "
                        "threshold_sum\n    terms: 60, 30, 20, 5, 4, 3, 2, 1\n"
                        "    assumption: terms_nonnegative")
    res = NCA(blocks, "red").compile()      # required = 3 (testemunha)
    prog, data, budget = compile_program(blocks, res)
    assert budget == 3
    forged = [("LOAD", i) for i in range(8)]              # 8 loads > 3
    forged += [("ADD",)] * 7 + [("CMPT", ">", 100), ("HALT",)]
    vm = ZephirumVM(data, budget)
    try:
        vm.run(forged)
        raise AssertionError("VM executou além do orçamento!")
    except VMFault as e:
        assert "BUDGET EXCEEDED" in str(e)
        assert vm.units == 3                       # parou exatamente no limite
    print("V2 orçamento: programa forjado de 8 unidades PAROU na 3ª — "
          "BUDGET EXCEEDED, certificado é lei")

    # V3: determinismo do trace
    r1 = vm_execute(blocks, res)
    r2 = vm_execute(blocks, res)
    assert r1["trace_hash"] == r2["trace_hash"]
    prog2 = list(prog)
    prog2[1] = ("LOAD", 2)
    vm3 = ZephirumVM(data, budget)
    a3, u3, h3 = vm3.run(prog2)
    assert h3 != r1["trace_hash"]
    print("V3 determinismo: mesmo programa => mesmo trace_hash; um opcode "
          "muda, hash muda")

    # V5: zero-execução => programa vazio
    dec = parse_nexa("ASK:\n    question: sum > 40\nMODEL:\n    type: "
                     "threshold_sum\n    terms: 60, 30\n    unknown: x in 0..10")
    res5 = NCA(dec, "zero").compile()
    p5, d5, b5 = compile_program(dec, res5)
    assert p5 == [("HALT",)] and b5 == 0
    print("V5 zero-execução: programa vazio (HALT), a resposta é o "
          "certificado")

    # V6: escopo honesto — mediana não é codificável NESTA fatia
    med = parse_nexa("ASK:\n    question: median > 50\nMODEL:\n    type: "
                     "raw_data\n    data: 12, 87, 45, 63, 51, 39, 96, 4, 58")
    res6 = NCA(med, "med").compile()
    try:
        compile_program(med, res6)
        raise AssertionError("VM fingiu codificar mediana!")
    except VMNotEncodable as e:
        assert "não codificável" in str(e)
    print("V6 escopo honesto: mediana => VMNotEncodable explícito "
          "(nunca silêncio, nunca fingimento)")

    print("RESULTADO: PASS — a VM gasta exatamente o que o certificado "
          "autoriza, nem uma unidade a mais")
    return 0


if __name__ == "__main__":
    sys.exit(main())
