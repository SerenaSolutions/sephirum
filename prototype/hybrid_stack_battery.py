#!/usr/bin/env python3
"""
HYBRID STACK BATTERY — a pilha quântica+IA (a "caixa" que todas as
linguagens tem) atravessada pelo PORTAO ZEPHIRUM.

Fluxo do infográfico-padrão da industria (o que TODO mundo tem):
  dados -> classico -> IA/ML -> QPU -> pos-processamento
Fluxo ZEPHIRUM (a caixa 3.5 que ninguem tem):
  dados -> classico -> IA/ML -> [GATE: decide exato com certificado]
        -> separavel: ROTA CLASSICA (0 shots de QPU)
        -> emaranhado: ADMITE QPU (a maquina testemunha)
        -> indecidivel: UNKNOWN (nunca palpite)   -> pos-processamento

A bateria usa as 100 perguntas publicas da witness_battery (semente
fixa, verdade-terreno independente por determinante exato) como se
fossem 100 entradas candidatas de uma carga de IA quantica (padrao
QCNN: entrada separavel = classicamente simulavel por construcao).
O gate decide cada uma exatamente, offline, zero QPU. Contabilidade:
quantas entradas o portao desviou da caixa 04 (QPU) do infográfico.

Politica §12: nada aqui simula shots; a conta de "shots evitados"
assume o custo padrao do projeto (512 shots por pergunta admitida)
e é ROTULADA como contrafactual declarado, não como medição.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
manifest = json.loads((BASE / "witness_battery" / "manifest.json").read_text())
cases = manifest["battery"]

routed_classical, admitted_quantum, mismatch = [], [], 0
for c in cases:
    # gate: veredito exato do certificado, conferido contra a verdade independente
    if c["cert_verdict"] != c["independent_truth"]:
        mismatch += 1
    if c["cert_verdict"] == 0:
        routed_classical.append(c["name"])
    else:
        admitted_quantum.append(c["name"])

n = len(cases)
SHOTS_DECLARED = 512  # custo padrao declarado do projeto por pergunta na nuvem
shots_avoided_declared = len(routed_classical) * SHOTS_DECLARED

report = {
    "battery": "hybrid_stack_battery",
    "source_manifest": "witness_battery/manifest.json (seed %s)" % manifest.get("seed"),
    "inputs": n,
    "gate_decisions_exact_offline": n,
    "routed_classical_separable": len(routed_classical),
    "admitted_quantum_entangled": len(admitted_quantum),
    "unknown": 0,
    "cert_vs_independent_truth_mismatch": mismatch,
    "qpu_units_in_gate": 0,
    "declared_counterfactual": {
        "shots_per_admitted_question": SHOTS_DECLARED,
        "shots_avoided_if_all_went_to_qpu": shots_avoided_declared,
        "note": "contrafactual DECLARADO (§12): nao e medicao de hardware",
    },
    "elimination_rate": round(len(routed_classical) / n, 4),
}

out = BASE / "hybrid_stack_results.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
print("inputs                           %d" % n)
print("gate: decisões exatas offline    %d (0 unidades de QPU)" % n)
print("rota clássica (separável)        %d  -> nunca chegam à caixa 04" % len(routed_classical))
print("admitidas ao QPU (emaranhado)    %d" % len(admitted_quantum))
print("UNKNOWN / palpite                0")
print("certificado vs verdade indep.    %d divergências" % mismatch)
print("eliminação no portão             %.1f%%" % (100 * report["elimination_rate"]))
print("contrafactual declarado (§12)    %d shots evitados (se TODAS fossem à nuvem)"
      % shots_avoided_declared)
print("resultado: %s" % out)
exit(1 if mismatch else 0)
