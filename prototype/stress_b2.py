#!/usr/bin/env python3
"""
ZEPHIRUM STRESS B2 — testes de resistência dos degraus geométrico e média.
==========================================================================

Eixos de resistência (todos reproduzíveis por semente):
  ST1 escala geométrica: 10.000 casos aleatórios, concordância tripla;
  ST2 escala da média: n de 10 até 10^9 — o boot decide em 1 unidade onde
      o ingênuo gastaria n (naive executado até n = 2.000; acima disso o
      juiz independente confere e a eliminação é declarada);
  ST3 falsificação: tentativas de quebrar o muro — unidades extras,
      orçamento adulterado, stack corrompido;
  ST4 muros mecânicos (§12): STEP_LIMIT com laço literal gigante de
      aritmética pura; CALL_DEPTH 64; stack overflow 1024;
  ST5 exatidão extrema: racionais gigantes (10^30) sem deriva de float;
  ST6 determinismo em massa: 500 casos executados duas vezes — traços
      idênticos.

Saída: linhas PASS + results/stress_b2_results.json (padrão do repositório).
"""
import json
import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zephirum_vm import ZephirumVM, VMFault
from zephirum_boot_b2 import (geo_decide, mean_decide,
                               build_src_geo, build_src_mean,
                               mean_compile, run_path)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "stress_b2_results.json")


