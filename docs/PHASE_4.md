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

## Veredito

PASS — fatia 1 do pilar SIMULATOR (diferencial + contabilidade +
modelos). Próximas fatias: contratos como máquinas de decisão
explícitas no simulator; backend de modelos múltiplos plugável.
