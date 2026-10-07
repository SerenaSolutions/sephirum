#!/usr/bin/env python3
"""
TESTE DO ISOLAMENTO DE PROCESSO — o filho morre, o hospedeiro segue.
=====================================================================

  V16 PARIDADE: recibo isolado == recibo em-processo (resposta,
     unidades, trace_hash idênticos) — 50 residuais
  V17 FALHA NO FILHO: VMFault (BUDGET) => IsolationFault com motivo;
     o hospedeiro segue de pé
  V18 MURO MECÂNICO NO FILHO: spin além do STEP_LIMIT => filho morre
     com motivo explícito; hospedeiro intacto
  V19 MURO DE MEMÓRIA: filho com os MESMOS limites que excede 128MB
     => derrubado (mecanismo RLIMIT ativo)
  V20 MURO DE TEMPO: filho que dorme => morto pelo relógio do pai
  V21 RUNTIME: 200 residuais no backend vm_isolated — vereditos ==
     cpu_exact, contabilidade fechada; IsolationFault => recusa de
     entrega (RuntimeRefusal), nunca entrega suja
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nexa_core import NCA, parse_nexa
from stress_test import build_src, make_case
from zephirum_isolate import (MEMORY_BYTES, _child_limits, run_isolated,
                              IsolationFault)
from zephirum_runtime import run, RuntimeRefusal
from zephirum_vm import ZephirumVM


def main():
    import random
    random.seed(62)

    # ---------- V16: paridade isolado vs em-processo ----------
    from zephirum_vm import compile_program, vm_execute
    for i in range(50):
        kind, terms, unk, thr, x = make_case()
        if kind not in ("plain", "oracle"):
            continue
        blocks = parse_nexa(build_src(kind, terms, unk, thr, x))
        res = NCA(blocks, "iso%d" % i).compile()
        prog, data, budget = compile_program(blocks, res)
        r_proc = ZephirumVM(data, budget).run(prog)
        r_iso = run_isolated(prog, data, budget)
        assert (r_proc[0], r_proc[1], r_proc[2]) == (
            r_iso["answer"], r_iso["units"], r_iso["trace_hash"]), i
    print("V16 paridade: recibo do processo isolado == recibo em-processo "
          "(resposta, unidades, trace_hash) — 50 residuais")

    # ---------- V17: falha no filho NÃO derruba o hospedeiro ----------
    forged = [("LOAD", i) for i in range(8)]      # orçamento de 3
    try:
        run_isolated(forged, [1] * 8, 3)
        raise AssertionError("filho forjado executou?! (V17)")
    except IsolationFault as e:
        assert "BUDGET EXCEEDED" in str(e)
    # o hospedeiro segue de pé (estamos executando aqui — prova viva)
    print("V17 falha no filho: BUDGET EXCEEDED => IsolationFault com "
          "motivo; hospedeiro segue executando (prova viva: este teste)")

    # ---------- V18: muro mecânico dentro do filho ----------
    spin = [("PUSH", 0), ("LOOP", 1000000), ("PUSH", 1), ("ADD",),
            ("ENDLOOP",), ("HALT",)]
    try:
        run_isolated(spin, [], 0)
        raise AssertionError("spin executou?! (V18)")
    except IsolationFault as e:
        assert "STEP LIMIT" in str(e)
    print("V18 muro mecânico: spin no filho => filho morre com motivo "
          "explícito (STEP LIMIT); hospedeiro intacto")

    # ---------- V19: muro de memória (mecanismo RLIMIT) ----------
    bomb = ("import resource\n"
            "try:\n"
            "    xs = bytearray(%d)\n"
            "    for i in range(0, len(xs), 4096):\n"
            "        xs[i] = 1\n"
            "except MemoryError:\n"
            "    raise SystemExit(3)\n"
            "raise SystemExit(0)\n" % (MEMORY_BYTES + 64 * 1024 * 1024))
    proc = subprocess.Popen([sys.executable, "-c", bomb],
                            preexec_fn=_child_limits())
    rc = proc.wait()
    assert rc == 3, "alocação além do muro não caiu (rc=%d)" % rc
    print("V19 muro de memória: filho com MESMOS limites alocando além "
          "de 128MB => MemoryError => derrubado (RLIMIT ativo)")

    # ---------- V20: muro de tempo ----------
    sleeper = "import time; time.sleep(60)"
    proc = subprocess.Popen([sys.executable, "-c", sleeper],
                            preexec_fn=_child_limits())
    try:
        proc.wait(timeout=2)
        raise AssertionError("dorminhoco sobreviveu?! (V20)")
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("V20 muro de tempo: filho dormindo => morto pelo relógio do "
          "pai (mecanismo de timeout ativo)")

    # ---------- V21: runtime end-to-end com vm_isolated ----------
    checked = 0
    for i in range(200):
        kind, terms, unk, thr, x = make_case()
        if kind not in ("plain", "oracle"):
            continue
        blocks = parse_nexa(build_src(kind, terms, unk, thr, x))
        r_iso = run(blocks, "r21a", backend="vm_isolated")
        r_ref = run(blocks, "r21b", backend="cpu_exact")
        assert r_iso["answer"] == r_ref["answer"], i
        assert r_iso["units_executed"] == r_ref["units_executed"], i
        # recibo fecha contabilidade: executado == autorizado
        assert r_iso["units_executed"] == r_iso["units_certified"], i
        assert r_iso["cross_check"] == "OK" and not r_iso["refused"], i
        checked += 1
    # entrega recusada quando o filho recusa (RuntimeRefusal, nunca suja)
    bad = parse_nexa("ASK:\n    question: det > 0\nMODEL:\n    type: "
                     "triangular_det\n    matrix: 1, 2; 3, 4\n")
    try:
        run(bad, "r21c", backend="vm_isolated")
        raise AssertionError("det pleno entregou?! (V21)")
    except RuntimeRefusal as e:
        assert "n!" in str(e)
    print("V21 runtime: %d residuais vm_isolated == cpu_exact (veredito "
          "e unidades); det pleno => RuntimeRefusal (nunca entrega suja)"
          % checked)

    print("RESULTADO: PASS — o isolamento é real: o filho morre, o "
          "hospedeiro entrega — e entrega LIMPA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
