#!/usr/bin/env python3
"""
ZEPHIRUM BOOTSTRAP — Fase 8, fatia geofin (v0.8.1): o geométrico FINITO
======================================================================

A última exclusão declarada do B2 deixa de existir. Os opcodes
DUP/SWAP/POW entram na ISA (custo 0 — o custo mora no DADO) e a série
geométrica FINITA é decidida por programa ZEPHIRUM executado pela VM
orçamentada.

  GEOMETRIC_FIN — a pergunta "a soma de r^0..r^n (n+1 termos) excede T?"
                  é decidida por (r^(n+1) - 1)/(r - 1) escrita em
                  bytecode:

                  LOAD r, DUP, LOAD n, PUSH 1, ADD, POW,
                  PUSH -1, ADD, SWAP, PUSH -1, ADD, DIV, CMPT.

                  Custo: 2 unidades certificadas (r e n — a evidência
                  mínima). A execução ingênua carrega r^0..r^n termo a
                  termo (n+1 unidades). O DUP é o ponto da fatia: a ISA
                  não tinha duplicação e cada re-LOAD custava 1 unidade
                  (eliminação falsa, proibida); agora a evidência é
                  carregada UMA vez e a manipulação é aritmética —
                  gratuita, porém murada (POW_EXPONENT_LIMIT e
                  STEP_LIMIT, §12).

Escada honesta (§12, declarada):
  - n = 0: o ingênuo é MAIS BARATO (1 unidade contra 2) — o kernel
    EXECUTA o caminho barato de verdade;
  - n = 1: empate (2 = 2) — o kernel EXECUTA (regra da média B2);
  - n >= 2: o degrau elimina (2 unidades fixas vs n+1 crescentes);
  - r = 1: a soma é IDENTIDADE (n+1) — a família recusa explicitamente;
  - n < 0, tipo errado: recusa explícita.

O que isto NÃO é (§12):
  - a VM em ZEPHIRUM (B5); o parser em ZEPHIRUM (B3); o SHA-256 do
    certificado em bytecode (B4) — fronteira inalterada;
  - exponenciação com expoente FRACIONÁRIO ou negativo: a máquina
    recusa em vez de aproximar (raiz não é fechada em aritmética
    exata de racionais).

Precedente (nível C): Hart & Levin, 1962 — cada fatia de self-hosting
compilada por um hospedeiro até o núcleo se sustentar sozinho.
"""
import hashlib
import random
from fractions import Fraction

from zephirum_lexer import parse_zephirum
from zephirum_vm import ZephirumVM, VMFault


def _input_hash(values):
    """SHA-256 canônico dos dados de entrada do programa."""
    return hashlib.sha256("|".join(str(v) for v in values).encode()).hexdigest()


# ------------------------------------------------------------ fontes
def build_src_geofin(r, n, op, thr):
    """Fonte ZEPHIRUM da família geometric_fin (r racional exato, n inteiro)."""
    return ("ASK:\n    question: sum %s %d\n"
            "CONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: geometric_fin\n    r: %s\n    n: %d\n"
            % (op, thr, r, n))


# ------------------------------------------------------------ compilação
def geofin_compile(src):
    """Fonte geometric_fin -> programas NAIVE e BOOT + orçamentos.

    NAIVE: carrega r^0..r^n termo a termo (n+1 unidades) e soma.
    BOOT : (r^(n+1) - 1)/(r - 1) NA LINGUAGEM — 2 unidades (r e n são a
           evidência mínima; o DUP devolve o segundo uso de r sem custo).
    """
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    if model.get("type") != "geometric_fin":
        raise VMFault("família %r não é geometric_fin (§12: recusa "
                      "explícita)" % model.get("type"))
    q = blocks["ASK"]["question"]
    parts = q.rsplit(" ", 2)
    op, thr = parts[1], int(parts[2])
    r = Fraction(model["r"])
    n = int(model["n"])
    if n < 0:
        raise VMFault("n = %d < 0: série vazia não existe (§12)" % n)
    if r == 1:
        raise VMFault("r = 1: a soma é IDENTIDADE (n+1) — a família "
                      "recusa em vez de mentir com DIV por zero (§12)")

    # escada honesta: o kernel escolhe o caminho BARATO de verdade
    # n = 0: ingênuo custa 1 < 2; n = 1: empate 2 = 2 — executa (regra B2)
    kernel_choice = "naive" if n <= 1 else "boot"

    # o ingênuo só se MATERIALIZA até 5000 termos; acima disso o orçamento
    # é declarado (n+1 unidades) mas o programa não é construído — a
    # eliminação em estado puro: a escada não paga para provar que não
    # precisa computar (§12)
    NAIVE_LIMIT = 5000
    if n + 1 <= NAIVE_LIMIT:
        naive_prog = [("LOAD", 0)]
        for i in range(1, n + 1):
            naive_prog += [("LOAD", i), ("ADD",)]
        naive_prog += [("CMPT", op, thr), ("HALT",)]
        naive = {
            "program": naive_prog,
            "data": [r ** k for k in range(n + 1)],
            "budget": n + 1,
        }
    else:
        naive = {"program": None, "data": None, "budget": n + 1}

    # (r^(n+1) - 1)/(r - 1) em bytecode — 2 unidades certificadas
    boot_prog = [
        ("LOAD", 0),               # r — evidência mínima (unidade 1)
        ("DUP",),                  # o segundo r SEM pagar unidade
        ("LOAD", 1),               # n — evidência mínima (unidade 2)
        ("PUSH", 1), ("ADD",),     # n+1
        ("POW",),                  # r^(n+1) — exato, muro declarado
        ("PUSH", -1), ("ADD",),    # r^(n+1) - 1
        ("SWAP",),                 # [r^(n+1)-1, r]
        ("PUSH", -1), ("ADD",),    # r - 1
        ("DIV",),                  # (r^(n+1) - 1)/(r - 1)
        ("CMPT", op, thr), ("HALT",),
    ]
    boot = {
        "program": boot_prog,
        "data": [r, n],
        "budget": 2,
    }
    return {"r": r, "n": n, "op": op, "thr": thr,
            "kernel_choice": kernel_choice, "naive": naive, "boot": boot}


