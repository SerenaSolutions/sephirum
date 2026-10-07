#!/usr/bin/env python3
"""Builds the arXiv-ready PDF of the Zephirum paper (A4, single column)."""
import textwrap
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

PAGE_W, PAGE_H = 8.27, 11.69   # A4 inches
MARGIN = 0.85
IND = "    "
plt.rcParams["font.family"] = "DejaVu Serif"

INK, ACC = "#14181d", "#8a6a15"
GREEN = "#1e6b34"


def wrap(t, width=98, first=""):
    return textwrap.wrap(t, width=width, initial_indent=first,
                         subsequent_indent="")


class Paper:
    def __init__(self, path):
        self.pdf = PdfPages(path)
        self.fig = None
        self.y = None
        self.page_no = 0

    def new(self):
        if self.fig is not None:
            self.pdf.savefig(self.fig)
            plt.close(self.fig)
        self.fig = plt.figure(figsize=(PAGE_W, PAGE_H))
        self.fig.text(0.5, 0.035, "Zephirum: An Elimination-First Decision Engine"
                      " — page %d" % (self.page_no + 2), ha="center",
                      fontsize=8, color="#666")
        self.y = PAGE_H - MARGIN
        self.page_no += 1

    def space(self, h):
        if self.y - h < MARGIN + 0.25:
            self.new()

    def para(self, text, size=10.3, width=98, indent=False, lead=1.42,
             color=INK, style="normal", first=""):
        lines = wrap(text, width=width, first=first)
        i = 0
        while i < len(lines):
            self.space(0.30)
            chunk, h = [], 0
            while i < len(lines) and h < 10:
                chunk.append(lines[i]); h += 1; i += 1
            yy = self.y
            for ln in chunk:
                yy -= size / 72 * lead
                self.fig.text(MARGIN, yy, ln, fontsize=size, color=color,
                              style=style, va="top", ha="left")
            self.y = yy - 0.05

    def title_block(self):
        self.space(2.6)
        t1 = "Zephirum: An Elimination-First Decision Engine"
        t2 = "with Certificate-Carrying Verdicts"
        self.y -= 0.42
        self.fig.text(0.5, self.y, t1, fontsize=19, color=INK,
                      ha="center", weight="bold")
        self.y -= 0.34
        self.fig.text(0.5, self.y, t2, fontsize=19, color=INK,
                      ha="center", weight="bold")
        self.y -= 0.38
        self.fig.text(0.5, self.y, "Ravi dos Anjos", fontsize=12,
                      color=ACC, ha="center")
        self.y -= 0.24
        self.fig.text(0.5, self.y, "QALQON — https://github.com/SerenaSolutions/zephirum",
                      fontsize=9.5, color="#555", ha="center")
        self.y -= 0.12
        self.fig.text(0.5, self.y, "October 2026 — preprint (v0.3 of the executable standard)",
                      fontsize=9, color="#777", ha="center", style="italic")
        self.y -= 0.30

    def section(self, n, t):
        self.space(0.85)
        self.y -= 0.34
        self.fig.text(MARGIN, self.y, "%d.  %s" % (n, t), fontsize=13,
                      color=INK, weight="bold", va="top")
        self.y -= 0.16

    def sub(self, t):
        self.space(0.6)
        self.y -= 0.20
        self.fig.text(MARGIN, self.y, t, fontsize=11, color=ACC,
                      weight="bold", va="top")
        self.y -= 0.10

    def maths(self, tex, size=12):
        self.space(0.45)
        self.y -= 0.10
        self.fig.text(0.5, self.y, tex, fontsize=size, ha="center",
                      color=INK, math_fontfamily="dejavusans")
        self.y -= 0.26

    def code(self, lines):
        for ln in lines:
            self.space(0.26)
            self.y -= 0.185
            self.fig.text(MARGIN + 0.15, self.y, ln, fontsize=8.8,
                          family="DejaVu Sans Mono", color="#20313f", va="top")
        self.y -= 0.06

    def close(self):
        if self.fig is not None:
            self.pdf.savefig(self.fig)
            plt.close(self.fig)
        self.pdf.close()


P = Paper("/app/conversations/6a530197110fe595b94f8812/zerum/docs/paper/"
          "zephirum_paper.pdf")
P.new(); P.title_block()

