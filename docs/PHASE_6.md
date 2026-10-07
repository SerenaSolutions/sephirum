# PHASE 6 — VM própria (componente interno do RUNTIME)

Data: 2026-10-07 · Fase 6, fatia 1. A VM é componente INTERNO do pilar
RUNTIME (arquitetura §RUNTIME), não um quinto pilar.

## O que é

Uma máquina de bytecode mínima, determinística e ORÇAMENTADA
(`zephirum_vm.py`). O certificado autoriza N unidades de execução
residual; a VM é construída para não conseguir gastar mais:

  - unidade = dado consumido (LOAD/PUSH de valor de entrada);
  - LOAD além do orçamento => VMFault BUDGET EXCEEDED na hora — o
    programa forjado PARA na unidade autorizada;
  - aritmética exata (Fraction); ISA sem fluxo de controle nesta fatia
    (laços desdobrados em compile-time);
  - trace determinístico COM operando: trocar o índice de um LOAD
    (adulterar o dado acessado) muda o trace_hash.

## Compilação certificada -> bytecode

compile_program(blocks, res): testemunha de redução, residual de
oráculo (base certificada da EVIDÊNCIA — re-derivada pelo verificador
independente), soma plena. Zero-execução => programa vazio (HALT):
a resposta é o certificado.

## Resultados (test_vm.py, V1-V6, PASS)

- 4.072 residuais executados em bytecode: TODOS conferem com o
  certificado; contabilidade fechada (unidades == orçamento) em todos
- orçamento é lei: programa de 8 unidades com certificado de 3 => parou
  na 3ª (BUDGET EXCEEDED)
- determinismo: mesmo programa => mesmo trace_hash; um operando muda,
  hash muda
- 2.897 casos zero-execução na amostra (programa vazio)
- escopo honesto: mediana/determinante/emaranhado => VMNotEncodable
  explícito — nunca fallback silencioso

## Integração

Backend `vm` do Runtime: `zephirum run prog.zeph --backend vm`.
Família não codificável => RuntimeRefusal com o motivo.

## Limitações (declaradas)

1. Sem fluxo de controle: laços desdobrados (tamanho do programa
   proporcional ao laço);
2. Escopo: famílias de soma; mediana/det/emaranhado ficam nos
   backends analíticos até a próxima fatia;
3. Stack sem proteção de transações: falha no meio do programa não
   desfaz estado (programas desta fatia são lineares — sem efeito);
4. A VM é interpretada (Python); VM em processo isolado fica para
   junto do isolamento de backend do Runtime.

## Veredito

PASS — fatia 1 da VM: orçamento como lei de microexecução, bytecode
determinístico com fingerprint de execução.


## FATIA 2 — Fluxo de controle ORÇADO (2026-10-07, v0.6.1)

A VM deixa de ser linha reta. Nova ISA: LOADSEQ (consumo sequencial,
custo 1 unidade), CMP (comparação -> 0/1), LABEL, JMPZ (desvio
condicional), LOOP n / ENDLOOP (laço com contagem LITERAL).

Leis do fluxo de controle (soundness-first):
1. LAÇO SÓ COM CONTAGEM LITERAL — laço infinito não é codificável;
2. JMPZ SÓ PARA FRENTE — retroceder exige a estrutura LOOP
   (VMFault explícito em salto para trás ou label inexistente);
3. cada LOADSEQ consome 1 unidade do orçamento certificado — série de
   64 termos vira bytecode de 7 instruções que gasta exatamente
   64/64 unidades (V7);
4. MURO MECÂNICO DECLARADO (§12): STEP_LIMIT de 65.536 passos totais
   — laço forjado de aritmética PURA (que não consome dado) bate no
   muro de passos (V10); o que consome dado bate no BUDGET (V9). O
   orçamento é lei; o muro é parede.

