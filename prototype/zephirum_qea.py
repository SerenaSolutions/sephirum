#!/usr/bin/env python3
"""
Z-QEA — ZEPHIRUM Quantum Execution Assurance Layer, slice 1.
================================================================

Charter: docs/ZQEA_PHASE_CHARTER.md (owner-adopted 2026-10-08).

ASK -> PROVE -> ASSESS -> CERTIFY -> EXECUTE -> VERIFY
                     ^^^^^^ this slice

What this slice adds on top of the existing decision core:

- ExecutionState: a FORMAL, validated model of a backend snapshot
  (charter rule 5). Absent metric = UNKNOWN, never inferred, never
  defaulted. Impossible metric = INVALID with a named reason.
- Admissibility assessment (charter rules 6, 8, 9): given a logical
  circuit's requirements and an execution state, the layer answers
  ADMISSIBLE / REFUSED / UNKNOWN / STALE / INVALID — internal reason
  codes over the trivalent verdict (1 / 0 / Z), never a replacement
  of it.
- Refusals always carry a reason (rule 9). Recusal is a valid output.
- QEA certificate (rule 7 subset): backend_id, snapshot hash,
  calibration timestamp, selected physical mapping, error budget,
  execution window — sealed with the same CERT_HASH machinery as the
  core (tamper = reject).
- Watchdog skeleton (rule 11): invalidate a certificate when the
  hardware state hash moves. EXPERIMENTAL — no backend in the
  sandbox can be watched in runtime (§12 honest wall).

Honest walls declared (§12):
- No real backend in the sandbox: snapshots are data, validated, not
  fetched live. ModelNotAvailable keeps being the honest answer for
  live fetch.
- No routing algorithm here (charter rule 10): candidate mappings are
  EVALUATED, not invented. SABRE/tket integration is a later slice.
- The error composition below is a DECLARED MODEL (independent-gate
  upper bound), an estimate for admissibility — labeled as such in
  every certificate it produces, never presented as a guarantee.

States (internal codes)          trivalent reading
ADMISSIBLE                       1  (may execute, justified)
REFUSED                          0  (must not execute, named reason)
UNKNOWN                          Z  (insufficient evidence)
STALE                            Z  (evidence past its window)
INVALID                          Z  (evidence itself is broken)
"""
import itertools
import json
import sys
from datetime import datetime, timezone
from fractions import Fraction

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from decision_kernel import canonical, digest, certify, check_hash  # noqa: E402

ADMISSIBLE, REFUSED, UNKNOWN, STALE, INVALID = (
    "ADMISSIBLE", "REFUSED", "UNKNOWN", "STALE", "INVALID")

QEA_TRIT = {ADMISSIBLE: 1, REFUSED: 0, UNKNOWN: "Z", STALE: "Z",
            INVALID: "Z"}


class QEAStructureError(Exception):
    """Structural error in the inputs (§12: explicit, never silent)."""


# ---------------------------------------------------------------------------
# exact metric conversion — NaN/negative/impossible refuse loudly
# ---------------------------------------------------------------------------

def frac(x):
    """Exact fraction from a metric value; refuses NaN/inf/garbage."""
    try:
        return Fraction(str(x))
    except (ValueError, ZeroDivisionError):
        raise QEAStructureError("metric not convertible to an exact "
                                "fraction: %r (§12)" % (x,))


def _prob_ok(p):
    return 0 <= p <= 1


# ---------------------------------------------------------------------------
# ExecutionState (charter rule 5)
# ---------------------------------------------------------------------------

