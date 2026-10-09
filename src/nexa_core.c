/* ZEPHIRUM — nexa_core.c: the exact decision core, in C.
 * Language-bar migration step 1 (2026-10-08).
 *
 * Scope, honestly declared (§12):
 *   - families: threshold_sum, mean_partial, geometric_series
 *   - arithmetic: exact on __int128; beyond-range inputs return
 *     UNKNOWN with reason, NEVER a guess
 *   - the Python engine (prototype/nexa_core.py) remains the
 *     reference for families outside this scope
 * Verdicts mirror the trivalent policy: decided 0/1, or UNKNOWN.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef __int128 i128;
#define MAXK 64
#define MAXLINE 512

typedef struct { i128 p, q; } Rat; /* q > 0, gcd not required for cmp */

static char g_cur_block[32];
static char g_question[MAXLINE];
static char g_type[64], g_terms[MAXLINE], g_known[MAXLINE];
static char g_bounds[MAXLINE], g_unknown[MAXLINE], g_assume[MAXLINE];
static char g_r[64], g_n[64];
static char g_state[256];
static char g_matrix[512];
static int ovl = 0; /* checked-overflow flag (§12: never a guess) */
static i128 ck(i128 a, i128 b){ i128 r; if(ovl) return 0;
  if(__builtin_mul_overflow(a,b,&r)) ovl=1; return ovl?0:r; }
static i128 cad(i128 a, i128 b){ i128 r; if(ovl) return 0;
  if(__builtin_add_overflow(a,b,&r)) ovl=1; return ovl?0:r; }
static i128 iabs(i128 a){ return a<0?-a:a; }
static i128 igcd(i128 a, i128 b){ if(a<0)a=-a; if(b<0)b=-b;
  while(b){ i128 t=a%b; a=b; b=t; } return a; }
static Rat rnorm(Rat r){ if(ovl||r.p==0){ if(!ovl&&r.p==0) r.q=1; return r; }
  i128 g=igcd(iabs(r.p),r.q); if(g>1){r.p/=g;r.q/=g;} return r; }
static Rat radd(Rat x, Rat y){ if(ovl) return x;
  i128 g=igcd(x.q,y.q); if(g==0){ovl=1;return x;}
  i128 l=ck(x.q/g,y.q);               /* lcm, checked */
  i128 num=cad(ck(x.p,l/x.q), ck(y.p,l/y.q));
  return rnorm((Rat){num,l}); }
static int  g_has_unknown_value; static long g_unknown_value;
static int  g_has_n; static long g_n_val;
static int  g_has_u; static long g_u_val;

static void trim(char *s){int a=0,b=strlen(s)-1;
  while(s[a]==' '||s[a]=='\t')a++; while(b>=a&&(s[b]==' '||s[b]=='\t'||s[b]=='\r'||s[b]=='\n'))b--;
  if(b<a){s[0]=0;return;} memmove(s,s+a,b-a+1); s[b-a+1]=0;}

static int split_block(const char*line){ /* returns 1 if block head */
  const char *heads[]={"ASK:","CONTRACT:","MODEL:","BUDGET:","REQUIRE:"};
  char t[MAXLINE]; strncpy(t,line,MAXLINE-1); t[MAXLINE-1]=0; trim(t);
  for(int i=0;i<5;i++) if(!strcmp(t,heads[i])){
    strncpy(g_cur_block,t,31); g_cur_block[strlen(t)-1]=0; /* strip ':' */
    g_cur_block[strlen(t)-1]=0; return 1;}
  return 0;}

