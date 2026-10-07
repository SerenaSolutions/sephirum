#!/usr/bin/env python3
"""
CAMADA DE IA SOBRE A ESCADA ZEPHIRUM (charter, secao 7: "o gerador pode ser
complexo, heuristico ou baseado em IA; o verificador deve ser independente").

Enriquecimento honesto: um modelo estatistico (naive Bayes) aprende do LEDGER
de compilacoes anteriores a prever o estado final de um problema a partir de
features baratas. A previsao e CONSULTIVA: ela reordena tentativas e antecipa
orcamento, mas NUNCA decide. Quem decide continua sendo a escada + verificador
independente. SOUNDNESS INTACTA POR CONSTRUCAO.

Uso: previsao de estado (advisory) -> o sistema pode avisar ANTES de gastar
analise: "esta classe de problema tende a exigir execucao completa / UNKNOWN".
"""
import json
import math
import random
import sys
from collections import Counter, defaultdict

from nexa_core import parse_nexa, NCA
from stress_test import make_case, build_src

random.seed(7)
TRAIN_N, TEST_N = 40000, 10000


def featurize(kind, terms, unk, thr):
    """Features baratas: nenhuma executacao, so meta-dados do problema."""
    s = sum(terms)
    return (
        "kind=" + kind,
        "n=%d" % min(len(terms), 12),
        "ratio=%d" % min(int(10 * thr / max(s, 1)), 10),
        "has_bounds=%s" % ("y" if unk else "n"),
    )


def gen(n):
    rows = []
    for _ in range(n):
        kind, terms, unk, thr, x = make_case()
        blocks = parse_nexa(build_src(kind, terms, unk, thr, x))
        res = NCA(blocks, "ai").compile()
        rows.append((featurize(kind, terms, unk, thr), res["status"]))
    return rows


def train(rows):
    cls = Counter()
    fc = defaultdict(Counter)
    for feats, label in rows:
        cls[label] += 1
        for f in feats:
            fc[f][label] += 1
    return cls, fc


def predict(feats, cls, fc, n_feat_values):
    labels = list(cls)
    total = sum(cls.values())
    best, best_p = None, -1e18
    for label in labels:
        logp = math.log((cls[label] + 1.0) / (total + len(labels)))
        for f in feats:
            logp += math.log((fc[f][label] + 1.0) /
                             (cls[label] + n_feat_values))
        if logp > best_p:
            best_p, best = logp, label
    return best


def main():
    print("Coletando ledger: %d treino + %d teste..." % (TRAIN_N, TEST_N))
    train_rows = gen(TRAIN_N)
    test_rows = gen(TEST_N)
    cls, fc = train(train_rows)
    # numero aproximado de valores distintos por feature (para suavizacao)
    n_vals = len(set(f for row in train_rows for f in row[0]))

    correct = 0
    per_class = Counter()
    per_class_total = Counter()
    for feats, label in test_rows:
        pred = predict(feats, cls, fc, n_vals)
        per_class_total[label] += 1
        if pred == label:
            correct += 1
            per_class[label] += 1
    acc = 100.0 * correct / len(test_rows)
    majority = max(cls, key=cls.get)
    baseline = 100.0 * sum(1 for _, l in test_rows if l == majority) / len(test_rows)

    print("\nDistribuicao aprendida (treino):")
    for label, c in cls.most_common():
        print("  %-30s %6d (%.1f%%)" % (label, c, 100.0 * c / sum(cls.values())))
    print("\nAcuracia da camada de IA (teste, %d casos): %.2f%%" % (TEST_N, acc))
    print("Baseline (chutar classe majoritaria '%s'): %.2f%%" % (majority, baseline))
    print("\nRevocacao por classe:")
    for label in sorted(per_class_total):
        t = per_class_total[label]
        r = 100.0 * per_class[label] / t
        print("  %-30s %6.1f%%  (%d casos)" % (label, r, t))

    # Exemplo consultivo: previsao ANTES de compilar
    kind, terms, unk, thr, x = make_case()
    feats = featurize(kind, terms, unk, thr)
    pred = predict(feats, cls, fc, n_vals)
    print("\nExemplo de aviso previo (sem gastar analise):")
    print("  problema %s com %d termos, limiar %d -> previsao: %s" %
          (kind, len(terms), thr, pred))
    print("  (a escada ainda compila e verifica; a previsao so orienta orcamento)")

    out = {"train_n": TRAIN_N, "test_n": TEST_N, "accuracy_pct": round(acc, 2),
           "baseline_pct": round(baseline, 2),
           "per_class_recall": {k: round(100.0 * per_class[k] / per_class_total[k], 1)
                                for k in per_class_total}}
    with open("ai_layer_results.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    ok = acc > baseline + 10
    print("\nVEREDICTO:", "camada de IA aprendeu sinal util (>%s%% sobre baseline)"
          % (baseline + 10) if ok else "sinal fraco: manter como conselho, sem controle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
