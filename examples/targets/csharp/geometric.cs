// Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM (autônomo).
// Familia: geometric_inf - pergunta: < 2 - §EXACT long; §12: ±9,2e18
using System;
using System.Security.Cryptography;
using System.Text;

public class ZephOut {{
    static int cmp(long a, long b) {{ return a.CompareTo(b); }}
    public static void Main() {{
        string DATA = "1|1/2";
        string OP = "<";
        long THR = 2L, UNITS = 2L;
        long A=1L,B=1L,P=1L,Q=2L; // |r|<1 garantido
int c = cmp(A*Q, THR*B*(Q-P));
        bool verdict = (OP == ">" && c > 0) || (OP == "<" && c < 0)
            || (OP == ">=" && c >= 0) || (OP == "<=" && c <= 0)
            || (OP == "==" && c == 0);
        string hex = BitConverter.ToString(
            SHA256.Create().ComputeHash(Encoding.UTF8.GetBytes(DATA)))
            .Replace("-", "").ToLower();
        Console.WriteLine("VERDICT " + (verdict ? 1 : 0));
        Console.WriteLine("HASH " + hex);
        Console.WriteLine("UNITS " + UNITS);
    }}
}}
