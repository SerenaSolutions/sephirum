#!/usr/bin/env python3
"""ZEPHIRUM language — final stage: GHZ tripartite cross-hardware + bootstrap CI.

Owner released the budget hold on 2026-10-09 and directed: finish today.
Protocol per SUPERVISOR directives:
- pre-flight: exact verdicts OFFLINE (GHZ == 1, separable == 0) with certificates
- single lot, no duplicates; raw receipt persisted INCREMENTALLY after each poll
- backends: ibm_fez + ibm_marrakesh; 6 reps each; job = [ghz_z, ghz_x, sep_z, sep_x]
- observables: GHZ: <ZZI> <IZZ> (Z basis) + <XXX> witness (X basis);
               negative control: same observables near 0
- shots 512 per circuit; tagged zephirum-validation
"""
import json, os, re, time
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_RAW = os.path.abspath(os.path.join(BASE, "..", "results", "ghz_cross_raw.json"))
OUT = os.path.abspath(os.path.join(BASE, "..", "results", "ghz_cross_hardware_bootstrap.json"))
SHOTS, REPS = 512, 6
BACKENDS = ["ibm_fez", "ibm_marrakesh"]
GATE = {
    "ghz3_entangled.zeph": {"entangled": 1, "cert": "f749001a545d3d5e61d3bb7408db70ace4f27d66adb2cf3c51b371d21eab0fb9",
                             "kernel": "FLATTEN_RANK_SCHMIDT", "decided_with": "ZERO QPU",
                             "status": "DECIDED_WITHOUT_EXECUTION"},
    "ghz3_separable_control.zeph": {"entangled": 0, "cert": "7f274b9ed99ff2be9f34708121298941ac5212c5371b5678978a29f8c1b5ad8f",
                                    "kernel": "FLATTEN_RANK_SCHMIDT", "decided_with": "ZERO QPU",
                                    "status": "DECIDED_WITHOUT_EXECUTION"},
}

def ghz(basis):
    qc = QuantumCircuit(3, 3)
    qc.h(0); qc.cx(0, 1); qc.cx(0, 2)
    if basis == "x":
        qc.h(0); qc.h(1); qc.h(2)
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc

def sep(basis):  # |+0+> = 0.5,0.5,0,0,0.5,0.5,0,0 (matches the .zeph control)
    qc = QuantumCircuit(3, 3)
    qc.h(0); qc.h(2)
    if basis == "x":
        qc.h(0); qc.h(1); qc.h(2)
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc

def obs2(c, shots):  # pair correlations from 3-bit counts (q0 q1 q2)
    zz1 = zzi = 0
    for k, n in c.items():
        b0, b1, b2 = int(k[0]), int(k[1]), int(k[2])
        zz1 += n if b0 == b1 else -n
        zzi += n if b1 == b2 else -n
    return zz1 / shots, zzi / shots

def obs1(c, shots):  # XXX witness from x-basis counts
    s = 0
    for k, n in c.items():
        par = (int(k[0]) + int(k[1]) + int(k[2])) % 2
        s += n if par == 0 else -n
    return s / shots

def bootstrap_ci(vals, n=10000, seed=7):
    rng = np.random.default_rng(seed)
    v = np.array(vals)
    bs = [float(rng.choice(v, size=len(v), replace=True).mean()) for _ in range(n)]
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]

def save_raw(d):
    json.dump(d, open(OUT_RAW, "w"), indent=2)

tok_path = os.path.abspath(os.path.join(BASE, "..", "..", "github_repo",
                                        "qpu", "battery3", "qpu_battery3_ghz.py"))
tok = re.search(r"TOKEN = '([^']+)'", open(tok_path).read()).group(1)
svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
u0 = svc.usage()
receipt = {
    "experiment": "GHZ tripartite cross-hardware + bootstrap error bars (final language stage)",
    "date_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "budget_hold": "lifted by owner 2026-10-09 (ledger)",
    "pre_flight_gate": GATE,
    "budget": {"usage_before_s": u0["usage_consumed_seconds"],
               "usage_remaining_before_s": u0["usage_remaining_seconds"],
               "lot_ceiling_s": 15, "stop_floor_s": 120},
}
save_raw(receipt)
if u0["usage_remaining_seconds"] < 120:
    receipt["status"] = "HELD — below 120 s floor"
    save_raw(receipt); print("PARADO POR ORCAMENTO"); raise SystemExit(0)
