#!/usr/bin/env python3
"""ZEPHIRUM — CHSH/QKD hardware witness on ibm_kingston.

Study ZYQL-TR-2026-10-10 (cybersecurity: entanglement-based key
distribution). House discipline, unchanged:

- The classical bound (S <= 2) and the Tsirelson ceiling (2*sqrt(2))
  are decided OFFLINE with certificates BEFORE any submission.
- The QPU only supplies RAW COUNTS. The LANGUAGE decides 'S > 2' over
  the declared counts (check: chsh_bound, mode: witness) — the hardware
  never judges.
- Single lot, ceiling 15 s, 2048 shots per setting, usage recorded
  before/after, receipt signed with ML-DSA-44 (FIPS 204).

Settings (X-Z plane angles, |Phi+> target): a0 = 0 (Z), a1 = pi/2 (X),
b0 = pi/4, b1 = -pi/4. Ideal correlators: E = cos(a-b) -> S = 2*sqrt(2).
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from nexa_core import parse_nexa, NCA
from pq_receipt import load_keys, sign_receipt

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "results", "chsh_qkd_kingston.json")
BACKEND = "ibm_kingston"
SHOTS = 2048
CEILING_S = 15
FLOOR_S = 120


def decide(src, name="chsh_qkd.zeph"):
    return NCA(parse_nexa(src), name=name).compile()


def chsh_circuit(theta_a, theta_b):
    """Bell pair + measurement bases rotated by theta in the X-Z plane."""
    qc = QuantumCircuit(2, 2, name="chsh_%+1.0f_%+1.0f"
                        % (theta_a, theta_b))
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(theta_a, 0)
    qc.ry(theta_b, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def counts_to_pair(counts):
    same = sum(v for k, v in counts.items() if k[0] == k[1])
    diff = sum(v for k, v in counts.items() if k[0] != k[1])
    return same, diff


def main():
    token = (os.environ.get("IBM_API_KEY")
             or os.environ.get("IDB_API_KEY"))
    if not token:
        raise SystemExit("IBM/IDB API key not set: hardware leg blocked "
                         "(owner must restore the token; offline battery "
                         "test_chsh_qkd.py remains fully certified).")

    # ── pre-flight gate: offline certificates BEFORE the QPU ──────────
    r = decide("ASK:\n    question: classical_max <= 2\nMODEL:\n"
               "    type: exact\n    check: chsh_bound\n    mode: classical\n")
    assert r["answer"] is True and \
        r["certificate"]["STATUS"] == "DECIDED_WITHOUT_EXECUTION"
    r = decide("ASK:\n    question: tsirelson > 2\nMODEL:\n"
               "    type: exact\n    check: chsh_bound\n    mode: tsirelson\n")
    assert r["answer"] is True
    print("PRE-FLIGHT: classical bound and Tsirelson ceiling certified "
          "offline — QPU authorized as WITNESS only")

    svc = QiskitRuntimeService(channel="ibm_quantum_platform",
                                token=token)
    usage_before = svc.usage()
    remaining = usage_before.get("usage_remaining_seconds", 0)
    if remaining < FLOOR_S:
        raise SystemExit("budget floor: %s s remaining < %s s — held"
                         % (remaining, FLOOR_S))

    receipt = {
        "experiment": "CHSH/QKD witness on ibm_kingston (study ZYQL-TR-2026-10-10)",
        "date_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pre_flight_gate": {
            "policy": "offline verdicts before any QPU unit",
            "classical_bound_S": 2,
            "tsirelson_bound_S": 2.8284271247461903,
        },
        "budget": {"usage_before_s": usage_before.get("usage_consumed_seconds"),
                   "usage_remaining_before_s": remaining,
                   "lot_ceiling_s": CEILING_S},
        "shots_per_setting": SHOTS,
        "settings": {"a0": 0.0, "a1": math.pi / 2,
                     "b0": math.pi / 4, "b1": -math.pi / 4},
    }

    backend = svc.backend(BACKEND)
    circuits = [chsh_circuit(a, b) for a, b in
                ((0.0, math.pi / 4), (0.0, -math.pi / 4),
                 (math.pi / 2, math.pi / 4), (math.pi / 2, -math.pi / 4))]
    tqc = transpile(circuits, backend=backend,
                    optimization_level=1)
    sampler = SamplerV2(mode=backend)
    job = sampler.run(tqc, shots=SHOTS)
    print("submitted:", job.job_id())
    res = job.result()

    pairs = {}
    for name, pub in zip(("a0b0", "a0b1", "a1b0", "a1b1"), res):
        counts = dict(pub[0].data.items())[0].__dict__ if False else pub[0].data
        # SamplerV2: get counts dict from the classical register
        c = getattr(pub[0].data, "c", None)
        counts = c.get_counts() if c is not None else pub[0].data.get_counts()
        pairs[name] = counts_to_pair(counts)
    receipt["counts"] = pairs

    # ── the LANGUAGE decides over the declared counts ─────────────────
    wit = ("ASK:\n    question: S > 2\nMODEL:\n    type: exact\n"
           "    check: chsh_bound\n    mode: witness\n"
           "    a0b0: %d,%d\n    a0b1: %d,%d\n    a1b0: %d,%d\n    a1b1: %d,%d\n"
           % (pairs["a0b0"] + pairs["a0b1"] + pairs["a1b0"] + pairs["a1b1"]))
    r = decide(wit, name="chsh_witness_kingston.zeph")
    ev = r["certificate"]["EVIDENCE"]
    receipt["language_verdict"] = {
        "answer": r["answer"], "status": r["certificate"]["STATUS"],
        "S": ev["S_float"], "S_exact": ev["S"],
        "correlators": {k: ev["E_" + k] for k in ("a0b0", "a0b1",
                                                  "a1b0", "a1b1")},
        "certificate_hash": r["certificate"]["CERT_HASH"],
    }

    usage_after = svc.usage()
    receipt["budget"].update({
        "usage_after_s": usage_after.get("usage_consumed_seconds"),
        "usage_remaining_after_s": usage_after.get("usage_remaining_seconds"),
        "lot_used_s": round(usage_after.get("usage_consumed_seconds", 0)
                            - usage_before.get("usage_consumed_seconds", 0), 3)})
    receipt["date_utc_end"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime())
    _, priv = load_keys()
    signed = sign_receipt(receipt, priv)
    with open(OUT, "w") as fh:
        json.dump(signed, fh, indent=2, sort_keys=True)
    print("VERDICT (language, over QPU counts): S = %.4f -> %s"
          % (ev["S_float"], "ENTANGLEMENT CERTIFIED (QKD-ready witness)"
             if r["answer"] else "NO VIOLATION (honest refusal)"))
    print("receipt:", OUT)


if __name__ == "__main__":
    main()
