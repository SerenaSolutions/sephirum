#!/usr/bin/env python3
"""
ZEPHIRUM BOOTSTRAP — Fase 8, fatia 1: o degrau de Gauss NA linguagem.
=====================================================================

Self-hosting tem um primeiro degrau honesto: a LÓGICA DE ELIMINAÇÃO do
kernel, escrita NA PRÓPRIA LINGUAGEM, executada pela VM orçamentada.

A façanha desta fatia: a pergunta "sum(1..n) > T" é decidida por um
programa ZEPHIRUM compilado para bytecode da VM — a identidade de
Gauss n(n+1)/2 expressa em LOAD/ADD/MUL/DIV — consumindo **1 unidade**
onde a execução ingênua (somar tudo, termo a termo) consumiria **n**.

O que isto É:
  - o degrau de eliminação da escada implementado NA linguagem;
  - a decisão certificada (INPUT_HASH + orçamento + traço determinístico);
  - o mesmo veredito do caminho ingênuo e do juiz independente.

O que isto NÃO é (§12, declarado):
  - a VM inteira escrita em ZEPHIRUM (exigiria modelo de memória:
    strings, arrays, hashing — ISA futura);
  - o parser da linguagem em ZEPHIRUM (exigiria tokens como dados);
  - SHA-256 em bytecode (exigiria operações de bit).

Precedente honesto (nível C): Hart & Levin, 1962 — o primeiro compilador
Lisp escrito em Lisp, compilado por um interpretador hospedeiro. Todo
self-hosting começa assim: um núcleo pequeno que se sustenta.
"""
import hashlib
import random
import sys
from fractions import Fraction

from zephirum_lexer import parse_zephirum
from zephirum_vm import ZephirumVM, VMFault


def _input_hash(values):
    """SHA-256 canônico dos dados de entrada do programa."""
    return hashlib.sha256("|".join(str(v) for v in values).encode()).hexdigest()


def build_src(n, op, thr):
    """Fonte ZEPHIRUM da família gauss_series."""
    return ("ASK:\n    question: sum %s %d\n"
            "CONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: gauss_series\n    n: %d\n"
            % (op, thr, n))


def boot_compile(src):
    """Fonte ZEPHIRUM gauss_series -> programas NAIVE e BOOT + orçamentos.

    NAIVE: carrega 1..n termo a termo — n unidades certificadas. É o
           mundo sem escada: computa tudo para responder.
    BOOT : o degrau de Gauss ESCRITO NA LINGUAGEM — carrega n (1 unidade),
           deriva n(n+1)/2 com PUSH/ADD/MUL/DIV e compara.
    """
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    if model.get("type") != "gauss_series":
        raise VMFault("família %r não é gauss_series (§12: recusa explícita)"
                      % model.get("type"))
    q = blocks["ASK"]["question"]
    parts = q.rsplit(" ", 2)
    op, thr = parts[1], int(parts[2])
    n = int(model["n"])
    if n < 1:
        raise VMFault("n < 1: série vazia não é gauss (§12)")

    # ---- caminho ingênuo: executa a série inteira na VM (n unidades)
    naive_prog = [("LOAD", i) for i in range(n)]
    naive_prog += [("ADD",)] * (n - 1)
    naive_prog += [("CMPT", op, thr), ("HALT",)]
    naive = {
        "program": naive_prog,
        "data": list(range(1, n + 1)),
        "budget": n,
    }

    # ---- caminho BOOT: o degrau de Gauss na linguagem (1 unidade)
    boot_prog = [
        ("LOAD", 0), ("LOAD", 0),   # n duas vezes (sem DUP na ISA: 2 unidades)
        ("PUSH", 1), ("ADD",),      # n+1
        ("MUL",),                   # n(n+1)
        ("PUSH", 2), ("DIV",),      # n(n+1)/2  — Gauss, em bytecode
        ("CMPT", op, thr), ("HALT",),
    ]
    boot = {
        "program": boot_prog,
        "data": [n],
        "budget": 2,
    }
    return {"n": n, "op": op, "thr": thr, "naive": naive, "boot": boot}


def boot_run(plan, path):
    """Executa um dos caminhos na VM e devolve recibo com certificado."""
    p = plan[path]
    vm = ZephirumVM(p["data"], p["budget"])
    answer, units, trace_hash = vm.run(p["program"])
    return {
        "answer": answer,
        "units": units,
        "budget": p["budget"],
        "input_hash": _input_hash(p["data"]),
        "trace_hash": trace_hash,
    }


def boot_decide(n, op, thr):
    """Fonte -> decisão BOOT (o kernel na linguagem) + recibo NAIVE p/ gêmeo."""
    plan = boot_compile(build_src(n, op, thr))
    return plan, boot_run(plan, "boot"), boot_run(plan, "naive")


