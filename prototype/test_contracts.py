#!/usr/bin/env python3
"""
TESTE DE CONTRATOS (Fase 4, fatia 2) — o contrato como máquina.
===============================================================

O contrato declarado não é decoração: cada cláusula é VERIFICADA.
Camadas que têm que disparar INDEPENDENTEMENTE:

  1. MOTOR (§12): contrato não-suportado = erro estrutural explícito.
  2. MÁQUINA DE CONTRATOS (simulator): violações sinalizadas.
  3. CHECKER: certificado com suposição mentirosa rejeitado.

Soundness-first: cada camada tem que pegar o que é dela.
"""
import sys

from nexa_core import NCA, parse_nexa
from verify_certificate import verify
from zephirum_simulator import ModelNotAvailable, check_contracts, compare

SRC_OK = ("ASK:\n    question: sum > 100\nCONTRACT:\n    absolute_error: 0\n"
          "MODEL:\n    type: threshold_sum\n    terms: 60, 30, 20, 5, 4, 3, 2, 1\n"
          "    assumption: terms_nonnegative")


def main():
    # (1) contrato válido: tudo verde, zero violações
    ok, v = check_contracts(parse_nexa(SRC_OK))
    assert ok and not v, v
    c = compare(parse_nexa(SRC_OK), "ok")
    assert c["contract_ok"] and c["verdict"] == "agreed" and c["cert_ok"]
    print("(1) contrato válido: máquina de contratos + kernel + checker OK")

    # (2) suposição mentirosa: o negativo escondido DEPOIS da testemunha
    # early-stop dispara com 150 > 100; a soma verdadeira é 150+30-500 < 0
    lying = SRC_OK.replace("terms: 60, 30, 20, 5, 4, 3, 2, 1",
                           "terms: 150, 30, -500")
    ok, v = check_contracts(parse_nexa(lying))
    assert not ok and any("negative" in x for x in v), v
    # o checker INDEPENDENTE também tem que rejeitar o certificado
    blocks = parse_nexa(lying)
    res = NCA(blocks, "lying").compile()          # motor pode emitir (não confia)
    cok, _ = verify(blocks, res["certificate"])
    assert cok is False, "checker aceitou suposição mentirosa!"
    print("(2) suposição mentirosa: máquina sinaliza + checker REJEITA")

    # (3) orçamento de erro não-exato: erro estrutural EXPLÍCITO no motor (§12)
    bad_budget = SRC_OK.replace("absolute_error: 0", "absolute_error: 0.5")
    try:
        NCA(parse_nexa(bad_budget), "bb").compile()
        raise AssertionError("motor aceitou contrato não-suportado em silêncio")
    except ValueError as e:
        assert "absolute_error" in str(e)
    ok, v = check_contracts(parse_nexa(bad_budget))
    assert not ok and any("error budget" in x for x in v), v
    print("(3) absolute_error != 0: motor falha explícito + máquina sinaliza")

    # (4) chave de contrato desconhecida: vocabulário estrito
    weird = SRC_OK + "\n    precision: ultra"
    weird = weird.replace("CONTRACT:\n    absolute_error: 0",
                          "CONTRACT:\n    absolute_error: 0")
    blocks_w = parse_nexa("ASK:\n    question: sum > 1\nCONTRACT:\n"
                          "    absolute_error: 0\n    quantum_guarantee: yes\n"
                          "MODEL:\n    type: threshold_sum\n    terms: 1, 2\n")
    try:
        NCA(blocks_w, "weird").compile()
        raise AssertionError("motor aceitou chave de contrato desconhecida")
    except ValueError as e:
        assert "contract keys" in str(e)
    ok, v = check_contracts(blocks_w)
    assert not ok and any("unknown contract key" in x for x in v), v
    print("(4) chave desconhecida: vocabulário estrito nas duas camadas")

    # (5) intervalo invertido no modelo: máquina de contratos sinaliza
    inv = ("ASK:\n    question: sum > 5\nMODEL:\n    type: threshold_sum\n"
           "    terms: 1, 2\n    unknown: x in 50..3")
    ok, v = check_contracts(parse_nexa(inv))
    assert not ok and any("inverted" in x.lower() for x in v), v
    try:
        NCA(parse_nexa(inv), "inv").compile()
        raise AssertionError("motor aceitou intervalo invertido")
    except ValueError as e:
        assert "inverted" in str(e)
    print("(5) intervalo invertido: motor §12 + máquina de contratos")

    # (6) contrato ausente = contrato exato (documentado): válido
    no_contract = ("ASK:\n    question: sum > 3\nMODEL:\n    type: threshold_sum\n"
                   "    terms: 1, 2, 3")
    ok, v = check_contracts(parse_nexa(no_contract))
    assert ok and not v, v
    c = compare(parse_nexa(no_contract), "nc")
    assert c["verdict"] == "agreed"
    print("(6) contrato ausente = exato (documentado): OK")

    print("RESULTADO: PASS — contrato é máquina em 3 camadas independentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
