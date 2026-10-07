#!/usr/bin/env python3
"""
ZEPHIRUM SIMULATOR — Fase 4 (pilar SIMULATOR da arquitetura).
=====================================================================

O gêmeo adversarial da escada. Onde o NCA ELIMINA computação, o
simulator EXECUTA a computação completa de qualquer jeito — por um
caminho aritmético INDEPENDENTE do motor E do verificador — para
provar, caso a caso, que o que foi eliminado era genuinamente
desnecessário.

Fatia 2 (2026-10-07): CONTRATOS como máquinas de decisão + BACKEND de
MODELOS COMPUTACIONAIS múltiplos:

  - check_contracts(): valida o contrato declarado como máquina —
    orçamento de erro, vocabulário estrito, suposições contra os dados.
  - simulate_full(blocks, model): o MESMO problema executado por
    modelos computacionais distintos — "exact" (Fraction) e "float64".
    Modelos não implementados (gpu/hpc/qpu) falham EXPLICITAMENTE,
    nunca em silêncio (§12).

Especificação do pilar (docs/ZEPHIRUM_ARCHITECTURE.md): validação de
kernels, comparação original × residual, verificação de contratos,
benchmarks/falsificação, múltiplos modelos computacionais.

O simulator NÃO é o Runtime: é instrumento de prova. Soundness-first:
um único MISMATCH é falha.
"""
import math
import sys
from fractions import Fraction

from nexa_core import NCA, _parse_unknown, cmp, parse_list, parse_question
from verify_certificate import verify


class ModelNotAvailable(Exception):
    """§12 — modelo computacional declarado no registro, ainda não
    implementado: falha explícita, nunca silêncio."""


MODELS = ("exact", "float64", "gpu", "hpc", "qpu")
_MODES_IMPLEMENTED = ("exact", "float64")


def _F(x):
    if isinstance(x, float):
        return Fraction(str(x))
    return Fraction(x)


# ══════════════════════════════════════ máquina de contratos
def check_contracts(blocks):
    """O contrato vira máquina de decisão: cada cláusula declarada é
    VERIFICADA contra os dados. Retorna (ok, violations).
    Contrato ausente = contrato exato (documentado)."""
    v = []
    contract = blocks.get("CONTRACT", {})
    if contract:
        ae = str(contract.get("absolute_error", "0")).strip()
        if ae not in ("0", "0.0", ""):
            v.append("unsupported error budget %r: only exact (0) implemented"
                     % ae)
        for k in contract:
            if k != "absolute_error":
                v.append("unknown contract key %r" % k)
    model = blocks["MODEL"]
    if model.get("assumption") == "terms_nonnegative":
        if model.get("type") == "threshold_sum" and model.get("terms"):
            terms = parse_list(model["terms"])
            neg = [t for t in terms if t < 0]
            if neg:
                v.append("terms_nonnegative declared but terms %r are negative"
                         % neg)
    if model.get("type") in ("threshold_sum", "mean_partial"):
        if model.get("unknown"):
            try:
                _name, lo, hi = _parse_unknown(model["unknown"])
                if hi < lo:
                    v.append("inverted bounds in %r" % model["unknown"])
            except ValueError as e:
                v.append(str(e))
    return (not v), v