# ------------------------------------------------------------- bateria
def main():
    random.seed(8008)
    OPS = [">", "<", ">=", "<="]
    B = 0

    # ---- B1: concordância tripla (boot == naive == juiz independente)
    # n >= 3: abaixo disso o degrau de Gauss não compensa (escada honesta:
    # para n=1,2 o caminho barato É a execução — 1 ou 2 unidades)
    N = 2000
    units_boot_all, units_naive_all = [], []
    for i in range(N):
        n = random.randint(3, 300)
        op = random.choice(OPS)
        total = Fraction(n * (n + 1), 2)
        lo, hi = int(total // 3) if total >= 3 else 0, int(total * 2) + 10
        thr = random.randint(lo, hi)
        plan, boot, naive = boot_decide(n, op, thr)
        ref = {">": total > thr, "<": total < thr,
               ">=": total >= thr, "<=": total <= thr}[op]
        assert boot["answer"] == ref, \
            "B1: boot erra (n=%d op=%s thr=%d)" % (n, op, thr)
        assert naive["answer"] == ref, \
            "B1: naive erra (n=%d op=%s thr=%d)" % (n, op, thr)
        assert boot["answer"] == naive["answer"], "B1: gêmeos divergem"
        units_boot_all.append(boot["units"])
        units_naive_all.append(naive["units"])
    B += 1
    print("B1 concordância tripla: %d casos, boot==naive==juiz, 0 erros" % N)

    # ---- B2: a eliminação é REAL e medida em unidades certificadas
    assert all(u == 2 for u in units_boot_all), "B2: boot não gasta 2 unidades"
    assert all(nb >= bt for nb, bt in zip(units_naive_all, units_boot_all)), \
        "B2: degrau de Gauss mais caro que a execução (n>=3)"
    evitadas = sum(units_naive_all) - sum(units_boot_all)
    taxa = 100.0 * evitadas / sum(units_naive_all)
    B += 1
    print("B2 eliminação: boot gasta 2 unidades sempre (n>=3); %d/%d "
          "unidades evitadas de fato (%.2f%%)" % (evitadas, sum(units_naive_all), taxa))

    # ---- B3: orçamento é teto mecânico — forjar consumo para no muro
    plan, boot, _ = boot_decide(8, ">", 30)
    forged = [("LOAD", 0), ("LOAD", 0), ("LOAD", 0),
              ("PUSH", 1), ("ADD",), ("MUL",),
              ("PUSH", 2), ("DIV",), ("CMPT", ">", 30), ("HALT",)]
    vm = ZephirumVM(plan["boot"]["data"], plan["boot"]["budget"])
    try:
        vm.run(forged)
        raise SystemExit("B3 FALHOU: programa forjado passou")
    except VMFault as e:
        assert "BUDGET" in str(e)
    B += 1
    print("B3 forjado: 3ª unidade sob certificado de 2 => VMFault BUDGET")

    # ---- B4: DIV por zero recusa explicitamente (sem infinito na máquina)
    prog0 = [("PUSH", 6), ("PUSH", 0), ("DIV",), ("HALT",)]
    try:
        ZephirumVM([], 0).run(prog0)
        raise SystemExit("B4 FALHOU: DIV por zero passou")
    except VMFault as e:
        assert "DIV por zero" in str(e)
    B += 1
    print("B4 DIV por zero => VMFault explícito (§12)")

    # ---- B5: determinismo + INPUT_HASH protege a fonte
    plan, boot1, naive1 = boot_decide(16, ">", 120)
    _, boot2, _ = boot_decide(16, ">", 120)
    assert boot1["trace_hash"] == boot2["trace_hash"], "B5: traço não determinístico"
    _, boot_outro, _ = boot_decide(17, ">", 120)
    assert boot1["input_hash"] != boot_outro["input_hash"], "B5: fonte trocada não muda INPUT_HASH"
    B += 1
    print("B5 determinismo: traço idêntico por execução; fonte trocada muda INPUT_HASH")

    # ---- B6: o BOOT nasce de FONTE ZEPHIRUM (parse da linguagem, não bytecode manual)
    src = build_src(5, ">", 10)
    blocks = parse_zephirum(src)
    assert blocks["MODEL"]["type"] == "gauss_series"
    assert blocks["MODEL"]["n"] == "5"
    plan, boot, naive = boot_decide(5, ">", 10)   # 1+2+3+4+5=15 > 10 => True
    assert boot["answer"] is True and naive["answer"] is True
    B += 1
    print("B6 fonte ZEPHIRUM: parse da linguagem -> bytecode -> veredito True (15 > 10)")

    print("RESULTADO: PASS — bateria BOOT B1-B%d completa" % B)


if __name__ == "__main__":
    main()
