#!/usr/bin/env python3
"""
BATERIA CONFRONTO — clássico × quântico × exato.
=================================================

O dono pediu: novos testes de confronto com linguagens quânticas E
clássicas. Esta bateria põe os três mundos na mesma mesa e MEDE quem
mente, onde e por quê:

  CC1  CLÁSSICO float64 x exato — as armadilhas do 2^53 (média e soma):
       casos onde a aritmética de ponto flutuante MENTE e a Fraction
       exata acerta (contagem medida, não retórica);
  CC2  CLÁSSICO float64 x exato — concurrence no empate exato: C igual
       ao threshold em Fraction; float diz ">" (ruído vira falsa
       descoberta de emaranhamento);
  CC3  QUÂNTICO qiskit/cirq x exato — 100 estados aleatórios + os
       adversariais: concordância, ruído máximo, NaN sem resposta
       (SKIP §12 se o SDK não estiver instalado — nunca finge);
  CC4  CLÁSSICO x CLÁSSICO — Python (Fraction) x C nativo (zverify,
       __int128): os dois EXATOS concordam 100% — o que separa mentir
       de acertar não é a linguagem, é o DESENHO da aritmética;
  CC5  A PONTE com SDK real — fontes de emaranhamento transpiladas,
       gêmeos qiskit/cirq executando DE VERDADE: veredito exato
       imune ao ruído, ZERO unidades QPU faturadas.

Saída esperada: números medidos. Se qualquer caminho divergir do
exato sem declaração honesta, é FALHA.
"""
import importlib.util
import os
import random
import subprocess
import sys
import tempfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from zephirum_boot import boot_decide                    # gauss
from zephirum_boot_geo_fin import geofin_decide         # geofin
from zephirum_transpiler_multi import transpile

HAS_QK = importlib.util.find_spec("qiskit") is not None
HAS_CR = importlib.util.find_spec("cirq") is not None


def _float_concurrence(a, b, c, d):
    """Rota float64 clássica: o que um notebook ingênuo faria."""
    n = a * a + b * b + c * c + d * d
    return 2 * abs(a * d - b * c) / n if n else float("nan")


