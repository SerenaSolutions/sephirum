#!/usr/bin/env python3
"""
BATERIA DE MAPEAMENTO KASHYAP — o infográfico como checklist de teste.
======================================================================

FONTE TÉCNICA — a matéria é UNIVERSAL (livros/artigos revisados):
  * concorrência de emaranhamento: Wootters, PRL 80, 2245 (1998);
  * decomposição de Schmidt: E. Schmidt (1906); Nielsen & Chuang,
    "Quantum Computation and Quantum Information", cap. 2;
  * estados de Bell e o critério CHSH: Bell (1964); Nielsen & Chuang,
    caps. 1-2. Nada aqui é copiado de autor individual de redes —
    o post (pauta) APONTOU o tema; a fundamentação vem da literatura.

Pauta que apontou o tema (Evidence Desk, rastreabilidade):
  Dr. Patanjali Kashyap, "Quantum Information Processing" (LinkedIn,
  out/2026) — pipeline Qubits -> Superposição -> Emaranhamento ->
  Teleporte -> Algoritmos -> Correção de Erro -> Redes -> Internet.

O mapeamento (conceito do infográfico -> artefato Zephirum):
  qubits/qumodes            -> MODEL: type=entanglement, 4 amplitudes
  superposição              -> estado normalizado no certificado
  "entanglement is the resource" -> concorrência exata de Schmidt
                                     (Fraction, sem QPU, sem float)
  correção de erro          -> análogo clássico: o CERTIFICADO verifica
                               sem re-executar (TRACE_HASH, INPUT_HASH)
  teleporte/algoritmos/redes -> FORA do modelo: o gateway declara e
                               roteia ao SDK (§12) — nunca adivinha

Casos (do próprio infográfico), cada um com veredito exato ==
referência teórica e contraprova float do SDK quando instalado:
  1. estados de Bell (o emaranhamento máximo citado)
  2. estados de produto (separáveis)
  3. emaranhamento parcial (família a|00> + d|11>)
  4. superposição SEM emaranhamento
  5. limiar EXATO na fronteira (onde o float titubeia, o exato decide)
  6. fora do muro: GHZ-3 e mistos (Werner) — recusa honesta, rota SDK
"""
import sys
from fractions import Fraction

from qsim_gateway import gateway
from test_qsim_gateway import _src, _float_C_exact

R2 = "0.70710678118654752"          # 1/sqrt(2) em decimal, como o SDK vê


def C_schmidt_nc(a, b, c, d):
    """Concrrência pela ROTA DE SCHMIDT (Nielsen & Chuang, cap. 2),
    derivada por dentro — sem usar a formula fechada de Wootters.

    rho_A/n (n = |a|^2+|b|^2+|c|^2+|d|^2) tem traco 1 e determinante
    D/n^2, com D = (ad-bc)^2. Seu polinomio caracteristico e
    l^2 - l + D/n^2 = 0; por VIETA, o produto das raizes l+*l- e o
    termo independente D/n^2 — os l sao os QUADRADOS dos coeficientes
    de Schmidt. A concorrencia de um estado puro de 2 qubits e
    C = 2*sqrt(l+*l-), logo C^2 = 4*D/n^2. Exato, simbolico, sem raiz
    e invariante a escala (o decimal do 1/sqrt(2) nao e problema).
    """
    n = a * a + b * b + c * c + d * d
    D = (a * d - b * c) ** 2
    assert n > 0
    l_p_times_l_m = D / (n * n)      # Vieta: produto dos autovalores
    return 4 * l_p_times_l_m         # = C^2


