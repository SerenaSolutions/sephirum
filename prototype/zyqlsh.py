#!/usr/bin/env python3
"""
ZYQLSH — the interactive shell of the ZEPHIRUM language.

ASK FIRST. PROVE NEXT. COMPUTE LAST.

Session model:
  - paste a .zeph program (ASK/CONTRACT/MODEL, optionally BUDGET/REQUIRE),
    then an empty line: the kernel decides it and prints the verdict,
    the elimination (naive vs certified units) and the certificate hash.
  - commands start with ':':
      :help             this help
      :families         supported model families
      :receipts [N]     last N session receipts (default 5)
      :verify <file>    re-verify a receipt saved in this session
      :clear            clear screen
      :exit | :quit     leave the shell (EOF also works)
  - every decided question is saved as a numbered receipt in
    $ZEPHIRUM_HOME/receipts/zyqlsh/ with SHA-256 content hash.

Honesty contract (unchanged from the kernel): verdicts are trivalent
TRUE / FALSE / UNKNOWN; no guessing, no eval, exact arithmetic only.
"""
import hashlib
import json
import os
import sys
import time
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zephirum_decide import BANNER, decide
from zephirum_lexer import parse_zephirum

PROMPT = "zyql> "
BLOCK_PROMPT = "  ...> "
RECEIPT_DIR = os.path.join(os.environ.get("ZEPHIRUM_HOME",
                          os.path.expanduser("~/.zephirum")), "receipts", "zyqlsh")

FAMILIES = {
    "gauss_series": "sum 1..n asked against a threshold — decided by n(n+1)/2",
    "arithmetic_mean": "mean of 1..n — decided by (n+1)/2",
    "geometric_inf": "infinite geometric series a, ar, ar^2, ... — decided by a/(1-r)",
}


def _fmt(fr):
    return str(fr) if fr.denominator != 1 else str(fr.numerator)


def print_help():
    print(__doc__)


def save_receipt(number, src, res):
    plan, boot, naive = res[0]
    rec = {
        "shell": "zyqlsh",
        "received_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": src,
        "family": res[1],
        "boot": {k: v for k, v in boot.items()},
        "naive_units": naive["units"],
        "certified_units": boot["units"],
    }
    rec["receipt_hash"] = hashlib.sha256(
        json.dumps(rec, sort_keys=True).encode()).hexdigest()
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    path = os.path.join(RECEIPT_DIR, "receipt_%03d.json" % number)
    with open(path, "w") as fh:
        json.dump(rec, fh, indent=2, sort_keys=True)
    return path, rec


def decide_and_report(number, src, boot_only=False):
    res = decide_boot_only(src) if boot_only else decide(src)
    plan, boot, naive = res[0]
    fam = res[1]
    op, thr = res[2], res[3]
    path, rec = save_receipt(number, src, res)
    print()
    print("MODEL:   %s" % fam)
    print("ASK:     is the quantity %s %s ?" % (op, _fmt(thr)))
    print()
    if naive.get("simulated") is False:
        print("NAIVE    : %d units (NOT simulated — VM budget refusal, §12 honesty)"
              % naive["units"])
    else:
        print("NAIVE    : %d units of computation" % naive["units"])
    print("ZEPHIRUM : %d certified units (budget %d) — elimination %d/%d"
          % (boot["units"], boot["budget"], naive["units"] - boot["units"],
             naive["units"]))
    verdict = boot["answer"]
    label = "UNKNOWN" if verdict is None else ("TRUE" if verdict else "FALSE")
    rec["label"] = label
    print("VERDICT  : %s" % label)
    print("INPUT_HASH  : %s" % boot["input_hash"])
    print("RECEIPT  : %s" % path)
    print("CERT:    receipt_hash %s" % rec["receipt_hash"][:32])
    print()
    return rec


def decide_boot_only(src):
    """VM refused the naive twin (budget exceeded): decide the certified
    path alone and report the naive cost as arithmetic, not simulation.
    Honest refusal stays visible — the kernel never fakes a run."""
    from zephirum_decide import _parse_question
    from zephirum_boot import boot_compile, boot_run, build_src
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    fam = model.get("type")
    op, thr = _parse_question(blocks["ASK"]["question"])
    if fam != "gauss_series":
        raise SystemExit("unsupported family for boot-only decision: %r" % fam)
    n = int(model["n"])
    plan = boot_compile(build_src(n, op, thr))
    boot = boot_run(plan, "boot")
    naive = {"units": n, "answer": None, "simulated": False}
    return (plan, boot, naive), "gauss", op, thr


def main():
    print(BANNER)
    print("ZYQLSH — interactive shell. Paste a program, empty line to decide. :help for commands.")
    print()
    history = []
    buf = []
    while True:
        try:
            line = input(BLOCK_PROMPT if buf else PROMPT)
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("\n(use :exit to leave)")
            continue
        stripped = line.strip()
        if not buf:
            if not stripped:
                continue
            if stripped.startswith(":"):
                cmd = stripped.split()[0].lower()
                arg = stripped[len(cmd):].strip()
                if cmd in (":exit", ":quit"):
                    break
                elif cmd == ":help":
                    print_help()
                elif cmd == ":families":
                    for k, v in FAMILIES.items():
                        print("  %-16s %s" % (k, v))
                elif cmd == ":receipts":
                    n = int(arg) if arg.isdigit() else 5
                    for rec in history[-n:]:
                        print("  #%d %s -> %s (%d units, cert %.12s)"
                              % (rec["number"], rec["family"], rec["label"],
                                 rec["certified_units"], rec["receipt_hash"]))
                elif cmd == ":verify":
                    try:
                        data = json.load(open(arg))
                        calc = hashlib.sha256(json.dumps(
                            {k: v for k, v in data.items()
                             if k != "receipt_hash"},
                            sort_keys=True).encode()).hexdigest()
                        print("  %s" % ("VERIFIED — hash matches"
                                       if calc == data.get("receipt_hash")
                                       else "FORGED — hash mismatch"))
                    except FileNotFoundError:
                        print("  file not found: %s" % arg)
                elif cmd == ":clear":
                    print("\033[2J\033[H", end="")
                else:
                    print("  unknown command: %s (:help)" % cmd)
                continue
            buf.append(line)
        else:
            if stripped:
                buf.append(line)
                continue
            src = "\n".join(buf)
            buf = []
            try:
                parse_zephirum(src)  # syntax gate first: honest errors
                rec = decide_and_report(len(history) + 1, src)
                rec["number"] = len(history) + 1
                history.append(rec)
            except SystemExit as e:
                print("  KERNEL REFUSES: %s" % e)
            except Exception as e:
                if "pc=" in str(e):
                    try:
                        rec = decide_and_report(len(history) + 1, src,
                                                boot_only=True)
                        rec["number"] = len(history) + 1
                        history.append(rec)
                    except SystemExit as e2:
                        print("  KERNEL REFUSES: %s" % e2)
                    except Exception as e2:
                        print("  BOOT-ONLY FAILED: %s" % e2)
                else:
                    print("  SYNTAX/SEMANTIC ERROR: %s" % e)
    print("ZYQLSH closed. %d question(s) decided this session."
          % len(history))


if __name__ == "__main__":
    main()
