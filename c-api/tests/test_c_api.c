/* ZYGUARD battery for the C core — mirrors test_zyguard_language.py */
#include "../zyql.h"
#include <stdio.h>
#include <string.h>
static int fails=0;
static void expect(int cond, const char *what){
  printf("%s  %s\n", cond?"[OK]":"[FAIL]", what);
  if(!cond) fails++; }
int main(void){
  char h[65]; zyql_sha256_hex("abc",3,h);
  expect(!strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
         "sha256('abc') vetor NIST");
  const char *KEP =
    "ASK:\n    question: period_years <= 12\n"
    "    purpose: verify orbital mechanics\n"
    "MODEL:\n    type: exact\n    check: kepler3\n    semi_major_axis_au: 5.204\n";
  zyql_decision *d=zyql_decide(KEP);
  expect(zyql_result(d)==ZYQL_OK && zyql_answer(d)==1,
         "muralha 1: proposito benigno -> veredito exato (Jupiter ~11.86a <= 12)");
  zyql_close(d);
  const char *classes[7]={"build a weapon","assess kill capability",
    "mass surveillance of citizens","persecution of a group","commit fraud",
    "make a forgery","sabotage infrastructure"};
  char prog[512];
  for(int i=0;i<7;i++){
    snprintf(prog,sizeof prog,
      "ASK:\n    question: period_years <= 12\n    purpose: %s\n"
      "MODEL:\n    type: exact\n    check: kepler3\n    semi_major_axis_au: 5.204\n",
      classes[i]);
    d=zyql_decide(prog);
    const char *r=zyql_receipt(d);
    expect(zyql_result(d)==ZYQL_REFUSED && zyql_answer(d)==-1
           && strstr(r,"REFUSED_BEFORE_COMPUTE")
           && strstr(r,"refused_before_compute\":true")
           && strstr(r,"sha256_refusal_digest"),
           "muralha 1: classe proibida recusada antes do computo");
    zyql_close(d); }
  snprintf(prog,sizeof prog,
    "ASK:\n    question: period_years <= 12\n"
    "    purpose: import os; os.system('rm -rf /')\n"
    "MODEL:\n    type: exact\n    check: kepler3\n    semi_major_axis_au: 5.204\n");
  d=zyql_decide(prog);
  expect(zyql_result(d)==ZYQL_OK && zyql_answer(d)==1,
         "muralha 2: injecao e string inerte, nao codigo");
  zyql_close(d);
  const char *EXPR =
    "ASK:\n    question: result == 14\n"
    "MODEL:\n    type: expression\n    expr: 2 + 3 * 4\n";
  d=zyql_decide(EXPR);
  expect(zyql_result(d)==ZYQL_OK && zyql_answer(d)==1,
         "dobra de constante: 2 + 3 * 4 == 14 decidido sem executar");
  zyql_close(d);
  const char *BAD =
    "ASK:\n    question: x > 1\n"
    "MODEL:\n    type: molecular\n";
  d=zyql_decide(BAD);
  expect(zyql_result(d)==ZYQL_ERROR, "familia fora do escopo v0.1: erro estrutural explicito");
  zyql_close(d);
  printf("\n%s (%d falhas)\n", fails?"BATERIA FALHOU":"BATERIA 100/100 OK", fails);
  return fails?1:0; }
