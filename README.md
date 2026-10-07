<p align="center"><img src="assets/brand/zephirum_bloch_z_dark.png" width="140" alt="ZEPHIRUM — monograma ZEPHIRUM: o Z feito de 0 e 1"></p>

# ZEPHIRUM — A Computação Antes da Execução

<p align="center"><img src="assets/brand/zephirum_bloch_z_dark.png" width="140" alt="ZEPHIRUM — monograma ZEPHIRUM: o Z feito de 0 e 1"></p>

> **PERGUNTE PRIMEIRO. PROVE DEPOIS. COMPUTE POR ÚLTIMO.**

ZEPHIRUM é um **compilador de necessidade**: dada uma pergunta sobre uma computação
(via linguagem **ZEPHIRUM**), ele procura provar que **não é preciso computar** — e só
executa o que sobrar, com certificado verificável.

O paradigma se inverte: de `ALGORITHM → COMPUTE` para `PROOF → COMPUTE`.

- **Linguagem:** ZEPHIRUM (do latim *zephirum*, a forma que Fibonacci
  registrou no *Liber Abaci*, 1202)
- **Algoritmo:** ZCA — Zephirum Compilation Algorithm (escada de eliminação)
- **Numeral:** ZEPHIRUM (Z) — o dígito que é 0 e 1 ao mesmo tempo; o terceiro
  valor de verdade (UNKNOWN) da lógica ZEPHIRUM — o numeral **Z**.
- **Livro:** *ZEPHIRUM — A Computação Antes da Execução* (PT/EN/AR, em produção)

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
prototype/   Lexer/parser ZEPHIRUM próprios (Fase 2: zero ast/eval), motor ZCA,
             verificador independente, REPL, transpilador ZEPHIRUM→Python
             (run_tests.py = soundness; stress_test.py = 500k casos;
              test_zephirum_lang.py = equivalência da linguagem; zephirum_repl.py = REPL;
              ai_layer.py = previsão consultiva; zephirum.py = lógica trivalente)
book/        O livro (PT mestre → EN → AR), estrutura e figuras
results/     Resultados JSON das baterias (reproduzíveis por semente)
docs/        Charter do projeto, paper (arXiv-ready), roteiro INPI
```

## Rodar

```bash
python3 prototype/run_tests.py      # bateria de soundness; exit 0 = ok
python3 prototype/stress_test.py 500000   # 500k problemas, ~14 s
python3 prototype/ai_layer.py      # camada de IA consultiva
python3 prototype/zephirum_repl.py     # REPL: digite programas ZEPHIRUM
cat prog.zeph | python3 prototype/zephirum_transpiler.py  # gera Python autônomo
python3 prototype/test_zephirum_lang.py  # equivalência da linguagem (Fase 2)
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

