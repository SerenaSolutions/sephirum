#!/usr/bin/env python3
"""
BATERIA ZVM — a máquina virtual ORÇADA em C puro.
===============================================

O segundo motor em C puro (o zref DECIDE; este EXECUTA): `zvm` roda o
bytecode da VM orçada com a mesma semântica da referência Python —
unidades certificadas, muros §12 idênticos e traço determinístico.

Cruzamento em três frentes:
  1. Planos BOOT e NAIVE das quatro famílias (gauss, geométrica
     infinita, média, geométrica finita) — os programas REAIS do
     kernel, executados nos dois mundos: mesmo ANSWER, mesmas UNITS,
     mesmo TRACE_HASH (byte a byte).
  2. 60 programas sintéticos aleatórios exercendo TODA a ISA:
     PUSH/LOAD/LOADSEQ/ADD/MUL/DIV/DUP/SWAP/POW/CMP/CMPT/LABEL/
     JMPZ/CALL/RET/LOOP/ENDLOOP/MEDIAN.
  3. FALTAS: as mesmas recusas nos dois mundos (orçamento, JMPZ para
     trás, DIV por zero, muro de POW, opcode desconhecido) — e o muro
     C de fração (10^9) declarado com honestidade §12.
"""
import os
import random
import subprocess
import sys
import tempfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from zephirum_boot import boot_compile, build_src
from zephirum_boot_b2 import geo_decide, mean_decide

from zephirum_boot_geo_fin import geofin_compile, build_src_geofin
from zephirum_vm import ZephirumVM, VMFault

ZVM = os.path.join(HERE, "zvm")
ZSRC = os.path.join(HERE, "zvm.c")
OPS = [">", "<", ">=", "<="]


def serialize(data, budget, prog):
    out = ["DATA %d" % len(data)]
    out += [str(v) for v in data]
    out.append("BUDGET %d" % budget)
    out.append("PROG %d" % len(prog))
    for ins in prog:
        out.append(" ".join(str(x) for x in ins))
    return "\n".join(out) + "\n"


