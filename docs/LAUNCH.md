# LAUNCH KIT — trazendo o ZEPHIRUM ao mundo real

Três veículos de lançamento, nesta ordem: (1) GitHub Release v1.0.0
(feito, automático via API), (2) arXiv (paper pronto, submissão requer a
conta do dono), (3) comunidade (Show HN + LinkedIn, rascunhos abaixo).

## 1. GitHub Release v1.0.0 (executado pelo agente)

Release pública com resumo de evidências, tags e recibo de verificação.
Feita via API com o token da organização.

## 2. Paper arXiv — `paper/main.tex`

Pronto para submissão. Caminho do dono:

1. Abrir https://arxiv.org/submit com a conta do dono (arXiv exige conta
   própria; o agente não pode submeter em nome de terceiros).
2. Preencher `[AUTHOR]` no main.tex com nome e afiliação reais.
3. Compilar no Overleaf (pdflatex) e enviar o PDF + fonte.
4. Categoria sugerida: quant-ph; secundário cs.PL.

Todo número do manuscrito vem dos recibos assinados no repositório;
nenhum valor é estimado. Regra AUŠRA preservada.

## 3. Show HN (rascunho, inglês, direto)

```
Show HN: ZEPHIRUM – a language that decides quantum questions before executing them

I built a language where you ask a question about a quantum computation
(ASK / CONTRACT / MODEL), and an exact classical kernel decides it FIRST —
with a trivalent verdict (1 / 0 / UNKNOWN) and a SHA-256 certificate anyone
can verify. The QPU never decides; it only witnesses.

What the receipts show (all public, all on IBM Heron hardware, free tier):
- 500,000 randomized problems: 0 wrong answers, 76.5% of computations
  eliminated by certificate alone
- 20/20 forged certificates rejected by independent verifiers
- Bell vs separable controls agreed with the exact verdict on 3 processors,
  with bootstrap CI95 excluding/containing zero in the right directions
- GHZ ladder 4→20 qubits: pole populations 95% → 40% as decoherence dilutes
  the routed chain, end-pair correlators stay high — verdicts were decided
  offline at zero QPU cost
- Overhead audit of real jobs: QPU active time is 0.04–1.6% of wall time;
  the queue dominates. Deciding first isn't an optimization, it's categorical.

Honest limitations: the exact kernel covers entanglement/separability and
stabilizer families so far; hardware runs are evidence, never the
certificate; no quantum-advantage claims.

Repo (language, grammar, receipts, QPU ledger, 20s demo):
https://github.com/SerenaSolutions/sephirum

Ask me anything — including the parts that don't work yet.
```

## 4. LinkedIn (rascunho, português, tom formal e técnico)

```
Decidir antes de executar.

Apresento o ZEPHIRUM: uma linguagem e um núcleo exato que respondem
perguntas sobre computações quânticas ANTES de qualquer execução — com
vereditos trivalentes (1 / 0 / DESCONHECIDO) e certificados SHA-256
verificáveis por qualquer terceiro. O QPU nunca decide; apenas testemunha.

Resultados medidos, com recibos públicos assinados:
— 500.000 problemas aleatorizados: zero respostas erradas; 76,5% das
computações eliminadas por certificado, sem executar nada.
— 20/20 certificados forjados rejeitados por verificadores independentes.
— Controles Bell e separável confirmados em três processadores IBM Heron
(fez, marrakesh, kingston), com intervalos de confiança bootstrap 95%.
— Escada GHZ de 4 a 20 qubits: vereditos exatos decididos offline a custo
zero de QPU; a evidência física dilui com a decoerência, como esperado.
— Auditoria de overhead em jobs reais: o QPU ativo consome 0,04%–1,6% do
tempo de parede; a fila domina. Decidir primeiro não é otimização — é
eficiência categórica.

Rigor antes de velocidade: hardware é evidência, nunca certificado.

Repositório, gramática, recibos e demonstração:
https://github.com/SerenaSolutions/sephirum
```

## O que exige a mão do dono

1. Submissão arXiv (conta pessoal; passo 2 acima).
2. Conta no Hacker News para postar o Show HN (o agente não publica em
nome de terceiros sem credencial).
3. Publicação no LinkedIn (aguardando autorização OAuth do conector,
quando o dono decidir).

Tudo o mais (release, paper, rascunhos, recibos) já está no mundo real.
