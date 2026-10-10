/* zyql.c — ZYQL verified-decision core, single-file amalgamation v0.1.0
 * C99, no dependencies. Parity-tested against prototype/nexa_core.py.
 * The purpose string is DATA, never executed (structural purity). */
#include "zyql.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <stdarg.h>

/* ------------------------------------------------------------ SHA-256 */
typedef struct { unsigned long len; unsigned long buf; unsigned char b[64];
                 unsigned int h[8]; } sha_ctx;
static unsigned int rotr(unsigned x, int n){return (x>>n)|(x<<(32-n));}
static void sha_init(sha_ctx *c){ c->len=0; c->buf=0;
  unsigned int k[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                     0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
  for(int i=0;i<8;i++) c->h[i]=k[i]; }
static void sha_block(sha_ctx *c, const unsigned char *p){
  static const unsigned int K[64]={
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
  unsigned w[64];
  for(int i=0;i<16;i++) w[i]=((unsigned)p[i*4]<<24)|(p[i*4+1]<<16)|(p[i*4+2]<<8)|p[i*4+3];
  for(int i=16;i<64;i++){unsigned s0=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3);
    unsigned s1=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10);
    w[i]=w[i-16]+s0+w[i-7]+s1;}
  unsigned a=c->h[0],b=c->h[1],cc=c->h[2],d=c->h[3],e=c->h[4],f=c->h[5],g=c->h[6],h=c->h[7];
  for(int i=0;i<64;i++){
    unsigned S1=rotr(e,6)^rotr(e,11)^rotr(e,25);
    unsigned ch=(e&f)^((~e)&g);
    unsigned t1=h+S1+ch+K[i]+w[i];
    unsigned S0=rotr(a,2)^rotr(a,13)^rotr(a,22);
    unsigned mj=(a&b)^(a&cc)^(b&cc);
    unsigned t2=S0+mj;
    h=g;g=f;f=e;e=d+t1;d=cc;cc=b;b=a;a=t1+t2;}
  c->h[0]+=a;c->h[1]+=b;c->h[2]+=cc;c->h[3]+=d;c->h[4]+=e;c->h[5]+=f;c->h[6]+=g;c->h[7]+=h;}
static void sha_update(sha_ctx *c, const void *data, unsigned long n){
  const unsigned char *p=data; c->len+=n;
  while(n--){ c->b[c->buf++]=*p++;
    if(c->buf==64){ sha_block(c,c->b); c->buf=0; } } }
static void sha_final(sha_ctx *c, unsigned char out[32]){
  unsigned long bits=c->len*8; unsigned char pad=0x80;
  sha_update(c,&pad,1); unsigned char z=0;
  while(c->buf!=56) sha_update(c,&z,1);
  unsigned char l[8]; for(int i=0;i<8;i++) l[i]=(unsigned char)(bits>>(56-8*i));
  c->len-=8; /* do not count the length bytes */
  for(int i=0;i<8;i++){ sha_update(c,l+i,1);} /* stream-safe */
  for(int i=0;i<8;i++){ out[i*4]=c->h[i]>>24; out[i*4+1]=c->h[i]>>16;
    out[i*4+2]=c->h[i]>>8; out[i*4+3]=c->h[i]; } }
void zyql_sha256_hex(const void *data, unsigned long len, char out[65]){
  sha_ctx c; sha_init(&c); sha_update(&c,data,len);
  unsigned char d[32]; sha_final(&c,d);
  for(int i=0;i<32;i++) sprintf(out+i*2,"%02x",d[i]); out[64]=0; }

/* ------------------------------------------------------- small utils */
static char *xstrdup(const char *s){ size_t n=strlen(s)+1; char *p=malloc(n);
  if(p) memcpy(p,s,n); return p; }
static void *xrealloc(void *p, size_t n){ p=realloc(p,n); if(!p) exit(2); return p; }

/* ci word-boundary match (regex \bword\b semantics) */
static int word_match(const char *hay, const char *needle){
  size_t nl=strlen(needle);
  for(const char *p=hay; *p; p++){
    if(tolower((unsigned char)*p)==tolower((unsigned char)needle[0])){
      size_t i=0;
      while(p[i] && i<nl &&
            tolower((unsigned char)p[i])==tolower((unsigned char)needle[i])) i++;
      if(i==nl){
        int before=(p==hay)||!isalnum((unsigned char)p[-1])&&p[-1]!='_';
        int after=(!p[nl])||!isalnum((unsigned char)p[nl])&&p[nl]!='_';
        if(before&&after) return 1; } } }
  return 0; }

