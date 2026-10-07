# Submissão arXiv — ZEPHIRUM (passo a passo do dono)

Pacote pronto em `docs/paper/arxiv/`:

- `main.tex` — fonte LaTeX completa (arXiv exige a FONTE, não só o PDF)
- tar de submissão: `zephirum_arxiv_v1.tar.gz` (gerado abaixo)

## Como subir (o dono executa; exige conta arXiv)

1. Conta em arxiv.org (se não tiver, criar — só e-mail institucional ou
   de domínio próprio acelera o endosso).
2. Categoria: `cs.LO` (Lógica em Ciência da Computação) ou `cs.PL`
   (Linguagens de Programação). O conteúdo cabe nas duas; sugerimos
   `cs.LO` com cross-list `cs.PL`.
3. Primeira submissão em cs.LO/cs.PL exige **endosso** de um autor que
   já publique na categoria. Alternativa sem endosso (e a mais rápida
   para selar anterioridade com DOI): **Zenodo** — upload direto,
   DOI imediato, sem endosso. O roteiro de registro do projeto
   (docs/INPI_REGISTRO.md) já recomenda Zenodo como primeiro passo.
4. Upload do tar.gz em arxiv.org/submit → o arXiv compila o .tex
   sozinho (pdfLaTeX).
5. Abstract pronto para colar: o bloco `\begin{abstract}` do main.tex
   (é o texto já atualizado com verificador C, transpilador e
   self-hosting).

## O que o pacote contém de novo (v1, 2026-10-07)

Além do conteúdo do draft (docs/PAPER_zephirum.md), o main.tex inclui
parágrafos medidos:

- verificador independente em C: 520/520 honestos, 8/8 forjados;
- transpilador multi-alvo: 90/90 fontes idênticas em Python/C/Java/C#;
- self-hosting: Gauss (2 un.), geométrica infinita (2), média (1) e
  geométrica finita (r^(n+1)−1)/(r−1) com DUP/SWAP/POW (2 unidades,
  fatia v0.8.1);
- Q-SIM Gateway: emaranhamento decidido no portão, zero unidades QPU.

Todos os números saem das baterias que correm no repositório
(conformance_v03.py, PASS integral, 10 batteries) — nada é promessa.