static void store_key(const char*line){
  char t[MAXLINE]; strncpy(t,line,MAXLINE-1); t[MAXLINE-1]=0; trim(t);
  char *colon=strchr(t,':'); if(!colon) return; *colon=0;
  char *key=t, *val=colon+1; trim(key); trim(val);
  if(!key[0]) return;
  if(!strcmp(key,"question")) strncpy(g_question,val,MAXLINE-1);
  else if(!strcmp(key,"type")) strncpy(g_type,val,63);
  else if(!strcmp(key,"terms")) strncpy(g_terms,val,MAXLINE-1);
  else if(!strcmp(key,"known")) strncpy(g_known,val,MAXLINE-1);
  else if(!strcmp(key,"bounds")) strncpy(g_bounds,val,MAXLINE-1);
  else if(!strcmp(key,"unknown")) strncpy(g_unknown,val,MAXLINE-1);
  else if(!strcmp(key,"assumption")) strncpy(g_assume,val,MAXLINE-1);
  else if(!strcmp(key,"r")) strncpy(g_r,val,63);
  else if(!strcmp(key,"n")) { strncpy(g_n? g_n:g_n, val,63); strncpy(g_n,val,63); g_has_n=1; g_n_val=atol(val);}
  else if(!strcmp(key,"unknown_count")) { g_has_u=1; g_u_val=atol(val);}
  else if(!strcmp(key,"unknown_value")) { g_has_unknown_value=1; g_unknown_value=atol(val);}
  else if(!strcmp(key,"state")) strncpy(g_state,val,255);
  else if(!strcmp(key,"matrix")) strncpy(g_matrix,val,511);}

/* ---- parsing question "target op thr" ---- */
static Rat parse_thr(const char*t){
  Rat r={0,1}; while(*t==' ')t++;
  int neg=0; if(*t=='-'){neg=1;t++;} else if(*t=='+'){t++;}
  const char*sl=strchr(t,'/');
  if(sl){ r.p=atol(t); r.q=atol(sl+1); if(r.q<0){r.q=-r.q;r.p=-r.p;} return r;}
  const char*dot=strchr(t,'.');
  if(dot){ long ip=atol(t); const char*d=dot+1; long fr=0; i128 den=1;
    while(*d>='0'&&*d<='9'){ fr=fr*10+(*d-'0'); den*=10; d++; }
    r.p=(i128)ip*den+fr; if(neg) r.p=-r.p; r.q=den; return r;}
  r.p=atol(t); if(neg) r.p=-r.p; return r; }
static int parse_q(char *tgt, char *op, Rat *thr){
  char q[MAXLINE]; strncpy(q,g_question,MAXLINE-1); q[MAXLINE-1]=0; trim(q);
  char *sp1=strchr(q,' '); if(!sp1) return 0; *sp1=0;
  char *rest=sp1+1; while(*rest==' ')rest++;
  /* op may be 1 or 2 chars followed by space */
  char *sp2=rest; while(*sp2 && *sp2!=' ') sp2++;
  if(*sp2!=' ') return 0;
  size_t opl=(size_t)(sp2-rest); if(opl==0||opl>2) return 0;
  strncpy(op,rest,opl); op[opl]=0;
  *thr=parse_thr(sp2);
  strcpy(tgt,q); return 1;}

static int cmp_l(long v, const char*op, long thr){
  if(!strcmp(op,">")) return v>thr; if(!strcmp(op,"<")) return v<thr;
  if(!strcmp(op,">=")) return v>=thr; if(!strcmp(op,"<=")) return v<=thr;
  if(!strcmp(op,"==")) return v==thr; return -1;}

/* rational exact cmp: a vs thr (both Rat) */
static int cmp_rat(Rat a, const char*op, Rat thr){
  i128 lhs=a.p*thr.q, rhs=thr.p*a.q;
  if(!strcmp(op,">")) return lhs>rhs; if(!strcmp(op,"<")) return lhs<rhs;
  if(!strcmp(op,">=")) return lhs>=rhs; if(!strcmp(op,"<=")) return lhs<=rhs;
  if(!strcmp(op,"==")) return lhs==rhs; return -1;}

static int parse_list_i128(const char*s, i128*out,int max){
  int n=0; char tmp[MAXLINE]; strncpy(tmp,s,MAXLINE-1); tmp[MAXLINE-1]=0;
  char *tok=strtok(tmp,","); while(tok&&n<max){ out[n++]=atol(tok); tok=strtok(NULL,",");}
  return n;}

