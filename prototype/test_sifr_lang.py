#!/usr/bin/env python3
"""
Testes da Fase 2 da SIFR (lexer próprio + transpilador).

(1) Equivalência de parser: para N problemas aleatórios, o IR do parser
    de tokens próprios (parse_sifr) deve ser IGUAL ao da Fase 1 (parse_nexa).
(2) Fuzz de expressões: avaliação própria (eval_expr) == safe_eval (ast).
(3) Transpilador: para N problemas, o código Python gerado, executado,
    responde o mesmo que o motor NCA decide (e 'Z' quando UNKNOWN).

Exit 0 = tudo passou. Qualquer divergência = falha.
"""
import random
import sys

from nexa_core import parse_nexa, NCA, safe_eval
from sifr_lexer import parse_sifr, eval_expr, tokenize, SifrSyntaxError
from sifr_transpiler import transpile
from stress_test import make_case, build_src

random.seed(1234)
N_EQUIV, N_FUZZ, N_TRANSP = 50000, 20000, 500


def test_equivalence():
    for i in range(N_EQUIV):
        kind, terms, unk, thr, x = make_case()
        src = build_src(kind, terms, unk, thr, x)
        old = parse_nexa(src)
        new = parse_sifr(src)
        assert old == new, "IR divergente no caso %d:\n%s\n%r\n%r" % (i, src, old, new)
        tokenize(src)  # lexer não pode rejeitar fonte válida
    print("(1) parse_sifr == parse_nexa em %d casos: OK" % N_EQUIV)


def _rand_expr(depth=0):
    if depth > 4 or random.random() < 0.3:
        return str(random.randint(0, 20))
    op = random.choice(["+", "-", "*", "//", "%", "**"])
    if op == "**":
        # base E expoente literais: impede cadeias de potência astronômicas
        a = str(random.randint(0, 20))
        b = str(random.randint(0, 6))
    elif op in ("//", "%"):
        a = _rand_expr(depth + 1)
        b = str(random.randint(1, 9))      # divisor positivo: sem divisão por zero
    else:
        a = _rand_expr(depth + 1)
        b = _rand_expr(depth + 1)
    return "(%s %s %s)" % (a, op, b) if random.random() < 0.5 else "%s %s %s" % (a, op, b)


def test_fuzz():
    for i in range(N_FUZZ):
        e = _rand_expr()
        try:
            ref = safe_eval(e)
        except ZeroDivisionError:
            continue
        got = eval_expr(e)
        assert abs(ref - got) < 1e-9, "expr divergente %r: %r != %r" % (e, ref, got)
    print("(2) eval_expr == safe_eval em %d expressões: OK" % N_FUZZ)


def test_syntax_errors():
    bad = ["ASK: sum > 40", "MOD EL:\n  x: 1", "ASK:\n  question sum > 40",
           "ASK:\n  question: (sum > 4", "MODEL:\n  type: $\nASK:\n  question: sum > 1"]
    for b in bad:
        try:
            parse_sifr(b)
        except SifrSyntaxError:
            continue
        raise AssertionError("fonte inválida aceita: %r" % b)
    print("(3) rejeição de sintaxe inválida: OK")


def test_transpiler():
    for i in range(N_TRANSP):
        kind, terms, unk, thr, x = make_case()
        src = build_src(kind, terms, unk, thr, x)
        blocks = parse_nexa(src)
        res = NCA(blocks, "t%d" % i).compile()
        code = transpile(blocks)
        ns = {}
        exec(compile(code, "<transpiled>", "exec"), ns)  # código GERADO, auditável
        got = ns["answer"]()
        want = "Z" if res["status"] == "UNKNOWN" else res["answer"]
        assert got == want, "transpilado diverge no caso %d (%s): %r != %r\n%s" % (
            i, kind, got, want, src)
    print("(4) transpilado == motor NCA em %d casos: OK" % N_TRANSP)


if __name__ == "__main__":
    test_equivalence()
    test_fuzz()
    test_syntax_errors()
    test_transpiler()
    print("\nFASE 2 COMPLETA: lexer próprio, sem ast, com transpilador. Exit 0.")
    sys.exit(0)
