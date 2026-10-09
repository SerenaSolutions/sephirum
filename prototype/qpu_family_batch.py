#!/usr/bin/env python3
"""ZEPHIRUM language — family batch: every remaining verdict family to hardware.

Owner-directed 2026-10-09: "lance tudo" — one lot, both backends, families:
  ghz4_entangled (1) / ghz4_separable_control (0)  [RECURSIVE_FLATTEN_RANK]
  qcnn_cluster_state (1) [CZ|++>, Cong-Choi-Lukin 2019 block]
  qcnn_gate_entangled (1) [Bell] / qcnn_gate_separable (0) [|+0>]
Pre-flight: ALL verdicts decided offline with certificates (below) BEFORE submission.
Raw receipt persisted incrementally. Reps R=4, shots 512, both backends.
"""
import json, os, re, time
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_RAW = os.path.abspath(os.path.join(BASE, "..", "results", "family_batch_raw.json"))
OUT = os.path.abspath(os.path.join(BASE, "..", "results", "family_batch_hardware.json"))
SHOTS, REPS = 512, 4
BACKENDS = ["ibm_fez", "ibm_marrakesh"]
GATE = {
    "ghz4_entangled.zeph": {"entangled": 1, "cert": "2fff3dd1fdfd2da2", "kernel": "RECURSIVE_FLATTEN_RANK"},
    "ghz4_separable_control.zeph": {"entangled": 0, "cert": "b4385f98855df70d", "kernel": "RECURSIVE_FLATTEN_RANK"},
    "qcnn_cluster_state.zeph": {"entangled": 1, "cert": "5c0ccc610c78da5c", "kernel": "SCHMIDT_DET_CRITERION"},
    "qcnn_gate_entangled.zeph": {"entangled": 1, "cert": "91aa55399c1c5541", "kernel": "SCHMIDT_DET_CRITERION"},
    "qcnn_gate_separable.zeph": {"entangled": 0, "cert": "75c310e12107cad0", "kernel": "SCHMIDT_DET_CRITERION"},
}
KEYS = ["ghz4_z", "plus4_z", "cluster_xz", "cluster_zx", "bell_z", "sep_z"]

def ghz4():  # |0000>+|1111> (chain CNOTs)
    qc = QuantumCircuit(4, 4); qc.h(0); qc.cx(0,1); qc.cx(1,2); qc.cx(2,3)
    qc.measure(range(4), range(4)); return qc

def plus4():  # |++++> separable control
    qc = QuantumCircuit(4, 4)
    for q in range(4): qc.h(q)
    qc.measure(range(4), range(4)); return qc

def cluster(basis):  # CZ|++>: X0Z1 or Z0X1 stabilizer
    qc = QuantumCircuit(2, 2); qc.h(0); qc.h(1); qc.cz(0,1)
    if basis == "xz":  # measure q0 in X, q1 in Z
        qc.h(0)
    else:              # measure q0 in Z, q1 in X
        qc.h(1)
    qc.measure([0,1],[0,1]); return qc

def prep2(state):  # bell |+0>
    qc = QuantumCircuit(2, 2)
    if state == "bell": qc.h(0); qc.cx(0,1)
    else: qc.h(0)
    qc.measure([0,1],[0,1]); return qc

def save(d): json.dump(d, open(OUT_RAW, "w"), indent=2)

def corr_pair(c, i, j, shots):
    s = 0
    for k, n in c.items():
        s += n if k[i] == k[j] else -n
    return s / shots

def corr_all(c, shots):
    s = 0
    for k, n in c.items():
        par = sum(int(b) for b in k) % 2
        s += n if par == 0 else -n
    return s / shots

def bootstrap_ci(vals, n=10000, seed=11):
    rng = np.random.default_rng(seed)
    v = np.array(vals)
    bs = [float(rng.choice(v, size=len(v), replace=True).mean()) for _ in range(n)]
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]

tok_path = os.path.abspath(os.path.join(BASE, "..", "..", "github_repo",
                                        "qpu", "battery3", "qpu_battery3_ghz.py"))
tok = re.search(r"TOKEN = '([^']+)'", open(tok_path).read()).group(1)
svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
u0 = svc.usage()
receipt = {"experiment": "family batch: all remaining verdict families to hardware",
           "date_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "owner_directive": "lance tudo (2026-10-09)",
           "pre_flight_gate": GATE,
           "budget": {"usage_before_s": u0["usage_consumed_seconds"],
                      "usage_remaining_before_s": u0["usage_remaining_seconds"]}}
save(receipt)
if u0["usage_remaining_seconds"] < 120:
    receipt["status"] = "HELD"; save(receipt); print("PARADO"); raise SystemExit(0)
for k, v in GATE.items():
    assert v["entangled"] in (0, 1)
print("[GATE] 5 vereditos exatos registrados (QPU zero)", flush=True)

jobs, meta = [], []
for name in BACKENDS:
    b = svc.backend(name)
    c4 = transpile([ghz4(), plus4()], backend=b, optimization_level=1, initial_layout=[0,1,2,3])
    c2 = transpile([cluster("xz"), cluster("zx"), prep2("bell"), prep2("sep")],
                   backend=b, optimization_level=1, initial_layout=[0,1])
    tqc = list(c4) + list(c2)
    for rep in range(REPS):
        job = SamplerV2(mode=b).run(tqc, shots=SHOTS)
        job.update_tags(["zephirum-validation", "family-batch", name, f"rep{rep}"])
        jobs.append(job)
        meta.append({"backend": name, "rep": rep, "job_id": job.job_id(),
                     "status": "SUBMITTED", "tags": job.tags})
    print(f"[{name}] {REPS} jobs (6 circuitos cada) submetidos", flush=True)
