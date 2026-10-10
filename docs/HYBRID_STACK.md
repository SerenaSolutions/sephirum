# A PILHA HÍBRIDA QUÂNTICO+IA E O PORTÃO ZEPHIRUM

Data: 2026-10-10 · Nível: A (números reproduzíveis) salvo indicação

## O contexto de mercado
A indústria converge para uma pilha híbrida padrão:
dados → camada clássica (CPU/GPU) → camada de IA/ML → QPU →
pós-processamento, com laço iterativo de otimização. TODAS as
linguagens e algoritmos têm essa pilha — ela é commodity, não
diferencial.

## O que o ZEPHIRUM acrescenta: a caixa 3.5
Entre a camada de IA e o QPU mora um PORTÃO DE ADMISSIBILIDADE com
certificado: antes de qualquer shot, o motor decide exatamente o que
precisa de QPU. Padrão QCNN como caso-livro (Cong 2019; McClean
2018; Huang-Kueng-Preskill 2022, nível B): entrada separável é
classicamente simulável POR CONSTRUÇÃO — desviada para a rota
clássica; entrada emaranhada é admitida; o indecidível é UNKNOWN,
nunca palpite.

## Números (bateria hybrid_stack_battery.py, 2026-10-10)
Carga: as 100 perguntas públicas da witness_battery (semente fixa,
verdade-terreno independente) como entradas candidatas de uma carga
de IA quântica:
- decisões exatas offline: 100/100, ZERO unidades de QPU no gate
- desviadas para a rota clássica (separáveis): 30 — nunca chegam ao QPU
- admitidas ao QPU (emaranhadas): 70
- divergência certificado vs verdade independente: 0
- eliminação no portão: 30,0%
- contrafactual DECLARADO (§12, não é medição): a 512 shots por
  pergunta na nuvem, as 30 desviadas economizariam 15.360 shots

## As três muralhas do guardião (frente paralela, 2026-10-10)
Status: implementado e bateria ZYGUARD 10/10 PASS REPORTADA pela
frente de desenvolvimento paralela; publicação dos artefatos neste
repositório pendente (§12: não publicamos o que não reproduzimos).
1. Portão lexical assinado: propósito declarado no texto do
   programa; classe proibida (armas, letalidade, vigilância,
   perseguição, fraude, falsificação, sabotagem) é recusada ANTES de
   qualquer computo — e a recusa é um certificado assinado que grava
   o propósito verbatim. Recuso auditável, não silêncio.
2. Pureza estrutural: a ZYQL não tem PRIMITIVO de execução — nenhum.
   Sem arquivo, rede ou atuador; injeção no campo de propósito é
   string inerte (provado por bateria).
3. Atribuição: certificado com SHA-256; pernas de hardware com
   assinatura ML-DSA-44 (FIPS 204).

Posição honesta (nível D, direção do autor): a muralha lexical é a
mais fraca — lista se contorna com sinônimo. A muralha real é a
ARQUITETURA: a ZYQL nasceu sem a capacidade de agir; nas linguagens
universais (C, Python, JS) o "não poder" é remendo parafusado por
fora; aqui é a fundação.

## Linguagem, algoritmo, sistema (terminologia oficial)
ZYQL = a LINGUAGEM (a forma de escrever: perguntas trivalentes
0/1/Z, dados declarados, contratos). O compilador de necessidade
(NCA + Decision Kernel) = o ALGORITMO (o procedimento que pega a
pergunta escrita e produz o certificado, executando zero QPU
quando nada precisa). ZEPHIRUM = o SISTEMA (a casa inteira:
linguagem + algoritmos + guardião). A receita, o português e a
cozinha.

## Auditoria das promessas "onde o quântico agrega valor"
- otimização complexa: o gate NÃO decide dureza de otimização hoje;
  admissibilidade para otimização = trabalho futuro (nível D)
- simulação científica: decidível para estados com simulação
  clássica trivial por construção (separáveis) — nível A
- representação de features / amostragem: sem veredito do gate hoje;
  qualquer alegação é hipótese (nível D)
A pergunta honesta não é "o que o quântico agrega", é "o que desta
carga NÃO precisa de quântico" — e essa pergunta ninguém mais faz.

## §12 deste documento
O contrafactual de shots é DECLARADO, não medido. A perna de QPU
desta bateria (testemunha das 70 admitidas) depende de credencial
IBM ativa no ambiente; pendente no dia da compilação. As três
muralhas são citadas por relatório da frente paralela até que os
artefatos sejam publicados e reproduzidos aqui.
