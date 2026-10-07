# PASSO 7 — TRUST: assinatura Ed25519 de emitente

Data: 2026-10-07 · `zephirum_trust.py` + `test_trust.py` (T1-T6, PASS).
Dependências opcionais: `cryptography`, `pynacl`
(`prototype/requirements-trust.txt`); sem elas, falha explícita
(TrustNotAvailable), nunca silêncio.

## O que fecha

O ciclo de confiança do certificado tinha duas pontas:
- INTEGRIDADE (Fase 3): CERT_HASH sela o payload canônico.
- AUTENTICIDADE (este passo): SIGNATURE Ed25519 do emitente cobre o
  MESMO payload canônico; ISSUER tem que estar no registro de
  emitentes confiáveis (`trusted_issuers.txt`).

Quem adultera um certificado assinado quebra a assinatura (T3: um
único bit de ANSWER/STATUS/EVIDENCE/COST_ESTIMATE/ELIMINATION_TRACE
invalida). Quem forja um certificado novo com chave própria não está
no registro (T4). Quem rouba o ISSUER de um emitente legítimo não tem
a chave para assinar (T4).

## Contraprova independente (T1)

Ed25519 é determinístico: com o mesmo par (chave, payload), as duas
bibliotecas — cryptography e PyNaCl, implementações independentes —
produzem EXATAMENTE a mesma assinatura, e cada uma verifica a
assinatura da outra (4/4). A mesma filosofia do verificador do
ZEPHIRUM aplicada à cripto: nenhuma fonte única de verdade.

## Uso (CLI)

```bash
zephirum.py trust gen-key --out issuer_key.txt   # gera (sk, pk)
zephirum.py trust allow <pubkey>                 # registro de emitentes
zephirum.py compile prog.zeph                    # certificado
zephirum.py trust sign prog.zeph.cert.json issuer_key.txt
zephirum.py verify prog.zeph.cert.json.signed.json prog.zeph
```

## Compatibilidade

Camada aditiva: certificado NÃO assinado segue verificável como
antes (T5); SIGNATURE sem ISSUER (ou vice-versa) é rejeitado
explicitamente. O `check_hash` ignora ISSUER/SIGNATURE (envelope, não
payload).

## Limitações (declaradas)

1. A assinatura prova ORIGEM, não MÉRITO: confiar na chave do
   emitente é decisão de política (o registro), não de criptografia;
2. Registro é um arquivo local plano (trusted_issuers.txt): sem
   expiração, revogação, hierarquia/web-of-trust (fase futura);
3. A chave privada do emitente vive em arquivo — proteção física do
   sigilo é responsabilidade do operador;
4. Vetores de teste RFC 8032 NÃO foram usados de memória: a prova de
   correção da Ed25519 aqui é a concordância bit-a-bit entre duas
   implementações independentes (T1), coerente com a política de
   evidência A-E (nada inventado).
