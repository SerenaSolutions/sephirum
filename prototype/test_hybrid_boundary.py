#!/usr/bin/env python3
"""HYBRID BOUNDARY PATTERN — routing tests (owner directive
2026-10-10). The classical side decides what crosses the
classical-quantum boundary; the QPU is witness, never decider."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nexa_core import parse_nexa, NCA

def run(src):
    return NCA(parse_nexa(src), name="hybrid.zeph").compile()

def plan(witness, budget, shots="2048", basis="ZZ,XX,YY"):
    return ("ASK:\n    question: plan_valid == 1\nMODEL:\n    type: hybrid\n"
            "    check: boundary_plan\n    qpu_witness: %s\n"
            "    budget_seconds: %s\n    shots: %s\n    basis: %s\n"
            % (witness, budget, shots, basis))

# 1. Valid witness plan: 4 stages, 1 crossing, budget within cap
r = run(plan("true", 15))
ev = r["certificate"]["EVIDENCE"]
assert r["answer"] is True and ev["stages"] == [
    "CLASSICAL_PREP", "EXACT_DECISION", "QPU_WITNESS", "RECEIPT"]
assert ev["boundary_crossings"] == 1
print("PLANO VALIDO  4 estagios, 1 travessia, orcamento 15s  [APROVADO]")

# 2. Budget above the supervisor cap -> refused
r = run(plan("true", 30))
ev = r["certificate"]["EVIDENCE"]
assert r["answer"] is False and "15 s/lot cap" in ev["reason"]
print("TETO  30s RECUSADO — diretiva do supervisor (15s/lote)  [RECUSADO]")

# 3. Witness with zero budget -> refused
r = run(plan("true", 0))
ev = r["certificate"]["EVIDENCE"]
assert r["answer"] is False and "zero budget" in ev["reason"]
print("ORCAMENTO ZERO  testemunha sem orcamento  [RECUSADO]")

# 4. Pure classical workload: exact-only, boundary NEVER crossed
r = run(plan("false", 0))
ev = r["certificate"]["EVIDENCE"]
assert r["answer"] is True and ev["stages"] == [
    "CLASSICAL_PREP", "EXACT_DECISION"]
assert ev["boundary_crossings"] == 0
print("CARGA CLASSICA  2 estagios, fronteira NUNCA atravessada  [EXATO]")

# 5. Section 12: unknown hybrid check refused
try:
    run("ASK:\n    question: plan_valid == 1\nMODEL:\n    type: hybrid\n"
        "    check: qpu_accelerator\n")
    sys.exit("FALHA: check inexistente aceito")
except ValueError as e:
    assert "Section 12" in str(e)
    print("SECAO 12  'qpu_accelerator' RECUSADO — a QPU nao e acelerador, "
          "e testemunha  [OK]")

print("\nRESULTADO: PASS — roteamento de fronteira 5/5; padrao hibrido "
      "formalizado")
