#!/usr/bin/env python3
"""
BATTERY — Q-SIM GATEWAY: decisions at the gate, ZERO QPU units billed.
======================================================================

What must hold for the gateway to ship:

1. ROUTED: 40 states (product, Bell, partial, decimal, random) — every
   question decided in the gateway with status DECIDED_WITHOUT_EXECUTION,
   ZERO QPU units billed, certificate verified by the INDEPENDENT checker.
2. FLOAT COUNTER-PROOF: an independent float path (eigenvalues of rho_A)
   agrees with the exact verdict wherever float can decide (non-boundary).
3. NOT ROUTED (§12): a gauss question is explicitly refused at the gate —
   never a silent UNKNOWN — with the SDK cost it would have required.
4. STRUCTURAL REFUSALS: malformed state (3 amplitudes) and the zero state
   are explicit errors, not answers.
"""
import math
import random
from fractions import Fraction

from nexa_core import parse_nexa, NCA
from qsim_gateway import gateway, _float_C


def _src(state, question):
    return ("ASK:\n    question: %s\nCONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: entanglement\n    state: %s\n"
            % (question, state))


def _float_C_exact(a, b, c, d):
    tr = a * a + b * b + c * c + d * d
    det = a * d - b * c
    return 2 * abs(det) / tr


def main():
    random.seed(2026)
    states = [
        ("0.70710678118654752,0,0,0.70710678118654752", Fraction(1, 2)),  # Bell
        ("1,0,0,0", Fraction(0)),                                         # product
        ("0.70710678118654752,0.70710678118654752,0,0", Fraction(0)),     # product
        ("0.70710678118654752,0,0.70710678118654752,0", Fraction(0)),     # product
    ]
    while len(states) < 36:
        toks = [Fraction(random.randint(-9, 9), 10) for _ in range(4)]
        if sum(t * t for t in toks) == 0:
            toks[0] = Fraction(3, 10)
        states.append((",".join(str(t) for t in toks),
                       _float_C_exact(*toks)))
    states.append(("0.6,0.4,0.4,0.6", _float_C_exact(Fraction(3, 5),
     Fraction(2, 5), Fraction(2, 5), Fraction(3, 5))))
    states.append(("0.70710678118654752,0,0.5,0.5", _float_C_exact(
        Fraction(1, 2), 0, Fraction(1, 2), Fraction(1, 2))))
    states.append(("0.5,0.5,0.5,0.5", Fraction(0)))
    states.append(("0.8,0.4,0.2,0.4", _float_C_exact(Fraction(4, 5),
     Fraction(2, 5), Fraction(1, 5), Fraction(2, 5))))

    routed = 0
    for i, (st, C_exact) in enumerate(states):
        question = "entangled == 1" if i % 3 == 0 else (
            "concurrence > %s" % (C_exact / 2 if C_exact > 0 else "1/3"))
        receipt, ok = gateway(_src(st, question))
        assert receipt["routed"], ("not routed: %s" % receipt)
        assert receipt["status"] == "DECIDED_WITHOUT_EXECUTION"
        assert receipt["qpu_units_billed"] == 0
        assert ok and receipt["independent_check"][0]
        # float counter-proof where float can decide
        if question.startswith("concurrence"):
            toks = [Fraction(x.strip()) for x in st.split(",")]
            fl = _float_C(*(float(t) for t in toks))
            thr = Fraction(question.split(" > ")[1])
            if abs(_float_C_exact(*toks) - thr) > Fraction(1, 1000):
                assert (fl > float(thr)) == (receipt["verdict"] == 1), (
                    st, question, fl)
        routed += 1
    print("ROUTED: %d/%d decisions at the gate — ZERO QPU units billed, "
          "certificates verified by the independent checker" % (routed,
                                                               len(states)))

    # §12 — explicit NOT ROUTED
    gauss_src = ("ASK:\n    question: sum > 10\nCONTRACT:\n    "
                 "absolute_error: 0\nMODEL:\n    type: threshold_sum\n"
                 "    data: 1,2,3\n")
    receipt, _ = gateway(gauss_src)
    assert receipt["routed"] is False and "outside supported" in receipt["reason"]
    print("NOT ROUTED (par.12): gauss question refused at the gate with an "
          "explicit reason — never a silent UNKNOWN")

    # structural refusals
    for bad in ("0.5,0.5,0.5", "0,0,0,0"):
        try:
            gateway(_src(bad, "entangled == 1"))
        except (ValueError, Exception) as e:
            if "structural" not in str(e) and "4 amplitudes" not in str(e):
                raise
        else:
            raise AssertionError("bad state accepted: %r" % bad)
    print("STRUCTURAL: malformed and zero states are explicit errors (2/2)")

    # SDK cross-check: honesto nos DOIS mundos (§12)
    import importlib.util
    if importlib.util.find_spec("qiskit") is not None:
        receipt, _ = gateway(_src(states[0][0], "entangled == 1"),
                             sdk="qiskit")
        assert "float concurrence" in receipt["sdk_cross_check"]
        assert "SKIP" not in receipt["sdk_cross_check"]
        assert receipt["qpu_units_billed"] == 0
        print("SDK CROSS-CHECK: qiskit PRESENTE — concurrence float medido "
              "como ruído em torno do exato; o veredito do certificado "
              "não muda, ZERO unidades QPU (§12)")
    else:
        receipt, _ = gateway(_src(states[0][0], "entangled == 1"),
                             sdk="qiskit")
        assert "SKIP (§12)" in receipt["sdk_cross_check"]
        print("SDK CROSS-CHECK: SKIP declared honestly (no qiskit here) — "
              "the gateway never pretends to have checked")

    print("RESULT: PASS — Q-SIM GATEWAY: the entanglement family is decided "
          "at the gate; the SDK is only ever paid for what cannot be proven")


if __name__ == "__main__":
    main()
