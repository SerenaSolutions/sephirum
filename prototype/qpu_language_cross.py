#!/usr/bin/env python3
"""ZEPHIRUM language — cross-hardware evidence battery (Stage: language).

Purpose (owner-directed 2026-10-09): replicate the language's entanglement
verdicts on a SECOND QPU and attach statistical error bars (bootstrap).

Protocol (per SUPERVISOR directives):
- Pre-flight gate: exact ZEPHIRUM verdicts decided OFFLINE (zero QPU in the
  decision path), certificate hashes recorded in the receipt BEFORE submission.
- Budget: service.usage() recorded before and after; lot ceiling 15 s.
- Two backends (ibm_fez, ibm_marrakesh), 6 repetitions each, 4 circuits
  per job (bell-z, bell-x, sep-z, sep-x), 512 shots, tagged zephirum-validation.
"""
import json, os, sys, time, re
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE))
from nexa_core import parse_nexa, NCA

SHOTS = 512
REPS = 6
BACKENDS = ["ibm_fez", "ibm_marrakesh"]

# ---- pre-flight gate: exact verdicts, offline, with certificates ----
BELL_SRC = """ASK:
    question: entangled == 1
CONTRACT:
    absolute_error: 0
MODEL:
    type: entanglement
    state: 0.70710678118654752,0,0,0.70710678118654752
"""
SEP_SRC = """ASK:
    question: entangled == 1
CONTRACT:
    absolute_error: 0
MODEL:
    type: entanglement
    state: 0.70710678118654752,0,0.70710678118654752,0
"""

def gate(src, name):
    nca = NCA(parse_nexa(src), name=name)
    r = nca.compile()
    cert = r.get("certificate") or {}
    verdict = 1 if r["answer"] is True else 0
    assert r["status"] == "DECIDED_WITHOUT_EXECUTION", r["status"]
    return {"program": name, "status": r["status"], "entangled": verdict,
            "kernel": r["kernel"], "rung": r["rung"],
            "cert_hash": cert.get("CERT_HASH"), "decided_with": "ZERO QPU"}

def bell(basis):
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.cx(0, 1)
    if basis == "x":
        qc.h(0); qc.h(1)
    qc.measure([0, 1], [0, 1])
    return qc

def sep(basis):
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    if basis == "x":
        qc.h(0); qc.h(1)
    qc.measure([0, 1], [0, 1])
    return qc

def best_pair(b):
    try:
        cx = b.target["cx"]
        edges = [(k, v.error) for k, v in cx.items()]
        (pair, err), *_ = sorted(edges, key=lambda e: (e[1] is None, e[1]))
        return list(pair), err
    except Exception:
        return [0, 1], None

def corr(counts, shots):
    p = sum(n for k, n in counts.items() if k[0] == k[1])
    return (2 * p / shots) - 1

def bootstrap_ci(vals, n=10000, seed=42):
    rng = np.random.default_rng(seed)
    v = np.array(vals)
    bs = [float(rng.choice(v, size=len(v), replace=True).mean()) for _ in range(n)]
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

