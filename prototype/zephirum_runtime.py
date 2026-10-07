#!/usr/bin/env python3
"""
ZEPHIRUM RUNTIME — Fase 5 (pilar RUNTIME da arquitetura).
=====================================================================

O Runtime executa SOMENTE o que sobreviveu à análise de necessidade.
Ele não decide nada: a decisão vem certificada do compilador; o Runtime
conferencia o certificado, executa o residual e fecha a contabilidade.

Contrato do Runtime (soundness-first, nesta ordem):
  1. certificado INVÁLIDO => recusa e ZERO unidades executadas;
  2. decisão certificada sem execução => entrega com ZERO unidades;
  3. residual/full => executa APENAS as unidades certificadas, por
     backend declarado, e confere a resposta contra o certificado;
  4. divergência backend vs certificado => MISMATCH: recusa a entrega
     (alarme) — a resposta certificada nunca é sobrescrita;
  5. UNKNOWN => entregue como Z, zero unidades (nada a executar).

Backends registrados: cpu_exact (Fraction), float64; gpu/hpc/qpu
registrados e honestos: ModelNotAvailable até existirem (§12).

A VM própria é componente INTERNO deste pilar (Fase 6, ainda não).
O Runtime é a linha de frente; o Simulator é instrumento de prova.
"""
from fractions import Fraction

from nexa_core import NCA, _parse_unknown, cmp, parse_list, parse_question
from verify_certificate import verify
from zephirum_simulator import MODELS, ModelNotAvailable, simulate_full
from zephirum_isolate import IsolationFault

BACKENDS = ("cpu_exact", "float64", "vm", "vm_isolated", "gpu", "hpc", "qpu")


class RuntimeRefusal(Exception):
    """O runtime recusou executar/entregar — com o motivo explícito."""


def execute_residual(blocks, res, backend):
    """Executa EXATAMENTE as unidades certificadas (required) para o
    status do certificado. Retorna (answer, units_executed, detail)."""
    model = blocks["MODEL"]
    target, op, thr = parse_question(blocks["ASK"]["question"])
    required = res["required"] or 0
    status = res["status"]

    if status == "UNKNOWN":
        return None, 0, "nothing to execute — Z delivered as certified"

    if required == 0:
        # decidido sem execução: a resposta É o certificado
        return res["answer"], 0, "certificate is the answer — zero units"

    if backend not in BACKENDS:
        raise ValueError("unknown backend: %r" % backend)
    if backend in ("gpu", "hpc", "qpu"):
        raise ModelNotAvailable("backend %r registered, not implemented "
                                "(§12: refusing to fake it)" % backend)

    if backend == "vm_isolated":
        # mesmo bytecode da VM, mas enjaulado em processo filho com muros
        # de CPU/memória/tempo — um crash morre no filho (zephirum_isolate)
        from zephirum_isolate import run_isolated
        try:
            prog, data, budget = _vm_plan(blocks, res)
        except RuntimeRefusal as e:
            raise e
        try:
            rec = run_isolated(prog, data, budget)
        except IsolationFault as e:
            raise RuntimeRefusal(str(e))
        if rec["units"] > budget:
            raise VMFault("contabilidade aberta: %d > %d"
                          % (rec["units"], budget))
        return (rec["answer"], rec["units"],
                "VM ISOLADA (processo filho, muros CPU/mem/tempo), "
                "orçamento %d/%d, trace %s..."
                % (rec["units"], rec["budget"], rec["trace_hash"][:16]))

    if backend == "vm":
        from zephirum_vm import VMNotEncodable, vm_execute
        try:
            r = vm_execute(blocks, res)
        except VMNotEncodable as e:
            raise RuntimeRefusal(str(e))
        return (r["answer"], r["units"],
                "VM bytecode, orçamento %d/%d, trace %s..."
                % (r["units"], r["budget"], r["trace_hash"][:16]))

    if backend == "float64":
        # executa o residual em float64: permitido, mas o recibo registra
        # o modelo — e o cross-check decide se ele é confiável AQUI
        return _exec_float64(blocks, res, target, op, thr, required)

    # ---- cpu_exact: Fraction, exato ----
    if status == "DECIDED_BY_REDUCTION":
        # testemunha: prefixo de `required` termos, recomputados aqui
        terms = parse_list(model["terms"])
        w = Fraction(0)
        for x in terms[:required]:
            w += Fraction(str(x)) if isinstance(x, float) else Fraction(x)
        return cmp(w, op, thr), required, "witness recomputed (%d units)" % required

    if status == "RESIDUAL_COMPUTATION_REQUIRED":
        terms = parse_list(model["terms"])
        unk = _parse_unknown(model["unknown"])
        oracle = Fraction(str(model["unknown_value"]))
        base = Fraction(0)
        for x in terms:
            base += Fraction(str(x)) if isinstance(x, float) else Fraction(x)
        return cmp(base + oracle, op, thr), 1, "oracle residual executed (1 unit)"

    if status == "FULL_EXECUTION_REQUIRED":
        sim = simulate_full(blocks, "exact")   # execução plena sobreviveu
        return sim["answer"], required, "full execution as certified"

    raise RuntimeRefusal("unhandled status %r (structural)" % status)


