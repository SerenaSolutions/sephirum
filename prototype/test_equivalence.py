#!/usr/bin/env python3
"""
TESTE DE EQUIVALÊNCIA TRIPLA (Fase 3, §10).
===========================================

Para cada caso (>= 10.000):
  SIFR/ZEPHIRUM -> kernel NCA  ->  resultado
  kernel -> certificado -> VERIFICADOR INDEPENDENTE  ->  mesmo resultado
  kernel -> transpilador -> Python autônomo -> execução  ->  mesmo resultado

Os três têm que coincidir. O caminho transpilado executa o CÓDIGO GERADO
(auditável), não o motor. O caminho do verificador re-deriva a decisão
da fonte, sem confiar no certificado.
"""
import sys

from nexa_core import parse_nexa, NCA
from stress_test import make_case, build_src
from verify_certificate import verify
from zephirum_transpiler import transpile

N = 10000


def main():
    verified = 0
    for i in range(N):
        kind, terms, unk, thr, x = make_case()
        src = build_src(kind, terms, unk, thr, x)
        blocks = parse_nexa(src)
        res = NCA(blocks, "eq%05d" % i).compile()

        # perna 1: verificador independente aceita o certificado
        ok, reason = verify(blocks, res["certificate"])
        assert ok, "caso %d: certificado rejeitado: %s\n%s" % (i, reason, src)

        # perna 2: certificado declara exatamente o resultado do motor
        want = "Z" if res["status"] == "UNKNOWN" else res["answer"]
        assert res["certificate"]["ANSWER"] == res["answer"], src
        assert res["certificate"]["STATUS"] == res["status"], src

        # perna 3: código Python transpilado (autônomo) concorda
        code = transpile(blocks)
        ns = {}
        exec(compile(code, "<transpiled>", "exec"), ns)
        got = ns["answer"]()
        assert got == want, ("caso %d (%s): transpilado %r != motor %r\n%s"
                             % (i, kind, got, want, src))
        verified += 1

    print("(§10) equivalência tripla motor/certificado+verificador/transpilado: "
          "%d/%d OK" % (verified, N))
    print("RESULTADO: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
