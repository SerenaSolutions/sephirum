# Varredura de Singularidade

> Renomeado 2026-10-07: ZERUM→**ZEPHIRUM**, SIFR→**ZEPHIRUM** (linguagem),
> SCA→**ZCA**. O texto abaixo usa os nomes atuais. — Dossiê de Anterioridade (2026-10-06)

**Objeto:** a composição ZEPHIRUM — Computation-Elimination-First:
necessity compilation (P, Q, C, B → menor computação certificável),
veredito trivalente (DESNECESSÁRIO_PROVADO / NECESSÁRIO_NO_MODELO /
UNKNOWN-Z), escada de eliminação de 11 degraus com parada no primeiro
degrau certificado, certificados de ELIMINAÇÃO verificáveis, política
soundness-first (falso negativo tolerado, falso positivo nunca).

**Método:** varredura web direcionada (Google/arXiv/ACM, 2026-10-06) sobre
todas as categorias de vizinhos conceituais, somada à pesquisa de
literatura anterior (18 fontes, 1976–2026). Hierarquia de evidências A-E
respeitada: técnicas individuais têm precedente; a COMPOSIÇÃO não.

## Vizinhos mais próximos e por que não equivalem

| # | Sistema/linha | O que faz | Falta o quê |
|---|---|---|---|
| 1 | Algorithm selection / portfolios (Rice 1976; SATzilla; Open Algorithm Selection Challenge 2017) | escolhe o algoritmo mais rápido por instância | **sempre executa um deles**; sem veredito "não execute"; sem certificado |
| 2 | Proof-Carrying Code (Necula 1997) + Abstraction-Carrying Code + certificados incrementais | certificado que o código é SEGURO executar | certifica a EXECUÇÃO, nunca a DESNECESSIDADE — direção oposta |
| 3 | Incremental / self-adjusting computation (Adapton etc.) | evita recomputar o que não mudou | eliminação mecânica DENTRO de uma computação; sem decisão trivalente, sem QPU/HPC |
| 4 | Semantic query optimization (King 1981, QUIST) | reescreve consultas usando restrições | eliminação só em BD; sem certificados, sem escada de recursos |
| 5 | Estimadores de recurso quântico (Azure Resource Estimator, Classiq) | quantifica custo da execução (qubits, tempo) | nunca PROVA que você não deveria executar |
| 6 | Quantum Economic Advantage Calculator (web tool) | prevê QUANDO quântico vence clássico | modelo econômico de linha do tempo, não compilador por problema |
| 7 | QuEST (Jones et al. 2019) | simulador de circuitos | simula; não decide necessidade |
| 8 | QuESt "Quantum Utility Estimation Toolkit" | (varredura 2026-10-06: ferramenta pública com esse nome exato NÃO localizada) | mesmo que exista como descrito: ESTIMADOR preditivo (heurístico), não compilador certificante com escada e trivalência |
| 9 | Multiverse Computing e consultorias QC | avaliação de viabilidade quântica para negócios | consultoria/heurística; sem veredito certificável |

## O que não existe em lugar nenhum da varredura

1. **Compilador cujo alvo é a necessidade** — compilar (P, Q, C, B) e
   produzir o menor kernel certificável, não código mais rápido.
2. **Veredito trivalente de computação** com UNKNOWN como cidadão de
   primeira classe (Z): "não sei" é resposta honesta e registrada, nunca
   convertida em necessidade.
3. **Escada de eliminação ordenada por custo de análise** (IDENTIDADE →
   QUÂNTICO, 11 degraus) com parada no primeiro degrau que decide.
4. **Certificado de eliminação** — prova verificável de que NÃO é preciso
   executar (o inverso exato do Proof-Carrying Code).
5. **Plataforma de família Qiskit** (LANGUAGE → COMPILER → SIMULATOR →
   RUNTIME) em que a decisão fundamental ocorre ANTES da execução.

## Veredito

- **Técnicas dos degraus (afirmação nível B/C):** têm precedente literário
  reconhecido. O projeto NÃO alega novidade das técnicas.
- **Composição arquitetural (afirmação nível A):** sem precedente
  localizado em duas varreduras independentes (18 fontes + varredura web
  direcionada de hoje). A hipótese NOVO CANDIDATO **sobrevive**.
- **Prova de soundness:** permanece pendente do experimento de
  falsificação (200 problemas, 4 famílias, meta: 0 certificados falsos).
  Singularidade sem soundness não vale nada: o experimento é o próximo
  passo obrigatório.

## Limites honestos desta varredura

Varredura via buscador público, não auditoria exaustiva de todo
GitHub/arXiv/patentes. Novos sistemas podem surgir (o campo "quando usar
quântico" está aquecendo: ver #6, #8, #9 — todos heurísticos). A
anterioridade técnica deve ser selada com DOI (Zenodo/arXiv) o quanto antes.
