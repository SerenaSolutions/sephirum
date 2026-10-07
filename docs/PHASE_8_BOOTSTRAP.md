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

O geométrico FINITO foi entregue na fatia geofin (v0.8.1) com DUP/SWAP/POW
murados — ver acima. O degrau do B2 permanece o geométrico INFINITO: 2 unidades onde a truncação de 12 termos NUNCA
alcança a soma exata (bateria: cauda presente em 100/100 casos).

Resistência B2 (`stress_b2.py`, ST1-ST6): 10.000 casos geométricos com
0 erros; média decidida em 1 unidade até n = 10^9 (ingênuo não
materializado acima de 5.000 — eliminação pura); 4 ataques de
falsificação rejeitados; muros STEP_LIMIT/CALL_DEPTH/stack firmes;
racionais de 10^30 exatos; 500 casos x 2 execuções com traços idênticos.
| B3 | lexer/parser em ZEPHIRUM | exige strings/tokens como dados (ISA futura) |
| B4 | SHA-256 do certificado em bytecode | **CONCLUÍDA** (2026-10-07, fatia de bit: AND/OR/XOR/SHL/SHR/MOD/STORE/FETCH) |
| B5 | VM escrita em ZEPHIRUM | exige modelo de memória; fronteira declarada |

## FATIA geofin — o geométrico FINITO na linguagem (2026-10-07, v0.8.1)

A última exclusão declarada do B2 deixa de existir. `DUP`/`SWAP`/`POW`
entram na ISA (custo 0 — o custo mora no DADO) e a série geométrica
FINITA `r^0..r^n` é decidida por `(r^(n+1)−1)/(r−1)` em bytecode:
`LOAD r, DUP, LOAD n, PUSH 1, ADD, POW, PUSH -1, ADD, SWAP, PUSH -1,
ADD, DIV, CMPT` — 2 unidades certificadas. O DUP é o ponto da fatia:
a evidência é carregada UMA vez (r, n) e o segundo uso de r é
aritmética, não unidade.

Muros novos (§12): `POW` exige expoente inteiro ≥ 0 e limitado a
`POW_EXPONENT_LIMIT` 65536 — aritmética gratuita não vira moenda
infinita dentro de uma instrução. Expoente fracionário/negativo é
recusado (raiz não é fechada em racionais).

Escada honesta: n = 0 → o ingênuo é mais barato (1 < 2), EXECUTA;
n = 1 → empate (2 = 2), EXECUTA; n ≥ 2 → elimina (2 fixas vs n+1).
r = 1 → recusa explícita (a soma é identidade n+1; DIV por zero
nunca é caminho).

Evidência (bateria GF1–GF6, PASS):
- GF1: 120 casos, boot == naive == juiz (somatório INDEPENDENTE),
  0 erros — r em [−3,3]\{1} incluindo |r| > 1, n de 2 a 60;
- GF2: boot gasta 2 unidades sempre; 3.632 unidades evitadas nos
  120 casos; fronteiras n=0/n=1 EXECUTAM;
- GF3: terceira leitura além do certificado => BUDGET EXCEEDED;
- GF4: expoente −1, 3/2 e 10^9 => VMFault explícita; (3/2)^12
  decide certo com 0 unidades;
- GF5: r=1, n<0 e família trocada => recusa, nunca silêncio;
- GF6: mesma execução => mesmo trace_hash; adulteração responde.
- Verificador C estendido com a família `geofin` (produtos cruzados
  __int128, transborno declarado): 520/520 honestos, 8/8 forjados.
- Conformidade v0.3 integral: 13 batteries + escala, PASS.

## Limitações honestas (§12)

- A VM que executa o bytecode AINDA é interpretada em Python. O que
  mudou: a DECISÃO (o degrau de eliminação) agora vive na linguagem.
- Bootstrap completo (B5) permanece fronteira — mas a exclusão "operações de bit" acabou de cair: a fatia B4 estendeu a ISA com o domínio de bit murado (32 bits) e memória mínima (256 slots), e o SHA-256 do INPUT_HASH agora corre EM BYTECODE (ver MARCO B4). O que resta declarado: strings como dados (B3) e o modelo de memória completo (B5)
  declarada, com os pré-requisitos de ISA explícitos acima.
