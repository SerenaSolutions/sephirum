# PHASE 4 — SIMULATOR: o gêmeo adversarial

Data: 2026-10-07 · Fase 4, fatia 1. Especificação do pilar em
`ZEPHIRUM_ARCHITECTURE.md` (validação de kernels, original × residual,
contratos, benchmarks/falsificação, múltiplos modelos computacionais).

## O que é

O simulator EXECUTA a computação completa que o NCA tentou eliminar —
de propósito, como instrumento de prova. Caminho aritmético
INDEPENDENTE do motor e do verificador:

| família | motor | simulator (plena) |
|---|---|---|
| threshold_sum | parada monotônica | Fraction, ordem reversa, sem early-stop |
| mean_partial | limites intervalares | extremos por Fraction de denominador |
| triangular_det | produto de diagonal | expansão de Laplace (cofatores) |
| geometric_series | forma fechada | loop ingênuo |
| raw_data | mediana clássica | ordenação plena |
| expression | AST restrito (safe_eval) | eval direto |
| entanglement | Schmidt exato (Fraction) | float64 numérico |

## compare()

Compila (kernel), verifica o certificado, executa a plena e compara.
Vereditos: `agreed` / `unknown_validated` / `MISMATCH`. Contabiliza
unidades plenas vs residual (original × residual).

## falsify(N) — hipóteses medidas

- H1 kernel == plena: 20.000 casos, **0 MISMATCH** (18.725 agreed +
  1.275 UNKNOWN validados)
- H2 eliminação desnecessária: 136.130 unidades evitadas foram
  executadas mesmo assim; a resposta não mudou em nenhuma
- H3 contabilidade residual coerente: required <= unidades plenas
- H4 UNKNOWN honesto: toda Z veio de execução plena subdeterminada
  (extremos divergem)
- H5 modelos computacionais: float64 erraria na armadilha 1e16
  (média de 10^16, 10^16+1, 10^16 > 10^16 dá False no float; o
  modelo exato dá True) — evidência de por que a aritmética é exata

## Limitações (declaradas)

1. O simulator cobre as famílias formais do motor; não simula
   dispositivos quânticos — 'entanglement' é simulado em float64
   clássico (Schmidt numérico), não em QPU.
2. GPU/HPC como modelos computacionais: não implementados nesta fatia
   (a infraestrutura de modelos múltiplos existe; os backends não).
3. O simulator é instrumento de prova, NÃO é o Runtime (não despacha
   nada para produção).

## Fatia 2 (2026-10-07): contratos como máquinas + modelos múltiplos

**Contrato como máquina de decisão** — cada cláusula declarada é
VERIFICADA, em três camadas independentes (`test_contracts.py`, PASS):
1. MOTOR (§12): `absolute_error != 0` ou chave de contrato desconhecida
   = erro estrutural EXPLÍCITO (nunca aceito em silêncio);
2. `check_contracts()` no simulator: vocabulário estrito, orçamento de
   erro, suposições conferidas CONTRA OS DADOS (terms_nonnegative com
   termo negativo = violação sinalizada);
3. CHECKER: certificado cuja testemunha contraria a suposição declarada
   é REJEITADO (defesa com profundidade — o motor pode mentir; o
   verificador nunca confia).
Contrato ausente = contrato exato (documentado).

**Backend de modelos computacionais** — o MESMO problema por modelos
distintos (`simulate_full(blocks, model)`, `test_models.py`, PASS):
- `exact` (Fraction) e `float64` implementados: 10.000 casos na faixa
  comum concordam 100%; na zona 2^53+ o float64 erra onde o exato
  acerta (soma e média em 1e16 medidas) — a razão da aritmética exata,
  agora evidência medida, não promessa;
- `gpu`/`hpc`/`qpu` REGISTRADOS e não implementados: falham
  explicitamente (`ModelNotAvailable`), nunca fingem execução (§12).

## Veredito (fatias 1+2)

PASS — fatias 1+2 do pilar SIMULATOR (diferencial + contabilidade +
contratos como máquinas + backend de modelos múltiplos). Próximas
fatias: backends gpu/hpc/qpu de verdade; contratos não-exatos
(orçamento de erro > 0) como semântica intervalar formal.
