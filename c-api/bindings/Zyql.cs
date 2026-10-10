// Zyql.cs — C# binding for the ZYQL C API (P/Invoke).
// Build libzyql (cc -std=c99 -O2 -fPIC -shared zyql.c -o libzyql.so)
// and place it next to the app. PROVIDED, NOT YET EXECUTED HERE
// (no .NET runtime in the authoring sandbox); the pattern is the
// standard one used by SQLite bindings. v0.1.0.
using System;
using System.Runtime.InteropServices;
using System.Text;

namespace Zyql
{
    public enum Status { Ok = 0, Refused = 1, Error = -1 }

    public sealed class Decision : IDisposable
    {
        [DllImport("libzyql", CallingConvention = CallingConvention.Cdecl)]
        private static extern IntPtr zyql_decide(string src);
        [DllImport("libzyql", CallingConvention = CallingConvention.Cdecl)]
        private static extern int zyql_result(IntPtr d);
        [DllImport("libzyql", CallingConvention = CallingConvention.Cdecl)]
        private static extern int zyql_answer(IntPtr d);
        [DllImport("libzyql", CallingConvention = CallingConvention.Cdecl)]
        private static extern IntPtr zyql_receipt(IntPtr d);
        [DllImport("libzyql", CallingConvention = CallingConvention.Cdecl)]
        private static extern void zyql_close(IntPtr d);

        private IntPtr _d;

        private Decision(IntPtr d) { _d = d; }

        public static Decision Decide(string program) =>
            new Decision(zyql_decide(program));

        public Status Status => (Status)zyql_result(_d);
        public int Answer => zyql_answer(_d);   // 1 true, 0 false, -1 null
        public string Receipt => Marshal.PtrToStringAnsi(zyql_receipt(_d));

        public void Dispose() { if (_d != IntPtr.Zero) { zyql_close(_d); _d = IntPtr.Zero; } }
    }
}
