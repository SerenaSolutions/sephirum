/*
 * ZREF — motor de referência do ZEPHIRUM em C puro (C11).
 * ========================================================
 *
 * O passo concreto para EXCLUIR o Python: este binário lê a FONTE
 * ZEPHIRUM (blocos ASK/CONTRACT/MODEL) diretamente, decide a pergunta
 * com aritmética exata própria (__int128, produtos cruzados, sem
 * raiz, sem float) e emite o recibo normativo:
 *
 *   VERDICT 0|1  ·  HASH sha256(data_string canónica)  ·  UNITS
 *
 * Reusa as primitivas auditadas do zverify.c (SHA-256 FIPS 180-4 e
 * os vereditos por produto cruzado, 520/520) e acrescenta: parser da
 * linguagem, frações exatas com decimais, e a família ENTANGLEMENT
 * com o critério de Schmidt sem raiz.
 *
 * Muros declarados (§12 em C, como no zverify):
 *   . amplitudes |num|,|den| <= 10^4  — comum D = lcm <= 10^16
 *   . threshold  |num|,|den| <= 10^3
 *   . gauss/mean n <= 10^12; geofin r^(n+1) em 64 bits
 *   Fora do muro => OVERFLOW honesto (exit 3), nunca mentira.
 *   Recusas estruturais (r=1, |r|>=1, estado nulo) => RECUSA (exit 2).
 *
 * Uso: zref <fonte.zeph>          (saída: recibo em stdout)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

/* ------------------------------------------------------------ SHA-256 */
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

