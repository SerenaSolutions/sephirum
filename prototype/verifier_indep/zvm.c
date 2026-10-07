/*
 * ZVM — a máquina virtual ORÇADA do ZEPHIRUM em C puro (C11).
 * =============================================================
 *
 * O segundo motor em C puro (depois do zref, que DECIDE): este EXECUTA
 * o bytecode da VM orçada com a MESMA semântica da referência Python
 * (zephirum_vm.py): unidades certificadas, muros §12 idênticos e traço
 * determinístico — mesmo ANSWER, mesmas UNITS, mesmo TRACE_HASH.
 *
 * Formato do ficheiro .zvm (texto, gerado pela bateria/serializador):
 *   DATA <n>            ; n linhas: valores exatos ("5", "3/2", "-7")
 *   BUDGET <k>
 *   PROG <m>            ; m linhas: opcode + operandos
 *     PUSH v | LOAD i | LOADSEQ | ADD | MUL | DIV | DUP | SWAP |
 *     POW | CMP op t | CMPT op t | LABEL L | JMPZ L | CALL L | RET |
 *     LOOP n | ENDLOOP | MEDIAN k | HALT
 *
 * Saída (stdout):  ANSWER 0|1|none / UNITS n / TRACE_HASH hex
 * Falta (§12): stderr "FALTA <motivo>" e exit 2 — nunca silêncio,
 * nunca mentira.
 *
 * Muros declarados (§12) — idênticos ao Python:
 *   STEP_LIMIT 65536 · CALL_DEPTH 64 · POW_EXPONENT 65536 · STACK 1024
 *   + muro C próprio: frações |num|,|den| <= 10^12 reduzidas — além,
 *   OVERFLOW declarado (a precisão arbitrária vive na referência).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

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

/* --------------------------------------------------- fração exata */
typedef __int128 i128;
#define LL(x) ((__int128)(x))
#define OVMAX LL(9223372036854775807LL)
#define WALL 1000000000000LL     /* |num|,|den| <= 10^12 (§12 em C) */

typedef struct { long long p, q; } Frac;   /* q > 0, reduzida */

static long long gcd_ll(long long a, long long b) {
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    while (b) { long long t = a % b; a = b; b = t; }
    return a;
}

static int frac_ok(long long p, long long q, Frac *out) {
    if (q == 0) return 0;
    if (q < 0) { p = -p; q = -q; }
    long long g = gcd_ll(p, q);
    if (g) { p /= g; q /= g; }
    if (llabs(p) > WALL || q > WALL) return 0;   /* muro C §12 */
    *out = (Frac){p, q};
    return 1;
}

/* parse exato: "p/q" | inteiro | decimal */
static int parse_exact(const char *s, Frac *out) {
    long long p, q;
    const char *sl = strchr(s, '/');
    if (sl && sscanf(s, "%lld/%lld", &p, &q) == 2 && q != 0)
        return frac_ok(p, q, out);
    const char *dot = strchr(s, '.');
    if (!dot) {
        if (sscanf(s, "%lld", &p) == 1) return frac_ok(p, 1, out);
        return 0;
    }
    int neg = (*s == '-');
    const char *a = s + (neg || *s == '+');
    long long ip = 0, fp = 0, k = 0;
    for (; *a >= '0' && *a <= '9' && a < dot; a++) ip = ip*10 + (*a-'0');
    if (a != dot) return 0;
    for (a = dot + 1; *a >= '0' && *a <= '9'; a++) { fp = fp*10 + (*a-'0'); k++; }
    if (*a) return 0;
    long long den = 1; for (long long i = 0; i < k; i++) den *= 10;
    long long num = ip * den + fp;
    if (neg) num = -num;
    return frac_ok(num, den, out);
}

/* aritmética: reduz em espaço __int128 ANTES do muro — produtos
 * cruzados chegam a 10^24; o cast só acontece pós-redução, com
 * |num|,|den| <= 10^12 garantindo cast seguro em long long */