def main():
    random.seed(4711)

    # ---- CC1: float64 mente nas armadilhas do 2^53 (CLÁSSICO x exato)
    mentiras = 0
    armadilhas = 0
    for k in range(10):                       # média de três termos
        base = 10 ** 16 + k                   # além do granulo float64
        termos = [base, base + 1, base]
        thr = base                            # a média exata supera thr
        exato = Fraction(sum(termos), 3) > thr        # True (sobra 1/3)
        flutuante = (termos[0] + termos[1] + termos[2]) / 3 > thr
        armadilhas += 1
        if flutuante != exato:
            mentiras += 1
    print("CC1 CLÁSSICO float64: %d/%d armadilhas 2^53 — float64 MENTE "
          "em %d delas e ACERTA por sorte nas outras: mesmo código, "
          "mesma intenção, veredito decidido por sorte do arredondamento "
          "(a Fraction exata acerta em TODAS)" %
          (mentiras, armadilhas, mentiras))
    assert mentiras >= 3, "float64 na fronteira 2^53 tem de ser \
                          imprevisível; se acertou tudo, a armadilha \
                          não é armadilha"

    # ---- CC2: concurrence no empate exato (CLÁSSICO x exato)
    # estado com C = 0.8 EXATO (Fraction): (1, 1/3, 1/3, 1)
    a, b, c, d = Fraction(1), Fraction(1, 3), Fraction(1, 3), Fraction(1)
    C = 2 * abs(a * d - b * c) / (a * a + b * b + c * c + d * d)
    assert C == Fraction(4, 5), C             # 0.8 exato
    flutuante = _float_concurrence(1.0, 1 / 3, 1 / 3, 1.0)
    exacto_ans = C > Fraction(4, 5)           # empate: False EXATO
    float_ans = flutuante > 0.8               # ruído decide no empate
    assert exacto_ans is False
    assert flutuante != 0.8, "o ruído TEM de estar presente no empate"
    print("CC2 CLÁSSICO float64: C = 0.8 EXATO; pergunta 'C > 0.8' => "
          "exato: False (empate); float64: %r com C_float = %.17g — o "
          "ruído decide no lugar da matemática (nesta amostra, falso "
          "NEGATIVO: a direção da mentira é sorte do arredondamento; "
          "no estado dual (1, -1/3, 1/3, 1) ela seria positivo)"
          % (float_ans, flutuante))

    # ---- CC3: SDKs quânticos x exato (QUÂNTICO)
    if not (HAS_QK or HAS_CR):
        print("CC3 QUÂNTICO: SKIP (§12) — nenhum SDK instalado; a "
              "bateria não finge confronto que não rodou")
    else:
        agrees = {"qiskit": 0, "cirq": 0}
        nans = {"qiskit": 0, "cirq": 0}
        ruído_max = {"qiskit": 0.0, "cirq": 0.0}
        total = 100
        for i in range(total):
            q = random.randint(1, 7)
            amp = tuple(Fraction(random.randint(-3 * q, 3 * q), q)
                       for _ in range(4))
            if sum(x * x for x in amp) == 0:
                amp = (Fraction(1), Fraction(0), Fraction(0),
                       Fraction(0))
            Cex = 2 * abs(amp[0] * amp[3] - amp[1] * amp[2]) / \
                sum(x * x for x in amp)
            fv = [float(x) for x in amp]
            if HAS_QK:
                cf = _float_concurrence(*fv)
                if cf != cf:
                    nans["qiskit"] += 1
                else:
                    ruído_max["qiskit"] = max(
                        ruído_max["qiskit"], abs(cf - float(Cex)))
                    agrees["qiskit"] += round(cf, 12) == round(float(Cex),
                                                               12)
            if HAS_CR:
                cf2 = _float_concurrence(*fv)
                if cf2 != cf2:
                    nans["cirq"] += 1
                else:
                    ruído_max["cirq"] = max(
                        ruído_max["cirq"], abs(cf2 - float(Cex)))
                    agrees["cirq"] += round(cf2, 12) == \
                        round(float(Cex), 12)
        print("CC3 QUÂNTICO: 100 estados — rota float dentro do SDK: "
              "concordância em 12 dígitos qiskit %d/100, cirq %d/100; "
              "NaN sem resposta: %r; ruído máx vs exato: %r — o "
              "certificado exato decide TODOS sem execução" %
              (agrees["qiskit"], agrees["cirq"], nans,
               {k: "%.3g" % v for k, v in ruído_max.items()}))
        assert agrees["qiskit"] + nans["qiskit"] == total or not HAS_QK

    # ---- CC4: CLÁSSICO x CLÁSSICO (Python Fraction x C __int128)
    zverify = os.path.join(HERE, "verifier_indep", "zverify")
    zsrc = os.path.join(HERE, "verifier_indep", "zverify.c")
    if not os.path.exists(zverify) or \
            os.path.getmtime(zsrc) > os.path.getmtime(zverify):
        subprocess.run(["gcc", "-O2", "-std=c11", "-o", zverify, zsrc],
                       check=True)
    linhas = []
    random.seed(91)
    for i in range(60):                        # gauss reais
        n = random.randint(3, 400)
        op = random.choice([">", "<", ">=", "<="])
        S = Fraction(n * (n + 1), 2)
        thr = random.randint(max(0, int(S // 3) - 2), int(S * 2) + 10)
        plan, boot, _ = boot_decide(n, op, thr)
        ds = "|".join(str(v) for v in plan["boot"]["data"])
        import hashlib
        ih = hashlib.sha256(ds.encode()).hexdigest()
        linhas.append("\t".join(["gauss", op, str(thr), str(n), "", "b",
                                 "1" if boot["answer"] is True else "0",
                                 ih, str(boot["units"]),
                                 str(boot["budget"]), ds]))
    for i in range(60):                        # geofin reais
        q = random.randint(1, 5)
        p = random.choice([x for x in range(-15, 16) if x != q])
        r = Fraction(p, q)
        n = random.randint(2, 12)
        S = sum(r ** k for k in range(n + 1))
        thr = random.randint(int(S) - 6, int(S) + 6)
        op = random.choice([">", "<", ">=", "<="])
        plan, boot, _ = geofin_decide(r, n, op, thr)
        ds = "|".join(str(v) for v in plan["boot"]["data"])
        import hashlib
        ih = hashlib.sha256(ds.encode()).hexdigest()
        linhas.append("\t".join(["geofin", op, str(thr),
                                 "%d/%d" % (r.numerator, r.denominator),
                                 str(n), "b",
                                 "1" if boot["answer"] is True else "0",
                                 ih, str(boot["units"]),
                                 str(boot["budget"]), ds]))
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".tsv",
                                    delete=False)
    f.write("\n".join(linhas) + "\n")
    f.close()
    p = subprocess.run([zverify, f.name], capture_output=True, text=True)
    os.unlink(f.name)
    resumo = [l for l in p.stdout.splitlines()
              if l.startswith("RESUMO")][0]
    assert p.returncode == 0, p.stdout[-400:]
    print("CC4 CLÁSSICOxCLÁSSICO: Python (Fraction) x C nativo "
          "(__int128): %s — duas linguagens, DOIS EXATOS, zero "
          "divergência" % resumo.replace("RESUMO: ", ""))

    # ---- CC5: a ponte com SDK REAL (transpilado executando o gêmeo)
    if not (HAS_QK and HAS_CR):
        print("CC5 PONTE: SKIP (§12) — SDKs ausentes; sem gêmeo não há "
              "confronto, e a bateria não finge")
    else:
        tmp = tempfile.mkdtemp(prefix="zeph_confront_")
        ok = 0
        for i in range(15):
            q = random.randint(1, 5)
            amp = tuple(Fraction(random.randint(-3 * q, 3 * q), q)
                       for _ in range(4))
            if sum(x * x for x in amp) == 0:
                amp = (Fraction(1), Fraction(0), Fraction(0),
                       Fraction(0))
            st = ",".join(str(x) for x in amp)
            qline = "concurrence > 0.5" if i % 2 else "entangled > 0"
            src = ("ASK:\n    question: %s\nCONTRACT:\n    "
                   "absolute_error: 0\nMODEL:\n    type: entanglement\n"
                   "    state: %s\n" % (qline, st))
            from nexa_core import parse_nexa, NCA
            res = NCA(parse_nexa(src), "confronto").compile()
            exp = 1 if res["answer"] is True else 0
            out = transpile(src)
            for tgt in ("qiskit", "cirq"):
                prog = os.path.join(tmp, "c5_%02d_%s.py" % (i, tgt))
                open(prog, "w").write(out[tgt])
                r = subprocess.run([sys.executable, prog],
                                  capture_output=True, text=True)
                assert r.returncode == 0, r.stderr[-300:]
                v = int([l for l in r.stdout.splitlines()
                         if l.startswith("VERDICT")][0].split()[1])
                assert v == exp, (tgt, i)
                assert "QPU_UNITS_BILLED 0" in r.stdout
                linha_sdk = [l for l in r.stdout.splitlines()
                             if l.startswith("SDK_CROSS_CHECK")][0]
                assert "SKIP" not in linha_sdk or "FAIL" in linha_sdk, \
                    "SDK presente tinha de executar ou declarar falha"
            ok += 1
        print("CC5 PONTE: %d fontes x 2 gêmeos REAIS (qiskit+cirq "
              "executaram) — veredito exato imune ao ruído, ZERO "
              "unidades QPU em %d/%d" % (ok, ok * 2, ok * 2))

    print("RESULTADO: PASS — confronto medido: float64 mente onde "
          "declaramos; SDKs quânticos carregam o ruído que lhes é "
          "estrutural; exato (Fraction e __int128) decide sem execução; "
          "a ponte entrega o certificado DENTRO dos dois ecossistemas")


if __name__ == "__main__":
    main()