static const char *const P_CLASSES[7]={
  "weapons","lethality","surveillance","persecution","fraud","forgery","sabotage"};
static const char *const P_WORDS[7][3]={
  {"weapon","gun","explosive"}, {"lethal","kill","assassination"},
  {"surveillance","spy","tracking"}, {"persecution","harassment","stalking"},
  {"fraud","scam","phishing"}, {"forgery","counterfeit",NULL},
  {"sabotage","disrupt",NULL} };
static const char *const P_WORDS_EXTRA[2][2]={{"ammunition",NULL},
                                             {NULL,NULL}};

const char *zyql_purpose_class(const char *purpose){
  if(!purpose) return NULL;
  for(int c=0;c<7;c++){
    int nw=3; if(!P_WORDS[c][2]) nw=2;
    for(int w=0;w<nw;w++)
      if(word_match(purpose,P_WORDS[c][w])) return P_CLASSES[c];
    if(c==0 && word_match(purpose,"ammunition")) return "weapons";
  }
  return NULL; }

/* -------------------------------------------------------- NEXA parse */
typedef struct { char *k, *v; } kv;
typedef struct { char *name; kv *items; int n, cap; } block;
typedef struct { block *b; int n; } blocks;

static block *find_block(blocks *B, const char *name){
  for(int i=0;i<B->n;i++) if(!strcmp(B->b[i].name,name)) return &B->b[i];
  return NULL; }
static const char *block_get(block *b, const char *k){
  if(!b) return NULL;
  for(int i=0;i<b->n;i++) if(!strcmp(b->items[i].k,k)) return b->items[i].v;
  return NULL; }
static void block_add(block *b, char *k, char *v){
  if(b->n==b->cap){ b->cap=b->cap?b->cap*2:4;
    b->items=xrealloc(b->items,sizeof(kv)*(size_t)b->cap); }
  b->items[b->n].k=k; b->items[b->n].v=v; b->n++; }

static char *trim(char *s){
  while(*s && isspace((unsigned char)*s)) s++;
  char *e=s+strlen(s);
  while(e>s && isspace((unsigned char)e[-1])) *--e=0;
  return s; }

static int parse_nexa(blocks *B, const char *src, char **err){
  char *cur_name=NULL; block *cur=NULL; *err=NULL;
  char *dup=xstrdup(src), *line=dup;
  while(line && *line){
    char *nl=strchr(line,'\n'); if(nl) *nl=0;
    char *l=trim(line);
    if(*l && *l!='#'){
      char head[64]; size_t hl=strlen(l);
      int is_head=0;
      if(hl && l[hl-1]==':'){
        snprintf(head,sizeof head,"%.*s",(int)(hl-1),l);
        if(!strcmp(head,"ASK")||!strcmp(head,"CONTRACT")||!strcmp(head,"MODEL")||
           !strcmp(head,"BUDGET")||!strcmp(head,"REQUIRE")) is_head=1;
        else { static char e[128];
               snprintf(e,sizeof e,"line outside block: %s",l);
               *err=e; free(dup); return 0; } }
      if(is_head){
        B->b=xrealloc(B->b,sizeof(block)*(size_t)(B->n+1));
        block *nb=&B->b[B->n++]; nb->name=xstrdup(head); nb->items=NULL;
        nb->n=nb->cap=0; cur=nb; cur_name=nb->name;
      } else if(cur){
        char *colon=strchr(l,':');
        if(colon){ *colon=0;
          block_add(cur,xstrdup(trim(l)),xstrdup(trim(colon+1)));
        } else block_add(cur,xstrdup(trim(l)),xstrdup("")); /* bare flag */
      } else { static char e[128];
        snprintf(e,sizeof e,"line outside block: %s",l);
        *err=e; free(dup); return 0; }
    }
    line = nl ? nl+1 : NULL;
  }
  free(dup);
  if(!find_block(B,"ASK")||!find_block(B,"MODEL")){
    static char e[]="missing ASK or MODEL block"; *err=e; return 0; }
  return 1; }

