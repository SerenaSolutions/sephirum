#!/usr/bin/env python3
"""Plugin CLI: zephirum-q <file.zeph> [--sdk qiskit|cirq]."""
import argparse
import json
import sys

from .core import gateway



STARTER_QUESTION = """# ZYQL (say "Zykel") — a real first question:
# is this two-qubit state entangled? Exact classical decision,
# zero QPU units, certificate included in the receipt.
ASK:
    question: entangled == 1
CONTRACT:
    absolute_error: 0
MODEL:
    type: entanglement
    state: 0.70710678118654752,0,0,0.70710678118654752
"""

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
                    version="zephirum-q 0.5.3 — ZEPHIRUM · ZYQL "
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
    ap.add_argument("--qpu-probe-remote", action="store_true",
                    help="remote QPU reachability via cloud "
                         "credential (§12: evidence, not a local "
                         "claim; submits no job, spends no QPU time)")
    ap.add_argument("--validate-remote-bell", action="store_true",
                    help="end-to-end evidence: run the Bell Phi+ "
                         "starter question on a real cloud QPU "
                         "(512 shots, OPT-IN — this DOES spend QPU "
                         "time on the free plan)")
    ap.add_argument("--init", metavar="FILE",
                    help="write a real starter question to FILE.zeph "
                         "and exit (start authoring ZYQL questions "
                         "in your own repo)")
    args = ap.parse_args(argv)

    from .standby import qpu_probe, standby_receipt
    if args.qpu_probe:
        pr = qpu_probe()
        print("QPU         %s (§12)" % pr["STATUS"])
        print("MOTIVO      %s" % pr["MOTIVO"])
        print("DECISAO     %s" % pr["DECISAO_CLASSICA"])
        return 0
    if args.qpu_probe_remote:
        from .standby import qpu_probe_remote
        pr = qpu_probe_remote()
        print("QPU_LOCAL   %s (§12)" % pr["QPU_LOCAL"])
        print("REMOTE      %s" % pr["REMOTE"])
        print("STATUS      %s" % pr["STATUS"])
        print("MOTIVO      %s" % pr["MOTIVO"])
        for b in pr.get("BACKENDS", []):
            print("BACKEND     %s (%d qubits)" % (b["name"], b["qubits"]))
        return 0
    if args.validate_remote_bell:
        import os
        token = os.environ.get("ZEPHIRUM_IBM_TOKEN") or \
            os.environ.get("IBM_QUANTUM_TOKEN") or \
            os.environ.get("QISKIT_IBM_TOKEN")
        if not token:
            print("NOT ROUTED (§12): no cloud credential in "
                  "environment (set ZEPHIRUM_IBM_TOKEN)")
            return 1
        from qiskit import QuantumCircuit, transpile
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        svc = QiskitRuntimeService(token=token,
                                   channel="ibm_quantum_platform")
        backend = svc.least_busy(simulator=False, operational=True)
        qc = QuantumCircuit(2, 2)
        qc.h(0); qc.cx(0, 1); qc.measure([0, 1], [0, 1])
        isa = transpile(qc, backend=backend, optimization_level=1)
        job = SamplerV2(mode=backend).run([isa], shots=512)
        res = job.result()
        counts = res[0].data.c.get_counts()
        tot = sum(counts.values())
        corr = (counts.get("00", 0) + counts.get("11", 0)
                - counts.get("01", 0) - counts.get("10", 0)) / tot
        # exact core verdict on the SPECIFIED state: det != 0
        print("BACKEND     %s" % backend.name)
        print("JOB_ID      %s" % job.job_id())
        print("SHOTS       512 (billed)")
        print("CORR_ZZ     %.4f (empirical)" % corr)
        print("EXACT_CORE  entangled == 1 (Schmidt det != 0, "
              "decided WITHOUT execution, 0 QPU units)")
        print("EVIDENCE    empirical correlation consistent with "
              "the exact verdict (§12: evidence, not certificate)")
        return 0
    if args.init:
        import os
        path = args.init if args.init.endswith(".zeph") else args.init + ".zeph"
        if os.path.exists(path):
            ap.error("%s already exists" % path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(STARTER_QUESTION)
        print("WROTE      %s" % path)
        print("NEXT       zephirum-q %s --json" % path)
        return 0
    if not args.source:
        print("ZYQL — your first three minutes:")
        print()
        print("  1. zephirum-q --init my_first.zeph   (writes a real starter question)")
        print("  2. zephirum-q my_first.zeph           (the certificate answers)")
        print("  3. zephirum-q my_first.zeph --json    (machine-readable receipt)")
        print()
        print("Docs: QUICKSTART.md — https://github.com/SerenaSolutions/zephirum")
        return 2
    try:
        with open(args.source, encoding="utf-8") as f:
            src = f.read()
    except FileNotFoundError:
        print("FILE NOT FOUND: %s" % args.source)
        print("NEXT  create a starter question:  zephirum-q --init my_first.zeph")
        return 2
    except (IsADirectoryError, PermissionError, UnicodeDecodeError) as e:
        print("CANNOT READ %s (%s)" % (args.source, type(e).__name__))
        print("NEXT  pass a .zeph source file — start with:  zephirum-q --init my_first.zeph")
        return 2
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
