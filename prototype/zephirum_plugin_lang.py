#!/usr/bin/env python3
"""
ZEPHIRUM PLUGIN-LANG — o PLUG-IN QUÂNTICO NA LINGUAGEM.
=====================================================

Direção do dono: o algoritmo do plug-in NÃO é Python — é ZEPHIRUM.
Este emissor compila a decisão quântica INTEIRA para bytecode:

  ESTÁGIO 1 (entrada): parser B3.2 estendido — 4 amplitudes COM SINAL
    ('-' unário) acumuladas em slots, muradas por máscara;
  ESTÁGIO 2 (decisão): critério de Schmidt em Fraction exata:
      n   = a²+b²+c²+d²
      det = ad − bc
      entangled  <=>  det ≠ 0
      C ~ t (p/q)  <=>  4·det²·q² ~ p²·n²   (multiplicação cruzada
      — a comparação de concorrência nunca divide: exata e sem
      raiz; Wootters PRL 80, 2245, 1998; N&C cap. 2)

O PROGRAMA É A NORMA. Python aqui é só o EMissor (compilador) e o
interpretador da VM — o mesmo papel de um javac/JVM; com o zvm C
puro, não há Python no runtime.

Saída na pilha: [DET, NSQ, C, VERDICT, VALID, NV].
  VALID = 1 exige: exatamente 4 amplitudes, n > 0, alfabeto ok.
Erros são FLAG (VALID=0), nunca crash (§12 herdado do B3.2).
"""
from fractions import Fraction

# ---- slots: estado persistente
N, D, F, K, PH, INV, VAL, NV, V, DG, SIGN = range(11)
# slots: amplitudes
A, B, C_, DQ = 50, 51, 52, 53
# ---- slots: trabalho por caractere
CHAR, ISD, SEP, SPC, DOT, SLA, MIN, OTH, CLO, MC = range(15, 25)
M0, M1, M2, D0, D1, D2, PS, PD, DGM, P10 = range(25, 35)
BS, BD, BADSEP, CLOS, NEGM = range(35, 40)
ST0, ST1, ST2, ST3 = 44, 45, 46, 47
DET, NSQ, NSQG, ABSV, VD, CD = 60, 61, 62, 63, 64, 65


def encode(s):
    return [ord(ch) for ch in s]