static i128 iabs128(i128 x) { return x < 0 ? -x : x; }
static i128 gcd128(i128 a, i128 b) {
    if (a < 0) a = -a;
    while (b) { i128 t = a % b; a = b; b = t; }
    return a;
}
static int frac_ok128(i128 p, i128 q, Frac *out) {
    if (q == 0) return 0;
    if (q < 0) { p = -p; q = -q; }
    i128 g = gcd128(p, q);
    if (g) { p /= g; q /= g; }
    if (iabs128(p) > LL(WALL) || q > LL(WALL)) return 0;  /* muro §12 */
    *out = (Frac){(long long)p, (long long)q};
    return 1;
}
static int f_add(Frac a, Frac b, Frac *r) {
    return frac_ok128(LL(a.p)*LL(b.q) + LL(b.p)*LL(a.q),
                      LL(a.q)*LL(b.q), r) ? 0 : -1;
}
static int f_mul(Frac a, Frac b, Frac *r) {
    return frac_ok128(LL(a.p)*LL(b.p), LL(a.q)*LL(b.q), r) ? 0 : -1;
}
static int f_div(Frac a, Frac b, Frac *r) {
    if (b.p == 0) return -2;                    /* DIV por zero */
    return frac_ok128(LL(a.p)*LL(b.q), LL(a.q)*LL(b.p), r) ? 0 : -1;
}
static int f_cmp(Frac a, Frac b) {
    i128 l = LL(a.p)*LL(b.q), r = LL(b.p)*LL(a.q);
    return l < r ? -1 : (l > r ? 1 : 0);
}

/* ------------------------------------------------------------ VM */
#define STEP_LIMIT 65536
#define CALL_DEPTH 64
#define POW_LIMIT  65536
#define STACK_MAX  1024
#define MAXPROG   4096

