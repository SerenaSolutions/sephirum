#!/usr/bin/env python3
"""
ZEPHIRUM TRUST — Passo 7: assinatura Ed25519 do emitente.
=====================================================================

O ciclo de confiança se fecha em duas pontas:
  INTEGRIDADE   (Fase 3): CERT_HASH sela o payload canônico — o
               conteúdo não pode ser adulterado sem quebrar o hash.
  AUTENTICIDADE (Passo 7): SIGNATURE Ed25519 do EMITENTE cobre o mesmo
               payload; o ISSUER tem que estar no REGISTRO DE CONFIANÇA
               (trusted_issuers.txt). Quem forja um certificado novo
               com chave própria não entra no registro — e quem
               adultera um certificado assinado quebra a assinatura.

Registro honesto (§12): a assinatura prova que o certificado saiu da
chave de um emitente REGISTRADO — não prova que a chave merece
confiança (isso é política, não criptografia; web-of-trust fica fora
deste escopo, declarado em docs/PHASE_7_TRUST.md).

Implementações: cryptography (emissão/verificação) e PyNaCl
(contraprova independente — Ed25519 é determinístico: as DUAS
bibliotecas têm que produzir exatamente a mesma assinatura para o
mesmo par (chave, payload); verificação cruzada na bateria).
"""
import os

from decision_kernel import canonical

TRUST_FIELDS = ("ISSUER", "SIGNATURE")
_HERE = os.path.dirname(os.path.abspath(__file__))
TRUSTED_FILE = os.path.join(_HERE, "trusted_issuers.txt")


class TrustNotAvailable(Exception):
    """Dependência cripto ausente — nunca fingimento (§12)."""


def _libs():
    crypto = nacl = None
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        crypto = ed25519
    except ImportError:
        pass
    try:
        from nacl import signing as nacl_signing
        nacl = nacl_signing
    except ImportError:
        pass
    return crypto, nacl


def payload_of(cert):
    """Payload semântico: o certificado sem os campos de envelope
    (CERT_HASH cobre isto; a assinatura cobre exatamente o mesmo)."""
    return {k: v for k, v in cert.items()
            if k not in TRUST_FIELDS and k != "CERT_HASH"}


# --------------------------------------------------------------- chaves
def gen_issuer(seed_hex=None):
    """Gera (sk_hex, pk_hex). seed opcional de 32 bytes hex."""
    crypto, nacl = _libs()
    if crypto is None and nacl is None:
        raise TrustNotAvailable("nem cryptography nem pynacl instalados")
    if seed_hex is None:
        if crypto is not None:
            sk = crypto.Ed25519PrivateKey.generate()
            return sk.private_bytes_raw().hex(), sk.public_key() \
                .public_bytes_raw().hex()
        sk = nacl.SigningKey.generate()
        return bytes(sk).hex(), bytes(sk.verify_key).hex()
    seed = bytes.fromhex(seed_hex)
    if crypto is not None:
        sk = crypto.Ed25519PrivateKey.from_private_bytes(seed)
        return seed_hex, sk.public_key().public_bytes_raw().hex()
    sk = nacl.SigningKey(seed)
    return seed_hex, bytes(sk.verify_key).hex()


# ----------------------------------------------------------- assinar
def sign_certificate(cert, sk_hex, backend="cryptography"):
    """Assina o payload canônico; devolve o certificado + ISSUER/SIGNATURE."""
    crypto, nacl = _libs()
    payload = payload_of(cert)
    msg = canonical(payload).encode("utf-8")
    seed = bytes.fromhex(sk_hex)
    if backend == "pynacl":
        if nacl is None:
            raise TrustNotAvailable("pynacl ausente (§12)")
        sig = bytes(nacl.SigningKey(seed).sign(msg).signature)
    else:
        if crypto is None:
            raise TrustNotAvailable("cryptography ausente (§12)")
        sig = crypto.Ed25519PrivateKey.from_private_bytes(seed) \
            .sign(msg)
    out = dict(cert)
    out["SIGNATURE"] = sig.hex()
    out["ISSUER"] = issuer_pk_of(sk_hex)
    return out


def issuer_pk_of(sk_hex):
    """Chave pública correspondente (mesma rota da emissão)."""
    crypto, nacl = _libs()
    seed = bytes.fromhex(sk_hex)
    if crypto is not None:
        return crypto.Ed25519PrivateKey.from_private_bytes(seed) \
            .public_key().public_bytes_raw().hex()
    if nacl is None:
        raise TrustNotAvailable("sem biblioteca cripto (§12)")
    return bytes(nacl.SigningKey(seed).verify_key).hex()


# ---------------------------------------------------------- verificar
def load_trusted(path=None):
    path = path or TRUSTED_FILE
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return {ln.strip() for ln in f if ln.strip()}


def verify_trust(cert, trusted_issuers=None, backend="cryptography"):
    """(ok, reason). ISSUER no registro + assinatura válida no payload."""
    crypto, nacl = _libs()
    iss, sig = cert.get("ISSUER"), cert.get("SIGNATURE")
    if not iss or not sig:
        return False, ("REJECT: trust fields incomplete "
                       "(ISSUER/SIGNATURE required together)")
    if trusted_issuers is None:
        trusted_issuers = load_trusted()
    if iss not in trusted_issuers:
        return False, "REJECT: untrusted issuer (not in registry)"
    msg = canonical(payload_of(cert)).encode("utf-8")
    try:
        raw_sig, pk = bytes.fromhex(sig), bytes.fromhex(iss)
    except ValueError:
        return False, "REJECT: malformed trust fields"
    try:
        if backend == "pynacl":
            if nacl is None:
                raise TrustNotAvailable("pynacl ausente (§12)")
            nacl.VerifyKey(pk).verify(msg, raw_sig)
        else:
            if crypto is None:
                raise TrustNotAvailable("cryptography ausente (§12)")
            crypto.Ed25519PublicKey.from_public_bytes(pk) \
                .verify(raw_sig, msg)
        return True, "issuer trusted + signature valid"
    except TrustNotAvailable:
        raise
    except Exception:
        return False, "REJECT: invalid signature (tampered or forged)"
