#!/usr/bin/env python3
"""
Falsification battery for the NEXA/ZERA prototype (spec S19 + S23).
Cases: A full elimination; B partial (residual); C cannot be eliminated;
D cannot know (UNKNOWN); I/J bounds decide; F identity; G analytic det;
H closed form; E soundness attack (tampered certificate must be REJECTED).
Exit 0 = all cases behaved as expected, 0 false certificates.
"""
import copy
import sys

from nexa_core import parse_nexa, NCA
from verify_certificate import verify

A = """
ASK:
    question: sum > 100
CONTRACT:
    absolute_error: 0
MODEL:
    type: threshold_sum
    terms: 60, 30, 20, 5, 4, 3, 2, 1
    assumption: terms_nonnegative
BUDGET:
    minimize: computation
REQUIRE:
    certified_answer
"""

B = """
ASK:
    question: sum > 200
CONTRACT:
    absolute_error: 0
MODEL:
    type: threshold_sum
    terms: 60, 30, 20
    unknown: x in 0..1000
    unknown_value: 37
"""

C = """
ASK:
    question: median > 50
MODEL:
    type: raw_data
    data: 12, 87, 45, 63, 51, 39, 96, 4, 58
"""

D = """
ASK:
    question: mean > 50
MODEL:
    type: mean_partial
    known: 60, 55, 65, 50, 60
    unknown_count: 5
    bounds: none
"""

I = """
ASK:
    question: mean > 50
MODEL:
    type: mean_partial
    known: 60, 55, 65, 50, 60
    unknown_count: 5
    bounds: 48..52
"""

J = """
ASK:
    question: sum > 100
MODEL:
    type: threshold_sum
    terms: 60, 30
    unknown: y in 0..5
"""

F = """
ASK:
    question: value == 7
MODEL:
    type: expression
    expr: 2*(3+4) - 10 + 3
"""

G = """
ASK:
    question: det > 0
MODEL:
    type: triangular_det
    matrix: 2,0,0; 3,4,0; 5,6,7
"""

H = """
ASK:
    question: value == 2047
MODEL:
    type: geometric_series
    r: 2
    n: 10
"""

# id -> (status, answer, required, eliminated, ratio, checker_must_accept)
EXPECTED = {
    "A": ("DECIDED_BY_REDUCTION", True, 3, 5, 62.5, True),
    "B": ("RESIDUAL_COMPUTATION_REQUIRED", False, 1, 3, 75.0, True),
    "C": ("FULL_EXECUTION_REQUIRED", True, 9, 0, 0.0, True),
    "D": ("UNKNOWN", None, None, 0, 0.0, True),
    "I": ("DECIDED_WITHOUT_EXECUTION", True, 0, 5, 100.0, True),
    "J": ("DECIDED_WITHOUT_EXECUTION", False, 0, 3, 100.0, True),
    "F": ("DECIDED_WITHOUT_EXECUTION", True, 0, 1, 100.0, True),
    "G": ("DECIDED_WITHOUT_EXECUTION", True, 0, 6, 100.0, True),
    "H": ("DECIDED_WITHOUT_EXECUTION", True, 0, 11, 100.0, True),
}

SRCS = {"A": A, "B": B, "C": C, "D": D, "I": I, "J": J,
        "F": F, "G": G, "H": H}


def run(src, name):
    blocks = parse_nexa(src)
    res = NCA(blocks, name).compile()
    ok, reason = verify(blocks, res["certificate"])
    return blocks, res, ok, reason


def main():
    results = {}
    failures = []

    for name in ("A", "B", "C", "D", "I", "J", "F", "G", "H"):
        blocks, res, ok, reason = run(SRCS[name], name)
        exp = EXPECTED[name]
        good = (res["status"] == exp[0] and res["answer"] == exp[1]
                and ok is exp[5]
                and res["required"] == exp[2] and res["eliminated"] == exp[3])
        if name in ("A", "B", "I", "J", "F", "G", "H"):
            good = good and abs(res["ratio"] - exp[4]) < 1e-9
        results[name] = (res, ok, reason)
        if not good:
            failures.append((name, res, reason))

    # Case E: soundness attack - tampered certificates MUST be rejected
    blocks_a, res_a, _, _ = run(A, "A")
    t1 = copy.deepcopy(res_a["certificate"])
    t1["EVIDENCE"]["witness_sum"] = 95              # forged sum
    e1, _ = verify(blocks_a, t1)
    t2 = copy.deepcopy(res_a["certificate"])
    t2["EVIDENCE"]["witness_terms"] = [60, 31, 20]  # forged witness
    t2["EVIDENCE"]["witness_sum"] = 111
    e2, _ = verify(blocks_a, t2)
    t3 = copy.deepcopy(res_a["certificate"])
    t3["STATUS"] = "DECIDED_WITHOUT_EXECUTION"     # forged status
    e3, _ = verify(blocks_a, t3)
    case_e_ok = (e1 is False) and (e2 is False) and (e3 is False)

    hdr = "%-3s %-30s %-7s %-10s %-8s %-8s %-7s" % (
        "ID", "STATUS", "ANSWER", "REQ/ELIM", "RATIO%", "NET", "CHECKER")
    print(hdr)
    print("-" * len(hdr))
    for name in ("A", "B", "C", "D", "I", "J", "F", "G", "H"):
        res, ok, reason = results[name]
        req = res["required"] if res["required"] is not None else "-"
        print("%-3s %-30s %-7s %-10s %-8s %-8s %-7s" % (
            name, res["status"], res["answer"],
            "%s/%s" % (req, res["eliminated"]),
            ("%.1f" % res["ratio"]) if res["ratio"] else "-",
            "%+.2f" % res["net_benefit"],
            "ACCEPT" if ok else "REJECT"))
    print("E   %-30s %-7s %-10s %-8s %-8s %-7s" % (
        "SOUNDNESS ATTACK (tampered certs)", "3x", "0/3 forged", "-", "-",
        "REJECTED (OK)" if case_e_ok else "ACCEPTED (CRITICAL FAILURE!)"))

    print()
    if failures or not case_e_ok:
        for name, res, reason in failures:
            print("FALSIFIED - case %s: status=%s answer=%s checker=%s"
                  % (name, res["status"], res["answer"], reason))
        print("RESULT: PROBLEMS FOUND - hypothesis falsified at this level.")
        return 1

    print("RESULT: all 9 decision cases behaved as expected.")
    print("        0 false certificates accepted; 3 forged certificates rejected.")
    print("\nELIMINATION LEDGER (case A - didactic example of spec S13):")
    for e in res_a["ledger"]:
        print("  [%s] %s - %s" % (e["rung"], e["outcome"], e["detail"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
