# PHASE 3 — COMPILER CORE: decisão, certificado, verificação independente

Data: 2026-10-07 · Repositório: SerenaSolutions/zephirum · Documento técnico.

## 1. Contexto e baseline (auditoria, §1 do prompt)

Auditoria completa da árvore ANTES de qualquer modificação. Bateria
existente, resultado baseline (todos exit 0): `run_tests.py`,
`test_zephirum_lang.py`, `test_zephirum_ir.py`, `falsification_200.py`,
`stress_test.py 500000`, `ai_layer.py` — 6/6 verdes. Nenhum teste
existente foi alterado para passar; correções, quando houve, foram na
implementação.

Renomeação aplicada antes da implementação, por decisão do chefe
(2026-10-07): ZERUM→ZEPHIRUM, SIFR→ZEPHIRUM, SCA→ZCA, SIWAHID deprecado.
Etimologia oficial: latim *zephirum* (Fibonacci, *Liber Abaci*, 1202).
Baseline re-verificada pós-rename: 6/6 verdes, zero mudança de
comportamento.

## 2. Pipeline implementado

    ZEPHIRUM (linguagem / formato de blocos)
      ↓  parse_zephirum | parse_nexa  (IR idêntica, testada em 50k casos)
    IR normalizada
      ↓  NCA (escada de eliminação, ledger degrau a degrau)
    decisão trivalente 0/1/Z
      ↓  Decision Kernel de primeira classe + certificado
    CERT_HASH (SHA-256 canônico)
      ↓  verify_certificate.py (verificador INDEPENDENTE)
    resultado final

## 3. IR determinística (§2 do prompt)

A IR de bloco é dicionário ordenável (parse determinístico). O
certificado tem serialização canônica (`decision_kernel.canonical`:
JSON com chaves ordenadas e separadores compactos). Mesma entrada →
mesma IR → mesmo certificado → mesmo CERT_HASH (§13: verificado com 3
execuções por representante, hashes idênticos; sensibilidade: um dígito
alterado muda o hash). O `zephirum_ir.py` (Fase 2) permanece o IR
transversal do SIFR-IR→ZEPHIRUM-IR, validado em 5.000 casos.

## 4. Escada de eliminação (§3)

Cada degrau registra tentativa no ledger: `[RUNG] OUTCOME — detalhe`.
Degraus ativos no motor: SIMPLIFICATION (constant folding), REDUCTION
(parada monotônica), LIMIT (limites intervalares), ANALYTIC (formas
fechadas: determinante triangular, série geométrica, critério de
Schmidt/emaranhado), CLASSICAL (execução plena justificada), RESIDUAL
(resíduo executado com justificativa). Mapeamento conceitual para os
STEP 0-7 do prompt: NORMALIZATION≡parse, CONSTANT FOLDING≡SIMPLIFICATION,
ALGEBRAIC REDUCTION≡REDUCTION, BOUND ANALYSIS/INTERVAL SEPARATION≡LIMIT,
DECISION≡kernel, RESIDUAL COMPUTATION≡RESIDUAL, UNKNOWN≡Z.

Categorias (§7) nunca misturadas: DECIDED_WITHOUT_EXECUTION,
DECIDED_BY_REDUCTION, RESIDUAL_COMPUTATION_REQUIRED,
FULL_EXECUTION_REQUIRED, UNKNOWN. UNKNOWN ≠ TRUE, UNKNOWN ≠ FALSE.

## 5. Decision Kernel de primeira classe

`DECISION_KERNEL = {id, name, question, verdict, verdict_reading, rung,
method, justification, scope, residual_units}`. Id determinístico
K-<sha256(name, question, rung, method, answer)[:16]>. Veredito
trivalente 0/1/Z (módulo zephirum.py, STATUS_TO_TRIT).

## 6. Certificado e CERT_HASH (§4/§14 do prompt)

CERT_HASH = SHA-256 do certificado canônico completo (evidência, rastro,
custos, status, resposta, kernel), sem o próprio hash. O hash serve
APENAS para integridade/identidade do artefato — nunca como prova
matemática (§14). Qualquer adulteração sem rehash quebra o hash e o
certificado é rejeitado antes de qualquer análise.

## 7. Princípio de não-confiança (§5) — verificador independente

`verify_certificate.py` NUNCA aceita `answer=true` porque o compilador
declarou. Ele:
1. confere INPUT_HASH (fonte) e CERT_HASH (integridade);
2. confere QUESTION e MODEL_TYPE contra a FONTE;
3. aplica schema ESTRITO de evidência por kernel (whitelist — campo
   fora do vocabulário do kernel: REJECT);
4. confere coerência do campo de execução com o status declarado
   (decidir sem execução exige required_terms=0; residual exige 1; full
   exige ≥1);
5. confere veredito/método/residual do kernel de primeira classe;
6. RE-DERIVA a decisão da fonte por método independente, por kernel:
   - MONOTONE_EARLY_STOP: testemunha é prefixo real, soma reconferida,
     monotonicidade preservada;
   - INTERVAL_BOUND: limites recomputados da fonte;
   - TRIANGULAR_DET_ANALYTIC: triangularidade reverificada + produto;
   - GEOMETRIC_CLOSED_FORM: soma ingênua contra forma fechada;
   - SCHMIDT_DET_CRITERION: rota cruzada det(M·Mᵗ) = det(M)² +
     amplitudes conferidas contra a fonte;
   - residuais: justificativa (limites atravessam o limiar) obrigatória;
7. certificado malformado: REJECT explícito, nunca crash (§12).

## 8. Erros estruturais (§12) — falha explícita, nunca UNKNOWN silencioso