/* ------------------------------------------- canonical JSON (parity) */
/* Python: json.dumps(obj, sort_keys=True) — nested dicts, default
 * separators (", ", ": "), ensure_ascii, keys sorted. Values here are
 * always strings (NEXA parser output) or nested string-dicts. */
typedef struct { char *s; size_t n, cap; } sb;
static void sb_add(sb *o, const char *fmt, ...){
  va_list a; va_start(a,fmt); vsnprintf(NULL,0,fmt,a); va_end(a);
  va_start(a,fmt); int need=vsnprintf(NULL,0,fmt,a); va_end(a);
  if(o->n+(size_t)need+1>o->cap){ o->cap=(o->n+(size_t)need+1)*2;
    o->s=xrealloc(o->s,o->cap); }
  va_start(a,fmt); o->n+=(size_t)vsnprintf(o->s+o->n,(size_t)need+1,fmt,a); va_end(a); }
static void sb_json_str(sb *o, const char *v){
  sb_add(o,"\"");
  for(const char *p=v; *p; p++){
    unsigned char c=(unsigned char)*p;
    if(c=='"'||c=='\\') sb_add(o,"\\%c",*p);
    else if(c=='\n') sb_add(o,"\\n");
    else if(c=='\t') sb_add(o,"\\t");
    else if(c=='\r') sb_add(o,"\\r");
    else if(c<0x20) sb_add(o,"\\u%04x",c);
    else sb_add(o,"%c",*p); }
  sb_add(o,"\""); }
static int kv_cmp(const void *a, const void *b){
  return strcmp(((const kv*)a)->k,((const kv*)b)->k); }
static void sb_block_json(sb *o, block *b){
  /* sort_keys=True on Python dicts; duplicate keys collapse — none here */
  qsort(b->items,(size_t)b->n,sizeof(kv),kv_cmp);
  sb_add(o,"{");
  for(int i=0;i<b->n;i++){
    if(i) sb_add(o,", ");
    sb_json_str(o,b->items[i].k); sb_add(o,": ");
    sb_json_str(o,b->items[i].v); }
  sb_add(o,"}"); }
static void input_hash(blocks *B, char out[65]){
  /* canonical: {"ASK": {...}, "CONTRACT": {...}, "MODEL": {...}} sorted */
  sb o={0}; sb_add(&o,"{");
  int first=1; const char *names[5]={"ASK","CONTRACT","MODEL","BUDGET","REQUIRE"};
  for(int i=0;i<5;i++){ block *b=find_block(B,names[i]); if(!b) continue;
    if(!first) sb_add(&o,", ");
    first=0;
    sb_json_str(&o,names[i]); sb_add(&o,": ");
    sb_block_json(&o,b); }
  sb_add(&o,"}");
  zyql_sha256_hex(o.s,(unsigned long)o.n,out);
  free(o.s); }

/* -------------------------------------------------------- arithmetic */
static int parse_num(const char *s, double *out){
  char *end; double v=strtod(s,&end);
  if(end==s || *trim(end)) return 0;
  *out=v; return 1; }
static int cmp_op(double v, const char *op, double thr){
  if(!strcmp(op,">"))  return v>thr;
  if(!strcmp(op,">=")) return v>=thr;
  if(!strcmp(op,"<"))  return v<thr;
  if(!strcmp(op,"<=")) return v<=thr;
  if(!strcmp(op,"==")) return v==thr;
  return 0; }
static int parse_question(const char *q, char *target, size_t tsz,
                          char *op, double *thr){
  const char *ops[5]={">=","<=","==",">","<"};
  for(int i=0;i<5;i++){
    const char *p=strstr(q,ops[i]);
    if(p){ size_t tl=(size_t)(p-q);
      snprintf(target,tsz>tl+1?tl+1:tsz,"%.*s",(int)tl,q);
      char *t2=trim(target); if(t2!=target) memmove(target,t2,strlen(t2)+1);
      snprintf(op,8,"%s",ops[i]);
      char vbuf[64]; snprintf(vbuf,sizeof vbuf,"%s",p+strlen(ops[i]));
      if(!parse_num(trim(vbuf),thr)) return 0;
      return 1; } }
  return 0; }

