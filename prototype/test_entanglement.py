#!/usr/bin/env python3
"""
TESTE DA FAMÍLIA EMARANHADO (Fase 3 — direção do chefe:
"ponha à prova a linguagem do algoritmo de emaranhado").
=================================================================

A linguagem ZEPHIRUM decide perguntas SOBRE emaranhamento de 2 qubits
puros pelo critério fechado de Schmidt — exato por Fraction, sem
simular o vetor de estado. Este teste põe a família à prova:

  1. VERDADE-TERRENO INDEPENDENTE: autovalores de ρ_A = M·Mᵗ por via
     numérica float (fórmula quadrática + raiz), C = 2√(λ₁λ₂)/⟨ψ|ψ⟩ —
     aritmética DIFERENTE da fração exata do motor. Casos de contorno
     (C == t) usam a verdade exata declarada à mão (float não decide
     igualdade).

  2. CERTIFICADO: todos verificados pelo checker independente
     (rota det(MMᵗ) = det(M)²).

  3. ADULTERAÇÃO: certificado de Bell forjado (det trocado) com hash
     recalculado tem que ser REJEITADO — não-confiança na família nova.

  4. CONTORNO: estados produto, Bell, parciais, decimais, limiares
     negativos, t > 1 (C ≤ 1 sempre, por AM-GM), zero-state estrutural.
"""
import copy
import math
import sys
from fractions import Fraction

from decision_kernel import digest
from nexa_core import parse_nexa, NCA
from verify_certificate import verify


def float_C(a, b, c, d):
    """Verdade-terreno independente: autovalores de ρ_A por via float."""
    M = [[a, b], [c, d]]
    tr = M[0][0] ** 2 + M[0][1] ** 2 + M[1][0] ** 2 + M[1][1] ** 2
    det_rho = (M[0][0] * M[1][1] - M[0][1] * M[1][0]) ** 2
    disc = tr * tr - 4 * det_rho
    if disc < 0:
        disc = 0.0
    l1 = (tr + math.sqrt(disc)) / 2
    l2 = (tr - math.sqrt(disc)) / 2
    return 2 * math.sqrt(l1 * l2) / tr  # concurrence via Schmidt


def z(src, name="t"):
    blocks = parse_nexa(src)
    res = NCA(blocks, name).compile()
    ok, reason = verify(blocks, res["certificate"])
    assert ok, "certificado rejeitado (%s): %s" % (name, reason)
    return res


def q(state, question):
    return ("ASK:\n    question: %s\nMODEL:\n    type: entanglement\n"
            "    state: %s\n" % (question, state))


CASES = [
    # (estado, pergunta, tipo, expected)
    # produto: det = 0
    ("1, 0, 0, 0", "entangled == 1", "exact", False),
    ("1, 0, 0, 0", "entangled == 0", "exact", True),
    ("1, 1, 1, 1", "entangled == 1", "exact", False),      # |++⟩ produto
    ("2, 3, 4, 6", "entangled == 0", "exact", True),       # razões iguais
    ("0.5, 0.5, 0.5, 0.5", "concurrence > 0.1", "exact", False),
    # Bell: C = 1
    ("1, 0, 0, 1", "concurrence > 0.5", "float", True),
    ("1, 0, 0, -1", "concurrence > 0.5", "float", True),
    ("0, 1, 1, 0", "concurrence > 0.99", "float", True),
    ("0, 1, -1, 0", "entangled == 1", "exact", True),
    ("0.5, 0, 0, 0.5", "concurrence > 0.5", "float", True),
    # parciais
    ("3, 0, 0, 4", "concurrence > 0.9", "float", True),    # C = 24/25
    ("3, 0, 0, 4", "concurrence > 0.97", "float", False),
    ("1, 2, 3, 4", "concurrence > 0.13", "float", True),   # C = 2/15
    ("1, 2, 3, 4", "concurrence > 0.14", "float", False),
    ("1, 1, 1, 2", "concurrence > 0.28", "float", True),    # C = 2/7
    ("1, 1, 1, 2", "concurrence > 0.29", "float", False),
    ("1, 0, 1, 1", "concurrence > 0.66", "float", True),   # C = 2/3
    ("1, 0, 1, 1", "concurrence > 0.67", "float", False),
    # contorno exato (float não decide igualdade: verdade à mão)
    ("1, 0, 0, 1", "concurrence > 1", "exact", False),     # C == 1: > é falso
    ("1, 0, 0, 1", "concurrence >= 1", "exact", True),
    ("1, 0, 0, 1", "concurrence == 1", "exact", True),
    ("1, 0, 0, 1", "concurrence < 1", "exact", False),
    ("1, 0, 0, 1", "concurrence <= 1", "exact", True),
    ("3, 0, 0, 4", "concurrence == 0.96", "exact", True),   # C = 24/25
    ("3, 0, 0, 4", "concurrence > 0.96", "exact", False),
    ("1, 2, 3, 4", "concurrence == 0.13333333333333333", "skip", None),
    ("1, 0, 0, 0", "concurrence > 0", "exact", False),     # C == 0
    ("1, 0, 0, 0", "concurrence <= 0", "exact", True),
    # limiares negativos / grandes
    ("1, 0, 0, 1", "concurrence > -0.5", "exact", True),
    ("1, 0, 0, 1", "concurrence < -0.5", "exact", False),
    ("1, 0, 0, 1", "concurrence <= -1", "exact", False),
    ("3, 0, 0, 4", "concurrence > 2", "exact", False),      # C <= 1 sempre
    ("1, 2, 3, 4", "concurrence > 1.5", "exact", False),
]


def main():
    ok = 0
    for i, (state, question, kind, expected) in enumerate(CASES):
        if kind == "skip":
            continue
        src = q(state, question)
        res = z(src, "ent%02d" % i)
        if kind == "float":
            a, b, c, d = (float(x) for x in state.split(","))
            t = float(question.rsplit(" ", 1)[1])
            Cf = float_C(a, b, c, d)
            if abs(Cf - t) < 1e-6:
                continue  # ambíguo para a via float — só contorno exato decide
            expected = Cf > t
            if question.startswith("concurrence <"):
                expected = Cf < t
        assert res["answer"] == expected, (
            "caso %d: %s | %s => motor %r, verdade %r"
            % (i, state, question, res["answer"], expected))
        assert res["status"] == "DECIDED_WITHOUT_EXECUTION", (state, question)
        assert res["required"] == 0
        ok += 1

    # ---- estado-zero: erro estrutural explícito (§12) ----
    try:
        z(q("0, 0, 0, 0", "entangled == 1"), "zero")
        raise AssertionError("estado-zero virou decisão — devia ser ValueError")
    except ValueError as e:
        assert "zero state" in str(e)

    # ---- adulteração: Bell com det forjado + REHASH tem que cair ----
    blocks = parse_nexa(q("1, 0, 0, 1", "concurrence > 0.5"))
    res = NCA(blocks, "forged").compile()
    for field, val in (("det", "0"), ("concurrence", "0"),
                       ("amplitudes", ["0", "0", "0", "1"])):
        t = copy.deepcopy(res["certificate"])
        t["EVIDENCE"][field] = val
        t.pop("CERT_HASH", None)
        t["CERT_HASH"] = digest(t)   # atacante recalcula o hash
        okc, _ = verify(blocks, t)
        assert okc is False, "Bell forjado (%s=%r) foi ACEITO" % (field, val)
        ok += 1

    print("(emaranhado) %d casos: motor exato == verdade-terreno float;"
          " contornos exatos; forja REHASH rejeitada (3/3)" % ok)
    print("RESULTADO: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