ValueError explícito para: modelo desconhecido, intervalo invertido
(hi < lo), valores inf/nan, valores não numéricos, expressão não
dobrável, estado-zero (família emaranhado), estado com ≠ 4 amplitudes,
pergunta não-parseável. O UNKNOWN permanece EXCLUSIVAMENTE para
"informação insuficiente sob garantias" — nunca para erro estrutural.

## 9. Família EMARANHADO (direção do chefe, 2026-10-07)

Perguntas SOBRE emaranhamento de 2 qubits puros, decididas sem simular
o vetor de estado: critério fechado de Schmidt. det(M)=0 ⇔ produto;
concurrence C = 2|det|/⟨ψ|ψ⟩; decisão exata por Fraction com o quadrado
eliminando a raiz (C ~ t ⟺ 4det² ~ t²n²). Emaranhado é a FAMÍLIA do
problema; o mecanismo decisório é clássico e exato — a regra da Fase 3
(sem quantum como mecanismo decisório) está preservada.
A própria bateria achou um furo na primeira versão do verificador
(amplitudes declaradas não conferidas contra a fonte) — fechado antes
da publicação. Verdade-terreno independente: autovalores de ρ_A por via
float (aritmética diferente da exata).

## 10. CLI (§15/§16)

`zephirum check|compile|verify|explain|benchmark` (prototype/zephirum.py).
`check` imprime RESULT/STATUS/CERTIFICATE/EXECUTION; `explain` mostra
pergunta, modelo, escada, decisão, execução, certificado; `verify`
faz verificação completa quando recebe a fonte (recomendado) e
verificação limitada (hash+estrutura) sem ela, com aviso explícito.

## 11. Baterias e resultados (§6/§8/§10/§11/§13/§17/§18)

| bateria | resultado |
|---|---|
| run_tests.py (regressão + soundness local) | PASS |
| test_adversarial_certificates.py (§6) | PASS: RAW 107/107 rejeitados; REHASH 83/83 obrigatórios rejeitados; determinismo 3× OK; sensibilidade do hash OK |
| test_properties.py (§11/§12) | PASS: 987 casos de propriedade + 10 de robustez |
| test_equivalence.py (§10) | PASS: 10.000 casos, tripla motor/certificado+verificador/transpilado |
| falsification_200.py (charter) | PASS: 0 certificados falsos (200 adversariais, 4 famílias) |
| test_entanglement.py | PASS: 35 casos, forja REHASH rejeitada 3/3 |
| test_zephirum_lang.py | PASS (50k equivalência de parsers + 20k fuzz + 500 transpilados) |
| test_zephirum_ir.py | PASS |
| ai_layer.py (consultiva, nunca decisória) | PASS |
| stress_test.py 500000 (§17) | PASS: 0 erradas, 0 certificados falsos, 20/20 forjados rejeitados, certificate_valid_rate 1.0, eliminação 76,51%, 500k em ~32s |

Métricas §8: total_problems=N; counts por categoria (distribuição);
elimination_rate = (original−required)/original explicitamente;
false_elimination_rate = wrong/N; certificate_valid_rate = certs_ok/N;
unknown_rate; total/mean time.

## 12. Limitações (declaradas, sem esconder)

1. ELIMINATION_TRACE é INFORMATIVO: adulteração com hash recalculado
   passa (não é evidência da decisão; o RAW é sempre rejeitado).
2. CERT_HASH cobre integridade, NÃO autenticidade: assinatura de
   emitente (ex. Ed25519) ainda não implementada.
3. Atacante que adiciona campo e recalcula o hash só é detectado se o
   campo viola o schema por kernel (estrito) — não há assinatura de
   terceiros sobre o schema.
4. O transpilador suporta as famílias canônicas; `entanglement` ainda
   não é transpilável (NotImplementedError explícito — §12 respeitado).
5. Limiar float é interpretado como decimal exato do token
   (Fraction(str)) — determinístico e documentado.
6. As famílias suportadas são formais e fechadas. Isto NÃO generaliza.

## 13. Formulação científica (§20 — obrigatória)

"ZEPHIRUM implementa uma infraestrutura verificável para provar, em
famílias de problemas formalmente suportadas, quando uma resposta pode
ser determinada sem executar a computação completa, e para declarar
UNKNOWN quando essa prova não está disponível."

NÃO declara: resolver computação em geral; decidir necessidade
matemática em todos os problemas; provar máquina específica
desnecessária; resolver indecidibilidade; substituir compiladores
tradicionais; substituir hardware especializado.

## 14. Veredito (§19)

- [x] todos os testes anteriores verdes
- [x] IR determinística (hash idêntico em execuções repetidas)
- [x] escada de eliminação registrada (ledger por degrau)
- [x] certificado produzido (kernel de primeira classe + CERT_HASH)
- [x] certificado verificado independentemente (re-derivação da fonte)
- [x] certificados adulterados rejeitados (RAW 100%; REHASH 100% das
      classes obrigatórias; exceção documentada: rastro informativo)
- [x] UNKNOWN permanece UNKNOWN (propriedades P3; categorias separadas)
- [x] transpiler preserva a decisão (Fraction exata; 500 + 10.000 casos)
- [x] kernel, transpiler e verifier concordam (tripla 10.000/10.000)
- [x] 10.000 testes de equivalência passam
- [x] property tests passam (987 + 10)
- [x] benchmark 500.000 continua passando (0 erradas, 76,51%)
- [x] nenhuma regressão (bateria completa verde)
- [x] documentação atualizada (este documento + README)

**FINAL VERDICT: PASS** — com as limitações dos itens 1-6 declaradas.
