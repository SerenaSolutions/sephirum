#!/usr/bin/env python3
"""
BATERIA B4 — o SHA-256 do certificado NA LINGUAGEM.
===============================================

Fatos exigidos por caso (H1..H4, SP1, FT1..FT4):
  H1  o digest em bytecode == hashlib.sha256 (FIPS 180-4);
  H2  o mesmo digest no zvm (C puro) == no Python (byte a byte);
  H3  UNITS == 16 (as 16 palavras do bloco) em ambos os motores;
  H4  TRACE_HASH idêntico entre os motores (execução determinística);
  SP1 uma rodada do SHA como recibo: h após 1 rodada confere com a
      referência numérica derivada da especificação FIPS 180-4;
  FT* faltas espelhadas: XOR em fração, SHL que escapa do muro 32,
      STORE fora de 0..255, MOD m<1 — recusa, nunca silêncio.
"""
import hashlib
import os
import random
import subprocess
import sys
import tempfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "verifier_indep"))

from zephirum_vm import ZephirumVM, VMFault
from zephirum_sha_lang import pad_block16, build_sha_program
from test_vm_c import run_c, serialize          # mesmo formato .zvm

ZVM = os.path.join(HERE, "verifier_indep", "zvm")


def run_py(words, budget, prog):
    vm = ZephirumVM(words, budget)
    _, u, th = vm.run(prog)
    return [int(v) for v in vm.last_stack], u, th


def main():
    rng = random.Random(314159)
    msgs = [b"", b"abc", b"The quick brown fox jumps over the lazy dog",
            b"ZEPHIRUM", b"evidence before velocity",
            b"\x00" * 55, b"\xff" * 31]
    msgs += [bytes(rng.randrange(256) for _ in range(rng.randint(1, 55)))
             for _ in range(18)]

    ok = 0
    for msg in msgs:
        words = pad_block16(msg)
        prog = build_sha_program(words)
        sp, up, tp = run_py(words, 16, prog)
        # H1: digest == hashlib
        got = "".join("%08x" % w for w in sp)
        want = hashlib.sha256(msg).hexdigest()
        assert got == want, (msg[:20], got, want)
        # H2/H3/H4: o mesmo no C puro — digest, unidades e traço
        with tempfile.NamedTemporaryFile(mode="w", suffix=".zvm",
                                         delete=False) as f:
            f.write(serialize(words, 16, prog))
            path = f.name
        try:
            r = subprocess.run([ZVM, path], capture_output=True, text=True)
        finally:
            os.unlink(path)
        assert r.returncode == 0, r.stderr[:200]
        out = {}
        fracs, key = [], None
        for line in r.stdout.splitlines():
            if line.startswith("STACK"):
                key = "stack"
            elif line.startswith("FRAC"):
                fracs.append(int(line.split()[1]))
        assert [int(x) for x in fracs] == sp, (msg[:20], "C difere")
        c_units = int([l for l in r.stdout.splitlines()
                        if l.startswith("UNITS")][0].split()[1])
        c_trace = [l for l in r.stdout.splitlines()
                   if l.startswith("TRACE_HASH")][0].split()[1]
        assert c_units == up == 16, (c_units, up)
        assert c_trace == tp, (msg[:20], "trace diverge")
        ok += 1

    # SP1: rodada única com recibo — h's após a 1ª rodada,
    # truncando o programa logo após o primeiro STORE no slot 64 (a')
    words = pad_block16(b"abc")
    full = build_sha_program(words)
    cut = None
    for i, ins in enumerate(full):
        if ins[0] == "FETCH" and ins[1] == 85:      # TA: a' da rodada
            cut = i
            break
    assert cut is not None
    # o STORE de a' (slot 64) vem logo após o FETCH TA
    while not (full[cut][0] == "STORE" and full[cut][1] == 64):
        cut += 1
    prog1 = full[:cut + 1]
    for i in range(64, 72):
        prog1.append(("FETCH", i))
    prog1.append(("HALT",))
    sp1, _, _ = run_py(words, 16, prog1)
    # referência da 1ª rodada: compressão FIPS com w = pad("abc")
    K, IV = build_sha_program.__globals__["_K"], \
        build_sha_program.__globals__["_IV"]
    rotr = lambda x, n: ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
    w = words + [0] * 48
    for t in range(16, 64):
        s0 = rotr(w[t-15], 7) ^ rotr(w[t-15], 18) ^ (w[t-15] >> 3)
        s1 = rotr(w[t-2], 17) ^ rotr(w[t-2], 19) ^ (w[t-2] >> 10)
        w[t] = (w[t-16] + w[t-7] + s0 + s1) & 0xFFFFFFFF
    a, b, c, d, e, f2, g, h = IV
    t = 0
    S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)
    ch = (e & f2) ^ ((~e & 0xFFFFFFFF) & g)
    temp1 = (h + S1 + ch + K[t] + w[t]) & 0xFFFFFFFF
    S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)
    maj = (a & b) ^ (a & c) ^ (b & c)
    temp2 = (S0 + maj) & 0xFFFFFFFF
    ref = [ (temp1 + temp2) & 0xFFFFFFFF,   # a'
            a, b, c,
            (d + temp1) & 0xFFFFFFFF,      # e'
            e, f2, g ]
    assert sp1 == ref, (sp1, ref)

    # FT1..FT4: faltas espelhadas
    faltas = 0
    for prog2, chave in [
        ([("PUSH", Fraction(1, 2)), ("PUSH", 1), ("AND",), ("HALT",)],
         "domínio de bit"),
        ([("PUSH", 0xFFFFFFFF), ("SHL", 1), ("HALT",)],
         "escapa do domínio"),
        ([("PUSH", 1), ("STORE", 256), ("HALT",)],
         "muro 0..255"),
        ([("PUSH", 1), ("MOD", 0), ("HALT",)],
         "< 1"),
    ]:
        try:
            ZephirumVM([], 0).run(prog2)
            raise AssertionError("faltou VMFault: %r" % chave)
        except VMFault as ex:
            assert chave in str(ex), (chave, str(ex))
        _, rc, err = run_c([], 0, prog2)
        assert rc == 2 and ("§12" in err), err[:160]
        faltas += 1

    print("B4 SHA-256 NA LINGUAGEM: %d mensagens hasheadas em BYTECODE "
          "ZEPHIRUM (padding 1 bloco + agenda + 64 rodadas): digest "
          "== hashlib em 100%% dos casos" % ok)
    print("TRIPLO: VM Python == zvm C puro == hashlib — digest, "
          "UNITS (16/caso) e TRACE_HASH idênticos entre motores")
    print("SP1: 1ª rodada com recibo == referência FIPS 180-4 derivada "
          "independentemente — ok")
    print("FALTAS: %d/4 recusas espelhadas (bit fora do muro, SHL "
          "escapando, slot 256, MOD m<1) — nunca silêncio" % faltas)
    print("RESULTADO: PASS — o INPUT_HASH do certificado agora é "
          "derivado NA PRÓPRIA LINGUAGEM; strings no hospedeiro, §12")


if __name__ == "__main__":
    main()
