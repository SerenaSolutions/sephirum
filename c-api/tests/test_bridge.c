/* BRIDGE battery: quantum-language circuit gate + LLM receipt check */
#include "../zyql.h"
#include <stdio.h>
#include <string.h>
static int fails=0;
static void expect(int cond,const char *what){
  printf("%s  %s\n",cond?"[OK]":"[FAIL]",what); if(!cond) fails++; }
int main(void){
  const char *BELL=
    "OPENQASM 3.0;\ninclude \"stdgates.inc\";\n"
    "qubit[2] q;\nbit[2] c;\nh q[0];\ncx q[0], q[1];\n"
    "c = measure q;\n";
  zyql_decision *d=zyql_gate_circuit(
      "research entanglement statistics",BELL);
  const char *r=zyql_receipt(d);
  expect(zyql_result(d)==ZYQL_OK && strstr(r,"PASSED_PORTGATE")
         && strstr(r,"CIRCUIT_SHA256"),
         "circuito Bell (texto OQ3 de qualquer linguagem quantica) passa a porta");
  zyql_close(d);
  d=zyql_gate_circuit("commit fraud",BELL);
  r=zyql_receipt(d);
  expect(zyql_result(d)==ZYQL_REFUSED && strstr(r,"REFUSED_BEFORE_COMPUTE")
         && strstr(r,"sha256_refusal_digest"),
         "mesmo circuito com proposito proibido: recusado ANTES de qualquer execucao");
  char receipt[4096]; snprintf(receipt,sizeof receipt,"%s",r);
  zyql_close(d);
  expect(zyql_verify_receipt(receipt)==1,
         "modelo de linguagem verifica recibo original em C puro: VALIDO");
  char *canon_p=strstr(receipt,"canonical_refusal");
  char *bad=strstr(canon_p,"fraud");
  if(bad) *bad='F';  /* tamper one byte of the purpose inside canonical */
  expect(zyql_verify_receipt(receipt)==0,
         "recibo adulterado: C puro detecta INVALIDO");
  expect(zyql_verify_receipt("{\"STATUS\":\"x\"}")==-1,
         "recibo sem campos de recusa: MALFORMADO");
  printf("\n%s (%d falhas)\n",fails?"PONTE FALHOU":"BATERIA PONTE 5/5 OK",fails);
  return fails?1:0; }