def _emit_close(prog, lbl, use_clo=False):
    """Fecha valor: DG guarda div/0; V por máscaras de fase; sinal
    aplicado (1-2·SIGN); armazenamento em A/B/C_/DQ selecionado por
    NV; NV++ no fecho; bad_close e push de FLAG no final."""
    # CLOS = CLO AND INV (meio) ou INV (EOF)
    if use_clo:
        prog.append(("FETCH", CLO))
        prog.append(("FETCH", INV))
        prog.append(("AND",))
    else:
        prog.append(("FETCH", INV))
    prog.append(("STORE", CLOS))
    # DG = D + 1 - (D>=1)
    prog.append(("FETCH", D))
    prog.append(("CMP", ">=", 1))
    prog.append(("STORE", DGM))
    prog.append(("FETCH", D))
    prog.append(("PUSH", 1))
    prog.append(("ADD",))
    prog.append(("FETCH", DGM))
    prog.append(("PUSH", -1))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("STORE", DG))
    # P10 = 10^K
    prog.append(("PUSH", 10))
    prog.append(("FETCH", K))
    prog.append(("POW",))
    prog.append(("STORE", P10))
    # V = M0*N + M1*(N/DG) + M2*((N*P10+F)/P10)
    prog.append(("FETCH", M0))
    prog.append(("FETCH", N))
    prog.append(("MUL",))
    prog.append(("FETCH", M1))
    prog.append(("FETCH", N))
    prog.append(("FETCH", DG))
    prog.append(("DIV",))
    prog.append(("MUL",))
    prog.append(("FETCH", N))
    prog.append(("FETCH", P10))
    prog.append(("MUL",))
    prog.append(("FETCH", F))
    prog.append(("ADD",))
    prog.append(("FETCH", P10))
    prog.append(("DIV",))
    prog.append(("FETCH", M2))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("ADD",))
    prog.append(("STORE", V))
    # bad_close (só no fecho): (M1 e D==0) ou (M2 e K==0)
    prog.append(("FETCH", D))
    prog.append(("CMP", "==", 0))
    prog.append(("FETCH", M1))
    prog.append(("AND",))
    prog.append(("STORE", BS))
    prog.append(("FETCH", K))
    prog.append(("CMP", "==", 0))
    prog.append(("FETCH", M2))
    prog.append(("AND",))
    prog.append(("STORE", BD))
    prog.append(("FETCH", BS))
    prog.append(("FETCH", BD))
    prog.append(("OR",))
    prog.append(("FETCH", CLOS))
    prog.append(("AND",))
    prog.append(("PUSH", 1))
    prog.append(("XOR",))
    prog.append(("FETCH", VAL))
    prog.append(("AND",))
    prog.append(("STORE", VAL))
    # sinal: V' = V * (1 - 2*SIGN)  [SUB não existe: soma do negativo]
    prog.append(("PUSH", 1))
    prog.append(("FETCH", SIGN))
    prog.append(("PUSH", -2))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("FETCH", V))
    prog.append(("MUL",))
    prog.append(("STORE", V))
    # armazenamento mascarado: ST_i = (NV==i) AND CLOS
    for i, (sti, vi) in enumerate(((ST0, A), (ST1, B),
                                   (ST2, C_), (ST3, DQ))):
        prog.append(("FETCH", NV))
        prog.append(("CMP", "==", i))
        prog.append(("FETCH", CLOS))
        prog.append(("AND",))
        prog.append(("STORE", sti))
        # vi' = ST_i*V + (1-ST_i)*vi
        prog.append(("FETCH", sti))
        prog.append(("FETCH", V))
        prog.append(("MUL",))
        prog.append(("PUSH", 1))
        prog.append(("FETCH", sti))
        prog.append(("XOR",))
        prog.append(("FETCH", vi))
        prog.append(("MUL",))
        prog.append(("ADD",))
        prog.append(("STORE", vi))
    # NV++ no fecho real
    prog.append(("FETCH", NV))
    prog.append(("FETCH", CLOS))
    prog.append(("ADD",))
    prog.append(("STORE", NV))
    # SIGN zera no fecho (SIGN' = SIGN*(1-CLOS))
    prog.append(("FETCH", SIGN))
    prog.append(("PUSH", 1))
    prog.append(("FETCH", CLOS))
    prog.append(("XOR",))
    prog.append(("MUL",))
    prog.append(("STORE", SIGN))
    prog.append(("LABEL", lbl))