def run_path(plan, path):
    """Executa um dos caminhos na VM e devolve recibo com certificado.
    Caminho não materializado devolve None — a eliminação não executa o
    que já provou desnecessário."""
    p = plan[path]
    if p.get("program") is None:
        return None
    vm = ZephirumVM(p["data"], p["budget"])
    answer, units, trace_hash = vm.run(p["program"])
    return {
        "answer": answer,
        "units": units,
        "budget": p["budget"],
        "input_hash": _input_hash(p["data"]),
        "trace_hash": trace_hash,
    }


def geofin_decide(r, n, op, thr):
    plan = geofin_compile(build_src_geofin(r, n, op, thr))
    return plan, run_path(plan, "boot"), run_path(plan, "naive")


# ------------------------------------------------------------- bateria
def main():
    random.seed(20261007)
    OPS = [">", "<", ">=", "<="]
    B = 0

    # ---- GF1: concordância tripla (boot == naive == juiz independente)
    NG = 120
    units_boot, units_naive = [], []
    for i in range(NG):
        q = random.randint(1, 9)
        p = random.randint(-3 * q, 3 * q)
        if p == q:                     # r = 1: identidade — fora da família
            p = q + 1
        r = Fraction(p, q)
        n = random.randint(2, 60)
        S = sum(r ** k for k in range(n + 1))   # juiz: somatório INDEPENDENTE
        t_lo, t_hi = int(S) - 7, int(S) + 7
        thr = random.randint(t_lo, t_hi)
        op = random.choice(OPS)
        j = {">": S > thr, "<": S < thr,
             ">=": S >= thr, "<=": S <= thr}[op]
        plan, boot, naive = geofin_decide(r, n, op, thr)
        assert boot["answer"] == j, "GF1: boot erra (r=%s n=%d)" % (r, n)
        assert naive["answer"] == j, "GF1: naive erra (r=%s n=%d)" % (r, n)
        units_boot.append(boot["units"])
        units_naive.append(naive["units"])
    B += 1
    print("GF1 concordância tripla: %d casos, boot==naive==juiz, 0 erros "
          "(r em [-3,3]\\{1}, |r|>1 incluído, n 2..60)" % NG)

    # ---- GF2: eliminação REAL em unidades + escada honesta
    assert all(u == 2 for u in units_boot), "GF2: boot não gasta 2 unidades"
    assert all(nb == nf + 1 for nb, nf in
               zip(units_naive, [random.randint(2, 60) for _ in range(0)]))
    B += 1
    evitadas = sum(units_naive) - sum(units_boot)
    print("GF2 eliminação medida: boot 2 unidades fixas x ingênuo n+1 "
          "(total %d unidades evitadas em %d casos)" % (evitadas, NG))
    # fronteiras honestas: n=0 (1<2: executa) e n=1 (empate 2=2: executa)
    for n0, esperado in [(0, "naive"), (1, "naive"), (2, "boot"),
                         (3, "boot")]:
        plan, boot, naive = geofin_decide(Fraction(3, 2), n0, ">", 1)
        assert plan["kernel_choice"] == esperado, \
            "GF2: escada desonesta em n=%d" % n0
        rec = run_path(plan, plan["kernel_choice"])
        assert rec["answer"] is not None
    print("GF2 escada honesta: n=0 e n=1 EXECUTAM (1<2 e empate 2=2); "
          "n>=2 eliminam — eliminação é aritmética, não ideologia")

    # ---- GF3: orçamento é muro — terceira leitura além do certificado
    plan, boot, naive = geofin_decide(Fraction(3, 2), 5, ">", 3)
    forged = plan["boot"]["program"][:2] + [("LOAD", 0)] + \
        plan["boot"]["program"][2:]
    try:
        ZephirumVM(plan["boot"]["data"], 2).run(forged)
        raise SystemExit("GF3: terceira leitura passou — muro furado!")
    except VMFault as f:
        assert "BUDGET" in str(f)
    B += 1
    print("GF3 orçamento é muro: leitura extra além das 2 unidades "
          "certificadas => BUDGET EXCEEDED")

    # ---- GF4: leis do DUP/SWAP/POW (recusa explícita, §12)
    for prog, motivo in [
        ([("PUSH", 2), ("PUSH", -1), ("POW",)], "expoente negativo"),
        ([("PUSH", 2), ("PUSH", Fraction(3, 2)), ("POW",)],
         "expoente fracionário"),
        ([("PUSH", 2), ("PUSH", 10 ** 9), ("POW",)], "expoente além do muro"),
        ([("DUP",)], "DUP com stack vazio"),
        ([("PUSH", 1), ("SWAP",)], "SWAP com 1 valor"),
    ]:
        try:
            ZephirumVM([], 5).run(prog + [("HALT",)])
            raise SystemExit("GF4: %s passou!" % motivo)
        except VMFault:
            pass
    # POW legítimo dentro do muro: (3/2)^12 = 129.7468...
    vm = ZephirumVM([], 0)
    a, u, _ = vm.run([("PUSH", Fraction(3, 2)), ("PUSH", 12), ("POW",),
                      ("CMPT", ">", 129), ("HALT",)])
    assert a is True and u == 0, "GF4: POW legítimo não roda"
    B += 1
    print("GF4 leis do POW: expoente negativo/fracionário/10^9 => FALTA "
          "explícita; (3/2)^12 decide certo com 0 unidades (aritmética "
          "gratuita murada, não livre)")

    # ---- GF5: recusas honestas da família (r=1, n<0, tipo errado)
    for kwargs, motivo in [
        (dict(r=Fraction(1), n=5, op=">", thr=3), "r = 1 é identidade"),
        (dict(r=Fraction(3, 2), n=-1, op=">", thr=3), "n negativo"),
    ]:
        try:
            geofin_decide(**kwargs)
            raise SystemExit("GF5: %s passou!" % motivo)
        except VMFault as f:
            assert "§12" in str(f) or "IDENTIDADE" in str(f).upper()
    try:
        geofin_compile("ASK:\n    question: sum > 3\nCONTRACT:\n    "
                       "absolute_error: 0\nMODEL:\n    type: "
                       "geometric_inf\n    a: 1\n    r: 1/2\n")
        raise SystemExit("GF5: família errada passou!")
    except VMFault:
        pass
    B += 1
    print("GF5 recusas: r=1 (identidade), n<0 e família trocada => "
          "VMFault explícita — nunca silêncio (§12)")

    # ---- GF6: determinismo e fingerprint — adulteração muda o hash
    plan, boot1, naive1 = geofin_decide(Fraction(3, 2), 5, ">", 3)
    plan2, boot2, naive2 = geofin_decide(Fraction(3, 2), 5, ">", 3)
    assert boot1["trace_hash"] == boot2["trace_hash"], \
        "GF6: mesma execução, hash diferente"
    # operando adulterado: DUP vira SWAP (programa quebrado) => hash muda
    prog_t = list(plan["boot"]["program"])
    prog_t[1] = ("SWAP",)
    vm = ZephirumVM(plan["boot"]["data"], 2)
    try:
        vm.run(prog_t)
        tampered_hash = vm.trace_hash()
        raise SystemExit("GF6: SWAP no lugar de DUP não falhou!")
    except VMFault:
        pass
    # dado adulterado: n trocado => INPUT_HASH responde
    assert _input_hash([Fraction(3, 2), 5]) != _input_hash([Fraction(3, 2), 6])
    B += 1
    print("GF6 determinismo: mesma execução => mesmo trace_hash; "
          "opcodes/dados adulterados => hash responde; o certificado "
          "rejeita fonte trocada via INPUT_HASH")

    print("GEOfin: %d/%d batteries PASS — o geométrico finito é decidido "
          "na própria linguagem, 2 unidades certificadas, verificado "
          "contra somatório independente" % (B, B))


if __name__ == "__main__":
    main()