/* safe constant folding: + - * / ( ) and unary -, doubles only */
typedef struct { const char *p; int ok; } fe;
static double fe_expr(fe *e);
static double fe_num(fe *e){
  while(*e->p==' ') e->p++;
  if(*e->p=='('){ e->p++; double v=fe_expr(e);
    while(*e->p==' ') e->p++;
    if(*e->p==')') e->p++; else e->ok=0; return v; }
  if(*e->p=='-') { e->p++; return -fe_num(e); }
  char *end; double v=strtod(e->p,&end);
  if(end==e->p) { e->ok=0; return 0; }
  e->p=end; return v; }
static double fe_term(fe *e){
  double v=fe_num(e);
  for(;;){ while(*e->p==' ') e->p++;
    if(*e->p=='*'){ e->p++; v*=fe_num(e); }
    else if(*e->p=='/'){ e->p++; double d=fe_num(e);
      if(d==0){ e->ok=0; return v; } v/=d; }
    else return v; } }
static double fe_expr(fe *e){
  double v=fe_term(e);
  for(;;){ while(*e->p==' ') e->p++;
    if(*e->p=='+'){ e->p++; v+=fe_term(e); }
    else if(*e->p=='-'){ e->p++; v-=fe_term(e); }
    else return v; } }

/* ------------------------------------------------------ decision obj */
struct zyql_decision { zyql_status st; int answer; char *receipt;
                       char *message; };

static void receipt_bool(sb *o, int v){ sb_add(o,v?"true":"false"); }

