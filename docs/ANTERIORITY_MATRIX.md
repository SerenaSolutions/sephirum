# Anteriority Matrix — charter §16, deliverable #1 (2026-10-08)

Evidence base: three independent world sweeps (docs/NOVELTY_SWEEP.md,
18 sources 1976-2026 + sweep 3, six additional lines) plus the
owner-supplied external audit (docs/ZQEA_PHASE_CHARTER.md).
Structure required by the charter:
FEATURE / EXISTS? / WHERE / DATE / OVERLAP / DIFFERENCE / POTENTIAL
CONTRIBUTION. Classification: A known · B known combination · C
combination with architectural difference · D potentially new
hypothesis · E not yet addressable.

| # | Feature | Exists? | Where | Date | Overlap | Difference | Class |
|---|---------|---------|-------|------|---------|------------|-------|
| 1 | Static proof of program properties | Yes | Necula PCC; F*/Liquid Haskell | 1996-2018 | proof attached to code that IS executed | certificate that execution is NOT needed — inverse direction | C |
| 2 | Program specialization / elimination inside a computation | Yes | Turchin supercompilation; Adapton | 1986-2014 | residual code, faster | trivalent verdict + elimination ladder stopping at first certified rung | C |
| 3 | Exact-arithmetic decision engine | Yes | SymPy, GMP, Fractions | 1970s- | exact math as library | exactness as the FIRST rung of a necessity compiler with certificate | B |
| 4 | Interval/numerical error control | Yes | interval arithmetic, NR-4 analogs, Ball arithmetic | 1966- | bounded error inside computation | error as CONTRACT (absolute_error) deciding BEFORE execution | C |
| 5 | Hardware-state awareness (drift, calibration, queues) | Yes | IBM Qiskit Runtime; Cirq calibration selection | 2019-2026 | monitoring and pausing | evidence model: metrics absent = UNKNOWN, never presumed; decision certificate cites the snapshot | C |
| 6 | Calibration/fidelity-aware routing and placement | Yes | tket; SABRE; Qiskit transpiler | 2018-2024 | routing algorithms | ZEPHIRUM selects/rejects/certifies routes, does not re-invent them | B |
| 7 | Quantum resource estimation | Yes | Azure Resource Estimator; Classiq | 2023- | cost estimate | verdict on whether to run at all, with certificate | C |
| 8 | Economic quantum-advantage forecasting | Yes | Quantum Economic Advantage Calculator | 2022- | timeline model per industry | per-instance decision compiler | C |
| 9 | Certifying algorithm results | Yes | Certifying algorithms (Ernst et al.) | 2009- | certificate of a computed RESULT | certificate of NON-necessity of computing | C |
| 10 | Succinct proofs of executed computation | Yes | zk-SNARKs, ZKML | 2016-2025 | verify execution happened correctly | verify execution NOT needed | C |
| 11 | Trivalent logic (true/false/unknown) | Yes | Kleene 3-valued logic; SQL NULL | 1938- | 3 values as logic semantics | UNKNOWN as first-class computational verdict with auditable reason | B |
| 12 | Compiled question language (DSL) | Yes | SQL; Datalog; Z3 queries | 1974-2010 | declarative querying | target of the compilation is the NECESSITY of execution (neologism: ours) | D |
| 13 | Elimination ladder ordered by analysis cost | No located | closest: portfolio algorithm selection (Rice 1976; SATzilla) | — | always executes one candidate | ordered rungs, stop at first certified; never executes when a rung certifies non-necessity | D |
| 14 | Verifiable certificate of elimination | No located | closest: PCC (inverse) | — | certifies safety of executing | certifies that executing was unnecessary, reconstructable justification | D |
| 15 | Execution assurance layer above compilers | Partial | Z-QEA charter hypothesis | 2026 | IBM/tket own the layers below | evidence-based admissibility decisions (ADMISIBLE/REFUSED/UNKNOWN/STALE) | D |
| 16 | Gateway product (name ZYQL GATEWAY) | Partial | this repo, plugin v0.5.1 | 2026 | none located (QSim collision retired) | certified necessity decisions before QPU spend | D |

## Reading of the matrix

- No feature of classes A/B is claimed as new — all credited above.
- The composition (#12+#13+#14+#15 in one architecture) has no
  located precedent in three sweeps. Claim level A (composition),
  sustained by the falsification experiment: 200 adversarial
  problems, 0 false certificates (83.5% elimination).
- What is NOT claimable (charter §21 preview): qubit stabilization;
  calibration-aware routing as invention; execution certification;
  any technique of the A/B rows.