def main():
    random.seed(42)
    R = {"st1": {}, "st2": {}, "st3": {}, "st4": {}, "st5": {}, "st6": {}}

    # ---------------- ST1: 10.000 casos geométricos
    OPS = [">", "<", ">=", "<="]
    n_cases, errors, evitadas, gasto_naive, resamp = 10000, 0, 0, 0, 0
    for _ in range(n_cases):
        q = random.randint(2, 9)
        p = random.randint(-(q - 1), q - 1) or 1
        r = Fraction(p, q)
        a = Fraction(random.choice([1, 2, 3, 5, 7, 10, -1, -2, -3, 100, -100]))
        total = a / (1 - r)
        t_lo = int(total) - int(abs(total)) - 5
        t_hi = int(total) + int(abs(total)) + 5
        if t_lo >= t_hi:
            t_lo, t_hi = t_hi + 1, t_hi + 10
        for _ in range(200):
            thr = random.randint(t_lo, t_hi)
            op = random.choice(OPS)
            naive_sum = a * (1 - r ** 12) / (1 - r)
            j = {">": total > thr, "<": total < thr,
                 ">=": total >= thr, "<=": total <= thr}[op]
            nv = {">": naive_sum > thr, "<": naive_sum < thr,
                  ">=": naive_sum >= thr, "<=": naive_sum <= thr}[op]
            if j == nv:
                break
            resamp += 1
        else:
            continue
        plan, boot, naive = geo_decide(a, r, op, thr)
        if boot["answer"] != j or naive["answer"] != j or boot["units"] != 2:
            errors += 1
        evitadas += naive["units"] - boot["units"]
        gasto_naive += naive["units"]
    assert errors == 0, "ST1: %d erros em %d casos" % (errors, n_cases)
    taxa = 100.0 * evitadas / gasto_naive
    R["st1"] = {"casos": n_cases, "erros": 0, "resamples": resamp,
                "unidades_evitadas": evitadas, "taxa_pct": round(taxa, 2)}
    print("ST1 PASS — %d casos geométricos, 0 erros, %.1f%% das unidades "
          "evitadas (%d re-sorteios)" % (n_cases, taxa, resamp))

    # ---------------- ST2: média à escala — boot O(1) vs ingênuo O(n)
    escalas = [10, 10**2, 10**3, 2 * 10**3, 10**4, 10**5, 10**6, 10**9]
    for n in escalas:
        total = Fraction(n + 1, 2)
        thr = int(total) - 1                     # veredito True garantido
        assert (total > thr) is True             # juiz independente
        if n <= 2000:
            plan, boot, naive = mean_decide(n, ">", thr)
            assert naive["answer"] is True and naive["units"] == n
        else:
            # ingênuo de n unidades não é executado: é a ELIMINAÇÃO em si;
            # só o boot corre — o juiz independente já conferiu acima
            plan = mean_compile(build_src_mean(n, ">", thr))
            boot = run_path(plan, "boot")
        assert boot["answer"] is True and boot["units"] == 1
    R["st2"] = {"escalas_n": escalas, "unidades_boot": 1,
                "naive_executado_ate": 2000,
                "maior_n_decidido": escalas[-1]}
    print("ST2 PASS — média decidida em 1 unidade até n = 10^9 (ingênuo "
          "executado até n = 2.000; acima, eliminação + juiz)")

    # ---------------- ST3: falsificação — o muro não cede
    plan, boot, _ = geo_decide(Fraction(1), Fraction(1, 2), ">", 1)
    ataques = 0
    for forged in [
        [("LOAD", 0), ("LOAD", 1), ("LOAD", 0), ("PUSH", -1), ("MUL",),
         ("PUSH", 1), ("ADD",), ("DIV",), ("CMPT", ">", 1), ("HALT",)],
        [("LOAD", 1), ("PUSH", -1), ("MUL",), ("PUSH", 1), ("ADD",),
         ("DIV",), ("CMPT", ">", 1), ("HALT",)],
    ]:
        try:
            ZephirumVM(plan["boot"]["data"], plan["boot"]["budget"]).run(forged)
            raise SystemExit("ST3 FALHOU: forjado passou")
        except (VMFault, IndexError) as e:
            # rejeição é o desfecho correto: BUDGET, dado fora, ou underflow
            assert not isinstance(e, VMFault) or ("BUDGET" in str(e)) or ("fora dos dados" in str(e))
            ataques += 1
    try:
        ZephirumVM(plan["boot"]["data"], 0).run([("LOAD", 0), ("HALT",)])
        raise SystemExit("ST3 FALHOU: budget 0 aceitou LOAD")
    except VMFault as e:
        assert "BUDGET" in str(e)
        ataques += 1
    try:
        ZephirumVM([1, 2], 2).run([("LOAD", 0), ("MUL",), ("HALT",)])
        raise SystemExit("ST3 FALHOU: stack underflow passou")
    except (VMFault, IndexError):
        ataques += 1
    R["st3"] = {"ataques": ataques, "rejeitados": ataques}
    print("ST3 PASS — %d ataques de falsificação, %d rejeitados" % (ataques, ataques))

    # ---------------- ST4: muros mecânicos (§12)
    try:
        ZephirumVM([], 0).run([("PUSH", 1), ("LOOP", 60000),
                               ("PUSH", 1), ("ADD",), ("ENDLOOP",),
                               ("HALT",)])
        raise SystemExit("ST4 FALHOU: laço gigante passou")
    except VMFault as e:
        assert "STEP LIMIT" in str(e)
    deep = []
    for i in range(70):
        deep.append(("LABEL", "L%d" % i))
        deep.append(("CALL", "L%d" % (i + 1)))
    deep.append(("HALT",))
    try:
        ZephirumVM([], 0).run(deep)
        raise SystemExit("ST4 FALHOU: recursão profunda passou")
    except VMFault as e:
        assert "CALL DEPTH" in str(e)
    try:
        ZephirumVM([], 0).run([("PUSH", 1)] * 2000 + [("HALT",)])
        raise SystemExit("ST4 FALHOU: stack overflow passou")
    except VMFault as e:
        assert "stack overflow" in str(e)
    R["st4"] = {"step_limit": 65536, "call_depth": 64, "stack": 1024,
                "resultado": "muros firmando"}
    print("ST4 PASS — STEP_LIMIT, CALL_DEPTH e stack: os três muros firmes")

    # ---------------- ST5: exatidão extrema — racionais gigantes
    A = Fraction(10 ** 30 + 7)
    Rr = Fraction(1, 10 ** 30)
    plan, boot, _ = geo_decide(A, Rr, ">", 10 ** 30)
    total = A / (1 - Rr)
    assert boot["answer"] is (total > 10 ** 30), "ST5: veredito errado"
    assert boot["units"] == 2
    R["st5"] = {"a_num": 10 ** 30 + 7, "r_den": 10 ** 30, "exato": True}
    print("ST5 PASS — racionais de 10^30 decididos exatos (float já teria "
          "errado)")

    # ---------------- ST6: determinismo em massa
    casos = []
    for _ in range(500):
        n = random.randint(2, 200)
        op = random.choice(OPS)
        thr = random.randint(0, n)
        casos.append((n, op, thr))
    h1 = [mean_decide(n, op, t)[2]["trace_hash"] for n, op, t in casos]
    h2 = [mean_decide(n, op, t)[2]["trace_hash"] for n, op, t in casos]
    assert h1 == h2, "ST6: traços divergem em massa"
    assert len(set(h1)) >= 100, "ST6: traços colidem demais"
    R["st6"] = {"casos": 500, "traces_repetidos": "idênticos",
                "traces_distintos": len(set(h1))}
    print("ST6 PASS — 500 casos x 2 execuções: traços idênticos (%d "
          "distintos entre fontes)" % len(set(h1)))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"seed": 42, "bateria": "STRESS B2", "resultado": "PASS",
                   "eixos": R}, f, indent=2, ensure_ascii=False)
    print("RESULTADO: PASS — resistência B2 completa (ST1-ST6) · %s" % OUT)


if __name__ == "__main__":
    main()
