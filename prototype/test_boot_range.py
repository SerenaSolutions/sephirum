#!/usr/bin/env python3
"""
Battery B2-r — Phase 8, slice range: the RANGE rung, in the language.
=====================================================================

"sum(a..n) > T" decided by a ZEPHIRUM program: G(n) - G(a-1) in
bytecode (opcode SUB), 4 certified units vs n-a+1 of the naive path.
The ladder CHOOSES per case: ranges with fewer than 5 terms are
cheaper to execute — elimination is unit arithmetic, not ideology.

R1 triple agreement (boot == naive == independent judge)
R2 honest choice: ladder always picks the cheaper path
R3 unit accounting: spent units <= certified budget
R4 budget wall: forged 5th LOAD under a certificate of 4 => VMFault
R5 explicit refusals (§12): a > n, wrong family
R6 determinism: stable trace; swapped source changes INPUT_HASH
R7 the decision is born from a parsed ZEPHIRUM source
"""
import random
import sys
from fractions import Fraction

from zephirum_boot import build_src_range, boot_decide_range
from zephirum_vm import ZephirumVM, VMFault


def main():
    random.seed(8022)
    OPS = [">", "<", ">=", "<="]

    def ref_cmp(val, op, thr):
        return {">": val > thr, "<": val < thr,
                ">=": val >= thr, "<=": val <= thr}[op]

    # ---- R1: triple agreement, 2,000 cases
    N = 2000
    eliminated = chosen_boot = chosen_naive = 0
    for i in range(N):
        a = random.randint(1, 60)
        length = random.randint(1, 300)
        n = a + length - 1
        op = random.choice(OPS)
        total = Fraction(sum(range(a, n + 1)))
        thr = random.randint(0, 2 * int(total))
        src = build_src_range(n, op, thr, a)
        plan, boot, naive, choice = boot_decide_range(src)
        ref = ref_cmp(total, op, thr)
        assert boot["answer"] == ref == naive["answer"], \
            "R1: divergence (a=%d n=%d)" % (a, n)
        assert boot["units"] == 4 and naive["units"] == length
        melhor = min(boot["units"], naive["units"])
        escolhido = boot["units"] if choice == "boot" else naive["units"]
        assert escolhido == melhor, "R1: ladder picked the expensive path"
        if choice == "boot":
            chosen_boot += 1
            eliminated += naive["units"] - boot["units"]
        else:
            chosen_naive += 1
    assert chosen_naive > 0, "R1: ladder never chose execution?"
    assert eliminated > 0, "R1: rung never eliminated?"
    print("R1 range_gauss: %d cases, boot==naive==judge, 0 errors; "
          "ladder chose rung %dx, execution %dx; %d units eliminated"
          % (N, chosen_boot, chosen_naive, eliminated))

    # ---- R2: honest choice at the exact boundary (4 terms: tie -> boot;
    #         3 terms: execution is cheaper)
    _, _, _, choice4 = boot_decide_range(build_src_range(9, ">", 20, a=6))
    assert choice4 == "boot"          # 4 terms: tie 4 == 4, rung allowed
    _, _, _, choice3 = boot_decide_range(build_src_range(8, ">", 20, a=6))
    assert choice3 == "naive"          # 3 terms: execution cheaper
    print("R2 boundary: 4 terms -> rung (tie), 3 terms -> execution")

    # ---- R3: unit accounting
    plan, boot, naive, _ = boot_decide_range(build_src_range(50, ">", 900, a=3))
    assert boot["units"] <= boot["budget"] and boot["budget"] == 4
    assert naive["units"] <= naive["budget"]
    print("R3 accounting: spent units <= certified budget, always")

    # ---- R4: budget wall — forged 5th LOAD under a certificate of 4
    plan2 = boot_decide_range.__globals__["boot_compile_range"](
        build_src_range(50, ">", 900, a=3))
    forged = [("LOAD", 0), ("LOAD", 0), ("LOAD", 0)] + plan2["boot"]["program"]
    vm = ZephirumVM(plan2["boot"]["data"], plan2["boot"]["budget"])
    try:
        vm.run(forged)
        raise SystemExit("R4 FAILED: forged program passed")
    except VMFault as e:
        assert "BUDGET" in str(e)
    print("R4 forged: 5th unit under a certificate of 4 => VMFault BUDGET")

    # ---- R5: explicit refusals (§12)
    try:
        boot_decide_range(build_src_range(5, ">", 1, a=9))
        raise SystemExit("R5 FAILED: empty series accepted")
    except VMFault as e:
        assert "empty series" in str(e)
    try:
        boot_decide_range("ASK:\n    question: sum > 3\n"
                          "CONTRACT:\n    absolute_error: 0\n"
                          "MODEL:\n    type: gauss_series\n    n: 4\n")
        raise SystemExit("R5 FAILED: wrong family accepted")
    except VMFault:
        pass
    print("R5 refusals: a > n (empty series) and wrong family => VMFault")

    # ---- R6: determinism + INPUT_HASH protects the source
    src = build_src_range(50, ">", 900, a=3)
    _, b1, _, _ = boot_decide_range(src)
    _, b2, _, _ = boot_decide_range(src)
    assert b1["trace_hash"] == b2["trace_hash"]
    _, b3, _, _ = boot_decide_range(build_src_range(51, ">", 900, a=3))
    assert b1["input_hash"] != b3["input_hash"]
    print("R6 determinism: stable trace; swapped source changes INPUT_HASH")

    # ---- R7: decision born from a parsed ZEPHIRUM source
    _, boot, naive, choice = boot_decide_range(build_src_range(10, ">", 40, a=5))
    assert boot["answer"] is True and naive["answer"] is True  # 45 > 40
    assert choice == "boot"    # 6 terms: rung (4) < execution (6)
    _, _, _, choice1 = boot_decide_range(build_src_range(5, ">", 3, a=5))
    assert choice1 == "naive"  # 1 term: execution is cheaper
    print("R7 source: 5..10 => 45 > 40 True (rung); 1 term => ladder "
          "executes (cheaper path)")

    print("RESULT: PASS — battery B2-r R1-R7 complete")


if __name__ == "__main__":
    main()