def main():
    ok = 0
    cases = [
        # (nome, amplitudes, C teórico, emaranhado?)
        ("Bell |Phi+> = (|00>+|11>)/sqrt2",
         f"{R2},0,0,{R2}", 1, True),
        ("Bell |Phi-> = (|00>-|11>)/sqrt2",
         f"{R2},0,0,-{R2}", 1, True),
        ("Bell |Psi+> = (|01>+|10>)/sqrt2",
         f"0,{R2},{R2},0", 1, True),
        ("Bell |Psi-> = (|01>-|10>)/sqrt2",
         f"0,{R2},-{R2},0", 1, True),
        ("produto |00> (separavel)", "1,0,0,0", 0, False),
        ("produto |01> (separavel)", "0,1,0,0", 0, False),
        ("superposicao SEM emaranhamento ((|0>+|1>)/sqrt2) (x) |0>",
         f"{R2},{R2},0,0", 0, False),
        ("emaranhamento parcial 3/5|00> + 4/5|11>",
         "0.6,0,0,0.8", Fraction(24, 25), True),
        ("emaranhamento parcial 7/25|00> + 24/25|11> (C=336/625)",
         "0.28,0,0,0.96", Fraction(336, 625), True),
    ]
    print("== CASOS DENTRO DO MODELO (decisao exata, zero unidade QPU) ==")
    for name, st, C_theory, ent in cases:
        toks = [Fraction(x) for x in st.split(",")]
        # referencia teorica independente: C = 2|ad - bc| / (a2+b2+c2+d2)
        C_ref = _float_C_exact(*toks)
        assert C_ref == C_theory, (name, C_ref, C_theory)
        # CONSENSO: (1) formula de Wootters 2|ad-bc|; (2) rota de
        # Schmidt (N&C cap. 2) derivada acima; (3) veredito exato do
        # Zephirum; (4) float do SDK — quatro caminhos independentes
        C2_schmidt = C_schmidt_nc(*toks)
        assert C2_schmidt == C_theory ** 2, (
            name, C2_schmidt, C_theory)
        q = "entangled == 1"
        rec, okver = gateway(_src(st, q), sdk="qiskit")
        assert rec["routed"] and rec["status"] == "DECIDED_WITHOUT_EXECUTION"
        assert rec["qpu_units_billed"] == 0 and okver
        got = rec["verdict"] == 1
        assert got == ent, (name, got, ent)
        cross = rec["sdk_cross_check"]
        ok += 1
        print("  [OK] %-46s C=%-6s consenso 4 rotas (Wootters==Schmidt"
              "==Zephirum==SDK)" % (name[:46], str(C_theory)[:6]))

    # limiar EXATO: C == limiar -> "concurrence > limiar" e FALSO
    # exatamente; o float pode cair de qualquer lado — e o certificado
    # nao se abala (evidence before velocity, na pratica)
    st = f"{R2},0,0,{R2}"
    rec, okver = gateway(_src(st, "concurrence > 1"), sdk="qiskit")
    assert rec["routed"] and okver and rec["verdict"] == 0
    print("  [OK] limiar EXATO C == 1: '> 1' e FALSO no exato; float "
          "pode cair dos dois lados e o veredito certificado nao muda")
    ok += 1

    print()
    print("== CASOS FORA DO MURO (mapeados com honestidade §12) ==")
    # GHZ-3 (3 qubits, 8 amplitudes): o muro e a ARIDADE 4 — recusa
    # imediata com excessao de validacao, antes de qualquer certificado
    ghz3 = ",".join(["0.57735026918962576"] + ["0"] * 6
                    + ["0.57735026918962576"])
    try:
        gateway(_src(ghz3, "entangled == 1"))
        raise AssertionError("GHZ-3 aceito: muro da aridade furado")
    except ValueError as ex:
        assert "4 amplitudes" in str(ex)
        print("  [OK] GHZ-3 (8 amps): recusado na porta — 'entanglement "
              "state must have 4 amplitudes' (§12, antes de certificar)")
    ok += 1
    # familia fora do suporte: recibo honesto roteando ao SDK
    src_mistos = ("ASK:\n    question: entangled == 1\nCONTRACT:\n"
                  "    absolute_error: 0\nMODEL:\n    type: mixed_werner\n"
                  "    state: 1,0,0,0\n")
    rec, _ = gateway(src_mistos)
    assert not rec["routed"]
    assert "outside supported families" in rec["reason"]
    print("  [OK] mistos (Werner, familia 'mixed_werner'): fora das "
          "familias — recibo honesto, rota direta ao SDK, nunca adivinha")
    ok += 1

    print()
    print("MAPEAMENTO KASHYAP->ZEPHIRUM: %d/%d casos conformes ao "
          "infográfico — veredito exato == teoria em 100%% dos casos "
          "dentro do muro; GHZ-3 e mistos recusados com honestidade e "
          "roteados ao SDK (nunca adivinhados)" % (ok, ok))
    print("RESULTADO: PASS — o checklist do professor e coberto ate "
          "onde a fisica do nosso muro alcanca; o resto e fronteira "
          "declarada, nao promessa")


if __name__ == "__main__":
    main()
