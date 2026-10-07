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

## Limitações (declaradas)

1. Interop limitada à família EMARANHADO (as perguntas quânticas
   suportadas pelo degrau ANALYTIC);
2. O SDK roda NUMÉRICA clássica (statevector) — não é QPU real;
3. Adaptadores Cirq/PennyLane registrados, não instalados no sandbox:
   ModelNotAvailable explícito (§12);
4. Resultados medidos no Qiskit 2.5.2 — a instabilidade da rota da
   pureza é comportamento observado desta versão.
