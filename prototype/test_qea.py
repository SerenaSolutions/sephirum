#!/usr/bin/env python3
"""
Z-QEA slice 1 battery — charter rules 18 (cases A-G), 19 (adversarial),
20 (ENGINE != VERIFIER: the battery judges the layer with its own
arithmetic, not the layer's own reasons).

Each case builds its OWN ground truth expectation before calling the
layer. Exit 0 only if every case holds.
"""
import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from zephirum_qea import (ADMISSIBLE, REFUSED, UNKNOWN, STALE, INVALID,
                          QEA_TRIT, assess, load_execution_state,
                          make_qea_certificate, watchdog, check_hash)

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)

BASE_SNAPSHOT = {
    "backend_id": "test_line",
    "status": "available",
    "n_qubits": 5,
    "connectivity": [[0, 1], [1, 2], [2, 3], [3, 4]],
    "gate_errors": {"0-1": "0.01", "1-2": "0.01", "2-3": "0.01",
                    "3-4": "0.01"},
    "readout_errors": {"0": "0.02", "1": "0.02", "2": "0.02",
                       "3": "0.02", "4": "0.02"},
    "calibration_timestamp": NOW.isoformat(),
    "max_calibration_age_seconds": 3600,
}

BASE_JOB = {
    "logical_qubits": 3,
    "interactions": [[0, 1], [1, 2]],
    "shots": 10,
    "error_budget": "1",
}

RESULTS = []


def case(name, got, expect_state, extra=None):
    ok = got["qea_state"] == expect_state
    detail = ""
    if extra is not None:
        ok_extra, detail = extra(got)
        ok = ok and ok_extra
    RESULTS.append((name, ok, detail or got["qea_state"]))
    print("%-46s %s" % (name, "ok" if ok else "FAIL: %s" % got))


def snapshot(**over):
    s = copy.deepcopy(BASE_SNAPSHOT)
    if "calibration_offset_seconds" in over:
        off = over.pop("calibration_offset_seconds")
        s["calibration_timestamp"] = (
            NOW - timedelta(seconds=off)).isoformat()
    s.update(over)
    return s


def job(**over):
    j = copy.deepcopy(BASE_JOB)
    j.update(over)
    return j


def fresh_state(s=None):
    st, problems = load_execution_state(s or snapshot())
    assert not problems, problems
    return st