typedef struct { char op[16]; char a1[128]; char a2[128]; int na; } Ins;

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "uso: zvm <programa.zvm>\n"); return 2; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror(argv[1]); return 2; }

    char line[512];
    long long ndata = 0, budget = 0, nprog = 0;
    Frac data[1024];
    Ins prog[MAXPROG];
    int pc = 0, have_data = 0, have_prog = 0;

    while (fgets(line, sizeof line, f)) {
        line[strcspn(line, "\r\n")] = 0;
        if (line[0] == 0 || line[0] == ';') continue;
        if (strncmp(line, "DATA ", 5) == 0) {
            ndata = atoll(line + 5); have_data = 1;
            for (long long i = 0; i < ndata; i++) {
                if (!fgets(line, sizeof line, f)) return 2;
                line[strcspn(line, "\r\n")] = 0;
                if (!parse_exact(line, &data[i])) {
                    fprintf(stderr, "FALTA dado '%s' fora do muro §12\n",
                            line);
                    return 2;
                }
            }
        } else if (strncmp(line, "BUDGET ", 7) == 0) {
            budget = atoll(line + 7);
        } else if (strncmp(line, "PROG ", 5) == 0) {
            nprog = atoll(line + 5); have_prog = 1;
            for (long long i = 0; i < nprog; i++) {
                if (!fgets(line, sizeof line, f)) return 2;
                line[strcspn(line, "\r\n")] = 0;
                Ins *in = &prog[pc++];
                char *sp = strchr(line, ' ');
                if (sp) { *sp = 0; strncpy(in->a1, sp + 1, 127);
                          in->na = 1;
                          char *sp2 = strchr(in->a1, ' ');
                          if (sp2) { *sp2 = 0;
                                     strncpy(in->a2, sp2 + 1, 127);
                                     in->na = 2; }
                } else { in->a1[0] = 0; in->a2[0] = 0; in->na = 0; }
                strncpy(in->op, line, 15);
            }
        }
    }
    fclose(f);
    if (!have_data || !have_prog || pc == 0) {
        fprintf(stderr, "FALTA ficheiro .zvm incompleto\n"); return 2;
    }

    /* pré-varredura: LABEL -> pc (duplicado = falta) */
    int labels_n = 0;
    char lname[MAXPROG][64]; int lpc[MAXPROG];
    for (int i = 0; i < pc; i++) {
        if (strcmp(prog[i].op, "LABEL") == 0) {
            for (int j = 0; j < labels_n; j++)
                if (strcmp(lname[j], prog[i].a1) == 0) {
                    fprintf(stderr, "FALTA label duplicado %s\n",
                            prog[i].a1);
                    return 2;
                }
            strncpy(lname[labels_n], prog[i].a1, 63);
            lpc[labels_n++] = i;
        }
    }

    Frac stack[STACK_MAX + 8];
    int sp = 0;
    long long units = 0, seq = 0, steps = 0;
    int loop_rem[MAXPROG], loop_body[MAXPROG], loop_n = 0;
    int call_stack[CALL_DEPTH + 8], call_n = 0;
    int answer = -1;                        /* -1 = none */
    int ip = 0;
    /* traço: concatenação "op|op:arg|..." como no Python */
    size_t tlen = 0, tcap = 1 << 20;
    char *trace = malloc(tcap);
    trace[0] = 0;

    while (ip < pc) {
        Ins *in = &prog[ip];
        steps++;
        if (steps > STEP_LIMIT) {
            fprintf(stderr, "FALTA STEP LIMIT: %d passos — laço "
                    "forjado sem consumo de dado não escapa do muro "
                    "(§12)\n", STEP_LIMIT);
            return 2;
        }
        if (strcmp(in->op, "LOADSEQ") != 0) {
            char entry[160];
            if (in->na == 0) snprintf(entry, sizeof entry, "%s", in->op);
            else snprintf(entry, sizeof entry, "%s:%s", in->op, in->a1);
            size_t el = strlen(entry);
            if (tlen + el + 2 > tcap) {
                tcap *= 2; trace = realloc(trace, tcap);
            }
            if (tlen) trace[tlen++] = '|';
            memcpy(trace + tlen, entry, el); tlen += el; trace[tlen] = 0;
        }

        if (strcmp(in->op, "PUSH") == 0) {
            Frac v;
            if (!parse_exact(in->a1, &v)) {
                fprintf(stderr, "FALTA PUSH '%s' fora do muro §12\n",
                        in->a1);
                return 2;
            }
            stack[sp++] = v;
        } else if (strcmp(in->op, "LOADSEQ") == 0) {
            if (seq >= ndata) {
                fprintf(stderr, "FALTA LOADSEQ fora dos dados (pc=%d)\n",
                        ip);
                return 2;
            }
            if (units >= budget) {
                fprintf(stderr, "FALTA BUDGET EXCEEDED: %lld/%lld "
                        "unidades — o certificado não autoriza mais "
                        "execução\n", units, budget);
                return 2;
            }
            stack[sp++] = data[seq];
            char entry[64];
            snprintf(entry, sizeof entry, "LOADSEQ:%lld", seq);
            size_t el = strlen(entry);
            if (tlen + el + 2 > tcap) { tcap *= 2; trace = realloc(trace, tcap); }
            if (tlen) trace[tlen++] = '|';
            memcpy(trace + tlen, entry, el); tlen += el; trace[tlen] = 0;
            seq++; units++;
            ip++; continue;
        } else if (strcmp(in->op, "LOAD") == 0) {
            long long i = atoll(in->a1);
            if (i < 0 || i >= ndata) {
                fprintf(stderr, "FALTA LOAD fora dos dados (pc=%d)\n", ip);
                return 2;
            }
            if (units >= budget) {
                fprintf(stderr, "FALTA BUDGET EXCEEDED: %lld/%lld "
                        "unidades — o certificado não autoriza mais "
                        "execução\n", units, budget);
                return 2;
            }
            stack[sp++] = data[i];
            units++;
        } else if (strcmp(in->op, "CMP") == 0) {
            if (sp < 1) { fprintf(stderr, "FALTA stack vazio (pc=%d)\n",
                          ip); return 2; }
            Frac v = stack[--sp], t;
            if (!parse_exact(in->a2, &t)) {
                fprintf(stderr, "FALTA CMP t fora do muro §12\n");
                return 2;
            }
            int c = f_cmp(v, t);
            int r = (in->a1[0] == '>' && c > 0) || (in->a1[0] == '<' &&
                    in->a1[1] == 0 && c < 0) ||
                    (strcmp(in->a1, ">=") == 0 && c >= 0) ||
                    (strcmp(in->a1, "<=") == 0 && c <= 0) ||
                    (strcmp(in->a1, "==") == 0 && c == 0);
            stack[sp++] = (Frac){r, 1};
        } else if (strcmp(in->op, "CMPT") == 0) {
            if (sp < 1) { fprintf(stderr, "FALTA stack vazio (pc=%d)\n",
                          ip); return 2; }
            Frac v = stack[--sp], t;
            if (!parse_exact(in->a2, &t)) {
                fprintf(stderr, "FALTA CMPT t fora do muro §12\n");
                return 2;
            }
            int c = f_cmp(v, t);
            answer = (in->a1[0] == '>' && c > 0) || (in->a1[0] == '<' &&
                     in->a1[1] == 0 && c < 0) ||
                     (strcmp(in->a1, ">=") == 0 && c >= 0) ||
                     (strcmp(in->a1, "<=") == 0 && c <= 0) ||
                     (strcmp(in->a1, "==") == 0 && c == 0);
        } else if (strcmp(in->op, "LABEL") == 0) {
            /* marcador: custo 0 */
        } else if (strcmp(in->op, "JMPZ") == 0) {
            int target = -1;
            for (int j = 0; j < labels_n; j++)
                if (strcmp(lname[j], in->a1) == 0) target = lpc[j];
            if (target < 0) {
                fprintf(stderr, "FALTA JMPZ para label inexistente %s\n",
                        in->a1);
                return 2;
            }
            if (target <= ip) {
                fprintf(stderr, "FALTA JMPZ para TRÁS (pc=%d -> %d): "
                        "retroceder exige LOOP (§soundness)\n", ip,
                        target);
                return 2;
            }
            if (sp < 1) { fprintf(stderr, "FALTA stack vazio (pc=%d)\n",
                          ip); return 2; }
            Frac v = stack[--sp];
            if (v.p == 0) { ip = target; continue; }
        } else if (strcmp(in->op, "CALL") == 0) {
            int target = -1;
            for (int j = 0; j < labels_n; j++)
                if (strcmp(lname[j], in->a1) == 0) target = lpc[j];
            if (target < 0) {
                fprintf(stderr, "FALTA CALL para label inexistente %s\n",
                        in->a1);
                return 2;
            }
            if (target <= ip) {
                fprintf(stderr, "FALTA CALL para TRÁS (pc=%d -> %d): "
                        "sub-rotina fica À FRENTE (§soundness)\n", ip,
                        target);
                return 2;
            }
            if (call_n >= CALL_DEPTH) {
                fprintf(stderr, "FALTA CALL DEPTH: %d níveis — recursão "
                        "infinita bate no muro (§12)\n", CALL_DEPTH);
                return 2;
            }
            call_stack[call_n++] = ip + 1;
            ip = target; continue;
        } else if (strcmp(in->op, "RET") == 0) {
            if (call_n == 0) {
                fprintf(stderr, "FALTA RET sem CALL (pc=%d)\n", ip);
                return 2;
            }
            ip = call_stack[--call_n]; continue;
        } else if (strcmp(in->op, "LOOP") == 0) {
            if (loop_n >= MAXPROG) return 2;
            loop_rem[loop_n] = atoi(in->a1);
            loop_body[loop_n] = ip + 1;
            loop_n++;
        } else if (strcmp(in->op, "ENDLOOP") == 0) {
            if (loop_n == 0) {
                fprintf(stderr, "FALTA ENDLOOP sem LOOP (pc=%d)\n", ip);
                return 2;
            }
            loop_rem[loop_n - 1]--;
            if (loop_rem[loop_n - 1] > 0) { ip = loop_body[loop_n - 1];
                                             continue; }
            loop_n--;
        } else if (strcmp(in->op, "MEDIAN") == 0) {
            int k = atoi(in->a1);
            if (k < 1 || sp < k) {
                fprintf(stderr, "FALTA MEDIAN k=%d inválido para "
                        "stack=%d (pc=%d)\n", k, sp, ip);
                return 2;
            }
            Frac vals[1024];
            for (int j = 0; j < k; j++) vals[j] = stack[--sp];
            for (int j = 1; j < k; j++) {       /* insertion sort exato */
                Frac key = vals[j];
                int i2 = j - 1;
                while (i2 >= 0 && f_cmp(vals[i2], key) > 0) {
                    vals[i2 + 1] = vals[i2]; i2--;
                }
                vals[i2 + 1] = key;
            }
            Frac m;
            if (k % 2) {
                m = vals[k / 2];
            } else {
                Frac s;
                if (f_add(vals[k/2 - 1], vals[k/2], &s)) {
                    fprintf(stderr, "FALTA OVERFLOW (§12): mediana fora "
                            "do muro de 10^12\n");
                    return 2;
                }
                if (f_div(s, (Frac){2, 1}, &m)) {
                    fprintf(stderr, "FALTA OVERFLOW (§12): mediana fora "
                            "do muro de 10^12\n");
                    return 2;
                }
            }
            stack[sp++] = m;
        } else if (strcmp(in->op, "ADD") == 0) {
            if (sp < 2) { fprintf(stderr, "FALTA stack insuficiente "
                          "(pc=%d)\n", ip); return 2; }
            Frac b = stack[--sp], a = stack[--sp], r;
            if (f_add(a, b, &r)) {
                fprintf(stderr, "FALTA OVERFLOW (§12): fração além do "
                        "muro de 10^12 — precisão arbitrária é da "
                        "referência\n");
                return 2;
            }
            stack[sp++] = r;
        } else if (strcmp(in->op, "MUL") == 0) {
            if (sp < 2) { fprintf(stderr, "FALTA stack insuficiente "
                          "(pc=%d)\n", ip); return 2; }
            Frac b = stack[--sp], a = stack[--sp], r;
            if (f_mul(a, b, &r)) {
                fprintf(stderr, "FALTA OVERFLOW (§12): fração além do "
                        "muro de 10^12 — precisão arbitrária é da "
                        "referência\n");
                return 2;
            }
            stack[sp++] = r;
        } else if (strcmp(in->op, "DIV") == 0) {
            if (sp < 2) { fprintf(stderr, "FALTA stack insuficiente "
                          "(pc=%d)\n", ip); return 2; }
            Frac b = stack[--sp], a = stack[--sp], r;
            int rc = f_div(a, b, &r);
            if (rc == -2) {
                fprintf(stderr, "FALTA DIV por zero (pc=%d): sem "
                        "infinito na máquina — recusa explícita (§12)\n",
                        ip);
                return 2;
            }
            if (rc == -1) {
                fprintf(stderr, "FALTA OVERFLOW (§12): fração além do "
                        "muro de 10^12\n");
                return 2;
            }
            stack[sp++] = r;
        } else if (strcmp(in->op, "DUP") == 0) {
            if (sp < 1) { fprintf(stderr, "FALTA DUP com stack vazio "
                          "(pc=%d)\n", ip); return 2; }
            stack[sp] = stack[sp - 1]; sp++;
        } else if (strcmp(in->op, "SWAP") == 0) {
            if (sp < 2) { fprintf(stderr, "FALTA SWAP com menos de 2 "
                          "valores (pc=%d)\n", ip); return 2; }
            Frac t = stack[sp-1]; stack[sp-1] = stack[sp-2];
            stack[sp-2] = t;
        } else if (strcmp(in->op, "POW") == 0) {
            if (sp < 2) { fprintf(stderr, "FALTA stack insuficiente "
                          "(pc=%d)\n", ip); return 2; }
            Frac e = stack[--sp], b = stack[--sp], r;
            if (e.q != 1 || e.p < 0) {
                fprintf(stderr, "FALTA POW: expoente fora do domínio — "
                        "recusa explícita (§12)\n");
                return 2;
            }
            if (e.p > POW_LIMIT) {
                fprintf(stderr, "FALTA POW EXPONENT LIMIT: %lld > %d — "
                        "aritmética gratuita tem parede declarada (§12)\n",
                        e.p, POW_LIMIT);
                return 2;
            }
            i128 n = 1, d = 1;
            for (long long i2 = 0; i2 < e.p; i2++) {
                n *= b.p; d *= b.q;
                if (iabs128(n) > LL(WALL) || d > LL(WALL)) {
                    fprintf(stderr, "FALTA OVERFLOW (§12): b^e além do "
                            "muro de 10^12 — precisão arbitrária é da "
                            "referência\n");
                    return 2;
                }
            }
            if (!frac_ok128(n, d, &r)) {
                fprintf(stderr, "FALTA OVERFLOW (§12): b^e além do "
                        "muro de 10^12\n");
                return 2;
            }
            stack[sp++] = r;
        } else if (strcmp(in->op, "HALT") == 0) {
            break;
        } else {
            fprintf(stderr, "FALTA opcode desconhecido %s (pc=%d)\n",
                    in->op, ip);
            return 2;
        }
        if (sp > STACK_MAX) {
            fprintf(stderr, "FALTA stack overflow (pc=%d)\n", ip);
            return 2;
        }
        ip++;
    }

    if (getenv("ZVM_DEBUG")) fprintf(stderr, "TRACEC %s\n", trace);
    uint8_t dg[32]; char hex[65];
    sha256(trace, dg); hex32(dg, hex);
    if (answer < 0) printf("ANSWER none\n");
    else printf("ANSWER %d\n", answer);
    printf("UNITS %lld\n", units);
    printf("TRACE_HASH %s\n", hex);
    printf("ENGINE zvm-c11 (orçada, §12 muros declarados)\n");
    return 0;
}