def _emit_char(prog, c, i):
    prog.append(("LOAD", i))
    prog.append(("STORE", CHAR))
    # máscaras de classe
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", ">=", 48))
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", "<=", 57))
    prog.append(("AND",))
    prog.append(("STORE", ISD))
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", "==", 124))
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", "==", 44))
    prog.append(("OR",))
    prog.append(("STORE", SEP))
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", "==", 32))
    prog.append(("STORE", SPC))
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", "==", 46))
    prog.append(("STORE", DOT))
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", "==", 47))
    prog.append(("STORE", SLA))
    prog.append(("FETCH", CHAR))
    prog.append(("CMP", "==", 45))
    prog.append(("STORE", MIN))
    prog.append(("FETCH", ISD))
    prog.append(("FETCH", SEP))
    prog.append(("OR",))
    prog.append(("FETCH", SPC))
    prog.append(("OR",))
    prog.append(("FETCH", DOT))
    prog.append(("OR",))
    prog.append(("FETCH", SLA))
    prog.append(("OR",))
    prog.append(("FETCH", MIN))
    prog.append(("OR",))
    prog.append(("PUSH", 1))
    prog.append(("XOR",))
    prog.append(("STORE", OTH))
    prog.append(("FETCH", SEP))
    prog.append(("FETCH", SPC))
    prog.append(("OR",))
    prog.append(("STORE", CLO))
    prog.append(("PUSH", 1))
    prog.append(("FETCH", CLO))
    prog.append(("XOR",))
    prog.append(("STORE", MC))
    # máscaras de fase (pré)
    prog.append(("FETCH", PH))
    prog.append(("CMP", "==", 0))
    prog.append(("STORE", M0))
    prog.append(("FETCH", PH))
    prog.append(("CMP", "==", 1))
    prog.append(("STORE", M1))
    prog.append(("FETCH", PH))
    prog.append(("CMP", "==", 2))
    prog.append(("STORE", M2))
    for msk, sub in ((M0, D0), (M1, D1), (M2, D2)):
        prog.append(("FETCH", ISD))
        prog.append(("FETCH", msk))
        prog.append(("AND",))
        prog.append(("STORE", sub))
    # fecho (stores mascarados; gated por CLOS)
    _emit_close(prog, "sk%d" % i, use_clo=True)
    # BADSEP = CLO AND (1-INV) — INV pré-atualização
    prog.append(("PUSH", 1))
    prog.append(("FETCH", INV))
    prog.append(("XOR",))
    prog.append(("FETCH", CLO))
    prog.append(("AND",))
    prog.append(("STORE", BADSEP))
    # N' = (D0*(N*10+(c-48)) + (1-D0)*N) * MC
    for acc, sub in ((N, D0), (D, D1), (F, D2)):
        prog.append(("FETCH", acc))
        prog.append(("PUSH", 10))
        prog.append(("MUL",))
        prog.append(("FETCH", CHAR))
        prog.append(("PUSH", -48))
        prog.append(("ADD",))
        prog.append(("ADD",))
        prog.append(("FETCH", sub))
        prog.append(("MUL",))
        prog.append(("PUSH", 1))
        prog.append(("FETCH", sub))
        prog.append(("XOR",))
        prog.append(("FETCH", acc))
        prog.append(("MUL",))
        prog.append(("ADD",))
        prog.append(("FETCH", MC))
        prog.append(("MUL",))
        prog.append(("STORE", acc))
    # K' = K*MC + D2
    prog.append(("FETCH", K))
    prog.append(("FETCH", MC))
    prog.append(("MUL",))
    prog.append(("FETCH", D2))
    prog.append(("ADD",))
    prog.append(("STORE", K))
    # INV' = ISD OR (INV AND MC)
    prog.append(("FETCH", INV))
    prog.append(("FETCH", MC))
    prog.append(("AND",))
    prog.append(("FETCH", ISD))
    prog.append(("OR",))
    prog.append(("STORE", INV))
    # sinal: '-' abre sinal do PRÓXIMO valor; fora de contexto é erro
    # bad_min = MIN AND (INV OR SIGN)  — com SIGN PRÉ-atualização
    prog.append(("FETCH", INV))
    prog.append(("FETCH", SIGN))
    prog.append(("OR",))
    prog.append(("FETCH", MIN))
    prog.append(("AND",))
    prog.append(("STORE", CD))
    # sign_ok = MIN AND (1-INV) AND (1-SIGN)
    prog.append(("PUSH", 1))
    prog.append(("FETCH", INV))
    prog.append(("XOR",))
    prog.append(("PUSH", 1))
    prog.append(("FETCH", SIGN))
    prog.append(("XOR",))
    prog.append(("AND",))
    prog.append(("FETCH", MIN))
    prog.append(("AND",))
    prog.append(("STORE", BS))
    # SIGN' = SIGN OR sign_ok
    prog.append(("FETCH", SIGN))
    prog.append(("FETCH", BS))
    prog.append(("OR",))
    prog.append(("STORE", SIGN))
    # transições de fase
    prog.append(("FETCH", SLA))
    prog.append(("FETCH", M0))
    prog.append(("AND",))
    prog.append(("FETCH", INV))
    prog.append(("AND",))
    prog.append(("STORE", PS))
    prog.append(("FETCH", DOT))
    prog.append(("FETCH", M0))
    prog.append(("AND",))
    prog.append(("FETCH", INV))
    prog.append(("AND",))
    prog.append(("STORE", PD))
    prog.append(("FETCH", PH))
    prog.append(("FETCH", MC))
    prog.append(("MUL",))
    prog.append(("FETCH", PS))
    prog.append(("ADD",))
    prog.append(("PUSH", 2))
    prog.append(("FETCH", PD))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("STORE", PH))
    # erros: barra/ponto fora de contexto, '-', alfabeto, sep órfão
    prog.append(("PUSH", 1))
    prog.append(("FETCH", PS))
    prog.append(("XOR",))
    prog.append(("FETCH", SLA))
    prog.append(("AND",))
    prog.append(("STORE", BS))
    prog.append(("PUSH", 1))
    prog.append(("FETCH", PD))
    prog.append(("XOR",))
    prog.append(("FETCH", DOT))
    prog.append(("AND",))
    prog.append(("STORE", BD))
    prog.append(("FETCH", BS))
    prog.append(("FETCH", BD))
    prog.append(("OR",))
    prog.append(("FETCH", OTH))
    prog.append(("OR",))
    prog.append(("FETCH", BADSEP))
    prog.append(("OR",))
    prog.append(("FETCH", CD))
    prog.append(("OR",))
    prog.append(("PUSH", 1))
    prog.append(("XOR",))
    prog.append(("FETCH", VAL))
    prog.append(("AND",))
    prog.append(("STORE", VAL))


