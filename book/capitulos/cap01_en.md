# Chapter 1 — The World Executes Before Asking
*ZERUM — Computation Before Execution | Part I: The Question*

## Level 1 — For every reader

To find out whether your front door is open, you have two options: walk ten steps and look; or hire a crew to demolish the house, inspect every brick, rebuild everything, and then declare: "yes, it was open."

Nobody would choose the second option. Yet it is the second one we choose every day in computing.

We throw supercomputers at entire storms to learn whether it will rain tomorrow at noon in one specific square. We sum complete lists when the first three numbers have already decided the answer. We reserve quantum processors for questions a one-line algebraic identity would settle. We execute first. We ask afterwards — if time remains.

This book is born from a question that should come before all others:

**"Do I really need to run this computation to answer the question I asked?"**

## Level 2 — For the scientist and the engineer

Computation exists to answer questions, but we organize the work backwards: we pick an algorithm, write a program, run it — and only then discover what the run told us about the original question.

We invert the order. A problem never arrives alone: it arrives with a **question** (what I want to know), a **tolerance** (what error is admissible), a **budget** (what I may spend), **assumptions** (what I may presume), and **constraints** (what must be preserved). We call this bundle the **contract**.

With the contract in hand, three questions guide the entire book:

1. Do I really need to run this computation to answer my question?
2. If I must compute something, what is the smallest computation I can justify?
3. How do I prove that what was eliminated really was unnecessary?

## Level 3 — For the computer scientist

Formally: given a problem P, a question Q, and a contract C (tolerance ε, budget B, model of computation M), we build a compiler that searches for a **Decision Kernel** — a certified procedure sufficient to decide Q under C with the smallest justifiable computation available — and emits one of five explicit states:

- `DECIDED_WITHOUT_EXECUTION` — the question was answered without executing anything;
- `DECIDED_BY_REDUCTION` — the question was decided by eliminating a substantial part of the computation;
- `RESIDUAL_COMPUTATION_REQUIRED` — only a residue of the computation remains necessary;
- `FULL_EXECUTION_REQUIRED` — no certified reduction was found; full execution is justified within the model;
- `UNKNOWN` — the system could prove neither necessity nor unnecessity.

The paradigm shifts from `ALGORITHM → COMPUTE` to `PROOF → COMPUTE`. The rest of the book pursues this inversion: first the research lines that already exist (chapter 5), then the attempts to destroy the hypothesis (chapter 6), and only then the architecture that survived.
