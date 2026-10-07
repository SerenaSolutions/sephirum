#!/usr/bin/env python3
"""
CONFRONTO: ZEPHIRUM × {Qiskit, Cirq, PennyLane} — fecho do ciclo.
=====================================================================

Os três SDKs quânticos atuais enfrentam o ZEPHIRUM nas mesmas arenas,
com a arquitetura preservada: ZEPHIRUM DECIDE (Schmidt exato,
certificado, ZERO execução); cada SDK EXECUTA o que a escada eliminou
(statevector, matriz densidade, pureza, autovalores de ρ_A) como gêmeo
adversarial numérico.

Arenas (uma violação = FAIL):
  A1  300 estados aleatórios: decisão certificada ZEPHIRUM ==
      resposta numérica de cada SDK (limiar sempre distante do C exato;
      empate exato fica com o exato por contrato)
  A2  48 estados PRODUTO: ZEPHIRUM certifica C = 0 EXATO; cada SDK
      devolve ruído/NaN na rota sqrt(2(1-pureza)) — medidos por SDK
  A3  FRONTEIRA 2^53 (det = 1 exato): cada SDK confrontado nas duas
      rotas (det float vs pureza) — o ZEPHIRUM é o único veredicto
      estável; registra-se se o SDK se contradiz
  A4  rota de autovalores de ρ_A: concordância com Schmidt exato
  A5  contabilidade: TODAS as decisões ZEPHIRUM com ZERO execução
  A6  registro honesto: os três adaptadores vivos; desconhecido =>
      ValueError; ausência de dependência => SKIP explícito
"""
import math
import sys
import warnings
from fractions import Fraction

warnings.filterwarnings("ignore", category=RuntimeWarning)

from nexa_core import NCA, parse_nexa
from verify_certificate import verify
from zephirum_qinterop import (BACKENDS, ModelNotAvailable, get_backend,
                                zephirum_decide)