static void sha256(const char *s, uint8_t out[32]) {
    uint64_t bl = (uint64_t)strlen(s);
    size_t total = (size_t)(((bl + 8) / 64 + 1) * 64);
    uint8_t *m = calloc(total, 1);
    memcpy(m, s, bl);
    m[bl] = 0x80;
    uint64_t bits = bl * 8;
    for (int i = 0; i < 8; i++)
        m[total - 1 - i] = (uint8_t)((bits >> (8 * i)) & 0xFF);
    uint32_t h[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                     0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    for (size_t off = 0; off < total; off += 64) {
        uint32_t w[64];
        for (int i = 0; i < 16; i++)
            w[i] = ((uint32_t)m[off+4*i]<<24)|((uint32_t)m[off+4*i+1]<<16)|
                   ((uint32_t)m[off+4*i+2]<<8)|(uint32_t)m[off+4*i+3];
        for (int i = 16; i < 64; i++) {
            uint32_t s0 = ROR(w[i-15],7)^ROR(w[i-15],18)^(w[i-15]>>3);
            uint32_t s1 = ROR(w[i-2],17)^ROR(w[i-2],19)^(w[i-2]>>10);
            w[i] = w[i-16]+s0+w[i-7]+s1;
        }
        uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
        for (int i = 0; i < 64; i++) {
            uint32_t S1 = ROR(e,6)^ROR(e,11)^ROR(e,25);
            uint32_t ch = (e&f)^((~e)&g);
            uint32_t t1 = hh+S1+ch+K256[i]+w[i];
            uint32_t S0 = ROR(a,2)^ROR(a,13)^ROR(a,22);
            uint32_t maj = (a&b)^(a&c)^(b&c);
            uint32_t t2 = S0+maj;
            hh=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
        }
        h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d;
        h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=hh;
    }
    for (int i = 0; i < 8; i++) {
        out[4*i]   = (uint8_t)(h[i]>>24); out[4*i+1] = (uint8_t)(h[i]>>16);
        out[4*i+2] = (uint8_t)(h[i]>>8);  out[4*i+3] = (uint8_t)h[i];
    }
    free(m);
}

static void hex32(const uint8_t d[32], char out[65]) {
    for (int i = 0; i < 32; i++) sprintf(out + 2*i, "%02x", d[i]);
    out[64] = 0;
}

/* --------------------------------------------------- aritmética exacta */
typedef __int128 i128;
#define LL(x) ((__int128)(x))
#define OVMAX LL(9223372036854775807LL)

static int cmpv(i128 l, i128 r) { return l < r ? -1 : (l > r ? 1 : 0); }

static long long gcd_ll(long long a, long long b) {
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    while (b) { long long t = a % b; a = b; b = t; }
    return a;
}

/* fração exata reduzida: den > 0 */
typedef struct { long long p, q; } Frac;

static Frac frac_norm(long long p, long long q) {
    if (q < 0) { p = -p; q = -q; }
    long long g = gcd_ll(p, q);
    if (g) { p /= g; q /= g; }
    return (Frac){p, q};
}

/* parse exato: "p/q" | inteiro | decimal "0.5" (sem float, nunca) */
static int parse_exact(const char *s, Frac *out) {
    long long p, q;
    const char *sl = strchr(s, '/');
    if (sl && sscanf(s, "%lld/%lld", &p, &q) == 2 && q != 0) {
        *out = frac_norm(p, q); return 1;
    }
    const char *dot = strchr(s, '.');
    if (!dot) {
        if (sscanf(s, "%lld", &p) == 1) { *out = frac_norm(p, 1); return 1; }
        return 0;
    }
    /* decimal: -?[0-9]+ . [0-9]+  =>  num/10^k */
    int neg = (*s == '-');
    const char *a = s + (neg || *s == '+');
    long long ip = 0, fp = 0, k = 0;
    for (; isdigit((unsigned char)*a) && a < dot; a++) ip = ip*10 + (*a-'0');
    if (a != dot) return 0;
    for (a = dot + 1; isdigit((unsigned char)*a); a++) { fp = fp*10 + (*a-'0'); k++; }
    if (*a) return 0;
    long long den = 1; for (long long i = 0; i < k; i++) den *= 10;
    long long num = ip * den + fp;
    if (neg) num = -num;
    *out = frac_norm(num, den); return 1;
}

/* str(Fraction) canónico do Python: "p/q" | "-p/q" | "p" | "0" */
static void frac_str(Frac f, char *buf, size_t n) {
    if (f.q == 1 || f.p == 0) snprintf(buf, n, "%lld", f.p);
    else snprintf(buf, n, "%lld/%lld", f.p, f.q);
}

static int mul_ovf(i128 a, i128 b, i128 *r) {
    *r = a * b;
    return (*r > OVMAX || *r < -OVMAX);
}

/* ----------------------------------------------- vereditos (zverify) */
static int verdict_from_cmp(int c, const char *op) {
    return (strcmp(op,">")==0 && c>0) || (strcmp(op,"<")==0 && c<0) ||
           (strcmp(op,">=")==0 && c>=0) || (strcmp(op,"<=")==0 && c<=0) ||
           (strcmp(op,"==")==0 && c==0);
}

static int verdict_gauss(long long n, const char *op, long long thr) {
    return verdict_from_cmp(cmpv(LL(n)*(LL(n)+1), LL(2)*LL(thr)), op);
}

static int verdict_mean(long long n, const char *op, long long thr) {
    return verdict_from_cmp(cmpv(LL(n)+1, LL(2)*LL(thr)), op);
}

static long long ipow64(long long b, long long e, int *ovf) {
    __int128 r = 1; *ovf = 0;
    if (b == 0) return e == 0 ? 1 : 0;
    for (long long i = 0; i < e; i++) {
        r *= b;
        if (r > OVMAX || r < -OVMAX) { *ovf = 1; return 0; }
    }
    return (long long)r;
}

static int verdict_geofin(long long P, long long Q, long long n,
                         const char *op, long long thr, const char **reason) {
    if (Q <= 0) { *reason = "FRAC"; return -1; }
    if (P == Q) { *reason = "IDENTITY"; return -1; }   /* r = 1 (§12) */
    if (n < 0)  { *reason = "NNEG"; return -1; }
    if (n + 1 > 62) { *reason = "OVERFLOW"; return -1; }
    int ovf;
    long long x = ipow64(P, n + 1, &ovf); if (ovf) { *reason = "OVERFLOW"; return -1; }
    long long y = ipow64(Q, n + 1, &ovf); if (ovf) { *reason = "OVERFLOW"; return -1; }
    long long qn = ipow64(Q, n, &ovf);    if (ovf) { *reason = "OVERFLOW"; return -1; }
    i128 den = LL(qn) * LL(P - Q);
    if (den == 0) { *reason = "DIVZERO"; return -1; }
    i128 lhs = LL(Q) * (LL(x) - LL(y)) - LL(thr) * LL(y) * LL(P - Q);
    int c = den > 0 ? cmpv(lhs, 0) : -cmpv(lhs, 0);
    return verdict_from_cmp(c, op);
}

static int verdict_geo(long long A, long long B, long long P, long long Q,
                       const char *op, long long thr, const char **reason) {
    if (Q <= 0 || B <= 0) { *reason = "FRAC"; return -1; }
    if (P >= Q || P <= -Q) { *reason = "CONVERGENCE"; return -1; }
    int c = cmpv(LL(A)*LL(Q), LL(thr)*LL(B)*(LL(Q)-LL(P)));
    return verdict_from_cmp(c, op);
}

static int mul_ovf_i64(long long a, long long b, long long *r) {
    __int128 x = LL(a) * LL(b);
    if (x > OVMAX || x < -OVMAX) return 1;
    *r = (long long)x; return 0;
}

/* entanglement — Schmidt SEM raiz, SEM float (critério do núcleo):
 *   C = 2|det|/n >= 0;  C ~ t  <=>  2|det| ~ t*n
 *   amplitudes com denominador comum D:  a = A/D ...
 *   det = (A*E - B*C_)/D^2, n = (A^2+B^2+C_^2+E^2)/D^2
 *   C > t (t = p/q >= 0):  2*q*|A*E-B*C_| > p*(A^2+B^2+C_^2+E^2)
 *   muros: |p|,|q| das amplitudes <= 10^4 (D <= 10^16); |t.p|,|t.q| <= 10^3
 */
static int verdict_entangle(Frac amp[4], const char *target,
                           const char *op, Frac t, const char **reason) {
    /* muros §12 */
    for (int i = 0; i < 4; i++) {
        if (llabs(amp[i].p) > 10000LL || amp[i].q > 10000LL) {
            *reason = "OVERFLOW"; return -1;
        }
    }
    if (llabs(t.p) > 1000LL || t.q > 1000LL) { *reason = "OVERFLOW"; return -1; }
    /* denominador comum D = lcm */
    long long D = 1;
    for (int i = 0; i < 4; i++) {
        long long g = gcd_ll(D, amp[i].q);
        long long dl = D / g;
        if (mul_ovf_i64(dl, amp[i].q, &D)) { *reason = "OVERFLOW"; return -1; }
    }
    i128 A[4], S = 0, det = 0;
    for (int i = 0; i < 4; i++) {
        A[i] = LL(amp[i].p) * LL(D / amp[i].q);       /* <= 10^16 */
        i128 sq; if (mul_ovf(A[i], A[i], &sq)) { *reason = "OVERFLOW"; return -1; }
        S += sq;
        if (S > OVMAX) { *reason = "OVERFLOW"; return -1; }
    }
    det = A[0]*A[3] - A[1]*A[2];
    if (strcmp(target, "entangled") == 0) {
        long long v = det != 0 ? 1 : 0;               /* 0 ou 1 vs t */
        i128 lhs = LL(v) * LL(t.q), rhs = LL(t.p) * LL(1);
        return verdict_from_cmp(cmpv(lhs, rhs), op);
    }
    if (strcmp(target, "concurrence") != 0) { *reason = "TARGET"; return -1; }
    /* C = 2|det|/S >= 0 (comum D^2 cancela); |t| para <,<=,== */
    long long tp = t.p < 0 ? -t.p : t.p;
    i128 lhs, rhs, two_abs_det = LL(2) * (det < 0 ? -det : det);
    if (mul_ovf(two_abs_det, LL(t.q), &lhs)) { *reason = "OVERFLOW"; return -1; }
    if (mul_ovf(LL(tp), S, &rhs)) { *reason = "OVERFLOW"; return -1; }
    int c = cmpv(lhs, rhs);
    /* veredito BOOLEANO, não o sinal da comparação (a semântica do
     * núcleo: guardas de sinal para t negativo, senão 2|det| ~ |t|n) */
    if (strcmp(op, ">") == 0)  return t.p < 0 ? 1 : (c > 0);
    if (strcmp(op, ">=") == 0) return t.p <= 0 ? 1 : (c >= 0);
    if (strcmp(op, "<") == 0)  return t.p <= 0 ? 0 : (c < 0);
    if (strcmp(op, "<=") == 0) return t.p < 0 ? 0 : (c <= 0);
    if (strcmp(op, "==") == 0) return c == 0;
    *reason = "OP"; return -1;
}

/* entanglement 3 qubits — separabilidade plena, SEM raiz, SEM float:
 *   |psi> = S a_ijk |ijk>; achatar ao longo do qubit 0:
 *     R0 = (a000,a001,a010,a011), R1 = (a100,a101,a110,a111)
 *   posto 1  <=>  |psi> = u (x) phi(q1,q2)    (menores 2x2 todos nulos)
 *   phi produto <=>  phi0*phi3 - phi1*phi2 = 0
 *   TOTALMENTE SEPARAVEL <=> posto 1 E det2 = 0;
 *   entangled == !(totalmente separavel) — bisseparavel (Bell(x)|0>)
 *   responde honestamente 1: nao e produto de tres.
 *   muros §12: |p|,|q| <= 10^4 por amplitude; D comum <= 10^12
 */
static int verdict_entangle3(Frac amp[8], const char *target,
                            const char *op, Frac t, const char **reason) {
    if (strcmp(target, "entangled") != 0) {
        *reason = "TARGET3"; return -1;
    }
    if (llabs(t.p) > 1000LL || t.q > 1000LL) { *reason = "OVERFLOW"; return -1; }
    long long D = 1;
    for (int i = 0; i < 8; i++) {
        if (llabs(amp[i].p) > 10000LL || amp[i].q > 10000LL) {
            *reason = "OVERFLOW"; return -1;
        }
        long long g = gcd_ll(D, amp[i].q);
        long long dl = D / g;
        if (mul_ovf_i64(dl, amp[i].q, &D)) { *reason = "OVERFLOW"; return -1; }
        if (D > 1000000000000LL) { *reason = "OVERFLOW_D12"; return -1; }
    }
    i128 A[8];
    for (int i = 0; i < 8; i++)
        A[i] = LL(amp[i].p) * LL(D / amp[i].q);      /* |A| <= 10^16 */
    /* posto 1 do achatamento: 6 menores 2x2 */
    static const int pr[6][2] = {{0,1},{0,2},{0,3},{1,2},{1,3},{2,3}};
    int rank1 = 1;
    for (int k = 0; k < 6; k++) {
        int j = pr[k][0], m = pr[k][1];
        if (A[j]*A[4+m] != A[m]*A[4+j]) { rank1 = 0; break; }
    }
    int entangled = 1;
    if (rank1) {
        int nz0 = 0;
        for (int i = 0; i < 4; i++) if (A[i] != 0) nz0 = 1;
        if (nz0) entangled = (A[0]*A[3] - A[1]*A[2]) != 0;
        else     entangled = (A[4]*A[7] - A[5]*A[6]) != 0;
    }
    long long v = entangled ? 1 : 0;
    i128 lhs = LL(v) * LL(t.q), rhs = LL(t.p);
    return verdict_from_cmp(cmpv(lhs, rhs), op);
}

/* separabilidade plena recursiva — vetor escalado A[0..L), L = 2^m
 * (exato, i128; produtos <= 10^32 dentro do tipo)
 */
static int sepN(const i128 *A, int L, int *ovf) {
    if (L == 2) return 1;                     /* 1 qubit é sempre produto */
    int h = L / 2;
    for (int j = 0; j < h; j++) {
        for (int k = j + 1; k < h; k++) {
            i128 l1, l2;
            if (mul_ovf(A[j], A[h + k], &l1) ||
                mul_ovf(A[k], A[h + j], &l2)) { *ovf = 1; return -1; }
            if (l1 != l2) return 0;           /* posto > 1: emaranhado */
        }
    }
    int nz = 0;
    for (int j = 0; j < h; j++) if (A[j] != 0) { nz = 1; break; }
    return sepN(nz ? A : A + h, h, ovf);
}

/* entanglement N qubits (4 <= N <= 12, muro declarado):
 *   TOTALMENTE SEPARÁVEL <=> posto 1 do achatamento (q0) e o resíduo
 *   totalmente separável (recursão) — critério exato, sem float
 *   muros §12: |p|,|q| <= 10^4 por amplitude; D comum <= 10^12;
 *   na <= 4096 amplitudes
 */
static int verdict_entangleN(Frac *amp, int na, const char *target,
                            const char *op, Frac t, const char **reason) {
    if (strcmp(target, "entangled") != 0) { *reason = "TARGETN"; return -1; }
    if (llabs(t.p) > 1000LL || t.q > 1000LL) { *reason = "OVERFLOW"; return -1; }
    long long D = 1;
    for (int i = 0; i < na; i++) {
        if (llabs(amp[i].p) > 10000LL || amp[i].q > 10000LL) {
            *reason = "OVERFLOW"; return -1; }
        long long g = gcd_ll(D, amp[i].q);
        if (mul_ovf_i64(D / g, amp[i].q, &D)) { *reason = "OVERFLOW"; return -1; }
        if (D > 1000000000000LL) { *reason = "OVERFLOW_D12"; return -1; }
    }
    i128 *A = malloc((size_t)na * sizeof(i128));
    if (!A) { *reason = "MEM"; return -1; }
    for (int i = 0; i < na; i++)
        A[i] = LL(amp[i].p) * LL(D / amp[i].q);
    int ovf = 0, sep = sepN(A, na, &ovf);
    free(A);
    if (ovf) { *reason = "OVERFLOW"; return -1; }
    long long v = sep ? 0 : 1;                /* entangled = !separável */
    i128 lhs = LL(v) * LL(t.q), rhs = LL(t.p);
    return verdict_from_cmp(cmpv(lhs, rhs), op);
}

/* ---------------------------------------------------------- parser */
static char *read_file(const char *path, size_t *len) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    char *b = malloc((size_t)n + 1);
    fread(b, 1, (size_t)n, f); b[n] = 0; fclose(f);
    if (len) *len = (size_t)n;
    return b;
}