def build_plugin_program(chars, question):
    """Estado (chars) + pergunta -> programa Zephirum da decisão.

    question: 'entangled == 1' | 'concurrence <op> <racional>' — o
    emissor conhece a pergunta em TEMPO DE COMPILAÇÃO (como o SHA
    conhece a mensagem): a COMPARAÇÃO é bytecode, a decisão é da
    linguagem.
    """
    q = question.strip()
    parts = q.rsplit(" ", 2)
    if len(parts) != 3:
        raise ValueError("pergunta %r malformada" % q)
    target, op, thr_s = parts
    prog = [("PUSH", 1), ("STORE", VAL)]
    for i, c in enumerate(chars):
        _emit_char(prog, c, i)
    # EOF: fecha último valor
    for msk, ph in ((M0, 0), (M1, 1), (M2, 2)):
        prog.append(("FETCH", PH))
        prog.append(("CMP", "==", ph))
        prog.append(("STORE", msk))
    _emit_close(prog, "eofsk", use_clo=False)
    # ==== ESTÁGIO 2: DECISÃO (critério de Schmidt, exato)
    # NSQ = a²+b²+c²+d²
    prog.append(("FETCH", A))
    prog.append(("FETCH", A))
    prog.append(("MUL",))
    prog.append(("FETCH", B))
    prog.append(("FETCH", B))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("FETCH", C_))
    prog.append(("FETCH", C_))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("FETCH", DQ))
    prog.append(("FETCH", DQ))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("STORE", NSQ))
    # DET = a·d − b·c
    prog.append(("FETCH", A))
    prog.append(("FETCH", DQ))
    prog.append(("MUL",))
    prog.append(("FETCH", B))
    prog.append(("FETCH", C_))
    prog.append(("MUL",))
    prog.append(("PUSH", -1))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("STORE", DET))
    # NSQG = NSQ + (NSQ==0)   [guarda div/0 para FRAÇÕES]
    prog.append(("FETCH", NSQ))
    prog.append(("CMP", "==", 0))
    prog.append(("STORE", NSQG))
    prog.append(("FETCH", NSQ))
    prog.append(("FETCH", NSQG))
    prog.append(("ADD",))
    prog.append(("STORE", NSQG))
    # ABSV = |det| = dm*det + (1-dm)*(-det)
    prog.append(("FETCH", DET))
    prog.append(("CMP", ">=", 0))
    prog.append(("STORE", BS))
    prog.append(("FETCH", BS))
    prog.append(("FETCH", DET))
    prog.append(("MUL",))
    prog.append(("PUSH", 1))
    prog.append(("FETCH", BS))
    prog.append(("XOR",))
    prog.append(("FETCH", DET))
    prog.append(("PUSH", -1))
    prog.append(("MUL",))
    prog.append(("MUL",))
    prog.append(("ADD",))
    prog.append(("STORE", ABSV))
    # CD = 2·ABSV / NSQG  (concorrência exata)
    prog.append(("PUSH", 2))
    prog.append(("FETCH", ABSV))
    prog.append(("MUL",))
    prog.append(("FETCH", NSQG))
    prog.append(("DIV",))
    prog.append(("STORE", CD))
    # VERDICT
    if target == "entangled":
        if op != "==" or thr_s != "1":
            raise ValueError("'entangled' responde '== 1'")
        # det ≠ 0  (dois CMP, OR)
        prog.append(("FETCH", DET))
        prog.append(("CMP", ">", 0))
        prog.append(("STORE", BS))
        prog.append(("FETCH", DET))
        prog.append(("CMP", "<", 0))
        prog.append(("STORE", BD))
        prog.append(("FETCH", BS))
        prog.append(("FETCH", BD))
        prog.append(("OR",))
        prog.append(("STORE", VD))
    elif target == "concurrence":
        t = Fraction(thr_s)
        p, q_ = t.numerator, t.denominator
        # sq = 4·det²·q² ; ts = p²·NSQ²  (multiplicação cruzada)
        prog.append(("PUSH", 4))
        prog.append(("FETCH", DET))
        prog.append(("MUL",))
        prog.append(("FETCH", DET))
        prog.append(("MUL",))
        prog.append(("PUSH", q_))
        prog.append(("MUL",))
        prog.append(("PUSH", q_))
        prog.append(("MUL",))
        prog.append(("STORE", BS))
        prog.append(("PUSH", p))
        prog.append(("PUSH", p))
        prog.append(("MUL",))
        prog.append(("FETCH", NSQ))
        prog.append(("MUL",))
        prog.append(("FETCH", NSQ))
        prog.append(("MUL",))
        prog.append(("STORE", BD))
        if op not in (">", "<", ">=", "<=", "=="):
            raise ValueError("operador %r não suportado (§12)" % op)
        # diff = sq - ts (soma do negativo); CMP compara com LITERAL
        prog.append(("FETCH", BS))
        prog.append(("FETCH", BD))
        prog.append(("PUSH", -1))
        prog.append(("MUL",))
        prog.append(("ADD",))
        prog.append(("CMP", {">": ">", "<": "<", ">=": ">=",
                             "<=": "<=", "==": "=="}[op], 0))
        prog.append(("STORE", VD))
    else:
        raise ValueError("alvo %r fora do plug-in" % target)
    # VALID exige exatamente 4 amplitudes e n > 0
    prog.append(("FETCH", NV))
    prog.append(("CMP", "==", 4))
    prog.append(("STORE", BS))
    prog.append(("FETCH", NSQ))
    prog.append(("CMP", ">", 0))
    prog.append(("STORE", BD))
    prog.append(("FETCH", BS))
    prog.append(("FETCH", BD))
    prog.append(("AND",))
    prog.append(("FETCH", VAL))
    prog.append(("AND",))
    prog.append(("STORE", VAL))
    # saída: [DET, NSQ, CD, VD, VAL, NV]
    for s in (DET, NSQ, CD, VD, VAL, NV):
        prog.append(("FETCH", s))
    prog.append(("HALT",))
    return prog


def ref_plugin_decision(state, question):
    """Referência INDEPENDENTE (Fraction direta) — mesmo critério,
    outra implementação, para consenso na bateria."""
    toks = [x.strip() for x in state.split(",")]
    vals = [Fraction(t) for t in toks[:4]] + \
           [Fraction(0)] * max(0, 4 - len(toks))
    a, b, c, d = vals
    nsq = a * a + b * b + c * c + d * d
    det = a * d - b * c
    target, op, thr_s = question.strip().rsplit(" ", 2)
    C = 2 * abs(det) / nsq if nsq else Fraction(0)
    if target == "entangled":
        vd = Fraction(1 if det != 0 else 0)
    else:
        t = Fraction(thr_s)
        sq, ts = 4 * det * det * t.denominator ** 2, \
            t.numerator ** 2 * nsq * nsq
        vd = Fraction(1 if {">": sq > ts, "<": sq < ts,
                            ">=": sq >= ts, "<=": sq <= ts,
                            "==": sq == ts}[op] else 0)
    valid = 1 if (len(toks) == 4 and nsq > 0) else 0
    return {"valid": Fraction(valid), "verdict": vd, "C": C,
            "det": det, "nsq": nsq}
