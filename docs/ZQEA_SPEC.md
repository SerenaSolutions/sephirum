# Z-QEA — Quantum Execution Assurance Layer, slice 1 (spec)

Charter: `docs/ZQEA_PHASE_CHARTER.md`. This slice implements the
**ASSESS** stage of `ASK -> PROVE -> ASSESS -> CERTIFY -> EXECUTE ->
VERIFY` on top of the existing decision core.

Status: PASS — battery `prototype/test_qea.py` 18/18, full regression
exit 0 (2026-10-09).

## What exists now

- `prototype/zephirum_qea.py` — the layer; `prototype/test_qea.py` —
  the battery.
- **ExecutionState** (rule 5): validated backend snapshot. Absent
  metric = UNKNOWN (recorded, never inferred). Impossible metric
  (NaN, negative probability, probability > 1, T1 = 0, edge beyond
  n_qubits, undeclared status) = INVALID with a named reason. The
  snapshot is sealed by `hardware_state_hash`.
- **Admissibility** (rules 6/8/9): internal codes ADMISSIBLE /
  REFUSED / UNKNOWN / STALE / INVALID over the trivalent verdict
  (1 / 0 / Z — the codes never replace it). Refusals always name the
  violated condition. Absence of evidence is an explicit UNKNOWN.
- **QEA certificate** (rule 7 subset): backend_id, snapshot hash,
  calibration timestamp, selected physical mapping, error budget,
  execution window, reasons — sealed with the same CERT_HASH
  machinery as the core (tamper = reject).
- **Watchdog skeleton** (rule 11): detects snapshot change or expiry
  after certification and INVALIDATES. EXPERIMENTAL.

## Declared model (honest label)

Error composition is the *independent-gate upper bound*:
`p_fail(shots) = (1 - prod(1 - p_gate)) * (1 - prod(1 - p_ro)) * shots`
over exact Fractions. It is an ESTIMATE for admissibility, labeled in
every certificate it produces — never presented as a guarantee.

## Walls declared (§12)

1. No real backend in the sandbox: snapshots are data, validated;
   live fetch keeps returning ModelNotAvailable.
2. No routing algorithm (rule 10 is a later slice): candidate
   mappings are EVALUATED (permutations, n <= 8 wall), not invented.
   SABRE/tket integration comes as selectable evidence sources.
3. Watchdog is a skeleton: no backend in the sandbox can be watched
   in runtime.
4. Conflict (case F) is detected only when the caller declares the
   conflicting hash; the layer never silently averages sources.

## Next slices (charter rules, in order)

- slice 2: ASK grammar extension (rule 22 — `ASSESS backend` /
  `EXECUTE IF CERTIFIED`) behind the existing lexer;
- slice 3: routing adapters as evidence sources (rule 10);
- slice 4: mitigation budget fields (rule 13);
- slice 5: Base44 operational dashboard (rule 21 — interface is
  never the source of truth).
