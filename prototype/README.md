# ZERA (ex-NEXA) — protótipo v0.1
"PROOF -> COMPUTE": compilador de necessidade com escada de eliminação, kernels de decisão,
certificados e verificador independente. Especificação fundadora: necessity_engine/MASTER_PROMPT_NEXUS_NEXA.md.

## Executar
python3 run_tests.py   # bateria de falsificação (S19/S23); exit 0 = soundness mantida

## Arquivos
- nexa_core.py    — parser NEXA/ZERA, IR, motor NCA/ZCA (degraus: simplificação, redução, limite, analítico, clássico), ledger, certificados
- nexa_checker.py — verificador independente (re-deriva da fonte; métodos distintos quando possível; rejeita certificados forjados)
- run_tests.py    — casos A–E + I/J/F/G/H; ataque de soundness com 3 certificados adulterados

## Escopo honesto
Famílias controladas: soma com limiar, média parcial com limites, determinante triangular,
série geométrica, dobragem constante, mediana (não-eliminável), UNKNOWN. Sem quantum real,
sem GPU/HPC/QPU ainda (backends progressivos previstos no spec §22).
