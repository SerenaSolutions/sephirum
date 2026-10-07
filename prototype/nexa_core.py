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
        toks = [x.strip() for x in self.model["state"].split(",")]
        if len(toks) != 4:
            raise ValueError("entanglement state must have 4 amplitudes")
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
