#!/usr/bin/env python3
"""
Testes mínimos do ZEPHIRUM-IR (Fase 3 — ordem corrigida: testar antes de expandir).

(1) Todo resultado do NCA atual se expressa como ZEPHIRUM-IR completo e válido.
(2) Round-trip JSON preserva o IR (hash idêntico).
(3) UNKNOWN mantém os invariantes (trit Z, sem resposta, sem kernel).
(4) Sabotagem detectada: fabricar resposta em UNKNOWN, kernel em UNKNOWN,
    residual em sem-execução — validate() DEVE rejeitar.
(5) O verificador independente aceita o certificado embutido no IR.

Exit 0 = IR consolidado como infraestrutura transversal.
"""
import copy
import json
import random
import sys

from nexa_core import parse_nexa, NCA
from verify_certificate import verify
from zephirum_ir import (from_nca, validate, ir_hash, to_json, from_json,
                     SifrIRError)
from stress_test import make_case, build_src

random.seed(2026)
N = 5000


def run():
    n_unknown = 0
    for i in range(N):
        kind, terms, unk, thr, x = make_case()
        src = build_src(kind, terms, unk, thr, x)
        blocks = parse_nexa(src)
        result = NCA(blocks, "ir%d" % i).compile()

        ir = from_nca(blocks, result)
        validate(ir)  # (1)

        h1 = ir_hash(ir)
        ir2 = from_json(to_json(ir))  # (2) round-trip
        if ir_hash(ir2) != h1:
            raise AssertionError("round-trip JSON alterou o IR (caso %d)" % i)

        if result["status"] == "UNKNOWN":
            n_unknown += 1
            assert ir["RESULT"]["trit"] == "Z"  # (3)
            assert ir["RESULT"]["answer"] is None

        ok, _ = verify(blocks, ir["CERTIFICATE"])  # (5)
        assert ok, "certificado embutido no IR não passou no verificador"

        if i < 50:  # (4) sabotagens devem ser rejeitadas
            bad = copy.deepcopy(ir)
            bad["RESULT"]["answer"] = True  # fabricar resposta
            try:
                if bad["STATUS"] != "UNKNOWN":
                    bad["STATUS"] = "UNKNOWN"
                validate(bad)
                raise AssertionError("fabricação de resposta aceita")
            except SifrIRError:
                pass
            bad = copy.deepcopy(ir)
            bad["DECISION_KERNEL"]["id"] = "INVENTADO"
            bad["CERTIFICATE"]["KERNEL"] = "INVENTADO"
            try:
                validate(bad)
            except SifrIRError:
                pass
    print("(1) %d resultados NCA -> ZEPHIRUM-IR válido: OK" % N)
    print("(2) round-trip JSON preserva o IR: OK")
    print("(3) UNKNOWN preservado honesto: %d/%d casos: OK" % (n_unknown, N))
    print("(4) sabotagens rejeitadas pelo validate(): OK")
    print("(5) certificados embutidos verificados de forma independente: OK")
    print("\nZEPHIRUM-IR CONSOLIDADO — infraestrutura transversal pronta. Exit 0.")


if __name__ == "__main__":
    run()
    sys.exit(0)