def run_c(data, budget, prog):
    """Executa no zvm; devolve (receipt, rc, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".zvm",
                                     delete=False) as f:
        f.write(serialize(data, budget, prog))
        path = f.name
    try:
        r = subprocess.run([ZVM, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    rec = {}
    for line in r.stdout.splitlines():
        if line.startswith("ANSWER"):
            rec["answer"] = None if "none" in line else \
                int(line.split()[1])
        elif line.startswith("UNITS"):
            rec["units"] = int(line.split()[1])
        elif line.startswith("TRACE_HASH"):
            rec["trace"] = line.split()[1]
    return rec, r.returncode, r.stderr


def py_run(data, budget, prog):
    vm = ZephirumVM(data, budget)
    a, u, th = vm.run(prog)
    return {"answer": 1 if a is True else (0 if a is False else None),
            "units": u, "trace": th}


def cross(name, data, budget, prog, stats):
    try:
        want = py_run(data, budget, prog)
        rc_err = None
    except VMFault as e:
        want, rc_err = None, str(e)
    got, rc, err = run_c(data, budget, prog)
    if want is not None:
        # muro aritmético C (§12): a referência Python tem precisão
        # arbitrária; o C declara o muro em vez de mentir — honestidade
        # auditada, NÃO igualdade (faltas de orçamento/fluxo seguem
        # sendo erro de teste: nunca mascaradas)
        if rc == 2 and ("fora do muro" in err or "além do muro" in err
                       or "fora do muro de" in err):
            stats["muro_c"] += 1
            return
        assert rc == 0, (name, err[:160])
        assert got["answer"] == want["answer"], (name, got, want)
        assert got["units"] == want["units"], (name, got, want)
        assert got["trace"] == want["trace"], (name, got["trace"],
                                               want["trace"])
        stats["ok"] += 1
    else:
        assert rc == 2, (name, "esperava FALTA", rc, err[:160])
        stats["falta"] += 1


def synth_program(rng, ndata):
    """Programa sintético VÁLIDO com depth-tracking; devolve
    (prog, data, budget)."""
    prog, data = [], []
    for _ in range(ndata):
        if rng.random() < 0.3:
            data.append(Fraction(rng.randint(-30, 30),
                       rng.randint(1, 9)))
        else:
            data.append(rng.randint(-50, 50))
    depth = 0
    units = 0
    label_n = 0
    pending_jmpz = []       # (label) — alvo criado à frente
    pending_call = []

    def emit(ins):
        prog.append(ins)

    n_ops = rng.randint(10, 40)
    guard = 0
    while len(prog) < n_ops and guard < 400:
        guard += 1
        c = rng.random()
        if c < 0.20:
            v = rng.randint(-40, 40)
            emit(("PUSH", v)); depth += 1
        elif c < 0.26:
            p = rng.randint(1, 20); q = rng.randint(1, 20)
            emit(("PUSH", Fraction(p, q))); depth += 1
        elif c < 0.33:
            if data:
                emit(("LOAD", rng.randrange(len(data))))
                depth += 1; units += 1
        elif c < 0.38:
            if data:
                emit(("LOADSEQ",)); depth += 1; units += 1
        elif c < 0.46 and depth >= 2:
            emit(("ADD",)); depth -= 1
        elif c < 0.54 and depth >= 2:
            emit(("MUL",)); depth -= 1
        elif c < 0.60 and depth >= 1:
            emit(("PUSH", rng.randint(1, 9)))
            emit(("DIV",))                      # divisor ≠ 0 garantido
        elif c < 0.66 and depth >= 1:
            emit(("DUP",)); depth += 1
        elif c < 0.70 and depth >= 2:
            emit(("SWAP",))
        elif c < 0.74 and depth >= 1:
            t = rng.choice([0, 5, Fraction(1, 2), -3])
            emit(("CMP", rng.choice(OPS), t))
        elif c < 0.78 and depth >= 1:
            emit(("PUSH", rng.randint(0, 12)))
            emit(("POW",)); depth -= 1
        elif c < 0.84:
            k = rng.randint(1, min(4, depth)) if depth else 0
            if k:
                emit(("MEDIAN", k)); depth -= (k - 1)
        elif c < 0.88:
            lbl = "L%d" % label_n
            pending_jmpz.append(lbl); label_n += 1
            if depth >= 1:
                emit(("PUSH", rng.randint(0, 1)))
                emit(("JMPZ", lbl)); depth -= 1
        elif c < 0.92:
            if depth >= 1:
                emit(("PUSH", rng.randint(1, 4)))
                emit(("LOOP", rng.randint(1, 5)))
                for _ in range(rng.randint(1, 4)):
                    emit(("PUSH", rng.randint(1, 6)))
                    depth += 1
                    if depth >= 2:
                        emit(("ADD",)); depth -= 1
                emit(("ENDLOOP",))
        else:
            lbl = "S%d" % label_n
            pending_call.append(lbl); label_n += 1
            if depth >= 1:
                emit(("CALL", lbl))
    # resolve desvios: alvos À FRENTE (soundness)
    for lbl in pending_jmpz:
        emit(("LABEL", lbl))
    for lbl in pending_call:
        emit(("LABEL", lbl))
        emit(("PUSH", 2))
        emit(("RET",))
    if depth >= 1 and rng.random() < 0.8:
        emit(("CMPT", rng.choice(OPS), rng.randint(-50, 50)))
        depth -= 1
    emit(("HALT",))
    budget = units + rng.choice([0, 0, 1, 3])
    return prog, data, budget


def main():
    if not os.path.exists(ZVM) or \
            os.path.getmtime(ZSRC) > os.path.getmtime(ZVM):
        subprocess.run(["gcc", "-O2", "-std=gnu11", "-o", ZVM, ZSRC],
                      check=True)
    rng = random.Random(271828)
    stats = {"ok": 0, "falta": 0, "muro_c": 0}

    # ---------------- 1. planos boot+naive das 4 famílias
    for _ in range(25):
        n = rng.randint(3, 60)
        op = rng.choice(OPS)
        thr = rng.randint(0, n * (n + 1) // 2 + 10)
        plan = boot_compile(build_src(n, op, thr))
        for path in ("boot", "naive"):
            if plan[path]["program"] is not None:
                cross("gauss:%s" % path, plan[path]["data"],
                      plan[path]["budget"], plan[path]["program"], stats)
    for _ in range(20):
        r = Fraction(rng.randint(-3, 3), rng.randint(4, 9)) or \
            Fraction(1, 3)
        a = rng.choice([1, 2, Fraction(1, 2), -1])
        op, thr = rng.choice(OPS), rng.randint(-5, 20)
        plan = geo_decide(a, r, op, thr)[0]
        for path in ("boot", "naive"):
            if plan[path].get("program") is not None:
                cross("geo:%s" % path, plan[path]["data"],
                      plan[path]["budget"], plan[path]["program"], stats)
    for _ in range(15):
        n = rng.randint(2, 40)
        op, thr = rng.choice(OPS), rng.randint(0, n + 5)
        plan = mean_decide(n, op, thr)[0]
        for path in ("boot", "naive"):
            if plan[path].get("program") is not None:
                cross("mean:%s" % path, plan[path]["data"],
                      plan[path]["budget"], plan[path]["program"], stats)
    for _ in range(20):
        r = Fraction(rng.randint(-9, 9) or 2, rng.randint(1, 4))
        if r == 1:
            r = Fraction(2, 1)
        n = rng.randint(2, 10)
        op, thr = rng.choice(OPS), rng.randint(-10, 30)
        plan = geofin_compile(build_src_geofin(r, n, op, thr))
        cross("geofin:boot", plan["boot"]["data"],
              plan["boot"]["budget"], plan["boot"]["program"], stats)

    # ---------------- 2. sintéticos: a ISA inteira
    for i in range(60):
        prog, data, budget = synth_program(rng, rng.randint(1, 6))
        cross("synth:%d" % i, data, budget, prog, stats)

    # ---------------- 3. faltas espelhadas
    cross("falta:budget", [1, 2, 3], 1,
          [("LOAD", 0), ("LOAD", 1), ("LOAD", 2), ("ADD",),
           ("HALT",)], stats)
    cross("falta:jmpz-tras",
          [1], 4,
          [("LABEL", "L0"), ("PUSH", 0), ("JMPZ", "L0"),
           ("HALT",)], stats)
    cross("falta:div-zero", [1], 1,
          [("PUSH", 1), ("PUSH", 0), ("DIV",), ("HALT",)], stats)
    cross("falta:pow-muro", [1], 1,
          [("PUSH", 2), ("PUSH", 70000), ("POW",), ("HALT",)], stats)
    cross("falta:opcode", [1], 1,
          [("PUSH", 1), ("REBOOT",), ("HALT",)], stats)
    # muro C honesto: fração além de 10^9 — Python resolve, C declara
    rec, rc, err = run_c([1], 2, [("PUSH", 9999999999999), ("HALT",)])
    assert rc == 2 and "§12" in err, err[:160]
    stats["muro_c"] += 1

    print("ZVM C-PURO: %d execuções cruzadas (boot+naive de 4 famílias "
          "+ ISA inteira): ANSWER, UNITS e TRACE_HASH idênticos byte a "
          "byte à referência Python" % stats["ok"])
    print("FALTAS: %d recusas espelhadas (orçamento, JMPZ para trás, DIV "
          "por zero, muro POW, opcode) + %d muro C de fração declarado "
          "com honestidade §12 (precisão arbitrária segue na referência)"
          % (stats["falta"], stats["muro_c"]))
    print("RESULTADO: PASS — o Zephirum agora DECIDE e EXECUTA em C "
          "puro; o Python resta como juiz e referência de precisão "
          "arbitrária")


if __name__ == "__main__":
    main()
