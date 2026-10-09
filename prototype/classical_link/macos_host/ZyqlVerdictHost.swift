// CLASSICAL LINK — macOS/Apple STANDBY host (Unix domain socket, JSON lines).
// Wire protocol: SPEC.md v1.0 (identical to the reference host).
//
// STATUS: STANDBY SKELETON. The transport (Unix socket server + JSON
// request/response) is complete; the engine wiring is a marked TODO.
// On a Mac, route the parsed request to the ZYQL engine (zref binary or
// the Python core) and return its certified answer.
// The host NEVER decides; Section 12 refusals travel the wire as-is.
//
// Build (standby check): swiftc ZyqlVerdictHost.swift -o ZyqlVerdictHost
// Run: ./ZyqlVerdictHost

import Foundation

let sockPath = "/tmp/zyql-verdict.sock"

func handle(_ line: String) -> String {
    // TODO(engine-wiring): parse `line` as a SPEC.md request, forward to
    // the ZYQL exact core (zref subprocess or embedded Python core), and
    // serialize the core's certified answer. Until wired, this STANDBY
    // host answers honestly:
    return "{\"refused\":true,\"reason\":\"standby host: engine not wired on this machine\",\"section\":\"12\"}"
}

// --- transport (complete) ---
unlink(sockPath)

let fd = socket(AF_UNIX, SOCK_STREAM, 0)
if fd < 0 { fatalError("socket() failed") }
var addr = sockaddr_un()
addr.sun_family = sa_family_t(AF_UNIX)
var pathBytes = Array(sockPath.utf8)
withUnsafeMutableBytes(of: &addr.sun_path) { $0.copyBytes(from: pathBytes) }
let bindResult = withUnsafePointer(to: &addr) {
    $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
        bind(fd, $0, socklen_t(MemoryLayout<sockaddr_un>.size))
    }
}
if bindResult < 0 { fatalError("bind() failed") }
if listen(fd, 8) < 0 { fatalError("listen() failed") }

print("ZYQL classical link (Apple STANDBY) serving \(sockPath)")
while true {
    let client = accept(fd, nil, nil)
    if client < 0 { continue }
    var buffer = [UInt8]()
    var chunk = [UInt8](repeating: 0, count: 4096)
    while !buffer.contains(10) {
        let n = recv(client, &chunk, chunk.count, 0)
        if n <= 0 { break }
        buffer.append(contentsOf: chunk[0..<n])
    }
    if let line = String(bytes: buffer, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
       !line.isEmpty {
        let response = handle(line) + "\n"
        response.withCString { ptr in
            _ = send(client, ptr, strlen(ptr), 0)
        }
    }
    close(client)
}
