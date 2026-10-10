#!/usr/bin/env python3
# BÓREAS driver: escada GHZ degraus 8 e 12 — testemunho empírico no QPU.
# Portão de pré-voo: vereditos exatos JÁ decididos offline (VERDICT 1, ZERO QPU).
# A QPU nunca decide; apenas confirma plausibilidade física (§12).
import os, json, time
from datetime import datetime, timezone

from qiskit import qasm3, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

TOKEN = os.environ["QISKIT_IBM_TOKEN"]
N_SHOTS = 512
OUT = "results/ghz8_12_ladder_receipt.json"

svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN, instance="auto")
backend = svc.backend("ibm_marrakesh")
print("[DRIVER] backend:", backend.name, "pending:", backend.status().pending_jobs)

usage_before = svc.usage()["usage_consumed_seconds"]
print("[DRIVER] uso antes:", usage_before, "s")

circuits = {}
for n in (8, 12):
    qc = qasm3.loads(open(f"fusion/openqasm/ghz{n}_entangled.qasm").read())
    qc.measure_all()
    circuits[n] = transpile(qc, backend=backend, optimization_level=1)
    print("[DRIVER] GHZ-%d transpilado: profundidade %d, %d CX 2q" %
          (n, circuits[n].depth(), circuits[n].num_nonlocal_gates()))

sampler = SamplerV2(mode=backend)
job = sampler.run([circuits[8], circuits[12]], shots=N_SHOTS)
print("[DRIVER] job:", job.job_id(), "estado:", job.status())

t0 = time.time()
while job.status() not in ("DONE", "ERROR", "CANCELLED"):
    time.sleep(15)
    st = job.status()
    print("[DRIVER] %s %s (%.0fs)" % (job.job_id(), st, time.time() - t0), flush=True)
    if time.time() - t0 > 3600:
        print("[DRIVER] timeout de espera"); break

print("[DRIVER] final:", job.status())
if job.status() != "DONE":
    raise SystemExit("job nao concluiu: " + job.status())

def analyze(bits, n):
    """bits: dict counts (string de n bits, qiskit little-endian)."""
    p0 = bits.get("0" * n, 0); p1 = bits.get("1" * n, 0)
    pop = (p0 + p1) / N_SHOTS
    # correlador ZZ do par extremo
    zz = 0
    for k, c in bits.items():
        if len(k) == n:
            b0 = int(k[n - 1]); b1 = int(k[0])  # q0 e q_{n-1}
            zz += c * (1 if b0 == b1 else -1)
    return {"pop_0N_1N": round(pop, 4), "z_endpair": round(zz / N_SHOTS, 4),
            "counts_top": dict(sorted(bits.items(), key=lambda kv: -kv[1])[:4])}

res8 = analyze(job.result()[0].data.meas.get_counts(), 8)
res12 = analyze(job.result()[1].data.meas.get_counts(), 12)
print("[DRIVER] GHZ-8:", res8)
print("[DRIVER] GHZ-12:", res12)

usage_after = svc.usage()["usage_consumed_seconds"]
receipt = {
    "experiment": "GHZ ladder rungs 8 and 12 — fusion chain .zeph -> exact verdict -> OpenQASM 3 -> qasm3.loads -> QPU; closes the scaling curve (2,3,4,6,8,12,20)",
    "date_utc_start": datetime.now(timezone.utc).isoformat(),
    "backend": backend.name,
    "job_id": job.job_id(),
    "shots": N_SHOTS,
    "pre_flight_gate": {
        "policy": "no QPU job without a prior exact ZEPHIRUM verdict",
        "ghz8": {"program": "ghz8_entangled.zeph", "verdict": 1,
                 "units_billed": 0, "hash": "0c4173ae96c09d5122aac825043a8bb9a7a5681a80f1a4c8961a246b72f33e2e"},
        "ghz12": {"program": "ghz12_entangled.zeph", "verdict": 1,
                  "units_billed": 0, "hash": "5c178775522ad94a02926f8ff4f58592427bc9bc7974bf9923fc450e5196db5f"},
    },
    "ghz8_entangled": res8,
    "ghz12_entangled": res12,
    "budget": {"usage_before_s": usage_before, "usage_after_s": usage_after,
               "lot_cost_s": usage_after - usage_before,
               "lot_cap_s": 15},
    "honesty": "Exact verdicts decided OFFLINE with integer arithmetic; QPU counts are empirical evidence of physical plausibility, never the certificate (§12).",
}
json.dump(receipt, open(OUT, "w"), indent=1)
print("[DRIVER] recibo:", OUT, "custo do lote:", usage_after - usage_before, "s")
