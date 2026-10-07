"""
DECISION KERNEL — cidadão de primeira classe (Fase 3 — COMPILER CORE).
=====================================================================

O kernel é o sobrevivente: tudo o mais foi eliminado pela escada.
Estrutura (spec docs/SIFR_ARCHITECTURE.md, DECISION_KERNEL):

    {id, name, question, verdict, rung, method, justification, scope, residual}

- id: determinístico (SHA-256 de name+question+rung+method+answer)
- verdict: TRIVALENTE — 0 (desnecessário/eliminado), 1 (necessário),
  Z (UNKNOWN: nem necessidade nem desnecessidade provadas)
- rung: degrau da escada que decidiu (REDUCTION, LIMIT, ANALYTIC, ...)
- method: técnica certificada (MONOTONE_EARLY_STOP, INTERVAL_BOUND, ...)
- justification: por que este degrau tem o direito de decidir
- scope: escopo de validade (suposições, contrato, pergunta)
- residual: unidades de computação que sobraram (o que ainda precisa rodar)

Integridade: CERT_HASH = SHA-256 do certificado canônico (sem o próprio
hash). Qualquer adulteração — de um dígito que seja — quebra o hash e o
checker independente rejeita. O hash cobre o certificado INTEIRO:
evidência, rastro da escada, custos, status, resposta.
"""
import hashlib
import json

from zephirum import STATUS_TO_TRIT


def canonical(obj):
    """Serialização canônica: determinística e independente de ordem."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), default=str)  # Fraction -> "3/10"


def digest(obj):
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def make_kernel(name, question, status, answer, rung, method,
                justification, scope, residual):
    """Constroi o kernel de decisão de primeira classe."""
    kid = "K-" + digest({"name": name, "question": question, "rung": rung,
                         "method": method, "answer": str(answer)})[:16]
    trit, reading = STATUS_TO_TRIT[status]
    return {
        "id": kid,
        "name": name,
        "question": question,
        "verdict": trit,
        "verdict_reading": reading,
        "rung": rung,
        "method": method,
        "justification": justification,
        "scope": scope,
        "residual_units": residual,
    }


def certify(cert):
    """Sela o certificado com o hash canônico (cobre tudo, menos a si mesmo)."""
    cert["CERT_HASH"] = digest(cert)
    return cert


def check_hash(cert):
    """True se o CERT_HASH casa com a recomputação canônica do corpo."""
    stored = cert.get("CERT_HASH")
    # Passo 7: ISSUER/SIGNATURE são envelope de confiança, não payload
    body = {k: v for k, v in cert.items()
            if k not in ("CERT_HASH", "ISSUER", "SIGNATURE")}
    return stored == digest(body)
