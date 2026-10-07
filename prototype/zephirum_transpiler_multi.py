#!/usr/bin/env python3
"""
ZEPHIRUM TRANSPILER MULTI-ALVO — uma fonte, N linguagens do mundo.
====================================================================

A finalidade: o Zephirum virar LINGUAGEM INDEPENDENTE — o mesmo programa
decide a mesma pergunta em qualquer ecossistema (Python, C, Java, C#),
cada um com aritmética exata PRÓPRIA e SHA-256 embutido. Nada de runtime
Zephirum: o código gerado é autônomo e verifica o certificado sozinho.

Alvos desta fatia:
  .py  — Fraction exata (fractions), hashlib
  .c   — __int128 + SHA-256 (FIPS 180-4) embutido, gcc -std=c11
  .java— long com cruzamento de produtos + MessageDigest
  .cs  — long + SHA256.Create

Famílias cobertas: gauss_series, geometric_inf, arithmetic_mean (a escada
de self-hosting, fatias 1-2). A recusa honesta (§12) é PRESERVADA em todos
os alvos: |r| >= 1 não gera programa — gera recusa.

§12 declarado: Java/C# são GERADOS com aritmética long (limites ±9,2e18);
a execução em JVM/.NET é testada onde o toolchain existir — nesta bateria,
C e Python executam de verdade; Java/C# ficam como código verificado
estruturalmente até haver runtime.
"""
import hashlib
from fractions import Fraction

from zephirum_lexer import parse_zephirum
from zephirum_vm import VMFault

UNITS = {"gauss_series": 2, "geometric_inf": 2, "arithmetic_mean": 1}


def _compile_src(src):
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    fam = model.get("type")
    if fam not in UNITS:
        raise VMFault("família %r fora dos alvos desta fatia (§12)" % fam)
    q = blocks["ASK"]["question"]
    parts = q.rsplit(" ", 2)
    op, thr = parts[1], int(parts[2])
    if fam == "gauss_series":
        n = int(model["n"])
        if n < 1:
            raise VMFault("n < 1: série vazia (§12)")
        data = [n]
    elif fam == "arithmetic_mean":
        n = int(model["n"])
        if n < 1:
            raise VMFault("n < 1: média vazia não existe (§12)")
        data = [n]
    else:
        a, r = Fraction(model["a"]), Fraction(model["r"])
        if abs(r) >= 1:
            raise VMFault("r=%s não converge (§12): recusa também no "
                          "transpilador — o alvo NÃO ganha série infinita "
                          "divergente" % r)
        data = [a, r]
    data_str = "|".join(str(v) for v in data)
    ih = hashlib.sha256(data_str.encode()).hexdigest()
    return {"fam": fam, "op": op, "thr": thr, "data": data,
            "data_str": data_str, "input_hash": ih, "units": UNITS[fam]}


