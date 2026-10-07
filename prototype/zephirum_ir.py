#!/usr/bin/env python3
"""
ZEPHIRUM-IR — representação intermediária própria da plataforma ZEPHIRUM (Fase 3).

Infraestrutura TRANSVERSAL: serve ao Compiler (produz), ao Simulator (valida)
e ao Runtime (executa o residual). NÃO é um quinto pilar.

Este módulo NÃO substitui nada do que existe: o `from_nca` adapta os
resultados do motor NCA atual (Fase 1) para a forma completa do ZEPHIRUM-IR,
provando que o protótipo já emite IR compatível. O protocolo de soundness
permanece: nenhum campo fabricado, UNKNOWN não vira necessidade.
"""
import hashlib
import json

IR_VERSION = "0.1"
IR_TOP_FIELDS = (
    "IR_VERSION", "PROBLEM", "QUESTION", "CONTRACT", "ASSUMPTIONS",
    "EVIDENCE", "DECISION_KERNEL", "ELIMINATION_TRACE", "RESIDUAL",
    "CERTIFICATE", "RESOURCE", "EXECUTION", "RESULT", "STATUS",
)
STATUSES = (
    "DECIDED_WITHOUT_EXECUTION", "DECIDED_BY_REDUCTION",
    "RESIDUAL_COMPUTATION_REQUIRED", "FULL_EXECUTION_REQUIRED", "UNKNOWN",
)
BACKENDS = ("CPU",)  # Fase 5 amplia: GPU, HPC, SIMULATOR, QPU


class SifrIRError(Exception):
    pass


def _question_of(blocks):
    from nexa_core import parse_question
    target, op, thr = parse_question(blocks["ASK"]["question"])
    return {"target": target, "op": op, "threshold": thr,
            "raw": blocks["ASK"]["question"]}


def from_nca(blocks, result):
    """(blocks IR, resultado NCA) -> ZEPHIRUM-IR completo e validável."""
    model = blocks.get("MODEL", {})
    cert = result["certificate"]
    status = result["status"]
    residual = result.get("required")
    is_unknown = status == "UNKNOWN"

    ir = {
        "IR_VERSION": IR_VERSION,
        "PROBLEM": {"family": model.get("type", ""),
                    "params": {k: v for k, v in model.items() if k != "type"}},
        "QUESTION": _question_of(blocks),
        "CONTRACT": dict(blocks.get("CONTRACT", {})),
        "ASSUMPTIONS": [model[k] for k in ("assumption",) if k in model],
        "EVIDENCE": dict(cert.get("EVIDENCE", {})),
        "DECISION_KERNEL": {
            "id": cert.get("KERNEL"),
            "rung": cert.get("RUNG"),
            "method": cert.get("KERNEL"),
            "justification": "%s no degrau %s" % (status, cert.get("RUNG")),
            "scope": model.get("type", ""),
        },
        "ELIMINATION_TRACE": list(result.get("ledger", []) or cert.get("ELIMINATION_TRACE", [])),
        "RESIDUAL": {
            "required_units": None if residual is None else int(residual),
            "spec": "" if residual is None else "soma do residual exigido pelo kernel",
        },
        "CERTIFICATE": dict(cert),
        "RESOURCE": {
            "analysis_cost": cert.get("COST_ESTIMATE", {}).get("analysis", 0.0),
            "execution_cost": cert.get("COST_ESTIMATE", {}).get("execution", 0.0),
            "verification_cost": cert.get("COST_ESTIMATE", {}).get("verification", 0.02),
            "backends": list(BACKENDS),
        },
        "EXECUTION": {
            "status": "NOT_REQUIRED" if status == "DECIDED_WITHOUT_EXECUTION"
                      else ("PENDING" if not is_unknown else "NOT_APPLICABLE"),
            "backend": "CPU",
        },
        "RESULT": {
            "answer": result.get("answer"),
            "trit": "Z" if is_unknown else (1 if result.get("answer") else 0),
        },
        "STATUS": status,
    }
    return ir


def validate(ir):
    """Soundness do IR. Levanta SifrIRError em qualquer violação."""
    for f in IR_TOP_FIELDS:
        if f not in ir:
            raise SifrIRError("campo obrigatório ausente: %s" % f)
    if ir["IR_VERSION"] != IR_VERSION:
        raise SifrIRError("versão de IR incompatível: %r" % ir["IR_VERSION"])
    if ir["STATUS"] not in STATUSES:
        raise SifrIRError("estado inválido: %r" % ir["STATUS"])
    # UNKNOWN nunca vira necessidade nem inventa resposta
    if ir["STATUS"] == "UNKNOWN":
        if ir["RESULT"]["answer"] is not None:
            raise SifrIRError("UNKNOWN com resposta fabricada")
        if ir["RESULT"]["trit"] != "Z":
            raise SifrIRError("UNKNOWN sem trit Z")
        if ir["CERTIFICATE"].get("KERNEL") != "NONE":
            raise SifrIRError("UNKNOWN com kernel: ausência de prova não é prova")
    else:
        if ir["RESULT"]["answer"] not in (True, False):
            raise SifrIRError("estado decidido sem resposta booleana")
        if not ir["CERTIFICATE"].get("INPUT_HASH"):
            raise SifrIRError("certificado sem input_hash: nada é verificável")
    # certificado refere-se a ESTE problema
    if not ir["CERTIFICATE"].get("QUESTION"):
        raise SifrIRError("certificado sem pergunta")
    # residual coerente com o estado
    if ir["STATUS"] == "DECIDED_WITHOUT_EXECUTION":
        if ir["RESIDUAL"]["required_units"] not in (0, None):
            raise SifrIRError("sem-execução exige residual zero")
        if ir["EXECUTION"]["status"] != "NOT_REQUIRED":
            raise SifrIRError("sem-execução não pode exigir runtime")
    for b in ir["RESOURCE"]["backends"]:
        if b not in BACKENDS:
            raise SifrIRError("backend não suportado na Fase atual: %r" % b)
    return True


def ir_hash(ir):
    """Hash canônico do IR (ordem estável de chaves)."""
    return hashlib.sha256(
        json.dumps(ir, sort_keys=True).encode()).hexdigest()


def to_json(ir):
    return json.dumps(ir, sort_keys=True, indent=1)


def from_json(text):
    ir = json.loads(text)
    validate(ir)
    return ir
