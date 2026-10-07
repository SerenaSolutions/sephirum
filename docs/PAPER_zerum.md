# ZERUM — Computation Before Execution: A Certified Necessity Compiler with a Trivalent Decision Logic

*Draft technical report (arXiv-ready), 2026-10-06. Author: AUŠRA Quantinum.*

## Abstract

We present ZERUM, a system that answers questions *about* computations before
running them. Problems are stated in SIFR, a small domain-specific language in
which the user declares a question (e.g., "is the sum above a threshold?"), a
contract (tolerance, budget, assumptions) and a model. The SIFR Compilation
Algorithm (SCA) searches an *elimination ladder* of increasingly expensive
techniques — identity, simplification, reduction, interval bounding, closed-form
evaluation, certified approximation, classical execution — and returns one of
five explicit states: decided without execution, decided by reduction, residual
computation required, full execution required, or UNKNOWN. Every decision is
emitted with a certificate that an independent verifier re-derives from the
original source. We introduce the numeral Z (zerum), the third truth value of
SIFR logic, which remains whenever neither necessity nor unnecessity can be
proven. On 500,000 randomized problems across four families, the system made
zero wrong decisions, all 500,000 certificates passed independent verification,
20/20 forged certificates were rejected, and 76.5% of the demanded computation
units were eliminated by certificate. An advisory statistical layer trained on
the compilation ledger predicts the final state with 95.67% accuracy (baseline
53.05%) without ever deciding. We claim no quantum capability; the architecture
is deliberately quantum-last.

## 1. Introduction

Computation exists to answer questions, yet the standard pipeline — pick an
algorithm, run it, then interpret — pays for execution before asking whether
execution is needed. ZERUM inverts this order: PROOF → COMPUTE. Given a problem
P, a question Q and a contract C (tolerance ε, budget B, model M), the compiler
searches for a *decision kernel*: a certified procedure sufficient to decide Q
under C at minimal justified cost. The design principle is stated in the project
charter: the generator may be heuristic or AI-based; the verifier must be
independent.

## 2. Prior art (recorded honestly)

The system composes known techniques. Partial evaluation and program
specialization (Jones et al.) justify eliminating unreachable work. Interval
arithmetic (Moore; Kulisch) supplies the bounding rungs. Proof-carrying code
(Necula) and certified computation (Appel's program proof assistant lineage;
Russell's thesis on practical certified computation) supply the
certificate/verifier separation. Cost models in query optimization (Chaudhuri;
Ioannidis) predate the idea of deciding before executing. This report claims
a composition — an elimination ladder with cost-ordered rungs, a trivalent
decision logic with an explicit UNKNOWN state, and a composite certificate with
ledger — not the invention of any constituent technique. An exhaustive
equivalence search (e.g., against quantum resource-estimation toolkits such as
QuESt) remains future work and is recorded as an open verification in the
charter (§26).

## 3. Architecture

**SIFR** (from Arabic ṣifr, the etymological root of "zero") declares ASK
(the question), CONTRACT (tolerance, error model), and MODEL (computation
family, assumptions, unknowns with optional bounds). The SCA ladder is ordered
by cost: rung attempts are cheap first; the first certified success decides the
question and emits a certificate; exhaustion of the ladder justifies execution.
Five states are explicit; in particular, UNKNOWN is a first-class result, never
a failure.

**The numeral Z (zerum).** SIFR logic is trivalent: 0 (false/eliminated),
1 (true/necessary), and Z — the question not yet collapsed. The decision
kernel is the collapse operator Z → 0|1, always accompanied by a verifiable
certificate. In quantum notation the concept is named by the plus state
Z ≡ (|0⟩+|1⟩)/√2; we stress that this is a *naming*, not new mathematics, and
the current implementation is classical. In Arabic the numeral's sibling name
is SIWAHID (ṣifr + wāḥid, "zero and one"); the Arabic grammatical dual
(ṣifrayn, "the two zeros together") is recorded as the concept's grammatical
ancestor.

**Certificates.** Each certificate carries the deciding rung, its evidence
(witness sums, bounds, evaluated values), and the eliminated units. The
verifier re-derives every number from the original source, using a method
different from the engine's where possible, and rejects any inconsistency.

## 4. Experiments

All experiments are reproducible from this repository with a fixed seed
(stdlib-only Python).

**Falsification battery.** 500,000 randomized problems in four families
(threshold sums with declared monotonicity; sums with an unknown under optional
bounds with an oracle; unknowns without oracle where UNKNOWN is the only
correct outcome; partial means with five unknowns, bounds present or absent).
Ground truth was computed by brute force independently of the engine. Results:
zero wrong answers in 468,582 decisions; 500,000/500,000 certificates verified;
31,418 honest UNKNOWNs (6.3%); 76.5% of 3,714,285 demanded units
eliminated by certificate.

**Soundness attack.** Twenty valid certificates were tampered with (witness
sums, base sums, bounds, evaluated values incremented). The independent
verifier rejected 20/20.

**Advisory layer.** A Naive Bayes classifier over cheap metadata (family,
size, threshold ratio) trained on 40,000 ledger entries predicts the final
state before analysis: 95.67% accuracy on 10,000 held-out cases (majority
baseline 53.05%); recall 100% for full-execution outcomes, 90% for UNKNOWN,
0% for the rare residual class (0.5% of corpus) — a recorded limitation. The
layer is advisory by construction: predictions reorder attention but never
produce decisions or certificates.

**Negative results, reported with equal weight.** Cases requiring full
execution and UNKNOWN outcomes carry negative net benefit (analysis cost
unpaid); the aggregate figures include them. A latent generator defect found
during integration was fixed and all published numbers regenerated to match
the fixed code exactly.

## 5. Limitations

The families tested have exploitable algebraic structure by construction;
the 76.5% figure does not generalize to arbitrary domains. The analysis cost
is negligible here but may not remain so when rungs require expensive proofs.
No quantum backend exists; the final rung is future work. Anterioridade
(prior-art equivalence) has not been exhaustively established.

## 6. Conclusion

ZERUM demonstrates, in a controlled but fully reproducible setting, that a
question-first compiler with independent verification can eliminate most
demanded computation while remaining unable to lie: zero wrong answers, all
certificates verified, all forgeries rejected. The deeper claim is
methodological: before asking machines to compute more, ask whether they need
to compute at all.