def main():
    # token: lido do repo zephyrum (mesma credencial Open Plan compartilhada)
    tok_path = os.path.join(os.path.dirname(BASE), "..", "github_repo",
                            "qpu", "battery3", "qpu_battery3_ghz.py")
    tok_path = os.path.abspath(tok_path)
    tok = re.search(r"TOKEN = '([^']+)'", open(tok_path).read()).group(1)
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
    usage_before = svc.usage()

    receipt = {
        "experiment": "language cross-hardware evidence + bootstrap error bars",
        "date_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pre_flight_gate": {
            "policy": "no QPU job without a prior exact ZEPHIRUM verdict (SUPERVISOR directive 2)",
            "bell_positive_control": gate(BELL_SRC, "bell_phi_plus.zeph"),
            "separable_negative_control": gate(SEP_SRC, "separable_plus0.zeph"),
        },
        "budget": {"usage_before_s": usage_before.get("usage_consumed_seconds"),
                   "usage_remaining_before_s": usage_before.get("usage_remaining_seconds"),
                   "lot_ceiling_s": 15, "stop_floor_s": 120},
    }
    if usage_before.get("usage_remaining_seconds", 0) < 120:
        receipt["status"] = "HELD — usage remaining below the 120 s floor"
        json.dump(receipt, open(os.path.join(BASE, "..", "results",
                "language_cross_hardware_bootstrap.json"), "w"), indent=2)
        print("PARADO POR ORCAMENTO (diretiva 1): remaining",
              usage_before.get("usage_remaining_seconds"))
        return

    assert receipt["pre_flight_gate"]["bell_positive_control"]["entangled"] == 1
    assert receipt["pre_flight_gate"]["separable_negative_control"]["entangled"] == 0
    print("[GATE] Bell: entangled==1 | Separable: entangled==0 (exact, zero QPU)", flush=True)

    jobs, meta = [], []
    for name in BACKENDS:
        b = svc.backend(name)
        pair, cerr = best_pair(b)
        circs = [bell("z"), bell("x"), sep("z"), sep("x")]
        tqc = transpile(circs, backend=b, optimization_level=1, initial_layout=pair)
        for rep in range(REPS):
            job = SamplerV2(mode=b).run(tqc, shots=SHOTS)
            job.update_tags(["zephirum-validation", "language-cross",
                             f"{name}-{pair[0]}-{pair[1]}", f"rep{rep}"])
            jobs.append(job)
            meta.append({"backend": name, "pair": pair, "cx_err": cerr, "rep": rep,
                         "job_id": job.job_id(), "tags": job.tags})
        print(f"[{name}] par dirigido {pair} (CX err {cerr}) — {REPS} jobs submetidos", flush=True)

    t0 = time.time()
    for m, job in zip(meta, jobs):
        while True:
            st = str(job.status())
            if st in ("DONE", "ERROR", "FAILED", "CANCELLED") or time.time() - t0 > 2400:
                break
            time.sleep(15)
        m["status"] = st
        print(f"[{m['backend']} rep{m['rep']}] {st}", flush=True)
        if st == "DONE":
            data = [r.data.c.get_counts() for r in job.result()]
            m["raw"] = {"bell_z": data[0], "bell_x": data[1],
                        "sep_z": data[2], "sep_x": data[3]}

    # ===== postprocess: correlations + bootstrap CIs =====
    stats = {}
    for name in BACKENDS:
        entry = {}
        for ctl, zz_key, xx_key in (("bell", "bell_z", "bell_x"), ("sep", "sep_z", "sep_x")):
            zz = [corr(m["raw"][zz_key], SHOTS) for m in meta
                  if m["backend"] == name and m["status"] == "DONE"]
            xx = [corr(m["raw"][xx_key], SHOTS) for m in meta
                  if m["backend"] == name and m["status"] == "DONE"]
            lo_z, hi_z = bootstrap_ci(zz)
            lo_x, hi_x = bootstrap_ci(xx)
            entry[ctl] = {"zz_reps": zz, "xx_reps": xx,
                          "zz_mean": float(np.mean(zz)), "zz_ci95": [lo_z, hi_z],
                          "xx_mean": float(np.mean(xx)), "xx_ci95": [lo_x, hi_x]}
        stats[name] = entry
    receipt["backends"] = stats
    receipt["jobs"] = meta
    usage_after = svc.usage()
    receipt["budget"]["usage_after_s"] = usage_after.get("usage_consumed_seconds")
    receipt["budget"]["lot_cost_s"] = (usage_after.get("usage_consumed_seconds")
                                       - usage_before.get("usage_consumed_seconds"))
    receipt["budget"]["usage_remaining_after_s"] = usage_after.get("usage_remaining_seconds")
    receipt["status"] = "DONE"
    out = os.path.abspath(os.path.join(BASE, "..", "results",
                                      "language_cross_hardware_bootstrap.json"))
    json.dump(receipt, open(out, "w"), indent=2)
    print("RECIBO:", out, flush=True)
    for name in BACKENDS:
        s = receipt["backends"][name]
        print(f"[{name}] Bell  <ZZ> {s['bell']['zz_mean']:+.3f} CI95 {s['bell']['zz_ci95']} | "
              f"<XX> {s['bell']['xx_mean']:+.3f} CI95 {s['bell']['xx_ci95']}", flush=True)
        print(f"[{name}] Sep   <ZZ> {s['sep']['zz_mean']:+.3f} CI95 {s['sep']['zz_ci95']} | "
              f"<XX> {s['sep']['xx_mean']:+.3f} CI95 {s['sep']['xx_ci95']}", flush=True)
    print("LOTE (s):", receipt["budget"]["lot_cost_s"], "| restante (s):",
          receipt["budget"]["usage_remaining_after_s"], flush=True)

if __name__ == "__main__":
    main()
