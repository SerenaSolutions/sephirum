/* Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM (autônomo — sem runtime).
 * Família: geometric_inf · pergunta: sum/mean < 2
 * §EXACT: aritmética __int128; §12: limites ±9,2e18. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

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

int main(void){
  /* certificado embutido (fonte ZEPHIRUM) */
  const char *DATA = "1|1/2";
  const char *OP = "<";
  long long THR = 2LL;
  long long UNITS = 2LL;
  long long A=1LL,B=1LL,P=1LL,Q=2LL;
  /* |r|<1 garantido pelo transpilador; S=A*Q/(B*(Q-P)) */
  int verdict = decide(cmpv(LL(A)*LL(Q), LL(THR)*LL(B)*(LL(Q)-LL(P))), OP);
  uint8_t d[32]; char hex[65];
  sha256(DATA, d); hex32(d, hex);
  printf("VERDICT %d\nHASH %s\nUNITS %lld\n", verdict, hex, UNITS);
  return 0;
}
