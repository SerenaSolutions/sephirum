#!/usr/bin/env python3
"""
ZEPHIRUM VM — Fase 6 (VM própria, componente INTERNO do pilar RUNTIME).
=====================================================================

Uma máquina de bytecode mínima, determinística e ORÇAMENTADA: o
certificado autoriza N unidades de execução residual e a VM é
construída para não conseguir gastar mais do que isso — estourar o
orçamento é FALTA, não liberdade.

Filosofia: o hardware tradicional cobra por tudo o que roda. A VM do
ZEPHIRUM cobra apenas o que o certificado autorizou — e recusa o resto
na unidade de microexecução.

ISA (mínima, sem fluxo de controle nesta fatia — desdobramento em
compile-time):
  PUSH v     empilha constante exata (Fraction)      [custo 0]
  LOAD i     empilha dado i (terms/oráculo)          [custo 1 unidade]
  ADD        soma o topo do stack                    [custo 0]
  MUL        multiplica o topo                        [custo 0]
  CMPT op t  compara o topo com (op, t) => resposta   [custo 0]
  HALT       fim

Unidade = dado consumido (LOAD/PUSH de valor de entrada). O orçamento
vem do certificado (required_terms). A aritmética é exata (Fraction).

Limitações desta fatia (declaradas, §12):
  - cobre resíduos das famílias de soma (testemunha, oráculo, soma
    plena) e séries desdobradas; mediana/determinante/emaranhado NÃO
    são codificáveis ainda (VMNotEncodable — recusa explícita);
  - sem fluxo de controle: laços são desdobrados em compile-time;
  - a base certificada (base_sum do residual) é reutilizada da
    EVIDÊNCIA do certificado — que o verificador independente já
    re-deriva; a VM só combina o oráculo com ela.
"""
import hashlib
import sys
from fractions import Fraction

from nexa_core import parse_list


class VMFault(Exception):
    """A VM violou o contrato: orçamento estourado ou programa mau."""


class VMNotEncodable(Exception):
    """Família ainda não codificável em bytecode nesta fatia (§12)."""


class ZephirumVM:
    """Executa bytecode com orçamento de unidades do certificado."""

    def __init__(self, data, budget):
        self.data = data            # valores carregáveis (LOAD)
        self.budget = budget        # unidades autorizadas pelo certificado
        self.units = 0              # unidades gastas
        self.trace = []             # opcodes executados (determinístico)

    def run(self, program):
        stack = []
        answer = None
        for pc, ins in enumerate(program):
            op = ins[0]
            # fingerprint COMPLETO da execução: opcode + operando — trocar
            # o índice de um LOAD adultera o dado acessado e MUDA o hash
            self.trace.append(op if len(ins) == 1 else "%s:%s" % (op, ins[1]))
            if op == "PUSH":
                stack.append(Fraction(str(ins[1])) if isinstance(ins[1], float)
                              else Fraction(ins[1]))
            elif op == "LOAD":
                i = ins[1]
                if i < 0 or i >= len(self.data):
                    raise VMFault("LOAD fora dos dados (pc=%d)" % pc)
                if self.units >= self.budget:
                    raise VMFault("BUDGET EXCEEDED: %d/%d unidades — o "
                                  "certificado não autoriza mais execução"
                                  % (self.units, self.budget))
                stack.append(Fraction(str(self.data[i])) if
                             isinstance(self.data[i], float) else
                             Fraction(self.data[i]))
                self.units += 1
            elif op == "ADD":
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
            elif op == "MUL":
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
            elif op == "CMPT":
                v = stack.pop()
                o, t = ins[1], ins[2]
                t = Fraction(str(t)) if isinstance(t, float) else Fraction(t)
                answer = {">": v > t, "<": v < t, ">=": v >= t,
                          "<=": v <= t, "==": v == t}[o]
            elif op == "HALT":
                break
            else:
                raise VMFault("opcode desconhecido %r (pc=%d)" % (op, pc))
            if len(stack) > 1024:
                raise VMFault("stack overflow (pc=%d)" % pc)
        return answer, self.units, self.trace_hash()

    def trace_hash(self):
        return hashlib.sha256("|".join(self.trace).encode()).hexdigest()


# ----------------------------------------------------------- compilação
def compile_program(blocks, res):
    """Certificado residual -> bytecode + dados + orçamento.
    Lança VMNotEncodable para famílias fora do escopo desta fatia."""
    model = blocks["MODEL"]
    status = res["status"]
    required = res["required"] or 0
    q = blocks["ASK"]["question"]
    # question: "sum > 100" -> op, thr
    parts = q.rsplit(" ", 2)
    op, thr = parts[1], parts[2]

    if required == 0:
        return ([("HALT",)], [], 0)          # nada a executar

    if status == "DECIDED_BY_REDUCTION":
        terms = parse_list(model["terms"])
        k = required                          # testemunha certificada
        prog = [("LOAD", 0)]
        for i in range(1, k):
            prog.append(("LOAD", i))
            prog.append(("ADD",))
        prog += [("CMPT", op, thr), ("HALT",)]
        return (prog, terms, k)

    if status == "RESIDUAL_COMPUTATION_REQUIRED":
        ev = res["certificate"]["EVIDENCE"]
        base = ev["base_sum"]                 # certificada (checker valida)
        prog = [("PUSH", base), ("LOAD", 0), ("ADD",),
                ("CMPT", op, thr), ("HALT",)]
        return (prog, [model["unknown_value"]], 1)

    if status == "FULL_EXECUTION_REQUIRED" and model.get("type") == "threshold_sum":
        terms = parse_list(model["terms"])
        prog = [("LOAD", 0)]
        for i in range(1, len(terms)):
            prog.append(("LOAD", i))
            prog.append(("ADD",))
        prog += [("CMPT", op, thr), ("HALT",)]
        return (prog, terms, len(terms))

    raise VMNotEncodable(
        "família/status %r não codificável na VM nesta fatia (§12: "
        "recusa explícita, nunca fallback silencioso)"
        % (model.get("type"),))


def vm_execute(blocks, res):
    """Compila o residual, executa sob orçamento e devolve o recibo."""
    prog, data, budget = compile_program(blocks, res)
    vm = ZephirumVM(data, budget)
    answer, units, trace = vm.run(prog)
    if units > budget:
        raise VMFault("contabilidade aberta: %d > %d" % (units, budget))
    return {"answer": answer, "units": units, "budget": budget,
            "trace_hash": trace, "program_size": len(prog)}


if __name__ == "__main__":
    print(__doc__)