def load_execution_state(snapshot):
    """Validate a backend snapshot. Returns (state, problems).

    Every metric is OPTIONAL: absence is UNKNOWN (recorded, never
    inferred). Present-but-impossible is INVALID (named reason).
    The snapshot hash binds the certificate to exactly this evidence.
    """
    problems = []
    if not isinstance(snapshot, dict):
        raise QEAStructureError("snapshot must be a JSON object (§12)")
    for key in ("backend_id",):
        if not snapshot.get(key):
            problems.append("missing %s" % key)

    n = snapshot.get("n_qubits")
    if n is not None and (not isinstance(n, int) or n <= 0):
        problems.append("n_qubits %r impossible (must be positive int)"
                        % (n,))

    status = snapshot.get("status")
    if status is not None and status not in ("available", "offline",
                                            "degraded"):
        problems.append("status %r not a declared status" % (status,))

    # connectivity: list of [i, j] physical edges
    edges = snapshot.get("connectivity")
    edge_set = set()
    if edges is not None:
        if not isinstance(edges, list):
            problems.append("connectivity must be a list of pairs")
        else:
            for e in edges:
                if (not isinstance(e, (list, tuple)) or len(e) != 2
                        or not all(isinstance(q, int) for q in e)):
                    problems.append("edge %r not a qubit pair" % (e,))
                elif n is not None and any(q >= n or q < 0 for q in e):
                    problems.append("edge %r outside n_qubits=%r"
                                    % (e, n))
                else:
                    edge_set.add(tuple(sorted(e)))

    # probabilistic metrics: every one must be a valid probability
    for field in ("gate_errors", "readout_errors"):
        block = snapshot.get(field)
        if block is None:
            continue
        if not isinstance(block, dict):
            problems.append("%s must be an object" % field)
            continue
        for k, v in block.items():
            try:
                p = frac(v)
            except QEAStructureError as exc:
                problems.append("%s[%r]: %s" % (field, k, exc))
                continue
            if not _prob_ok(p):
                problems.append("%s[%r]=%r not in [0,1]"
                                % (field, k, v))

    for field in ("T1_us", "T2_us"):
        block = snapshot.get(field)
        if block is None:
            continue
        if not isinstance(block, dict):
            problems.append("%s must be an object" % field)
            continue
        for k, v in block.items():
            try:
                t = frac(v)
            except QEAStructureError as exc:
                problems.append("%s[%r]: %s" % (field, k, exc))
                continue
            if t <= 0:
                problems.append("%s[%r]=%r not positive" % (field, k, v))

    ts = snapshot.get("calibration_timestamp")
    if ts is not None:
        try:
            _parse_ts(ts)
        except QEAStructureError as exc:
            problems.append("calibration_timestamp: %s" % exc)

    state = dict(snapshot)
    state["_edge_set"] = edge_set
    state["_problems"] = problems
    state["_hardware_state_hash"] = digest(
        {k: v for k, v in snapshot.items() if not k.startswith("_")})
    return state, problems


def _parse_ts(ts):
    try:
        dt = datetime.fromisoformat(str(ts))
    except ValueError:
        raise QEAStructureError("not an ISO timestamp: %r" % (ts,))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def calibration_age_seconds(state, now=None):
    """Age of the calibration evidence in seconds, or None if absent.

    None (not the string UNKNOWN) keeps the absence checkable by the
    caller without confusing absence with a value."""
    ts = state.get("calibration_timestamp")
    if ts is None:
        return None
    now = now or datetime.now(timezone.utc)
    return (now - _parse_ts(ts)).total_seconds()


# ---------------------------------------------------------------------------
# Admissibility (charter rules 6, 8, 9)
# ---------------------------------------------------------------------------

def _routes(logical_n, interactions, n_qubits, edge_set):
    """All physical mappings where every logical interaction lands on a
    physical edge. EVALUATES candidate mappings; routing algorithms
    (SABRE/tket/…) are a later slice (rule 10) — permutations only,
    n <= 8 declared wall."""
    if logical_n > n_qubits:
        return []
    out = []
    for perm in itertools.permutations(range(n_qubits), logical_n):
        ok = True
        for i, j in interactions:
            if tuple(sorted((perm[i], perm[j]))) not in edge_set:
                ok = False
                break
        if ok:
            out.append(perm)
    return out


def _route_evidence(state, mapping, interactions):
    """(p_circuit_upper, evidence_complete, missing) for one mapping.

    Model (declared, labeled): independent-gate upper bound.
    p_fail(shot) = 1 - (1 - prod_gate p_g) * (1 - prod_read p_ro)
    Readout applies to every measured qubit (all of them here).
    """
    gate_err = state.get("gate_errors") or {}
    ro_err = state.get("readout_errors") or {}
    missing = []
    p_gate = Fraction(1)
    for i, j in interactions:
        e = tuple(sorted((mapping[i], mapping[j])))
        v = gate_err.get("%d-%d" % e, gate_err.get(e))
        if v is None:
            missing.append("gate_errors[%d-%d]" % e)
        else:
            p_gate *= (1 - frac(v))
    p_ro = Fraction(1)
    for q in mapping:
        v = ro_err.get(str(q), ro_err.get(q))
        if v is None:
            missing.append("readout_errors[%d]" % q)
        else:
            p_ro *= (1 - frac(v))
    if missing:
        return None, False, missing
    return 1 - p_gate * p_ro, True, []