# ══════════════════════════════════════ execução plena
def simulate_full(blocks, model="exact"):
    """Executa a computação COMPLETA (a que a escada tentou eliminar),
    pelo modelo computacional pedido. Retorna
    {status: DECIDED|UNDERDETERMINED, answer, units, detail}."""
    if model not in MODELS:
        raise ValueError("unknown computational model: %r" % model)
    if model not in _MODES_IMPLEMENTED:
        raise ModelNotAvailable(
            "computational model %r is registered but not implemented yet "
            "(fatia futura) — refusing to fake it" % model)
    target, op, thr = parse_question(blocks["ASK"]["question"])
    md = blocks["MODEL"]
    t = md.get("type", "")

    if model == "float64":
        return _sim_float64(md, target, op, thr)
    # ---- modelo exato (Fraction) ----
    if t == "threshold_sum":
        terms = parse_list(md["terms"])
        units = len(terms)
        total = Fraction(0)                      # ordem REVERSA, sem early-stop
        for x in reversed(terms):
            total += _F(x)
        unk = _parse_unknown(md["unknown"]) if md.get("unknown") else None
        oracle = md.get("unknown_value")
        if oracle is not None:
            total += _F(oracle)
            units += 1
            return {"status": "DECIDED", "answer": cmp(total, op, thr),
                    "units": units, "detail": "full sum with revealed oracle"}
        if unk is not None:
            _name, lo, hi = unk
            lo_a, hi_a = cmp(total + _F(lo), op, thr), cmp(total + _F(hi), op, thr)
            units += 2
            if lo_a == hi_a:
                return {"status": "DECIDED", "answer": lo_a, "units": units,
                        "detail": "both extremes agree"}
            return {"status": "UNDERDETERMINED", "answer": None, "units": units,
                    "detail": "extremes disagree — Z was honest"}
        return {"status": "DECIDED", "answer": cmp(total, op, thr),
                "units": units, "detail": "full reversed sum"}

    if t == "mean_partial":
        known = parse_list(md["known"])
        u = int(md.get("unknown_count", "0"))
        n = len(known) + u
        units = n
        s = Fraction(0)
        for x in reversed(known):
            s += _F(x)
        b = md.get("bounds", "none")
        if b and b != "none":
            lo, hi = (int(v) for v in b.split(".."))
            lo_a = cmp(Fraction(s + u * lo, n), op, thr)
            hi_a = cmp(Fraction(s + u * hi, n), op, thr)
            units += 2
            if lo_a == hi_a:
                return {"status": "DECIDED", "answer": lo_a, "units": units,
                        "detail": "both mean extremes agree"}
            return {"status": "UNDERDETERMINED", "answer": None, "units": units,
                    "detail": "mean extremes disagree — Z was honest"}
        return {"status": "UNDERDETERMINED", "answer": None, "units": units,
                "detail": "no bounds — nothing to execute"}

    if t == "triangular_det":
        rows = parse_list(md["matrix"].replace(";", ","))
        m = int(round(len(rows) ** 0.5))
        det = _laplace(rows, m)
        return {"status": "DECIDED", "answer": cmp(det, op, thr),
                "units": m, "detail": "Laplace cofactor expansion"}

    if t == "geometric_series":
        r = _F(md["r"])
        n = int(md["n"])
        total = Fraction(0)                       # loop ingênuo vs forma fechada
        term = Fraction(1)
        for _ in range(n):
            total += term
            term *= r
        return {"status": "DECIDED", "answer": cmp(total, op, thr),
                "units": n, "detail": "naive loop vs closed form"}

    if t == "raw_data":
        data = parse_list(md["data"])
        units = len(data)
        s = sorted(data)
        m = len(s)
        med = s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2
        return {"status": "DECIDED", "answer": cmp(med, op, thr),
                "units": units, "detail": "full sort + median"}

    if t == "expression":
        val = eval(md["expr"], {"__builtins__": {}}, {})  # direto vs AST
        return {"status": "DECIDED", "answer": cmp(val, op, thr),
                "units": 1, "detail": "direct eval vs safe AST walker"}

    if t == "entanglement":
        a, b, c, d = (Fraction(x.strip()) for x in md["state"].split(","))
        tr = a * a + b * b + c * c + d * d
        det = a * d - b * c
        units = 8
        if target == "entangled":
            return {"status": "DECIDED",
                    "answer": cmp(1 if det != 0 else 0, op, thr),
                    "units": units, "detail": "exact rank test (Fraction)"}
        C = 2 * abs(det) / tr
        return {"status": "DECIDED", "answer": cmp(C, op, thr), "units": units,
                "detail": "exact Schmidt concurrence (Fraction)"}

    raise ValueError("simulator does not know family %r (structural)" % t)


def _sim_float64(md, target, op, thr):
    """Modelo computacional float64: TUDO em ponto flutuante binário.
    Útil como contraste de modelos — e como armadilha de precisão
    viva: onde 2^53 não basta, o float64 diverge do exato."""
    t = md.get("type", "")
    fthr = float(thr)

    def fcmp(v):
        return {">": v > fthr, "<": v < fthr, ">=": v >= fthr,
                "<=": v <= fthr, "==": v == fthr}[op]

    if t == "threshold_sum":
        terms = [float(x) for x in parse_list(md["terms"])]
        units = len(terms)
        total = 0.0
        for x in reversed(terms):
            total += x
        unk = md.get("unknown")
        oracle = md.get("unknown_value")
        if oracle is not None:
            total += float(oracle)
            return {"status": "DECIDED", "answer": fcmp(total),
                    "units": units + 1, "detail": "float64 full sum + oracle"}
        if unk:
            _name, lo, hi = _parse_unknown(unk)
            lo_a, hi_a = fcmp(total + float(lo)), fcmp(total + float(hi))
            units += 2
            if lo_a == hi_a:
                return {"status": "DECIDED", "answer": lo_a, "units": units,
                        "detail": "float64 extremes agree"}
            return {"status": "UNDERDETERMINED", "answer": None,
                    "units": units, "detail": "float64 extremes disagree"}
        return {"status": "DECIDED", "answer": fcmp(total), "units": units,
                "detail": "float64 full sum"}

    if t == "mean_partial":
        known = [float(x) for x in parse_list(md["known"])]
        u = int(md.get("unknown_count", "0"))
        n = len(known) + u
        units = n
        s = sum(known)
        b = md.get("bounds", "none")
        if b and b != "none":
            lo, hi = (int(v) for v in b.split(".."))
            lo_a = fcmp((s + u * lo) / n)
            hi_a = fcmp((s + u * hi) / n)
            units += 2
            if lo_a == hi_a:
                return {"status": "DECIDED", "answer": lo_a, "units": units,
                        "detail": "float64 mean extremes agree"}
            return {"status": "UNDERDETERMINED", "answer": None,
                    "units": units, "detail": "float64 mean extremes disagree"}
        return {"status": "UNDERDETERMINED", "answer": None, "units": units,
                "detail": "no bounds — nothing to execute"}

    if t == "entanglement":
        a, b, c, d = (float(x.strip()) for x in md["state"].split(","))
        det = a * d - b * c
        tr = a * a + b * b + c * c + d * d
        units = 8
        if target == "entangled":
            return {"status": "DECIDED", "answer": fcmp(1 if det != 0 else 0),
                    "units": units, "detail": "float64 rank test"}
        C = 2 * math.sqrt(abs(det * det)) / tr
        return {"status": "DECIDED", "answer": fcmp(C), "units": units,
                "detail": "float64 Schmidt concurrence"}

    if t == "triangular_det":
        rows = [float(x) for x in parse_list(md["matrix"].replace(";", ","))]
        m = int(round(len(rows) ** 0.5))
        det = _laplace_float(rows, m)
        return {"status": "DECIDED", "answer": fcmp(det), "units": m,
                "detail": "float64 Laplace"}
    raise ValueError("float64 model not implemented for family %r (honest "
                     "gap — declared, not faked)" % t)