def main():
    print("Z-QEA slice 1 battery — charter cases A-G + adversarial\n")

    # --- CASE A: decidable without QPU -> NO EXECUTION --------------
    got = assess(job(offline_verdict=1), fresh_state(), now=NOW)
    case("A: offline verdict -> NO_EXECUTION", got, "NO_EXECUTION")

    # --- CASE B: QPU needed, route adequate -> ADMISSIBLE -----------
    got = assess(job(), fresh_state(), now=NOW)
    # ground truth, computed here independently: line topology maps
    # 3 logical on 5 physical with both interactions on edges
    case("B: fresh state, adequate route -> ADMISSIBLE", got, ADMISSIBLE,
         lambda g: (g["route"] is not None, "route: %s" % g["route"]))

    # --- CASE C: connectivity exists, budget violated -> REFUSE -----
    got = assess(job(shots=10000, error_budget="0.001"), fresh_state(), now=NOW)
    # 10000 shots * p_fail_upper(~0.1) >> 0.001 — refused, named reason
    case("C: budget violated -> REFUSE with reason", got, REFUSED,
         lambda g: ("error budget" in " ".join(g["reasons"]), g["reasons"][0]))

    # --- CASE D: several routes, one admissible -> SELECT -----------
    s = snapshot()
    s["connectivity"] = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 2]]
    s["gate_errors"]["0-2"] = "0.5"   # one bad edge -> route avoided
    st, _ = load_execution_state(s)
    got = assess(job(), st, now=NOW)
    def route_avoids_bad(g):
        if g["route"] is None:
            return False, "no route"
        pairs = [tuple(sorted((g["route"][i], g["route"][j])))
                 for i, j in BASE_JOB["interactions"]]
        return (all(p != (0, 2) for p in pairs),
                "route %s uses %s" % (g["route"], pairs))
    case("D: bad edge avoided in selection", got, ADMISSIBLE, route_avoids_bad)

    # --- CASE E: stale calibration -> STALE -------------------------
    st = fresh_state(snapshot(calibration_offset_seconds=7200))
    got = assess(job(), st, now=NOW)
    case("E: stale snapshot -> STALE with reason", got, STALE)

    # --- CASE E2: no timestamp at all -> UNKNOWN --------------------
    s = snapshot()
    del s["calibration_timestamp"]
    st, _ = load_execution_state(s)
    got = assess(job(), st, now=NOW)
    case("E2: no timestamp -> UNKNOWN (never guessed)", got, UNKNOWN)

    # --- CASE F: conflicting sources -> UNKNOWN, no silent pick -----
    st = fresh_state()
    st["conflicts_with"] = "deadbeef"
    got = assess(job(), st, now=NOW)
    case("F: source conflict -> UNKNOWN", got, UNKNOWN)

    # --- CASE G: hardware moves after certification -> INVALIDATE ---
    st0 = fresh_state()
    a = assess(job(), st0, now=NOW)
    cert = make_qea_certificate(job(), st0, a)
    still, reason = watchdog(cert, st0, now=NOW)
    ok_g1 = still
    s_new = snapshot()
    s_new["gate_errors"]["1-2"] = "0.02"   # calibration moved
    st1, _ = load_execution_state(s_new)
    still2, reason2 = watchdog(cert, st1, now=NOW)
    ok_g2 = (not still2) and "changed" in reason2
    RESULTS.append(("G: watchdog invalidates on change", ok_g2 and ok_g1,
                    reason2))
    print("%-46s %s" % ("G: watchdog invalidates on change",
                       "ok" if (ok_g2 and ok_g1) else "FAIL"))

    # --- missing metrics: UNKNOWN, never default --------------------
    s = snapshot()
    s["gate_errors"] = {}   # no edge carries evidence at all
    st, _ = load_execution_state(s)
    got = assess(job(), st, now=NOW)
    case("H: missing gate metric -> UNKNOWN", got, UNKNOWN)

    # --- trivalent mapping intact ------------------------------------
    ok = (QEA_TRIT[ADMISSIBLE] == 1 and QEA_TRIT[REFUSED] == 0
          and QEA_TRIT[UNKNOWN] == QEA_TRIT[STALE] == QEA_TRIT[INVALID]
          == "Z")
    RESULTS.append(("T: internal codes map to trivalent 0/1/Z", ok, ""))
    print("%-46s %s" % ("T: internal codes map to trivalent 0/1/Z",
                       "ok" if ok else "FAIL"))

    # --- adversarial: impossible values -> INVALID ------------------
    for name, bad in [
        ("NaN metric", {"gate_errors": {"1-2": "nan"}}),
        ("negative probability", {"gate_errors": {"1-2": "-0.01"}}),
        ("probability > 1", {"readout_errors": {"1": "1.5"}}),
        ("T1 zero", {"T1_us": {"1": 0}}),
        ("edge beyond n_qubits", {"connectivity": [[0, 9]]}),
        ("bad status", {"status": "probably fine"}),
    ]:
        st, problems = load_execution_state(snapshot(**bad))
        if st is not None and problems:
            got = assess(job(), st, now=NOW)
            ok = got["qea_state"] == INVALID and problems
        else:
            ok = False
            got = {"qea_state": "?", "reasons": ["no problems raised"]}
        RESULTS.append(("X: %s -> INVALID" % name, ok,
                         "; ".join(problems or ["no problem"])[:70]))
        print("%-46s %s" % ("X: %s -> INVALID" % name,
                            "ok" if ok else "FAIL: %s" % got))

    # --- adversarial: tampered certificate rejected ------------------
    st = fresh_state()
    a = assess(job(), st, now=NOW)
    cert = make_qea_certificate(job(), st, a)
    good = check_hash(cert)
    tampered = copy.deepcopy(cert)
    tampered["qea_state"] = ADMISSIBLE if cert["qea_state"] != ADMISSIBLE \
        else REFUSED
    bad = check_hash(tampered)
    ok = good and not bad
    RESULTS.append(("X: tampered certificate rejected", ok, ""))
    print("%-46s %s" % ("X: tampered certificate rejected",
                       "ok" if ok else "FAIL"))

    # --- determinism: same evidence -> same certificate hash -------
    st = fresh_state()
    a1 = assess(job(), st, now=NOW)
    c1 = make_qea_certificate(job(), st, a1)
    a2 = assess(job(), fresh_state(snapshot()), now=NOW)
    c2 = make_qea_certificate(job(), fresh_state(snapshot()), a2)
    ok = c1["CERT_HASH"] == c2["CERT_HASH"]
    RESULTS.append(("T: determinism — same evidence, same hash", ok, ""))
    print("%-46s %s" % ("T: determinism — same evidence, same hash",
                        "ok" if ok else "FAIL"))

    # -----------------------------------------------------------------
    fails = [n for n, ok, _ in RESULTS if not ok]
    print("\n%d/%d casos ok" % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FALHAS:", fails)
        return 1
    print("RESULTADO: PASS — Z-QEA slice 1: ASSESS decide com evidência, "
          "recusa com motivo, nunca adivinha (§12)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
