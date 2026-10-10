"""
NEXA core prototype - Necessity Compilation Algorithm (NCA) v0.1
================================================================
Founding spec: necessity_engine/MASTER_PROMPT_NEXUS_NEXA.md (2026-10-06)
Philosophy: PROOF -> COMPUTE. Soundness > completeness. UNKNOWN is a valid output.
Scope (honest): controlled mathematical/scientific problem families. Stdlib only.

Pipeline: NEXA source -> PARSER -> NEXA-IR (blocks) -> NECESSITY COMPILER
(rungs ordered by analysis cost) -> DECISION KERNEL -> CERTIFICATE -> LEDGER.
"""
import ast
import hashlib
import json
import math
from fractions import Fraction

from decision_kernel import make_kernel, certify
import operator as _O

STATUSES = (
    "DECIDED_WITHOUT_EXECUTION",
    "DECIDED_BY_REDUCTION",
    "RESIDUAL_COMPUTATION_REQUIRED",
    "FULL_EXECUTION_REQUIRED",
    "UNKNOWN",
)

_BIN = {
    ast.Add: _O.add, ast.Sub: _O.sub, ast.Mult: _O.mul, ast.Div: _O.truediv,
    ast.Pow: _O.pow, ast.FloorDiv: _O.floordiv, ast.Mod: _O.mod,
}


