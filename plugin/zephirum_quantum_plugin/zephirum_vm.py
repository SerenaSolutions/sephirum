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
  CALL L     chama sub-rotina (só PARA FRENTE)        [custo 0]
  RET        retorna ao ponto da chamada              [custo 0]
  ADD        soma o topo do stack                    [custo 0]
  MUL        multiplica o topo                        [custo 0]
  DIV        divide exato o topo (b != 0)             [custo 0]
  DUP        duplica o valor do topo                [custo 0]
  SWAP       troca os dois valores do topo          [custo 0]
  POW        b^e exato: e = topo, inteiro >= 0     [custo 0]
             (muro POW_EXPONENT_LIMIT: expoente > 65536 => FALTA
              declarada §12 — a aritmética gratuita não escapa
              dos passos de máquina sem parede própria)
  CMP op t   compara o topo com (op, t) => 1/0        [custo 0]
  AND/OR/XOR bit a op b (inteiros, 0 <= v < 2^32)    [custo 0]
             (muro §12: fora do domínio de bit = FALTA)
  SHL k / SHR k   desloca k LITERAL (0..31)          [custo 0]
  MOD m      a mod m (inteiros, m >= 1)             [custo 0]
  STORE i    guarda o topo no slot i (0..255)        [custo 0]
  FETCH i    empilha o slot i                        [custo 0]
  (fatia B4: memória mínima + domínio de bit — o SHA-256
   do certificado em bytecode; strings seguem fora, §12)
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
     no muro de passos; o laço que consome dados bate no BUDGET;
  5. sub-rotina só PARA FRENTE (mesma lei do JMPZ) e profundidade
     de chamada com muro: CALL_DEPTH 64 — recursão infinita bate no
     muro e morre com motivo explícito (§12).

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

def parse_list(s):
    """Autossuficiente: separa vírgulas em Fraction (compatível com
    o nexa_core do protótipo — dependência cortada no pacote)."""
    def _num(tok):
        try:
            return Fraction(tok)
        except (ValueError, ZeroDivisionError):
            return float(tok)
    return [_num(x) for x in s.split(",") if x.strip()]


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
        self.slots = [Fraction(0)] * 256   # memória mínima (B4, §12)
        self.last_stack = None      # pilha final (inspeção da bateria)

    STEP_LIMIT = 65536   # muro mecânico (§12): passos TOTAIS de máquina
    CALL_DEPTH = 64      # muro (§12): profundidade de chamada
    BIT_WALL = 4294967296       # muro (§12): domínio de bit 32
    POW_EXPONENT_LIMIT = 65536  # muro (§12): expoente de POW —
    # b**e cresce sem custo de unidade; sem este muro, um
    # expoente forjado transformaria aritmética gratuita em
    # moenda infinita DENTRO de uma única instrução

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
        call_stack = []                   # endereços de RETORNO
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
            elif op == "CALL":
                target = labels.get(ins[1])
                if target is None:
                    raise VMFault("CALL para label inexistente %r" % ins[1])
                if target <= pc:
                    raise VMFault("CALL para TRÁS (pc=%d -> %d): "
                                  "sub-rotina fica À FRENTE (§soundness)"
                                  % (pc, target))
                if len(call_stack) >= self.CALL_DEPTH:
                    raise VMFault("CALL DEPTH: %d níveis — recursão "
                                  "infinita bate no muro (§12)"
                                  % self.CALL_DEPTH)
                call_stack.append(pc + 1)
                pc = target
                continue
            elif op == "RET":
                if not call_stack:
                    raise VMFault("RET sem CALL (pc=%d)" % pc)
                pc = call_stack.pop()
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
            elif op == "DIV":
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise VMFault("DIV por zero (pc=%d): sem infinito na "
                                  "máquina — recusa explícita (§12)" % pc)
                stack.append(a / b)
            elif op == "DUP":
                if not stack:
                    raise VMFault("DUP com stack vazio (pc=%d)" % pc)
                stack.append(stack[-1])
            elif op == "SWAP":
                if len(stack) < 2:
                    raise VMFault("SWAP com menos de 2 valores (pc=%d)" % pc)
                stack[-1], stack[-2] = stack[-2], stack[-1]
            elif op == "POW":
                e = stack.pop()
                b = stack.pop()
                if e.denominator != 1 or e < 0:
                    raise VMFault("POW: expoente %s não é inteiro >= 0 — "
                                  "recusa explícita (§12)" % e)
                if e.numerator > self.POW_EXPONENT_LIMIT:
                    raise VMFault("POW EXPONENT LIMIT: %d > %d — "
                                  "aritmética gratuita tem parede "
                                  "declarada (§12)"
                                  % (e.numerator, self.POW_EXPONENT_LIMIT))
                stack.append(b ** e.numerator)
            elif op == "CMPT":
                v = stack.pop()
                o, t = ins[1], ins[2]
                t = Fraction(str(t)) if isinstance(t, float) else Fraction(t)
                answer = {">": v > t, "<": v < t, ">=": v >= t,
                          "<=": v <= t, "==": v == t}[o]
            elif op == "AND" or op == "OR" or op == "XOR":
                b = stack.pop()
                a = stack.pop()
                for v in (a, b):
                    if v.denominator != 1 or not (0 <= v < self.BIT_WALL):
                        raise VMFault("%s: operando %s fora do domínio "
                                      "de bit 32 (§12)" % (op, v))
                na, nb = a.numerator, b.numerator
                if op == "AND":
                    stack.append(Fraction(na & nb))
                elif op == "OR":
                    stack.append(Fraction(na | nb))
                else:
                    stack.append(Fraction(na ^ nb))
            elif op == "SHL" or op == "SHR":
                k = ins[1]
                if not (0 <= k <= 31):
                    raise VMFault("%s: deslocamento %s fora do muro "
                                  "0..31 (§12)" % (op, k))
                a = stack.pop()
                if a.denominator != 1 or not (0 <= a < self.BIT_WALL):
                    raise VMFault("%s: operando %s fora do domínio "
                                  "de bit 32 (§12)" % (op, a))
                if op == "SHL":
                    if a.numerator << k >= self.BIT_WALL:
                        raise VMFault("SHL: %d << %d escapa do domínio "
                                      "de bit 32 (§12)" % (a.numerator, k))
                    stack.append(Fraction(a.numerator << k))
                else:
                    stack.append(Fraction(a.numerator >> k))
            elif op == "MOD":
                m = ins[1]
                if m < 1:
                    raise VMFault("MOD: m=%s < 1 (§12)" % m)
                a = stack.pop()
                if a.denominator != 1 or a < 0:
                    raise VMFault("MOD: operando %s não é inteiro "
                                  ">= 0 (§12)" % a)
                stack.append(Fraction(a.numerator % m))
            elif op == "STORE":
                i = ins[1]
                if not (0 <= i < 256):
                    raise VMFault("STORE: slot %d fora do muro 0..255 "
                                  "(§12)" % i)
                self.slots[i] = stack.pop()
            elif op == "FETCH":
                i = ins[1]
                if not (0 <= i < 256):
                    raise VMFault("FETCH: slot %d fora do muro 0..255 "
                                  "(§12)" % i)
                stack.append(self.slots[i])
            elif op == "HALT":
                break
            else:
                raise VMFault("opcode desconhecido %r (pc=%d)" % (op, pc))
            if len(stack) > 1024:
                raise VMFault("stack overflow (pc=%d)" % pc)
            pc += 1
        self.last_stack = list(stack)
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