zyql_decision *zyql_decide(const char *program_src){
  struct zyql_decision *d=calloc(1,sizeof *d);
  if(!d) return NULL;
  d->st=ZYQL_ERROR; d->answer=-1;
  blocks B={0}; char *err=NULL;
  if(!parse_nexa(&B,program_src,&err)){
    d->message=xstrdup(err?err:"parse error");
    sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
    sb_json_str(&o,d->message); sb_add(&o,"}");
    d->receipt=o.s; return d; }

  char ih[65]; input_hash(&B,ih);
  block *ask=find_block(&B,"ASK"), *model=find_block(&B,"MODEL");
  block *contract=find_block(&B,"CONTRACT");

  /* PORTGATE first: judge intent BEFORE any compute */
  const char *purpose=block_get(ask,"purpose");
  const char *cls=zyql_purpose_class(purpose?purpose:"");
  if(purpose && *purpose && cls){
    sb canon={0};
    sb_add(&canon,"{\"class\":"); sb_json_str(&canon,cls);
    sb_add(&canon,",\"list_version\":\"1\",\"purpose_verbatim\":");
    sb_json_str(&canon,purpose); sb_add(&canon,"}");
    char dig[65]; zyql_sha256_hex(canon.s,(unsigned long)canon.n,dig);
    sb o={0};
    sb_add(&o,"{\"INPUT_HASH\":\"%s\",\"QUESTION\":",ih);
    sb_json_str(&o,block_get(ask,"question")?block_get(ask,"question"):"");
    sb_add(&o,",\"MODEL_TYPE\":");
    sb_json_str(&o,block_get(model,"type")?block_get(model,"type"):"");
    sb_add(&o,",\"KERNEL\":\"PORTGATE\",\"RUNG\":\"ANALYSIS\",");
    sb_add(&o,"\"EVIDENCE\":{\"gate\":\"PORTGATE\",\"list_version\":\"1\",");
    sb_add(&o,"\"class\":"); sb_json_str(&o,cls);
    sb_add(&o,",\"purpose_verbatim\":"); sb_json_str(&o,purpose);
    sb_add(&o,",\"refused_before_compute\":true,");
    sb_add(&o,"\"sha256_refusal_digest\":\"%s\",",dig);
    sb_add(&o,"\"canonical_refusal\":"); sb_json_str(&o,canon.s);
    sb_add(&o,"},\"STATUS\":\"REFUSED_BEFORE_COMPUTE\",\"ANSWER\":null}");
    free(canon.s);
    d->st=ZYQL_REFUSED; d->answer=-1; d->receipt=o.s;
    d->message=xstrdup("prohibited purpose class; refused before compute");
    return d; }

  /* contract: only absolute_error = 0 (exact) is implemented */
  if(contract && contract->n){
    const char *ae=block_get(contract,"absolute_error");
    if(ae && strcmp(ae,"0") && strcmp(ae,"0.0") && *ae){
      d->message=xstrdup("unsupported contract: only absolute_error = 0");
      sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
      sb_json_str(&o,d->message); sb_add(&o,"}");
      d->receipt=o.s; return d; }
    for(int i=0;i<contract->n;i++)
      if(strcmp(contract->items[i].k,"absolute_error")){
        d->message=xstrdup("unsupported contract keys");
        sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
        sb_json_str(&o,d->message); sb_add(&o,"}");
        d->receipt=o.s; return d; } }

  const char *q=block_get(ask,"question");
  char target[128], op[8]; double thr;
  if(!q || !parse_question(q,target,sizeof target,op,&thr)){
    d->message=xstrdup("unparseable question");
    sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
    sb_json_str(&o,d->message); sb_add(&o,"}");
    d->receipt=o.s; return d; }

  const char *type=block_get(model,"type");
  double value=0; const char *kernel=NULL,*rung=NULL,*check=NULL;
  if(type && !strcmp(type,"exact") && block_get(model,"check") &&
      !strcmp(block_get(model,"check"),"kepler3")){
    double a; if(!parse_num(block_get(model,"semi_major_axis_au"),&a)){
      d->message=xstrdup("invalid semi_major_axis_au");
      sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
      sb_json_str(&o,d->message); sb_add(&o,"}");
      d->receipt=o.s; return d; }
    value=pow(a,1.5); kernel="EXACT_KEPLER_III"; rung="ANALYSIS"; check="kepler3";
  } else if(type && !strcmp(type,"expression")){
    const char *expr=block_get(model,"expr");
    if(!expr){ d->message=xstrdup("missing expr");
      sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
      sb_json_str(&o,d->message); sb_add(&o,"}");
      d->receipt=o.s; return d; }
    fe e={expr,1}; value=fe_expr(&e);
    while(*e.p==' ') e.p++;
    if(!e.ok||*e.p){ d->message=xstrdup("expression not foldable");
      sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
      sb_json_str(&o,d->message); sb_add(&o,"}");
      d->receipt=o.s; return d; }
    kernel="CONSTANT_FOLD"; rung="SIMPLIFICATION"; check=expr;
  } else {
    d->message=xstrdup("unsupported model type in C core v0.1 "
                       "(see nexa_core.py for the full ladder)");
    sb o={0}; sb_add(&o,"{\"STATUS\":\"STRUCTURAL_ERROR\",\"MESSAGE\":");
    sb_json_str(&o,d->message); sb_add(&o,"}");
    d->receipt=o.s; return d; }

  int ans=cmp_op(value,op,thr);
  sb o={0};
  sb_add(&o,"{\"INPUT_HASH\":\"%s\",\"QUESTION\":",ih); sb_json_str(&o,q);
  sb_add(&o,",\"MODEL_TYPE\":"); sb_json_str(&o,type);
  sb_add(&o,",\"KERNEL\":\"%s\",\"RUNG\":\"%s\",",kernel,rung);
  sb_add(&o,"\"EVIDENCE\":{\"input_hash\":\"%s\",\"kernel\":\"%s\",",ih,kernel);
  if(!strcmp(kernel,"EXACT_KEPLER_III")){
    sb_add(&o,"\"check\":\"kepler3\",\"period_years\":%.17g,",value);
    sb_add(&o,"\"law\":\"T^2 = a^3 (host mass = 1 solar)\",");
  } else { sb_add(&o,"\"expr\":"); sb_json_str(&o,check);
           sb_add(&o,",\"value\":%.17g,",value); }
  sb_add(&o,"\"assumption\":");
  sb_json_str(&o,block_get(model,"assumption")?block_get(model,"assumption"):"");
  sb_add(&o,",\"question\":"); sb_json_str(&o,q);
  sb_add(&o,"},\"STATUS\":\"DECIDED_WITHOUT_EXECUTION\",\"ANSWER\":");
  receipt_bool(&o,ans); sb_add(&o,"}");
  d->st=ZYQL_OK; d->answer=ans; d->receipt=o.s;
  d->message=xstrdup("decided without execution");
  return d; }