def assess(job, state, now=None):
    """ASSESS one job against one execution state.

    job: {logical_qubits, interactions[[i,j]], shots, error_budget,
          offline_verdict (optional)}
    Returns the assessment dict — qea_state + reasons + evidence.
    """
    problems = []
    logical_n = job.get("logical_qubits")
    interactions = [tuple(p) for p in job.get("interactions", [])]
    shots = job.get("shots", 1)
    budget = job.get("error_budget")

    if budget is not None:
        try:
            budget = frac(budget)
        except QEAStructureError as exc:
            problems.append("error_budget: %s" % exc)
            budget = None

    # CASE F (conflict): two sources disagreeing is UNKNOWN, never a
    # silent pick. The caller passes the conflicting snapshot hash.
    if state.get("conflicts_with"):
        return _dec(UNKNOWN, ["source conflict: snapshot %s disagrees"
                              % state["conflicts_with"]])

    # CASE A: already decided offline by the elimination ladder —
    # the QPU never sees this job.
    if job.get("offline_verdict") is not None:
        return _dec("NO_EXECUTION",
                    ["decided offline by the elimination ladder; "
                     "zero QPU units (ASK->PROVE closed the question)"])

    # broken evidence refuses EARLY: no route evaluation on top of a
    # snapshot that failed validation (§12 — NaN/impossible metrics
    # are INVALID, never inputs)
    if state.get("_problems"):
        return _dec(INVALID, ["snapshot failed validation: %s" % p
                              for p in state["_problems"]])

    if problems:
        return _dec(INVALID, problems)
    if budget is None:
        return _dec(UNKNOWN, ["no error budget declared; refusing to "
                              "guess an implicit one (§12)"])

    # staleness
    window = state.get("max_calibration_age_seconds")
    age = calibration_age_seconds(state, now=now)
    if age is None:
        return _dec(UNKNOWN, ["no calibration timestamp: the snapshot "
                              "has no temporal validity (§12)"])
    if window is None:
        return _dec(UNKNOWN, ["no max calibration age declared: "
                              "cannot judge staleness (§12)"])
    if age < 0:
        return _dec(INVALID, ["calibration timestamp in the future"])
    if age > float(window):
        return _dec(STALE, ["hardware snapshot stale: age %.0fs > "
                            "window %ss" % (age, window)])

    if state.get("status") == "offline":
        return _dec(REFUSED, ["backend reports offline"])

    n_qubits = state.get("n_qubits")
    edge_set = state.get("_edge_set")
    if n_qubits is None or edge_set is None:
        return _dec(UNKNOWN, ["insufficient evidence: n_qubits or "
                              "connectivity not exposed by the backend"])

    if state.get("status") == "degraded":
        problems.append("backend reports degraded: admissibility judged "
                        "on declared metrics only")

    routes = _routes(logical_n, interactions, n_qubits, edge_set)
    if not routes:
        return _dec(REFUSED,
                    ["no certified physical mapping satisfies the "
                     "declared connectivity (%d logical qubits, "
                     "%d interactions)" % (logical_n, len(interactions))]
                    + problems)

    # evaluate every candidate route — the layer selects, never
    # invents (rule 10)
    admissible, over_budget, no_evidence = [], [], []
    for r in routes:
        p_circ, complete, missing = _route_evidence(state, r,
                                                    interactions)
        if not complete:
            no_evidence.append((r, missing))
        elif p_circ * shots <= budget:
            admissible.append((r, p_circ))
        else:
            over_budget.append((r, p_circ))

    if admissible:
        admissible.sort(key=lambda t: t[1])
        best, p_best = admissible[0]
        return _dec(ADMISSIBLE,
                    ["route %s admissible: p_fail_upper(shots)=%s <= "
                     "budget %s (independent-gate upper bound, "
                     "declared model)" % (list(best), p_best, budget),
                     "%d of %d candidate mappings admissible"
                     % (len(admissible), len(routes))]
                    + problems,
                    route=list(best), p_fail_upper=p_best)
    if over_budget:
        _, worst = min(over_budget, key=lambda t: t[1])
        return _dec(REFUSED,
                   ["no certified physical mapping satisfies the "
                    "declared error budget: best p_fail_upper(shots)="
                    "%s > budget %s" % (worst, budget)] + problems)
    return _dec(UNKNOWN,
                ["routes exist but evidence is incomplete: missing %s "
                 "(backend did not expose sufficient calibration "
                 "evidence)" % sorted(set(
                     m for _, miss in no_evidence for m in miss))[:6]]
                + problems)


