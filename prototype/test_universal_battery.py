#!/usr/bin/env python3
"""UNIVERSAL EXACT FAMILY — every domain, closed-form checks (owner
directive 2026-10-09: 'put those tests inside the OS and the language').
Each verdict is verified against known ground truth. Zero QPU."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nexa_core import parse_nexa, NCA

def run(src):
    return NCA(parse_nexa(src), name="universal.zeph").compile()

ok = 0
# 1. ASTRONOMY — Kepler III, Jupiter: a=5.204 AU -> T=11.862 yr
r = run("ASK:\n    question: period_years <= 12\nMODEL:\n    type: exact\n"
        "    check: kepler3\n    semi_major_axis_au: 5.204\n")
T = r["certificate"]["EVIDENCE"]["period_years"]
assert abs(T - 5.204 ** 1.5) < 1e-9 and r["answer"] is True; ok += 1
print("ASTRONOMIA  Kepler III: Jupiter a=5.204 -> T=%.3f yr (a^1.5, exato;"
      " observado 11.862 difere ~0.1%% pela massa nao nula de Jupiter)"
      % T)
# Earth: a=1 -> T=1
r = run("ASK:\n    question: period_years <= 1\nMODEL:\n    type: exact\n"
        "    check: kepler3\n    semi_major_axis_au: 1\n")
assert r["answer"] is True; ok += 1
print("ASTRONOMIA  Kepler III: Terra a=1 -> T=%.3f yr  [EXATO]" % T)

# 2. MATEMATICA — primality
for n, want in ((2, True), (7919, True), (7917, False), (999999937, True)):
    r = run("ASK:\n    question: is_prime == 1\nMODEL:\n    type: exact\n"
            "    check: primality\n    n: %d\n" % n)
    assert r["answer"] is want, n; ok += 1
print("MATEMATICA  Primalidade: 2, 7919, 999999937 primos; 7917 composto  [4/4]")

# 3. JURIDICO — prazo (contagem: exclui o comeco, inclui o vencimento;
# dias uteis; feriados declarados pelo operador)
r = run("ASK:\n    question: calendar_days_until_deadline <= 7\nMODEL:\n"
        "    type: exact\n    check: prazo_cpc\n    start: 2026-10-05\n"
        "    days: 5\n    dias_uteis: true\n")
dl = r["certificate"]["EVIDENCE"]["deadline"]
assert dl == "2026-10-12" and r["answer"] is True; ok += 1
r = run("ASK:\n    question: calendar_days_until_deadline <= 5\nMODEL:\n"
        "    type: exact\n    check: prazo_cpc\n    start: 2026-10-05\n"
        "    days: 5\n    dias_uteis: false\n")
dl = r["certificate"]["EVIDENCE"]["deadline"]
assert dl == "2026-10-10" and r["answer"] is True; ok += 1
print("JURIDICO  Prazo: 5 dias uteis de seg -> %s; corridos -> %s  [EXATOS]"
      % ("2026-10-12", dl))

# 4. MEDICINA (calculo) — dose = peso x taxa; decisao clinica fora do nucleo
r = run("ASK:\n    question: dose_mg <= 350\nMODEL:\n    type: exact\n"
        "    check: dose_mgkg\n    weight_kg: 70\n    mg_per_kg: 5\n")
assert abs(r["certificate"]["EVIDENCE"]["dose_mg"] - 350) < 1e-9 and r["answer"] is True
ok += 1
print("MEDICINA  Dose: 70 kg x 5 mg/kg = 350.0 mg  [EXATO; decisao clinica = profissional]")

# 5. AGRO — densidade de plantio e taxa por area
r = run("ASK:\n    question: plants_per_hectare <= 80000\nMODEL:\n"
        "    type: exact\n    check: agro_density\n"
        "    row_spacing_m: 0.5\n    plant_spacing_m: 0.25\n")
assert abs(r["certificate"]["EVIDENCE"]["plants_per_hectare"] - 80000) < 1e-9 and r["answer"] is True
ok += 1
r = run("ASK:\n    question: total <= 250\nMODEL:\n    type: exact\n"
        "    check: agro_rate\n    rate_per_ha: 50\n    hectares: 5\n")
assert r["answer"] is True; ok += 1
print("AGRO  Densidade: 0.5x0.25 m -> 80000 plantas/ha; 50 un/ha x 5 ha = 250  [EXATOS]")

# 6. ENGENHARIA — tensao e fator de seguranca
r = run("ASK:\n    question: safety_factor >= 1.5\nMODEL:\n    type: exact\n"
        "    check: stress_safety\n    force_n: 1000\n    area_m2: 0.01\n"
        "    limit_pa: 150000\n")
ev = r["certificate"]["EVIDENCE"]
assert abs(ev["stress_pa"] - 100000) < 1e-9 and abs(ev["safety_factor"] - 1.5) < 1e-9
ok += 1
print("ENGENHARIA  Estatica: tensao=100000 Pa, fs=1.5  [EXATO]")

# 7. QUIMICA — massa molar (IUPAC)
for f, want, thr in (("H2O", 18.015, 18.02), ("CaCO3", 100.086, 100.09),
                     ("C6H12O6", 180.156, 180.16)):
    r = run("ASK:\n    question: molar_mass_g_mol <= %.3f\nMODEL:\n"
            "    type: exact\n    check: molar_mass\n    formula: %s\n"
            % (thr, f))
    mm = r["certificate"]["EVIDENCE"]["molar_mass_g_mol"]
    assert abs(mm - want) < 0.005 and r["answer"] is True, (f, mm)
    ok += 1
    print("QUIMICA  Massa molar: %s = %.3f g/mol  [EXATO]" % (f, mm))

# 8. Section 12 — unknown check must refuse
try:
    run("ASK:\n    question: anything == 1\nMODEL:\n    type: exact\n"
        "    check: chess_engine\n")
    print("FALHA: check inexistente aceito"); sys.exit(1)
except ValueError as e:
    assert "Section 12" in str(e) or "unknown check" in str(e); ok += 1
    print("SECAO 12  check desconhecido RECUSADO — a linguagem nao adivinha  [OK]")

print("\nRESULTADO: PASS — bateria universal %d/%d; sete dominios, zero QPU" % (ok, ok))
