// CLASSICAL LINK — Windows STANDBY host (named pipe, JSON lines).
// Wire protocol: SPEC.md v1.0 (identical to the reference host).
//
// STATUS: STANDBY SKELETON. The transport (named pipe server + JSON
// request/response) is complete; the engine wiring is a marked TODO.
// On a Windows machine, route the parsed request to the ZYQL engine
// (zref.exe or the Python core) and return its certified answer.
// The host NEVER decides; Section 12 refusals travel the wire as-is.
//
// Build (standby check): csc ZyqlVerdictHost.cs
// Run: ZyqlVerdictHost.exe

using System;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;

namespace Zephirum.ClassicalLink
{
    public static class ZyqlVerdictHost
    {
        private const string PipeName = "zyql-verdict";

        public static void Main()
        {
            Console.WriteLine("ZYQL classical link (Windows STANDBY) serving \\\\.\\pipe\\" + PipeName);
            while (true)
            {
                using (var server = new NamedPipeServerStream(
                    PipeName, PipeDirection.InOut, 4))
                {
                    server.WaitForConnection();
                    using (var reader = new StreamReader(server, Encoding.UTF8))
                    using (var writer = new StreamWriter(server, Encoding.UTF8))
                    {
                        string line = reader.ReadLine();
                        if (line != null)
                        {
                            string response = Handle(line);
                            writer.WriteLine(response);
                            writer.Flush();
                        }
                    }
                }
            }
        }

        // One request line in, one response line out (SPEC.md v1.0).
        private static string Handle(string line)
        {
            // TODO(engine-wiring): parse `line`, forward to the ZYQL exact
            // core (zref.exe subprocess or embedded Python core), and
            // serialize the core's certified answer. Until wired, this
            // STANDBY host answers honestly:
            return "{\"refused\":true,\"reason\":\"standby host: engine not wired on this machine\",\"section\":\"12\"}";
        }
    }
}
