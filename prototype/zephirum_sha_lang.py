#!/usr/bin/env python3
"""
ZEPHIRUM SHA-LANG — fatia B4: o SHA-256 do certificado EM LINGUAGEM.
=====================================================================

O certificado Zephirum carrega um INPUT_HASH em SHA-256 (FIPS 180-4).
Até agora, o hash era computado pelo HOSPEDEIRO (hashlib/C) — a fatia
B4 o transfere para DENTRO da linguagem: o programa abaixo é bytecode
ZEPHIRUM puro, executável pela VM orçada (Python) e pelo zvm (C puro),
com o MESMO veredicto do hashlib.

O que isto É:
  - o SHA-256 completo (padding de um bloco, agenda de mensagens,
    64 rodadas de compressão) em LOAD/STORE/FETCH/AND/OR/XOR/SHL/
    SHR/MOD — a extensão de bit da ISA;
  - mais um tijolo do self-hosting honesto: o certificado agora pode
    derivar o próprio hash na linguagem.

O que isto NÃO é (§12, declarado):
  - strings ainda não são dados da linguagem: a codificação
    bytes -> palavras de 32 bits é feita pelo emissor (hospedeiro);
  - mensagens de um bloco (0..55 bytes): multi-bloco exigiria laço
    externo sobre blocos — mesma técnica, outra fatia;
  - o domínio de bit é murado em 32 bits (BIT_WALL): deslocamento
    que escapa é FALTA, não silêncio.

Mapeamento de memória (slots):
  0..63   w[0..63]   agenda de mensagens
  64..71  h[0..7]    estado de trabalho
  72..79  IV[0..7]   vetor de inicialização (constante)
  80,81   temp1,t2   valores da rodada
  84,85   e',a'      valores deslocados antes do rodízio
"""
import hashlib

MOD32 = 4294967296            # 2^32: o muro do domínio de bit (§12)
NOT32 = 4294967295            # 0xFFFFFFFF: NOT(x) == XOR(x, NOT32)

_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b,
    0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
    0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7,
    0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152,
    0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
    0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819,
    0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
    0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f,
    0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
_IV = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
]

# slots
W0, H0, IV0 = 0, 64, 72
TEMP1, T2, TE, TA = 80, 81, 84, 85


def pad_block16(msg):
    """Mensagem (0..55 bytes) -> 16 palavras de 32 bits (FIPS 180-4)."""
    assert len(msg) <= 55, "§12: um bloco (0..55 bytes)"
    padded = msg + b"\x80" + b"\x00" * (55 - len(msg))
    padded += (8 * len(msg)).to_bytes(8, "big")
    return [int.from_bytes(padded[i:i+4], "big") for i in range(0, 64, 4)]


def _rot(prog, slot, n):
    """ROTR(x, n) com AND antes do SHL — nunca escapa do muro 32 bits."""
    prog.append(("FETCH", slot))
    prog.append(("SHR", n))
    prog.append(("FETCH", slot))
    prog.append(("PUSH", (1 << n) - 1))
    prog.append(("AND",))
    prog.append(("SHL", 32 - n))
    prog.append(("OR",))