[🇧🇷 Português](#zephirum--a-computação-antes-da-execução) | [🇺🇸 English](#zephirum--computation-before-execution)

---

# ZEPHIRUM — Computation Before Execution

<p align="center"><img src="assets/brand/zephirum_bloch_z_dark.png" width="140" alt="ZEPHIRUM — monograma ZEPHIRUM: o Z feito de 0 e 1"></p>

> **ASK FIRST. PROVE NEXT. COMPUTE LAST.**

ZEPHIRUM is a **necessity compiler**: given a question about a computation
(stated in the **ZEPHIRUM** language), it tries to prove that **no computation is
needed** — and only executes what remains, with a verifiable certificate.

The paradigm inverts: from `ALGORITHM → COMPUTE` to `PROOF → COMPUTE`.

- **Language:** ZEPHIRUM (from Latin *zephirum*, as recorded by Fibonacci
  in *Liber Abaci*, 1202)
- **Algorithm:** ZCA — Zephirum Compilation Algorithm (elimination ladder)
- **Numeral:** ZEPHIRUM (Z) — the digit that is 0 and 1 at the same time; the
  third truth value (UNKNOWN) of ZEPHIRUM logic — the numeral **Z**.
- **Book:** *ZEPHIRUM — Computation Before Execution* (PT/EN/AR, in production)

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
prototype/   Own ZEPHIRUM lexer/parser (Phase 2: zero ast/eval), ZCA engine,
             independent verifier, REPL, ZEPHIRUM→Python transpiler
             (run_tests.py = soundness; stress_test.py = 500k cases;
              test_zephirum_lang.py = language equivalence; zephirum_repl.py = REPL;
              ai_layer.py = advisory prediction; zephirum.py = trivalent logic)
book/        The book (PT master → EN → AR), structure and figures
results/     JSON results (reproducible by seed)
docs/        Project charter, arXiv-ready paper, INPI roadmap
```

## Run

```bash
python3 prototype/run_tests.py      # soundness battery; exit 0 = ok
python3 prototype/stress_test.py 500000   # 500k problems, ~14 s
python3 prototype/ai_layer.py      # advisory AI layer
python3 prototype/zephirum_repl.py     # REPL: type ZEPHIRUM programs
cat prog.zeph | python3 prototype/zephirum_transpiler.py  # standalone Python output
python3 prototype/test_zephirum_lang.py  # language equivalence (Phase 2)
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
| ![ZEPHIRUM](assets/brand/zephirum_bloch_z_dark.png) | **ZEPHIRUM** — the language (Bloch-Z: the state vector pinned to the equator, neither \|0⟩ nor \|1⟩) |
| ![ZCA](assets/brand/zca_escada_dark.png) | **ZCA** — the commercial algorithm (the certified ladder: stops at the first rung that decides) |
| ![Kernel](assets/brand/kernel_caroco_dark.png) | **Decision Kernel** — the product (only the kernel survives; shell = certificate, seed = answer) |

Full spec: `docs/BRAND_IDENTITY.md`. Z is an epistemic decision state; the
Bloch-sphere analogy is iconographic, never a physical claim.

| Marca | Produto |
|---|---|
| ![ZEPHIRUM](assets/brand/zephirum_bloch_z_dark.png) | **ZEPHIRUM** — a linguagem (Bloch-Z: o vetor no equador, nem \|0⟩ nem \|1⟩ = Z) |
| ![ZCA](assets/brand/zca_escada_dark.png) | **ZCA** — o algoritmo comercial (a escada certificada: para no primeiro degrau que decide) |
| ![Caroço](assets/brand/kernel_caroco_dark.png) | **Decision Kernel** — o produto (só o caroço sobrevive; casca = certificado, semente = resposta) |

Especificação completa: `docs/BRAND_IDENTITY.md`. Z é estado de decisão
epistêmico; a analogia com a esfera de Bloch é iconográfica, nunca alegação física.

## Fase 3 — Compiler Core: decisão → certificado → verificação independente

Pipeline completo e verificável (detalhes técnicos: `docs/PHASE_3.md`):

    ZEPHIRUM → parser → IR → escada de eliminação → decisão trivalente
      → Decision Kernel de primeira classe → certificado (CERT_HASH SHA-256)
      → verificador INDEPENDENTE → resultado

- **Decision Kernel**: {id, verdict 0/1/Z, rung, method, justification,
  scope, residual} — cidadão de primeira classe.
- **CERT_HASH**: SHA-256 canônico do certificado inteiro — integridade;
  adulteração de um dígito quebra o hash.
- **Princípio de não-confiança**: o verificador re-deriva a decisão da
  FONTE (método diferente do motor), com schema estrito de evidência por
  kernel; certificado malformado é rejeitado explicitamente, nunca aceito.
- **Erros estruturais explícitos** (nunca UNKNOWN silencioso): modelo
  desconhecido, intervalo invertido, inf/nan, estado-zero.
- **Família EMARANHADO** (2 qubits puros): perguntas sobre concurrence e
  emaranhamento decididas pelo critério fechado de Schmidt — exato por
  frações, sem simular o vetor de estado. Quantum é a família do
  problema; o mecanismo decisório é clássico e exato.

CLI:

```bash
python3 prototype/zephirum.py check prog.zeph      # RESULT/STATUS/CERTIFICATE/EXECUTION
python3 prototype/zephirum.py explain prog.zeph    # pergunta, escada, decisão
python3 prototype/zephirum.py compile prog.zeph     # grava prog.zeph.cert.json
python3 prototype/zephirum.py verify cert.json prog.zeph   # verificação completa
python3 prototype/zephirum.py benchmark 500000     # benchmark completo
```

Baterias da Fase 3 (todas PASS): adulteração de certificados (RAW 107/107,
REHASH 83/83 obrigatórios), property tests (987+10), equivalência tripla
motor/verificador/transpilado (10.000/10.000), emaranhado (35, forja
rejeitada 3/3), falsificação 200 (0 certificados falsos), stress 500.000
(0 erradas, certificate_valid_rate 1.0, eliminação 76,51%).

Formulação científica: "ZEPHIRUM implementa uma infraestrutura verificável
para provar, em famílias de problemas formalmente suportadas, quando uma
resposta pode ser determinada sem executar a computação completa, e para
declarar UNKNOWN quando essa prova não está disponível."

## Fase 4 — Simulator: o gêmeo adversarial

O pilar SIMULATOR executa a computação COMPLETA que a escada eliminou,
por caminho aritmético independente (Fraction em ordem reversa, Laplace
vs diagonal, loop vs forma fechada, float64 vs exato), para provar por
construção que a eliminação era certa (`docs/PHASE_4.md`):

- **20.000 casos diferenciais: 0 MISMATCH** — kernel == execução plena
- **171.422 unidades simuladas, 136.130 evitadas de fato (79,41%)** —
  o eliminado foi executado mesmo assim e a resposta não mudou
- UNKNOWN honesto: toda Z confirmada como subdeterminada na execução plena
- comparação de modelos computacionais: o float64 erraria na armadilha
  1e16 onde o modelo exato acerta — por isso a aritmética é exata

```bash
python3 prototype/zephirum.py simulate prog.zeph   # kernel vs plena + contratos
python3 prototype/test_simulator.py                # bateria 20k
python3 prototype/test_contracts.py                # contrato: 3 camadas independentes
python3 prototype/test_models.py                   # modelos: exact vs float64
```

**Fatia 2** — contratos são máquinas: o motor rejeita contrato
não-suportado explicitamente (§12), o simulator confere suposições
contra os dados, o checker rejeita testemunha que contraria a suposição
declarada. Modelos computacionais múltiplos: `exact` (Fraction) e
`float64` concordam na faixa comum (10.000/10.000); na zona 2^53+ o
float64 erra onde o exato acerta — medida, não promessa. `gpu`/`hpc`/
`qpu` registrados e honestos: falham explicitamente até existirem.

## The four pillars / Os quatro pilares

```
LANGUAGE (ZEPHIRUM) → COMPILER (NCA + Decision Kernel) → SIMULATOR → RUNTIME
                        │
              CERTIFICATE + RESIDUAL + ZEPHIRUM-IR (transversal)
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
