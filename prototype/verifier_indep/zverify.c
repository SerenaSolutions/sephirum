/*
 * ZVERIFY — verificador independente do ZEPHIRUM v0.3, em C puro (C11).
 * =====================================================================
 *
 * Implementação INDEPENDENTE da referência Python: re-deriva os vereditos
 * dos degraus de eliminação com aritmética exata própria (__int128),
 * recalcula o INPUT_HASH com SHA-256 (FIPS 180-4) implementado aqui, e
 * audita os custos NORMATIVOS da tabela §5 do padrão.
 *
 * Este ficheiro NÃO inclui nem depende de nenhum código do repositório
 * Python: é a prova de que o padrão atravessa linguagens, compiladores
 * e máquinas ("além do espaço").
 *
 * Formato do caso (TAB-separado, um por linha):
 *   family  op  thr  p1  p2  lane  expected  input_hash  units  budget  data_string
 *
 *   family : gauss | geo | mean
 *   op     : > < >= <= ==
 *   p1/p2  : parâmetros (gauss/mean: p1 = n; geo: p1 = a=p/q, p2 = r=p/q)
 *   lane   : b (boot) | n (naive)
 *   expected: veredito declarado (1/0)
 *   input_hash: SHA-256 hex do data_string (64 hex)
 *   units/budget: contabilidade do certificado
 *   data_string : string canónica cuja hash deve bater
 *
 * Falha declarada (§12 em C): cobertura de 64 bits/128 bits — racionais
 * fora de ±9,2e18 (p.e. os 10^30 da bateria Python) ficam fora do escopo
 * deste verificador; a referência Python mantém precisão arbitrária.
 *
 * Saída: uma linha por caso ("PASS"/"FAIL <motivo>") + resumo.
 * Exit 0 iff todos os casos passam.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>
#include <strings.h>

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

static int cmpv(i128 l, i128 r) { return l < r ? -1 : (l > r ? 1 : 0); }

static int parse_frac(const char *s, long long *num, long long *den) {
    if (sscanf(s, "%lld/%lld", num, den) == 2) return *den != 0;
    if (sscanf(s, "%lld", num) == 1) { *den = 1; return 1; }
    return 0;
}

/* veredicto INDEPENDENTE: comparação exacta por produtos cruzados */
static int verdict_gauss(long long n, const char *op, long long thr) {
    int c = cmpv(LL(n)*(LL(n)+1), LL(2)*LL(thr));   /* n(n+1)/2 vs thr */
    return (strcmp(op,">")==0 && c>0) || (strcmp(op,"<")==0 && c<0) ||
           (strcmp(op,">=")==0 && c>=0) || (strcmp(op,"<=")==0 && c<=0) ||
           (strcmp(op,"==")==0 && c==0);
}

static int verdict_mean(long long n, const char *op, long long thr) {
    int c = cmpv(LL(n)+1, LL(2)*LL(thr));           /* (n+1)/2 vs thr */
    return (strcmp(op,">")==0 && c>0) || (strcmp(op,"<")==0 && c<0) ||
           (strcmp(op,">=")==0 && c>=0) || (strcmp(op,"<=")==0 && c<=0) ||
           (strcmp(op,"==")==0 && c==0);
}

/* geo: a=A/B, r=P/Q, |r|<1 exigido; S = A*Q / (B*(Q-P)) vs thr */
static int verdict_geo(long long A, long long B, long long P, long long Q,
                       const char *op, long long thr, const char **reason) {
    if (Q <= 0 || B <= 0) { *reason = "FRAC"; return -1; }
    if (P >= Q || P <= -Q) { *reason = "CONVERGENCE"; return -1; }
    /* B>0 e (Q-P)>0: sinal de S = sinal de A*Q; comparação por cruzamento */
    int c = cmpv(LL(A)*LL(Q), LL(thr)*LL(B)*(LL(Q)-LL(P)));
    return (strcmp(op,">")==0 && c>0) || (strcmp(op,"<")==0 && c<0) ||
           (strcmp(op,">=")==0 && c>=0) || (strcmp(op,"<=")==0 && c<=0) ||
           (strcmp(op,"==")==0 && c==0);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "uso: zverify <casos.tsv>\n"); return 2; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror(argv[1]); return 2; }
    char line[8192];
    int ncase = 0, nfail = 0;
    while (fgets(line, sizeof line, f)) {
        line[strcspn(line, "\r\n")] = 0;     /* o \n não entra na hash */
        if (line[0] == '#' || line[0] == '\0') continue;
        ncase++;
        char *fld[11], *tok = line, **pp = fld;
        int nf = 0;
        while (nf < 11) {
            *pp++ = tok; nf++;
            char *tab = strchr(tok, '\t');
            if (!tab) break;
            *tab = 0; tok = tab + 1;
        }
        if (nf < 11) { printf("FAIL %d PARSE\n", ncase); nfail++; continue; }
        char *rest;
        long long thr = strtoll(fld[2], &rest, 10);
        int expected = atoi(fld[6]);
        long long units = strtoll(fld[8], &rest, 10);
        long long budget = strtoll(fld[9], &rest, 10);
        /* 1) INPUT_HASH recalculado de raiz */
        uint8_t d[32]; char hex[65];
        sha256(fld[10], d); hex32(d, hex);
        /* 2) veredito re-derivado */
        int v;
        const char *family = fld[0], *op = fld[1], *reason = NULL;
        if (strcmp(family, "gauss") == 0) {
            long long n = strtoll(fld[3], &rest, 10);
            v = verdict_gauss(n, op, thr);
        } else if (strcmp(family, "mean") == 0) {
            long long n = strtoll(fld[3], &rest, 10);
            v = verdict_mean(n, op, thr);
        } else if (strcmp(family, "geo") == 0) {
            long long A, B, P, Q;
            if (!parse_frac(fld[3], &A, &B) || !parse_frac(fld[4], &P, &Q)) {
                printf("FAIL %d FRAC\n", ncase); nfail++; continue;
            }
            v = verdict_geo(A, B, P, Q, op, thr, &reason);
            if (v < 0) { printf("FAIL %d %s\n", ncase, reason); nfail++; continue; }
        } else { printf("FAIL %d FAMILY\n", ncase); nfail++; continue; }
        /* 3) as três auditorias do certificado */
        char why[64];
        if (v != expected) {
            snprintf(why, sizeof why, "VERDICT (esperado %d, derivado %d)",
                     expected, v);
            printf("FAIL %d %s\n", ncase, why); nfail++; continue;
        }
        if (strcasecmp(hex, fld[7]) != 0) {
            printf("FAIL %d HASH (recalculado %s != %s)\n", ncase, hex, fld[7]);
            nfail++; continue;
        }
        if (units > budget) {
            printf("FAIL %d BUDGET (%lld > %lld)\n", ncase, units, budget);
            nfail++; continue;
        }
        /* 4) custo NORMATIVO (tabela §5) para a lane boot */
        if (fld[5][0] == 'b') {
            long long cost = (strcmp(family, "mean") == 0) ? 1 : 2;
            if (units != cost) {
                printf("FAIL %d COST (boot %s: %lld != %lld unidades "
                       "normativas)\n", ncase, family, units, cost);
                nfail++; continue;
            }
        }
        printf("PASS %d %s\n", ncase, family);
    }
    fclose(f);
    printf("RESUMO: %d/%d PASS\n", ncase - nfail, ncase);
    return nfail ? 1 : 0;
}