Fronteira honesta do trace_hash (V12, declarada): o traço é impressão
digital da EXECUÇÃO (opcodes, operandos, padrão de acesso, fluxo) —
valor de DADO não está no traço. Quem protege o dado é o INPUT_HASH do
certificado: certificado de fonte trocada => REJECT na verificação.

Bateria V7-V12 (PASS):
- V7 laço: 64 termos => 7 instruções, 64/64 unidades, veredito ==
  referência exata (Fraction)
- V8 desvio: JMPZ frente-only, dois ramos corretos, caminhos
  distintos => trace_hash distinto
- V9 laço forjado: contagem inflada além do orçamento => BUDGET
  EXCEEDED no meio do laço
- V10 spin forjado: 1.000.000 de iterações sem consumo => STEP LIMIT
- V11 JMPZ para trás / label inexistente => VMFault explícito
- V12 determinismo: mesma execução => mesmo hash; contagem/operando
  adulterados => hash muda; valor de dado => INPUT_HASH responde

Limitações da fatia 2 (declaradas): sem chamada de sub-rotina (sem
return address); desvio só para frente; LOOP exige contagem em tempo
de compilação (não pode depender de dado); mediana/determinante/
emaranhado seguem VMNotEncodable.


## FATIA 3 — Famílias extras (2026-10-07, v0.6.2)

A última recusa honesta da VM vira cobertura explícita:

- MEDIANA (raw_data): codifica — sort clássico em bytecode. Opcode
  MEDIAN k (mediana exata dos k valores do topo, par = média das
  duas centrais em Fraction). m LOADs = m unidades certificadas.
  V13/V15: ímpar, par e fuzz de 200 casos, contabilidade fechada.
- EMARANHADO (entanglement): codifica como HALT de 1 instrução, 0/0
  unidades — a família é eliminada ANALITICAMENTE (Schmidt). A
  máquina não responde (answer=None); QUEM RESPONDE É O
  CERTIFICADO (V14). A tese do projeto demonstrada no bytecode.
- DETERMINANTE PLENO: recusa EXPLÍCITA com motivo (V6): a unidade
  certificada é o termo de expansão Laplace (n!), não o dado
  consumido (LOAD) — semânticas distintas. Rebaixar o teto
  orçamentário ou inflar o custo seria desonesto (§12). Det
  TRIANGULAR segue analítico (zero unidades, HALT).

Bateria V1-V15 completa (PASS). O que a VM NÃO faz segue declarado:
det pleno, sub-rotina (return address), LOOP com contagem dependente
de dado.


## FATIA 4 — Isolamento de processo (2026-10-07, v0.6.3)

A VM sai do processo do runtime e vira filho descartável:
`zephirum_isolated_runner.py` (o filho) + `zephirum_isolate.py` (as
portas) + backend `vm_isolated` no runtime e CLI.

MUROS aplicados ao filho: RLIMIT_CPU 5s (kernel), RLIMIT_AS 128 MB,
timeout de 10s no relógio do pai, cwd em diretório temporário vazio,
ambiente mínimo. Um crash — laço forjado, BUDGET EXCEEDED, STEP
LIMIT, falta de memória — morre no FILHO; o hospedeiro segue de pé e
entrega LIMPA (IsolationFault => RuntimeRefusal, nunca entrega suja).

DECLARAÇÃO HONESTA (§12): em Python puro não há isolamento de
sistema de arquivos nem de rede (sem seccomp/container aqui). Os
muros são processo + CPU + memória + tempo. Camada de container/jail
do SO é aditiva e fica documentada como recomendação de deploy.

Bateria V16-V21 (PASS): paridade isolado==em-processo (resposta,
unidades, trace_hash — 50 residuais); BUDGET/STEP LIMIT no filho com
motivo explícito; RLIMIT de memória derruba alocação de 192MB; muro
de tempo mata o dorminhoco; 142 residuais end-to-end no runtime com
veredito == cpu_exact e cross-check OK; det pleno => RuntimeRefusal.