receipt["jobs"] = meta
save(receipt)

t0 = time.time()
while True:
    pend = 0
    for m, job in zip(meta, jobs):
        if m["status"] == "DONE": continue
        st = str(job.status())
        if st == "DONE":
            data = [r.data.c.get_counts() for r in job.result()]
            m["raw"] = dict(zip(KEYS, data))
        m["status"] = st
        if st not in ("DONE","ERROR","FAILED","CANCELLED"): pend += 1
    save(receipt)
    print(f"done {sum(1 for m in meta if m['status']=='DONE')}/{len(meta)} pend {pend}", flush=True)
    if pend == 0 or time.time()-t0 > 2400: break
    time.sleep(20)

OBS = {"ghz4": ("ghz4_z", [("z01",0,1), ("z03",0,3)]),
       "plus4": ("plus4_z", [("z01",0,1), ("z03",0,3)]),
       "cluster": (None, None), "bell": ("bell_z", None), "sep": ("sep_z", None)}
receipt["backends"] = {}
for name in BACKENDS:
    e = {"ghz4": {}, "plus4": {}, "cluster": {}, "bell": {}, "sep": {}}
    z01, z03, p01, p03, cxz, czx, bz, sz = [], [], [], [], [], [], [], []
    for m in meta:
        if m["backend"] != name or "raw" not in m: continue
        r = m["raw"]
        z01.append(corr_pair(r["ghz4_z"],0,1,SHOTS)); z03.append(corr_pair(r["ghz4_z"],0,3,SHOTS))
        p01.append(corr_pair(r["plus4_z"],0,1,SHOTS)); p03.append(corr_pair(r["plus4_z"],0,3,SHOTS))
        cxz.append(corr_all(r["cluster_xz"],SHOTS)); czx.append(corr_all(r["cluster_zx"],SHOTS))
        bz.append(corr_all(r["bell_z"],SHOTS)); sz.append(corr_all(r["sep_z"],SHOTS))
    def pack(tag, label, arr):
        arr = [a for a in arr if a is not None]
        e[tag] = {label+"_reps": arr, label+"_mean": float(np.mean(arr)),
                  label+"_ci95": bootstrap_ci(arr), "n": len(arr)} if arr else {}
    pack("ghz4","z01",z01); e["ghz4"]["z03_reps"]=z03
    e["ghz4"]["z03_mean"]=float(np.mean(z03)); e["ghz4"]["z03_ci95"]=bootstrap_ci(z03)
    pack("plus4","z01",p01)
    e["plus4"]["z03_reps"]=p03; e["plus4"]["z03_mean"]=float(np.mean(p03))
    e["plus4"]["z03_ci95"]=bootstrap_ci(p03)
    e["cluster"]={"xz": {"reps": cxz, "mean": float(np.mean(cxz)), "ci95": bootstrap_ci(cxz)},
                  "zx": {"reps": czx, "mean": float(np.mean(czx)), "ci95": bootstrap_ci(czx)}}
    e["bell"]={"zz": {"reps": bz, "mean": float(np.mean(bz)), "ci95": bootstrap_ci(bz)}}
    e["sep"]={"zz": {"reps": sz, "mean": float(np.mean(sz)), "ci95": bootstrap_ci(sz)}}
    receipt["backends"][name] = e

u1 = svc.usage()
receipt["budget"]["usage_after_s"] = u1["usage_consumed_seconds"]
receipt["budget"]["lot_cost_s"] = u1["usage_consumed_seconds"] - u0["usage_consumed_seconds"]
receipt["budget"]["usage_remaining_after_s"] = u1["usage_remaining_seconds"]
receipt["status"] = "DONE"
json.dump(receipt, open(OUT, "w"), indent=2)
print("RECIBO:", OUT, flush=True)
for name in BACKENDS:
    e = receipt["backends"][name]
    print(f"[{name}] ghz4 <Z0Z1> {e['ghz4']['z01_mean']:+.3f} CI {e['ghz4']['z01_ci95']} | "
          f"<Z0Z3> {e['ghz4']['z03_mean']:+.3f} CI {e['ghz4']['z03_ci95']}", flush=True)
    print(f"[{name}] plus4 <Z0Z1> {e['plus4']['z01_mean']:+.3f} CI {e['plus4']['z01_ci95']}", flush=True)
    print(f"[{name}] cluster <X0Z1> {e['cluster']['xz']['mean']:+.3f} CI {e['cluster']['xz']['ci95']} | "
          f"<Z0X1> {e['cluster']['zx']['mean']:+.3f} CI {e['cluster']['zx']['ci95']}", flush=True)
    print(f"[{name}] bell <ZZ> {e['bell']['zz']['mean']:+.3f} CI {e['bell']['zz']['ci95']} | "
          f"sep <ZZ> {e['sep']['zz']['mean']:+.3f} CI {e['sep']['zz']['ci95']}", flush=True)
print("LOTE (s):", receipt["budget"]["lot_cost_s"], flush=True)
