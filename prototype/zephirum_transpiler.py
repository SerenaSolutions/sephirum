#!/usr/bin/env python3
"""
ZEPHIRUM TRANSPILER — ZEPHIRUM -> Python (Fase 2).

Gera um programa Python autônomo que responde à pergunta ZEPHIRUM SEM precisar
do motor ZEPHIRUM: a lógica de decisão do kernel é embutida no código gerado
(a mesma aritmética do verificador independente). Quando nem o kernel
consegue decidir, o programa gerado responde Z (zephirum) — honestidade
preservada também no código transpilado.

Nota honesta: o transpilado recomputa a decisão com aritmética própria;
ele não reexecuta a escada completa (isso é trabalho do compilador, não
do programa respondido). Para as famílias atuais a resposta coincide
por construção; o teste `test_zephirum_lang.py` verifica isso caso a caso.
"""
import sys

from nexa_core import parse_question, parse_list, _parse_unknown
from zephirum_lexer import eval_expr

TEMPLATE = '''#!/usr/bin/env python3
# Gerado automaticamente pelo transpilador ZEPHIRUM (Fase 2).
# Pergunta original: {question!r}
QUESTION = {question!r}
OP = {op!r}
THR = {thr!r}

from fractions import Fraction  # decisao exata: o motor decide por Fraction


def cmp(a, op, b):
    return {{">": a > b, "<": a < b,
            ">=": a >= b, "<=": a <= b, "==": a == b}}[op]


def answer():
{body}
    return a


if __name__ == "__main__":
    a = answer()
    print("RESPOSTA:", "Z (UNKNOWN)" if a == "Z" else a)
'''


def _cmp_line(var="a"):
    return "    %s = cmp(val, OP, THR)" % var


def transpile(blocks):
    """blocks IR -> código-fonte Python autônomo (string)."""
    target, op, thr = parse_question(blocks["ASK"]["question"])
    model = blocks["MODEL"]
    mtype = model.get("type", "")
    body = []
    if mtype == "constant_fold":
        val = eval_expr(model["expr"])
        body.append("    val = %r" % val)
        body.append(_cmp_line())
    elif mtype == "threshold_sum":
        terms = parse_list(model["terms"])
        unk = _parse_unknown(model["unknown"]) if model.get("unknown") else None
        oracle = model.get("unknown_value")
        body.append("    known = %r" % terms)
        if oracle is not None:
            body.append("    val = sum(known) + %s" % _num(oracle))
            body.append(_cmp_line())
        elif unk is not None:
            _name, lo, hi = unk
            body.append("    lo, hi = %r, %r" % (lo, hi))
            body.append("    a_lo = cmp(sum(known) + lo, OP, THR)")
            body.append("    a_hi = cmp(sum(known) + hi, OP, THR)")
            body.append("    if a_lo == a_hi:")
            body.append("        a = a_lo")
            body.append("    else:")
            body.append("        a = 'Z'  # nem necessidade nem desnecessidade provadas")
        else:
            body.append("    val = sum(known)")
            body.append(_cmp_line())
    elif mtype == "mean_partial":
        known = parse_list(model["known"])
        ucnt = int(model.get("unknown_count", "0"))
        bounds = model.get("bounds", "none")
        n = len(known) + ucnt
        body.append("    known = %r" % known)
        body.append("    n = %d" % n)
        if bounds and bounds != "none":
            lo, hi = (int(v) for v in bounds.split(".."))  # formato "a..b"
            body.append("    lo, hi = %r, %r" % (lo, hi))
            body.append("    a_lo = cmp(Fraction(sum(known) + %d * lo, n), OP, THR)" % ucnt)
            body.append("    a_hi = cmp(Fraction(sum(known) + %d * hi, n), OP, THR)" % ucnt)
            body.append("    if a_lo == a_hi:")
            body.append("        a = a_lo")
            body.append("    else:")
            body.append("        a = 'Z'")
        else:
            body.append("    a = 'Z'  # sem limites declarados: UNKNOWN honesto")
    else:
        raise NotImplementedError("transpilação ainda não suporta o modelo %r" % mtype)
    return TEMPLATE.format(question=blocks["ASK"]["question"], op=op,
                           thr=thr, body="\n".join(body))


def _num(s):
    s = str(s).strip()
    try:
        return int(s)
    except ValueError:
        return float(s)


if __name__ == "__main__":
    from nexa_core import parse_nexa
    src = sys.stdin.read()
    print(transpile(parse_nexa(src)))
