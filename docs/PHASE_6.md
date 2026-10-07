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