# ---------------------------------------------------------------- C
_C_SHA = r"""
typedef __int128 i128;
#define LL(x) ((__int128)(x))
static int cmpv(i128 l, i128 r){ return l<r?-1:(l>r?1:0); }
static const uint32_t K256[64] = {
  0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,
  0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
  0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,
  0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
  0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,
  0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
  0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,
  0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
  0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,
  0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
  0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
#define ROR(x,n) (((x)>>(n))|((x)<<(32-(n))))
static void sha256(const char*s, uint8_t out[32]){
  uint64_t bl=(uint64_t)strlen(s);
  size_t total=(size_t)(((bl+8)/64+1)*64);
  uint8_t*m=calloc(total,1); memcpy(m,s,bl); m[bl]=0x80;
  uint64_t bits=bl*8;
  for(int i=0;i<8;i++) m[total-1-i]=(uint8_t)((bits>>(8*i))&0xFF);
  uint32_t h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                 0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
  for(size_t off=0;off<total;off+=64){
    uint32_t w[64];
    for(int i=0;i<16;i++)
      w[i]=((uint32_t)m[off+4*i]<<24)|((uint32_t)m[off+4*i+1]<<16)|
           ((uint32_t)m[off+4*i+2]<<8)|(uint32_t)m[off+4*i+3];
    for(int i=16;i<64;i++){
      uint32_t s0=ROR(w[i-15],7)^ROR(w[i-15],18)^(w[i-15]>>3);
      uint32_t s1=ROR(w[i-2],17)^ROR(w[i-2],19)^(w[i-2]>>10);
      w[i]=w[i-16]+s0+w[i-7]+s1;
    }
    uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
    for(int i=0;i<64;i++){
      uint32_t S1=ROR(e,6)^ROR(e,11)^ROR(e,25);
      uint32_t ch=(e&f)^((~e)&g);
      uint32_t t1=hh+S1+ch+K256[i]+w[i];
      uint32_t S0=ROR(a,2)^ROR(a,13)^ROR(a,22);
      uint32_t maj=(a&b)^(a&c)^(b&c);
      uint32_t t2=S0+maj;
      hh=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;
  }
  for(int i=0;i<8;i++){
    out[4*i]=(uint8_t)(h[i]>>24);out[4*i+1]=(uint8_t)(h[i]>>16);
    out[4*i+2]=(uint8_t)(h[i]>>8);out[4*i+3]=(uint8_t)h[i];
  }
  free(m);
}
static void hex32(const uint8_t d[32], char out[65]){
  for(int i=0;i<32;i++) sprintf(out+2*i,"%02x",d[i]);
  out[64]=0;
}
static int decide(int c, const char*op){
  return (strcmp(op,">")==0&&c>0)||(strcmp(op,"<")==0&&c<0)||
         (strcmp(op,">=")==0&&c>=0)||(strcmp(op,"<=")==0&&c<=0)||
         (strcmp(op,"==")==0&&c==0);
}
"""

_C_TMPL = """/* Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM (autônomo — sem runtime).
 * Família: {fam} · pergunta: sum/mean {op} {thr}
 * §EXACT: aritmética __int128; §12: limites ±9,2e18. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
{sha}
int main(void){{
  /* certificado embutido (fonte ZEPHIRUM) */
  const char *DATA = "{data_str}";
  const char *OP = "{op}";
  long long THR = {thr}LL;
  long long UNITS = {units}LL;
{decide_c}
  uint8_t d[32]; char hex[65];
  sha256(DATA, d); hex32(d, hex);
  printf("VERDICT %d\\nHASH %s\\nUNITS %lld\\n", verdict, hex, UNITS);
  return 0;
}}
"""


def _c_decide(c):
    fam, op, thr = c["fam"], c["op"], c["thr"]
    if fam == "gauss_series":
        n = c["data"][0]
        return ("  long long n = %dLL;\n"
                "  int verdict = decide(cmpv((i128)n*(LL(n)+1), LL(2)*LL(THR)), OP);"
                % n)
    if fam == "arithmetic_mean":
        n = c["data"][0]
        return ("  long long n = %dLL;\n"
                "  int verdict = decide(cmpv(LL(n)+1, LL(2)*LL(THR)), OP);" % n)
    a, r = c["data"]
    return ("  long long A=%dLL,B=%dLL,P=%dLL,Q=%dLL;\n"
            "  /* |r|<1 garantido pelo transpilador; S=A*Q/(B*(Q-P)) */\n"
            "  int verdict = decide(cmpv(LL(A)*LL(Q), LL(THR)*LL(B)*(LL(Q)-LL(P))), OP);"
            % (a.numerator, a.denominator, r.numerator, r.denominator))


# ------------------------------------------------------------- Python
def _gen_python(c):
    fam, op, thr = c["fam"], c["op"], c["thr"]
    if fam == "gauss_series":
        body = "val = Fraction(n*(n+1), 2)"
        decl = "n = %d" % c["data"][0]
    elif fam == "arithmetic_mean":
        body = "val = Fraction(n+1, 2)"
        decl = "n = %d" % c["data"][0]
    else:
        a, r = c["data"]
        body = "val = a / (1 - r)"
        decl = "a = Fraction(%d, %d)\nr = Fraction(%d, %d)" % (
            a.numerator, a.denominator, r.numerator, r.denominator)
    return '''#!/usr/bin/env python3
# Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM (autônomo).
# Família: %s · pergunta: %s %s
import hashlib
from fractions import Fraction

DATA = %r
OP = %r
THR = Fraction(%d)

%s
%s

verdict = {">": val > THR, "<": val < THR,
           ">=": val >= THR, "<=": val <= THR}[OP]
print("VERDICT", 1 if verdict else 0)
print("HASH", hashlib.sha256(DATA.encode()).hexdigest())
print("UNITS", %d)
''' % (fam, op, thr, c["data_str"], op, thr, decl, body, c["units"])


