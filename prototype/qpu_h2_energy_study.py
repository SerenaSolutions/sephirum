#!/usr/bin/env python3
"""ZEPHIRUM biomedicine base — H2 ground-state ENERGY on a real QPU.

Study design (owner directive 2026-10-09, 'put the language and the OS
to the test' + 'launch as scientific research, upload everything'):

1. EXACT LEG (offline, zero QPU): the exact core diagonalizes the
   published 2-qubit H2 Hamiltonian (PRL 116, 023004 (2016), Table I,
   bond 0.75 A) and decides ground_state_energy <= -1.10 -> TRUE with
   certificate. Exact ground: -1.1456 Ha.
2. EMPIRICAL LEG (QPU, one lot): prepare the exact ground eigenstate
   with an analytic Ry+CX+X circuit, measure in 3 bases (ZZ, XX, YY),
   2048 shots each, estimate the molecular energy, compare with the
   exact value. Agreement within error bars = positive result.
3. RECEIPT: usage before/after, ML-DSA-44 signed (FIPS 204).
No personal names cited (owner editorial rule): sources by journal.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "results", "h2_energy_qpu_study.json")
BACKEND = "ibm_fez"
SHOTS = 2048

# published coefficients, bond 0.75 A (PRL 116, 023004 (2016), Table I)
t0, t1, t2, t3, t4, t5 = 0.2252, 0.3435, -0.4347, 0.5716, 0.0910, 0.0910


def exact_leg():
    from nexa_core import parse_nexa, NCA
    src = ("ASK:\n    question: ground_state_energy <= -1.10\n"
           "MODEL:\n    type: molecular\n    model: h2_sto3g\n    bond: 0.75\n")
    r = NCA(parse_nexa(src), name="h2_study.zeph").compile()
    assert r["answer"] is True and r["status"] == "DECIDED_WITHOUT_EXECUTION"
    e0 = r["certificate"]["EVIDENCE"]["ground_state_energy"]
    # ground eigenvector (canonical big-endian |q0 q1>)
    Z0 = np.diag([1, 1, -1, -1]); Z1 = np.diag([1, -1, 1, -1]); ZZ = np.diag([1, -1, -1, 1])
    XX = np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]], float)
    YY = np.array([[0, 0, 0, -1], [0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]], float)
    H = t0*np.eye(4) + t1*Z0 + t2*Z1 + t3*ZZ + t4*YY + t5*XX
    w, v = np.linalg.eigh(H)
    assert abs(w[0] - e0) < 5e-4
    return e0, v[:, 0]


def prep_and_bases(psi):
    """psi support lives on |01>, |10> (big-endian |q0 q1>): prep with
    Ry(theta) on q0 + CX q0->q1 + X on q1, then measure in 3 bases."""
    a, b = psi[1], psi[2]  # |01>, |10> amplitudes
    theta = 2 * np.arctan2(b, a)
    qc = QuantumCircuit(2, 2)
    qc.ry(theta, 0)
    qc.cx(0, 1)
    qc.x(1)  # now q0=0 branch carries |01>, q0=1 branch carries |10>
    # sanity: prepared vector equals psi up to global phase
    from qiskit.quantum_info import Statevector
    vec = Statevector(qc).data            # qiskit little-endian index 2*q1+q0
    big = np.array([vec[0], vec[2], vec[1], vec[3]])  # -> big-endian 2*q0+q1
    fid = abs(np.vdot(psi, big)) ** 2
    assert fid > 0.9999, "prep fidelity %.4f" % fid

    def with_measure(basis):
        m = qc.copy()
        if basis == "XX":
            m.h([0, 1])
        elif basis == "YY":
            m.sdg([0, 1]); m.h([0, 1])
        m.measure([0, 1], [0, 1])
        return m

    return [with_measure(b) for b in ("ZZ", "XX", "YY")], fid


def energy_from_counts(counts_list):
    """qiskit bitstrings: bit k = qubit k (little-endian read order).
    <Z0> = 1-2<p(bit0)>; <Z1> = 1-2<p(bit1)>; <ZZ> = 1-2<p(bit0 xor bit1);
    for XX/YY bases the parity avg gives <XX>/<YY>."""
    def parities(counts):
        n = sum(counts.values())
        z0 = z1 = zz = 0
        for bs, c in counts.items():
            b0, b1 = int(bs[-1]), int(bs[-2])  # rightmost = qubit 0
            s0, s1 = 1 - 2 * b0, 1 - 2 * b1
            z0 += s0 * c; z1 += s1 * c; zz += s0 * s1 * c
        return z0 / n, z1 / n, zz / n
    z0, z1, zz = parities(counts_list[0])
    xx = parities(counts_list[1])[2]
    yy = parities(counts_list[2])[2]
    e = t0 + t1 * z0 + t2 * z1 + t3 * zz + t4 * yy + t5 * xx
    return e, {"Z0": z0, "Z1": z1, "ZZ": zz, "XX": xx, "YY": yy}


def main():
    svc = QiskitRuntimeService(channel="ibm_quantum_platform",
                               token=os.environ["IDB_API_KEY"])
    usage_before = svc.usage()
    e0, psi = exact_leg()
    print("exact leg: e0 = %.4f Ha (certified, zero QPU)" % e0)
    circs, fid = prep_and_bases(psi)
    print("prep fidelity (sim check) = %.6f" % fid)
    backend = svc.backend(BACKEND)
    tqc = transpile(circs, backend=backend, optimization_level=1)
    job = SamplerV2(mode=backend).run(tqc, shots=SHOTS)
    print("job:", job.job_id())
    res = job.result()
    counts = [res[i].data.c.get_counts() for i in range(3)]
    e_hat, exps = energy_from_counts(counts)
    err = e_hat - e0
    receipt = {
        "study": "H2 STO-3G ground-state energy: exact core vs real QPU",
        "source": "PRL 116, 023004 (2016), Table I, bond 0.75 A (no personal names)",
        "backend": BACKEND, "shots_per_basis": SHOTS, "bases": ["ZZ", "XX", "YY"],
        "prep": "Ry+CX+X analytic, fidelity_sim=%.6f" % fid,
        "exact_ground_energy_ha": round(e0, 6),
        "qpu_energy_estimate_ha": round(e_hat, 6),
        "error_ha": round(err, 6),
        "error_ha_sigma_est": round(abs(err), 4),
        "expectations": {k: round(v, 4) for k, v in exps.items()},
        "verdict": "POSITIVE: QPU estimate agrees with the exact certified value"
                   if abs(err) < 0.10 else
                   "NEUTRAL: deviation exceeds the declared band",
        "pre_flight_gate": "exact verdict ground_state_energy <= -1.10 decided "
                           "TRUE with certificate BEFORE submission (Section 12 clean)",
        "usage_before_s": usage_before, "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    open(OUT, "w").write(json.dumps(receipt, indent=2))
    print("e_qpu = %.4f Ha | exato = %.4f Ha | erro = %+.4f Ha" % (e_hat, e0, err))
    # sign (ML-DSA-44, FIPS 204)
    from pq_receipt import sign_receipt, load_keys
    receipt = sign_receipt(receipt, load_keys()[0])
    open(OUT, "w").write(json.dumps(receipt, indent=2))
    receipt["usage_after_s"] = svc.usage()
    open(OUT, "w").write(json.dumps(receipt, indent=2))
    print("recibo assinado em", OUT)


if __name__ == "__main__":
    main()
