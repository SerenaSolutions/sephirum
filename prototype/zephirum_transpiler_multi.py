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
  .qiskit / .cirq — A PONTE QUÂNTICA: o veredito EXATO (Schmidt,
      Fraction, zero execução) roda DENTRO do ecossistema do SDK;
      o SDK é o gêmeo adversarial (cross-check opcional). Sem o SDK
      instalado o programa imprime SKIP (§12) — nunca finge. Eles
      executam; o ZEPHIRUM prova: o par antitético num só programa.

Famílias cobertas: gauss_series, geometric_inf, arithmetic_mean (a escada
de self-hosting, fatias 1-2) + ENTANGLEMENT nos alvos python/qiskit/cirq
(decisão de Schmidt exata transpilada, ZERO unidades QPU faturadas).
A recusa honesta (§12) é PRESERVADA em todos os alvos: |r| >= 1, estado
nulo e família fora de escopo não geram programa — geram recusa com
motivo explícito. Entanglement NÃO transpila para C/Java/C# nesta fatia
(limites long/128 declarados) — os alvos recusam com §12 visível.

§12 declarado: Java/C# são GERADOS com aritmética long (limites ±9,2e18);
a execução em JVM/.NET é testada onde o toolchain existir — nesta bateria,
C e Python executam de verdade; Java/C# ficam como código verificado
estruturalmente até haver runtime.
"""
import hashlib
from fractions import Fraction

from zephirum_lexer import parse_zephirum
from zephirum_vm import VMFault

UNITS = {"gauss_series": 2, "geometric_inf": 2, "arithmetic_mean": 1,
          "entanglement": 0}   # Schmidt: decidido SEM execução


KSTR = "#x428a2f98 #x71374491 #xb5c0fbcf #xe9b5dba5 #x3956c25b #x59f111f1 #x923f82a4 #xab1c5ed5 #xd807aa98 #x12835b01 #x243185be #x550c7dc3 #x72be5d74 #x80deb1fe #x9bdc06a7 #xc19bf174 #xe49b69c1 #xefbe4786 #x0fc19dc6 #x240ca1cc #x2de92c6f #x4a7484aa #x5cb0a9dc #x76f988da #x983e5152 #xa831c66d #xb00327c8 #xbf597fc7 #xc6e00bf3 #xd5a79147 #x06ca6351 #x14292967 #x27b70a85 #x2e1b2138 #x4d2c6dfc #x53380d13 #x650a7354 #x766a0abb #x81c2c92e #x92722c85 #xa2bfe8a1 #xa81a664b #xc24b8b70 #xc76c51a3 #xd192e819 #xd6990624 #xf40e3585 #x106aa070 #x19a4c116 #x1e376c08 #x2748774c #x34b0bcb5 #x391c0cb3 #x4ed8aa4a #x5b9cca4f #x682e6ff3 #x748f82ee #x78a5636f #x84c87814 #x8cc70208 #x90befffa #xa4506ceb #xbef9a3f7 #xc67178f2"
SHA_LISP = '(defparameter +k+ \'#(%K%))\n(defun rotr32 (x n)\n  (let ((x (logand x #xFFFFFFFF)))\n    (logand #xFFFFFFFF (logior (ash x (- n)) (ash x (- 32 n))))))\n(defun w2hex (n)\n  (let ((s (format nil "~x" n)))\n    (concatenate \'string (subseq "00000000" (min 8 (length s))) s)))\n(defun sha256 (msg)\n  ;; FIPS 180-4 portado — inteiro puro, zero biblioteca\n  (let* ((bytes (map \'vector #\'char-code msg))\n         (len (length bytes))\n         (z (mod (- 56 (+ len 1)) 64))\n         (total (+ len 1 z 8))\n         (buf (make-array total :initial-element 0)))\n    (loop for i below len do (setf (aref buf i) (aref bytes i)))\n    (setf (aref buf len) #x80)\n    (let ((bits (* len 8)))\n      (loop for k from 0 to 7\n            do (setf (aref buf (+ len 1 z k))\n                     (logand 255 (ash bits (* -8 (- 7 k)))))))\n    (let ((h0 #x6a09e667) (h1 #xbb67ae85) (h2 #x3c6ef372) (h3 #xa54ff53a)\n          (h4 #x510e527f) (h5 #x9b05688c) (h6 #x1f83d9ab) (h7 #x5be0cd19))\n      (loop for off from 0 below total by 64\n            do (let ((w (make-array 64)))\n                 (loop for i below 16\n                       do (setf (aref w i)\n                                (logior (ash (aref buf (+ off (* 4 i))) 24)\n                                        (ash (aref buf (+ off (* 4 i) 1)) 16)\n                                        (ash (aref buf (+ off (* 4 i) 2)) 8)\n                                        (aref buf (+ off (* 4 i) 3)))))\n                 (loop for i from 16 below 64\n                       do (let* ((x15 (aref w (- i 15))) (x2 (aref w (- i 2)))\n                                 (s0 (logxor (rotr32 x15 7) (rotr32 x15 18)\n                                             (ash x15 -3)))\n                                 (s1 (logxor (rotr32 x2 17) (rotr32 x2 19)\n                                             (ash x2 -10))))\n                            (setf (aref w i)\n                                  (logand #xFFFFFFFF\n                                          (+ (aref w (- i 16)) s0\n                                             (aref w (- i 7)) s1)))))\n                 (let ((a h0) (b h1) (cc h2) (d h3) (e h4) (f h5)\n                       (g h6) (h h7))\n                   (loop for i below 64\n                         do (let* ((s1 (logxor (rotr32 e 6)\n                                               (rotr32 e 11) (rotr32 e 25)))\n                                   (ch (logior (logand e f)\n                                               (logand (lognot e) g)))\n                                   (t1 (+ h s1 ch (aref +k+ i) (aref w i)))\n                                   (s0 (logxor (rotr32 a 2)\n                                               (rotr32 a 13) (rotr32 a 22)))\n                                   (maj (logior (logand a b)\n                                                (logior (logand a cc)\n                                                        (logand b cc))))\n                                   (t2 (+ s0 maj)))\n                              (setf h g g f f e)\n                              (setf e (logand #xFFFFFFFF (+ d t1)))\n                              (setf d cc cc b b a)\n                              (setf a (logand #xFFFFFFFF (+ t1 t2)))))\n                   (setf h0 (logand #xFFFFFFFF (+ h0 a)))\n                   (setf h1 (logand #xFFFFFFFF (+ h1 b)))\n                   (setf h2 (logand #xFFFFFFFF (+ h2 cc)))\n                   (setf h3 (logand #xFFFFFFFF (+ h3 d)))\n                   (setf h4 (logand #xFFFFFFFF (+ h4 e)))\n                   (setf h5 (logand #xFFFFFFFF (+ h5 f)))\n                   (setf h6 (logand #xFFFFFFFF (+ h6 g)))\n                   (setf h7 (logand #xFFFFFFFF (+ h7 h))))))\n      (concatenate \'string\n                   (w2hex h0) (w2hex h1) (w2hex h2) (w2hex h3)\n                   (w2hex h4) (w2hex h5) (w2hex h6) (w2hex h7)))))'


def _compile_src(src):
    blocks = parse_zephirum(src)
    model = blocks["MODEL"]
    fam = model.get("type")
    if fam not in UNITS:
        raise VMFault("família %r fora dos alvos desta fatia (§12)" % fam)
    q = blocks["ASK"]["question"]
    parts = q.rsplit(" ", 2)
    op = parts[1]
    if fam == "entanglement":
        toks = [x.strip() for x in model["state"].split(",")]
        if len(toks) not in (4, 8):
            raise VMFault("estado com %d amplitudes — precisa 4 ou 8 (§12: "
                          "recusa antes de gerar qualquer programa)"
                          % len(toks))
        data = [Fraction(t) for t in toks]
        if sum(x * x for x in data) == 0:
            raise VMFault("estado nulo não é estado quântico (§12: "
                          "recusa antes de gerar qualquer programa)")
        target = parts[0]
        if target not in ("entangled", "concurrence"):
            raise VMFault("pergunta %r fora da família de emaranhamento "
                          "(§12)" % target)
        if len(toks) == 8 and target != "entangled":
            raise VMFault("concurrence é medida de 2 qubits — 3 qubits "
                          "respondem apenas 'entangled' (§12)")
        # threshold FRACIONÁRIO exato (decimal de token, não float)
        return {"fam": fam, "op": op, "thr": Fraction(parts[2]),
                "target": target, "data": data,
                "data_str": "|".join(str(v) for v in data),
                "input_hash": hashlib.sha256(
                    "|".join(str(v) for v in data).encode()).hexdigest(),
                "units": UNITS[fam]}
    thr = int(parts[2])
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
    elif fam == "entanglement":
        return _gen_entangle_exact(c, sdk=None)
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


def _ent_exact_body(c):
    """Núcleo de decisão exato (Schmidt, Fraction) — transpilado."""
    if c.get("target") == "entangled":
        dec = ('TARGET = "entangled"\n'
               'THR = Fraction(%r)\n'
               'N = A*A + B*B + C_*C_ + D*D\n'
               'DET = A*D - B*C_\n'
               'v = Fraction(1 if DET != 0 else 0)\n'
               'verdict = {">": v > THR, "<": v < THR, ">=": v >= THR,\n'
               '           "<=": v <= THR, "==": v == THR}[OP]')
        return dec % str(c["thr"])
    dec = ('TARGET = "concurrence"\n'
           'THR = Fraction(%r)\n'
           'N = A*A + B*B + C_*C_ + D*D\n'
           'DET = A*D - B*C_\n'
           'sq, tsq = 4*DET*DET, THR*THR*N*N\n'
           'if OP == ">":\n'
           '    verdict = True if THR < 0 else sq > tsq\n'
           'elif OP == ">=":\n'
           '    verdict = True if THR <= 0 else sq >= tsq\n'
           'elif OP == "<":\n'
           '    verdict = False if THR <= 0 else sq < tsq\n'
           'elif OP == "<=":\n'
           '    verdict = False if THR < 0 else sq <= tsq\n'
           'else:\n'
           '    verdict = sq == tsq')
    return dec % str(c["thr"])


def _gen_entangle3_exact(c, sdk):
    """3 qubits: separabilidade plena exata (Fraction) + gêmeo SDK."""
    amps = c["data"]
    decl = ("AMPS = [%s]\nDATA = %r\nOP = %r\n"
            % (", ".join("Fraction(%r)" % str(a) for a in amps),
               c["data_str"], c["op"]))
    body = (
        '# Família: entanglement (3 qubits) · pergunta: entangled %s %s\n'
        '# TOTALMENTE SEPARÁVEL <=> posto 1 do achatamento (q0) E det2=0\n'
        'R0, R1 = AMPS[:4], AMPS[4:]\n'
        'rank1 = all(R0[j]*R1[k] == R0[k]*R1[j]\n'
        '            for j in range(4) for k in range(j+1, 4))\n'
        'if rank1:\n'
        '    phi = R0 if any(R0) else R1\n'
        '    ent = (phi[0]*phi[3] - phi[1]*phi[2]) != 0\n'
        'else:\n'
        '    ent = True\n'
        'THR = Fraction(%r)\n'
        'v = Fraction(1 if ent else 0)\n'
        'verdict = {">": v > THR, "<": v < THR, ">=": v >= THR,\n'
        '           "<=": v <= THR, "==": v == THR}[OP]\n'
        'print("VERDICT", 1 if verdict else 0)\n'
        'print("HASH", hashlib.sha256(DATA.encode()).hexdigest())\n'
        'print("UNITS", %d)\n'
        'print("QPU_UNITS_BILLED", 0)\n'
        % (c["op"], str(c["thr"]), str(c["thr"]), c["units"]))
    head = ('#!/usr/bin/env python3\n'
            '# Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM — ALVO %s.\n'
            '# Família: entanglement · 3 qubits · separabilidade plena.\n'
            '# O veredito EXATO é do ZEPHIRUM (Fraction, ZERO execução);\n'
            '# o SDK é o gêmeo adversarial; ausente => SKIP §12.\n'
            'import hashlib\n'
            'from fractions import Fraction\n\n'
            '%s\n%s\n' % (sdk or "EXATO (sem SDK)", decl, body))
    if sdk == "qiskit":
        head += ('try:\n'
                 '    import numpy as np\n'
                 '    from qiskit.quantum_info import Statevector\n'
                 '    sv = Statevector([float(x) for x in AMPS])\n'
                 '    M = np.asarray(sv.data).reshape(2, 4)\n'
                 '    print("SDK_CROSS_CHECK", "qiskit flatten rank = %d '
                 '(ruído float em torno do veredito exato)"\n'
                 '          % np.linalg.matrix_rank(M, tol=1e-9))\n'
                 'except ImportError:\n'
                 '    print("SDK_CROSS_CHECK SKIP (§12): qiskit não '
                 'instalado neste ambiente — o gateway nunca finge")\n'
                 'except Exception as e:\n'
                 '    print("SDK_CROSS_CHECK FAIL (§12): o SDK não '
                 'representa este estado:", e)\n')
    return head


def _gen_openqasm(c):
    """ALVO OpenQASM 3 (fusão internacional): o ZEPHIRUM emite o
    artefato de EXECUÇÃO no padrão que qualquer SDK absorve. O veredito
    exato permanece do núcleo; o QASM carrega o estado e, quando o
    padrão de amplitudes é conhecido (Bell/GHZ/antipodal), o circuito
    de preparação. Caso geral: vetor exato em comentário e preparação
    delegada ao SDK absorvente (§12 — nunca finge)."""
    if c["fam"] != "entanglement":
        return ("// ZEPHIRUM -> OpenQASM 3: ainda não coberto nesta fatia "
                "(§12)\n")
    amps = c["data"]
    nz = [(i, a) for i, a in enumerate(amps) if a != 0]
    n = len(amps)
    hdr = ("OPENQASM 3.0;\ninclude \"stdgates.inc\";\n"
           "// Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM\n"
           "// Pergunta: %s %s %s (decidida EXATAMENTE pelo núcleo "
           "Zephirum, sem execução)\n"
           "// Estado exato (Fraction): %s\n"
           % (c.get("target", "entangled"), c["op"], str(c["thr"]),
              c["data_str"]))
    if n == 4 and [i for i, _ in nz] == [0, 3] and nz[0][1] == nz[1][1]:
        # c(|00>+|11>)/1: classe Bell
        return (hdr + "qubit[2] q;\nh q[0];\ncx q[0], q[1];\n")
    if n == 8 and len(nz) == 2 and nz[0][0] == 0 and nz[1][0] == 7 \
            and abs(nz[0][1]) == abs(nz[1][1]):
        # c0|000> + c1|111>: classe GHZ (fase relativa em z)
        import math
        theta = 2 * math.atan2(abs(float(nz[1][1])), abs(float(nz[0][1])))
        gate = ("ry(%r) q[0];" % theta) + ("\nz q[0];" if
               (nz[1][1] < 0) != (nz[0][1] < 0) else "")
        return (hdr + "qubit[3] q;\n%s\ncx q[0], q[1];\ncx q[0], q[2];\n"
                % gate)
    return (hdr + "// Preparação geral delegada ao SDK absorvente "
            "(§12);\n// o vetor exato acima é a fonte de verdade.\n"
            "qubit[%d] q;\n" % (3 if n == 8 else 2))


def _gen_entangle_exact(c, sdk):
    """Programa autônomo: veredito EXATO do ZEPHIRUM + gêmeo SDK opcional.

    O SDK (qiskit/cirq) é o ADVERSÁRIO: executa o caminho que o
    certificado eliminou. Sem SDK instalado => SKIP §12 — nunca finge.
    """
    if len(c["data"]) == 8:
        return _gen_entangle3_exact(c, sdk)
    a, b, cc, d = c["data"]
    decl = ('A = Fraction(%r)\nB = Fraction(%r)\nC_ = Fraction(%r)\n'
            'D = Fraction(%r)\nDATA = %r\nOP = %r\n'
            % (str(a), str(b), str(cc), str(d), c["data_str"], c["op"]))
    head = ('#!/usr/bin/env python3\n'
            '# Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM — ALVO %s.\n'
            '# Família: entanglement · pergunta: %s %s %s\n'
            '# O veredito EXATO é do ZEPHIRUM (critério de Schmidt,\n'
            '# Fraction, ZERO execução). O SDK é o gêmeo adversarial;\n'
            '# ausente => SKIP §12.\n'
            'import hashlib\n'
            'from fractions import Fraction\n\n'
            '%s\n%s\n\n'
            'print("VERDICT", 1 if verdict else 0)\n'
            'print("HASH", hashlib.sha256(DATA.encode()).hexdigest())\n'
            'print("UNITS", %d)\n'
            'print("QPU_UNITS_BILLED", 0)\n'
            'print("SDK_PATH_ELIMINATED",\n'
            '      "statevector + eigendecomposition (8 unidades, salvas '
            'pelo "\n'
            '      "critério de Schmidt)")\n'
            % (sdk or "EXATO (sem SDK)", c.get("target", "entangled"),
               c["op"], str(c["thr"]), decl, _ent_exact_body(c),
               c["units"]))
    if sdk == "qiskit":
        head += ('try:\n'
                 '    import numpy as np\n'
                 '    from qiskit.quantum_info import Statevector\n'
                 '    sv = Statevector([float(A), float(B), float(C_), '
                 'float(D)])\n'
                 '    m = np.asarray(sv.data).reshape(2, 2)\n'
                 '    cf = 2 * abs(m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0])'
                 ' / float(N)\n'
                 '    print("SDK_CROSS_CHECK", "qiskit Statevector '
                 'concurrence = %.17g (ruído float em torno do veredito '
                 'exato)" % cf)\n'
                 'except ImportError:\n'
                 '    print("SDK_CROSS_CHECK SKIP (§12): qiskit não '
                 'instalado neste ambiente — o gateway nunca finge")\n'
                 'except Exception as e:\n'
                 '    print("SDK_CROSS_CHECK FAIL (§12): o SDK não '
                 'representa este estado:", e)\n')
    elif sdk == "cirq":
        head += ('try:\n'
                 '    import numpy as np\n'
                 '    import cirq\n'
                 '    # o Cirq VALIDA a normalização: o estado exato cru\n'
                 '    # (norm != 1) não é representável lá. A pista do\n'
                 '    # gêmeo normaliza por float — perde exatidão, e é\n'
                 '    # exatamente isso que ela existe para mostrar.\n'
                 '    _v = [float(A), float(B), float(C_), float(D)]\n'
                 '    _n = sum(x * x for x in _v) ** 0.5\n'
                 '    sv = cirq.to_valid_state_vector(\n'
                 '        [x / _n for x in _v])\n'
                 '    m = np.asarray(sv).reshape(2, 2)\n'
                 '    cf = 2 * abs(m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0])\n'
                 '    print("SDK_CROSS_CHECK", "cirq Statevector '
                 'concurrence = %.17g (ruído float em torno do veredito '
                 'exato)" % cf)\n'
                 'except ImportError:\n'
                 '    print("SDK_CROSS_CHECK SKIP (§12): cirq não '
                 'instalado neste ambiente — o gateway nunca finge")\n'
                 'except Exception as e:\n'
                 '    print("SDK_CROSS_CHECK FAIL (§12): o SDK não '
                 'representa este estado:", e)\n')
    return head


def _gen_qiskit(c):
    return _gen_entangle_exact(c, sdk="qiskit")


def _gen_cirq(c):
    return _gen_entangle_exact(c, sdk="cirq")


def _gen_c(c):
    return _C_TMPL.format(sha=_C_SHA, decide_c=_c_decide(c), **c)





def _gen_lisp(c):
    """Alvo COMMON LISP — racional exato NATIVO, SHA-256 FIPS 180-4
    embutido. A ironia honesta do painel: a linguagem mais ANTIGA
    (1958) e a mais EXATA — racionais sao primitivos do CL. So ANSI
    CL, zero biblioteca, programa autonomo.
    """
    fam, op, thr = c["fam"], c["op"], c["thr"]
    head = (";;;; SEPHIRUM -> Common Lisp (autonomo, so ANSI CL)\n"
            ";;;; Familia: %s | pergunta: %s %s\n" % (fam, op, thr))
    pre = SHA_LISP.replace("%K%", KSTR)
    body = ("(defparameter data \"%s\")\n(defparameter op \"%s\")\n"
            % (c["data_str"], op))
    if fam == "gauss_series":
        body += ("(defparameter n %d)\n"
                 "(defparameter val (/ (* n (+ n 1)) 2))\n"
                 "(defparameter thr %s)\n"
                 "(defparameter verdict (cond ((string= op \">\") (> val thr))"
                 " ((string= op \"<\") (< val thr))"
                 " ((string= op \">=\") (>= val thr))"
                 " ((string= op \"<=\") (<= val thr))))\n"
                 % (c["data"][0], thr))
    elif fam == "arithmetic_mean":
        body += ("(defparameter n %d)\n"
                 "(defparameter val (/ (+ n 1) 2))\n"
                 "(defparameter thr %s)\n"
                 "(defparameter verdict (cond ((string= op \">\") (> val thr))"
                 " ((string= op \"<\") (< val thr))"
                 " ((string= op \">=\") (>= val thr))"
                 " ((string= op \"<=\") (<= val thr))))\n"
                 % (c["data"][0], thr))
    elif fam == "entanglement":
        if len(c["data"]) == 8:
            body += (";; 3 qubits: nao coberto nesta fatia (§12) — o "
                     "veredito exato esta no nucleo C/Python; alvos "
                     "qiskit/openqasm carregam o estado.\n")
            return body
        A, B, C_, D = c["data"]
        body += ("(defparameter thr %s)\n" % str(thr))
        if c.get("target") == "entangled":
            body += ("(let* ((n (+ (* %s %s) (* %s %s) (* %s %s) (* %s %s)))\n"
                     "      (det (- (* %s %s) (* %s %s))))\n"
                     "  (let ((v (if (/= det 0) 1 0)))\n"
                     "    (format t \"VERDICT ~d~%%\" (if (= v thr) 1 0))))\n"
                     % (A, A, B, B, C_, C_, D, D, A, D, B, C_))
        else:
            body += ("(let* ((n (+ (* %s %s) (* %s %s) (* %s %s) (* %s %s)))\n"
                     "      (det (- (* %s %s) (* %s %s)))\n"
                     "      (sq (* 4 det det))\n"
                     "      (tsq (* thr thr n n)))\n"
                     "  (cond ((string= op \">\") (setq verdict (if (< thr 0) t (> sq tsq))))\n"
                     "        ((string= op \">=\") (setq verdict (if (< thr 0) nil (if (= thr 0) t (>= sq tsq)))))\n"
                     "        ((string= op \"<\") (setq verdict (if (<= thr 0) nil (< sq tsq))))\n"
                     "        ((string= op \"<=\") (setq verdict (if (< thr 0) nil (<= sq tsq))))\n"
                     "        (t (setq verdict (= sq tsq))))\n"
                     "  (format t \"VERDICT ~d~%%\" (if verdict 1 0)))\n"
                     % (A, A, B, B, C_, C_, D, D, A, D, B, C_))
    else:
        a, r = c["data"]
        body += ("(defparameter a %s)\n(defparameter r %s)\n"
                 "(defparameter val (/ a (- 1 r)))\n"
                 "(defparameter thr %s)\n"
                 "(defparameter verdict (cond ((string= op \">\") (> val thr))"
                 " ((string= op \"<\") (< val thr))"
                 " ((string= op \">=\") (>= val thr))"
                 " ((string= op \"<=\") (<= val thr))))\n"
                 % (a, r, thr))
    if fam not in ("entanglement",):
        body += '(format t "VERDICT ~d~%" (if verdict 1 0))\n'
    body += ('(format t "HASH ~a~%" (string-upcase (sha256 data)))\n'
             '(format t "UNITS ~d~%" ' + str(c["units"]) + ')\n')
    return head + pre + "\n" + body


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
    cert = {"fam": c["fam"], "op": c["op"], "thr": c["thr"],
            "input_hash": c["input_hash"], "units": c["units"],
            "data_str": c["data_str"]}
    if c["fam"] == "entanglement":
        fora = ("§12 RECUSA: entanglement transpila para python/qiskit/"
                "cirq nesta fatia — aritmética long/128 não cobre o "
                "regime; gerar código errado seria pior que recusar")
        return {"python": _gen_python(c), "qiskit": _gen_qiskit(c),
                "openqasm": _gen_openqasm(c),
                "cirq": _gen_cirq(c), "lisp": _gen_lisp(c),
                "c": fora, "java": fora, "csharp": fora, "cert": cert}
    fora_q = ("§12: os alvos qiskit/cirq cobrem a família entanglement "
              "(a ponte quântica) — a família %r transpila para "
              "python/c/java/csharp" % c["fam"])
    return {"python": _gen_python(c), "c": _gen_c(c),
            "java": _gen_java(c), "csharp": _gen_csharp(c),
            "lisp": _gen_lisp(c),
            "qiskit": fora_q, "cirq": fora_q, "cert": cert}


if __name__ == "__main__":
    import sys
    src = open(sys.argv[1]).read()
    out = transpile(src)
    for tgt in ("python", "c", "java", "csharp", "qiskit", "cirq"):
        print("=== %s ===" % tgt)
        print(out[tgt])
