#!/usr/bin/env python3
"""
CLASSICAL LINK — reference host (Unix domain socket, JSON lines).

A WORKING standby connector for the ZYQL verdict engine on POSIX
systems (Linux, macOS). Windows and macOS native hosts live in their
own standby skeletons; the wire protocol is identical (SPEC.md).

The host never decides: it parses the request, forwards it to the exact
core (nexa_core), and returns the core's certified answer — or the core's
refusal, untouched (Section 12 travels the wire).

Usage:
  python3 host_reference.py            # serves /tmp/zyql-verdict.sock
  python3 host_reference.py --demo     # starts host, runs 2 clients, stops
"""
import json
import os
import socket
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nexa_core import parse_nexa, NCA  # exact core — the only decider

SOCK = "/tmp/zyql-verdict.sock"


def to_source(req):
    """Canonical .zeph source from a wire request (SPEC.md v1.0)."""
    lines = ["ASK:", "    question: %s" % req["ask"]]
    if req.get("contract"):
        lines.append("CONTRACT:")
        for k, v in req["contract"].items():
            lines.append("    %s: %s" % (k, json.dumps(v) if isinstance(v, (dict, list)) else v))
    lines.append("MODEL:")
    for k, v in req["model"].items():
        lines.append("    %s: %s" % (k, json.dumps(v) if isinstance(v, (dict, list)) else v))
    return "\n".join(lines)


def handle_request(line):
    """Forward one request to the exact core. Never decides itself."""
    try:
        req = json.loads(line)
    except json.JSONDecodeError as e:
        return {"refused": True, "reason": "malformed JSON: %s" % e,
                "section": "12"}
    if req.get("zyql") != "1.0":
        return {"refused": True, "reason": "protocol version must be 1.0",
                "section": "12"}
    if "ask" not in req or "model" not in req:
        return {"refused": True, "reason": "request needs ask and model",
                "section": "12"}
    try:
        res = NCA(parse_nexa(to_source(req)), "classical-link").compile()
    except Exception as e:
        return {"refused": True, "reason": "engine refusal: %s" % e,
                "section": "12"}
    status = res["status"]
    if status.startswith("DECIDED"):
        return {"verdict": 1 if res["answer"] is True else 0,
                "status": status,
                "kernel": res["kernel"],
                "units_required": res["required"],
                "input_hash": res["certificate"]["INPUT_HASH"]}
    if status == "UNKNOWN":
        return {"verdict": "UNKNOWN", "status": status,
                "kernel": res.get("kernel", ""),
                "input_hash": res["certificate"]["INPUT_HASH"]}
    # core is offline-exact: statuses demanding execution are honest refusals here
    return {"refused": True, "reason": "core status: %s" % status,
            "section": "12"}


def serve(path=SOCK):
    if os.path.exists(path):
        os.unlink(path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(path)
    srv.listen(8)
    return srv


def client(path, request):
    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    c.connect(path)
    c.sendall((json.dumps(request) + "\n").encode())
    data = b""
    while b"\n" not in data:
        chunk = c.recv(4096)
        if not chunk:
            break
        data += chunk
    c.close()
    return json.loads(data.decode().strip())


def demo():
    srv = serve()
    threading.Thread(target=_accept, args=(srv,), daemon=True).start()
    import time
    time.sleep(0.2)
    bell = {"zyql": "1.0", "ask": "entangled == 1",
            "contract": {"absolute_error": 0},
            "model": {"type": "entanglement", "state": "0.5,0,0,0.5"}}
    sep = {"zyql": "1.0", "ask": "entangled == 1",
           "contract": {"absolute_error": 0},
           "model": {"type": "entanglement", "state": "0.5,0.5,0.5,0.5"}}
    print("Bell   ->", json.dumps(client(SOCK, bell)))
    print("Sep    ->", json.dumps(client(SOCK, sep)))
    srv.close()
    os.unlink(SOCK)


def _accept(srv):
    while True:
        conn, _ = srv.accept()
        with conn:
            buf = b""
            while b"\n" not in buf:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
            resp = handle_request(buf.decode().strip()) if buf.strip() else \
                {"refused": True, "reason": "empty request", "section": "12"}
            conn.sendall((json.dumps(resp) + "\n").encode())


def main():
    if "--demo" in sys.argv:
        demo()
        return
    srv = serve()
    print("ZYQL classical link (reference host) serving %s" % SOCK)
    _accept(srv)


if __name__ == "__main__":
    main()