/* valor da chave "    key: value" dentro da fonte (primeira ocorrência) */
static int src_key(char *src, const char *key, char *out, size_t outn) {
    size_t kl = strlen(key);
    char *p = src;
    while ((p = strstr(p, key)) != NULL) {
        if ((p == src || p[-1] == ' ' || p[-1] == '\n') &&
            p[kl] == ':') {
            char *v = p + kl + 1;
            while (*v == ' ' || *v == '\t') v++;
            char *e = v;
            while (*e && *e != '\n' && *e != '\r') e++;
            while (e > v && (e[-1] == ' ' || e[-1] == '\t')) e--;
            size_t vl = (size_t)(e - v);
            if (vl >= outn) vl = outn - 1;
            memcpy(out, v, vl); out[vl] = 0;
            return 1;
        }
        p += kl;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "uso: zref <fonte.zeph>\n"); return 2; }
    char *src = read_file(argv[1], NULL);
    if (!src) { perror(argv[1]); return 2; }
    char qline[256], ftype[64], vn[64], va[128], vr[128], vstate[262144];
    if (!src_key(src, "question", qline, sizeof qline) ||
        !src_key(src, "type", ftype, sizeof ftype)) {
        fprintf(stderr, "RECUSA (§12): fonte sem ASK/MODEL parseável\n");
        return 2;
    }
    /* pergunta: <alvo> <op> <thr>  |  sum <op> <thr> (família implícita) */
    char target[64] = "", op[8] = "", thrs[128] = "";
    char t1[64] = "", t2[8] = "", t3[128] = "";
    int nf = sscanf(qline, "%63s %7s %127s", t1, t2, t3);
    if (nf != 3) {
        fprintf(stderr, "RECUSA (§12): pergunta malformada: '%s'\n", qline);
        return 2;
    }
    strcpy(target, t1); strcpy(op, t2); strcpy(thrs, t3);

    char data[512], hex[65];
    char *dhash = data;
    uint8_t dg[32];
    long long units;
    int v = -1;
    const char *reason = "";

    if (strcmp(ftype, "gauss_series") == 0) {
        if (!src_key(src, "n", vn, sizeof vn)) { fprintf(stderr,
            "RECUSA (§12): gauss exige n\n"); return 2; }
        long long n = atoll(vn);
        if (n < 1) { fprintf(stderr, "RECUSA (§12): n < 1\n"); return 2; }
        if (n > 1000000000000LL) { fprintf(stderr,
            "OVERFLOW (§12): n além do muro de 10^12\n"); return 3; }
        long long thr = atoll(thrs);
        v = verdict_gauss(n, op, thr);
        snprintf(data, sizeof data, "%lld", n);
        units = 2;
    } else if (strcmp(ftype, "arithmetic_mean") == 0) {
        if (!src_key(src, "n", vn, sizeof vn)) { fprintf(stderr,
            "RECUSA (§12): mean exige n\n"); return 2; }
        long long n = atoll(vn);
        if (n < 1) { fprintf(stderr, "RECUSA (§12): n < 1\n"); return 2; }
        if (n > 1000000000000LL) { fprintf(stderr,
            "OVERFLOW (§12): n além do muro de 10^12\n"); return 3; }
        long long thr = atoll(thrs);
        v = verdict_mean(n, op, thr);
        snprintf(data, sizeof data, "%lld", n);
        units = 1;
    } else if (strcmp(ftype, "geometric_inf") == 0) {
        if (!src_key(src, "a", va, sizeof va) ||
            !src_key(src, "r", vr, sizeof vr)) { fprintf(stderr,
            "RECUSA (§12): geo exige a e r\n"); return 2; }
        Frac a, r;
        if (!parse_exact(va, &a) || !parse_exact(vr, &r)) {
            fprintf(stderr, "RECUSA (§12): a/r não parseável exato\n");
            return 2;
        }
        if (r.p >= r.q || r.p <= -r.q) { fprintf(stderr,
            "RECUSA (§12): r=%lld/%lld não converge — recusa também em C\n",
            r.p, r.q); return 2; }
        long long thr = atoll(thrs);
        v = verdict_geo(a.p, a.q, r.p, r.q, op, thr, &reason);
        if (v < 0) { fprintf(stderr, "RECUSA (§12): %s\n", reason);
            return 2; }
        char sa[64], sr[64]; frac_str(a, sa, sizeof sa); frac_str(r, sr, sizeof sr);
        snprintf(data, sizeof data, "%s|%s", sa, sr);
        units = 2;
    } else if (strcmp(ftype, "geometric_fin") == 0) {
        if (!src_key(src, "r", vr, sizeof vr) ||
            !src_key(src, "n", vn, sizeof vn)) { fprintf(stderr,
            "RECUSA (§12): geofin exige r e n\n"); return 2; }
        Frac r;
        if (!parse_exact(vr, &r)  || *vn == 0 || !strchr(vn,0)) { fprintf(stderr,
            "RECUSA (§12): r/n não parseável exato\n"); return 2; }
        long long n = atoll(vn);
        long long thr = atoll(thrs);
        if (r.p == r.q) { fprintf(stderr,
            "RECUSA (§12): r = 1 é identidade, não série\n"); return 2; }
        v = verdict_geofin(r.p, r.q, n, op, thr, &reason);
        if (v < 0) {
            if (strcmp(reason, "OVERFLOW") == 0) { fprintf(stderr,
                "OVERFLOW (§12): r^(n+1) além de 64 bits — muro declarado\n");
                return 3;
            }
            fprintf(stderr, "RECUSA (§12): %s\n", reason); return 2;
        }
        char sr[64]; frac_str(r, sr, sizeof sr);
        snprintf(data, sizeof data, "%s|%lld", sr, n);
        units = 2;
    } else if (strcmp(ftype, "entanglement") == 0) {
        if (!src_key(src, "state", vstate, sizeof vstate)) { fprintf(stderr,
            "RECUSA (§12): entanglement exige state (2^N amplitudes, N = 2..12)\n");
            return 2;
        }
        int na = 0, cap = 16;
        Frac *amp = malloc((size_t)cap * sizeof(Frac));
        if (!amp) { fprintf(stderr,
            "RECUSA (§12): memória insuficiente\n"); return 2; }
        char *save = NULL;
        for (char *t = strtok_r(vstate, ",", &save); t;
             t = strtok_r(NULL, ",", &save)) {
            if (na == 4096) { fprintf(stderr,
                "RECUSA (§12): muro do núcleo — máximo 4096 amplitudes "
                "(12 qubits)\n"); free(amp); return 2; }
            if (na == cap) {
                cap *= 2;
                Frac *tmp = realloc(amp, (size_t)cap * sizeof(Frac));
                if (!tmp) { free(amp); fprintf(stderr,
                    "RECUSA (§12): memória insuficiente\n"); return 2; }
                amp = tmp;
            }
            while (*t == ' ') t++;
            if (!parse_exact(t, &amp[na])) { fprintf(stderr,
                "RECUSA (§12): amplitude '%s' não exata\n", t);
                free(amp); return 2; }
            na++;
        }
        if (!(na == 4 || na == 8 ||
              (na >= 16 && (na & (na - 1)) == 0))) {
            fprintf(stderr, "RECUSA (§12): estado com %d amplitudes — "
                "precisa 2^N (N = 2..12)\n", na);
            free(amp); return 2;
        }
        /* estado nulo: recusa estrutural (nunca veredito) */
        {
            i128 nn = 0;
            char s4[64][4];
            for (int i = 0; i < na; i++) {
                i128 sq; mul_ovf(LL(amp[i].p), LL(amp[i].p), &sq);
                nn += sq * 1;
                (void)s4;
            }
            int zero = 1;
            for (int i = 0; i < na; i++)
                if (amp[i].p != 0) zero = 0;
            if (zero) { fprintf(stderr,
                "RECUSA (§12): estado nulo não é estado quântico\n");
                return 2;
            }
            (void)nn;
        }
        Frac t;
        if (!parse_exact(thrs, &t)) { fprintf(stderr,
            "RECUSA (§12): threshold não exato\n"); return 2; }
        v = (na == 4) ? verdict_entangle(amp, target, op, t, &reason)
            : (na == 8) ? verdict_entangle3(amp, target, op, t, &reason)
            : verdict_entangleN(amp, na, target, op, t, &reason);
        if (v < 0) {
            if (strcmp(reason, "OVERFLOW_D12") == 0) { fprintf(stderr,
                "OVERFLOW (§12): denominador comum > 10^12 no estado de "
                "3 qubits — precisão arbitrária é da referência Python, "
                "muro é declarado aqui\n"); return 3; }
            if (strcmp(reason, "TARGET3") == 0) { fprintf(stderr,
                "RECUSA (§12): concurrence é medida de 2 qubits — "
                "3 qubits respondem apenas 'entangled'\n"); return 2; }
            if (strcmp(reason, "TARGETN") == 0) { fprintf(stderr,
                "RECUSA (§12): concurrence é medida de 2 qubits — "
                "N qubits respondem apenas 'entangled'\n"); return 2; }
            if (strcmp(reason, "MEM") == 0) { fprintf(stderr,
                "RECUSA (§12): memória insuficiente\n"); return 2; }
            if (strcmp(reason, "OVERFLOW") == 0) { fprintf(stderr,
                "OVERFLOW (§12): amplitudes/threshold além do muro "
                "(10^4/10^3) — precisão arbitrária é da referência "
                "Python, muro é declarado aqui\n"); return 3;
            }
            fprintf(stderr, "RECUSA (§12): %s\n", reason); return 2;
        }
        if (na == 8) {
            char sf8[8][64];
            for (int i = 0; i < 8; i++) frac_str(amp[i], sf8[i], sizeof sf8[i]);
            snprintf(data, sizeof data, "%s|%s|%s|%s|%s|%s|%s|%s",
                     sf8[0], sf8[1], sf8[2], sf8[3],
                     sf8[4], sf8[5], sf8[6], sf8[7]);
        } else if (na == 4) {
            char sf[4][64];
            for (int i = 0; i < 4; i++) frac_str(amp[i], sf[i], sizeof sf[i]);
            snprintf(data, sizeof data, "%s|%s|%s|%s", sf[0], sf[1], sf[2], sf[3]);
        } else {
            char tmp[64];
            size_t need = 2;
            for (int i = 0; i < na; i++) {
                frac_str(amp[i], tmp, sizeof tmp);
                need += strlen(tmp) + 1;
            }
            dhash = malloc(need);
            if (!dhash) { free(amp); fprintf(stderr,
                "RECUSA (§12): memória insuficiente\n"); return 2; }
            char *w = dhash;
            for (int i = 0; i < na; i++) {
                frac_str(amp[i], tmp, sizeof tmp);
                size_t l = strlen(tmp);
                if (i) *w++ = '|';
                memcpy(w, tmp, l); w += l;
            }
            *w = 0;
        }
        units = 0;
        free(amp);
    } else {
        fprintf(stderr, "RECUSA (§12): família '%s' fora do motor C nesta "
                "fatia\n", ftype);
        return 2;
    }

    sha256(dhash, dg); hex32(dg, hex);
    if (dhash != data) free(dhash);
    printf("VERDICT %d\n", v);
    printf("HASH %s\n", hex);
    printf("UNITS %lld\n", units);
    if (strcmp(ftype, "entanglement") == 0)
        printf("QPU_UNITS_BILLED 0\n");
    printf("ENGINE zref-c11 (exato, §12 muros declarados)\n");
    return 0;
}
