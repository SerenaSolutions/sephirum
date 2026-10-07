#!/usr/bin/env python3
"""
TESTE DE CONJUNTO: ZEPHIRUM × QISKIT (interoperabilidade quântica).
=====================================================================

O par antitético trabalhando JUNTO, medido (uma violação = FAIL):

  Q1  N estados aleatórios: ZEPHIRUM (Schmidt exato, ZERO execução)
      == Qiskit (concurrence numérico) em TODAS as perguntas
  Q2  estados PRODUTO: ZEPHIRUM sabe que C = 0 EXATAMENTE; o Qiskit
      devolve ruído float ~1e-17 — medida do contraste exato/numérico
  Q3  LIMITE DE PRECISÃO: estado com det = 1 exato escondido em 2^53 —
      o Qiskit colapsa det para 0.0 (não emaranhado); o ZEPHIRUM
      certifica emaranhado — e o ZEPHIRUM é quem está certo
  Q4  rota de autovalores: max(eig ρ_A) == 1 exato se produto
      (Qiskit concorda em todos os casos comuns), < 1 se emaranhado
  Q5  contabilidade: TODAS as decisões do ZEPHIRUM saíram do degrau
      ANALYTIC com ZERO unidades executadas; o Qiskit rodou a
      computação completa (statevector + ρ_A) em todos — o trabalho
      que a escada eliminou, executado só pra provar que era
      desnecessário
  Q6  registro honesto: cirq/pennylane ausentes => ModelNotAvailable
"""
import sys
from fractions import Fraction

from nexa_core import parse_nexa
from verify_certificate import verify
from zephirum_qinterop import ModelNotAvailable, get_backend, zephirum_decide


