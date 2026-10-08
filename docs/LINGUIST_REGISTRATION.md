# GitHub Linguist registration — ZEPHIRUM

Goal: make Zephirum a recognized language on GitHub (language bar,
syntax highlighting, search by language). Owner-directed 2026-10-08.

## The exact bar (linguist CONTRIBUTING.md, read 2026-10-08)

A new extension is accepted only with *sufficient wide-spread usage*:
- at least 2000 indexed files of the extension in the last 12 months,
  excluding forks, for extensions occurring more than once per repo;
- results must show a reasonable distribution across distinct
  user/repo combinations — the language owner's own repos are
  filtered out of the assessment;
- Linguist explicitly closes PRs for "very new or hobby languages"
  that do not meet this.

Current usage: 6 `.zeph` files, all in this repository (owner's).
Gap: ~1994 files across many distinct owners.

## Registration package (must exist BEFORE the PR)

1. [x] TextMate grammar — `grammar/zephirum.tmLanguage.json`
   (scope `source.zephirum`, faithful to `prototype/nexa_core.py`
   parser: ASK/CONTRACT/MODEL/BUDGET/REQUIRE blocks, `#` comments,
   sum/mean/median targets, comparison and arithmetic operators,
   `a..b` ranges, exact-number literals, bare flags, `none`).
   Hosted copy: SerenaSolutions/zephirum-tmlanguage (separate repo,
   as `script/add-grammar` requires a standalone grammar repo).
2. [x] Proposed `languages.yml` entry (below).
3. [x] Samples: real battery sources, MIT-licensed (this repo's
   LICENSE). PR must state this license.
4. [ ] Usage evidence: GitHub search link showing 2000+ files.
5. [ ] The PR itself: entry + `script/add-grammar
   https://github.com/SerenaSolutions/zephirum-tmlanguage` +
   samples + search link, from a fork, following the PR template.

## Proposed languages.yml entry

```yaml
Zephirum:
  type: programming
  color: "#22D3EE"
  extensions:
  - .zeph
  tm_scope: source.zephirum
  ace_mode: text
  language_id: # assigned by script/update-ids
```

## Adoption plan (honest, no farming)

We will NOT mass-create repos — Linguist filters the owner and
farming violates their spirit. Growth levers, in order:
1. Kata/exercise collections and worked examples in the README and
   book, written so third parties adopt the format for their own
   questions (battery-style ASK/CONTRACT/MODEL files).
2. The plugin: every user who saves a ZYQL question in their own
   repo creates real `.zeph` usage.
3. Tutorials/community posts with copyable, non-trivial sources
   (Linguist rejects hello-world-only samples).
4. Re-check search quarterly: `ext:zeph NOT user:SerenaSolutions`.

## Status log

- 2026-10-08: grammar written and validated as JSON; registration
  package tracked here; grammar repo created. PR intentionally NOT
  opened yet — Linguist closes PRs below the 2000-file bar.

## Editor distribution (adoption lever #1)

- 2026-10-08: VS Code extension package prepared at
  `editors/vscode/zephirum/` (manifest, language configuration,
  embedded grammar). Publishing to the Marketplace requires the
  owner's publisher account (PAT via `vsce`) — package is ready.