def _gen_c(c):
    return _C_TMPL.format(sha=_C_SHA, decide_c=_c_decide(c), **c)


def _gen_java(c):
    fam, op, thr = c["fam"], c["op"], c["thr"]
    if fam == "gauss_series":
        dec = "long n = %dL;\nint c = cmp128(n*(n+1L), 2L*THR);" % c["data"][0]
    elif fam == "arithmetic_mean":
        dec = "long n = %dL; int c = cmp128(n+1L, 2L*THR);" % c["data"][0]
    else:
        a, r = c["data"]
        dec = ("long A=%dL,B=%dL,P=%dL,Q=%dL; // |r|<1 garantido\n"
               "int c = cmp128(A*Q, THR*B*(Q-P));"
               % (a.numerator, a.denominator, r.numerator, r.denominator))
    return '''// Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM (autônomo).
// Familia: %s - pergunta: %s %s - §EXACT long; §12: ±9,2e18
import java.security.MessageDigest;

public class ZephOut {{
    static int cmp128(long a, long b) {{
        // produtos cruzados no intervalo long desta fatia (§12)
        return Long.compare(a, b);
    }}
    public static void main(String[] args) throws Exception {{
        String DATA = %s;
        String OP = %s;
        long THR = %dL, UNITS = %dL;
        %s
        boolean verdict = (OP.equals(">") && c > 0) || (OP.equals("<") && c < 0)
            || (OP.equals(">=") && c >= 0) || (OP.equals("<=") && c <= 0)
            || (OP.equals("==") && c == 0);
        byte[] h = MessageDigest.getInstance("SHA-256").digest(DATA.getBytes());
        StringBuilder hex = new StringBuilder();
        for (byte b : h) hex.append(String.format("%%02x", b));
        System.out.println("VERDICT " + (verdict ? 1 : 0));
        System.out.println("HASH " + hex);
        System.out.println("UNITS " + UNITS);
    }}
}}
''' % (fam, op, thr, repr(c["data_str"]).replace("'", '"'),
       repr(op).replace("'", '"'), thr, c["units"], dec)


def _gen_csharp(c):
    fam, op, thr = c["fam"], c["op"], c["thr"]
    if fam == "gauss_series":
        dec = "long n = %dL; int c = cmp(n * (n + 1), 2 * THR);" % c["data"][0]
    elif fam == "arithmetic_mean":
        dec = "long n = %dL; int c = cmp(n + 1, 2 * THR);" % c["data"][0]
    else:
        a, r = c["data"]
        dec = ("long A={0}L,B={1}L,P={2}L,Q={3}L; // |r|<1 garantido\n"
               "int c = cmp(A*Q, THR*B*(Q-P));").format(
            a.numerator, a.denominator, r.numerator, r.denominator)
    return '''// Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM (autônomo).
// Familia: %s - pergunta: %s %s - §EXACT long; §12: ±9,2e18
using System;
using System.Security.Cryptography;
using System.Text;

public class ZephOut {{
    static int cmp(long a, long b) {{ return a.CompareTo(b); }}
    public static void Main() {{
        string DATA = "%s";
        string OP = "%s";
        long THR = %dL, UNITS = %dL;
        %s
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
''' % (fam, op, thr, c["data_str"], op, thr, c["units"], dec)


def transpile(src):
    """Fonte ZEPHIRUM -> dict de programas autônomos (4 alvos).

    Recusa (§12) em TODOS os alvos: |r| >= 1, n < 1, família desconhecida.
    """
    c = _compile_src(src)
    return {"python": _gen_python(c), "c": _gen_c(c),
            "java": _gen_java(c), "csharp": _gen_csharp(c),
            "cert": {"fam": c["fam"], "op": c["op"], "thr": c["thr"],
                     "input_hash": c["input_hash"], "units": c["units"],
                     "data_str": c["data_str"]}}


if __name__ == "__main__":
    import sys
    src = open(sys.argv[1]).read()
    out = transpile(src)
    for tgt in ("python", "c", "java", "csharp"):
        print("=== %s ===" % tgt)
        print(out[tgt])
