# Security Policy and Update Path — ZEPHIRUM / ZYQL

This document defines how users of the ZEPHIRUM exact-decision language
receive and verify security updates. The language has no network
primitives, no phone-home, and no auto-update — **by design**. The update
channel is therefore the distribution channel itself: this repository and
its signed releases. Git is the updater; the guardian is in the payload.

## 1. Current security baseline

| Component | Value |
|---|---|
| Latest release | v1.1.0 (security baseline) |
| PORTGATE list version | 1 |
| Guardian battery | ZYGUARD 13/13 |
| Receipt signatures | ML-DSA-44 (FIPS 204), self-contained |

## 2. How to update a clone

From any existing clone of this repository:

```
git fetch --tags
git checkout main
git pull --ff-only
git tag -l            # confirm v1.1.0 is present
```

Clones predating the guardian (ZYGUARD) upgrade to the guarded lineage
with the same commands. There is no patch file and no installer: the
unit of distribution is the repository itself, and history is
append-only (never rewritten; fixes are new commits, never rebases).

## 3. How to verify you are on the guarded version

1. Run the ZYGUARD language battery:

```
python3 prototype/test_zyguard_language.py
```

Expected: 13/13 PASS, including refusal-before-compute for all seven
prohibited classes and inertness of injected execution strings.

2. Check the PORTGATE stamp: every guarded certificate carries
   `gate: PORTGATE` and `list_version`. Certificates without the
   PORTGATE stamp predate the guardian and are pre-protocol artifacts.

3. Verify receipts: every signed artifact in `results/` embeds its
   ML-DSA-44 public key and is self-contained — verification requires
   no infrastructure beyond this repository.

## 4. Reporting a security issue

Open a GitHub issue titled `[SECURITY]`. Include: the affected
component, a minimal `.zeph` program, and the certificate hash. Do not
report suspected issues through untrusted third-party channels.

## 5. Scope

Structural purity (no execution primitives in the grammar) is the
primary security property and cannot be "patched on" — it is the
language itself. Security releases refine the guardian's lists,
signing hygiene, and documentation; they never add execution,
network, or I/O primitives. Any future release containing such a
primitive would violate the language charter and must be rejected by
the community.
