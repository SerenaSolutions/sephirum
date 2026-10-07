"""
Independent certificate checker for NEXA v0.1 (spec S23 item 10)
================================================================
Soundness contract: a certificate is accepted ONLY if this module can
re-derive the claimed decision from the ORIGINAL NEXA source, using its
own recomputation (and, where possible, a DIFFERENT method than the engine).
The engine never audits itself. Tampered evidence must be rejected.
"""
import hashlib
import json
from fractions import Fraction

from decision_kernel import check_hash

from nexa_core import (
    parse_list, parse_matrix, parse_question, cmp, safe_eval, _num,
    _parse_unknown,
)


def verify(blocks, cert):
    """Return (ok: bool, reason: str)."""
    # 0. integrity: certificate must refer to this exact source
    h = hashlib.sha256(json.dumps(blocks, sort_keys=True).encode()).hexdigest()
    if h != cert.get("INPUT_HASH"):
        return False, "REJECT: input hash mismatch (certificate/source divergence)"

    # 0.5 integridade criptográfica: o hash canônico sela o certificado
    # inteiro (evidência, rastro, custos, status, resposta). Sem o hash, ou
    # com hash quebrado, o certificado é rejeitado ANTES de qualquer análise.
    if not check_hash(cert):
        return False, "REJECT: certificate hash mismatch (tampered certificate)"

    target, op, thr = parse_question(blocks["ASK"]["question"])
    model = blocks["MODEL"]
    ev = cert.get("EVIDENCE", {})
    k = cert.get("KERNEL")
    answer = cert.get("ANSWER")
    status = cert.get("STATUS")
    # 0.6 kernel de primeira classe: veredito trivalente consistente
    dk = cert.get("DECISION_KERNEL", {})
    from zerum import STATUS_TO_TRIT
    if dk.get("method") != cert.get("KERNEL"):
        return False, "REJECT: kernel method diverges from certificate kernel"
    if dk.get("verdict") != STATUS_TO_TRIT.get(status, ("?",))[0]:
        return False, "REJECT: kernel verdict inconsistent with status"
    if dk.get("verdict") == "Z" and answer is not None:
        return False, "REJECT: Z verdict must claim no answer"
    if dk.get("verdict") in (0, 1) and not isinstance(answer, bool):
        return False, "REJECT: collapsed verdict must carry a boolean answer"


    if k == "NONE":  # UNKNOWN claims nothing; nothing to verify
        return (status == "UNKNOWN" and answer is None), \
            "ok: UNKNOWN claims nothing to verify"

    if k == "CONSTANT_FOLD":
        try:
            val = safe_eval(model["expr"])
        except Exception:
            return False, "REJECT: expression not independently foldable"
        if val != ev.get("value"):
            return False, "REJECT: folded value mismatch"
        if cmp(val, op, thr) != answer:
            return False, "REJECT: answer inconsistent with recomputed value"
        return True, "ok: identity independently recomputed"

    if k == "MONOTONE_EARLY_STOP":
        if model.get("assumption") != "terms_nonnegative":
            return False, "REJECT: monotonicity assumption not declared in source"
        terms = parse_list(model["terms"])
        w = ev.get("witness_terms", [])
        if w != terms[:len(w)]:
            return False, "REJECT: witness is not a prefix of the declared terms"
        s = sum(w)
        if s != ev.get("witness_sum"):
            return False, "REJECT: witness sum mismatch"
        if not cmp(s, op, thr):
            return False, "REJECT: witness sum does not satisfy the question"
        if any(t < 0 for t in terms[len(w):]):
            return False, "REJECT: monotonicity broken (negative eliminated term)"
        if answer is not True or status != "DECIDED_BY_REDUCTION":
            return False, "REJECT: bad status/answer pair"
        return True, "ok: monotone early stop independently verified from source"

    if k == "INTERVAL_BOUND":
        if model.get("type") == "threshold_sum":
            terms = parse_list(model["terms"])
            if not model.get("unknown"):
                return False, "REJECT: no unknown declared"
            name, lo, hi = _parse_unknown(model["unknown"])
            base = sum(terms)
            if ev.get("base_sum") != base or ev.get("bounds") != [lo, hi]:
                return False, "REJECT: bound evidence mismatch"
            if answer is True:
                if not base + lo > thr:
                    return False, "REJECT: lower bound does not decide positively"
            elif answer is False:
                if not base + hi <= thr:
                    return False, "REJECT: upper bound does not decide negatively"
            else:
                return False, "REJECT: interval bound with non-boolean answer"
            if status != "DECIDED_WITHOUT_EXECUTION" or ev.get("required_terms", 1) != 0:
                return False, "REJECT: bounds decision must require zero execution"
            return True, "ok: interval bound independently recomputed"
        if model.get("type") == "mean_partial":
            known = parse_list(model["known"])
            u = int(_num(model["unknown_count"]))
            lo, hi = [ _num(x) for x in model["bounds"].split("..") ]
            tot = sum(known)
            N = len(known) + u
            mean_lo = (tot + u * lo) / N
            mean_hi = (tot + u * hi) / N
            if ev.get("mean_lo") != mean_lo or ev.get("mean_hi") != mean_hi:
                return False, "REJECT: mean interval mismatch"
            exact_lo = Fraction(tot + u * lo, N)
            exact_hi = Fraction(tot + u * hi, N)
            if answer is True and not exact_lo > thr:
                return False, "REJECT: lower mean bound does not decide (exact arithmetic)"
            if answer is False and not exact_hi <= thr:
                return False, "REJECT: upper mean bound does not refute (exact arithmetic)"
            return True, "ok: mean interval independently recomputed"
        return False, "REJECT: INTERVAL_BOUND on unexpected model type"

    if k == "RESIDUAL_EVAL":
        terms = parse_list(model["terms"])
        name, lo, hi = _parse_unknown(model["unknown"])
        base = sum(terms)
        if ev.get("base_sum") != base or ev.get("bounds") != [lo, hi]:
            return False, "REJECT: residual evidence mismatch"
        # residual must be JUSTIFIED: bounds straddle, so evaluation was unavoidable
        if not (base + lo <= thr and base + hi > thr):
            return False, "REJECT: unjustified residual (bounds already decided)"
        if "unknown_value" not in model:
            return False, "REJECT: residual evaluation not declared in source"
        x = _num(model["unknown_value"])
        if ev.get("evaluated_value") != x:
            return False, "REJECT: evaluated value mismatch"
        s = base + x
        if ev.get("final_sum") != s:
            return False, "REJECT: final sum mismatch"
        if cmp(s, op, thr) != answer or status != "RESIDUAL_COMPUTATION_REQUIRED":
            return False, "REJECT: bad answer/status for residual"
        return True, "ok: residual justified (bounds straddle) and recomputed"

    if k == "TRIANGULAR_DET_ANALYTIC":
        M = parse_matrix(model["matrix"])
        n = len(M)
        upper = all(M[i][j] == 0 for i in range(n) for j in range(i))
        lower = all(M[i][j] == 0 for i in range(n) for j in range(i + 1, n))
        if not (upper or lower):
            return False, "REJECT: matrix is not triangular"
        d = 1
        for i in range(n):
            d *= M[i][i]
        if d != ev.get("det") or cmp(d, op, thr) != answer:
            return False, "REJECT: determinant mismatch"
        if ev.get("triangular_kind") not in ("upper", "lower"):
            return False, "REJECT: triangular kind not declared"
        return True, "ok: triangularity re-verified; product recomputed"

    if k == "GEOMETRIC_CLOSED_FORM":
        r = _num(model["r"])
        n = int(_num(model["n"]))
        # independent method: naive summation (engine used the closed form)
        s = sum(r ** i for i in range(n + 1))
        if s != ev.get("closed_form"):
            return False, "REJECT: closed form disagrees with naive summation"
        if cmp(s, op, thr) != answer:
            return False, "REJECT: answer inconsistent"
        return True, "ok: closed form cross-checked by independent naive summation"

    if k == "FULL_SUM":
        terms = parse_list(model["terms"])
        s = sum(terms)
        if s != ev.get("full_sum") or cmp(s, op, thr) != answer:
            return False, "REJECT: full sum mismatch"
        if status != "FULL_EXECUTION_REQUIRED":
            return False, "REJECT: full execution must not claim elimination"
        return True, "ok: full execution recomputed (no elimination claimed)"

    if k == "FULL_DET":
        M = parse_matrix(model["matrix"])
        # independent method: expansion by minors (engine used same; both O(n!))
        def lap(A):
            m = len(A)
            if m == 1:
                return A[0][0]
            return sum((-1) ** j * A[0][j] *
                       lap([row[:j] + row[j + 1:] for row in A[1:]])
                       for j in range(m))
        d = lap(M)
        if d != ev.get("det") or cmp(d, op, thr) != answer:
            return False, "REJECT: determinant mismatch"
        return True, "ok: determinant recomputed independently"

    if k == "MEDIAN_CLASSICAL":
        data = parse_list(model["data"])
        s = sorted(data)
        m = len(s)
        med = s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2
        if med != ev.get("median") or cmp(med, op, thr) != answer:
            return False, "REJECT: median mismatch"
        return True, "ok: median recomputed independently"

    return False, "REJECT: unknown kernel %r" % k
