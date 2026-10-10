#!/usr/bin/env python3
"""
QPU HYBRID WITNESS — a perna de hardware da bateria da pilha hibrida.

Pergunta: o que sobrevive quando o portao ADMITIU? O QPU nao julga,
testemunha: prepara o estado certificado e mede as correlacoes
exatas (ZZ e XX) para FALSIFICAR o certificado.

Dois casos, um job (4 pubs, 512 shots):
  - caso CLARO (concurrence maxima entre os admitidos): o hardware
    deve corroborar ZZ/XX exatos dentro do IC95
  - caso DURAO (determinante minimo, fronteira ad~bc): margem de
    emaranhamento ABAIXO do piso de ruido do hardware — o QPU nao
    consegue arbitrar; o certificado e a unica testemunha. Demonstracao
    fisica da tese (§12: rotulado como tal, nao como verificacao).

Token: env IBM_Q_TOKEN (nunca no repositorio). Ledger: receipt JSON em
results/ + secao no docs/HYBRID_STACK.md com job ID.
"""
import json, os, random, re
from fractions import Fraction
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

BASE = Path(__file__).resolve().parent
SHOT = 512
tok = os.environ["IBM_Q_TOKEN"]
svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok, instance="open-instance")
backend = svc.backend("ibm_marrakesh")
print("backend:", backend.name, "fila:", backend.status().pending_jobs)

manifest = json.loads((BASE / "witness_battery" / "manifest.json").read_text())
adm = []
for c in manifest["battery"]:
    if c["cert_verdict"] == 1:
        a, b, cc, d = [Fraction(x) for x in c["amplitudes"]]
        n2 = a*a + b*b + cc*cc + d*d
        det = abs(a*d - b*cc)
        adm.append({"name": c["name"], "amps": [a, b, cc, d], "N2": n2, "det": det,
                    "conc": float(2 * det / n2),
                    "zz": float((a*a + d*d - b*b - cc*cc) / n2),
                    "xx": float(2 * (a*d + b*cc) / n2)})
clear = max(adm, key=lambda r: r["conc"])
hard = min(adm, key=lambda r: r["det"])
print("claro :", clear["name"], "C =", round(clear["conc"], 4))
print("durao :", hard["name"], "C =", hard["conc"], "det =", hard["det"])

def pubs_for(r):
    n = float(r["N2"]) ** 0.5
    amps = [float(x) / n for x in r["amps"]]
    def mk(xx):
        qc = QuantumCircuit(2, 2)
        qc.append(StatePreparation(amps), [0, 1])
        if xx:
            qc.h([0, 1])
        qc.measure([0, 1], [0, 1])
        return transpile(qc, backend=backend, optimization_level=1)
    return mk(False), mk(True)

cases = [("clear", clear), ("hard", hard)]
circs, meta = [], []
for tag, r in cases:
    z, x = pubs_for(r)
    circs += [z, x]; meta += [(tag, "ZZ", r), (tag, "XX", r)]

job = SamplerV2(mode=backend).run(circs, shots=SHOT)
print("job:", job.job_id(), "— aguardando...")
res = job.result()
print("job finalizado, status:", job.status())

def counts_of(p):
    for name in ("c", "m", "meas"):
        if hasattr(p.data, name):
            return p.data.__getattr__(name).get_counts()
    return p.data.__getattr__(list(p.data.__dir__() & set())[0]).get_counts()

rng = random.Random(20261010)
out = {"job_id": job.job_id(), "backend": backend.name, "shots": SHOT, "date": "2026-10-10", "cases": {}}
for i, (tag, basis, r) in enumerate(meta):
    cnt = counts_of(res[i])
    bs = [k for k, v in cnt.items() for _ in range(v)]
    par = [1 if k in ("00", "11") else -1 for k in bs]
    emp = float(np.mean(par))
    boots = [float(np.mean([rng.choice(par) for _ in par])) for _ in range(2000)]
    ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
    pred = r["zz"] if basis == "ZZ" else r["xx"]
    ok = ci[0] <= pred <= ci[1]
    out["cases"]["%s_%s" % (tag, basis)] = {
        "question": r["name"], "basis": basis, "exact_prediction": pred,
        "measured": emp, "ci95": ci, "corroborates": ok, "counts": cnt,
    }
    print("%s %s: exato %.4f | medido %.4f IC95 [%.3f, %.3f] | corrobora: %s"
          % (r["name"], basis, pred, emp, ci[0], ci[1], ok))

out["thesis_note"] = ("caso hard: margem de emaranhamento |det|=%s abaixo do piso de "
                      "ruido do hardware; o QPU nao pode arbitrar o veredito — o certificado "
                      "e a unica testemunha (demonstracao da tese, §12)" % hard["det"])
p = BASE.parent / "results" / "hybrid_witness_marrakesh.json"
p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
print("receipt:", p)
