# PHASE 5 — RUNTIME: só executa o que sobreviveu

Data: 2026-10-07 · Fase 5, fatia 1. Especificação do pilar em
`ZEPHIRUM_ARCHITECTURE.md`: o Runtime executa SOMENTE o que sobreviveu à
análise de necessidade e despacha para backends. A VM própria é
componente INTERNO deste pilar (Fase 6 — ainda não).

## Contrato do Runtime (nesta ordem, soundness-first)

1. certificado INVÁLIDO => RuntimeRefusal e ZERO unidades executadas
   (o gate é o verificador independente — antes de qualquer execução);
2. decisão certificada sem execução => entrega com ZERO unidades
   (o certificado É a resposta);
3. residual/full => executa APENAS as unidades certificadas, no backend
   declarado, e confere contra o certificado (cross-check);
4. backend diverge do certificado => MISMATCH: entrega RECUSADA — a
   resposta certificada nunca é sobrescrita;
5. UNKNOWN => entregue como Z, zero unidades.

## Recibo

Cada execução emite recibo: resposta, status, backend, unidades
executadas vs certificadas vs originais, unidades eliminadas,
cross-check, CERT_HASH. A contabilidade fecha:
units_executed == units_certified (R1, 20.000 recibos).

## Backends

- `cpu_exact` (Fraction, padrão) e `float64` implementados;
- `gpu`/`hpc`/`qpu` registrados, não implementados: ModelNotAvailable
  explícito (§12 — nunca fingir execução).

## Resultados medidos (test_runtime.py, PASS, R1-R7)

- 20.000 recibos: contabilidade fechada, cross-check OK
- 155.168 unidades originais, 35.292 executadas, **119.876 eliminadas
  (77,26%)** — o número do Runtime
- 11.896/20.000 casos executaram ZERO unidades (resposta direto do
  certificado)
- forja com rehash: rejeitada no gate, zero execução
- armadilha 1e16 com oráculo: cpu_exact entrega; float64 diverge no
  residual e a entrega é RECUSADA (certificado não é sobrescrito)

## Limitações (declaradas)

1. O Runtime re-executa o residual por caminho próprio, mas o backend
   é o mesmo processo; isolamento de processo/sandbox fica para fatia
   futura (o cross-check cobre a divergência conhecida).
2. Sem fila/agendamento/paralelismo: execuções são síncronas e locais.
3. VM própria (bytecode): Fase 6, componente interno — não existe ainda.
4. A autenticação de emitente do certificado (Ed25519) continua pendente;
   o gate cobre integridade e re-derivação, não autenticidade.

## Veredito

PASS — fatia 1 do pilar RUNTIME (gate + execução residual + recibo +
backends honestos). Próximas fatias: isolamento de backend em processo;
assinatura Ed25519 de emitente; VM própria (Fase 6, dentro do Runtime).