P.para("Abstract. Most computation is spent answering questions that could "
       "be settled without it. We present Zephirum, a decision engine that "
       "inverts the conventional order of a computation stack: given a "
       "question about a computation, it first attempts to prove that the "
       "computation is unnecessary, and only executes what remains, under an "
       "explicit unit budget, using exact rational arithmetic. Every verdict "
       "is emitted with a certificate that an independent checker, sharing "
       "no code with the engine, can validate. On 500,000 randomised "
       "problems the engine produced zero wrong answers; 76.5% of the "
       "computation budget was eliminated by certificates. An independent "
       "verifier written in C agreed with the reference engine on 400/400 "
       "cases and rejected 5/5 forged certificates. A multi-target "
       "transpiler (Python, C, Java, C#) reproduced identical verdicts and "
       "hashes across all four targets. We report a case study, the Q-SIM "
       "Gateway, in which entanglement questions about two-qubit pure states "
       "are decided analytically at the gate — with zero quantum-processing "
       "units billed — before a quantum SDK or a QPU is ever paid for. "
       "Limitations are stated explicitly and refusal is a first-class "
       "answer: the engine never guesses.", style="italic", width=104, size=9.6)

P.space(0.4); P.y -= 0.12
P.para("Keywords: proof-carrying code; certifying algorithms; exact "
       "arithmetic; decision problems; quantum software engineering; "
       "resource awareness.", size=9.5, color="#555")

# 1 ---------------------------------------------------------------
P.section(1, "Introduction")
P.para("A large share of executed computation answers questions that are "
       "decidable without execution: a threshold question about a finite sum "
       "is settled by a closed form; a question about a geometric series by "
       "a limit; a question about entanglement of a two-qubit pure state by "
       "a rank condition. Conventional software nonetheless computes first "
       "and compares afterwards, paying the full price — cycles, energy, "
       "cloud billing, and, in the quantum setting, scarce QPU time — for "
       "answers that a proof would have handed over for free.")
P.para("Zephirum (v0.3) is an executable standard and engine built on three "
       "commitments. First, elimination before execution: the engine climbs "
       "an elimination ladder — reduction, analytic closed forms, algebraic "
       "identities — and only the residue reaches the execution kernel, "
       "under a declared budget of elementary units. Second, exactness: all "
       "arithmetic is performed over the rationals, so no verdict depends "
       "on floating-point rounding. Third, certificates: every verdict "
       "carries a receipt — the answer, the rung of the ladder that decided "
       "it, hashes of the input and of the decision trace, and the units "
       "billed — which a checker that shares no code with the engine can "
       "validate independently.")
P.para("The design is deliberately honest about its reach. Zephirum "
       "operates on formally supported problem families, not arbitrary "
       "programmes; outside those families it refuses with an explicit "
       "reason rather than degrading silently (Section 7). The refusal "
       "UNKNOWN is a first-class answer, a norm we call §12 in the standard.")
P.para("Contributions. (i) An elimination-first decision model in which "
       "proof precedes computation and execution is budgeted (Sections 2-3). "
       "(ii) A certificate format validated by an independent C verifier "
       "(Section 3). (iii) Measurements over 500,000 randomised problems, "
       "boot-family self-hosting in the engine's own bytecode, and "
       "cross-language reproduction of verdicts (Section 4). (iv) The Q-SIM "
       "Gateway: quantum questions decided at the gate with zero QPU units "
       "billed (Section 5). (v) An explicit statement of limitations and of "
       "the relationship to proof-carrying code and certifying algorithms "
       "(Sections 6-7).")

# 2 ---------------------------------------------------------------
P.section(2, "The Zephirum model")
P.para("A Zephirum programme is a triple ASK/CONTRACT/MODEL: a question, a "
       "guarantee demanded of the answer, and a formal description of the "
       "computation the question is about. The canonical form is:")
P.code(["ASK:        question: sum > 10",
        "CONTRACT:   absolute_error: 0",
        "MODEL:      type: threshold_sum    data: 1,2,3,...,n"])
P.para("The engine never treats a programme as free-form code. Each MODEL "
       "type declares the family it belongs to — threshold sums, geometric "
       "series, means, two-qubit pure states — and each family carries its "
       "closed-form theory. The ladder is applied in fixed order:")
P.para("1. REDUCTION — structural simplification of the model (constant "
       "folding of the data, degenerate cases).", size=10.3)
P.para("2. ANALYTIC — a closed form decides the question outright "
       "(Gauss' sum n(n+1)/2; the geometric limit a/(1-r); the Schmidt "
       "determinant for entanglement).", size=10.3)
P.para("3. ALGEBRAIC / BOOT — the identity is executed as bytecode in the "
       "engine's own budgeted virtual machine, a step of self-hosting: the "
       "elimination mechanism of the engine is written in the language the "
       "engine defines.", size=10.3)
P.para("4. VM — the residue is computed under a declared budget of "
       "elementary units. A certificate records which rung decided the "
       "question and how many units were billed.", size=10.3)