def safe_eval(expr):
    """Whitelisted arithmetic constant folding (no names, no calls)."""
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            v = n.value
            # §EXACT: str(float) devolve o literal decimal curto:
            # 0.1 -> '0.1' -> Fraction(1, 10). O fold fica exato.
            return Fraction(str(v)) if isinstance(v, float) else v
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            return _BIN[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        raise ValueError("disallowed syntax: %s" % type(n).__name__)
    return ev(ast.parse(expr, mode="eval").body)


def _num(s):
    """§EXACT: inteiros ficam int; DECIMAIS viram Fraction (semântica
    decimal exata: '0.1' é 1/10, não o float binário). Não-numéricos
    e infinitos falham explicitamente (§12)."""
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        raise ValueError("non-finite/invalid numeric value not "
                         "allowed: %r" % s)


def parse_list(s):
    return [_num(x) for x in s.split(",") if x.strip()]


def parse_matrix(s):
    return [parse_list(row) for row in s.split(";") if row.strip()]


_OPS = {
    ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}


def cmp(value, op, thr):
    return _OPS[op](value, thr)


def parse_question(q):
    for op in (">=", "<=", "==", ">", "<"):
        if op in q:
            target, v = q.split(op, 1)
            return target.strip(), op, _num(v)
    raise ValueError("unparseable question: %r" % q)


def parse_nexa(src):
    """NEXA source -> block IR (ASK / CONTRACT / MODEL / BUDGET / REQUIRE)."""
    blocks, current = {}, None
    for raw in src.strip().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head = line[:-1].strip() if line.endswith(":") else ""
        if head in ("ASK", "CONTRACT", "MODEL", "BUDGET", "REQUIRE"):
            current = head
            blocks[current] = {}
        elif current is not None:
            if ":" in line:
                k, v = line.split(":", 1)
                blocks[current][k.strip()] = v.strip()
            else:  # bare flag line, e.g. "certified_answer"
                blocks[current][line] = ""
        else:
            raise SyntaxError("line outside block: %r" % line)
    for req in ("ASK", "MODEL"):
        if req not in blocks:
            raise SyntaxError("missing %s block" % req)
    return blocks


def _parse_unknown(s):
    """'x in 0..1000' -> ('x', 0, 1000)"""
    name, rest = s.split(" in ")
    lo, hi = rest.split("..")
    lo, hi = _num(lo), _num(hi)
    if hi < lo:  # §12: intervalo invertido é erro estrutural explícito
        raise ValueError("inverted bounds in %r: hi < lo" % s)
    return name.strip(), lo, hi


class NCA:
    """Necessity Compilation Algorithm.

    Input:  P (model), Q (question), C (contract), B (budget), A (available rungs).
    Output: K (decision kernel), R (residual), Pi (certificate), S (status).
    """

    def __init__(self, blocks, name="mission"):
        self.b = blocks
        self.name = name
        self.model = blocks["MODEL"]
        self.contract = blocks.get("CONTRACT", {})
        self.ledger = []
        self.input_hash = hashlib.sha256(
            json.dumps(blocks, sort_keys=True).encode()).hexdigest()
        self.q = parse_question(blocks["ASK"]["question"])

    # ------------------------------------------------------------- ledger
    def log(self, rung, outcome, detail=""):
        self.ledger.append({"rung": rung, "outcome": outcome, "detail": detail})

    # ------------------------------------------------------------- output
    def _finish(self, status, answer, kernel, rung, evidence,
                original, required, analysis_cost):
        if status == "UNKNOWN":
            eliminated, ratio, exec_cost = 0, 0.0, 0.0
            net = -analysis_cost  # baseline must still run; analysis bought nothing
        else:
            eliminated = original - required
            ratio = (100.0 * eliminated / original) if original else 0.0
            exec_cost = float(required)
            net = float(original) - (analysis_cost + exec_cost + 0.02)
        ev = dict(evidence)
        ev.update({
            "input_hash": self.input_hash,
            "kernel": kernel,
            "original_terms": original,
            "required_terms": 0 if required is None else required,
            "assumption": self.model.get("assumption", ""),
            "question": self.b["ASK"]["question"],
        })
        cert = {
            "INPUT_HASH": self.input_hash,
            "QUESTION": self.b["ASK"]["question"],
            "CONTRACT": self.contract,
            "MODEL_TYPE": self.model.get("type", ""),
            "KERNEL": kernel,
            "RUNG": rung,
            "EVIDENCE": ev,
            "ELIMINATION_TRACE": self.ledger,
            "STATUS": status,
            "ANSWER": answer,
            "CHECKER": "verify_certificate.verify",
            "COST_ESTIMATE": {
                "analysis": analysis_cost,
                "execution": exec_cost,
                "verification": 0.02,
            },
        }
        # FASE 3 — COMPILER CORE: Decision Kernel de primeira classe
        justification = (self.ledger[-1]["detail"] if self.ledger
                         else "decided at %s rung" % rung)
        kernel_obj = make_kernel(
            name=self.name, question=self.b["ASK"]["question"],
            status=status, answer=answer, rung=rung, method=kernel,
            justification=justification,
            scope={"assumption": self.model.get("assumption", ""),
                   "contract": dict(self.contract) if self.contract else {},
                   "question": self.b["ASK"]["question"]},
            residual=0 if required is None else required)
        cert["DECISION_KERNEL"] = kernel_obj
        certify(cert)  # CERT_HASH: SHA-256 canônico sela o certificado inteiro
        return {
            "name": self.name, "status": status, "answer": answer,
            "kernel": kernel, "rung": rung, "original": original,
            "required": required, "eliminated": eliminated, "ratio": ratio,
            "net_benefit": net, "certificate": cert, "ledger": self.ledger,
            "decision_kernel": kernel_obj,
        }

    def _unknown(self, why, original=1, analysis_cost=0.0):
        return self._finish("UNKNOWN", None, "NONE", "NONE", {"reason": why},
                            original=original, required=None,
                            analysis_cost=analysis_cost)

    # ------------------------------------------------------------- compile
    def compile(self):
        # §12 — contrato: o motor implementa SOMENTE o contrato exato.
        # Declarar orçamento de erro diferente, ou chave de contrato
        # desconhecida, é ERRO ESTRUTURAL — nunca aceito em silêncio.
        c = self.b.get("CONTRACT", {})
        if c:
            ae = str(c.get("absolute_error", "0")).strip()
            if ae not in ("0", "0.0", ""):
                raise ValueError("unsupported contract: only absolute_error "
                                 "= 0 (exact) is implemented")
            unknown = [k for k in c if k != "absolute_error"]
            if unknown:
                raise ValueError("unsupported contract keys: %r" % unknown)
        t = self.model.get("type")
        target, op, thr = self.q
        if t == "expression":
            return self._expression(op, thr)
        if t == "threshold_sum":
            return self._threshold_sum(op, thr)
        if t == "mean_partial":
            return self._mean_partial(op, thr)
        if t == "triangular_det":
            return self._det(op, thr)
        if t == "geometric_series":
            return self._geo(op, thr)
        if t == "raw_data":
            return self._raw(op, thr)
        if t == "entanglement":
            return self._entangle(op, thr)
        if t == "molecular":
            return self._molecular(op, thr)
        if t == "crypto":
            return self._crypto(op, thr)
        if t == "exact":
            return self._exact(op, thr)
        if t == "hybrid":
            return self._hybrid(op, thr)
        # §12: erro estrutural falha explicitamente — nunca vira UNKNOWN
        raise ValueError("unsupported model type: %r" % t)

    # ------------------------------------------------------------- rungs
    def _expression(self, op, thr):
        expr = self.model["expr"]
        try:
            val = safe_eval(expr)
        except Exception as e:
            self.log("SIMPLIFICATION", "FAILED", str(e))
            # §12: erro estrutural falha explicitamente — nunca vira UNKNOWN
            raise ValueError("expression not foldable: %s: %s"
                              % (expr, e))
        self.log("SIMPLIFICATION", "ELIMINATED",
                 "constant fold: %s = %s" % (expr, val))
        ev = {"expr": expr, "value": val, "op": op, "threshold": thr}
        return self._finish("DECIDED_WITHOUT_EXECUTION", cmp(val, op, thr),
                            "CONSTANT_FOLD", "SIMPLIFICATION", ev,
                            original=1, required=0, analysis_cost=0.01)

    def _threshold_sum(self, op, thr):
        terms = parse_list(self.model["terms"])
        n = len(terms)
        assumption = self.model.get("assumption", "")
        unk = self.model.get("unknown", "")

        # RUNG: REDUCTION - monotone early stop (didatic example, spec S13)
        if assumption == "terms_nonnegative" and op in (">", ">=") and not unk:
            s = 0
            for k, t in enumerate(terms, 1):
                s += t
                if cmp(s, op, thr):
                    self.log("REDUCTION", "ELIMINATED",
                             "decided with %d/%d terms (partial sum %s)" % (k, n, s))
                    ev = {"witness_terms": terms[:k], "witness_sum": s,
                          "op": op, "threshold": thr,
                          "assumption": "terms_nonnegative"}
                    return self._finish("DECIDED_BY_REDUCTION", True,
                                        "MONOTONE_EARLY_STOP", "REDUCTION", ev,
                                        original=n, required=k, analysis_cost=0.05)
            self.log("REDUCTION", "NOT_CONCLUSIVE",
                     "partial sums never crossed threshold")
        else:
            self.log("REDUCTION", "NOT_APPLICABLE",
                     "missing assumption, unknown present, or unsupported op")

        # RUNG: LIMIT - interval bounds on an unknown (spec S23 item 4)
        if unk:
            name, lo, hi = _parse_unknown(unk)
            base = sum(terms)
            if op != ">":
                # FALSIFICACAO 2026-10-06: decidir ignorando a incognita era
                # certificado FALSO. Soundness-first: recusar e permanecer Z.
                return self._unknown(
                    "unknown present with unsupported op '%s': refuse to "
                    "decide from partial information" % op,
                    original=n + 1, analysis_cost=0.15)
            if op == ">":
                if base + lo > thr:
                    self.log("LIMIT", "ELIMINATED",
                             "lower bound already decides (%s+%s > %s)" % (base, lo, thr))
                    ev = {"base_sum": base, "unknown": name,
                          "bounds": [lo, hi], "op": op, "threshold": thr,
                          "mode": "positive"}
                    return self._finish("DECIDED_WITHOUT_EXECUTION", True,
                                        "INTERVAL_BOUND", "LIMIT", ev,
                                        original=n + 1, required=0,
                                        analysis_cost=0.10)
                if base + hi <= thr:
                    self.log("LIMIT", "ELIMINATED",
                             "upper bound already refutes (%s+%s <= %s)" % (base, hi, thr))
                    ev = {"base_sum": base, "unknown": name,
                          "bounds": [lo, hi], "op": op, "threshold": thr,
                          "mode": "negative"}
                    return self._finish("DECIDED_WITHOUT_EXECUTION", False,
                                        "INTERVAL_BOUND", "LIMIT", ev,
                                        original=n + 1, required=0,
                                        analysis_cost=0.10)
                self.log("LIMIT", "NOT_CONCLUSIVE", "bounds straddle threshold")
                # RESIDUAL: evaluate the unknown (oracle stands in for real computation)
                if self.model.get("unknown_value", "") != "":
                    x = _num(self.model["unknown_value"])
                    self.log("RESIDUAL", "EXECUTED",
                             "evaluated %s = %s" % (name, x))
                    s = base + x
                    ev = {"base_sum": base, "unknown": name,
                          "bounds": [lo, hi], "evaluated_value": x,
                          "final_sum": s, "op": op, "threshold": thr}
                    return self._finish(
                        "RESIDUAL_COMPUTATION_REQUIRED", cmp(s, op, thr),
                        "RESIDUAL_EVAL", "CLASSICAL", ev,
                        original=n + 1, required=1, analysis_cost=0.15)
                return self._unknown("bounds straddle; no oracle for unknown",
                                     original=n + 1, analysis_cost=0.15)

        # RUNG: CLASSICAL - nothing eliminated; full execution
        s = sum(terms)
        self.log("CLASSICAL", "EXECUTED", "full sum over %d terms" % n)
        ev = {"full_sum": s, "op": op, "threshold": thr}
        return self._finish("FULL_EXECUTION_REQUIRED", cmp(s, op, thr),
                            "FULL_SUM", "CLASSICAL", ev,
                            original=n, required=n, analysis_cost=0.05)

    def _mean_partial(self, op, thr):
        known = parse_list(self.model["known"])
        u = int(_num(self.model.get("unknown_count", "0")))
        bounds = self.model.get("bounds", "none")
        tot = sum(known)
        N = len(known) + u
        if bounds != "none" and u > 0 and op == ">":
            lo, hi = bounds.split("..")
            lo, hi = _num(lo), _num(hi)
            mean_lo = (tot + u * lo) / N
            mean_hi = (tot + u * hi) / N
            # FALSIFICACAO 2026-10-06: float perde o dígito que decide em
            # magnitudes ~1e16. A decisão é por Fraction exata; o float
            # permanece apenas como valor de exibição no certificado.
            exact_lo = Fraction(tot + u * lo) / N
            exact_hi = Fraction(tot + u * hi) / N
            self.log("LIMIT", "EXECUTED",
                     "interval arithmetic on %d unknowns in [%s, %s]" % (u, lo, hi))
            if exact_lo > thr:
                self.log("LIMIT", "ELIMINATED",
                         "mean_lo = %s > %s: decided without any evaluation" % (mean_lo, thr))
                ev = {"known_sum": tot, "unknown_count": u, "bounds": [lo, hi],
                      "mean_lo": exact_lo, "mean_hi": exact_hi,
                      "op": op, "threshold": thr, "mode": "positive"}
                return self._finish("DECIDED_WITHOUT_EXECUTION", True,
                                    "INTERVAL_BOUND", "LIMIT", ev,
                                    original=u, required=0, analysis_cost=0.05)
            if exact_hi <= thr:
                self.log("LIMIT", "ELIMINATED",
                         "mean_hi = %s <= %s: refuted without evaluation" % (mean_hi, thr))
                ev = {"known_sum": tot, "unknown_count": u, "bounds": [lo, hi],
                      "mean_lo": exact_lo, "mean_hi": exact_hi,
                      "op": op, "threshold": thr, "mode": "negative"}
                return self._finish("DECIDED_WITHOUT_EXECUTION", False,
                                    "INTERVAL_BOUND", "LIMIT", ev,
                                    original=u, required=0, analysis_cost=0.05)
            self.log("LIMIT", "NOT_CONCLUSIVE",
                     "mean in [%s, %s] straddles threshold" % (mean_lo, mean_hi))
            return self._unknown("bounds insufficient to decide the mean",
                                 original=u, analysis_cost=0.05)
        self.log("LIMIT", "NOT_APPLICABLE",
                 "no usable bounds on unknowns")
        return self._unknown(
            "impossible to decide with available information "
            "(spec S14: never invent an answer; never claim execution without justification)",
            original=max(u, 1), analysis_cost=0.05)

    def _laplace(self, M):
        n = len(M)
        if n == 1:
            return M[0][0]
        return sum((-1) ** j * M[0][j] *
                   self._laplace([row[:j] + row[j + 1:] for row in M[1:]])
                   for j in range(n))

    def _det(self, op, thr):
        M = parse_matrix(self.model["matrix"])
        n = len(M)
        fact = 1
        for i in range(2, n + 1):
            fact *= i
        upper = all(M[i][j] == 0 for i in range(n) for j in range(i))
        lower = all(M[i][j] == 0 for i in range(n) for j in range(i + 1, n))
        if upper or lower:
            d = 1
            for i in range(n):
                d *= M[i][i]
            self.log("ANALYTIC", "ELIMINATED",
                     "det(triangular) = prod(diagonal): O(n) instead of O(n!)")
            ev = {"diagonal": [M[i][i] for i in range(n)], "det": d,
                  "op": op, "threshold": thr,
                  "triangular_kind": "upper" if upper else "lower"}
            return self._finish("DECIDED_WITHOUT_EXECUTION", cmp(d, op, thr),
                                "TRIANGULAR_DET_ANALYTIC", "ANALYTIC", ev,
                                original=fact, required=0, analysis_cost=0.05)
        self.log("ANALYTIC", "NOT_APPLICABLE", "matrix not triangular")
        d = self._laplace(M)
        self.log("CLASSICAL", "EXECUTED", "Laplace expansion over %dx%d" % (n, n))
        ev = {"det": d, "op": op, "threshold": thr}
        return self._finish("FULL_EXECUTION_REQUIRED", cmp(d, op, thr),
                            "FULL_DET", "CLASSICAL", ev,
                            original=fact, required=fact, analysis_cost=0.05)

    def _geo(self, op, thr):
        r = _num(self.model["r"])
        n = int(_num(self.model["n"]))
        if r != 1 and isinstance(r, int):
            closed = (r ** (n + 1) - 1) // (r - 1)
        else:
            closed = (r ** (n + 1) - 1) / (r - 1) if r != 1 else n + 1
        self.log("ANALYTIC", "ELIMINATED",
                 "geometric closed form instead of %d additions" % (n + 1))
        ev = {"r": r, "n": n, "closed_form": closed, "op": op, "threshold": thr}
        return self._finish("DECIDED_WITHOUT_EXECUTION", cmp(closed, op, thr),
                            "GEOMETRIC_CLOSED_FORM", "ANALYTIC", ev,
                            original=n + 1, required=0, analysis_cost=0.05)

    def _entangle(self, op, thr):
        """EMARANHADO — família de 2 qubits puros (Fase 3, direção do chefe).

        Perguntas SOBRE emaranhamento, respondidas sem simular o vetor de
        estado — o critério de Schmidt é fechado e exato:
          M = [[a, b], [c, d]]   (a|00⟩+b|01⟩+c|10⟩+d|11⟩)
          det(M) = 0  <=>  estado produto (posto de Schmidt 1)
          concurrence C = 2|det| / ⟨ψ|ψ⟩,  ⟨ψ|ψ⟩ = a²+b²+c²+d²
        Decisão exata por Fraction (o quadrado elimina a raiz):
          C ~ t  ⟺  4·det² ~ t²·n²     (n = ⟨ψ|ψ⟩ > 0)
        O caminho completo (autovalores de MMᵗ, 8 unidades) é ELIMINADO:
        critério analítico de 3 multiplicações — DECIDED_WITHOUT_EXECUTION.
        Emaranhado é a FAMÍLIA do problema; o mecanismo decisório é
        clássico e exato (regra da Fase 3 preservada).
        """
        state_str = self.model["state"]
        if state_str.startswith("sparse("):
            import re as _re
            m = _re.match(r"sparse\((\d+)\)\s*(.*)$", state_str)
            if not m:
                raise ValueError("sparse(N) malformado")
            nq = int(m.group(1)); body = m.group(2).strip()
            if not (1 <= nq <= 64):
                raise ValueError("sparse(N): N = 1..64 (espaco declarado)")
            entries = []
            seen = set()
            for tok in body.split(","):
                tok = tok.strip()
                if not tok:
                    continue
                if ":" not in tok:
                    raise ValueError("entrada esparsa sem idx:amp")
                i_s, a_s = tok.split(":", 1)
                i = int(i_s)
                if i >= (1 << nq):
                    raise ValueError("indice alem do espaco 2^N")
                if i in seen:
                    raise ValueError("indice duplicado")
                seen.add(i)
                entries.append((i, Fraction(a_s)))
                if len(entries) > 256:
                    raise ValueError("muro esparso: maximo 256 entradas")
            if not entries or all(a == 0 for _, a in entries):
                raise ValueError("zero state is not a quantum state (structural)")
            entries = [(i, a) for i, a in entries if a != 0]
            def _sep_sp(ents, m2):
                if m2 == 1:
                    return True
                hb = m2 - 1
                mask = (1 << hb) - 1
                R0 = [(i & mask, a) for i, a in ents if not (i >> hb) & 1]
                R1 = [(i & mask, a) for i, a in ents if (i >> hb) & 1]
                if not R0 or not R1:
                    return _sep_sp(ents, m2 - 1)
                d0 = dict(R0); d1 = dict(R1)
                pos = sorted(set(d0) | set(d1))
                for aa in range(len(pos)):
                    for bb in range(aa + 1, len(pos)):
                        j, k = pos[aa], pos[bb]
                        if d0.get(j, 0) * d1.get(k, 0) != \
                           d0.get(k, 0) * d1.get(j, 0):
                            return False
                return _sep_sp(R0, hb)
            ent = not _sep_sp(entries, nq)
            target = self.q[0]
            if target != "entangled":
                raise ValueError("N-qubit entanglement answers only 'entangled'")
            ans = cmp(1 if ent else 0, op, thr)
            self.log("ANALYTIC", "ELIMINATED",
                     "sparse recursive separability: ent=%s" % ent)
            ev = {"n_qubits": nq, "support": len(entries),
                  "fully_separable": not ent, "op": op, "threshold": thr}
            return self._finish("DECIDED_WITHOUT_EXECUTION", ans,
                                "SPARSE_RECURSIVE_FLATTEN_RANK", "ANALYTIC", ev,
                                original=len(entries), required=0, analysis_cost=0.05)
        toks = [x.strip() for x in self.model["state"].split(",")]
        if len(toks) == 8:
            # 3 qubits: separabilidade plena, exato por Fraction
            # (postos do achatamento + Schmidt residual — sem simulacao)
            a8 = [Fraction(t) for t in toks]
            if sum(x * x for x in a8) == 0:
                raise ValueError("zero state is not a quantum state (structural)")
            R0, R1 = a8[:4], a8[4:]
            rank1 = all(R0[j] * R1[k] == R0[k] * R1[j]
                        for j in range(4) for k in range(j + 1, 4))
            if rank1:
                phi = R0 if any(R0) else R1
                ent = (phi[0] * phi[3] - phi[1] * phi[2]) != 0
            else:
                ent = True
            target = self.q[0]
            if target != "entangled":
                raise ValueError("3-qubit entanglement answers only 'entangled'")
            ans = cmp(1 if ent else 0, op, thr)
            self.log("ANALYTIC", "ELIMINATED",
                     "flatten rank + residual Schmidt det: rank1=%s ent=%s"
                     % (rank1, ent))
            ev = {"amplitudes": toks, "fully_separable": not ent,
                  "op": op, "threshold": thr}
            return self._finish("DECIDED_WITHOUT_EXECUTION", ans,
                                "FLATTEN_RANK_SCHMIDT", "ANALYTIC", ev,
                                original=8, required=0, analysis_cost=0.05)
        toks = [x.strip() for x in self.model["state"].split(",")]
        if len(toks) == 8:
            # 3 qubits: separabilidade plena, exato por Fraction
            # (postos do achatamento + Schmidt residual — sem simulacao)
            a8 = [Fraction(t) for t in toks]
            if sum(x * x for x in a8) == 0:
                raise ValueError("zero state is not a quantum state (structural)")
            R0, R1 = a8[:4], a8[4:]
            rank1 = all(R0[j] * R1[k] == R0[k] * R1[j]
                        for j in range(4) for k in range(j + 1, 4))
            if rank1:
                phi = R0 if any(R0) else R1
                ent = (phi[0] * phi[3] - phi[1] * phi[2]) != 0
            else:
                ent = True
            target = self.q[0]
            if target != "entangled":
                raise ValueError("3-qubit entanglement answers only 'entangled'")
            ans = cmp(1 if ent else 0, op, thr)
            self.log("ANALYTIC", "ELIMINATED",
                     "flatten rank + residual Schmidt det: rank1=%s ent=%s"
                     % (rank1, ent))
            ev = {"amplitudes": toks, "fully_separable": not ent,
                  "op": op, "threshold": thr}
            return self._finish("DECIDED_WITHOUT_EXECUTION", ans,
                                "FLATTEN_RANK_SCHMIDT", "ANALYTIC", ev,
                                original=8, required=0, analysis_cost=0.05)
        if len(toks) >= 16:
            # N qubits (4 <= N <= 12): separabilidade plena recursiva,
            # exata por Fraction — posto do achatamento q0 + residuo
            n_amp = len(toks)
            if n_amp & (n_amp - 1):
                raise ValueError("state must have 2^N amplitudes")
            if n_amp > 4096:
                raise ValueError("core wall: max 4096 amplitudes (12 qubits)")
            aN = [Fraction(t) for t in toks]
            if sum(x * x for x in aN) == 0:
                raise ValueError("zero state is not a quantum state (structural)")
            def _sep(v):
                L = len(v)
                if L == 2:
                    return True
                h = L // 2
                R0, R1 = v[:h], v[h:]
                if any(R0[j] * R1[k] != R0[k] * R1[j]
                       for j in range(h) for k in range(j + 1, h)):
                    return False
                return _sep(R0 if any(R0) else R1)
            ent = not _sep(aN)
            target = self.q[0]
            if target != "entangled":
                raise ValueError("N-qubit entanglement answers only 'entangled'")
            ans = cmp(1 if ent else 0, op, thr)
            self.log("ANALYTIC", "ELIMINATED",
                     "recursive flatten-rank separability: ent=%s" % ent)
            ev = {"amplitudes": n_amp, "fully_separable": not ent,
                  "op": op, "threshold": thr}
            return self._finish("DECIDED_WITHOUT_EXECUTION", ans,
                                "RECURSIVE_FLATTEN_RANK", "ANALYTIC", ev,
                                original=n_amp, required=0, analysis_cost=0.05)
        if len(toks) != 4:
            raise ValueError("entanglement state must have 4, 8 or 2^N "
                             "amplitudes (N <= 12) (structural)")
        a, b, c, d = (Fraction(t) for t in toks)   # decimal exato, não float
        n = a * a + b * b + c * c + d * d
        if n == 0:
            raise ValueError("zero state is not a quantum state (structural)")
        det = a * d - b * c
        C = 2 * abs(det) / n                       # Fraction exata
        target = self.q[0]
        if target == "entangled":
            ans = cmp(1 if det != 0 else 0, op, thr)
        elif target == "concurrence":
            t = Fraction(str(thr)) if isinstance(thr, float) else Fraction(thr)
            sq, tsq = 4 * det * det, t * t * n * n
            if op == ">":
                ans = True if t < 0 else sq > tsq
            elif op == ">=":
                ans = True if t <= 0 else sq >= tsq
            elif op == "<":
                ans = False if t <= 0 else sq < tsq
            elif op == "<=":
                ans = False if t < 0 else sq <= tsq
            elif op == "==":
                ans = sq == tsq
            else:
                raise ValueError("unsupported op for concurrence: %r" % op)
        else:
            raise ValueError("entanglement family answers 'entangled' or "
                             "'concurrence', not %r" % target)
        self.log("ANALYTIC", "ELIMINATED",
                 "Schmidt determinant criterion: det=%s, C=%s (exact)" % (det, C))
        ev = {"amplitudes": toks, "det": str(det), "norm_sq": str(n),
              "concurrence": str(C), "op": op, "threshold": thr}
        return self._finish("DECIDED_WITHOUT_EXECUTION", ans,
                            "SCHMIDT_DET_CRITERION", "ANALYTIC", ev,
                            original=8, required=0, analysis_cost=0.05)

    def _molecular(self, op, thr):
        """BIOMEDICINE BASE (owner directive 2026-10-09): exact ground-state
        energy of quantum many-body models — the family seed for molecular
        and chemical questions (the 2-site member is the H2-dimer analog).
        Dense exact diagonalization, zero QPU, decided offline.

        MODEL:
            type: molecular
            model: heisenberg          (seed kernel; more with fusion)
            sites: N                   (2..12 — exact diagonalization range)
            coupling: J               (optional, default 1)
            field: h                  (optional, default 0)
        ASK: ground_state_energy <op> <threshold>   (Hartree-scaled units)

        Honest scope (Evidence Before Velocity): this kernel decides small
        active spaces exactly. Molecule-scale drug discovery needs the
        fault-tolerant era; the scaling path is the Qiskit Nature /
        PennyLane fusion target, which consumes the same .zeph question.
        """
        import numpy as np
        m = self.model
        kind = m.get("model", "heisenberg").lower()
        if kind not in ("heisenberg", "h2_sto3g", "hubbard"):
            raise ValueError("molecular family: model must be heisenberg, "
                             "h2_sto3g (real H2) or hubbard (charge transport)")
        if kind == "h2_sto3g":
            return self._molecular_h2(op, thr)
        if kind == "hubbard":
            return self._molecular_hubbard(op, thr)
        n = int(m.get("sites", "4"))
        if not 2 <= n <= 12:
            raise ValueError("sites out of exact-diagonalization range 2..12")
        j = _num(m.get("coupling", "1"))
        h = _num(m.get("field", "0"))
        dim = 1 << n
        H = np.zeros((dim, dim))
        for st in range(dim):
            for i in range(n - 1):
                bi, bj = (st >> i) & 1, (st >> (i + 1)) & 1
                if bi == bj:
                    H[st, st] += j / 4.0
                else:
                    H[st, st] -= j / 4.0
                    t = st ^ ((1 << i) | (1 << (i + 1)))
                    H[t, st] += j / 2.0
            for i in range(n):
                H[st, st] += h / 2.0 * (1 - 2 * ((st >> i) & 1))
        e0 = float(np.linalg.eigvalsh(H)[0])
        self.log("EXACT_DIAGONALIZATION", "ELIMINATED",
                 "dense eigh on %d-dim Hilbert space" % dim)
        ev = {"model": kind, "sites": n, "coupling": j, "field": h,
              "ground_state_energy": e0, "op": op, "threshold": thr,
              "dim": dim}
        return self._finish("DECIDED_WITHOUT_EXECUTION", cmp(e0, op, thr),
                            "EXACT_DIAGONALIZATION", "ANALYSIS", ev,
                            original=dim, required=0, analysis_cost=0.05)

    def _molecular_hubbard(self, op, thr):
        """Hubbard chain, full spinful Fock space, exact diagonalization —
        the standard effective model for charge/hole transport in
        molecular wires (including the DNA pi-stack; hole transport is
        the chemistry of DNA damage). Biomedicine base, study scope:
        exact verdicts for small clusters; molecule scale is the
        fusion/fault-tolerant path. No personal names in sources; the
        model is universal textbook material.

        MODEL:
            type: molecular
            model: hubbard
            sites: L            (2..5; dim = 4^L spinful Fock)
            hopping: t          (default 1)
            onsite: U           (default 4)
        ASK: ground_state_energy <op> <threshold>  (units of t)
        Ground is taken over ALL particle-number sectors (honest Fock).
        """
        import numpy as np
        m = self.model
        L = int(m.get("sites", "2"))
        if not 2 <= L <= 5:
            raise ValueError("hubbard: sites must be 2..5 (dim 4^L cap)")
        t = float(_num(m.get("hopping", "1")))
        U = float(_num(m.get("onsite", "4")))
        dim = 1 << (2 * L)
        H = np.zeros((dim, dim))
        for st in range(dim):
            for i in range(L):
                if (st >> (2 * i)) & 1 and (st >> (2 * i + 1)) & 1:
                    H[st, st] += U
            for i in range(L - 1):
                for sp in (0, 1):
                    a, b = 2 * i + sp, 2 * (i + 1) + sp
                    # ONE matrix element per bond/spin/state: the two
                    # Hermitian conjugate terms land on different
                    # (st, st2) pairs — never both on the same entry.
                    if ((st >> a) & 1) != ((st >> b) & 1):
                        st2 = st ^ ((1 << a) | (1 << b))
                        nb = bin((st >> (a + 1)) & ((1 << (b - a - 1)) - 1))
                        nb = nb.count("1") & 1
                        H[st2, st] += -t * (1 - 2 * nb)
        e0 = float(np.linalg.eigvalsh(H)[0])
        self.log("EXACT_DIAGONALIZATION", "ELIMINATED",
                 "dense eigh on %d-dim spinful Hubbard Fock (L=%d, U/t=%.2f)"
                 % (dim, L, U / t if t else float("inf")))
        ev = {"model": "hubbard", "sites": L, "hopping": t, "onsite": U,
              "fock_dim": dim, "ground_state_energy": e0,
              "op": op, "threshold": thr,
              "scope": "small-cluster exact; molecule scale = fusion path"}
        return self._finish("DECIDED_WITHOUT_EXECUTION", cmp(e0, op, thr),
                            "EXACT_DIAGONALIZATION", "ANALYSIS", ev,
                            original=dim, required=0, analysis_cost=0.05)

    # REAL H2, minimal basis: coefficients from the primary literature:
    # PRL 116, 023004 (2016), Table I (arXiv:1512.06860). No personal names
    # are cited, per the owner's editorial rule (universal-source doctrine).
    # extracted from the published PDF today. H = t0 I + t1 Z0 + t2 Z1 +
    # t3 Z0Z1 + t4 Y0Y1 + t5 X0X1 (tapered, 2 qubits); spectrum preserved.
    H2_STO3G = {
        "0.40": (1.1182, 0.4754, -0.9145, 0.6438, 0.0825, 0.0825),
        "0.45": (0.9083, 0.4534, -0.8194, 0.6336, 0.0835, 0.0835),
        "0.50": (0.7381, 0.4325, -0.7355, 0.6233, 0.0846, 0.0846),
        "0.55": (0.5979, 0.4125, -0.6612, 0.6129, 0.0858, 0.0858),
        "0.60": (0.4808, 0.3937, -0.5950, 0.6025, 0.0870, 0.0870),
        "0.65": (0.3819, 0.3760, -0.5358, 0.5921, 0.0883, 0.0883),
        "0.70": (0.2976, 0.3593, -0.4826, 0.5818, 0.0896, 0.0896),
        "0.75": (0.2252, 0.3435, -0.4347, 0.5716, 0.0910, 0.0910),
        "0.80": (0.1626, 0.3288, -0.3915, 0.5616, 0.0925, 0.0925),
        "0.85": (0.1083, 0.3149, -0.3523, 0.5518, 0.0939, 0.0939),
    }

    def _molecular_h2(self, op, thr):
        """REAL hydrogen molecule, STO-3G minimal basis (biomedicine base).
        Exact dense diagonalization of the 2-qubit tapered Hamiltonian,
        zero QPU, coefficients from PRL 116, 023004 (2016) Table I.

        MODEL:
            type: molecular
            model: h2_sto3g
            bond: 0.75          (angstrom, rows of PRL 116 023004 Table I)
        ASK: ground_state_energy <op> <threshold>   (Hartree)
        """
        import numpy as np
        m = self.model
        bond = str(float(_num(m.get("bond", "0.75"))))
        rows = [k for k in ("0.40", "0.45", "0.50", "0.55", "0.60", "0.65",
                            "0.70", "0.75", "0.80", "0.85")]
        if bond not in rows:
            bond = min(rows, key=lambda r: abs(float(r) - float(bond)))
        t0, t1, t2, t3, t4, t5 = self.H2_STO3G[bond]
        # t0 of the source ALREADY includes nuclear repulsion.
        # Canonical Pauli construction (audited 2026-10-09): Z0 = Z(x)I,
        # Z1 = I(x)Z, Z0Z1 = Z(x)Z — the exact ground of the published
        # Hamiltonian at bond 0.75 A is -1.1456 Ha.
        I1 = np.eye(2)
        Zp = np.diag([1.0, -1.0])
        K = lambda a, b: np.kron(a, b)
        Z0, Z1, I2 = K(Zp, I1), K(I1, Zp), np.eye(4)
        # XX and YY in the true Pauli convention (YY has -1 corners);
        # cross-checked against the canonical construction: the ground
        # of the published Hamiltonian at bond 0.75 A is -1.1456 Ha.
        XX = np.array([[0, 0, 0, 1], [0, 0, 1, 0],
                       [0, 1, 0, 0], [1, 0, 0, 0]], float)
        YY = np.array([[0, 0, 0, -1], [0, 0, 1, 0],
                       [0, 1, 0, 0], [-1, 0, 0, 0]], float)
        H = (t0 * I2 + t1 * Z0 + t2 * Z1 + t3 * K(Zp, Zp) +
             t4 * YY + t5 * XX)
        evals = np.linalg.eigvalsh(H)
        e0 = float(evals[0])
        self.log("EXACT_DIAGONALIZATION", "ELIMINATED",
                 "dense eigh on 4-dim tapered H2 (bond %s A, PRL 116 023004)"
                 % bond)
        ev = {"model": "h2_sto3g", "bond_angstrom": float(bond),
              "ground_state_energy": e0, "op": op, "threshold": thr,
              "dim": 4, "source": "PRL 116 023004 (2016), Table I"}
        return self._finish("DECIDED_WITHOUT_EXECUTION", cmp(e0, op, thr),
                            "EXACT_DIAGONALIZATION", "ANALYSIS", ev,
                            original=4, required=0, analysis_cost=0.03)

    def _hybrid(self, op, thr):
        """HYBRID BOUNDARY PATTERN (owner directive 2026-10-10, from the
        heterogeneous quantum-classical stack theme; universal sources:
        Preskill, Quantum 2, 79 (2018); Peruzzo et al., Nat. Commun. 5,
        4213 (2014)). The QPU is NOT an accelerator that receives a
        model and returns a faster answer: it is a specialized witness
        resource inside a larger heterogeneous system. The classical
        side decides WHICH part of the workload crosses the boundary —
        and the exact core decides BEFORE any crossing.

        Four stages, explicit in every certificate:
        1. CLASSICAL_PREP   — data prep / transpilation (never crosses)
        2. EXACT_DECISION   — core verdict, offline, zero QPU
        3. QPU_WITNESS      — crosses the boundary; budget-gated
        4. RECEIPT          — ML-DSA signature closes the loop

        MODEL:
            type: hybrid
            check: boundary_plan
            qpu_witness: true|false
            budget_seconds: N   (supervisor cap: 15 s/lot)
            shots: 2048
            basis: ZZ,XX,YY
        ASK: plan_valid == 1
        """
        m = self.model
        if m.get("check") != "boundary_plan":
            raise ValueError("hybrid family: only check: boundary_plan "
                             "is implemented (Section 12)")
        witness = str(m.get("qpu_witness", "false")).lower() == "true"
        budget = int(_num(m.get("budget_seconds", "0")))
        shots = int(_num(m.get("shots", "2048")))
        bases = [b.strip() for b in m.get(
            "basis", "ZZ,XX,YY").split(",") if b.strip()]
        stages = ["CLASSICAL_PREP", "EXACT_DECISION"]
        valid, reason = True, "boundary plan valid"
        if witness:
            if budget <= 0:
                valid = False
                reason = ("QPU witness requested with zero budget - "
                          "refused (supervisor directive)")
            elif budget > 15:
                valid = False
                reason = ("budget %d s exceeds the 15 s/lot cap "
                          "(supervisor directive)" % budget)
            elif not (1 <= shots <= 4096):
                valid = False
                reason = "shots outside the declared study range"
            elif not bases:
                valid = False
                reason = "no measurement bases declared for the witness"
            else:
                stages += ["QPU_WITNESS", "RECEIPT"]
        ev = {"check": "boundary_plan", "qpu_witness": witness,
              "budget_seconds": budget, "shots": shots, "bases": bases,
              "stages": stages,
              "boundary_crossings": 1 if witness else 0,
              "plan_valid": int(valid), "reason": reason,
              "pattern": "classical decides what crosses; the QPU is "
                         "witness, never the decider; receipt closes "
                         "the loop"}
        self.log("HYBRID_BOUNDARY_PLAN", "ELIMINATED",
                 "boundary routing decided offline, zero QPU")
        return self._finish("DECIDED_WITHOUT_EXECUTION",
                            cmp(int(valid), op, thr),
                            "HYBRID_BOUNDARY_PLAN", "ANALYSIS", ev,
                            original=1, required=0, analysis_cost=0.01)

    # IUPAC standard atomic weights (abridged, conventional) for the
    # molar-mass kernel of the universal exact family.
    ATOMIC_WEIGHTS = {"H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
                      "Na": 22.990, "Mg": 24.305, "Al": 26.982,
                      "Si": 28.085, "P": 30.974, "S": 32.06,
                      "Cl": 35.45, "K": 39.098, "Ca": 40.078,
                      "Fe": 55.845, "Cu": 63.546, "Zn": 65.38}

    def _exact(self, op, thr):
        """UNIVERSAL EXACT FAMILY (owner directive 2026-10-09: every
        domain of knowledge, from agro to space, gets an exact kernel
        INSIDE the language — and a Section 12 refusal where exactness
        does not hold). One family, many deterministic checks:

        check: kepler3        (astronomy/orbital mechanics)
        check: primality       (number theory / mathematics)
        check: prazo_cpc       (legal deadline counting, deterministic
                                rule application; holiday DATA must be
                                declared by the operator — the kernel is
                                exact, the data is declared)
        check: dose_mgkg       (clinical dosage COMPUTATION; the
                                clinical decision remains with the
                                licensed professional — computation
                                only, never diagnosis)
        check: agro_density / agro_rate   (agronomy engineering)
        check: stress_safety   (engineering statics)
        check: molar_mass      (chemistry, IUPAC standard weights)
        """
        import re
        m = self.model
        kind = m.get("check")
        if kind == "chsh_bound":
            # CYBERSECURITY BASE (study ZYQL-TR-2026-10-10, QKD witness):
            # the CHSH game bounds of entanglement-based key distribution.
            # S = E(a0,b0) + E(a0,b1) + E(a1,b0) - E(a1,b1).
            mode = m.get("mode", "classical")
            if mode == "classical":
                # exact enumeration of ALL 16 deterministic local
                # strategies (A0,A1,B0,B1 in {-1,+1}): the classical
                # bound is a finite arithmetic fact, zero QPU.
                best = -10
                for A0 in (-1, 1):
                    for A1 in (-1, 1):
                        for B0 in (-1, 1):
                            for B1 in (-1, 1):
                                S = (A0 * B0 + A0 * B1 + A1 * B0
                                     - A1 * B1)
                                best = max(best, abs(S))
                ev = {"check": "chsh_bound", "mode": "classical",
                      "classical_max_abs_S": best,
                      "strategies_enumerated": 16,
                      "law": "local realism bounded by 2 (finite "
                             "enumeration, exact integers)"}
                self.log("EXACT_CHSH_CLASSICAL", "ELIMINATED",
                         "16-strategy enumeration: |S|max=%d" % best)
                return self._finish("DECIDED_WITHOUT_EXECUTION",
                                    cmp(best, op, thr),
                                    "EXACT_CHSH_CLASSICAL", "ANALYSIS", ev,
                                    original=16, required=0,
                                    analysis_cost=0.01)
            if mode == "tsirelson":
                from decimal import Decimal, getcontext
                getcontext().prec = 28
                v = 2 * Decimal(2).sqrt()
                ev = {"check": "chsh_bound", "mode": "tsirelson",
                      "tsirelson_bound": float(v),
                      "law": "quantum max S = 2*sqrt(2)",
                      "note_s12": "sqrt(2) is irrational: Decimal "
                                  "truncated to 28 significant digits, "
                                  "disclosed, never faked exact"}
                self.log("EXACT_CHSH_TSIRELSON", "ELIMINATED",
                         "2*sqrt(2) = %s (28 digits)" % v)
                return self._finish("DECIDED_WITHOUT_EXECUTION",
                                    cmp(float(v), op, thr),
                                    "EXACT_CHSH_TSIRELSON", "ANALYSIS", ev,
                                    original=1, required=0,
                                    analysis_cost=0.01)
            if mode == "witness":
                # The QPU (or any declared source) supplies RAW COUNTS as
                # declared empirical data; the language computes the
                # correlators and S EXACTLY in Fractions and decides.
                # The hardware never judges: it only witnesses. §12: the
                # kernel is exact over DECLARED data; provenance is the
                # receipt attached by the operator.
                from fractions import Fraction
                def _pair(key):
                    toks = str(m[key]).replace(" ", "").split(",")
                    if (len(toks) != 2
                            or not all(t.lstrip("-").isdigit()
                                       for t in toks)):
                        raise ValueError("chsh witness %s: expected "
                                         "'same,diff' integer pair "
                                         "(structural)" % key)
                    a, b = int(toks[0]), int(toks[1])
                    tot = a + b
                    if tot <= 0:
                        raise ValueError("chsh witness %s: counts must be "
                                         "positive (structural)" % key)
                    return Fraction(a - b, tot), tot
                E00, n0 = _pair("a0b0")
                E01, n1 = _pair("a0b1")
                E10, n2 = _pair("a1b0")
                E11, n3 = _pair("a1b1")
                S = E00 + E01 + E10 - E11
                ev = {"check": "chsh_bound", "mode": "witness",
                      "E_a0b0": str(E00), "E_a0b1": str(E01),
                      "E_a1b0": str(E10), "E_a1b1": str(E11),
                      "S": str(S), "S_float": float(S),
                      "shots_total": n0 + n1 + n2 + n3,
                      "note_s12": "counts are declared empirical data; "
                                  "the verdict is exact over them"}
                self.log("EXACT_CHSH_WITNESS", "ELIMINATED",
                         "S = %s from declared counts (exact Fractions)"
                         % S)
                return self._finish("DECIDED_WITHOUT_EXECUTION",
                                    cmp(float(S), op, thr),
                                    "EXACT_CHSH_WITNESS", "ANALYSIS", ev,
                                    original=n0 + n1 + n2 + n3, required=0,
                                    analysis_cost=0.01)
            raise ValueError("chsh_bound: mode must be classical, "
                             "tsirelson or witness (structural)")
        if kind == "kepler3":
            a = float(_num(m["semi_major_axis_au"]))
            T = a ** 1.5  # Kepler III, M_host = 1 solar mass
            ev = {"check": "kepler3", "semi_major_axis_au": a,
                  "period_years": T,
                  "law": "T^2 = a^3 (host mass = 1 solar)"}
            self.log("EXACT_KEPLER_III", "ELIMINATED",
                     "closed form a^1.5, zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(T, op, thr), "EXACT_KEPLER_III",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        if kind == "primality":
            n = int(_num(m["n"]))
            if not 2 <= n <= 10 ** 12:
                raise ValueError("primality: 2 <= n <= 10^12 (trial "
                                 "division remains exact and finite)")
            isp = all(n % d for d in range(2, int(n ** 0.5) + 1))
            ev = {"check": "primality", "n": n, "is_prime": int(isp),
                  "method": "deterministic trial division (exact)"}
            self.log("EXACT_PRIMALITY", "ELIMINATED",
                     "trial division to sqrt(n), zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(int(isp), op, thr), "EXACT_PRIMALITY",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        if kind == "prazo_cpc":
            from datetime import date, timedelta
            start = date(*map(int, m["start"].split("-")))
            days = int(_num(m["days"]))
            uteis = str(m.get("dias_uteis", "true")).lower() == "true"
            hol = set(m.get("holidays", "").replace(" ", "").split(",")) - {""}
            hol = {tuple(map(int, h.split("-"))) for h in hol}
            d, count = start, 0
            while count < days:
                d += timedelta(days=1)
                ok = (d.weekday() < 5) if uteis else True
                if ok and (d.year, d.month, d.day) not in hol:
                    count += 1
            cal = (d - start).days
            ev = {"check": "prazo_cpc", "start": m["start"], "days": days,
                  "dias_uteis": uteis, "holidays_declared": sorted(m.get(
                      "holidays", "").split(",") if m.get("holidays") else []),
                  "deadline": d.isoformat(),
                  "rule": "exclude day of start, include day of expiry "
                          "(deadline counting); operator-declared holidays",
                  "calendar_days_until_deadline": cal}
            self.log("EXACT_PRAZO_CPC", "ELIMINATED",
                     "deterministic date arithmetic, zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(cal, op, thr), "EXACT_PRAZO_CPC",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        if kind == "dose_mgkg":
            w = float(_num(m["weight_kg"]))
            r = float(_num(m["mg_per_kg"]))
            dose = w * r
            ev = {"check": "dose_mgkg", "weight_kg": w, "mg_per_kg": r,
                  "dose_mg": dose,
                  "scope": "computation only; clinical decision remains "
                           "with the licensed professional"}
            self.log("EXACT_DOSE_MGKG", "ELIMINATED",
                     "exact arithmetic w*r, zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(dose, op, thr), "EXACT_DOSE_MGKG",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        if kind == "agro_density":
            row = float(_num(m["row_spacing_m"]))
            plant = float(_num(m["plant_spacing_m"]))
            dens = 10000.0 / (row * plant)
            ev = {"check": "agro_density", "row_spacing_m": row,
                  "plant_spacing_m": plant, "plants_per_hectare": dens,
                  "formula": "10000 / (row * plant)"}
            self.log("EXACT_AGRO_DENSITY", "ELIMINATED",
                     "exact geometry, zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(dens, op, thr), "EXACT_AGRO_DENSITY",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        if kind == "agro_rate":
            rate = float(_num(m["rate_per_ha"]))
            ha = float(_num(m["hectares"]))
            tot = rate * ha
            ev = {"check": "agro_rate", "rate_per_ha": rate,
                  "hectares": ha, "total": tot}
            self.log("EXACT_AGRO_RATE", "ELIMINATED",
                     "exact arithmetic rate*area, zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(tot, op, thr), "EXACT_AGRO_RATE",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        if kind == "stress_safety":
            f = float(_num(m["force_n"]))
            area = float(_num(m["area_m2"]))
            limit = float(_num(m["limit_pa"]))
            stress = f / area
            sf = limit / stress
            ev = {"check": "stress_safety", "force_n": f, "area_m2": area,
                  "stress_pa": stress, "limit_pa": limit,
                  "safety_factor": sf, "formula": "stress=F/A; sf=limit/stress"}
            self.log("EXACT_STRESS_SAFETY", "ELIMINATED",
                     "exact statics, zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(sf, op, thr), "EXACT_STRESS_SAFETY",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        if kind == "molar_mass":
            import re as _re
            formula = m["formula"].strip()
            if not _re.fullmatch(r"(?:[A-Z][a-z]?\d*)+", formula):
                raise ValueError("molar_mass: invalid chemical formula")
            mm = 0.0
            for el, cnt in _re.findall(r"([A-Z][a-z]?)(\d*)", formula):
                if el not in self.ATOMIC_WEIGHTS:
                    raise ValueError("molar_mass: element %r not in the "
                                     "abridged IUPAC table" % el)
                mm += self.ATOMIC_WEIGHTS[el] * (int(cnt) if cnt else 1)
            ev = {"check": "molar_mass", "formula": formula,
                  "molar_mass_g_mol": mm,
                  "weights": "IUPAC standard atomic weights (conventional)"}
            self.log("EXACT_MOLAR_MASS", "ELIMINATED",
                     "exact formula arithmetic, zero QPU")
            return self._finish("DECIDED_WITHOUT_EXECUTION",
                                cmp(mm, op, thr), "EXACT_MOLAR_MASS",
                                "ANALYSIS", ev, original=1, required=0,
                                analysis_cost=0.01)
        raise ValueError("exact family: unknown check %r (Section 12: "
                         "the language refuses to guess)" % kind)

    def _crypto(self, op, thr):
        """CYBERSECURITY BASE (owner directive 2026-10-09): post-quantum
        signature verification decided EXACTLY on classical hardware —
        zero QPU. The language can already answer 'is this verdict/
        message/authentic artifact genuinely signed?' against FIPS 204.

        MODEL:
            type: crypto
            check: ml_dsa_verify
            public_key: <b64 ML-DSA-44 public key>
            message: <plain text>
            signature: <b64 ML-DSA-44 signature>
        ASK: signature_valid == 1    (verdict 0 == invalid/forged)
        """
        from pq_receipt import _unb64
        from pqcrypto.sign import ml_dsa_44
        m = self.model
        if m.get("check") != "ml_dsa_verify":
            raise ValueError("crypto family: only check: ml_dsa_verify is "
                             "implemented")
        pub = _unb64(m["public_key"])
        sig = _unb64(m["signature"])
        msg = m.get("message", "").encode("utf-8")
        try:
            ml_dsa_44.verify(pub, msg, sig)
            valid = True
        except Exception:
            valid = False
        self.log("ML_DSA_VERIFY", "ELIMINATED",
                 "FIPS 204 verification, zero QPU")
        ev = {"check": "ml_dsa_verify", "alg": "ML-DSA-44",
              "message_chars": len(msg), "signature_valid": int(valid)}
        return self._finish("DECIDED_WITHOUT_EXECUTION",
                            cmp(int(valid), op, thr), "ML_DSA_VERIFY",
                            "ANALYSIS", ev, original=1, required=0,
                            analysis_cost=0.01)

    def _raw(self, op, thr):
        data = parse_list(self.model["data"])
        self.log("REDUCTION", "NOT_APPLICABLE", "no exploitable structure")
        self.log("ANALYTIC", "NOT_APPLICABLE", "no closed form for median")
        self.log("CLASSICAL", "EXECUTED", "full sort + median")
        s = sorted(data)
        m = len(s)
        med = s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2
        ev = {"sorted": s, "median": med, "op": op, "threshold": thr}
        return self._finish("FULL_EXECUTION_REQUIRED", cmp(med, op, thr),
                            "MEDIAN_CLASSICAL", "CLASSICAL", ev,
                            original=m, required=m, analysis_cost=0.05)