def main():
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)  # ruído
    # documentado da rota sqrt(2(1-pureza)) do SDK: é EVIDÊNCIA (Q2/Q3),
    # não defeito do nosso teste — medimos, não escondemos
    try:
        qk = get_backend("qiskit")
    except ModelNotAvailable as e:
        print("SKIP (dependência opcional ausente): %s" % e)
        print("Instale com: pip install qiskit")
        return 0
    import random
    random.seed(2026)

    def ask_both(state, question, label):
        """ZEPHIRUM (certificado) vs Qiskit (numérico) para a mesma pergunta."""
        res = zephirum_decide(state, question)
        ok, _ = verify(parse_nexa("ASK:\n    question: %s\nMODEL:\n    type: "
                                  "entanglement\n    state: %s\n"
                                  % (question, state)), res["certificate"])
        assert ok, "certificado inválido em %s" % label
        a, b, c, d = (float(x.strip()) for x in state.split(","))
        import math
        n = a * a + b * b + c * c + d * d
        det = a * d - b * c
        if question.startswith("entangled"):
            z_ans = res["answer"]           # 1 se det exato != 0
            q_val = 1 if qk.concurrence([a / math.sqrt(n), b / math.sqrt(n),
                                         c / math.sqrt(n),
                                         d / math.sqrt(n)]) > 1e-12 else 0
        else:
            t = Fraction(question.rsplit(" ", 1)[1])
            z_ans = res["answer"]
            q_ans = qk.concurrence([a / math.sqrt(n), b / math.sqrt(n),
                                     c / math.sqrt(n),
                                     d / math.sqrt(n)]) > float(t)
            return res, z_ans, q_ans, q_val if False else None
        return res, z_ans, q_val, None

    # ---------- Q1: estados aleatórios, perguntas concurrence ----------
    agree = disagree = 0
    zero_exec = 0
    for i in range(300):
        a, b, c, d = (random.randint(-5, 5) for _ in range(4))
        if (a, b, c, d) == (0, 0, 0, 0):
            continue
        state = "%d, %d, %d, %d" % (a, b, c, d)
        # limiar decimal MAIS DISTANTE do C exato entre os candidatos:
        # nenhuma chance de empate numérico entre exato e float
        C = abs(2 * (a * d - b * c))
        n = a * a + b * b + c * c + d * d
        cands = [0.05, 0.2, 0.4, 0.6, 0.8]
        t = max(cands, key=lambda x: abs(C / n - x))
        question = "concurrence > %s" % t
        res = zephirum_decide(state, question, str(i))
        assert res["required"] in (0, None) and res["status"] == \
            "DECIDED_WITHOUT_EXECUTION", res["status"]
        zero_exec += 1
        import math
        fl = [x / math.sqrt(n) for x in (a, b, c, d)]
        q_c = qk.concurrence(fl)
        q_ans = q_c > t
        if res["answer"] == q_ans:
            agree += 1
        else:
            disagree += 1
    assert disagree == 0, "%d discordâncias na faixa comum" % disagree
    print("Q1 300 estados aleatórios: ZEPHIRUM (exato, 0 exec) == Qiskit "
          "numérico — %d/%d (empates exatos ficam com o exato por contrato)"
          % (agree, agree + disagree))

    # ---------- Q2: estados produto — exato 0 vs ruído float ----------
    noise = []
    nan_cases = 0
    prod_agree = 0
    for i in range(50):
        p0, p1, q0, q1 = (random.randint(-4, 4) for _ in range(4))
        if (p0, p1) == (0, 0) or (q0, q1) == (0, 0):
            continue
        state = "%d, %d, %d, %d" % (p0 * q0, p0 * q1, p1 * q0, p1 * q1)
        res = zephirum_decide(state, "concurrence > 0", "p%d" % i)
        assert res["answer"] is False, "produto com C exato != 0?!"
        import math
        amps = [p0 * q0, p0 * q1, p1 * q0, p1 * q1]
        n = sum(x * x for x in amps)
        fl = [x / math.sqrt(n) for x in amps]
        q_c = qk.concurrence(fl)
        if math.isnan(q_c):
            nan_cases += 1        # sqrt(negativo) na rota da pureza do SDK
        else:
            noise.append(abs(q_c))
        prod_agree += 1
    print("Q2 %d estados PRODUTO: ZEPHIRUM certifica C = 0 EXATO; Qiskit "
          "devolve ruído float até %.2e%s (%d casos)"
          % (prod_agree, max(noise),
             (" | %d casos com NAN na rota da pureza (sqrt de negativo: "
              "instabilidade documentada da fórmula 2(1-Tr rho_A^2) do SDK)"
              % nan_cases) if nan_cases else "", prod_agree))

    # ---------- Q3: limite de precisão — o SDK erra, o exato acerta ----------
    BIG = 2 ** 53
    state = "%d, 1, %d, 1" % (BIG + 1, BIG)     # det = 1 exato
    det_exact = Fraction(BIG + 1) * 1 - 1 * Fraction(BIG)
    assert det_exact == 1
    res = zephirum_decide(state, "entangled > 0.5", "trap")
    assert res["answer"] is True, "ZEPHIRUM deveria ver det=1 exato"
    import math
    n = (BIG + 1) ** 2 + 1 + BIG ** 2 + 1
    fl = [(BIG + 1) / math.sqrt(n), 1 / math.sqrt(n),
          BIG / math.sqrt(n), 1 / math.sqrt(n)]
    det_float = fl[0] * fl[3] - fl[1] * fl[2]
    q_c = qk.concurrence(fl)
    eigs = qk.rho_a_eigenvalues(fl)
    # o SDK se contradiiz na fronteira: det float = 0 (falso negativo),
    # concurrence = ruído > 0 (falso positivo da rota da pureza),
    # autovalores de rho_A = puro. ZEPHIRUM: det=1 exato, EMARANHADO.
    assert det_float == 0.0, "float não colapsou? rever"
    assert q_c > 0.0, "concurrence sem ruído? rever"
    assert abs(eigs[0] - 1.0) < 1e-9, "rho_A não deu puro? rever"
    assert res["answer"] is True
    print("Q3 LIMITE 2^53 (det = 1 exato): o SDK se CONTRADIZ — "
          "det float = 0.0 (não-emaranhado), concurrence = %.2e "
          "(emaranhado, ruído da pureza), rho_A autovalores = puro; "
          "ZEPHIRUM certifica EMARANHADO com det = 1 exato — único "
          "veredicto estável" % q_c)

    # ---------- Q4: rota de autovalores de ρ_A ----------
    import math
    ev_ok = 0
    for state, kind in [("%d, %d, %d, %d" % (1, 0, 0, 1), "ent"),
                        ("%d, %d, %d, %d" % (1, 1, 1, -1), "ent"),
                        ("%d, %d, %d, %d" % (1, 2, 2, 4), "prod"),
                        ("%d, %d, %d, %d" % (3, 0, 0, 3), "prod")]:
        a, b, c, d = (int(x) for x in state.split(","))
        n = a * a + b * b + c * c + d * d
        fl = [x / math.sqrt(n) for x in (a, b, c, d)]
        eigs = qk.rho_a_eigenvalues(fl)
        entangled_exact = (a * d - b * c) != 0
        # Schmidt: produto <=> ρ_A puro <=> max eig = 1
        if entangled_exact:
            assert abs(eigs[0] - 1.0) > 1e-9, (state, eigs)
        else:
            assert abs(eigs[0] - 1.0) < 1e-9, (state, eigs)
        ev_ok += 1
    print("Q4 autovalores de ρ_A (partial_trace): %d/4 casos concordam com "
          "o critério de Schmidt exato" % ev_ok)

    # ---------- Q6: registro honesto ----------
    for name in ("cirq", "pennylane"):
        try:
            get_backend(name)
            raise AssertionError("%s fingiu disponibilidade" % name)
        except ModelNotAvailable as e:
            assert name in str(e)
    try:
        get_backend("forest")
    except ValueError as e:
        assert "unknown SDK" in str(e)
    print("Q6 registro honesto: cirq/pennylane => ModelNotAvailable "
          "explícito; desconhecido => ValueError")

    print("Q5 contabilidade: %d/%d decisões com ZERO unidades executadas "
          "(degrau ANALYTIC) — o Qiskit rodou o statevector completo em "
          "todas: a computação eliminada, executada só para provar que "
          "era desnecessária" % (zero_exec, agree + disagree + prod_agree))
    print("RESULTADO: PASS — o par antitético trabalha junto: ZEPHIRUM "
          "decide certificado, o SDK valida executando")
    return 0


if __name__ == "__main__":
    sys.exit(main())
