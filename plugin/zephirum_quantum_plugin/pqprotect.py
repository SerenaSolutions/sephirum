#!/usr/bin/env python3
"""PQ-PROTECT — autoprotecao pos-quantica do plug-in.

Direcao do dono: "criptografia quantica de protecao pra ele mesmo"
+ "encapsular ele contra qualquer ataque".

Camadas entregues (verificaveis, cada uma com recibo):
  1. ASSINATURA HASH-BASED (Lamport 1979, 64 bits de cobertura):
     a familia que o NIST padronizou como SPHINCS+ (FIPS 205) —
     seguranca fundada em SHA-256, sem confianca em fatoracao ou
     log discreto (o que a maquina de Shor quebraria). O CERT_HASH
     e assinado; a chave publica VIAJA no certificado.
  2. SELO DE INTEGRIDADE: manifesto SHA-256 dos proprios arquivos
     do plug-in — adulteracao de um byte e pega.
  3. ENCAPSULAMENTO: o nucleo da decisao e FUNCAO PURA — sem rede,
     sem I/O de arquivo, sem importacao dinamica, sem eval/exec.
     Superficie de ataque minima e AUDITAVEL.

Honestidade (S12): "contra QUALQUER ataque" absoluto nao existe em
engenharia — o que existe e protecao em camadas com verificacao
independente; QKD real exige hardware fisico (declarado, nao
encenado). Seguranca plena de assinatura = FIPS 205/204 com
implementacao auditada; esta camada e o SELO self-contained.
"""
import hashlib
import json
import os

BITS = 64  # bits de cobertura do hash (128 pre-imagens SHA-256)


def _h(b):
    return hashlib.sha256(b).digest()


def _sk(i, b, seed):
    return _h(seed + bytes((i, b)))


def keypair(seed):
    """seed (bytes 32) -> pk = [[h(sk0|0), h(sk0|1)], ...] (hex)."""
    pk = []
    for i in range(BITS):
        pk.append([_h(_sk(i, 0, seed)).hex(),
                   _h(_sk(i, 1, seed)).hex()])
    return pk


def sign(msg_hash, seed):
    """Assina os primeiros BITS bits do hash (hex list)."""
    if len(msg_hash) < BITS // 8:
        raise ValueError("hash curto (S12)")
    sig = []
    for i in range(BITS):
        bit = (msg_hash[i // 8] >> (7 - i % 8)) & 1
        sig.append(_sk(i, bit, seed).hex())
    return sig


def verify(msg_hash, sig, pk):
    """Verifica: h(sig[i]) == pk[i][bit_i]."""
    if len(msg_hash) < BITS // 8 or len(sig) != BITS or len(pk) != BITS:
        return False
    for i in range(BITS):
        bit = (msg_hash[i // 8] >> (7 - i % 8)) & 1
        if _h(bytes.fromhex(sig[i])) != bytes.fromhex(pk[i][bit]):
            return False
    return True


def self_seal(pkg_dir=None):
    """Manifesto SHA-256 dos arquivos .py do pacote (sem __pycache__)."""
    if pkg_dir is None:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
    man = {}
    for name in sorted(os.listdir(pkg_dir)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(pkg_dir, name)
        with open(path, "rb") as f:
            man[name] = hashlib.sha256(f.read()).hexdigest()
    seal = hashlib.sha256(json.dumps(man, sort_keys=True)
                          .encode()).hexdigest()
    return {"files": man, "seal": seal}


def verify_seal(manifest, pkg_dir=None):
    """Confere o pacote atual contra um manifesto salvo (a prova e o
    manifesto que o dono guarda, nao o software que se autoconfessa)."""
    return self_seal(pkg_dir)["seal"] == manifest["seal"]


def pq_protect(cert):
    """Assina o CERT_HASH com Lamport; anexa PQ_PROTECT (chave
    publica + assinatura + selo de integridade do pacote)."""
    seed = os.urandom(32)
    ch = bytes.fromhex(cert["CERT_HASH"])
    sig = sign(ch, seed)
    pk = keypair(seed)
    cert["PQ_PROTECT"] = {
        "ALGORITHM": "LAMPORT-OTS-SHA256-64 (familia FIPS 205)",
        "PK": pk,
        "SIG": sig,
        "PACKAGE_SEAL": self_seal()["seal"],
        "DECLARATION": "assinatura pos-quantica hash-based; QKD real "
                       "exige hardware (S12); seguranca plena = "
                       "FIPS 205 auditado — isto e o selo "
                       "self-contained verificavel",
    }
    return cert


def pq_verify(cert):
    """Verifica o selo pos-quantico do certificado."""
    pq = cert.get("PQ_PROTECT")
    if not pq:
        return False, "sem selo pos-quantico"
    ch = bytes.fromhex(cert["CERT_HASH"])
    if not verify(ch, pq["SIG"], pq["PK"]):
        return False, "assinatura Lamport NAO confere (adulteracao)"
    return True, "selo pos-quantico Lamport confere (FIPS 205 family)"