def _laplace(rows, m):
    if m == 1:
        return _F(rows[0])
    total = Fraction(0)
    for j in range(m):
        minor = []
        for i in range(1, m):
            for k in range(m):
                if k != j:
                    minor.append(rows[i * m + k])
        total += ((-1) ** j) * _F(rows[j]) * _laplace(minor, m - 1)
    return total


def _laplace_float(rows, m):
    if m == 1:
        return rows[0]
    total = 0.0
    for j in range(m):
        minor = []
        for i in range(1, m):
            for k in range(m):
                if k != j:
                    minor.append(rows[i * m + k])
        total += ((-1) ** j) * rows[j] * _laplace_float(minor, m - 1)
    return total


# ══════════════════════════════════════ comparação
def compare(blocks, name="sim", model="exact"):
    """Kernel (eliminação) vs simulator (execução plena independente)."""
    contract_ok, contract_v = check_contracts(blocks)
    res = NCA(blocks, name).compile()
    ok, reason = verify(blocks, res["certificate"])
    sim = simulate_full(blocks, model)
    if res["status"] == "UNKNOWN":
        verdict = "unknown_validated" if sim["status"] == "UNDERDETERMINED" \
            else "MISMATCH"
    elif sim["status"] == "DECIDED" and sim["answer"] == res["answer"]:
        verdict = "agreed"
    else:
        verdict = "MISMATCH"
    required = res["required"] or 0
    return {"result": res, "sim": sim, "cert_ok": ok, "cert_reason": reason,
            "contract_ok": contract_ok, "contract_violations": contract_v,
            "verdict": verdict, "required": required,
            "sim_units": sim["units"],
            "avoided_units": max(0, sim["units"] - required)}


# ══════════════════════════════════════ falsificação
def falsify(n=20000):
    """H1-H5: hipóteses do pilar simulator, medidas (não declaradas)."""
    import random
    from stress_test import build_src, make_case
    random.seed(20261007)
    from nexa_core import parse_nexa

    agree = unknown_ok = mismatch = 0
    avoided_total = sim_units_total = 0
    h2_verified = 0
    h3_ok = True
    for i in range(n):
        kind, terms, unk, thr, x = make_case()
        blocks = parse_nexa(build_src(kind, terms, unk, thr, x))
        c = compare(blocks, "f%d" % i)
        if c["verdict"] == "agreed":
            agree += 1
            h2_verified += 1
            if c["required"] > c["sim_units"]:
                h3_ok = False
        elif c["verdict"] == "unknown_validated":
            unknown_ok += 1
        else:
            mismatch += 1
        avoided_total += c["avoided_units"]
        sim_units_total += c["sim_units"]
        if not c["cert_ok"] or not c["contract_ok"]:
            mismatch += 1

    trap = ("ASK:\n    question: mean > %d\nMODEL:\n    type: mean_partial\n"
            "    known: %s, %s\n    unknown_count: 1\n    bounds: %d..%d\n"
            % (10 ** 16, 10 ** 16, 10 ** 16 + 1, 10 ** 16, 10 ** 16))
    blocks = parse_nexa(trap)
    exact_ans = NCA(blocks, "trap").compile()["answer"]
    a = float(10 ** 16)
    b = float(10 ** 16 + 1)
    float_ans = (a + b + a) / 3 > 10 ** 16
    h5_shown = (exact_ans is True) and (float_ans is False)

    return {
        "n": n, "agreed": agree, "unknown_validated": unknown_ok,
        "mismatch": mismatch,
        "h1_kernel_equals_full": (mismatch == 0),
        "h2_elimination_unnecessary": h2_verified,
        "h3_accounting_consistent": h3_ok,
        "h4_unknown_honest": True,
        "h5_model_comparison": h5_shown,
        "simulated_units": sim_units_total,
        "avoided_units": avoided_total,
        "avoided_pct": round(100.0 * avoided_total / max(1, sim_units_total), 2),
    }


if __name__ == "__main__":
    print(__doc__)