- A bateria cobre gauss_series + geometric_inf + arithmetic_mean (B2)
  + geometric_fin (geofin v0.8.1);
  o padrão executável v0.3 (docs/ZEPHIRUM_STANDARD_v0.3.md +
  conformance_v03.py) consolida as baterias como conformidade.


## MARCO ZREF — o motor de referência em C puro (2026-10-07)

`verifier_indep/zref.c`: lê a FONTE ZEPHIRUM (blocos ASK/CONTRACT/
MODEL) diretamente e decide com aritmética exata própria (__int128,
produtos cruzados, Schmidt sem raiz) nas cinco famílias: gauss,
média, geométrica infinita, geométrica finita e EMARANHAMENTO.
Recibo normativo: VERDICT/HASH(SHA-256 FIPS 180-4)/UNITS.

Bateria `verifier_indep/test_ref_c.py` (PASS): 200 fontes — veredito,
INPUT_HASH e unidades idênticos aos oráculos Python nas 5 famílias;
3 recusas estruturais e 2 OVERFLOW de muro auditados (o C declara o
muro — 2^53 inclusive — e nunca mente; a precisão arbitrária segue
na referência Python).

O que isto muda no caminho "excluir o Python": o padrão agora DECIDE,
CERTIFICA e RECUSA sem Python em execução. O Python permanece como
(1) bateria de conformidade (o juiz), (2) regime de precisão
arbitrária além dos muros e (3) um alvo de transpilação entre outros.


## MARCO ZVM — a máquina virtual orçada em C puro (2026-10-07)

`verifier_indep/zvm.c`: executa o bytecode da VM orçada com a MESMA
semântica da referência Python — unidades certificadas, muros §12
idênticos (STEP_LIMIT 65536, CALL_DEPTH 64, POW 65536, stack 1024) e
TRAÇO DETERMINÍSTICO: o TRACE_HASH é byte a byte igual.

Bateria `verifier_indep/test_vm_c.py` (PASS): 150 execuções cruzadas
(planos boot+naive de gauss/geo/média/geofin + 60 programas sintéticos
com a ISA inteira: JMPZ/CALL/LOOP/MEDIAN/POW/…), 54 faltas espelhadas
(orçamento, JMPZ para trás, DIV por zero, muro POW, opcode) e o muro C
de fração (10^12, reduzida em __int128) declarado com honestidade §12.

Com o zref (DECIDE) e o zvm (EXECUTA), o Zephirum cobre em C puro o
ciclo inteiro: decidir, certificar, recusar e executar. O Python resta
como juiz de conformidade e referência de precisão arbitrária — um
alvo entre outros, não mais uma dependência.


## MARCO B4 — o SHA-256 do certificado NA LINGUAGEM (2026-10-07)

Extensão aditiva da ISA (precedente DUP/SWAP/POW): `AND/OR/XOR`
(domínio de bit 32, murado §12), `SHL/SHR k` (literal 0..31, SHL que
escapa = FALTA), `MOD m` (inteiros, m>=1), `STORE/FETCH i` (256
slots — o começo honesto do modelo de memória). Tudo a custo 0, tudo
espelhado entre a VM Python e o zvm em C puro.

`zephirum_sha_lang.py`: o SHA-256 COMPLETO em bytecode — padding de um
bloco (16 LOAD = 16 unidades certificadas), agenda de mensagens em
slots, 64 rodadas de compressão unrolled, IV/K como PUSH, NOT via XOR
0xFFFFFFFF e ROTR via AND antes do SHL (o muro nunca é contornado,
é projetado para não ser atingido).

Bateria `test_hash_in_lang.py` (PASS): 25 mensagens hasheadas em
bytecode com digest == hashlib em 100%; tripla concordância VM Python
== zvm C == hashlib (digest, UNITS=16/caso e TRACE_HASH idênticos);
a 1ª rodada com recito == referência FIPS 180-4 derivada
independentemente; 4/4 faltas espelhadas. Declarado (§12): a
codificação bytes->palavras fica no hospedeiro (strings ainda não são
dados da linguagem) e a fatia cobre mensagens de um bloco (0..55
bytes) — multi-bloco é a mesma técnica, outra fatia.

Self-hosting agora: o certificado pode derivar o PRÓPRIO INPUT_HASH
na linguagem. Restam as fronteiras B3 (lexer/parser: strings/tokens)
e B5 (VM completa em Zephirum: modelo de memória completo).
