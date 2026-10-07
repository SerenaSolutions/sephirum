# Kit de Endosso arXiv — ZEPHIRUM

*Preparado 2026-10-07. Objetivo: endosso de um cientista com conta
arXiv ativa e publicação recente em cs.LO ou cs.PL para a primeira
submissão do paper.*

## Regra honesta (lida antes de tudo)

O sistema de endosso do arXiv é amarrado a CONTA HUMANA com publicações
recentes na categoria. Uma IA (Claude/GPT/etc.) pode REVISAR o paper e
ajudar a preparação, mas não pode assinar o endosso — apresentar IA
como endossante seria fabricar credencial e queimaria a submissão. O
papel da IA aqui é: revisão técnica pré-submissão + este kit pronto.

## O que já está pronto

1. Fonte LaTeX: `docs/paper/arxiv/main.tex` (arXiv compila sozinho).
2. Pacote: `zephirum_arxiv_v1.tar.gz`.
3. Abstract pronto (bloco `\begin{abstract}` do main.tex).
4. Repositório público com TODOS os números reproduzíveis:
   `github.com/SerenaSolutions/zephirum` (conformidade executável:
   `python3 prototype/conformance_v03.py` → 11 batteries PASS).

## Roteiro para conseguir o endosso (o dono executa)

1. **Perfil do endossante ideal:** pesquisador/a em verificação de
   programas, lógica aplicada ou linguagens — ex., autores de trabalhos
   que o paper CITA honestamente (program specialization, proof-
   carrying code, certified computation, query optimization) ou
   docentes de PL/lógica de universidades brasileiras (USP, Unicamp,
   UFRJ, UFMG) que publiquem em cs.LO/cs.PL no arXiv.
2. **Abordagem:** e-mail curto (modelo abaixo) com o pitch de uma
   página + link do repositório. Oferecer rodar a conformidade na
   máquina deles: a reprodutibilidade É o argumento.
3. **O que pedir:** "endorsement para submissão em cs.LO" — o
   endossante recebe um link do arXiv quando você inicia a submissão
   com o e-mail dele indicado como endossante.
4. **Plano B sem endosso:** Zenodo (DOI imediato, sem endosso) — já
   recomendado no `docs/INPI_REGISTRO.md` para selar anterioridade.
   O paper pode IR ao Zenodo primeiro e ao arXiv depois.

## Pitch de uma página (para anexar ou colar)

O pitch está no próprio paper (Abstract + §1). Versão PT: "O ZEPHIRUM
inverte o pipeline de computação: prova antes de executar. Dada uma
pergunta sobre uma computação (soma excede threshold? estado está
emaranhado?), o compilador procura PROVAR que não é preciso computar,
por uma escada de eliminação com custo crescente; o que sobra executa
com certificado verificável por um verificador independente —
re-implementado em C puro e transpilado para Python/C/Java/C#/Qiskit/
Cirq. ZERO respostas erradas em 500.000 problemas; 76,5% da computação
exigida eliminada por certificado; UNKNOWN é cidadão de primeira
classe. Todos os números reproduzem com um comando."

## Modelo de e-mail (EN)

Subject: Endorsement request — Zephirum, a certified necessity compiler (cs.LO)

Dear Prof. [Name],

I am submitting a technical report to cs.LO and, as a first-time
arXiv author in the category, I need an endorsement. The work is
Zephirum: a question-first compiler with an elimination ladder and
trivalent decision logic (0/1/UNKNOWN) that answers questions about
computations before executing them; every decision ships with a
certificate re-derived by an independent verifier, re-implemented in
pure C and transpiled to four targets including Qiskit and Cirq.
Zero wrong answers on 500,000 randomized problems; 76.5% of demanded
computation eliminated by certificate; all numbers reproduce from a
public repository with a single command (conformance suite, 11
batteries). The paper claims a composition — not new constituent
techniques — and states its limitations explicitly.

Repository: https://github.com/SerenaSolutions/zephirum
One-page abstract and LaTeX source: attached.

Would you be willing to endorse the submission? I can share the full
reproducibility script beforehand if useful.

Respectfully,
[Nome do dono] — SerenaSolutions

## Checklist final do dono

- [ ] Conta arXiv criada e verificada
- [ ] Cientista contactado (modelo acima)
- [ ] Endosso recebido (link chega ao endossante pelo arXiv)
- [ ] Submissão com zephirum_arxiv_v1.tar.gz (cs.LO, cross-list cs.PL)
- [ ] Plano B executado em paralelo: DOI no Zenodo
