#!/usr/bin/env python3
"""
ZEPHIRUM BOOTSTRAP — Fase 8, fatia 2 (B2): degraus geométrico e média NA linguagem.
================================================================================

Self-hosting, segundo degrau honesto: DUAS famílias novas de eliminação
decididas por programas ZEPHIRUM executados pela VM orçamentada.

  GEOMETRIC_INF  — a pergunta "a série geométrica infinita (a, r), |r| < 1,
                   excede T?" é decidida por a/(1-r) escrita em bytecode:
                   LOAD a, LOAD r, PUSH -1, MUL, PUSH 1, ADD, DIV.
                   Custo: 2 unidades certificadas. A execução ingênua é uma
                   TRUNCAÇÃO de N termos (N unidades) — e nem assim alcança
                   a soma exata: a cauda é infinita. O degrau não é apenas
                   mais barato; é o ÚNICO caminho exato.

  ARITHMETIC_MEAN — a pergunta "a média de 1..n excede T?" é decidida por
                   (n+1)/2 em bytecode: LOAD n, PUSH 1, ADD, PUSH 2, DIV.
                   Custo: 1 unidade certificada — o degrau mais barato da
                   escada. A execução ingênua carrega n termos (n unidades).

Escada honesta (§12, declarada):
  - média: n = 1 é empate de custo (1 = 1) — o kernel EXECUTA; n >= 2 elimina;
  - geométrico: a e r são a evidência mínima (2 unidades) — sem eles não há
    pergunta; a truncação ingênua só é honesta com erro declarado.

O que isto NÃO é (§12):
  - exponenciação em bytecode (o geométrico FINITO (r^(n+1)-r)/(r-1) exigiria
    DUP/SWAP/POW; laço com re-LOAD custa n unidades — eliminação falsa);
  - a VM em ZEPHIRUM (B5); o parser em ZEPHIRUM (B3).

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
def build_src_geo(a, r, op, thr):
    """Fonte ZEPHIRUM da família geometric_inf (a, r racionais exatos)."""
    return ("ASK:\n    question: sum_inf %s %d\n"
            "CONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: geometric_inf\n    a: %s\n    r: %s\n"
            % (op, thr, a, r))


def build_src_mean(n, op, thr):
    """Fonte ZEPHIRUM da família arithmetic_mean."""
    return ("ASK:\n    question: mean %s %d\n"
            "CONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: arithmetic_mean\n    n: %d\n"
            % (op, thr, n))


# ------------------------------------------------------------ compilação
def geo_compile(src, naive_terms=12):
    """Fonte geometric_inf -> programas NAIVE (truncação) e BOOT + orçamentos."""
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    if model.get("type") != "geometric_inf":
        raise VMFault("família %r não é geometric_inf (§12: recusa explícita)"
                      % model.get("type"))
    q = blocks["ASK"]["question"]
    parts = q.rsplit(" ", 2)
    op, thr = parts[1], int(parts[2])
    a = Fraction(model["a"])
    r = Fraction(model["r"])
    if abs(r) >= 1:
        raise VMFault("r=%s não converge (|r| >= 1): a máquina recusa a "
                      "série infinita em vez de mentir (§12)" % r)
    if a == 0:
        raise VMFault("a = 0: série nula não é geométrica (§12)")

    naive_prog = [("LOAD", i) for i in range(naive_terms)]
    naive_prog += [("ADD",)] * (naive_terms - 1)
    naive_prog += [("CMPT", op, thr), ("HALT",)]
    naive = {
        "program": naive_prog,
        "data": [a * r ** k for k in range(naive_terms)],
        "budget": naive_terms,
    }

    # a/(1-r) em bytecode: [a, r] -> a, -r -> 1-r -> a/(1-r)
    boot_prog = [
        ("LOAD", 0), ("LOAD", 1),   # a, r — a evidência mínima (2 unidades)
        ("PUSH", -1), ("MUL",),     # a, -r
        ("PUSH", 1), ("ADD",),      # a, 1-r
        ("DIV",),                   # a/(1-r)  — o infinito decidido exato
        ("CMPT", op, thr), ("HALT",),
    ]
    boot = {
        "program": boot_prog,
        "data": [a, r],
        "budget": 2,
    }
    return {"a": a, "r": r, "op": op, "thr": thr,
            "naive": naive, "boot": boot}


def mean_compile(src):
    """Fonte arithmetic_mean -> programas NAIVE e BOOT + orçamentos.

    NAIVE: carrega 1..n termo a termo (n unidades) e divide — LOAD/ADD
           intercalados para respeitar o muro de stack (1024, §12).
    BOOT : (n+1)/2 NA LINGUAGEM — 1 unidade (n é a evidência mínima).
    """
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    if model.get("type") != "arithmetic_mean":
        raise VMFault("família %r não é arithmetic_mean (§12: recusa "
                      "explícita)" % model.get("type"))
    q = blocks["ASK"]["question"]
    parts = q.rsplit(" ", 2)
    op, thr = parts[1], int(parts[2])
    n = int(model["n"])
    if n < 1:
        raise VMFault("n < 1: média de série vazia não existe (§12)")

    # o ingênuo só se MATERIALIZA até 5000 termos; acima disso o orçamento
    # é declarado (n unidades) mas o programa não é construído — é a
    # eliminação em estado puro: a escada não paga para provar que não
    # precisa computar (§12)
    NAIVE_LIMIT = 5000
    if n <= NAIVE_LIMIT:
        naive_prog = [("LOAD", 0)]
        for i in range(1, n):
            naive_prog += [("LOAD", i), ("ADD",)]
        naive_prog += [("PUSH", n), ("DIV",), ("CMPT", op, thr), ("HALT",)]
        naive = {
            "program": naive_prog,
            "data": list(range(1, n + 1)),
            "budget": n,
        }
    else:
        naive = {"program": None, "data": None, "budget": n}

    # (n+1)/2 em bytecode: o degrau mais barato da escada (1 unidade)
    boot_prog = [
        ("LOAD", 0),               # n — a evidência mínima (1 unidade)
        ("PUSH", 1), ("ADD",),     # n+1
        ("PUSH", 2), ("DIV",),     # (n+1)/2
        ("CMPT", op, thr), ("HALT",),
    ]
    boot = {
        "program": boot_prog,
        "data": [n],
        "budget": 1,
    }
    return {"n": n, "op": op, "thr": thr, "naive": naive, "boot": boot}


def run_path(plan, path):
    """Executa um dos caminhos na VM e devolve recibo com certificado.
    Caminho não materializado (ingênuo acima do limite) devolve None —
    a eliminação não executa o que já provou desnecessário."""
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


def geo_decide(a, r, op, thr):
    plan = geo_compile(build_src_geo(a, r, op, thr))
    return plan, run_path(plan, "boot"), run_path(plan, "naive")


def mean_decide(n, op, thr):
    plan = mean_compile(build_src_mean(n, op, thr))
    return plan, run_path(plan, "boot"), run_path(plan, "naive")


# ------------------------------------------------------------- bateria
def main():
    random.seed(20261007)
    OPS = [">", "<", ">=", "<="]
    B = 0
    resamples = 0

    # ---- G1: 100 casos geométricos, concordância tripla (boot == naive == juiz)
    NG = 100
    units_boot, units_naive = [], []
    tails = 0
    for i in range(NG):
        q = random.randint(2, 9)
        p = random.randint(-(q - 1), q - 1)
        if p == 0:
            p = 1
        r = Fraction(p, q)
        a = Fraction(random.choice([1, 2, 3, 5, 7, 10, -1, -2, -3]))
        total = a / (1 - r)                     # juiz: soma exata
        t_lo = int(total) - int(abs(total)) - 5
        t_hi = int(total) + int(abs(total)) + 5
        if t_lo >= t_hi:
            t_lo, t_hi = t_hi + 1, t_hi + 10
        for _ in range(200):
            thr = random.randint(t_lo, t_hi)
            op = random.choice(OPS)
            naive_sum = a * (1 - r ** 12) / (1 - r)   # 12 termos
            j = {">": total > thr, "<": total < thr,
                 ">=": total >= thr, "<=": total <= thr}[op]
            nv = {">": naive_sum > thr, "<": naive_sum < thr,
                  ">=": naive_sum >= thr, "<=": naive_sum <= thr}[op]
            if j == nv:
                break
            resamples += 1
        else:
            raise SystemExit("G1: não achou threshold honesto (bug)")
        if naive_sum != total:
            tails += 1                          # a truncação NÃO alcança a soma
        plan, boot, naive = geo_decide(a, r, op, thr)
        assert boot["answer"] == j, "G1: boot erra (a=%s r=%s)" % (a, r)
        assert naive["answer"] == nv == j, "G1: naive erra (a=%s r=%s)" % (a, r)
        units_boot.append(boot["units"])
        units_naive.append(naive["units"])
    B += 1
    print("G1 concordância tripla: %d casos geométricos, boot==naive==juiz, "
          "0 erros (%d re-sorteios de threshold honesto)" % (NG, resamples))

    # ---- G2: eliminação REAL em unidades + a truncação nunca é exata
    assert all(u == 2 for u in units_boot), "G2: boot não gasta 2 unidades"
    assert all(nb == 12 for nb in units_naive), "G2: naive não gasta 12 unidades"
    evitadas = sum(units_naive) - sum(units_boot)
    taxa = 100.0 * evitadas / sum(units_naive)
    assert tails == NG, "G2: cauda nula em todos os casos (improvável — bug?)"
    B += 1
    print("G2 eliminação: boot gasta 2 unidades sempre; naive 12; %d/%d "
          "unidades evitadas (%.1f%%) — e a truncação falha a soma exata "
          "em %d/%d casos (a cauda é infinita)" % (evitadas, sum(units_naive),
                                                   taxa, tails, NG))

    # ---- G3: r = 1 não converge — a máquina recusa em vez de mentir
    try:
        geo_compile(build_src_geo(Fraction(1), Fraction(1), ">", 10))
        raise SystemExit("G3 FALHOU: série divergente passou")
    except VMFault as e:
        assert "não converge" in str(e)
    try:
        ZephirumVM([Fraction(1), Fraction(1)], 2).run(
            [("LOAD", 0), ("LOAD", 1), ("PUSH", -1), ("MUL",),
             ("PUSH", 1), ("ADD",), ("DIV",), ("HALT",)])
        raise SystemExit("G3 FALHOU: DIV por zero passou")
    except VMFault as e:
        assert "DIV por zero" in str(e)
    B += 1
    print("G3 divergência: |r| >= 1 recusado em AMBOS os níveis — compilador "
          "('não converge') e VM (DIV por zero, §12)")

    # ---- G4: orçamento é teto mecânico — 3ª unidade sob certificado de 2
    plan, boot, _ = geo_decide(Fraction(1), Fraction(1, 2), ">", 1)
    forged = [("LOAD", 0), ("LOAD", 1), ("LOAD", 0),
              ("PUSH", -1), ("MUL",), ("PUSH", 1), ("ADD",),
              ("DIV",), ("CMPT", ">", 1), ("HALT",)]
    try:
        ZephirumVM(plan["boot"]["data"], plan["boot"]["budget"]).run(forged)
        raise SystemExit("G4 FALHOU: programa forjado passou")
    except VMFault as e:
        assert "BUDGET" in str(e)
    B += 1
    print("G4 forjado geométrico: 3ª unidade sob certificado de 2 => VMFault "
          "BUDGET")

    # ---- G5: determinismo + INPUT_HASH protege a fonte
    plan1, boot1, _ = geo_decide(Fraction(3), Fraction(1, 2), ">", 4)
    _, boot2, _ = geo_decide(Fraction(3), Fraction(1, 2), ">", 4)
    assert boot1["trace_hash"] == boot2["trace_hash"], "G5: traço não determinístico"
    _, boot_outro, _ = geo_decide(Fraction(4), Fraction(1, 2), ">", 4)
    assert boot1["input_hash"] != boot_outro["input_hash"], \
        "G5: fonte trocada não muda INPUT_HASH"
    B += 1
    print("G5 determinismo: traço idêntico por execução; fonte trocada muda "
          "INPUT_HASH")

    # ---- G6: o BOOT nasce de FONTE ZEPHIRUM -> parse -> bytecode -> veredito
    src = build_src_geo(Fraction(1), Fraction(1, 2), ">", 1)
    blocks = parse_zephirum(src)
    assert blocks["MODEL"]["type"] == "geometric_inf"
    assert blocks["MODEL"]["r"] == "1/2"
    plan, boot, naive = geo_decide(Fraction(1), Fraction(1, 2), ">", 1)
    # a=1, r=1/2: 1 + 1/2 + 1/4 + ... = 2 > 1 => True
    assert boot["answer"] is True and naive["answer"] is True
    B += 1
    print("G6 fonte ZEPHIRUM: parse -> bytecode -> veredito True (2 > 1; "
          "1 + 1/2 + 1/4 + ... = 2)")

    # ---- M1: 100 casos de média, concordância tripla
    NM = 100
    ub, un, ns = [], [], []
    for i in range(NM):
        n = random.randint(2, 300)
        op = random.choice(OPS)
        total = Fraction(n + 1, 2)
        lo = max(0, int(total // 3) - 2)
        hi = int(total * 2) + 10
        thr = random.randint(lo, hi)
        ref = {">": total > thr, "<": total < thr,
               ">=": total >= thr, "<=": total <= thr}[op]
        ns.append(n)
        plan, boot, naive = mean_decide(n, op, thr)
        assert boot["answer"] == ref, "M1: boot erra (n=%d)" % n
        assert naive["answer"] == ref, "M1: naive erra (n=%d)" % n
        ub.append(boot["units"]); un.append(naive["units"])
    B += 1
    print("M1 concordância tripla: %d casos de média, boot==naive==juiz, "
          "0 erros" % NM)

    # ---- M2: eliminação REAL — 1 unidade onde o ingênuo gasta n
    assert all(u == 1 for u in ub), "M2: boot não gasta 1 unidade"
    assert un == ns, "M2: naive não gasta n unidades"
    # escada honesta: n=1 é empate (1=1) — o kernel EXECUTA
    plan, boot, naive = mean_decide(1, ">", 0)   # média de 1..1 = 1 > 0
    assert naive["units"] == 1 and boot["units"] == 1
    B += 1
    evitadas_m = sum(un) - sum(ub)
    print("M2 eliminação: boot gasta 1 unidade sempre; naive gasta n "
          "(%d/%d evitadas); n=1 é empate honesto — kernel executa"
          % (evitadas_m, sum(un)))

    # ---- M3: forjado de média — 2ª unidade sob certificado de 1
    plan, boot, _ = mean_decide(10, ">", 5)
    forged = [("LOAD", 0), ("LOAD", 0), ("PUSH", 1), ("ADD",),
              ("PUSH", 2), ("DIV",), ("CMPT", ">", 5), ("HALT",)]
    try:
        ZephirumVM(plan["boot"]["data"], plan["boot"]["budget"]).run(forged)
        raise SystemExit("M3 FALHOU: programa forjado passou")
    except VMFault as e:
        assert "BUDGET" in str(e)
    B += 1
    print("M3 forjado média: 2ª unidade sob certificado de 1 => VMFault BUDGET")

    # ---- M4: fonte ZEPHIRUM -> parse -> bytecode -> veredito
    src = build_src_mean(10, ">", 5)
    blocks = parse_zephirum(src)
    assert blocks["MODEL"]["type"] == "arithmetic_mean"
    plan, boot, naive = mean_decide(10, ">", 5)  # média 1..10 = 5.5 > 5 => True
    assert boot["answer"] is True and naive["answer"] is True
    B += 1
    print("M4 fonte ZEPHIRUM: parse -> bytecode -> veredito True (5.5 > 5)")

    print("RESULTADO: PASS — bateria B2 completa (G1-G6 + M1-M4)")


if __name__ == "__main__":
    main()