P.para("The contrast with naive computation is sharpest in the geometric "
       "family. The question 'is the infinite sum 1 + 1/2 + 1/4 + ... "
       "strictly less than 2?' cannot be settled by any finite truncation: "
       "the naive 12-term sum is 4095/2048, which supports TRUE, and the "
       "error is wrong at any finite length. The exact identity settles the "
       "sum as a/(1-r) = 2, so the certified verdict is FALSE — obtained in "
       "two units, with the truncation path printed alongside for "
       "comparison and refusal.")
P.maths(r"$\mathrm{sum} = a/(1-r) = 1/(1-\frac{1}{2}) = 2 \quad \Rightarrow "
        r"\quad \mathrm{sum} < 2 \; \mathrm{is} \; \mathrm{FALSE}$")

# 3 ---------------------------------------------------------------
P.section(3, "Certificates and independent verification")
P.para("Every decision emits a receipt with fixed fields: ANSWER, RUNG "
       "(the ladder step that decided), STATUS, COST_ESTIMATE (units "
       "billed against the budget), INPUT_HASH, CERT_HASH, ELIMINATION_"
       "TRACE and EVIDENCE (family-specific grounds, e.g. the determinant "
       "and squared norm of a state). The certificate is designed so that "
       "verification does not require trusting the engine:")
P.para("An independent verifier, written in C with no shared code, "
       "re-derives each verdict from the source programme and the "
       "certificate. In the adversarial battery it agreed with the "
       "reference engine on 400/400 randomised certificates and rejected "
       "5/5 forged certificates whose hashes had been recalculated to "
       "match the tampered evidence — the checker validates the "
       "mathematical route, not the hash alone. This follows the "
       "philosophy of proof-carrying code [1,2]: trust is established by "
       "the consumer checking evidence, not by trusting the producer.")
P.para("All arithmetic is exact, over the rationals. Where a quantum SDK "
       "compares amplitudes as binary64, its verdicts inherit the "
       "representation's limits; three mainstream SDKs were observed to "
       "disagree on exact-equality questions for amplitudes beyond the "
       "2^53 boundary of the double format [7]. Zephirum's certificates "
       "carry exact rationals, so equality questions are decided by "
       "arithmetic, not by tolerance.")

# 4 ---------------------------------------------------------------
P.section(4, "Measured results")
P.para("All measurements are reproducible from the repository, in pure "
       "Python 3 with no external dependencies:")
P.para("1. Soundness: 500,000 randomised problems across families — zero "
       "wrong answers; every answer either a certified verdict or an "
       "explicit refusal.", size=10.3)
P.para("2. Elimination: 76.5% of the execution budget eliminated by "
       "certificate on the reference workload; the elimination steps "
       "themselves are boot programmes running on the engine's own "
       "budgeted bytecode VM (Gauss, geometric and mean steps, B1-B6, "
       "G1-G6, M1-M4).", size=10.3)
P.para("3. Independent checking: C verifier agreement 400/400; forged "
       "certificates rejected 5/5.", size=10.3)
P.para("4. Portability: a multi-target transpiler emits Python, C, Java "
       "and C# from one source; all four targets reproduce identical "
       "verdicts and identical input hashes, replicating the §12 refusal "
       "protocol.", size=10.3)
P.para("5. Resistance: 10,000 adversarial cases with zero memory or stack "
       "faults; scale validated to n = 10^9 under the optimised kernel "
       "with verifiable verdicts.", size=10.3)
P.para("6. Conformance: an executable standard (v0.3) with a nine-battery "
       "conformance suite, integrated and green in the same commit as "
       "each new family.", size=10.3)

# 5 ---------------------------------------------------------------
P.section(5, "Case study: the Q-SIM Gateway")
P.para("The Q-SIM Gateway is the first product built on Zephirum. It sits "
       "in front of a quantum SDK (Qiskit, Cirq, PennyLane) or a real QPU: "
       "entanglement-family questions are decided analytically at the "
       "gate, with exact rational arithmetic and zero QPU units billed. "
       "For a two-qubit pure state")
P.maths(r"$|\psi\rangle = a|00\rangle + b|01\rangle + c|10\rangle + d|11"
        r"\rangle$,   $M = [[a,b],[c,d]]$")
P.para("the Schmidt criterion is closed and exact: the state is a product "
       "state if and only if det(M) = 0, and its concurrence is C = 2|det "
       "M| / ⟨ψ|ψ⟩. The full route — building the state vector and "
       "diagonalising M·M^T — costs eight units on the SDK path; the "
       "criterion costs three multiplications and is decided at the gate. "
       "In the gateway battery, 40/40 states (product, Bell, partial, "
       "decimal and random) were decided at the gate with zero QPU units "
       "billed, every certificate verified by the independent checker, and "
       "a float counter-proof (eigenvalues of the reduced density matrix) "
       "agreed wherever floating point can decide. Questions outside the "
       "supported families are NOT ROUTED, with an explicit reason and "
       "the SDK cost they would have required; a missing SDK produces an "
       "honest SKIP rather than a pretended cross-check.")
