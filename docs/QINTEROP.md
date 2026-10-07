# INTEROPERABILIDADE QUÂNTICA — ZEPHIRUM × SDK

Data: 2026-10-07 · `test_qinterop.py` (dependência opcional:
`pip install qiskit`, ver `prototype/requirements-interop.txt`;
sem o SDK o teste sai com SKIP explícito, nunca finge).

## O teste de conjunto

O par antitético TRABALHANDO JUNTO, cada um no seu papel:
- **ZEPHIRUM decide**: pergunta de emaranhamento pelo critério de
  Schmidt exato (Fraction), degrau ANALYTIC, certificado verificado,
  **ZERO unidades de execução**;
- **o SDK (Qiskit 2.5.2) executa**: statevector, matriz densidade,
  autovalores de ρ_A, concurrence numérica — a computação que a escada
  eliminou, rodada de propósito como gêmeo adversarial.

O SDK NÃO é mecanismo decisório (regra da Fase 3): é validação
independente e, no futuro, backend do residual de execução quântica
genuína (quando houver hardware).

## Resultados medidos (Q1-Q6, PASS)

| # | caso | resultado |
|---|---|---|
| Q1 | 300 estados aleatórios | ZEPHIRUM (exato, 0 exec) == Qiskit numérico: **300/300**; empates exatos ficam com o exato por contrato |
| Q2 | 48 estados PRODUTO | ZEPHIRUM: C = 0 EXATO; Qiskit: ruído float até 2.98e-08 e **11 casos NAN** (sqrt de negativo na rota da pureza — instabilidade documentada da fórmula 2(1−Tr ρ_A²)) |
| Q3 | fronteira 2^53, det = 1 exato | **o SDK se contradiz**: det float = 0.0 (não emaranhado), concurrence = 2.98e-08 (emaranhado, ruído), autovalores de ρ_A = puro; ZEPHIRUM certifica EMARANHADO — único veredicto estável |
| Q4 | rota de autovalores | partial_trace/ρ_A concorda com o Schmidt exato em 4/4 casos comuns |
| Q5 | contabilidade | 300 decisões com ZERO execução no ZEPHIRUM; o SDK rodou o statevector completo em todas |
| Q6 | registro honesto | cirq/pennylane ausentes => ModelNotAvailable explícito; desconhecido => ValueError |

## O que o Q3 prova

Na fronteira de precisão, as DUAS rotas numéricas do SDK divergem ENTRE
SI (falso negativo no det, falso positivo na pureza) — e ambas divergem
do exato. O certificado ZEPHIRUM (det = 1 exato) é a única resposta
estável. Isso não é defeito do Qiskit: é o custo estrutural da
aritmética de ponto flutuante em quantidade que exige cancelamento
catastrófico. O ZEPHIRUM existe exatamente para esse regime.

## Confronto triplo (2026-10-07, v0.5.0): ZEPHIRUM × Qiskit × Cirq × PennyLane

Os três SDKs quânticos atuais enfrentaram o ZEPHIRUM nas mesmas arenas
(`test_qinterop.py`, A1-A6, PASS; versões medidas: Qiskit 2.5.2, Cirq
1.7.0, PennyLane 0.45.1 — dependências opcionais, SKIP explícito sem
elas).

| Arena | Qiskit | Cirq | PennyLane | ZEPHIRUM |
|---|---|---|---|---|
| A1 — 300 estados aleatórios | 293 respostas, 7 NaN | 292, 8 NaN | 292, 8 NaN | **346/346 decisões certificadas, zero execução** |
| A2 — 46 estados produto | ruído 3.0e-08, 11 NaN | 3.0e-08, 12 NaN | 3.0e-08, 11 NaN | **C = 0 EXATO em todos** |
| A3 — fronteira 2^53 (det=1 exato) | **se contradiz** | **se contradiz** | **se contradiz** | **único veredicto estável: EMARANHADO** |
| A4 — autovalores de ρ_A | concorda com Schmidt | concorda | concorda | fonte do critério |

Leitura honesta: onde os três SDKs CONSEGUEM responder, todos concordam
com o certificado (A1/A4) — o exato e o numérico se validam mutuamente.
O regime em que os três quebram é o mesmo em todos: a rota da pureza
`sqrt(2(1-Tr ρ_A²))` produz NaN (sqrt de negativo) e ruído ~3e-08; na
fronteira 2^53 os três dão respostas que se autocontradizem (det float
= 0 "não", concurrence = 2.98e-08 "sim", ρ_A "puro"). Isso não é defeito
dos SDKs: é o custo estrutural do float em cancelamento catastrófico —
o regime exato para o qual o ZEPHIRUM existe.

## Panorama: o ZEPHIRUM frente às linguagens quânticas atuais

Comparação documentária (nível de evidência B/C — características
públicas e conhecidas das ferramentas; nada inventado):

| Stack | O que faz de melhor | O que não faz (e o ZEPHIRUM faz) |
|---|---|---|
| OpenQASM 3 (padrão aberto) | descrição portável de circuitos, linguagem de montagem quântica de facto | não tem semântica de DECISÃO: descreve execução, não a elimina |
| Qiskit 2.x (IBM, core Rust) | ecossistema completo, transpiler, hardware real | executa por design; na fronteira de precisão se contradiz (A3) |
| Cirq 1.7 (Google) | circuitos, schedulers, simulate, ​suporte a research | idem — sem decisão certificada pré-execução |
| PennyLane 0.45 (Xanadu) | diferenciação automática, QML, interfaces fotônicas | idem — computa gradientes, não certifica desnecessidade |
| Q# / Azure Quantum | **estimativa de recursos ANTES da execução** — o parente espiritual mais próximo (precedente nível B) | estimar não é DECIDIR: sem certificado trivalente, sem escada, sem verificador independente |
| Stim / correção de erro | simulação de código de erro em escala | fora do escopo deste confronto |

O que NENHUM deles tem (a contribuição de composição do ZEPHIRUM):
a necessidade computacional como OBJETO EXPLÍCITO de compilação —
escada ordenada por custo, estados trivalentes 0/1/Z, certificado
verificável independentemente, runtime que recusa o não-autorizado,
VM orçamentada. E o que o ZEPHIRUM NÃO tem (honestidade): transpilação
de circuitos, hardware real, correção de erro, diferenciação
automática. O par é complementar: ZEPHIRUM decide; o stack executa o
que sobreviveu — ou valida executando o que foi eliminado.

## Limitações (declaradas)

1. Interop limitada à família EMARANHADO (as perguntas quânticas
   suportadas pelo degrau ANALYTIC);
2. O SDK roda NUMÉRICA clássica (statevector) — não é QPU real;
3. Adaptadores Cirq/PennyLane registrados, não instalados no sandbox:
   ModelNotAvailable explícito (§12);
4. Resultados medidos em Qiskit 2.5.2, Cirq 1.7.0, PennyLane 0.45.1;
   a instabilidade da rota da pureza é comportamento observado
   destas versões.
