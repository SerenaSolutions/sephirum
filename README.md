<p align="center"><img src="assets/brand/sifr_bloch_z_dark.png" width="140" alt="SIFR — monograma ZERUM: o Z feito de 0 e 1"></p>

# ZERUM — A Computação Antes da Execução

<p align="center"><img src="assets/brand/sifr_bloch_z_dark.png" width="140" alt="SIFR — monograma ZERUM: o Z feito de 0 e 1"></p>

> **PERGUNTE PRIMEIRO. PROVE DEPOIS. COMPUTE POR ÚLTIMO.**

ZERUM é um **compilador de necessidade**: dada uma pergunta sobre uma computação
(via linguagem **SIFR**), ele procura provar que **não é preciso computar** — e só
executa o que sobrar, com certificado verificável.

O paradigma se inverte: de `ALGORITHM → COMPUTE` para `PROOF → COMPUTE`.

- **Linguagem:** SIFR (árabe *ṣifr*, raiz etimológica de "zero")
- **Algoritmo:** SCA — SIFR Compilation Algorithm (escada de eliminação)
- **Numeral:** ZERUM (Z) — o dígito que é 0 e 1 ao mesmo tempo; o terceiro
  valor de verdade (UNKNOWN) da lógica SIFR; nome-irmão árabe: **SIWAHID**
  (*ṣifr* + *wāḥid*)
- **Livro:** *ZERUM — A Computação Antes da Execução* (PT/EN/AR, em produção)

## Resultados medidos (reproduzíveis)

| Métrica | Valor |
|---|---|
| Problemas aleatórios testados | 500.000 (14 s, stdlib pura) |
| Respostas erradas | **0** |
| Certificados verificados independentemente | 500.000/500.000 |
| Certificados forjados rejeitados | 20/20 |
| Computação eliminada com certificado | **76,5%** |
| UNKNOWN honesto (não inventou resposta) | 31.418 (6,3%) |
| Camada de IA consultiva (advisory) | 95,67% acurácia vs 53,05% baseline |

## Estrutura

```
prototype/   Lexer/parser SIFR próprios (Fase 2: zero ast/eval), motor SCA,
             verificador independente, REPL, transpilador SIFR→Python
             (run_tests.py = soundness; stress_test.py = 500k casos;
              test_sifr_lang.py = equivalência da linguagem; sifr_repl.py = REPL;
              ai_layer.py = previsão consultiva; zerum.py = lógica trivalente)
book/        O livro (PT mestre → EN → AR), estrutura e figuras
results/     Resultados JSON das baterias (reproduzíveis por semente)
docs/        Charter do projeto, paper (arXiv-ready), roteiro INPI
```

## Rodar

```bash
python3 prototype/run_tests.py      # bateria de soundness; exit 0 = ok
python3 prototype/stress_test.py 500000   # 500k problemas, ~14 s
python3 prototype/ai_layer.py      # camada de IA consultiva
python3 prototype/sifr_repl.py     # REPL: digite programas SIFR
cat prog.sifr | python3 prototype/sifr_transpiler.py  # gera Python autônomo
python3 prototype/test_sifr_lang.py  # equivalência da linguagem (Fase 2)
```

Python 3 puro. Sem dependências. Sem LLM. Sem nuvem.

## Honestidade por projeto

- O que existe: DSL funcional + composição testada de técnicas conhecidas
  (partial evaluation, aritmética de intervalos, certificados verificáveis).
- Possível contribuição: a **composição** — escada de eliminação por custo
  crescente + estados trivalentes + certificado composto + ledger.
- O que NÃO existe aqui: computação quântica (o degrau final é futuro),
  prova de originalidade formal (busca de anterioridade pendente),
  generalização das taxas para domínios arbitrários.
- IA nunca decide: o charter exige gerador heurístico + **verificador
  independente**. A camada de IA é consultiva por construção.

## Licenças

- Código: MIT
- Livro e textos: CC BY-NC-ND 4.0
- Charter e conceito: publicados aqui para anterioridade pública (2026-10-06)

© 2026 AUŠRA Quantinum. Autoria e datas comprováveis pelo histórico Git.

---

