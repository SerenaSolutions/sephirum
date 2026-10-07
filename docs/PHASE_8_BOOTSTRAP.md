# FASE 8 — BOOTSTRAP: o kernel na própria linguagem (v0.8.0)

> "Todo self-hosting começa assim: um núcleo pequeno que se sustenta."
> Precedente (nível C): Hart & Levin, 1962 — o primeiro compilador Lisp
> escrito em Lisp, compilado por um interpretador hospedeiro.

## O que é bootstrap aqui

O caminho que fez Python, C, Go e Rust virarem padrão tem um degrau comum:
a linguagem passa a sustentar a si mesma. O ZEPHIRUM entra nesse caminho
da forma honesta: **a lógica de eliminação do kernel, escrita NA própria
linguagem, executada pela própria VM orçamentada.**

## Fatia 1 (entregue nesta versão): o degrau de Gauss na linguagem

A pergunta `sum(1..n) > T` pode ser respondida de dois jeitos na VM:

- **NAIVE** — o mundo sem escada: carrega 1..n termo a termo.
  Custo: **n unidades certificadas**.
- **BOOT** — a identidade de Gauss `n(n+1)/2` expressa em bytecode
  ZEPHIRUM (`LOAD, LOAD, PUSH 1, ADD, MUL, PUSH 2, DIV, CMPT`).
  Custo: **2 unidades** (dois `LOAD` do mesmo dado — a ISA não tem DUP e
  cada leitura é contada; inflar ou esconder unidade seria desonesto).

O programa BOOT nasce de **fonte ZEPHIRUM** (`MODEL: type: gauss_series`),
passa pelo parser próprio da linguagem e é compilado para bytecode —
não é bytecode escrito à mão.

### Escada honesta
Para `n <= 2` o degrau de Gauss NÃO compensa: a execução é mais barata
(1 ou 2 unidades). O kernel escolhe o caminho barato de verdade —
eliminação não é ideologia, é aritmética de unidades.

## Evidência (nível C: bateria, não promessa)

- **B1** concordância tripla: 2.000 casos aleatórios (3 <= n <= 300),
  BOOT == NAIVE == juiz independente (Fraction em Python, caminho
  separado). 0 erros.
- **B2** eliminação medida: BOOT gasta 2 unidades sempre;
  **98,69%** das unidades do caminho ingênua evitadas de fato
  (302.468/306.468).
- **B3** orçamento é muro: programa forjado com 3ª leitura sob
  certificado de 2 => `VMFault BUDGET EXCEEDED`.
- **B4** `DIV` por zero => `VMFault` explícito — sem infinito na
  máquina (§12).
- **B5** determinismo: mesmo traço em toda execução; fonte trocada
  muda `INPUT_HASH` — certificado de fonte errada rejeitado.
- **B6** a decisão sai da FONTE ZEPHIRUM parseada pela linguagem
  (ex.: n=5, T=10 => 15 > 10 => True, com recibo).

Regressões do repositório inteiro: **17/17 PASS** após a adição do
opcode `DIV` (exato, Fraction; divisor zero recusado).

## Roadmap do bootstrap (declarado, não prometido)

| Etapa | Conteúdo | Estado |
|-------|----------|--------|
| B1 | degrau de Gauss na linguagem (esta fatia) | **CONCLUÍDA** |
| B2 | degraus geométrico (`geometric_inf`: a/(1-r), \|r\|<1) e de média (`arithmetic_mean`: (n+1)/2) em linguagem | **CONCLUÍDA** |

O geométrico FINITO (r^(n+1)-r)/(r-1) exige DUP/SWAP/POW na ISA — laço
com re-LOAD custa n unidades (eliminação falsa, §12). O degrau entregue é
o geométrico INFINITO: 2 unidades onde a truncação de 12 termos NUNCA
alcança a soma exata (bateria: cauda presente em 100/100 casos).

Resistência B2 (`stress_b2.py`, ST1-ST6): 10.000 casos geométricos com
0 erros; média decidida em 1 unidade até n = 10^9 (ingênuo não
materializado acima de 5.000 — eliminação pura); 4 ataques de
falsificação rejeitados; muros STEP_LIMIT/CALL_DEPTH/stack firmes;
racionais de 10^30 exatos; 500 casos x 2 execuções com traços idênticos.
| B3 | lexer/parser em ZEPHIRUM | exige strings/tokens como dados (ISA futura) |
| B4 | SHA-256 do certificado em bytecode | exige operações de bit (ISA futura) |
| B5 | VM escrita em ZEPHIRUM | exige modelo de memória; fronteira declarada |

## Limitações honestas (§12)

- A VM que executa o bytecode AINDA é interpretada em Python. O que
  mudou: a DECISÃO (o degrau de eliminação) agora vive na linguagem.
- Bootstrap completo (B5) não é promessa de roadmap: é fronteira
  declarada, com os pré-requisitos de ISA explícitos acima.
- A bateria cobre gauss_series + geometric_inf + arithmetic_mean (B2);
  o padrão executável v0.3 (docs/ZEPHIRUM_STANDARD_v0.3.md +
  conformance_v03.py) consolida as baterias como conformidade.
