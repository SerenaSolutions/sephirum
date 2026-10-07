#!/usr/bin/env python3
"""
ZEPHIRUM PARSE-LANG — fatia B3.2: o PARSER de dados EM LINGUAGEM.
====================================================================

Continuação direta do B3.1 (lexer): a linguagem não só LÊ a própria
entrada, agora a INTERPRETA — os formatos de dados do certificado
(inteiros, frações n/d e decimais) viram VALORES EXATOS (Fraction)
na pilha, com a aritmética da própria linguagem.

Gramática desta fatia (declarada, o programa é a norma):
  VALOR   := INT ('/' INT)? | INT '.' INT+
  INT     := dígito+
  FLUXO   := sequência de VALORES separados por '|' ou ','
  Regras: '/' só dentro de um valor em fase inteira; '.' idem;
  separador sem valor aberto é ERRO (flag); denominador vazio
  ('1/') e decimal sem casas ('1.') são ERRO; '1/0' não é crash —
  é ERRO por flag (o DG do guarda elimina a divisão por zero);
  caracteres fora do alfabeto (letras, acentos, outros operadores)
  são ERRO. O EOF fecha o último valor.

Saída na pilha (fundo -> topo): [v0, v1, ..., VALID, NVAL].
  VALID = 1/0 exato · NVAL = quantidade de valores.

O que isto NÃO é (§12, declarado):
  - tokens como TABELA endereçável: sem memória indexada (fronteira
    B5), o parser consome o fluxo de caracteres DIRETO — a tabela
    de tokens continua declarada como próxima fatia;
  - a codificação texto->inteiros segue no hospedeiro (strings
    ainda não são um TIPO da linguagem);
  - muro de grandeza: parte inteira, denominador e casas decimais
    limitados a 9 dígitos/casas (parede do i128 no zvm); além disso
    é recusa declarada, nunca overflow silencioso;
  - sinais ('-3') ficam para a próxima fatia: '-' é fora do
    alfabeto e marca ERRO.

Custo: 1 LOAD por caractere — UNITS == comprimento do texto.
"""
from fractions import Fraction

MOD32 = 4294967296

# estado persistente
N, D, F, K, PH, INV, VAL, NV, V, DG = range(10)
# trabalho por caractere
CHAR, ISD, SEP, SPC, DOT, SLA, OTH, CLO, MC = range(15, 24)
M0, M1, M2, D0, D1, D2, PS, PD, DGM, P10 = range(24, 34)
BS, BD, BADSEP, CLOS = 34, 35, 37, 38


def encode(s):
    return [ord(ch) for ch in s]


def _emit_close(prog, lbl, use_clo=False):
    """Fecha o valor corrente: DG guarda divisão por zero; V é
    combinado por máscaras de fase; push condicional via JMPZ
    (frente). Atualiza VAL com bad_close (denominador/decimal
    vazios) — SÓ no fecho real (máscara CLOS)."""
    # CLOS = CLO AND INV (meio do texto) ou INV (EOF)
    if use_clo:
        prog.append(("FETCH", CLO))
        prog.append(("FETCH", INV))
        prog.append(("AND",))
    else:
        prog.append(("FETCH", INV))
    prog.append(("STORE", CLOS))
    # DGM = (D >= 1); DG = D + 1 - DGM
    prog.append(("FETCH", D))
    prog.append(("CMP", ">=", 1))
    prog.append(("STORE", DGM))
    prog.append(("FETCH", D))
    prog.append(("PUSH", 1))
    prog.append(("ADD",))
    prog.append(("FETCH", DGM))
    prog.append(("PUSH", -1))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("STORE", DG))
    # P10 = 10^K (POW: base e expoente da pilha)
    prog.append(("PUSH", 10))
    prog.append(("FETCH", K))
    prog.append(("POW",))
    prog.append(("STORE", P10))
    # V = M0*N + M1*(N/DG) + M2*((N*P10+F)/P10)
    prog.append(("FETCH", M0))
    prog.append(("FETCH", N))
    prog.append(("MUL",))                       # t0
    prog.append(("FETCH", M1))
    prog.append(("FETCH", N))
    prog.append(("FETCH", DG))
    prog.append(("DIV",))
    prog.append(("MUL",))                       # t1
    prog.append(("FETCH", N))
    prog.append(("FETCH", P10))
    prog.append(("MUL",))
    prog.append(("FETCH", F))
    prog.append(("ADD",))
    prog.append(("FETCH", P10))
    prog.append(("DIV",))
    prog.append(("FETCH", M2))
    prog.append(("MUL",))                       # t2
    prog.append(("ADD",))
    prog.append(("ADD",))
    prog.append(("STORE", V))
    # bad_close: (M1 e D==0) ou (M2 e K==0)
    prog.append(("FETCH", D))
    prog.append(("CMP", "==", 0))
    prog.append(("FETCH", M1))
    prog.append(("AND",))
    prog.append(("STORE", BS))
    prog.append(("FETCH", K))
    prog.append(("CMP", "==", 0))
    prog.append(("FETCH", M2))
    prog.append(("AND",))
    prog.append(("STORE", BD))
    prog.append(("FETCH", BS))
    prog.append(("FETCH", BD))
    prog.append(("OR",))
    prog.append(("FETCH", CLOS))
    prog.append(("AND",))                          # só no fecho
    prog.append(("PUSH", 1))
    prog.append(("XOR",))
    prog.append(("FETCH", VAL))
    prog.append(("AND",))
    prog.append(("STORE", VAL))
    # push condicional: empilha V e conta APENAS no fecho real
    prog.append(("FETCH", CLOS))
    prog.append(("JMPZ", lbl))
    prog.append(("FETCH", V))
    prog.append(("FETCH", NV))
    prog.append(("PUSH", 1))
    prog.append(("ADD",))
    prog.append(("STORE", NV))
    prog.append(("LABEL", lbl))