/* -------------------------------------------------- v0.2: the bridge */
static const char *json_get_str(const char *json, const char *key,
                                char *out, size_t outsz){
  char pat[64]; snprintf(pat,sizeof pat,"\"%s\"",key);
  const char *p=strstr(json,pat); if(!p) return NULL;
  p=strstr(p+strlen(pat),"\""); if(!p) return NULL; p++;
  size_t n=0;
  while(*p && n<outsz-1){
    if(*p=='\\'){ p++;
      if(*p=='"') out[n++]='"';
      else if(*p=='\\') out[n++]='\\';
      else if(*p=='n') out[n++]='\n';
      else if(*p=='t') out[n++]='\t';
      else if(*p=='r') out[n++]='\r';
      else break; p++; }
    else if(*p=='"') break;
    else out[n++]=*p++; }
  if(*p!='"') return NULL;
  out[n]=0; return out; }

zyql_decision *zyql_gate_circuit(const char *purpose,
                                 const char *openqasm3_src){
  struct zyql_decision *d=calloc(1,sizeof *d);
  if(!d) return NULL;
  const char *cls=zyql_purpose_class(purpose?purpose:"");
  char cdig[65]; zyql_sha256_hex(openqasm3_src?openqasm3_src:"",
                                 openqasm3_src?(unsigned long)strlen(openqasm3_src):0,
                                 cdig);
  sb o={0};
  if(cls){
    sb canon={0};
    sb_add(&canon,"{\"class\":"); sb_json_str(&canon,cls);
    sb_add(&canon,",\"list_version\":\"1\",\"purpose_verbatim\":");
    sb_json_str(&canon,purpose); sb_add(&canon,"}");
    char dig[65]; zyql_sha256_hex(canon.s,(unsigned long)canon.n,dig);
    sb_add(&o,"{\"GATE\":\"PORTGATE_CIRCUIT\",\"CIRCUIT_SHA256\":\"%s\",",cdig);
    sb_add(&o,"\"EVIDENCE\":{\"gate\":\"PORTGATE_CIRCUIT\",");
    sb_add(&o,"\"list_version\":\"1\",\"class\":"); sb_json_str(&o,cls);
    sb_add(&o,",\"purpose_verbatim\":"); sb_json_str(&o,purpose);
    sb_add(&o,",\"refused_before_compute\":true,");
    sb_add(&o,"\"sha256_refusal_digest\":\"%s\",",dig);
    sb_add(&o,"\"canonical_refusal\":"); sb_json_str(&o,canon.s);
    sb_add(&o,"},\"STATUS\":\"REFUSED_BEFORE_COMPUTE\",\"ANSWER\":null}");
    free(canon.s);
    d->st=ZYQL_REFUSED; d->answer=-1; d->receipt=o.s;
    d->message=xstrdup("prohibited purpose class; circuit refused before execution");
    return d; }
  sb_add(&o,"{\"GATE\":\"PORTGATE_CIRCUIT\",\"CIRCUIT_SHA256\":\"%s\",",cdig);
  sb_add(&o,"\"EVIDENCE\":{\"purpose_verbatim\":");
  sb_json_str(&o,purpose?purpose:"");
  sb_add(&o,",\"circuit_sha256\":\"%s\",",cdig);
  sb_add(&o,"\"note\":\"ZYQL gates and never executes; "
            "the target backend executes\"},");
  sb_add(&o,"\"STATUS\":\"PASSED_PORTGATE\",\"ANSWER\":null}");
  d->st=ZYQL_OK; d->answer=-1; d->receipt=o.s;
  d->message=xstrdup("circuit passed the purpose gate");
  return d; }

int zyql_verify_receipt(const char *receipt_json){
  if(!receipt_json) return -1;
  char canon[2048], dig[128];
  if(!json_get_str(receipt_json,"canonical_refusal",canon,sizeof canon))
    return -1;
  if(!json_get_str(receipt_json,"sha256_refusal_digest",dig,sizeof dig))
    return -1;
  char real[65]; zyql_sha256_hex(canon,(unsigned long)strlen(canon),real);
  return strcmp(real,dig)==0 ? 1 : 0; }

zyql_status zyql_result(const zyql_decision *d){ return d?d->st:ZYQL_ERROR; }
int zyql_answer(const zyql_decision *d){ return d?d->answer:-1; }
const char *zyql_receipt(const zyql_decision *d){ return d?d->receipt:"{}"; }
const char *zyql_message(const zyql_decision *d){ return d?d->message:""; }
void zyql_close(zyql_decision *d){
  if(d){ free(d->receipt); free(d->message); free(d); } }
