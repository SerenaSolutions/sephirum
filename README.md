# ZERUM — A Computação Antes da Execução

> **PERGUNTE PRIMEIRO. PROVE DEPOIS. COMPUTE POR ÚLTIMO.**

ZERUM é um **compilador de necessidade**: dada uma pergunta sobre uma computação
(via linguagem **SIFR**), ele procura provar que **não é preciso computar** — e só
executa o que sobrar, com certificado verificável.

O paradigma se inverte: de `ALGORITHM → COMPUTE` para `PROOF → COMPUTE`.

- **Linguagem:** SIFR ( árabe *ṣifr*, raiz etimológica de "zero")
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
prototype/   SIFR parser, motor SCA, verificador independente, testes
             (run_tests.py = bateria de soundness; stress_test.py = 500k casos;
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
