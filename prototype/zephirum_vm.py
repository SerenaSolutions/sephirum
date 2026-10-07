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

ISA (fatia 2: fluxo de controle ORÇADO):
  PUSH v     empilha constante exata (Fraction)      [custo 0]
  LOAD i     empilha dado i (terms/oráculo)          [custo 1 unidade]
  LOADSEQ    empilha o próximo dado em sequência     [custo 1 unidade]
  MEDIAN k   mediana exata dos k valores do topo     [custo 0]
  ADD        soma o topo do stack                    [custo 0]
  MUL        multiplica o topo                        [custo 0]
  CMP op t   compara o topo com (op, t) => 1/0        [custo 0]
  CMPT op t  compara e FIXA a resposta                [custo 0]
  LABEL L    marcador (alvo de desvio)               [custo 0]
  JMPZ L     desvia SE o topo == 0 (só PARA FRENTE)  [custo 0]
  LOOP n     inicia laço com n LITERAL                [custo 0]
  ENDLOOP    fim do corpo; repete enquanto restar    [custo 0]
  HALT       fim

Leis do fluxo de controle (soundness-first):
  1. laço só com contagem LITERAL: laço infinito NÃO é codificável;
  2. JMPZ só para frente: retroceder exige a estrutura LOOP;
  3. cada LOADSEQ consome 1 unidade do orçamento certificado;
  4. muro mecânico declarado (§12): STEP_LIMIT de passos totais —
     laço forjado de aritmética PURA (que não consome dados) bate
     no muro de passos; o laço que consome dados bate no BUDGET.

Unidade = dado consumido (LOAD/PUSH de valor de entrada). O orçamento
vem do certificado (required_terms). A aritmética é exata (Fraction).

Limitações desta fatia (declaradas, §12):
  - cobre resíduos das famílias de soma (testemunha, oráculo, soma
    plena, séries longas em laço) e MEDIANA (sort clássico em
    bytecode, m unidades = m dados); emaranhado codifica como HALT
    (eliminação analítica total); DETERMINANTE PLENO recusa
    explicitamente: a unidade certificada é o termo de expansão
    Laplace (n!), não o dado consumido (LOAD) — semânticas distintas,
    e rebaixar o teto ou inflar o custo seria desonesto (§12);
  - desvio condicional é frente-only; não existe chamada de
    sub-rotina (sem return address) nesta fatia;
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

    STEP_LIMIT = 65536   # muro mecânico (§12): passos TOTAIS de máquina

    def run(self, program):
        stack = []
        answer = None
        labels = {}                       # LABEL L -> pc (pré-varredura)
        for i, ins in enumerate(program):
            if ins[0] == "LABEL":
                if ins[1] in labels:
                    raise VMFault("label duplicado %r" % ins[1])
                labels[ins[1]] = i
        pc = 0
        seq = 0                           # cursor do LOADSEQ
        loop_stack = []                   # (restantes, corpo_pc)
        steps = 0
        while pc < len(program):
            ins = program[pc]
            op = ins[0]
            steps += 1
            if steps > self.STEP_LIMIT:
                raise VMFault("STEP LIMIT: %d passos — laço forjado sem "
                              "consumo de dado não escapa do muro (§12)"
                              % self.STEP_LIMIT)
            # fingerprint COMPLETO da execução: opcode + operando — trocar
            # o índice de um LOAD adultera o dado acessado e MUDA o hash
            if op != "LOADSEQ":     # LOADSEQ registra índice no branch
                self.trace.append(op if len(ins) == 1
                                  else "%s:%s" % (op, ins[1]))
            if op == "PUSH":
                stack.append(Fraction(str(ins[1])) if isinstance(ins[1], float)
                              else Fraction(ins[1]))
            elif op == "LOADSEQ":
                if seq >= len(self.data):
                    raise VMFault("LOADSEQ fora dos dados (pc=%d)" % pc)
                if self.units >= self.budget:
                    raise VMFault("BUDGET EXCEEDED: %d/%d unidades — o "
                                  "certificado não autoriza mais execução"
                                  % (self.units, self.budget))
                v = self.data[seq]
                self.trace.append("LOADSEQ:%d" % seq)
                seq += 1
                stack.append(Fraction(str(v)) if isinstance(v, float)
                              else Fraction(v))
                self.units += 1
                pc += 1
                continue
            elif op == "CMP":
                v = stack.pop()
                o, t = ins[1], ins[2]
                t = Fraction(str(t)) if isinstance(t, float) else Fraction(t)
                stack.append(Fraction(1 if {">": v > t, "<": v < t,
                    ">=": v >= t, "<=": v <= t, "==": v == t}[o] else 0))
            elif op == "LABEL":
                pass                       # marcador: custo 0, traço 0
            elif op == "JMPZ":
                target = labels.get(ins[1])
                if target is None:
                    raise VMFault("JMPZ para label inexistente %r" % ins[1])
                if target <= pc:
                    raise VMFault("JMPZ para TRÁS (pc=%d -> %d): retroceder "
                                  "exige LOOP (§soundness)" % (pc, target))
                v = stack.pop()
                if v == 0:
                    pc = target
                    continue
            elif op == "LOOP":
                loop_stack.append([ins[1], pc + 1])
            elif op == "ENDLOOP":
                if not loop_stack:
                    raise VMFault("ENDLOOP sem LOOP (pc=%d)" % pc)
                ctx = loop_stack[-1]
                ctx[0] -= 1
                if ctx[0] > 0:
                    pc = ctx[1]
                    continue
                loop_stack.pop()
            elif op == "MEDIAN":
                k = ins[1]
                if k < 1 or len(stack) < k:
                    raise VMFault("MEDIAN k=%d inválido para stack=%d "
                                  "(pc=%d)" % (k, len(stack), pc))
                vals = [stack.pop() for _ in range(k)]
                sv = sorted(vals)
                m = len(sv)
                stack.append(sv[m // 2] if m % 2
                             else (sv[m // 2 - 1] + sv[m // 2]) / 2)
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
            pc += 1
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

    if status == "FULL_EXECUTION_REQUIRED" and model.get("type") == "raw_data":
        data = parse_list(model["data"])
        prog = [("LOAD", i) for i in range(len(data))]
        prog += [("MEDIAN", len(data)), ("CMPT", op, thr), ("HALT",)]
        return (prog, data, len(data))

    if status == "FULL_EXECUTION_REQUIRED" and \
            model.get("type") == "triangular_det":
        raise VMNotEncodable(
            "determinante pleno: unidade certificada = termo de expansão "
            "Laplace (n!), não dado consumido (LOAD) — semânticas de "
            "unidade distintas; recusa explícita §12 (nunca rebaixar o "
            "teto orçamentário nem inflar o custo)")

    if status == "FULL_EXECUTION_REQUIRED" and model.get("type") == "threshold_sum":
        terms = parse_list(model["terms"])
        if len(terms) >= 8:
            # série longa: bytecode em LAÇO — tamanho independente de n,
            # cada LOADSEQ consome 1 unidade => orçamento = len(terms)
            prog = [("PUSH", 0), ("LOOP", len(terms)),
                    ("LOADSEQ",), ("ADD",), ("ENDLOOP",),
                    ("CMPT", op, thr), ("HALT",)]
        else:
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
