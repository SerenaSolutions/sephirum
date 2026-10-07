# SIFR — Gramática Formal (v0.2)

*Formalização fiel ao interpretador existente (`prototype/nexa_core.py`).
Nada aqui é aspiracional: cada regra descreve sintaxe que o parser atual aceita.*

## 1. Visão

SIFR é uma linguagem declarativa de **pergunta sobre computação**. Um programa
SIFR não descreve COMO computar; descreve O QUE SE PERGUNTA sobre uma
computação, sob que contrato, e com que modelo. O compilador de necessidade
(SCA) então decide: prova a resposta sem executar, ou declara ZERUM (UNKNOWN).

```
PERGUNTE PRIMEIRO. PROVE DEPOIS. COMPUTE POR ÚLTIMO.
```

## 2. Gramática EBNF

```
program     := { block } ;
block       := block_head NEWLINE { statement } ;
block_head  := "ASK" | "CONTRACT" | "MODEL" | "BUDGET" | "REQUIRE" ;
statement   := key ":" value NEWLINE ;
key         := identifier ;
value       := question | number | range | list | "none"
              | identifier | expression ;

question    := target cmp_op number ;          (* "sum > 42", "mean >= 3.5" *)
target      := "sum" | "mean" | "median" ;
cmp_op      := ">" | "<" | ">=" | "<=" | "==" ;

range       := number ".." number ;           (* "0..50" *)
list        := number { "," number } ;        (* "3, 7, 12, 40" *) ;

expression  := aritmética sobre literais (folding seguro);
              operadores: + - * / // % ** ; unários: + -
number      := integer | real ;                (* negativos permitidos *)
```

## 3. Blocos (semântica)

| Bloco | Papel | Chaves aceitas hoje |
|---|---|---|
| `ASK` | a pergunta (única, obrigatória) | `question` |
| `CONTRACT` | tolerâncias e modelo de erro | `absolute_error` |
| `MODEL` | a família computacional | `type`, `terms`, `assumption`, `unknown`, `unknown_value`, `known`, `unknown_count`, `bounds`, `expr` |
| `BUDGET` | limites de custo declarados | reservado |
| `REQUIRE` | pré-condições do usuário | reservado |

Modelos (`type`) atuais: `threshold_sum`, `mean_partial`, `constant_fold`.

## 4. Exemplo canônico

```
ASK:
    question: sum > 40
CONTRACT:
    absolute_error: 0
MODEL:
    type: threshold_sum
    terms: 3, 7, 12, 40
    assumption: terms_nonnegative
    unknown: x in 0..50
    unknown_value: 7
```

## 5. O caminho "como o Python foi criado"

O Python nasceu (1991) como: sintaxe projetada → lexer → parser → AST →
interpretador de bytecode → biblioteca padrão. A SIFR já tem o embrião
(existente e testado): fonte → parser → IR (blocos) → compilador de
necessidade → certificado → ledger. A escada de evolução:

| Fase | Artefato | Status |
|---|---|---|
| 0 | Parser + IR + motor + verificador | **feita e testada (500k casos)** |
| 1 | Gramática formal (este documento) + REPL | **feita** |
| 2 | Lexer próprio (sem `ast` do Python) + transpilação SIFR→Python | próxima |
| 3 | Máquina de bytecode própria (VM) + tipos | futura |
| 4 | Toolchain em Rust/C + gerenciador de pacotes + stdlib | futura |

A fase 2 é o divisor de águas: enquanto o parser empresta o `ast` do Python
para expressões, a SIFR é uma DSL hospedada. Com lexer e parser próprios, ela
passa a ser uma linguagem no sentido pleno — o mesmo degrau que separa o
Python 0.9.0 de um script experimental.
