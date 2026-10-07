# SIFR — Arquitetura da Plataforma (v1.0, 2026-10-06)

*Correção arquitetural aceita: a SIFR não é uma DSL que transpila para Python.
A transpilação Python é um backend provisório do RUNTIME. A VM própria é
componente interno do RUNTIME — não a próxima camada conceitual.*

## Os QUATRO PILARES

```
                         SIFR
                   LANGUAGE
                       │
                       ▼
                   COMPILER
                       │
                 NCA / DECISION
                     KERNEL
                       │
              ┌────────┴────────┐
              ▼                 ▇▇
          CERTIFICATE         RESIDUAL
              │                 │
              └────────┬────────┘
                       ▼
                   SIMULATOR
                       │
                       ▼
                    RUNTIME
                       │
          ┌────────────┼────────────┐
          ▇            ▇            ▇
         CPU          GPU          HPC
                                    │
                              SIMULATOR/QPU
   (a VM própria vive DENTRO do bloco RUNTIME)
```

1. **LANGUAGE — SIFR.** A linguagem de programação própria: lexer, parser,
   gramática, semântica, REPL, tipos. SIFR ≠ Python; SIFR ≠ DSL hospedada.
2. **COMPILER — NCA.** O Necessity Compilation Algorithm: dado (P, Q, C, B),
   determinar *qual é a menor computação certificável necessária para
   responder Q sob C*, materializada no **Decision Kernel**.
3. **SIMULATOR.** Validação de kernels, comparação original × residual,
   verificação de contratos, benchmarks, falsificação de hipóteses,
   múltiplos modelos computacionais (CPU/GPU/HPC/clássico/quântico).
   Não é o Runtime.
4. **RUNTIME.** Executa SOMENTE o que sobreviveu à análise de necessidade.
   Despacha para CPU, GPU, HPC, Simulator, (futuro) QPU. A VM própria é
   um componente interno deste pilar.

O **SIFR-IR** é infraestrutura transversal aos pilares Compiler, Simulator
e Runtime — não é um quinto pilar.

## A inversão em relação a IBM/Qiskit

Mesma família de usabilidade (LANGUAGE → COMPILER → SIMULATOR → RUNTIME),
finalidade oposta:

```
Qiskit:  PROBLEMA → CIRCUITO → COMPILAÇÃO → EXECUÇÃO → RESULTADO
SIFR:    PROBLEMA → PERGUNTA → CONTRATO → NECESSITY ANALYSIS
                       → DECISION KERNEL → CERTIFICATE
                       → RESIDUAL → EXECUÇÃO
```

A pergunta central da SIFR: **"Eu realmente preciso executar esta computação
para responder à pergunta?"**

## Definição formal do NCA

**Entradas:**
- `P` — problema/modelo/programa (o bloco MODEL, a família computacional)
- `Q` — a pergunta (bloco ASK; alvo, operador de comparação, limiar)
- `C` — o contrato (bloco CONTRACT: tolerâncias, modelo de erro)
- `B` — o orçamento/restrições (bloco BUDGET/REQUIRE)

**Objetivo:** encontrar o par `(K, R)` tal que:

- `K` — **Decision Kernel**: o núcleo computacional certificado capaz de
  responder `Q` sob `C`;
- `R` — **Residual**: a menor parte que exige execução real;
- e maximizar `eliminado(P, R)` sob a restrição de soundness:
  **nenhuma resposta sem certificado verificável; nenhuma fabricação.**

**Escada de eliminação** (ordenada por custo de análise crescente):

```
IDENTIDADE → INVARIANTE → SIMPLIFICAÇÃO → REDUÇÃO → LIMITE
→ SOLUÇÃO ANALÍTICA → APROXIMAÇÃO CERTIFICADA → CLÁSSICO
→ PARALELO → SIMULAÇÃO → QUÂNTICO
```

O NCA sobe a escada enquanto o degrau for **aplicável e provável**; para no
primeiro degrau que decide. Se nenhum degrau decide sob as garantias
exigidas, o estado é `UNKNOWN` — que é um resultado honesto, não uma falha.

