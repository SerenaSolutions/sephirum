# ZYQL — GitHub Linguist registration kit

ZYQL (Zephirum Query Language, spoken "Zykel") is a necessity-first,
trivalent exact-decision language: `1` / `0` / `Z (REFUSED)`.
Source files use the `.zeph` extension.

This kit contains everything needed to request ZYQL's inclusion in the
GitHub Linguist catalogue, so the language gets its own name and color
in the repository language bar.

## Contents

1. `grammars/zyql.tmLanguage.json` — TextMate grammar (highlighting for
   GitHub, VS Code, and any TextMate-compatible editor). Covers the five
   sections (ASK / CONTRACT / MODEL / BUDGET / REQUIRE), keys, exact
   decimals, comparison operators, verdict constants and `#` comments.
2. `zyql.yml` — proposed `vendor/` entry for linguist.
3. `../vscode/language-configuration.json` — editor behavior (brackets,
   comment toggling, indentation) for the VS Code extension scaffold.

## Submission path (when adoption is there)

1. Fork https://github.com/github-linguist/linguist
2. Copy `zyql.yml` content into `vendor/langs/` (merge alphabetical)
3. Copy the grammar into the Sublime/TextMate grammar location required
   by their CONTRIBUTING.md (they accept either a Sublime syntax or a
   TextMate grammar)
4. Open a PR titled "Add ZYQL (Zephirum Query Language)"

## Honest criteria note

Linguist's stated policy is *usage*: they only accept languages with
meaningful real-world adoption in public repositories (their
CONTRIBUTING.md is the authoritative source; historically the practical
bar has been on the order of hundreds of repos from distinct users).
Until ZYQL is used by others in the wild, the PR would likely be
declined. The kit is ready now so the moment adoption exists, submission
is a copy-paste.

## Interim workaround (today, zero adoption needed)

A `.gitattributes` line colors `.zeph` files in *this* repo's stats:

```
*.zeph linguist-language=ZYQL
```

(not catalog-aware, but keeps Python percentages honest in the bar)
