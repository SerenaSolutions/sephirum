#!/usr/bin/env python3
"""CLI do plug-in: zephirum-q <arquivo.zeph> [--sdk qiskit|cirq]."""
import argparse
import json
import sys

from .core import gateway


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="zephirum-q",
        description="Zephirum Quantum Plugin — decisão exata de "
                    "emaranhamento com certificado, zero unidades QPU")
    ap.add_argument("source", nargs="?",
                help="arquivo .zeph (fonte NEXA; opcional "
                     "com --qpu-probe)")
    ap.add_argument("--sdk", default=None,
                    help="gêmeo adversarial de contraprova (qiskit|cirq)")
    ap.add_argument("--json", action="store_true",
                    help="recibo completo em JSON")
    ap.add_argument("--standby", action="store_true",
                    help="modo standby: estado do QPU + decisão "
                         "clássica ativa (o plug-in que aguarda a "
                         "computação quântica)")
    ap.add_argument("--qpu-probe", action="store_true",
                    help="apenas o estado honesto do QPU (§12)")
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
        print("NAO ROTEADO (§12): %s" % receipt["reason"])
        return 1
    cert = receipt["cert"]
    print("STATUS      %s" % receipt["status"])
    print("VERDICT     %d" % receipt["verdict"])
    print("CONCURRENCE %s (exata)" % receipt["concurrence_exact"])
    print("QPU UNITS   %d (faturadas)" % receipt["qpu_units_billed"])
    print("INPUT_HASH  %s" % cert["INPUT_HASH"])
    print("CERT_HASH   %s" % cert["CERT_HASH"])
    print("INDEP CHECK %s" % receipt["independent_check"][1])
    if "standby" in receipt:
        print("QPU         %s (§12) — decisão clássica exata ATIVA"
              % receipt["standby"]["STATUS"])
    if "sdk_cross_check" in receipt:
        print("SDK CROSS   %s" % receipt["sdk_cross_check"])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
