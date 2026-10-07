#!/usr/bin/env python3
"""
ZEPHIRUM LEX-LANG — fatia B3.1: o LEXER de assinatura EM LINGUAGEM.
====================================================================

O PHASE_8 declara B3 (lexer/parser em Zephirum) como fronteira que
exige "strings/tokens como dados". A fatia B4 abriu o caminho: com
slots (STORE/FETCH), domínio de bit (AND/OR/XOR) e MOD, esta fatia
executa o PRIMEIRO estágio do self-hosting léxico — a linguagem lendo
a própria entrada de dados.

O que este programa É:
  - um lexer completo em BYTECODE: para cada caractere, classifica
    (dígito, espaço, letra, operador, outro) por comparações CMP e
    máscaras 0/1 combinadas com AND/OR/XOR — branchless, sem JMPZ;
  - reconhece TOKENS NUMÉRICOS: sequências maximais de dígitos,
    acumulando o valor com MUL 10/ADD, exatamente, mod 2^32 (muro de
    bit declarado);
  - emite uma ASSINATURA LÉXICA exata de 6 valores: [n_tokens,
    soma_dos_valores, n_operadores, n_letras, n_espaços, n_outros].

O que isto NÃO é (§12, declarado):
  - strings ainda não são um TIPO da linguagem: o texto entra como
    inteiros (códigos de caractere) via LOAD — a codificação é do
    hospedeiro, a LÓGICA léxica é da linguagem;
  - o ponto entra como operador (não faz parte do token numérico):
    números reais exigem a próxima fatia;
  - o acumulador numérico é murado mod 2^32 (BIT_WALL): silêncio
    não — a bateria verifica o comportamento de wrap contra a
    referência com o MESMO muro;
  - não há parser/árvore: tokens viram assinatura, não estrutura.

Custo: cada caractere é lido EXATAMENTE UMA vez — UNITS == comprimento.
"""
MOD32 = 4294967296
OP_CHARS = "+-*/|:,.<>=()"

# slots persistentes
N_TOK, SUM, N_OP, N_LET, N_SPC, N_OTH, CUR, INN = range(8)
# slots de trabalho por caractere
CHAR, ISD, SPC, ISL, ISO, ISOTH, ENDN = 15, 16, 17, 18, 19, 20, 21


def encode(s):
    """Texto -> dados (códigos de caractere, host-side, §12)."""
    return [ord(ch) for ch in s]


def _sub(prog, slot, lit):
    """empilha (valor do slot - lit) via ADD com negativo."""
    prog.append(("FETCH", slot))
    prog.append(("PUSH", -lit))
    prog.append(("ADD",))


