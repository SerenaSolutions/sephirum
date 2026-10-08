# Z-QEA — Extended Decision Kernel & Certificate Specification (v0.1-draft)

Charter deliverables #8 (extended kernel) and #9 (certificate).
Drafted 2026-10-08. Every field below maps to charter §7-§13. No field
is aspirational: each is REQUIRED, OPTIONAL, or CONDITIONAL, and
absent evidence is NEVER filled with a guess (§12) — it is null with
an explicit reason code.

## 1. Kernel decision record (top-level)

| Field | Req. | Type | Meaning |
|---|---|---|---|
| schema_version | req | string | "zqea-kernel/0.1" |
| question_id | req | string | hash of normalized ZYQL source |
| backend_id | req | string | e.g. "ibm_heron_..." |
| backend_snapshot | req | object | provider calibration snapshot, AS RECEIVED |
| calibration_timestamp | req | ISO-8601 | age of the snapshot, not of the decision |
| hardware_state_hash | req | sha256 | canonical hash of the snapshot fields used |
| logical_qubits | opt | int | only when the question fixes a width |
| physical_mapping | cond | object | only when a mapping was evaluated |
| routing_evidence | cond | array | per-candidate route verdicts (§10) |
| connectivity_evidence | cond | array | coupling-map facts consulted |
| coherence_evidence | cond | object | T1/T2 values used, per qubit |
| fidelity_evidence | cond | object | 1q/2q gate errors used |
| error_budget | req | object | declared tolerances from CONTRACT |
| execution_window | cond | ISO-8601 | validity window of the decision |
| decision | req | enum | see §2 |
| justification | req | array | ordered reason codes, human-readable |
| residual | req | object | what was NOT eliminated and why |
| mitigation | cond | array | §13 registry entries (selected/required/verified/insufficient) |
| certificate_hash | req | sha256 | hash over the canonical record |

## 2. Decision states (charter §8)

Internal states, NEVER replacing the trivalent verdict (0 / 1 / Z):

ADMISSIBLE — evidence supports execution within declared budget.
REFUSED — evidence contradicts the declared budget (§9 examples:
stale snapshot; no certified mapping satisfies error budget).
UNKNOWN — evidence insufficient (§9: backend did not expose enough
calibration evidence).
STALE — snapshot older than the declared max calibration age.
INVALID — watchdog detected condition change after certification
(§11); forces STOP / RECOMPILE / REROUTE / RETRY / REFUSE / UNKNOWN.

Mapping rule: ADMISSIBLE -> trivalent verdict of the question;
REFUSED/STALE/INVALID -> refusal receipt (execution not attempted);
UNKNOWN -> Z with reason codes. A refusal is a VALID output.

## 3. Certificate reconstruction requirement

From the certificate alone, a third party must be able to answer:
(1) what was asked; (2) what evidence existed and its age;
(3) what was eliminated before execution; (4) what was executed and
under which declared budget; (5) why the decision is ADMISSIBLE,
REFUSED, STALE, INVALID or UNKNOWN. If any of these cannot be
reconstructed, the certificate is invalid by definition.

## 4. Anti-claims (binding, §12-§21)

The kernel evaluates, selects, certifies and refuses. It does not
stabilize qubits, correct physical errors, or replace calibration.
Integration with SABRE/tket/Cirq routing, ZNE/PEC/TREX mitigation is
selection + certification, not invention (§10, §13, §16 matrix rows
6, 13-16).

## 5. Status

v0.1-draft — the classical elimination rungs (exact arithmetic,
gauss identity, statistical identities, entanglement invariants) are
implemented and falsified (200 adversarial problems, 0 false
certificates). The quantum-facing fields activate when a real
backend credential is connected; until then every backend-facing
field carries value null with reason "no backend credential (§12)".