**Honestidade de contribuição:** as técnicas dos degraus existem na
literatura. A contribuição candidata está na COMPOSIÇÃO ARQUITETURAL —
transformar a necessidade computacional em objeto explícito do processo de
compilação, com certificado composto e rastreabilidade (elimination trace).

## Estados obrigatórios (invariantes)

| Estado | Significado | Regra inviolável |
|---|---|---|
| `DECIDED_WITHOUT_EXECUTION` | provado sem executar | certificado obrigatório |
| `DECIDED_BY_REDUCTION` | executado só o residual | certificado + trace |
| `RESIDUAL_COMPUTATION_REQUIRED` | o residual é o kernel | certificado |
| `FULL_EXECUTION_REQUIRED` | nada eliminável provado | justificativa registrada |
| `UNKNOWN` | conhecimento insuficiente | resposta `Z`; nunca vira necessidade |

Nunca transformar UNKNOWN em necessidade automaticamente. Nunca
transformar ausência de prova em prova de desnecessidade. Nunca fabricar
certificado.

## SIFR-IR — representação intermediária própria

Infraestrutura transversal (implementação: `prototype/sifr_ir.py`). Campos
obrigatórios do nível superior:

```
PROBLEM            família computacional e parâmetros (P)
QUESTION           alvo, operador, limiar (Q)
CONTRACT           tolerâncias (C)
ASSUMPTIONS        premissas sob as quais as provas valem
EVIDENCE           fatos e medidas que sustentam o kernel
DECISION_KERNEL    {id, rung, método, justificação, escopo}
ELIMINATION_TRACE  ladder percorrido, degrau a degrau
RESIDUAL           {unidades exigidas, especificação do que falta executar}
CERTIFICATE        o certificado verificável (assinado pelo input_hash)
RESOURCE           custos: análise, execução, verificação; backends
EXECUTION          NOT_REQUIRED | PENDING | DONE (+ backend)
RESULT             resposta final + trit (0/1/Z)
STATUS             um dos cinco estados
```

## Contratos entre pilares

**Compiler → Simulator:** entrega IR com `DECISION_KERNEL` e hipóteses;
o Simulator valida o kernel (original × residual, contrato, aproximações) e
devolve um **relatório de validação** — nunca altera certificado nem status.

**Compiler → Runtime:** entrega IR com `RESIDUAL` e `RESOURCE`; o Runtime
executa APENAS o residual, no backend declarado, e devolve o registro de
`EXECUTION` — nunca re-decide, nunca otimiza, nunca elimina nada.

**Runtime → Compiler:** o resultado da execução do residual preenche
`RESULT` e fecha o ciclo do certificado. O certificado continua verificável
pelo caminho independente (`nexa_checker`).

**Simulator vs Runtime:** o Simulator valida e compara (mundo da evidência);
o Runtime despacha e executa (mundo da operação). Não se confundem.

## Roadmap corrigida

| Fase | Entrega | Status |
|---|---|---|
| 0 | Conceito / pesquisa / anterioridade | concluída |
| 1 | Protótipo SIFR + IR + motor NCA inicial | concluída (500k casos) |
| 2 | Linguagem própria: lexer, parser, gramática, REPL, transpiler, fuzzing | **concluída** |
| 3 | **COMPILER CORE**: SIFR-IR consolidado, NCA formal, Decision Kernel, ladder, trace, certificados, residual | **atual** |
| 4 | SIMULATOR: execução de referência, validação de kernels, original × residual, benchmarks | futura |
| 5 | RUNTIME: scheduler, abstração de backend (CPU/GPU/HPC/Simulator) | futura |
| 6 | VM própria — construída DENTRO do Runtime | futura |

## O que NÃO fazer (permanente)

Não apagar lexer/parser; não transformar SIFR em Python; não tratar o
transpiler como produto final; não tratar VM como núcleo conceitual; não
criar quinto pilar; não assumir que quântico é sempre o destino; não
afirmar novidade sem verificação de anterioridade; não converter UNKNOWN em
necessidade; não confundir otimização tradicional com a proposta central.