def _exec_float64(blocks, res, target, op, thr, required):
    model = blocks["MODEL"]
    status = res["status"]
    fthr = float(thr)

    def fcmp(v):
        return {">": v > fthr, "<": v < fthr, ">=": v >= fthr,
                "<=": v <= fthr, "==": v == fthr}[op]

    if status == "DECIDED_BY_REDUCTION":
        terms = [float(x) for x in parse_list(model["terms"])]
        w = 0.0
        for x in terms[:required]:
            w += x
        return fcmp(w), required, "float64 witness recomputed"
    if status == "RESIDUAL_COMPUTATION_REQUIRED":
        terms = [float(x) for x in parse_list(model["terms"])]
        oracle = float(model["unknown_value"])
        return fcmp(sum(terms) + oracle), 1, "float64 oracle residual"
    sim = simulate_full(blocks, "float64")
    return sim["answer"], required, "float64 full execution"


def run(blocks, name="rt", backend="cpu_exact"):
    """Pipeline completo do Runtime. Retorna o recibo da execução.
    Recusa (RuntimeRefusal) ANTES de executar qualquer unidade se o
    certificado não for válido."""
    res = NCA(blocks, name).compile()
    cert = res["certificate"]

    # 1. soundness gate: certificado inválido => ZERO execução
    ok, reason = verify(blocks, cert)
    if not ok:
        raise RuntimeRefusal("invalid certificate — refusing to execute: "
                             "%s" % reason)

    # 2-5. executa o que sobreviveu e fecha a contabilidade
    ans, units, detail = execute_residual(blocks, res, backend)
    certified = res["answer"]
    if ans is None or certified is None:
        cross = "NONE"                     # UNKNOWN: nada a conferir
    elif ans == certified:
        cross = "OK"
    else:
        cross = "MISMATCH"

    original = cert.get("EVIDENCE", {}).get("original_terms", 0) or units
    return {
        "question": blocks["ASK"]["question"],
        "answer": certified if cross != "MISMATCH" else None,
        "status": res["status"],
        "backend": backend,
        "units_executed": units,
        "units_certified": res["required"] or 0,
        "units_original": original,
        "units_eliminated": max(0, original - units),
        "cross_check": cross,
        "detail": detail,
        "cert_hash": cert["CERT_HASH"],
        "refused": cross == "MISMATCH",
    }


if __name__ == "__main__":
    print(__doc__)


def _vm_plan(blocks, res):
    """Plano de execução da VM: (bytecode, dados, orçamento) —
    compartilhado pelos backends vm e vm_isolated."""
    from zephirum_vm import VMNotEncodable, compile_program
    try:
        return compile_program(blocks, res)
    except VMNotEncodable as e:
        raise RuntimeRefusal(str(e))