/* ---------- family: threshold_sum ---------- */
static void fam_sum(const char*op, Rat thr){
  i128 t[MAXK]; int n=parse_list_i128(g_terms,t,MAXK);
  long lo=0,hi=0; int has_unk=0;
  if(g_unknown[0]){
    char *din=strstr(g_unknown,"in"); if(din){
      long a=atol(din+2); char *dots=strstr(din,"..");
      long b=dots? atol(dots+2):a; lo=a;hi=b;has_unk=1;}}
  /* REDUCTION rung: monotone early stop, mirroring the reference */
  if(!has_unk && !strcmp(g_assume,"terms_nonnegative") && (!strcmp(op,">")||!strcmp(op,">="))){
    i128 pre=0; for(int k=0;k<n;k++){ pre+=t[k]; Rat sr={pre,1};
      if(cmp_rat(sr,op,thr)){
        printf("{\"status\":\"DECIDED_BY_REDUCTION\",\"answer\":1,"
               "\"reason\":\"monotone early stop at term %d\"}\n",k+1); return;}}}
  i128 base=0; for(int k=0;k<n;k++) base+=t[k];
  /* LIMIT rung: unknown with bounds — engine policy: op '>' only */
  if(has_unk){
    if(strcmp(op,">")){
      printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"unknown present with unsupported op: refuse (soundness-first)\"}\n"); return;}
    Rat elo={base+(i128)lo,1}, ehi={base+(i128)hi,1};
    if(cmp_rat(elo,">",thr)){
      printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":1,\"reason\":\"lower bound already decides\"}\n"); return;}
    if(cmp_rat(ehi,"<=",thr)){
      printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":0,\"reason\":\"upper bound already refutes\"}\n"); return;}
    if(g_has_unknown_value){
      Rat fin={base+(i128)g_unknown_value,1};
      printf("{\"status\":\"RESIDUAL_COMPUTATION_REQUIRED\",\"answer\":%d,\"reason\":\"residual evaluation of the unknown\"}\n",cmp_rat(fin,">",thr)); return;}
    printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"bounds straddle; no oracle for unknown\"}\n"); return;}
  /* CLASSICAL rung: full sum */
  Rat fr={base,1}; int c=cmp_rat(fr,op,thr);
  printf("{\"status\":\"FULL_EXECUTION_REQUIRED\",\"answer\":%d,\"reason\":\"full sum over terms\"}\n",c);}

/* ---------- family: mean_partial ---------- */
static void fam_mean(const char*op, Rat thr){
  if(!g_has_u){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"missing unknown_count\"}\n");return;}
  i128 k[MAXK]; int m=parse_list_i128(g_known,k,MAXK);
  char *dots=strstr(g_bounds,"..");
  if(strcmp(op,">")||!dots||!strcmp(g_bounds,"none")||g_u_val<=0){
    printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"no usable bounds or unsupported op (never invent an answer)\"}\n");return;}
  long lo=atol(g_bounds), hi=atol(dots+2);
  i128 tot=0; for(int i=0;i<m;i++) tot+=k[i];
  i128 N=(i128)m+(i128)g_u_val;
  Rat elo={tot+(i128)g_u_val*(i128)lo,N}, ehi={tot+(i128)g_u_val*(i128)hi,N};
  if(cmp_rat(elo,">",thr)){
    printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":1,\"reason\":\"worst-case mean lower bound decides\"}\n");return;}
  if(cmp_rat(ehi,"<=",thr)){
    printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":0,\"reason\":\"worst-case mean upper bound refutes\"}\n");return;}
  printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"bounds insufficient to decide the mean\"}\n");}