def build_lex_program(chars):
    """Lista de códigos -> programa lexer em bytecode ZEPHIRUM."""
    prog = []
    for i, c in enumerate(chars):
        prog.append(("LOAD", i))                 # 1 unidade por caractere
        prog.append(("STORE", CHAR))
        # ISD = (c >= 48) AND (c <= 57)
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", ">=", 48))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "<=", 57))
        prog.append(("AND",))
        prog.append(("STORE", ISD))
        # SPC = (c == 32)
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "==", 32))
        prog.append(("STORE", SPC))
        # ISL = (65<=c<=90) OR (97<=c<=122)
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", ">=", 65))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "<=", 90))
        prog.append(("AND",))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", ">=", 97))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "<=", 122))
        prog.append(("AND",))
        prog.append(("OR",))
        prog.append(("STORE", ISL))
        # ISO = c in OP_CHARS (cadeia de == e OR)
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "==", ord(OP_CHARS[0])))
        for o in OP_CHARS[1:]:
            prog.append(("FETCH", CHAR))
            prog.append(("CMP", "==", ord(o)))
            prog.append(("OR",))
        prog.append(("STORE", ISO))
        # ISOTH = NOT(ISD OR SPC OR ISL OR ISO)  (máscaras 0/1, XOR 1)
        prog.append(("FETCH", ISD))
        prog.append(("FETCH", SPC))
        prog.append(("OR",))
        prog.append(("FETCH", ISL))
        prog.append(("OR",))
        prog.append(("FETCH", ISO))
        prog.append(("OR",))
        prog.append(("PUSH", 1))
        prog.append(("XOR",))
        prog.append(("STORE", ISOTH))
        # ENDN = (1 - ISD) AND INN  (fecho do token numérico anterior)
        prog.append(("PUSH", 1))
        _sub(prog, ISD, 0)
        prog.append(("ADD",))                   # 1 + (0 - isd) = 1 - isd
        prog.append(("FETCH", INN))
        prog.append(("AND",))
        prog.append(("STORE", ENDN))
        # N_TOK' = N_TOK + ENDN
        prog.append(("FETCH", N_TOK))
        prog.append(("FETCH", ENDN))
        prog.append(("ADD",))
        prog.append(("STORE", N_TOK))
        # SUM' = (SUM + ENDN*CUR) mod 2^32
        prog.append(("FETCH", SUM))
        prog.append(("FETCH", ENDN))
        prog.append(("FETCH", CUR))
        prog.append(("MUL",))
        prog.append(("ADD",))
        prog.append(("MOD", MOD32))
        prog.append(("STORE", SUM))
        # CUR' = ISD * (CUR*10 + (c-48)) mod 2^32
        prog.append(("FETCH", CUR))
        prog.append(("PUSH", 10))
        prog.append(("MUL",))
        _sub(prog, CHAR, 48)                    # c - 48
        prog.append(("ADD",))
        prog.append(("FETCH", ISD))
        prog.append(("SWAP",))
        prog.append(("MUL",))
        prog.append(("MOD", MOD32))
        prog.append(("STORE", CUR))
        # INN' = ISD
        prog.append(("FETCH", ISD))
        prog.append(("STORE", INN))
        # contadores de classe
        for cnt, msk in ((N_OP, ISO), (N_LET, ISL),
                         (N_SPC, SPC), (N_OTH, ISOTH)):
            prog.append(("FETCH", cnt))
            prog.append(("FETCH", msk))
            prog.append(("ADD",))
            prog.append(("STORE", cnt))
    # fecho do token numérico de fim de texto (EOF fecha, como todo lexer)
    prog.append(("PUSH", 1))
    prog.append(("FETCH", INN))
    prog.append(("AND",))
    prog.append(("STORE", ENDN))
    prog.append(("FETCH", N_TOK))
    prog.append(("FETCH", ENDN))
    prog.append(("ADD",))
    prog.append(("STORE", N_TOK))
    prog.append(("FETCH", SUM))
    prog.append(("FETCH", ENDN))
    prog.append(("FETCH", CUR))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("MOD", MOD32))
    prog.append(("STORE", SUM))
    # assinatura léxica na pilha (6 valores)
    for i in range(6):
        prog.append(("FETCH", i))
    prog.append(("HALT",))
    return prog


def ref_lex(s):
    """Referência INDEPENDENTE (mesma semântica, outra implementação):
    usada pela bateria para consenso — nunca pelo programa gerado."""
    ops = set(OP_CHARS)
    n_tok = sum_ = n_op = n_let = n_spc = n_oth = 0
    cur = inn = 0
    for ch in s:
        c = ord(ch)
        isd = 48 <= c <= 57
        if inn and not isd:                    # fecho do token anterior
            n_tok += 1
            sum_ = (sum_ + cur) % MOD32
            cur = 0
        if isd:
            cur = (cur * 10 + c - 48) % MOD32
        else:
            cur = 0
        inn = 1 if isd else 0
        if isd:                                # dígito: classe do token
            pass
        elif c == 32:
            n_spc += 1
        elif 65 <= c <= 90 or 97 <= c <= 122:
            n_let += 1
        elif chr(c) in ops:
            n_op += 1
        else:
            n_oth += 1
    if inn:                                     # EOF fecha
        n_tok += 1
        sum_ = (sum_ + cur) % MOD32
    return [n_tok, sum_, n_op, n_let, n_spc, n_oth]
