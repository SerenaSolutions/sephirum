#!/usr/bin/env python3
"""
BATERIA DA AUTOPROTECAO POS-QUANTICA — PQ-PROTECT.
=================================================
Direcao do dono: "criptografia quantica de protecao pra ele mesmo"
+ "encapsular ele contra qualquer ataque".

Fatos exigidos (PQ1..PQ4, EC1..EC3):
  PQ1 Lamport OTS (familia FIPS 205, hash-based — imune a Shor):
      roundtrip assina/verifica; mensagem falsa NAO passa;
  PQ2 o CERTIFICADO assinado: selo confere no recibo; SIG
      adulterada pega; RESPOSTA adulterada pega na verificacao
      independente (duas camadas: CERT_HASH + assinatura);
  PQ3 selo de integridade dos arquivos do pacote: um byte
      adulterado e detectado pelo manifesto SHA-256;
  PQ4 determinismo: mesma semente, mesma assinatura;
  EC1 ENCAPSULAMENTO funcional: rede, arquivo e subprocesso
      BLOQUEADOS durante a decisao — o nucleo decide igual
      (funcao pura: superficie de ataque minima e auditavel);
  EC2 nenhum modulo de rede/execucao no nucleo;
  EC3 lixo na entrada (unicode, volumes, injecao): veredito por
      FLAG ou ValueError com motivo — nunca crash, nunca hang.

S12 DECLARADO: "contra QUALQUER ataque" absoluto nao existe em
engenharia; QKD real exige hardware. O que existe — e aqui se
prova — sao camadas verificaveis + honestidade.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugin"))

R2 = "0.70710678118654752"
SRC = ("ASK:\n    question: entangled == 1\nMODEL:\n    type: "
       "entanglement\n    state: %s,0,0,%s\n" % (R2, R2))


def main():
    import zephirum_quantum_plugin as zq

    # PQ1: roundtrip + falsa mensagem
    seed = b"\x01" * 32
    msg = b"\x42" * 32
    pk, sig = zq.pqprotect.keypair(seed), zq.pqprotect.sign(msg, seed)
    assert zq.pqprotect.verify(msg, sig, pk)
    assert not zq.pqprotect.verify(b"\x43" * 32, sig, pk)
    print("PQ1: Lamport 64 bits self-contained — roundtrip ok, "
          "mensagem falsa REJEITADA (hash-based: o que Shor nao "
          "quebra; familia do FIPS 205/SPHINCS+)")

    # PQ2: certificado assinado — camadas de deteccao
    rec, ok = zq.gateway(SRC)
    assert ok and rec["pq_protect"][0], rec["pq_protect"]
    cert = rec["cert"]
    okq, _ = zq.pq_verify(cert)
    assert okq
    falso = dict(cert)
    falso["PQ_PROTECT"] = dict(cert["PQ_PROTECT"])
    falso["PQ_PROTECT"]["SIG"] = list(cert["PQ_PROTECT"]["SIG"])
    falso["PQ_PROTECT"]["SIG"][3] = "00" * 32
    okq, whyq = zq.pq_verify(falso)
    assert not okq and "assinatura" in whyq
    ok2, _ = zq.verify(SRC, falso)
    assert not ok2
    falso2 = dict(cert)
    falso2["ANSWER"] = not cert["ANSWER"]
    ok3, why3 = zq.verify(SRC, falso2)
    assert not ok3
    print("PQ2: certificado com selo Lamport ok; SIG adulterada PEGA "
          "na assinatura; ANSWER adulterada PEGA na verificacao "
          "independente — adulteracao precisa quebrar DUAS camadas")

    # PQ3: selo dos proprios arquivos
    s = zq.pqprotect.self_seal()
    assert zq.pqprotect.verify_seal(s)
    ruim = {"seal": s["seal"][:-1] + ("0" if s["seal"][-1] != "0"
                                     else "1"), "files": s["files"]}
    assert not zq.pqprotect.verify_seal(ruim)
    print("PQ3: manifesto SHA-256 do pacote (%d arquivos) — selo "
          "confere; um nibble trocado e DETECTADO" % len(s["files"]))

    # PQ4: determinismo
    sig2 = zq.pqprotect.sign(msg, seed)
    assert sig2 == sig
    print("PQ4: mesma semente, mesma assinatura — verificacao "
          "reprodutivel")

    # EC1a: gateway inteiro com REDE e PROCESSO bloqueados (o selo
    # le os proprios arquivos, somente leitura, declarado)
    code = (
        "import sys; "
        "sys.path.insert(0, %r); "
        "import socket; socket.socket = lambda *a, **k: (_ for _ in "
        "()).throw(RuntimeError('rede bloqueada')); "
        "import subprocess; subprocess.Popen = lambda *a, **k: (_ "
        "for _ in ()).throw(RuntimeError('processo bloqueado')); "
        "from zephirum_quantum_plugin import gateway; "
        "r, ok = gateway(%r); "
        "assert ok and r['verdict'] == 1; "
        "print('puro')" % (os.path.join(HERE, "..", "plugin"), SRC))
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "puro" in r.stdout, r.stderr[:300]
    # EC1b: NUCLEO DA DECISAO com I/O DE ARQUIVO tambem bloqueado
    code = (
        "import sys, builtins; "
        "sys.path.insert(0, %r); "
        "builtins.open = lambda *a, **k: (_ for _ in ()).throw("
        "RuntimeError('I/O bloqueado — nucleo puro')); "
        "import socket; socket.socket = lambda *a, **k: (_ for _ in "
        "()).throw(RuntimeError('rede bloqueada')); "
        "import subprocess; subprocess.Popen = lambda *a, **k: (_ "
        "for _ in ()).throw(RuntimeError('processo bloqueado')); "
        "from zephirum_quantum_plugin import decide, parse_nexa; "
        "ev = decide(parse_nexa(%r)); "
        "assert ev['answer'] is True; "
        "print('nucleo puro')"
        % (os.path.join(HERE, "..", "plugin"), SRC))
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "nucleo puro" in r.stdout, r.stderr[:300]
    print("EC1: gateway decide com REDE/PROCESSO bloqueados; o "
          "NUCLEO da decisao e puro INCLUSIVE com I/O bloqueado "
          "(o selo de integridade, camada separada, so LE os "
          "proprios arquivos — declarado)")

    # EC2: nenhum modulo de ataque puxado pelo nucleo (a checagem
    # nao importa nada — so espiona sys.modules)
    code = ("import sys; sys.path.insert(0, %r); "
            "proibidos = {'socket', 'subprocess', 'requests', "
            "'urllib'}; "
            "pre = {m.split('.')[0] for m in sys.modules}; "
            "from zephirum_quantum_plugin import gateway; "
            "r, ok = gateway(%r); assert ok; "
            "pos = {m.split('.')[0] for m in sys.modules}; "
            "somados = proibidos & (pos - pre); "
            "assert not somados, somados; "
            "print('limpo')"
            % (os.path.join(HERE, "..", "plugin"), SRC))
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "limpo" in r.stdout, r.stderr[:300]
    print("EC2: nenhum modulo de rede/execucao importado pelo nucleo "
          "— superficie auditavel")

    # EC3: lixo na entrada — flag ou ValueError, nunca crash
    for ruim_q, ruim_st in [
        ("entangled == 1", "1,2,3,%$#"),
        ("entangled == 1", "café,1,2,3"),
        ("entangled == 1", "," * 500),
        ("entangled == 1", "1,2,3,4,5"),
        ("grover == 1", "1,2,3,4"),
        ("entangled == 1", "0,0,0,0")]:
        try:
            rec2, _ = zq.gateway("ASK:\n    question: %s\nMODEL:\n"
                                 "    type: entanglement\n    state: "
                                 "%s\n" % (ruim_q, ruim_st))
            assert rec2.get("routed") is False
        except zq.zephirum_vm.VMFault as ex:
            # muro declarado: volume alem do limite de passos e
            # RECUSADO com recibo (S12) — nunca silencio, nunca hang
            assert "S12" in str(ex) or "§12" in str(ex)
        except (ValueError, SyntaxError) as ex:
            assert str(ex)
    print("EC3: 6 entradas hostis (injecao, unicode, volume, sobra, "
          "familia errada, estado nulo) — todas decididas com motivo "
          "(flag, ValueError ou MURO de passos com recibo S12), "
          "ZERO crash escondido, ZERO hang")

    print()
    print("PQ-PROTECT: PASS — plug-in com autoprotecao pos-quantica "
          "(assinatura hash-based FIPS 205-family no certificado, "
          "selo SHA-256 dos proprios arquivos, nucleo encapsulado "
          "como funcao pura) e recibo honesto S12: camadas "
          "verificaveis, nao promessa absoluta")


if __name__ == "__main__":
    main()