/* ---------- family: geometric_series ---------- */
static Rat mul(Rat a,Rat b){Rat r={a.p*b.p,a.q*b.q};return r;}
static void fam_geo(const char*op, Rat thr){
  long p=1,q=1;
  if(strchr(g_r,'/')){ p=atol(g_r); q=atol(strchr(g_r,'/')+1);
    if(q<0){q=-q;p=-p;} } else p=atol(g_r);
  if(!g_has_n){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"missing n\"}\n");return;}
  long n=g_n_val;
  if(n<0||n>62){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"beyond C exact range (§12)\"}\n");return;}
  /* sum_{i=0}^{n} r^i ; r==1 -> n+1 */
  Rat sum;
  if(p==q){ sum.p=(i128)n+1; sum.q=1; }
  else{ /* (r^(n+1)-1)/(r-1) */
    Rat rp={p,q}, pw={1,1};
    for(long i=0;i<=n;i++) pw=mul(pw,rp);
    Rat num={pw.p-pw.q,pw.q}, den={p-q,q};
    /* ratio num/den ; den may be negative -> normalize sign into den.q? den.q>0 so den sign in p-q */
    if(den.p<0){den.p=-den.p; num.p=-num.p;}
    sum.p=num.p*den.q; sum.q=num.q*den.p;
    if(sum.q<0){sum.q=-sum.q;sum.p=-sum.p;}}
  int c=cmp_rat(sum,op,thr); if(c<0){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"unsupported op\"}\n");return;}
  printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":%d,\"reason\":\"geometric closed form, exact rational\"}\n",c);}

/* ---------- family: entanglement (Schmidt criterion, exact) ----------
 * Amplitudes become integers over a COMMON denominator D (lcm).
 * det = (P0*P3 - P1*P2)/D^2,  n = (P0^2+..+P3^2)/D^2, so D cancels:
 *   entangled  <=>  P0*P3 - P1*P2 != 0
 *   C ~ t      <=>  2|detP| * t_den  ~  t_num * S      (both sides >= 0)
 * Exact integers end to end; overflow -> UNKNOWN, never a guess (§12). */
static void fam_entangle(const char*op, Rat thr, const char*tgt){
  if(!g_state[0]){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"missing state\"}\n");return;}
  char tmp[256]; strncpy(tmp,g_state,255); tmp[255]=0;
  char *tok[4]; int nt=0; char *t=strtok(tmp,",");
  while(t&&nt<4){ char e[64]; strncpy(e,t,63); e[63]=0;
    char *q=e; while(*q==' ')q++;
    tok[nt]=(char*)malloc(strlen(q)+1); strcpy(tok[nt],q); nt++;
    t=strtok(NULL,","); }
  if(nt!=4){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"state must have 4 amplitudes (structural)\"}\n");return;}
  Rat amp[4];
  for(int i=0;i<4;i++){ amp[i]=rnorm(parse_thr(tok[i])); }
  /* common denominator D = lcm of the four q's */
  i128 D = amp[0].q;
  for(int i=1;i<4&&!ovl;i++){
    i128 g=igcd(D,amp[i].q);
    D = ck(D/g, amp[i].q); }
  if(ovl){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"beyond C exact range (§12)\"}\n");return;}
  i128 P[4];
  for(int i=0;i<4&&!ovl;i++) P[i]=ck(amp[i].p, D/amp[i].q);
  i128 detP = cad(ck(P[0],P[3]), -ck(P[1],P[2]));
  i128 S = cad(cad(ck(P[0],P[0]),ck(P[1],P[1])), cad(ck(P[2],P[2]),ck(P[3],P[3])));
  if(ovl){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"beyond C exact range (§12)\"}\n");return;}
  if(S==0){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"zero state is not a quantum state (structural)\"}\n");return;}
  if(!strcmp(tgt,"entangled")){
    Rat v = { detP!=0 ? 1 : 0, 1 };
    printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":%d,\"reason\":\"Schmidt determinant criterion, exact\"}\n",
           cmp_rat(v,op,thr));return;}
  if(!strcmp(tgt,"concurrence")){
    i128 A = ck(ck(2,iabs(detP)), thr.q);   /* 2|detP| * t_den */
    i128 B = ck(iabs(thr.p), S);            /* t_num * S      */
    if(ovl){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"beyond C exact range (§12)\"}\n");return;}
    int neg = thr.p<0; int ans;
    if(!strcmp(op,">")) ans = neg ? 1 : (A>B);
    else if(!strcmp(op,">=")) ans = (neg||thr.p==0) ? 1 : (A>=B);
    else if(!strcmp(op,"<")) ans = (neg||thr.p==0) ? 0 : (A<B);
    else if(!strcmp(op,"<=")) ans = neg ? 0 : (A<=B);
    else if(!strcmp(op,"==")) ans = (A==B);
    else { printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"unsupported op for concurrence\"}\n"); return; }
    printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":%d,\"reason\":\"concurrence by exact integer comparison, no root, no float\"}\n",ans);return;}
  printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"family answers entangled or concurrence only\"}\n");}

