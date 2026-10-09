# CLASSICAL LINK — standby connectivity drivers for the ZYQL verdict engine

The ZYQL core is exact and hardware-agnostic. Classical hosts (Windows,
macOS, and any POSIX system) should be able to request a verdict from the
engine over a *local classical channel* — no quantum cloud in the decision
path, no SDK dependency. This directory defines that channel and ships:

1. `host_reference.py` — a WORKING reference host (Unix domain socket,
   JSON-lines protocol, wired to the exact core `nexa_core`). Verified
   end-to-end on this machine; see `README section "Evidence"`.
2. `windows_host/ZyqlVerdictHost.cs` — STANDBY named-pipe host (C#).
   Same wire protocol; wiring to the engine marked TODO.
3. `macos_host/ZyqlVerdictHost.swift` — STANDBY Unix-socket host (Swift).
   Same wire protocol; wiring to the engine marked TODO.

HarmonyOS is intentionally out of scope (owner directive 2026-10-09:
"very different, leave it quiet").

## Wire protocol (v1.0) — JSON lines

One request per line, one response per line, UTF-8, no framing beyond `\n`.

Request:

```json
{"zyql":"1.0","ask":"entangled == 1","contract":{"absolute_error":0},
 "model":{"type":"entanglement","state":"0.5,0,0,0.5"}}
```

Response (decided):

```json
{"verdict":1,"units":0,"input_hash":"b8c6...","cert_hash":"..."}
```

Response (refusal — Section 12 honesty travels the wire too):

```json
{"refused":true,"reason":"index beyond the declared 2^N space","section":"12"}
```

`verdict` is `1`, `0` or `"UNKNOWN"` — the trivalent contract of the
language, unchanged by transport. The host never decides; it forwards to
the exact core and returns what the core certified.

## Status

| Component | Status | Channel |
|---|---|---|
| reference host (Linux/macOS) | WORKING (tested here) | Unix domain socket `/tmp/zyql-verdict.sock` |
| Windows host | STANDBY (compiles as skeleton; engine wiring TODO) | named pipe `\\.\pipe\zyql-verdict` |
| macOS host | STANDBY (compiles as skeleton; engine wiring TODO) | Unix domain socket `/tmp/zyql-verdict.sock` |