P.para("The gateway is the industrial form of the engine's thesis: prove "
       "before you pay.")

# 6 ---------------------------------------------------------------
P.section(6, "Related work")
P.para("Proof-carrying code. Necula and Lee introduced proof-carrying "
       "code, in which untrusted code ships with a formal proof that a "
       "host can check cheaply [1,2]. Zephirum adopts the consumer-side "
       "checking discipline — verdicts are trusted only through "
       "certificate validation — and applies it to decision problems "
       "about computations rather than to the safety of mobile code.")
P.para("Certifying algorithms. McConnell, Mehlhorn, Näher and Schweitzer "
       "systematised algorithms that output, with each answer, a witness "
       "the user can verify more easily than re-running the algorithm "
       "[3]. The Zephirum receipt is a certifying witness in this sense; "
       "the distinction is that the certificate records also what was "
       "eliminated, turning the witness into a unit-level accounting "
       "instrument.")
P.para("Quantum programme verification. Quipper [4], QWIRE [5] and SQIR "
       "[6] embed quantum computation in dependently-typed or classical "
       "hosts and verify correctness of circuits with proof assistants. "
       "Zephirum addresses a different layer: not the verification of a "
       "circuit's unitary semantics, but the elimination of the need to "
       "execute at all for questions with closed-form theory — a layer "
       "that composes with, and does not replace, verified toolchains. "
       "The exactness argument against binary64 equality follows the "
       "classical analysis of floating point [7].")
P.para("We state clearly that the prior-art review reported here is "
       "scoped to the three threads above and remains, per the standard's "
       "own §12 protocol, an open obligation to be extended before formal "
       "publication of the standard itself.")

# 7 ---------------------------------------------------------------
P.section(7, "Limitations")
P.para("Zephirum v0.3 operates on formally supported families: threshold "
       "sums, geometric series, means, and two-qubit pure states. Outside "
       "these families it refuses explicitly (NOT ROUTED at the gateway; "
       "UNKNOWN in the kernel) and never guesses. The surface language "
       "is deliberately small; a mature parser and a normative grammar are "
       "declared roadmap work, as are pip/PyPI packaging and an HTTP "
       "service form of the gateway. The quantum rung covers two-qubit "
       "pure-state questions; mixed states, higher registers and channel "
       "semantics are future work. The measurements reported here were "
       "produced by the reference implementation and its C verifier; "
       "they are reproducible but have not yet been independently "
       "replicated by third parties.")

# 8 ---------------------------------------------------------------
P.section(8, "Conclusion and future work")
P.para("Zephirum demonstrates a practical inversion of the computation "
       "stack — ask first, prove next, compute last — with exact "
       "arithmetic, budgeted execution, and consumer-verifiable "
       "certificates, measured on half a million problems with zero "
       "wrong answers and a 76.5% eliminated budget. The Q-SIM Gateway "
       "shows the industrial consequence: quantum questions with "
       "closed-form theory need never reach a paid queue. Future work "
       "follows the published roadmap: the normative grammar and parser, "
       "a formally specified VM, additional verifiers in independent "
       "languages, families for mixed states, and a proof-carrying "
       "protocol for cloud billing. The executable standard, conformance "
       "suite and all batteries are open and reproducible at "
       "https://github.com/SerenaSolutions/zephirum.")
P.space(0.5); P.y -= 0.10
P.para("References", size=11, width=40, color=INK)
refs = [
 "[1] G. C. Necula and P. Lee. Proof-Carrying Code. Principles of "
 "Programming Languages (POPL), pp. 106-119, 1997.",
 "[2] G. C. Necula. Compiling with Proofs. PhD thesis, Carnegie Mellon "
 "University, 1998.",
 "[3] R. M. McConnell, K. Mehlhorn, S. Naher and P. Schweitzer. "
 "Certifying Algorithms. Computer Science Review 5(2), 2011.",
 "[4] A. S. Green, P. L. Lumsdaine, N. J. Ross, P. Selinger and B. "
 "Valiron. Quipper: A Scalable Quantum Programming Language. PLDI, 2013.",
 "[5] R. Rand, J. Paykin and S. Zdancewic. QWIRE: A Core Language for "
 "Quantum Circuits. POPL, 2018.",
 "[6] K. Hietala, R. Rand, S.-H. Hung, X. Wu and M. Hicks. A Verified "
 "Optimizer for Quantum Circuits. POPL, 2021.",
 "[7] D. Goldberg. What Every Computer Scientist Should Know About "
 "Floating-Point Arithmetic. ACM Computing Surveys 23(1), 1991.",
]
for r in refs:
    P.para(r, size=9.2, width=104)

P.close()
print("PDF ok")
