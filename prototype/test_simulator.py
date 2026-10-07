#!/usr/bin/env python3
"""
TESTE DO SIMULATOR (Fase 4) — o gêmeo adversarial à prova.
==========================================================

Para 20.000 casos aleatórios + famílias fixas: o kernel eliminou
computação; o simulator EXECUTOU a computação completa de qualquer
jeito, por caminho independente. Critérios (soundness-first, um único
violamento = FAIL):

  H1  kernel == execução plena           (0 MISMATCH)
  H2  eliminação era desnecessária       (executada mesmo assim, mesma resposta)
  H3  contabilidade residual coerente    (required <= unidades plenas)
  H4  UNKNOWN é honesto                  (toda Z = subdeterminado na plena)
  H5  comparação de modelos              (float64 erra onde o exato acerta)

O número de cabeçalho: unidades que o simulator executou sem precisar
— a prova viva de que a eliminação funcionou.
"""
import sys

from nexa_core import parse_nexa
from zephirum_simulator import compare, falsify

from test_entanglement import CASES as ENT_CASES


def main():
    r = falsify(20000)
    print("diferencial 20.000 casos: agreed=%d unknown_validated=%d mismatch=%d"
          % (r["agreed"], r["unknown_validated"], r["mismatch"]))
    print("unidades plenas simuladas: %d | evitadas (eliminadas de fato): %d (%.2f%%)"
          % (r["simulated_units"], r["avoided_units"], r["avoided_pct"]))

    # H4 explícito: toda Z confirmada como subdeterminada pelo simulador
    assert r["unknown_validated"] > 0, "nenhum UNKNOWN no lote? bateria fraca"

    # famílias fixas: mediana, determinante (Laplace), geo (loop), expressão
    fixed = [
        ("ASK:\n    question: median > 50\nMODEL:\n    type: raw_data\n"
         "    data: 12, 87, 45, 63, 51, 39, 96, 4, 58", "median"),
        ("ASK:\n    question: det > 20\nMODEL:\n    type: triangular_det\n"
         "    matrix: 2,1,7; 0,3,4; 0,0,5", "det"),
        ("ASK:\n    question: sum > 100\nMODEL:\n    type: geometric_series\n"
         "    r: 2\n    n: 10", "geo"),
        ("ASK:\n    question: value >= 7\nMODEL:\n    type: expression\n"
         "    expr: (2 + 3) * 2 - 3", "expr"),
    ]
    for src, name in fixed:
        c = compare(parse_nexa(src), "fix_" + name)
        assert c["verdict"] == "agreed" and c["cert_ok"], (name, c["verdict"])
        print("família %-7s: kernel == plena (método independente) OK" % name)

    # emaranhado: modelo float64 vs exato concordam em todos os casos decimais
    ent_ok = 0
    for state, question, kind, expected in ENT_CASES:
        if kind in ("exact", "skip"):
            continue
        src = ("ASK:\n    question: %s\nMODEL:\n    type: entanglement\n"
               "    state: %s\n" % (question, state))
        c = compare(parse_nexa(src), "ent")
        assert c["verdict"] == "agreed" and c["cert_ok"], (state, question)
        ent_ok += 1
    print("emaranhado: float64 (simulador) == exato (kernel) em %d casos OK" % ent_ok)

    ok = (r["h1_kernel_equals_full"] and r["h3_accounting_consistent"]
          and r["h5_model_comparison"] and r["mismatch"] == 0)
    print("H1 kernel==plena: %s | H2 desnecessária: %d | H3 contábil: %s | "
          "H4 UNKNOWN honesto: %s | H5 modelos: %s"
          % (r["h1_kernel_equals_full"], r["h2_elimination_unnecessary"],
             r["h3_accounting_consistent"], bool(r["unknown_validated"]),
             r["h5_model_comparison"]))
    print("RESULTADO:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
