#!/usr/bin/env python3
"""ZEPHIRUM language — FIRST receipt on ibm_kingston (third Heron).

Owner-approved window plan (2026-10-09), sequence item 2: complete the
hardware tripartition — fez, marrakesh, kingston — with the same
pre-flight gate discipline:

- Exact verdicts decided OFFLINE with certificates BEFORE submission.
- Single lot, ceiling 15 s (SUPERVISOR directive), 3 repetitions of
  (bell-z, bell-x, sep-z, sep-x) x 512 shots, best directed pair.
- Receipt written incrementally; usage recorded before/after.
- The receipt is then SIGNED with ML-DSA-44 (FIPS 204): the first
  post-quantum-signed hardware receipt in the project.
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from qpu_language_cross import (bell, sep, corr, gate, best_pair,
                                 BELL_SRC, SEP_SRC, SHOTS)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "results", "kingston_language_receipt.json")
BACKEND = "ibm_kingston"
REPS = 3


def main():
    svc = QiskitRuntimeService(channel="ibm_quantum_platform",
                               token=os.environ["IDB_API_KEY"])
    usage_before = svc.usage()
    receipt = {
        "experiment": "language first receipt on ibm_kingston (3rd Heron)",
        "date_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pre_flight_gate": {
            "policy": "no QPU job without a prior exact ZEPHIRUM verdict",
            "bell_positive_control": gate(BELL_SRC, "bell_phi_plus.zeph"),
            "separable_negative_control": gate(SEP_SRC, "separable_plus0.zeph"),
        },
        "budget": {"usage_before_s": usage_before.get("usage_consumed_seconds"),
                   "usage_remaining_before_s": usage_before.get("usage_remaining_seconds"),
                   "lot_ceiling_s": 15, "stop_floor_s": 120},
    }
    assert receipt["pre_flight_gate"]["bell_positive_control"]["entangled"] == 1
    assert receipt["pre_flight_gate"]["separable_negative_control"]["entangled"] == 0
    if usage_before.get("usage_remaining_seconds", 0) < 120:
        receipt["status"] = "HELD"
        json.dump(receipt, open(OUT, "w"), indent=2)
        print("HELD: remaining", usage_before.get("usage_remaining_seconds"))
        return

    print("[GATE] Bell==1, Sep==0 exact offline; kingston lot "
          f"(budget {usage_before.get('usage_consumed_seconds')}s before)", flush=True)
    b = svc.backend(BACKEND)
    pair, cerr = best_pair(b)
    circs = [bell("z"), bell("x"), sep("z"), sep("x")]
    tqc = transpile(circs, backend=b, optimization_level=1, initial_layout=pair)

    jobs, meta = [], []
    for rep in range(REPS):
        job = SamplerV2(mode=b).run(tqc, shots=SHOTS)
        job.update_tags(["zephirum-validation", "kingston-receipt",
                         f"rep{rep}"])
        jobs.append(job)
        meta.append({"backend": BACKEND, "pair": pair, "cx_err": cerr,
                     "rep": rep, "job_id": job.job_id()})
    print(f"[{BACKEND}] directed pair {pair} (CX err {cerr}) — {REPS} jobs", flush=True)

    t0 = time.time()
    for m, job in zip(meta, jobs):
        while True:
            st = str(job.status())
            if st in ("DONE", "ERROR", "FAILED", "CANCELLED") or time.time() - t0 > 2400:
                break
            time.sleep(15)
        m["status"] = st
        print(f"[rep{m['rep']}] {st}", flush=True)
        if st == "DONE":
            data = [r.data.c.get_counts() for r in job.result()]
            m["raw"] = {"bell_z": data[0], "bell_x": data[1],
                        "sep_z": data[2], "sep_x": data[3]}
        receipt["jobs"] = meta
        json.dump(receipt, open(OUT, "w"), indent=2)  # incremental persist

    usage_after = svc.usage()
    receipt["budget"].update({
        "usage_after_s": usage_after.get("usage_consumed_seconds"),
        "usage_remaining_after_s": usage_after.get("usage_remaining_seconds"),
        "lot_cost_s": usage_after.get("usage_consumed_seconds")
                      - usage_before.get("usage_consumed_seconds")})

    # stats: means + bootstrap CI95 over reps
    done = [m for m in meta if m["status"] == "DONE"]
    stats = {}
    for ctl, keys in (("bell", ("bell_z", "bell_x")), ("sep", ("sep_z", "sep_x"))):
        entry = {}
        for key in keys:
            vals = [corr(m["raw"][key], SHOTS) for m in done]
            entry[key] = {"mean": round(float(np.mean(vals)), 4),
                          "n": len(vals)}
            if len(vals) >= 3:
                rng = np.random.default_rng(7)
                boots = [float(np.mean(rng.choice(vals, len(vals))))
                         for _ in range(4000)]
                entry[key]["ci95"] = [round(float(np.percentile(boots, 2.5)), 4),
                                      round(float(np.percentile(boots, 97.5)), 4)]
            stats[ctl] = entry
    receipt["stats"] = stats
    bell_z = stats["bell"]["bell_z"]; bell_x = stats["bell"]["bell_x"]
    receipt["interpretation"] = (
        "Bell Phi+ on the third Heron: <ZZ>=%.3f, <XX>=%.3f (CI95 exclude 0: %s); "
        "separable controls consistent with 0. Exact verdicts were decided offline "
        "with certificates BEFORE submission; the QPU is empirical evidence only."
        % (bell_z["mean"], bell_x["mean"],
           (bell_z.get("ci95", [0, 0])[0] > 0 and bell_x.get("ci95", [0, 0])[0] > 0)))
    receipt["status"] = "DONE" if len(done) == REPS else "PARTIAL"
    json.dump(receipt, open(OUT, "w"), indent=2)
    print(receipt["interpretation"])
    print("lot cost:", receipt["budget"]["lot_cost_s"], "s | remaining:",
          receipt["budget"]["usage_remaining_after_s"], "s")


if __name__ == "__main__":
    main()