[🇧🇷 Português](#zerum--a-computação-antes-da-execução) | [🇺🇸 English](#zerum--computation-before-execution)

---

# ZERUM — Computation Before Execution

<p align="center"><img src="assets/brand/sifr_bloch_z_dark.png" width="140" alt="SIFR — monograma ZERUM: o Z feito de 0 e 1"></p>

> **ASK FIRST. PROVE NEXT. COMPUTE LAST.**

ZERUM is a **necessity compiler**: given a question about a computation
(stated in the **SIFR** language), it tries to prove that **no computation is
needed** — and only executes what remains, with a verifiable certificate.

The paradigm inverts: from `ALGORITHM → COMPUTE` to `PROOF → COMPUTE`.

- **Language:** SIFR (Arabic *ṣifr*, the etymological root of "zero")
- **Algorithm:** SCA — SIFR Compilation Algorithm (elimination ladder)
- **Numeral:** ZERUM (Z) — the digit that is 0 and 1 at the same time; the
  third truth value (UNKNOWN) of SIFR logic; Arabic sibling name: **SIWAHID**
  (*ṣifr* + *wāḥid*)
- **Book:** *ZERUM — Computation Before Execution* (PT/EN/AR, in production)

## Measured results (reproducible)

| Metric | Value |
|---|---|
| Randomized problems tested | 500,000 (14 s, pure stdlib) |
| Wrong answers | **0** |
| Certificates independently verified | 500,000/500,000 |
| Forged certificates rejected | 20/20 |
| Computation eliminated by certificate | **76.5%** |
| Honest UNKNOWNs (no guessing) | 31,418 (6.3%) |
| Advisory AI layer | 95.67% accuracy vs 53.05% baseline |

## Structure

```
prototype/   Own SIFR lexer/parser (Phase 2: zero ast/eval), SCA engine,
             independent verifier, REPL, SIFR→Python transpiler
             (run_tests.py = soundness; stress_test.py = 500k cases;
              test_sifr_lang.py = language equivalence; sifr_repl.py = REPL;
              ai_layer.py = advisory prediction; zerum.py = trivalent logic)
book/        The book (PT master → EN → AR), structure and figures
results/     JSON results (reproducible by seed)
docs/        Project charter, arXiv-ready paper, INPI roadmap
```

## Run

```bash
python3 prototype/run_tests.py      # soundness battery; exit 0 = ok
python3 prototype/stress_test.py 500000   # 500k problems, ~14 s
python3 prototype/ai_layer.py      # advisory AI layer
python3 prototype/sifr_repl.py     # REPL: type SIFR programs
cat prog.sifr | python3 prototype/sifr_transpiler.py  # standalone Python output
python3 prototype/test_sifr_lang.py  # language equivalence (Phase 2)
```

Pure Python 3. No dependencies. No LLM. No cloud.

## Honesty by design

- What exists: a working DSL + a tested composition of known techniques
  (partial evaluation, interval arithmetic, verifiable certificates).
- Possible contribution: the **composition** — a cost-ordered elimination
  ladder + trivalent states + composite certificate + ledger.
- What does NOT exist here: quantum computing (the final rung is future
  work), formal proof of originality (prior-art search pending),
  generalization of the rates to arbitrary domains.
- AI never decides: the charter requires a heuristic generator + an
  **independent verifier**. The AI layer is advisory by construction.


## Brand marks / Marcas

| Mark | Product |
|---|---|
| ![SIFR](assets/brand/sifr_bloch_z_dark.png) | **SIFR** — the language (Bloch-Z: the state vector pinned to the equator, neither \|0⟩ nor \|1⟩) |
| ![SCA](assets/brand/sca_escada_dark.png) | **SCA** — the commercial algorithm (the certified ladder: stops at the first rung that decides) |
| ![Kernel](assets/brand/kernel_caroco_dark.png) | **Decision Kernel** — the product (only the kernel survives; shell = certificate, seed = answer) |

Full spec: `docs/BRAND_IDENTITY.md`. Z is an epistemic decision state; the
Bloch-sphere analogy is iconographic, never a physical claim.

| Marca | Produto |
|---|---|
| ![SIFR](assets/brand/sifr_bloch_z_dark.png) | **SIFR** — a linguagem (Bloch-Z: o vetor no equador, nem \|0⟩ nem \|1⟩ = Z) |
| ![SCA](assets/brand/sca_escada_dark.png) | **SCA** — o algoritmo comercial (a escada certificada: para no primeiro degrau que decide) |
| ![Caroço](assets/brand/kernel_caroco_dark.png) | **Decision Kernel** — o produto (só o caroço sobrevive; casca = certificado, semente = resposta) |

Especificação completa: `docs/BRAND_IDENTITY.md`. Z é estado de decisão
epistêmico; a analogia com a esfera de Bloch é iconográfica, nunca alegação física.

## The four pillars / Os quatro pilares

```
LANGUAGE (SIFR) → COMPILER (NCA + Decision Kernel) → SIMULATOR → RUNTIME
                        │
              CERTIFICATE + RESIDUAL + SIFR-IR (transversal)
```

EN: The transpiler to Python is a provisional RUNTIME backend, not the
product. The VM will be built INSIDE the Runtime (Phase 6). Full spec:
`docs/SIFR_ARCHITECTURE.md`. Roadmap: Phase 3 = COMPILER CORE.

PT: O transpiler para Python é um backend provisório do RUNTIME, não o
produto. A VM será construída DENTRO do Runtime (Fase 6). Especificação
completa: `docs/SIFR_ARCHITECTURE.md`. Roadmap: Fase 3 = COMPILER CORE.

## Licenses

- Code: MIT
- Book and texts: CC BY-NC-ND 4.0
- Charter and concept: published here for public anteriority (2026-10-06)

© 2026 AUŠRA Quantinum. Authorship and dates provable by Git history.
