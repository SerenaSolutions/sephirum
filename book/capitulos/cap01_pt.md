# Capítulo 1 — O mundo executa antes de perguntar
*ZERUM — A Computação Antes da Execução | Parte I: A Pergunta*

## Nível 1 — Para qualquer leitor

Para saber se a porta da frente da sua casa está aberta, você tem duas opções: caminhar dez passos e olhar; ou contratar uma equipe para demolir a casa, examinar cada tijolo, reconstruir tudo e então declarar: "sim, estava aberta".

Ninguém escolheria a segunda opção. E, no entanto, é a segunda que escolhemos todos os dias na computação.

Lançamos supercomputadores sobre temporais inteiros para saber se choverá amanhã ao meio-dia numa praça específica. Somamos listas completas quando os três primeiros números já decidiram a resposta. Reservamos processadores quânticos para perguntas que uma identidade algébrica resolve em uma linha. Executamos primeiro. Perguntamos depois — se sobrar tempo.

Este livro nasce de uma pergunta que deveria vir antes de todas as outras:

**"Eu realmente preciso executar esta computação para responder à pergunta que fiz?"**

## Nível 2 — Para o cientista e o engenheiro

A computação existe para responder perguntas, mas organizamos o trabalho ao contrário: escolhemos um algoritmo, escrevemos um programa, executamos — e só então descobrimos o que a execução nos disse sobre a pergunta original.

Invertemos a ordem. Um problema não chega sozinho: chega com uma **pergunta** (o que eu quero saber), uma **tolerância** (qual erro é admissível), um **orçamento** (quanto posso gastar), **hipóteses** (o que posso assumir) e **restrições** (o que devo preservar). Chamamos esse conjunto de **contrato**.

Com o contrato em mãos, três perguntas guiam todo o livro:

1. Eu realmente preciso executar esta computação para responder à pergunta que fiz?
2. Se preciso computar, qual é a menor computação que consigo justificar?
3. Como provar que aquilo que foi eliminado realmente não era necessário?

## Nível 3 — Para o cientista da computação

Formalmente: dado um problema P, uma pergunta Q e um contrato C (tolerância ε, orçamento B, modelo de computação M), construímos um compilador que procura um **Decision Kernel** — um procedimento certificado suficiente para decidir Q sob C com a menor computação justificável disponível — e emite um de cinco estados explícitos:

- `DECIDED_WITHOUT_EXECUTION` — a pergunta foi respondida sem executar nada;
- `DECIDED_BY_REDUCTION` — a pergunta foi decidida eliminando parte substancial da computação;
- `RESIDUAL_COMPUTATION_REQUIRED` — apenas um resíduo da computação permanece necessário;
- `FULL_EXECUTION_REQUIRED` — nenhuma redução certificada foi encontrada; a execução completa é justificada dentro do modelo;
- `UNKNOWN` — o sistema não conseguiu provar nem necessidade nem desnecessidade.

O paradigma muda de `ALGORITHM → COMPUTE` para `PROOF → COMPUTE`. O restante do livro persegue essa inversão: primeiro as linhas de pesquisa que já existem (capítulo 5), depois as tentativas de destruir a hipótese (capítulo 6), e só então a arquitetura que sobreviveu.