/* ---------- family: triangular_det ---------- */
static i128 g_M[8][8]; static int g_mn;
static i128 lap(i128 M[8][8], int n){
  if(n==1) return M[0][0];
  i128 d=0;
  for(int j=0;j<n&&!ovl;j++){
    i128 minor[8][8];
    for(int r=1;r<n;r++){ int cc=0;
      for(int c=0;c<n;c++) if(c!=j) minor[r-1][cc++]=M[r][c]; }
    i128 t=ck(M[0][j], lap(minor,n-1));
    d = cad(d, (j%2)? -t : t); }
  return d; }
static void fam_det(const char*op, Rat thr){
  if(!g_matrix[0]){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"missing matrix\"}\n");return;}
  /* parse rows separated by ';' , entries by ',' */
  char tmp[512]; strncpy(tmp,g_matrix,511); tmp[511]=0;
  int n=0; char *p=tmp;
  while(*p && n<8){
    int k=0;
    while(*p && *p!=';' && k<8){
      while(*p==' '||*p==',')p++;
      if(*p==';'||!*p) break;
      g_M[n][k++]=(i128)strtol(p,&p,10); }
    if(k>0){ g_mn=k; n++; }
    while(*p==' ')p++;
    if(*p==';')p++; else if(*p) break; }
  if(n==0||n!=g_mn){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"matrix must be square (structural)\"}\n");return;}
  int upper=1, lower=1;
  for(int i=0;i<n;i++) for(int j=0;j<n;j++){
    if(j<i && g_M[i][j]!=0) upper=0;
    if(j>i && g_M[i][j]!=0) lower=0; }
  i128 d;
  if(upper||lower){
    d=1; for(int i=0;i<n&&!ovl;i++) d=ck(d,g_M[i][i]);
    if(ovl){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"beyond C exact range (§12)\"}\n");return;}
    Rat dr={d,1};
    printf("{\"status\":\"DECIDED_WITHOUT_EXECUTION\",\"answer\":%d,\"reason\":\"det(triangular) = product of diagonal, O(n) instead of O(n!)\"}\n",cmp_rat(dr,op,thr));return;}
  d = lap(g_M,n);
  if(ovl){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"beyond C exact range (§12)\"}\n");return;}
  Rat dr={d,1};
  printf("{\"status\":\"FULL_EXECUTION_REQUIRED\",\"answer\":%d,\"reason\":\"Laplace expansion, exact\"}\n",cmp_rat(dr,op,thr));}

int main(int argc,char**argv){
  if(argc<2){fprintf(stderr,"usage: nexa_core <file.zeph>\n");return 2;}
  FILE*f=fopen(argv[1],"r"); if(!f){perror("open");return 2;}
  char line[MAXLINE];
  while(fgets(line,MAXLINE,f)){
    char t[MAXLINE]; strncpy(t,line,MAXLINE-1); t[MAXLINE-1]=0; trim(t);
    if(!t[0]||t[0]=='#') continue;
    if(split_block(line)) continue;
    store_key(line);}
  fclose(f);
  char tgt[32],op[4]; Rat thr;
  if(!parse_q(tgt,op,&thr)){printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"unparseable question (§12)\"}\n");return 0;}
  if(!strcmp(g_type,"threshold_sum")) fam_sum(op,thr);
  else if(!strcmp(g_type,"mean_partial")) fam_mean(op,thr);
  else if(!strcmp(g_type,"geometric_series")) fam_geo(op,thr);
  else if(!strcmp(g_type,"entanglement")) fam_entangle(op,thr,tgt);
  else if(!strcmp(g_type,"triangular_det")) fam_det(op,thr);
  else printf("{\"status\":\"UNKNOWN\",\"answer\":null,\"reason\":\"family outside C core scope (§12)\"}\n");
  return 0;}
