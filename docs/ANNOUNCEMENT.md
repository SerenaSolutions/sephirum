# ZERUM — Launch announcement

## English (GitHub / international audience)

Today I open-sourced ZERUM: a necessity compiler.

The current paradigm is: pick an algorithm, execute, interpret. ZERUM inverts it: ask first, prove next, compute last.

Given a problem and a question ("does the sum exceed the threshold? is the average above X?"), it tries to prove that no computation is needed at all, through an escalating ladder: identity, simplification, reduction, interval bounds, closed form. Only what remains gets executed — and every decision ships with a certificate verified by a module independent of the engine.

The numbers (reproducible, fixed seed, pure Python, zero dependencies):

- 500,000 randomized problems, **zero wrong answers**
- 500,000/500,000 certificates independently verified
- 20/20 deliberately forged certificates were rejected
- **76.5% of the demanded computation eliminated by proof**
- when it doesn't know, it says UNKNOWN instead of guessing (the numeral Z, zerum: the digit that is 0 and 1 at the same time)

Open source (MIT), with a trilingual book in production and the technical paper in this repository: **github.com/SerenaSolutions/zerum**

The name follows the same journey as zero itself: śūnya → ṣifr → zerum.

The thesis is simple: before asking machines to compute more, ask whether they need to compute at all.

---

## Português (LinkedIn)

Hoje tornei open source o ZERUM: um compilador de necessidade.

O paradigma atual é: escolher algoritmo, executar, interpretar. O ZERUM inverte: perguntar primeiro, provar depois, computar por último.

Dado um problema e uma pergunta ("a soma ultrapassa o limiar? a média excede X?"), ele tenta provar que não é preciso computar nada, por uma escada crescente: identidade, simplificação, redução, limites, forma fechada. Só executa o que sobrar — e cada decisão sai com certificado verificável por um módulo independente do motor.

Os números (reproduzíveis, semente fixa, Python puro, zero dependências):

- 500.000 problemas aleatórios, **zero respostas erradas**
- 500.000/500.000 certificados verificados de forma independente
- 20/20 certificados forjados deliberadamente foram rejeitados
- **76,5% da computação demandada eliminada por prova**
- quando não sabe, diz UNKNOWN em vez de inventar (o numeral Z, zerum: o dígito que é 0 e 1 ao mesmo tempo)

Open source (MIT), com livro trilíngue em produção e paper técnico no repositório: **github.com/SerenaSolutions/zerum**

O nome segue a mesma viagem do zero: śūnya → ṣifr → zerum.

A tese é simples: antes de pedir às máquinas que computem mais, pergunte se elas precisam computar.