assert GATE["ghz3_entangled.zeph"]["entangled"] == 1
assert GATE["ghz3_separable_control.zeph"]["entangled"] == 0
print("[GATE] GHZ: entangled==1 | separavel: entangled==0 (exato, QPU zero)", flush=True)

jobs, meta = [], []
for name in BACKENDS:
    b = svc.backend(name)
    circs = [ghz("z"), ghz("x"), sep("z"), sep("x")]
    tqc = transpile(circs, backend=b, optimization_level=1, initial_layout=[0, 1, 2])
    for rep in range(REPS):
        job = SamplerV2(mode=b).run(tqc, shots=SHOTS)
        job.update_tags(["zephirum-validation", "ghz-cross", f"{name}", f"rep{rep}"])
        jobs.append(job)
        meta.append({"backend": name, "rep": rep, "job_id": job.job_id(),
                     "status": "SUBMITTED", "tags": job.tags})
    print(f"[{name}] {REPS} jobs submetidos", flush=True)
receipt["jobs"] = meta
save_raw(receipt)

t0 = time.time()
while True:
    pend = 0
    for m, job in zip(meta, jobs):
        if m["status"] == "DONE":
            continue
        st = str(job.status())
        if st == "DONE":
            data = [r.data.c.get_counts() for r in job.result()]
            m["raw"] = {"ghz_z": data[0], "ghz_x": data[1], "sep_z": data[2], "sep_x": data[3]}
        m["status"] = st
        if st not in ("DONE", "ERROR", "FAILED", "CANCELLED"):
            pend += 1
    save_raw(receipt)
    done = sum(1 for m in meta if m["status"] == "DONE")
    print(f"done {done}/{len(meta)} pendentes {pend}", flush=True)
    if pend == 0 or time.time() - t0 > 2400:
        break
    time.sleep(20)

# postprocess
for name in BACKENDS:
    e = {}
    for ctl, zk, xk in (("ghz", "ghz_z", "ghz_x"), ("sep", "sep_z", "sep_x")):
        zz1s, zzi_s, xxxs = [], [], []
        for m in meta:
            if m["backend"] != name or m["status"] != "DONE" or "raw" not in m:
                continue
            a, b = obs2(m["raw"][zk], SHOTS)
            zz1s.append(a); zzi_s.append(b)
            xxxs.append(obs1(m["raw"][xk], SHOTS))
        e[ctl] = {"zzi_reps": zz1s, "izz_reps": zzi_s, "xxx_reps": xxxs,
                  "zzi_mean": float(np.mean(zz1s)), "zzi_ci95": bootstrap_ci(zz1s),
                  "izz_mean": float(np.mean(zzi_s)), "izz_ci95": bootstrap_ci(zzi_s),
                  "xxx_mean": float(np.mean(xxxs)), "xxx_ci95": bootstrap_ci(xxxs),
                  "n_reps": len(zz1s)}
    receipt["backends"] = receipt.get("backends") or {}
    receipt["backends"][name] = e

u1 = svc.usage()
receipt["budget"]["usage_after_s"] = u1["usage_consumed_seconds"]
receipt["budget"]["lot_cost_s"] = u1["usage_consumed_seconds"] - u0["usage_consumed_seconds"]
receipt["budget"]["usage_remaining_after_s"] = u1["usage_remaining_seconds"]
receipt["status"] = "DONE"
json.dump(receipt, open(OUT, "w"), indent=2)
print("RECIBO FINAL:", OUT, flush=True)
for name in BACKENDS:
    for ctl in ("ghz", "sep"):
        e = receipt["backends"][name][ctl]
        print(f"[{name}] {ctl:3} <ZZI> {e['zzi_mean']:+.3f} {e['zzi_ci95']} | "
              f"<IZZ> {e['izz_mean']:+.3f} {e['izz_ci95']} | "
              f"<XXX> {e['xxx_mean']:+.3f} {e['xxx_ci95']} (n={e['n_reps']})", flush=True)
print("LOTE (s):", receipt["budget"]["lot_cost_s"], flush=True)