def build_parse_program(chars):
    prog = []
    prog.append(("PUSH", 1))                    # VALID nasce 1 (sem erros)
    prog.append(("STORE", VAL))
    for i, c in enumerate(chars):
        prog.append(("LOAD", i))                 # 1 unidade/caractere
        prog.append(("STORE", CHAR))
        # máscaras de classe
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", ">=", 48))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "<=", 57))
        prog.append(("AND",))
        prog.append(("STORE", ISD))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "==", 124))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "==", 44))
        prog.append(("OR",))
        prog.append(("STORE", SEP))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "==", 32))
        prog.append(("STORE", SPC))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "==", 46))
        prog.append(("STORE", DOT))
        prog.append(("FETCH", CHAR))
        prog.append(("CMP", "==", 47))
        prog.append(("STORE", SLA))
        prog.append(("FETCH", ISD))
        prog.append(("FETCH", SEP))
        prog.append(("OR",))
        prog.append(("FETCH", SPC))
        prog.append(("OR",))
        prog.append(("FETCH", DOT))
        prog.append(("OR",))
        prog.append(("FETCH", SLA))
        prog.append(("OR",))
        prog.append(("PUSH", 1))
        prog.append(("XOR",))
        prog.append(("STORE", OTH))
        prog.append(("FETCH", SEP))
        prog.append(("FETCH", SPC))
        prog.append(("OR",))
        prog.append(("STORE", CLO))
        prog.append(("PUSH", 1))
        prog.append(("FETCH", CLO))
        prog.append(("XOR",))
        prog.append(("STORE", MC))
        # máscaras de fase (pré-transição)
        prog.append(("FETCH", PH))
        prog.append(("CMP", "==", 0))
        prog.append(("STORE", M0))
        prog.append(("FETCH", PH))
        prog.append(("CMP", "==", 1))
        prog.append(("STORE", M1))
        prog.append(("FETCH", PH))
        prog.append(("CMP", "==", 2))
        prog.append(("STORE", M2))
        # sub-máscaras de dígito por fase
        for msk, sub in ((M0, D0), (M1, D1), (M2, D2)):
            prog.append(("FETCH", ISD))
            prog.append(("FETCH", msk))
            prog.append(("AND",))
            prog.append(("STORE", sub))
        # fecha valor corrente (push condicional)
        _emit_close(prog, "sk%d" % i, use_clo=True)
        # BADSEP = CLO AND (1 - INV) — INV PRÉ-atualização
        prog.append(("PUSH", 1))
        prog.append(("FETCH", INV))
        prog.append(("XOR",))
        prog.append(("FETCH", CLO))
        prog.append(("AND",))
        prog.append(("STORE", BADSEP))
        # N' = (D0*(N*10 + c-48) + (1-D0)*N) * MC
        prog.append(("FETCH", N))
        prog.append(("PUSH", 10))
        prog.append(("MUL",))
        prog.append(("FETCH", CHAR))
        prog.append(("PUSH", -48))
        prog.append(("ADD",))
        prog.append(("ADD",))                    # N*10 + (c-48)
        prog.append(("FETCH", D0))
        prog.append(("MUL",))
        prog.append(("PUSH", 1))
        prog.append(("FETCH", D0))
        prog.append(("XOR",))
        prog.append(("FETCH", N))
        prog.append(("MUL",))
        prog.append(("ADD",))
        prog.append(("FETCH", MC))
        prog.append(("MUL",))
        prog.append(("STORE", N))
        # D' e F' análogos
        for acc, sub in ((D, D1), (F, D2)):
            prog.append(("FETCH", acc))
            prog.append(("PUSH", 10))
            prog.append(("MUL",))
            prog.append(("FETCH", CHAR))
            prog.append(("PUSH", -48))
            prog.append(("ADD",))
            prog.append(("ADD",))                # acc*10 + (c-48)
            prog.append(("FETCH", sub))
            prog.append(("MUL",))
            prog.append(("PUSH", 1))
            prog.append(("FETCH", sub))
            prog.append(("XOR",))
            prog.append(("FETCH", acc))
            prog.append(("MUL",))
            prog.append(("ADD",))
            prog.append(("FETCH", MC))
            prog.append(("MUL",))
            prog.append(("STORE", acc))
        # K' = K*MC + D2
        prog.append(("FETCH", K))
        prog.append(("FETCH", MC))
        prog.append(("MUL",))
        prog.append(("FETCH", D2))
        prog.append(("ADD",))
        prog.append(("STORE", K))
        # INV' = ISD OR (INV AND MC)
        prog.append(("FETCH", INV))
        prog.append(("FETCH", MC))
        prog.append(("AND",))
        prog.append(("FETCH", ISD))
        prog.append(("OR",))
        prog.append(("STORE", INV))
        # transições de fase: PS (barra), PD (ponto) — só em contexto
        prog.append(("FETCH", SLA))
        prog.append(("FETCH", M0))
        prog.append(("AND",))
        prog.append(("FETCH", INV))
        prog.append(("AND",))
        prog.append(("STORE", PS))
        prog.append(("FETCH", DOT))
        prog.append(("FETCH", M0))
        prog.append(("AND",))
        prog.append(("FETCH", INV))
        prog.append(("AND",))
        prog.append(("STORE", PD))
        # PH' = PH*MC + PS + 2*PD  (1 = fração, 2 = decimal)
        prog.append(("FETCH", PH))
        prog.append(("FETCH", MC))
        prog.append(("MUL",))
        prog.append(("FETCH", PS))
        prog.append(("ADD",))
        prog.append(("PUSH", 2))
        prog.append(("FETCH", PD))
        prog.append(("MUL",))
        prog.append(("ADD",))
        prog.append(("STORE", PH))
        # erros: barra/ponto fora de contexto, alfabeto, sep órfão
        prog.append(("PUSH", 1))
        prog.append(("FETCH", PS))
        prog.append(("XOR",))
        prog.append(("FETCH", SLA))
        prog.append(("AND",))
        prog.append(("STORE", BS))
        prog.append(("PUSH", 1))
        prog.append(("FETCH", PD))
        prog.append(("XOR",))
        prog.append(("FETCH", DOT))
        prog.append(("AND",))
        prog.append(("STORE", BD))
        prog.append(("FETCH", BS))
        prog.append(("FETCH", BD))
        prog.append(("OR",))
        prog.append(("FETCH", OTH))
        prog.append(("OR",))
        prog.append(("FETCH", BADSEP))
        prog.append(("OR",))
        prog.append(("PUSH", 1))
        prog.append(("XOR",))
        prog.append(("FETCH", VAL))
        prog.append(("AND",))
        prog.append(("STORE", VAL))
    # EOF: fecha o último valor
    prog.append(("FETCH", PH))
    prog.append(("CMP", "==", 0))
    prog.append(("STORE", M0))
    prog.append(("FETCH", PH))
    prog.append(("CMP", "==", 1))
    prog.append(("STORE", M1))
    prog.append(("FETCH", PH))
    prog.append(("CMP", "==", 2))
    prog.append(("STORE", M2))
    _emit_close(prog, "eofsk")
    # saída: VALID e NVAL no topo
    prog.append(("FETCH", VAL))
    prog.append(("FETCH", NV))
    prog.append(("HALT",))
    return prog


