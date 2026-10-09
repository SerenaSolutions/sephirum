#!/usr/bin/env python3
"""Collector for the language cross-hardware battery.
Retrieves every job tagged 'language-cross' (both lots — the first lot's
ids were lost in a session crash; the incident is recorded in the receipt),
computes correlations + bootstrap CIs, writes the receipt."""
import json, os, re, time
import numpy as np
from qiskit_ibm_runtime import QiskitRuntimeService

SHOTS = 512
BASE = os.path.dirname(os.path.abspath(__file__))

def corr(counts, shots):
    p = sum(n for k, n in counts.items() if k[0] == k[1])
    return (2 * p / shots) - 1

def bootstrap_ci(vals, n=10000, seed=42):
    rng = np.random.default_rng(seed)
    v = np.array(vals)
    bs = [float(rng.choice(v, size=len(v), replace=True).mean()) for _ in range(n)]
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]

tok_path = os.path.abspath(os.path.join(BASE, "..", "..", "github_repo",
                                        "qpu", "battery3", "qpu_battery3_ghz.py"))
tok = re.search(r"TOKEN = '([^']+)'", open(tok_path).read()).group(1)
svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
usage_now = svc.usage()
print("usage now:", usage_now["usage_consumed_seconds"], "s | remaining:",
      usage_now["usage_remaining_seconds"], flush=True)

# espera todos os jobs language-cross terminarem (teto 20 min)
t0 = time.time()
jobs = {}
while time.time() - t0 < 1200:
    lst = svc.jobs(limit=100)
    jobs = {j.job_id(): j for j in lst if "language-cross" in (j.tags or [])}
    pend = [j for j in jobs.values() if str(j.status()) not in
            ("DONE", "ERROR", "FAILED", "CANCELLED")]
    print(f"{len(jobs)} jobs language-cross | pendentes: {len(pend)}", flush=True)
    if not pend:
        break
    time.sleep(30)

print("status:", {j.job_id(): str(j.status()) for j in jobs.values()}, flush=True)

# agrupa por backend + rep (primeiro DONE vence; duplicados contados p/ incidente)
seen, dup = {}, 0
for j in jobs.values():
    tags = j.tags or []
    rep = next((t[3:] for t in tags if t.startswith("rep")), None)
    be = next((t for t in tags if t in ("ibm_fez-0-1", "ibm_marrakesh-0-1")), None)
    be = be.rsplit("-", 2)[0] if be else "?"
    key = (be, rep)
    if key in seen and seen[key] is not None:
        dup += 1
        if str(j.status()) == "DONE":
            continue
    if str(j.status()) == "DONE":
        seen[key] = j
    elif key not in seen:
        seen[key] = None

receipt = {
    "experiment": "language cross-hardware evidence + bootstrap error bars",
    "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "pre_flight_gate": {
        "policy": "no QPU job without a prior exact ZEPHIRUM verdict (SUPERVISOR directive 2)",
        "bell_positive_control": {
            "program": "bell_phi_plus.zeph", "status": "DECIDED_WITHOUT_EXECUTION",
            "entangled": 1, "kernel": "SCHMIDT_DET_CRITERION", "rung": "ANALYTIC",
            "cert_hash": "7d55227631fd4be7613e71358d545bf446f187eefb800507fbe1a44ef4beef0a",
            "decided_with": "ZERO QPU"},
        "separable_negative_control": {
            "program": "separable_plus0.zeph", "status": "DECIDED_WITHOUT_EXECUTION",
            "entangled": 0, "kernel": "SCHMIDT_DET_CRITERION", "rung": "ANALYTIC",
            "cert_hash": "(recorded at submission; same exact criterion, det == 0)",
            "decided_with": "ZERO QPU"},
    },
    "incident": ("session crash mid-battery: the first lot of 12 jobs was submitted and its "
                 "job ids lost before polling; a second identical lot was submitted. All jobs "
                 "carry the 'language-cross' tag; duplicates by (backend, rep) are counted "
                 f"here: {dup}. QPU cost below is the honest total measured by the usage ledger."),
    "protocol": {"backends": ["ibm_fez", "ibm_marrakesh"], "reps": 6,
                 "circuits_per_job": 4, "shots": 512, "pair": [0, 1],
                 "controls": ["Bell Phi+ (positive, verdict 1)",
                              "separable |+0> (negative, verdict 0)"]},
    "budget": {"usage_before_battery_s": 64,
               "usage_at_collection_s": usage_now["usage_consumed_seconds"],
               "lot_cost_total_s": usage_now["usage_consumed_seconds"] - 64,
               "usage_remaining_s": usage_now["usage_remaining_seconds"]},
}
jobs_meta, per_backend = [], {}
for (be, rep), j in sorted(seen.items()):
    if j is None:
        jobs_meta.append({"backend": be, "rep": rep, "status": "NOT_RETRIEVED"})
        continue
    data = [r.data.c.get_counts() for r in j.result()]
    meta = {"backend": be, "rep": rep, "job_id": j.job_id(), "tags": j.tags}
    meta["raw"] = {"bell_z": data[0], "bell_x": data[1], "sep_z": data[2], "sep_x": data[3]}
    jobs_meta.append(meta)
    per_backend.setdefault(be, {"bell_z": [], "bell_x": [], "sep_z": [], "sep_x": []})
    per_backend[be]["bell_z"].append(corr(data[0], SHOTS))
    per_backend[be]["bell_x"].append(corr(data[1], SHOTS))
    per_backend[be]["sep_z"].append(corr(data[2], SHOTS))
    per_backend[be]["sep_x"].append(corr(data[3], SHOTS))

receipt["jobs"] = jobs_meta
receipt["backends"] = {}
for be, d in per_backend.items():
    receipt["backends"][be] = {}
    for ctl, keys in (("bell", ("bell_z", "bell_x")), ("sep", ("sep_z", "sep_x"))):
        zk, xk = keys
        receipt["backends"][be][ctl] = {
            "zz_reps": d[zk], "xx_reps": d[xk],
            "zz_mean": float(np.mean(d[zk])), "zz_ci95": bootstrap_ci(d[zk]),
            "xx_mean": float(np.mean(d[xk])), "xx_ci95": bootstrap_ci(d[xk]),
            "n_reps": len(d[zk])}

out = os.path.abspath(os.path.join(BASE, "..", "results",
                                   "language_cross_hardware_bootstrap.json"))
json.dump(receipt, open(out, "w"), indent=2)
print("RECIBO:", out, flush=True)
for be, s in receipt["backends"].items():
    for ctl in ("bell", "sep"):
        e = s[ctl]
        print(f"[{be}] {ctl:4} <ZZ> {e['zz_mean']:+.3f} CI95 {e['zz_ci95']} | "
              f"<XX> {e['xx_mean']:+.3f} CI95 {e['xx_ci95']} (n={e['n_reps']})", flush=True)
print("LOTE TOTAL (s):", receipt["budget"]["lot_cost_total_s"], flush=True)
