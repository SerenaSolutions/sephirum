#!/usr/bin/env python3
"""
SIFR LEXER — Fase 2 da evolução da linguagem (roadmap da gramática).

A partir daqui a SIFR não pede mais emprestado o módulo `ast` do Python:
tokenização e avaliação de expressões são próprias (recursive descent).
O objetivo de soundness se mantém: sem execução de código arbitrário,
sem `eval`, sem chamadas — só aritmética de literais.

Pipeline Fase 2: SIFR source -> LEXER -> TOKENS -> PARSER -> blocks IR
(igual ao da Fase 1) -> NCA (inalterado).
"""
import re

# ── Tokens ──────────────────────────────────────────────────────────
BLOCK_KEYWORDS = ("ASK", "CONTRACT", "MODEL", "BUDGET", "REQUIRE")
TWO_CHAR_OPS = (">=", "<=", "==", "//", "**", "..")

TOKEN_RE = re.compile(r"""
    (?P<WS>        [ \t]+                       )
  | (?P<NEWLINE>   \n                           )
  | (?P<BLOCK>     ASK|CONTRACT|MODEL|BUDGET|REQUIRE\b )
  | (?P<NUMBER>    \d+\.\d+|\d+                 )
  | (?P<TWOOP>     >=|<=|==|//|\*\*|\.\.        )
  | (?P<OP>        [><]                          )
  | (?P<ARITH>     [+\-*/%()]                   )
  | (?P<COMMA>     ,                             )
  | (?P<COLON>     :                             )
  | (?P<IDENT>     [A-Za-z_][A-Za-z0-9_]*       )
""", re.VERBOSE)


class SifrSyntaxError(Exception):
    pass


def tokenize(src):
    """SIFR source -> lista de tokens (type, value, line)."""
    tokens, pos, line = [], 0, 1
    n = len(src)
    while pos < n:
        if src[pos] in " \t":
            pos += 1
            continue
        if src[pos] == "\n":
            tokens.append(("NEWLINE", "\\n", line))
            pos += 1
            line += 1
            continue
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise SifrSyntaxError("caractere ilegal %r na linha %d" % (src[pos], line))
        kind = m.lastgroup
        val = m.group()
        if kind == "IDENT" and val in BLOCK_KEYWORDS:
            raise SifrSyntaxError("palavra reservada %r usada como identificador (linha %d)" % (val, line))
        tokens.append((kind, val, line))
        pos = m.end()
    return tokens


# ── Parser de blocos (produz o IR idêntico ao da Fase 1) ────────────
def parse_sifr(src):
    """SIFR source (tokens próprios) -> blocks IR {ASK: {...}, ...}.

    Estrutura validada por tokens; os valores preservam o texto-fonte
    (contracto da Fase 1), garantindo equivalência exata com parse_nexa.
    """
    tokens = tokenize(src)
    blocks, current = {}, None
    i, n = 0, len(tokens)
    src_lines = src.split("\n")
    while i < n:
        kind, val, line = tokens[i]
        if kind == "NEWLINE":
            i += 1
            continue
        if kind == "BLOCK":
            current = val
            if current in blocks:
                raise SifrSyntaxError("bloco %s duplicado (linha %d)" % (val, line))
            blocks[current] = {}
            i += 1
            # o cabeçalho de bloco termina em ':' (ex.: "ASK:")
            if i < n and tokens[i][0] == "COLON":
                i += 1
            else:
                raise SifrSyntaxError("bloco %s sem ':' (linha %d)" % (val, line))
            while i < n and tokens[i][0] != "NEWLINE":
                raise SifrSyntaxError("conteúdo inesperado após %s (linha %d)" % (val, line))
            continue
        if kind == "IDENT":
            if current is None:
                raise SifrSyntaxError("declaração fora de bloco (linha %d)" % line)
            if i + 1 >= n or tokens[i + 1][0] != "COLON":
                raise SifrSyntaxError("chave %s sem ':' (linha %d)" % (val, line))
            key = val
            # valida a sequência de tokens do valor até o fim da linha
            j = i + 2
            depth = 0
            while j < n and tokens[j][0] != "NEWLINE":
                k2 = tokens[j][0]
                if k2 not in ("NUMBER", "IDENT", "OP", "TWOOP", "ARITH", "COMMA"):
                    raise SifrSyntaxError("token ilegal %r no valor (linha %d)" % (tokens[j][1], line))
                if tokens[j][1] == "(":
                    depth += 1
                if tokens[j][1] == ")":
                    depth -= 1
                    if depth < 0:
                        raise SifrSyntaxError("parêntese desbalanceado (linha %d)" % line)
                j += 1
            if depth != 0:
                raise SifrSyntaxError("parêntese aberto sem fechar (linha %d)" % line)
            # valor = texto-fonte da linha após o ':'
            raw = src_lines[line - 1]
            ci = raw.find(":")
            value = raw[ci + 1:].strip() if ci >= 0 else ""
            blocks[current][key] = value
            i = j
            continue
        raise SifrSyntaxError("token inesperado %r (linha %d)" % (val, line))
    if "ASK" not in blocks:
        raise SifrSyntaxError("programa sem bloco ASK")
    return blocks