def ref_parse(s):
    """Referência INDEPENDENTE da mesma gramática declarada — para
    consenso na bateria, nunca usada pelo programa gerado."""
    vals, valid = [], 1
    n = d = f = k = ph = inv = 0
    for ch in s:
        c = ord(ch)
        isd = 48 <= c <= 57
        sep, spc, dot, sla = c in (124, 44), c == 32, c == 46, c == 47
        clo = sep or spc
        m0, m1, m2 = ph == 0, ph == 1, ph == 2
        if clo and inv:                            # fecha e empilha
            if ph == 1 and d == 0:                  # bad_close no fecho
                valid = 0
            if ph == 2 and k == 0:
                valid = 0
            if ph == 0:
                vals.append(Fraction(n))
            elif ph == 1:
                vals.append(Fraction(n, d if d else 1))
            else:
                vals.append(Fraction(n * 10 ** k + f, 10 ** k))
        if clo and not inv:                        # sep órfão
            valid = 0
        ps = sla and inv and ph == 0
        pd = dot and inv and ph == 0
        if (sla and not ps) or (dot and not pd):    # fora de contexto
            valid = 0
        if not (isd or sep or spc or dot or sla):   # alfabeto
            valid = 0
        if isd:
            if ph == 0:
                n = n * 10 + c - 48
            elif ph == 1:
                d = d * 10 + c - 48
            else:
                f = f * 10 + c - 48
                k += 1
            inv = 1
        if clo:
            n = d = f = k = ph = inv = 0
        else:
            ph = ph + (1 if ps else 0) + (2 if pd else 0)
    if inv:                                         # EOF fecha
        if ph == 1 and d == 0:                      # bad_close no fecho
            valid = 0
        if ph == 2 and k == 0:
            valid = 0
        if ph == 0:
            vals.append(Fraction(n))
        elif ph == 1:
            vals.append(Fraction(n, d if d else 1))
        else:
            vals.append(Fraction(n * 10 ** k + f, 10 ** k))
    return vals + [Fraction(valid), Fraction(len(vals))]