def build_sha_program(words16):
    """16 palavras -> programa SHA-256 em bytecode ZEPHIRUM."""
    assert len(words16) == 16
    prog = []
    # IV: constante permanente (72..79) e estado inicial (64..71)
    for i, iv in enumerate(_IV):
        prog.append(("PUSH", iv))
        prog.append(("STORE", IV0 + i))
        prog.append(("PUSH", iv))
        prog.append(("STORE", H0 + i))
    # mensagem: 16 LOAD — 16 unidades certificadas (o dado consumido)
    for i in range(16):
        prog.append(("LOAD", i))
        prog.append(("STORE", W0 + i))
    # agenda de mensagens: w[t] = w[t-16] + w[t-7] + s0 + s1 (mod 2^32)
    for t in range(16, 64):
        # s0 = ROTR(w[t-15],7) ^ ROTR(w[t-15],18) ^ (w[t-15] >> 3)
        _rot(prog, W0 + t - 15, 7)
        _rot(prog, W0 + t - 15, 18)
        prog.append(("XOR",))
        prog.append(("FETCH", W0 + t - 15))
        prog.append(("SHR", 3))
        prog.append(("XOR",))
        # s1 = ROTR(w[t-2],17) ^ ROTR(w[t-2],19) ^ (w[t-2] >> 10)
        _rot(prog, W0 + t - 2, 17)
        _rot(prog, W0 + t - 2, 19)
        prog.append(("XOR",))
        prog.append(("FETCH", W0 + t - 2))
        prog.append(("SHR", 10))
        prog.append(("XOR",))
        # w[t] = (w[t-16] + s01 + w[t-7]) mod 2^32
        prog.append(("ADD",))                     # s0 + s1
        prog.append(("FETCH", W0 + t - 16))
        prog.append(("ADD",))
        prog.append(("FETCH", W0 + t - 7))
        prog.append(("ADD",))
        prog.append(("MOD", MOD32))
        prog.append(("STORE", W0 + t))
    # 64 rodadas de compressão — unrolled, sem laço (§12: determinístico)
    for t in range(64):
        a, b, c, d, e, f, g, h = (H0 + i for i in range(8))
        # t2 = ROTR(a,2)^ROTR(a,13)^ROTR(a,22) + maj  (S0 + maj)
        _rot(prog, a, 2)
        _rot(prog, a, 13)
        prog.append(("XOR",))
        _rot(prog, a, 22)
        prog.append(("XOR",))
        # maj = (a&b) ^ (a&c) ^ (b&c)
        prog.append(("FETCH", a))
        prog.append(("FETCH", b))
        prog.append(("AND",))
        prog.append(("FETCH", a))
        prog.append(("FETCH", c))
        prog.append(("AND",))
        prog.append(("XOR",))
        prog.append(("FETCH", b))
        prog.append(("FETCH", c))
        prog.append(("AND",))
        prog.append(("XOR",))
        prog.append(("ADD",))                     # S0 + maj
        prog.append(("MOD", MOD32))
        prog.append(("STORE", T2))
        # ch = (e & f) ^ (NOT(e) & g); NOT(e) = e XOR 0xFFFFFFFF
        prog.append(("FETCH", e))
        prog.append(("FETCH", f))
        prog.append(("AND",))
        prog.append(("FETCH", e))
        prog.append(("PUSH", NOT32))
        prog.append(("XOR",))
        prog.append(("FETCH", g))
        prog.append(("AND",))
        prog.append(("XOR",))                     # [ch]
        # S1 = ROTR(e,6) ^ ROTR(e,11) ^ ROTR(e,25)
        _rot(prog, e, 6)
        _rot(prog, e, 11)
        prog.append(("XOR",))
        _rot(prog, e, 25)
        prog.append(("XOR",))                     # [ch, S1]
        # temp1 = h + S1 + ch + K[t] + w[t]  (mod 2^32)
        prog.append(("FETCH", h))
        prog.append(("ADD",))                      # ch + S1
        prog.append(("SWAP",))
        prog.append(("ADD",))                      # + ch
        prog.append(("PUSH", _K[t]))
        prog.append(("ADD",))
        prog.append(("FETCH", W0 + t))
        prog.append(("ADD",))
        prog.append(("MOD", MOD32))
        prog.append(("STORE", TEMP1))
        # e' = (d + temp1) mod 2^32 — antes do rodízio (d é sobrescrito)
        prog.append(("FETCH", d))
        prog.append(("FETCH", TEMP1))
        prog.append(("ADD",))
        prog.append(("MOD", MOD32))
        prog.append(("STORE", TE))
        # a' = (temp1 + t2) mod 2^32
        prog.append(("FETCH", TEMP1))
        prog.append(("FETCH", T2))
        prog.append(("ADD",))
        prog.append(("MOD", MOD32))
        prog.append(("STORE", TA))
        # rodízio: h=g, g=f, f=e, d=c, c=b, b=a
        prog.append(("FETCH", g))
        prog.append(("STORE", h))
        prog.append(("FETCH", f))
        prog.append(("STORE", g))
        prog.append(("FETCH", e))
        prog.append(("STORE", f))
        prog.append(("FETCH", c))
        prog.append(("STORE", d))
        prog.append(("FETCH", b))
        prog.append(("STORE", c))
        prog.append(("FETCH", a))
        prog.append(("STORE", b))
        prog.append(("FETCH", TE))
        prog.append(("STORE", e))
        prog.append(("FETCH", TA))
        prog.append(("STORE", a))
    # final: H[i] = (h[i] + IV[i]) mod 2^32 — digest na pilha (H0..H7)
    for i in range(8):
        prog.append(("FETCH", H0 + i))
        prog.append(("FETCH", IV0 + i))
        prog.append(("ADD",))
        prog.append(("MOD", MOD32))
        prog.append(("STORE", H0 + i))
    for i in range(8):
        prog.append(("FETCH", H0 + i))
    prog.append(("HALT",))
    return prog


def sha_in_lang(msg, run):
    """Conveniência: hasheia `msg` rodando o bytecode em `run`
    (funcao data, budget, prog -> [8 palavras])."""
    words = pad_block16(msg)
    prog = build_sha_program(words)
    digest_words = run(words, 16, prog)
    return "".join("%08x" % w for w in digest_words)