# ── Parser de expressões (recursive descent, sem ast) ──────────────
class ExprParser:
    """expr := term (('+'|'-') term)*
       term := unary (('*'|'/'|'//'|'%') unary)*
       unary := ('+'|'-') unary | power
       power := atom ('**' unary)?
       atom := NUMBER | '(' expr ')'
    """

    def __init__(self, text):
        self.toks = []
        pos = 0
        while pos < len(text):
            ch = text[pos]
            if ch in " \t":
                pos += 1
                continue
            two = text[pos:pos + 2]
            if two in ("**", "//"):
                self.toks.append((two, two))
                pos += 2
                continue
            if ch.isdigit() or ch == ".":
                m = re.match(r"\d+\.\d+|\d+|\.\d+", text[pos:])
                if not m:
                    raise SifrSyntaxError("número malformado em %r" % text)
                s = m.group()
                self.toks.append(("num", float(s) if "." in s else int(s)))
                pos += len(s)
                continue
            if ch in "+-*/%()":
                self.toks.append((ch, ch))
                pos += 1
                continue
            raise SifrSyntaxError("caractere ilegal em expressão: %r" % ch)
        self.toks.append(("end", None))
        self.i = 0

    def peek(self):
        return self.toks[self.i]

    def take(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, kind):
        t = self.take()
        if t[0] != kind:
            raise SifrSyntaxError("esperava %s, veio %r" % (kind, t[0]))
        return t

    def parse(self):
        v = self.expr()
        if self.peek()[0] != "end":
            raise SifrSyntaxError("sobras na expressão: %r" % self.peek()[1])
        return v

    def expr(self):
        v = self.term()
        while self.peek()[0] in ("+", "-"):
            op = self.take()[0]
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.unary()
        while self.peek()[0] in ("*", "/", "//", "%"):
            op = self.take()[0]
            r = self.unary()
            if op == "*":
                v = v * r
            elif op == "/":
                v = v / r
            elif op == "//":
                v = v // r
            else:
                v = v % r
        return v

    def unary(self):
        if self.peek()[0] in ("+", "-"):
            op = self.take()[0]
            v = self.unary()
            return v if op == "+" else -v
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek()[0] == "**":
            self.take()
            exp = self.unary()  # associativo à direita, como Python
            return base ** exp
        return base

    def atom(self):
        t = self.take()
        if t[0] == "num":
            return t[1]
        if t[0] == "(":
            v = self.expr()
            self.expect(")")
            return v
        raise SifrSyntaxError("átomo inválido: %r" % (t[0],))


def eval_expr(text):
    """Avalia expressão aritmética de literais SEM ast/eval do Python."""
    return ExprParser(text).parse()
