#!/usr/bin/env python3
"""
WITNESS BATTERY — 100 perguntas de emaranhamento, 0 segundos de QPU.

A "prova viva": o núcleo de decisão certifica as 100 respostas offline
(DECIDED_WITHOUT_EXECUTION, 0 unidades de QPU); a bateria fica pronta
para o confronto adversarial na máquina real da IBM — que executa a
mesma pergunta só para FALSIFICAR o certificado, não para respondê-la.

Verdade-terreno INDEPENDENTE do motor: estado puro de 2 qubits
(a,b,c,d) é emaranhado sse ad - bc != 0 (posto de Schmidt 2),
criterio exato por Fraction. O motor decide por outro caminho
(Schmidt/determinante da matriz 2x2 — verificado por bateria própria).

Distribuição das 100 perguntas (semente fixa, reproduzível):
  25 produto puro (inclui base computacional, superposição, rank-1)
  25 emaranhado Schmidt (a,0,0,d)
  25 gerais (veredito misto pelo determinante exato)
  25 ARMADILHAS de fronteira (ad ~ bc, quase-separáveis, borda exata)

Saída: witness_battery/ (100 arquivos .zeph) + manifest JSON com
veredito do certificado, verdade independente, status e concurrence.
EXIT 1 se qualquer divergência entre certificado e verdade exata.
"""
import json
import random
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

RNG = random.Random(20261009)
OUT = Path(__file__).parent / "witness_battery"
PLUGIN = "zephirum-q"


def frac_str(f: Fraction) -> str:
    """Amplitude como decimal exato de ~16+ dígitos (o plugin parseia
    como Fraction exata — política §EXACT)."""
    dec = Fraction(f).limit_denominator(10 ** 6)
    x = dec.numerator / dec.denominator
    return format(x, ".17g")


def state_src(amps) -> str:
    return ("ASK:\n    question: entangled == 1\nCONTRACT:\n"
            "    absolute_error: 0\nMODEL:\n    type: entanglement\n"
            "    state: %s\n" % ",".join(frac_str(a) for a in amps))


def independent_truth(amps) -> int:
    """Posto de Schmidt via determinante exato — método != motor."""
    a, b, c, d = (Fraction(x) for x in amps)
    return 1 if (a * d - b * c) != 0 else 0


def battery():
    cases = []

    # 25 produto puro
    for i in range(25):
        if i < 4:  # base computacional
            amps = [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)][i]
            amps = [Fraction(x) for x in amps]
        elif i == 4:  # |++>
            amps = [Fraction(1, 2)] * 4
        else:         # rank-1: (a,b,0,0) ou (a,0,c,0)...
            a, b = Fraction(RNG.randint(1, 15), 16), Fraction(RNG.randint(1, 15), 16)
            if i % 2:
                amps = [a, b, Fraction(0), Fraction(0)]
            else:
                amps = [a, Fraction(0), b, Fraction(0)]
        cases.append(amps)

    # 25 emaranhado Schmidt (a,0,0,d)
    for i in range(25):
        a = Fraction(RNG.randint(1, 15), 16)
        d = Fraction(RNG.randint(1, 15), 16)
        cases.append([a, Fraction(0), Fraction(0), d])

    # 25 gerais
    for i in range(25):
        cases.append([Fraction(RNG.randint(-15, 15), 16) for _ in range(4)])

    # 25 ARMADILHAS de fronteira
    for i in range(25):
        # a = 1/16 garante que d = bc/a tenha decimal TERMINANTE
        # (bc/a = 16*bc); sem isso d pode ser não-terminante e a
        # serialização trunca, mudando a pergunta efetivamente feita
        # (achado da própria bateria em q085 — o motor acertou o
        # estado truncado; o erro era do gerador, não do motor).
        a = Fraction(1, 16)
        b = Fraction(RNG.randint(1, 15), 16)
        c = Fraction(RNG.randint(1, 15), 16)
        if i % 5 == 0:          # exatamente produto: d = bc/a
            d = b * c / a
        elif i % 5 == 1:        # quase-separável: bc/a ± 1/256
            d = b * c / a + Fraction(RNG.choice([1, -1]), 256)
        elif i % 5 == 2:        # termo minúsculo
            d = Fraction(RNG.choice([1, -1]), 256)
        elif i % 5 == 3:        # emaranhado máximo: (1,0,0,1)
            amps = [Fraction(1), Fraction(0), Fraction(0), Fraction(1)]
            cases.append(amps)
            continue
        else:                   # fase negativa: ad - bc < 0 (não-zero)
            d = -b * c / a + Fraction(1, 16)
        cases.append([a, b, c, d])

    return cases[:100]  # trava exata


def main():
    OUT.mkdir(exist_ok=True)
    cases = battery()
    assert len(cases) == 100, "esperado 100, obtidos %d" % len(cases)
    manifest, mismatch = [], 0
    qpu_total = 0
    for i, amps in enumerate(cases):
        name = "q%03d" % i
        src = state_src(amps)
        (OUT / (name + ".zeph")).write_text(src)
        r = subprocess.run([PLUGIN, str(OUT / (name + ".zeph")), "--json"],
                           capture_output=True, text=True)
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            print("!! %s: saída não-JSON do plugin" % name)
            mismatch += 1
            continue
        status = out.get("status", "NO_STATUS")
        verdict = out.get("verdict")
        billed = out.get("qpu_units_billed", 0) or 0
        qpu_total += billed
        # verdade sobre os decimais ESCRITOS no arquivo (a pergunta
        # que o motor realmente recebeu), nao sobre as fracoes internas
        # do gerador — fecha qualquer lacuna de serializacao
        written = (OUT / (name + ".zeph")).read_text().split("state: ")[1].strip()
        truth = independent_truth([Fraction(t) for t in written.split(",")])
        if status != "DECIDED_WITHOUT_EXECUTION" or verdict != truth:
            mismatch += 1
            print("!! %s: certificado=%s verdade=%s status=%s"
                  % (name, verdict, truth, status))
        manifest.append({
            "name": name, "amplitudes": [str(a) for a in amps],
            "independent_truth": truth, "cert_verdict": verdict,
            "status": status, "qpu_units_billed": billed,
            "concurrence_exact": out.get("concurrence_exact"),
        })

    ent = sum(1 for m in manifest if m["independent_truth"] == 1)
    prod = sum(1 for m in manifest if m["independent_truth"] == 0)
    ok = len(manifest) - mismatch
    json.dump({"total": len(manifest), "agreed": ok, "mismatch": mismatch,
               "entangled": ent, "product": prod,
               "qpu_units_billed_total": qpu_total,
               "seed": 20261009, "battery": manifest},
              open(OUT / "manifest.json", "w"), indent=1, ensure_ascii=False)
    print("WITNESS BATTERY: %d perguntas | %d emaranhadas, %d produto"
          % (len(manifest), ent, prod))
    print("certificado == verdade exata: %d/%d" % (ok, len(manifest)))
    print("unidades de QPU gastas para responder as 100: %d" % qpu_total)
    print("manifest: %s" % (OUT / "manifest.json"))
    sys.exit(1 if mismatch else 0)


if __name__ == "__main__":
    main()