def _dec(qea_state, reasons, route=None, p_fail_upper=None):
    return {"qea_state": qea_state,
            "trit": QEA_TRIT[qea_state] if qea_state in QEA_TRIT else "Z",
            "reasons": reasons,
            "route": route,
            "p_fail_upper": str(p_fail_upper) if p_fail_upper is not None
            else None}


# ---------------------------------------------------------------------------
# QEA certificate (charter rule 7 subset) + watchdog (rule 11)
# ---------------------------------------------------------------------------

def make_qea_certificate(job, state, assessment, issuer="z-qea"):
    """Certificate that answers: why did ZEPHIRUM admit or refuse?"""
    cert = {
        "id": "Q-" + digest({"backend": state.get("backend_id"),
                             "job": canonical(job),
                             "qea_state": assessment["qea_state"]})[:16],
        "layer": "Z-QEA",
        "issuer": issuer,
        "backend_id": state.get("backend_id"),
        "hardware_state_hash": state.get("_hardware_state_hash"),
        "calibration_timestamp": state.get("calibration_timestamp"),
        "logical_qubits": job.get("logical_qubits"),
        "physical_mapping": assessment.get("route"),
        "qea_state": assessment["qea_state"],
        "trit": assessment["trit"],
        "reasons": assessment["reasons"],
        "error_budget": str(job.get("error_budget")),
        "execution_window_seconds": state.get(
            "max_calibration_age_seconds"),
        "residual": "admissibility decision only; execution itself is "
                    "the backend adapter's job",
    }
    return certify(cert)


def watchdog(cert, state_now, now=None):
    """EXPERIMENTAL (rule 11): is the certificate's evidence still
    the live hardware state? Returns (still_valid, reason)."""
    if not check_hash(cert):
        return False, "certificate hash mismatch — tampered or corrupted"
    age = calibration_age_seconds(state_now, now=now)
    window = state_now.get("max_calibration_age_seconds")
    if age is None or window is None or age > float(window):
        return False, "hardware snapshot stale — certificate expired"
    if cert.get("hardware_state_hash") != state_now.get(
            "_hardware_state_hash"):
        return False, ("backend snapshot changed after certification — "
                       "certificate INVALIDATED")
    return True, "hardware state unchanged inside the declared window"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Z-QEA slice 1: assess a job against a backend "
                    "snapshot, emit the QEA certificate")
    ap.add_argument("snapshot", help="JSON file: backend snapshot")
    ap.add_argument("job", help="JSON file: job requirements")
    ap.add_argument("--now", help="ISO timestamp to evaluate staleness "
                                  "at (testing)")
    args = ap.parse_args()
    now = datetime.fromisoformat(args.now).replace(
        tzinfo=timezone.utc) if args.now else None

    state, problems = load_execution_state(
        json.load(open(args.snapshot)))
    if problems:
        print(json.dumps({"qea_state": INVALID, "reasons": problems},
                         indent=2))
        return 1
    assessment = assess(json.load(open(args.job)), state, now=now)
    cert = make_qea_certificate(json.load(open(args.job)), state,
                               assessment)
    out = dict(assessment)
    out["certificate"] = cert
    print(json.dumps(out, indent=2))
    return 0 if assessment["qea_state"] in (ADMISSIBLE, "NO_EXECUTION",
                                            REFUSED) else 2


if __name__ == "__main__":
    raise SystemExit(main())