def main():
    import random
    random.seed(2026)

    # ---- os combatentes presentes (§12: quem não tem, sai com SKIP) ----
    sdks = {}
    for name in ("qiskit", "cirq", "pennylane"):
        try:
            sdks[name] = get_backend(name)
        except ModelNotAvailable as e:
            print("SKIP %s: %s" % (name, e))
    if not sdks:
        print("SKIP total: nenhum SDK instalado (pip install qiskit cirq "
              "pennylane)")
        return 0
    print("CONFRONTO: ZEPHIRUM (exato) x %s"
          % " x ".join(sorted(sdks)))

    # ---------- A1: 300 estados aleatórios por SDK ----------
    states = []
    for i in range(300):
        a, b, c, d = (random.randint(-5, 5) for _ in range(4))
        if (a, b, c, d) == (0, 0, 0, 0):
            continue
        C = abs(2 * (a * d - b * c))
        n = a * a + b * b + c * c + d * d
        t = max([0.05, 0.2, 0.4, 0.6, 0.8], key=lambda x: abs(C / n - x))
        states.append((i, "%d, %d, %d, %d" % (a, b, c, d),
                       a, b, c, d, n, t))
    agree = {k: 0 for k in sdks}
    sdk_nan = {k: 0 for k in sdks}
    zero_exec = 0
    for i, state, a, b, c, d, n, t in states:
        question = "concurrence > %s" % t
        res = zephirum_decide(state, question, "c%d" % i)
        assert res["required"] in (0, None), "emaranhado com residual?!"
        assert res["status"] == "DECIDED_WITHOUT_EXECUTION"
        zero_exec += 1
        ok, _ = verify(parse_nexa("ASK:\n    question: %s\nMODEL:\n    type: "
                                  "entanglement\n    state: %s\n"
                                  % (question, state)), res["certificate"])
        assert ok
        fl = [x / math.sqrt(n) for x in (a, b, c, d)]
        for name, bk in sdks.items():
            cq = bk.concurrence(fl)
            if math.isnan(cq):
                sdk_nan[name] += 1     # o SDK não conseguiu responder
            elif (cq > t) == res["answer"]:
                agree[name] += 1
    for name in sdks:
        # discordância genuína é FALHA; NaN do SDK é instabilidade DELE
        assert agree[name] == len(states) - sdk_nan[name], \
            "%s discordou de verdade em %d casos" % (
                name, len(states) - sdk_nan[name] - agree[name])
    print("A1 %d estados aleatórios: concordância total com o certificado "
          "ZEPHIRUM (%s)%s" % (len(states),
          " | ".join("%s %d/%d" % (k, agree[k], len(states))
                     for k in sorted(agree)),
          (" | NaN sem resposta: %s" % " ".join(
              "%s=%d" % (k, sdk_nan[k]) for k in sorted(sdk_nan)
              if sdk_nan[k])) if any(sdk_nan.values()) else ""))

    # ---------- A2: estados produto — ruído e NaN por SDK ----------
    prods = []
    for i in range(48):
        p0, p1, q0, q1 = (random.randint(-4, 4) for _ in range(4))
        if (p0, p1) == (0, 0) or (q0, q1) == (0, 0):
            continue
        amps = (p0 * q0, p0 * q1, p1 * q0, p1 * q1)
        n = sum(x * x for x in amps)
        prods.append((amps, n))
    stats = {k: {"noise": 0.0, "nan": 0} for k in sdks}
    zeph_zero = 0
    for amps, n in prods:
        state = "%d, %d, %d, %d" % amps
        res = zephirum_decide(state, "concurrence > 0", "p")
        assert res["answer"] is False, "produto com C exato != 0?!"
        zeph_zero += 1
        fl = [x / math.sqrt(n) for x in amps]
        for name, bk in sdks.items():
            cq = bk.concurrence(fl)
            if math.isnan(cq):
                stats[name]["nan"] += 1
            else:
                stats[name]["noise"] = max(stats[name]["noise"], abs(cq))
    print("A2 %d estados PRODUTO: ZEPHIRUM certifica C = 0 EXATO em TODOS; "
          "por SDK (ruído máx / NaN na rota da pureza): %s"
          % (len(prods), " | ".join("%s %.1e / %d nan" % (k, v["noise"],
                                                          v["nan"])
                                   for k, v in stats.items())))
    assert zeph_zero == len(prods)

    # ---------- A3: fronteira 2^53 — cada SDK se confronta ----------
    BIG = 2 ** 53
    state = "%d, 1, %d, 1" % (BIG + 1, BIG)          # det = 1 EXATO
    n = (BIG + 1) ** 2 + 1 + BIG ** 2 + 1
    fl = [(BIG + 1) / math.sqrt(n), 1 / math.sqrt(n),
          BIG / math.sqrt(n), 1 / math.sqrt(n)]
    res = zephirum_decide(state, "entangled > 0.5", "trap")
    assert res["answer"] is True                    # det=1 exato: EMARANHADO
    det_float = fl[0] * fl[3] - fl[1] * fl[2]
    assert det_float == 0.0                          # float colapsa
    a3 = {}
    for name, bk in sdks.items():
        cq = bk.concurrence(fl)
        eigs = bk.rho_a_eigenvalues(fl)
        pure = abs(eigs[0] - 1.0) < 1e-9
        # rota det (float): NÃO emaranhado | rota pureza: C>0 => sim
        contradiz = (det_float == 0.0) and (cq > 0.0 or math.isnan(cq))
        a3[name] = (cq, pure, contradiz)
    print("A3 FRONTEIRA 2^53 (det = 1 exato): float colapsa det para 0.0 "
          "(não-emaranhado); ZEPHIRUM certifica EMARANHADO; por SDK — %s"
          % " | ".join("%s: C=%.2e, rho_A puro=%s, SE CONTRADIZ=%s"
                       % (k, v[0], v[1], v[2]) for k, v in a3.items()))
    for name in sdks:
        assert a3[name][2] or a3[name][1], \
            "%s estável demais? registrar achado" % name

    # ---------- A4: rota de autovalores concorda com Schmidt ----------
    for name, bk in sdks.items():
        for state, kind in [("%d, %d, %d, %d" % (1, 0, 0, 1), True),
                            ("%d, %d, %d, %d" % (1, 1, 1, -1), True),
                            ("%d, %d, %d, %d" % (1, 2, 2, 4), False),
                            ("%d, %d, %d, %d" % (0, 1, 0, 2), False),
                            # Bell Phi+: det=9, MAXIMAMENTE emaranhado
                            ("%d, %d, %d, %d" % (3, 0, 0, 3), True)]:
            a, b, c, d = (int(x) for x in state.split(","))
            nn = a * a + b * b + c * c + d * d
            fll = [x / math.sqrt(nn) for x in (a, b, c, d)]
            e0 = bk.rho_a_eigenvalues(fll)[0]
            if kind:                                  # emaranhado: rho_A misto
                assert abs(e0 - 1.0) > 1e-9, (name, state)
            else:                                     # produto: rho_A puro
                assert abs(e0 - 1.0) < 1e-9, (name, state)
    print("A4 autovalores de rho_A: %s — TODOS concordam com o critério "
          "de Schmidt exato (emaranhado=misto, produto=puro)"
          % ", ".join(sorted(sdks)))

    # ---------- A6: registro honesto ----------
    for name in ("qiskit", "cirq", "pennylane"):
        assert name in BACKENDS
    try:
        get_backend("forest")
        raise AssertionError("SDK desconhecido aceito")
    except ValueError as e:
        assert "unknown SDK" in str(e)
    print("A6 registro: 3 adaptadores vivos; desconhecido => ValueError; "
          "ausência de SDK => SKIP explícito (nunca silêncio)")

    # ---------- A5: contabilidade ----------
    print("A5 contabilidade: %d+%d decisões ZEPHIRUM com ZERO unidades de "
          "execução (degrau ANALYTIC) — os SDKs rodaram statevector/matriz "
          "densa em TODAS: a computação eliminada, executada só para "
          "provar que era desnecessária" % (len(states), len(prods)))
    print("RESULTADO: PASS — o ciclo fecha: ZEPHIRUM decide certificado; "
          "a stack quântica atual valida executando")
    return 0


if __name__ == "__main__":
    sys.exit(main())
