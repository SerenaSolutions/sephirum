# ZEPHIRUM — PADRÃO EXECUTÁVEL v0.3

**Estado:** normativo · **Data:** 2026-10-07 · **Moto:** *evidence before velocity*
**Conformidade:** uma implementação só pode afirmar "ZEPHIRUM v0.3" se passar
integralmente a suíte executável §6. O padrão NÃO é este documento — é a
suíte que o executa. Este documento é o mapa.

## §1 Escopo

ZEPHIRUM é um compilador de necessidade: dada uma pergunta sobre uma
computação, procura PROVAR que não é preciso computar — e só executa o
resíduo, com certificado verificável. Uma implementação v0.3 fornece:

1. lógica trivalente exata (verdadeiro, falso, **Z** = desconhecido honesto);
2. lexer/parser próprio da linguagem ZEPHIRUM (blocos ASK/CONTRACT/MODEL);
3. VM de bytecode ORÇAMENTADA conforme §4;
4. degraus de eliminação conforme §5;
5. certificado conforme §3;
6. PASS na suíte de conformidade §6 — executada
   por MAIS DE UMA linguagem: a referência Python e o verificador
   independente em C (`verifier_indep/zverify.c`) têm de concordar
   integralmente.

## §2 Núcleo normativo

- Aritmética EXATA (Fraction ou equivalente); `DIV` por zero é FALTA, não
  infinito.
- Desconhecimento é resposta legítima: `Z` nunca vira palpite.
- Determinismo total: mesma entrada → mesmo traço → mesmo veredito.

## §3 Certificado (campos normativos)

| Campo | Semântica |
|-------|-----------|
| `INPUT_HASH` | SHA-256 canônico dos dados consumidos; trocar a fonte muda o hash |
| `budget` | teto mecânico de unidades; exceder é `VMFault BUDGET EXCEEDED` |
| `units` | unidades EFETIVAMENTE gastas (contabilidade aberta) |
| `trace_hash` | SHA-256 do traço de opcodes executados |
| `answer` | veredito fixado por `CMPT` (ou recusa explícita) |

Certificado forjado = rejeitado (baterias G4/M3/B3 verificam o muro).

## §4 ISA da VM — custos NORMATIVOS por unidade

| Opcode | Custo | Lei |
|--------|-------|-----|
| `PUSH v`, `ADD`, `MUL`, `DIV`, `DUP`, `SWAP`, `POW`, `CMP`, `CMPT`, `MEDIAN`, `LABEL`, `JMPZ`, `LOOP n`, `ENDLOOP`, `CALL L`, `RET` | **0** | aritmética, stack e fluxo são grátis — o custo mora no DADO |
| `LOAD i`, `LOADSEQ` | **1** | unidade = dado consumido do mundo |

Muros mecânicos (§12, declarados): `STEP_LIMIT` 65536 passos totais;
`CALL_DEPTH` 64; `JMPZ`/`CALL` somente PARA FRENTE; laço só com contagem
LITERAL (laço infinito não é codificável); `stack` máx 1024;
`POW` exige expoente inteiro ≥ 0 e `POW_EXPONENT_LIMIT` 65536 —
aritmética gratuita não vira moenda infinita DENTRO de uma
instrução (além do muro: `VMFault` explícita).

## §5 Degraus de eliminação (a escada, v0.3)

| Família | Identidade | Unidades certificadas | Escada honesta |
|---------|-----------|----------------------|----------------|
| `gauss_series` | n(n+1)/2 | 2 | n ≤ 2: kernel EXECUTA |
| `geometric_inf` | a/(1−r), \|r\| < 1 | 2 | evidência mínima = (a, r); \|r\| ≥ 1 recusado em DOIS níveis (compilador e VM) |
| `arithmetic_mean` | (n+1)/2 | 1 | n = 1 é empate (1 = 1): kernel EXECUTA |
| `geometric_fin` | (r^(n+1)−1)/(r−1), r^0..r^n | 2 | n ≤ 1: kernel EXECUTA (1 < 2 e empate 2 = 2); r = 1: recusa (identidade n+1) |

A eliminação é medida em unidades certificadas (dado consumido), não em
ideologia: a bateria exige `units_boot < units_naive` nos casos eliminados
e gêmeos concordantes (boot == naive == juiz independente).

