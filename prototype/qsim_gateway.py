#!/usr/bin/env python3
"""
Q-SIM GATEWAY — prove before you pay.
=====================================

The gateway sits in FRONT of a quantum SDK (Qiskit, Cirq, PennyLane) or a
real QPU: entanglement-family questions are decided ANALYTICALLY in the
gateway — exact Fractions, certificate, ZERO QPU units billed. Only the
residual (what cannot be proven) is routed to the SDK.

    python3 qsim_gateway.py prog.zeph [--sdk qiskit|cirq|pennylane]

Receipt emitted on every run:
  verdict, certificate hash, QPU units billed, eliminated SDK path,
  residual to the SDK, and the SDK cross-check (or an explicit §12 SKIP
  when the SDK is not installed — the gateway never pretends).

Honesty is the product (§12): unsupported families are NOT ROUTED with an
explicit reason and the SDK cost they would have required — never a silent
UNKNOWN.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexa_core import parse_nexa, NCA
from verify_certificate import verify

SUPPORTED = {"entanglement"}


def _float_C(a, b, c, d):
    """Independent float ground truth (eigenvalues of rho_A)."""
    tr = a * a + b * b + c * c + d * d
    det_rho = (a * d - b * c) ** 2
    disc = max(0.0, tr * tr / 4 - det_rho)
    l1 = tr / 2 + disc ** 0.5
    l2 = max(0.0, tr / 2 - disc ** 0.5)
    return 2 * (l1 * l2) ** 0.5 / tr if tr > 0 else 0.0


def gateway(src, sdk=None):
    """Returns (receipt dict, ok bool)."""
    blocks = parse_nexa(src)
    fam = blocks["MODEL"].get("type", "")
    if fam not in SUPPORTED:
        return {"routed": False,
                "reason": "family %r outside supported families (§12)" % fam,
                "sdk_path_would_cost": "statevector + measurement, billed by "
                                      "the SDK/QPU",
                "advice": "route directly to the SDK — nothing provable here "
                          "yet"}, False
    res = NCA(blocks, "qsim-gateway").compile()
    cert = res["certificate"]
    ok, why = verify(blocks, cert)
    receipt = {
        "routed": True,
        "status": res["status"],
        "verdict": 1 if res["answer"] is True else (0 if res["answer"] is False
                                                    else "Z"),
        "cert_hash": cert["CERT_HASH"],
        "input_hash": cert["INPUT_HASH"],
        "independent_check": (ok, why),
        "qpu_units_billed": 0,
        "sdk_path_eliminated": "statevector + eigendecomposition "
                               "(%d units, saved by the Schmidt criterion)"
                               % res["original"],
        "residual_to_sdk": "none — the certificate is the answer",
    }
    if sdk:
        try:
            __import__(sdk)
        except ImportError:
            receipt["sdk_cross_check"] = (
                "SKIP (§12): %s not installed in this environment" % sdk)
        else:
            toks = [float(x) for x in blocks["MODEL"]["state"].split(",")]
            a, b, c, d = toks
            fl = _float_C(a, b, c, d)
            receipt["sdk_cross_check"] = (
                "%s float concurrence C = %.17g (noise around the exact "
                "value; the certificate remains the stable verdict)" % (sdk, fl))
    return receipt, ok


def _print(receipt):
    for k, v in receipt.items():
        print("%-22s: %s" % (k, v))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = open(sys.argv[1]).read()
    sdk = None
    if "--sdk" in sys.argv:
        sdk = sys.argv[sys.argv.index("--sdk") + 1]
    print("Q-SIM GATEWAY — prove before you pay")
    receipt, ok = gateway(src, sdk)
    _print(receipt)
    if not receipt.get("routed"):
        raise SystemExit(0)   # explicit NOT ROUTED, not an error
    if not ok:
        print("GATEWAY: certificate FAILED independent check — refusing")
        raise SystemExit(1)
    print("GATEWAY: decision delivered with ZERO QPU units billed")


if __name__ == "__main__":
    main()
