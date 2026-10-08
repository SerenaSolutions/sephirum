#!/usr/bin/env python3
"""CLI do plug-in: zephirum-q <arquivo.zeph> [--sdk qiskit|cirq]."""
import argparse
import json
import sys

from .core import gateway


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="zephirum-q",
        description="ZEPHIRUM Quantum Plugin — ZYQL (say \"Zykel\": "
                    "the Zephirum Query Language) decides entanglement "
                    "exactly, with a verifiable certificate and zero "
                    "QPU units")
    ap.add_argument("source", nargs="?",
                    help=".zeph source file (ZYQL source; optional "
                         "with --qpu-probe)")
    ap.add_argument("--version", action="version",
                    version="zephirum-q 0.5.1 — ZEPHIRUM · ZYQL "
                    "(say \"Zykel\")")
    ap.add_argument("--sdk", default=None,
                    help="adversarial twin for cross-checking "
                         "(qiskit|cirq)")
    ap.add_argument("--json", action="store_true",
                    help="full receipt in JSON")
    ap.add_argument("--standby", action="store_true",
                    help="standby mode: QPU status + active exact "
                         "classical decision (the plugin that waits "
                         "for quantum hardware)")
    ap.add_argument("--qpu-probe", action="store_true",
                    help="honest QPU status only (§12)")
    args = ap.parse_args(argv)

    from .standby import qpu_probe, standby_receipt
    if args.qpu_probe:
        pr = qpu_probe()
        print("QPU         %s (§12)" % pr["STATUS"])
        print("MOTIVO      %s" % pr["MOTIVO"])
        print("DECISAO     %s" % pr["DECISAO_CLASSICA"])
        return 0
    if not args.source:
        ap.error("source e obrigatorio (exceto com --qpu-probe)")
    with open(args.source, encoding="utf-8") as f:
        src = f.read()
    if args.standby:
        receipt, ok = standby_receipt(src)
    else:
        receipt, ok = gateway(src, sdk=args.sdk)
    if args.json:
        print(json.dumps(receipt, indent=2, ensure_ascii=False,
                         default=str))
        return 0 if receipt.get("routed") else 1
    if not receipt.get("routed"):
        print("NOT ROUTED (§12): %s" % receipt["reason"])
        return 1
    cert = receipt["cert"]
    print("STATUS      %s" % receipt["status"])
    print("VERDICT     %d" % receipt["verdict"])
    print("CONCURRENCE %s (exact)" % receipt["concurrence_exact"])
    print("QPU UNITS   %d (billed)" % receipt["qpu_units_billed"])
    print("INPUT_HASH  %s" % cert["INPUT_HASH"])
    print("CERT_HASH   %s" % cert["CERT_HASH"])
    print("INDEP CHECK %s" % receipt["independent_check"][1])
    if "pq_protect" in receipt:
        print("PQ PROTECT  %s" % receipt["pq_protect"][1])
    if "standby" in receipt:
        print("QPU         %s (§12) — exact classical decision ACTIVE"
              % receipt["standby"]["STATUS"])
    if "sdk_cross_check" in receipt:
        print("SDK CROSS   %s" % receipt["sdk_cross_check"])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