## §6 Suíte executável de conformidade (O padrão)

Executar `python3 prototype/conformance_v03.py`. PASS integral exige:

| Battery | O que prova |
|---------|-------------|
| `zephirum_boot.py` B1–B6 | degrau de Gauss na linguagem; orçamento-muro; DIV; determinismo |
| `zephirum_boot_b2.py` G1–G6, M1–M4 | geométrico infinito e média na linguagem; recusa de divergência; forjados; determinismo |
| `zephirum_boot_geo_fin.py` GF1–GF6 | geométrico finito na linguagem: DUP/SWAP/POW murados, concordância tripla com somatório independente |
| `stress_b2.py` ST1–ST6 | resistência: 10k casos, escala 10^9, falsificação, muros, exatidão 10^30, determinismo em massa |
| `test_vm.py` | ISA, muros e faltas da VM |
| `test_zephirum_lang.py` | equivalência linguagem ↔ núcleo (Fase 2) |
| `run_tests.py` | soundness do motor ZCA |
| `stress_test.py 5000` | escala com veredito verificável por semente |
| `verifier_indep/zverify.c` | verificador INDEPENDENTE em C: re-deriva vereditos, recalcula `INPUT_HASH` (SHA-256 próprio) e audita custos §5 — concordância Python<->C 520/520 (inclui 120 geofin), forjados 8/8 rejeitados |
| `zephirum_transpiler_multi.py` | UMA fonte ZEPHIRUM -> programas autônomos em Python, C, Java, C#, Qiskit e Cirq: veredito, `INPUT_HASH` e unidades idênticos (90/90 + 40 emaranhamentos); recusa §12 preservada em todos os alvos |
| `test_confront.py` CC1–CC5 | confronto medido clássico × quântico × exato: float64 mente na fronteira 2^53; SDKs com ruído/NaN declarados; Python×C exatos 120/120; ponte qiskit+cirq 30/30 com zero QPU |
| `verifier_indep/zvm.c` + `test_vm_c.py` | máquina virtual ORÇADA em C puro: 150 execuções cruzadas (boot+naive de 4 famílias + ISA inteira) com ANSWER, UNITS e TRACE_HASH idênticos byte a byte; 54 faltas espelhadas |
| `verifier_indep/zref.c` + `test_ref_c.py` | motor de referência em C puro: 200 fontes ZEPHIRUM decididas direto da fonte (5 famílias), sem Python em execução; muros §12 declarados e auditados |

## §7 Versionamento

- MAIOR: quebra de certificado ou de ISA; MENOR: degrau novo (B-fatias);
  PATCH: bateria/bug sem mudança semântica.
- Cada versão do padrão declara suas §12 na tabela de limitações.
- v0.3 + fatia geofin (2026-10-07, v0.8.1): ISA `DUP`/`SWAP`/`POW` +
  família `geometric_fin` — emenda aditiva, nenhum certificado existente
  é quebrado.
- v0.3 + fatia zvm (2026-10-07): a VM orçada executando em C puro
  (`zvm`) — ANSWER/UNITS/TRACE_HASH idênticos à referência; emenda
  aditiva, nenhum certificado quebrado.
- v0.3 + fatias interop e motor C (2026-10-07): alvos qiskit/cirq no
  transpilador, bateria de confronto CC1–CC5 e `zref` (motor C puro) —
  emendas aditivas; o Python deixa de ser necessário para DECIDIR
  (permanece como juiz de conformidade, regime de precisão arbitrária
  e alvo de transpilação).

## §8 Limitações declaradas (§12)

- A VM é interpretada em Python — a DECISÃO vive na linguagem; a máquina,
  ainda não (B5 exige modelo de memória).
- O geométrico FINITO foi ENTREGUE (v0.8.1): `DUP`/`SWAP`/`POW` na ISA,
  (r^(n+1)−1)/(r−1) com 2 unidades certificadas. Segue declarado:
  expoente fracionário/negativo não é fechado em racionais — a
  máquina recusa (raiz é aproximação, e aproximação sem contrato é
  fabricação, §12).
- Lexer/parser em ZEPHIRUM (B3) exige strings/tokens como dados.
- SHA-256 em bytecode (B4) exige operações de bit.

O desconhecido é dito com Z. O impossível é dito com VMFault. O feito é
provado com bateria.
