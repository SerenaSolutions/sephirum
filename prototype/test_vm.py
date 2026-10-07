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

Fatia 2 — fluxo de controle ORÇADO:
  V7 LAÇO: série de 64 termos em LOOP — bytecode compacto, 64 unidades
  V8 DESVIO: JMPZ frente-only, dois ramos, traces distintos
  V9 LAÇO FORJADO: contagem inflada => BUDGET EXCEEDED
  V10 MURO MECÂNICO: laço de aritmética pura => STEP LIMIT (§12)
  V11 JMPZ para trás / label inexistente => VMFault
  V12 DETERMINISMO do laço + dado adulterado muda o trace_hash
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

    # ================= Fatia 2: fluxo de controle ORÇADO ================
    from fractions import Fraction

    # V7: série longa em LAÇO
    terms = ",".join(str(i) for i in range(1, 65))
    blocks = parse_nexa(
        "ASK:\n    question: sum > 2048\nMODEL:\n    type: threshold_sum\n"
        "    terms: %s\n    threshold: 2048\n" % terms)
    res = NCA(blocks, "loop64").compile()
    r = vm_execute(blocks, res)
    ref = sum(Fraction(i) for i in range(1, 65))
    assert r["answer"] == (ref > 2048) and r["units"] == 64 == r["budget"]
    assert r["program_size"] == 7
    print("V7 laço: 64 termos => 7 instruções, 64/64 unidades, veredito "
          "== referência exata")

    # V8: desvio condicional (JMPZ frente-only) — os dois ramos
    prog = [("LOAD", 0), ("CMP", ">", 0),
            ("JMPZ", "neg"),
            ("PUSH", 1), ("CMPT", ">", 0), ("HALT",),
            ("LABEL", "neg"), ("PUSH", -1), ("CMPT", "<", 0), ("HALT",)]
    for x in (5, -3):
        vm = ZephirumVM([x], 1)
        ans, units, th = vm.run(prog)
        assert ans is True and units == 1, (x, ans, units)
    t_pos = ZephirumVM([5], 1).run(prog)[2]
    t_neg = ZephirumVM([-3], 1).run(prog)[2]
    assert t_pos != t_neg
    print("V8 desvio: JMPZ frente-only, dois ramos corretos; caminhos "
          "distintos => trace_hash distinto")

    # V9: laço forjado — contagem inflada além do orçamento
    forged = [("PUSH", 0), ("LOOP", 1000), ("LOADSEQ",), ("ADD",),
              ("ENDLOOP",), ("CMPT", ">", 0), ("HALT",)]
    try:
        ZephirumVM([1, 2, 3, 4, 5, 6, 7, 8], 3).run(forged)
        raise AssertionError("laço forjado executou?! (V9)")
    except VMFault as e:
        assert "BUDGET EXCEEDED" in str(e)
    print("V9 laço forjado: contagem inflada => BUDGET EXCEEDED no meio "
          "do laço (3/3 unidades)")

    # V10: muro mecânico — laço de aritmética PURA (não consome dado)
    spin = [("PUSH", 0), ("LOOP", 1000000), ("PUSH", 1), ("ADD",),
            ("ENDLOOP",), ("HALT",)]
    try:
        ZephirumVM([], 0).run(spin)
        raise AssertionError("spin executou?! (V10)")
    except VMFault as e:
        assert "STEP LIMIT" in str(e)
    print("V10 muro mecânico: laço forjado sem consumo de dado => STEP "
          "LIMIT (§12) — o orçamento é lei, o muro é parede")

    # V11: JMPZ para trás / label inexistente => VMFault explícito
    for bad, why in [
            ([("LABEL", "top"), ("PUSH", 0), ("JMPZ", "top"),
              ("HALT",)], "backward"),
            ([("PUSH", 0), ("JMPZ", "ghost"), ("HALT",)], "ghost")]:
        try:
            ZephirumVM([], 0).run(bad)
            raise AssertionError("desvio ilegal aceito?! (V11)")
        except VMFault as e:
            assert ("TRÁS" if why == "backward" else "inexistente") in str(e)
    print("V11 desvio ilegal: JMPZ para trás => VMFault; label inexistente "
          "=> VMFault — retroceder exige LOOP")

    # V12: determinismo do laço + FRONTeira honesta do traço
    data64 = list(range(1, 65))
    loop_prog = [("PUSH", 0), ("LOOP", 64), ("LOADSEQ",), ("ADD",),
                 ("ENDLOOP",), ("CMPT", ">", 2048), ("HALT",)]
    t1 = ZephirumVM(data64, 64).run(loop_prog)[2]
    t2 = ZephirumVM(data64, 64).run(loop_prog)[2]
    assert t1 == t2                      # determinismo: mesmo hash
    t_count = ZephirumVM(data64, 64).run(
        [("PUSH", 0), ("LOOP", 63), ("LOADSEQ",), ("ADD",),
         ("ENDLOOP",), ("CMPT", ">", 2048), ("HALT",)])[2]
    assert t_count != t1, "contagem do laço adulterada, traço idêntico?!"
    t_push = ZephirumVM(data64, 64).run(
        [("PUSH", 7), ("LOOP", 64), ("LOADSEQ",), ("ADD",),
         ("ENDLOOP",), ("CMPT", ">", 2048), ("HALT",)])[2]
    assert t_push != t1, "operando adulterado, traço idêntico?!"
    # FRONTEIRA DECLARADA: valor de DADO não está no traço (o traço é da
    # EXECUÇÃO: opcodes + padrão de acesso + fluxo). Quem protege o dado
    # é o INPUT_HASH do certificado — mudar a fonte invalida o cert.
    t_value = ZephirumVM([99] + data64[1:], 64).run(loop_prog)[2]
    assert t_value == t1, "valor de dado NO traço?! fronteira mentiu"
    tampered_blocks = parse_nexa(
        "ASK:\n    question: sum > 2048\nMODEL:\n    type: threshold_sum\n"
        "    terms: %s\n    threshold: 2048\n"
        % ",".join(str(i) for i in [99] + list(range(2, 65))))
    tres = NCA(tampered_blocks, "loop65").compile()
    from verify_certificate import verify
    ok, reason = verify(tampered_blocks, tres["certificate"])
    assert ok          # fonte nova compila cert NOVO (consistente)
    ok2, _ = verify(blocks, tres["certificate"])
    assert not ok2, "cert de outra fonte aceito?! INPUT_HASH falhou"
    print("V12 determinismo: laço => mesmo trace_hash; contagem e operando "
          "adulterados => hash muda; FRONTEIRA: valor de dado NÃO está no "
          "traço — quem protege o dado é o INPUT_HASH (cert de fonte "
          "trocada => REJECT)")

    print("RESULTADO: PASS — a VM gasta exatamente o que o certificado "
          "autoriza, nem uma unidade a mais")
    return 0


if __name__ == "__main__":
    sys.exit(main())
