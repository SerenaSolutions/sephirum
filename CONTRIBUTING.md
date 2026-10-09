# Contributing to ZEPHIRUM

Soundness first: a wrong verdict is never acceptable, and an unsound
refusal is preferred over a corrupted answer (Section 12).

## Ground rules
1. The Python engine (`prototype/nexa_core.py`) is the reference semantics;
   the C core must stay verdict-identical (`tests/cross_check_c.py`, 0 mismatches).
2. Every claim in a PR needs evidence: run the cross-check, the corpus
   validator, or attach a hardware receipt id.
3. If a target language cannot represent an answer exactly, emit a formal
   refusal — never a silent approximation.

## How to submit
1. Fork, branch from `main`, keep commits focused.
2. Fill the PR template (What / Evidence / Section 12 check).
3. CI must pass: build the C core, cross-check, emission smoke.
