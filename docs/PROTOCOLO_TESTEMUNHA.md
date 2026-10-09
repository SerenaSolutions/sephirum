# PROTOCOLO TESTEMUNHA — 100 perguntas, 0 segundos de QPU

A *prova viva* do ZEPHIRUM nos laboratórios da IBM: uma bateria de
100 perguntas de emaranhamento respondidas por certificado, offline,
com 0 unidades de QPU — e a máquina real convidada, em seguida, a
discordar de cada resposta.

Complementa (não substitui) os recibos de hardware já publicados
(Bell/GHZ-3/GHZ-4/QCNN/GHZ-20 no ledger do repositório).

## A bateria (concluída — Tier A, sandbox)

- `prototype/witness_battery.py` — 100 estados de 2 qubits,
  semente fixa 20261009 (reproduzível), distribuição:
  25 produto puro · 25 emaranhado Schmidt · 25 geral ·
  25 armadilhas de fronteira (produto exato, quase-separável ±1/256,
  termo 1/256, emaranhado máximo, fase negativa).
- Verdade-terreno INDEPENDENTE: posto de Schmidt via determinante
  exato `ad − bc` sobre os decimais *como escritos no arquivo*
  (método ≠ caminho do motor).
- Resultado (2026-10-09): **100/100 certificado == verdade exata**,
  70 emaranhados · 30 produto, **0 unidades de QPU faturadas** para
  responder as 100.
- Manifest público por pergunta: `prototype/witness_battery/manifest.json`.
- Achado forense da própria bateria (q085): um caso quase-separável
  cujo decimal exato é não-terminante (7/13); a serialização truncada
  tornava o estado *genuinamente* levemente emaranhado — o motor
  acertou a pergunta que recebeu; o erro era do gerador de casos.
  Corrigido: armadilhas só com decimais terminantes e verdade lida
  do estado como escrito. A bateria caça erros de qualquer lado —
  inclusive os dela mesma.

## O confronto (Tier B — laboratórios da IBM, pendente de execução)

Para cada pergunta selecionada da bateria:

1. O certificado já respondeu offline (veredito 0/1 + concurrence
   exata, hash público no manifest).
2. A máquina real prepara o estado (qiskit `initialize`) e mede as
   testemunhas correlacionais (⟨XX⟩, ⟨ZZ⟩; produto → nenhuma
   correlação em nenhuma base; emaranhado → correlação com sinal e
   magnitude coerentes com o certificado).
3. A pergunta da máquina não é "qual o veredito?" — é
   "o certificado errou?". Discorda dentro do intervalo de confiança
   → falsificação registrada com destaque. Concorda → recibo.
4. Ledger público: job IDs, uso antes/depois, incidentes, nunca
   apagados (política inalterada).

### Escala e honestidade de cota (§12)
- Plano Open (gratuito) tem cota pequena de QPU; a bateria é
  dimensionada pra caber: Tier B propõe as **10 mais duras** —
  as armadilhas de fronteira + emaranhado máximo + produto negativo
  (controles) — dentro da cota mensal gratuita.
- Todas as 100 permanecem respondidas por certificado; a máquina
  valida só a amostra adversarial. Isso é declarado no recibo, não
  escondido.
- O que isto NÃO prova: não é claim de speedup de hardware; o
  hardware é EVIDÊNCIA, não fonte de certificado; decoerência é
  reportada, não suavizada (§12).

### Papéis
- Titular (AUŠRA): orientação da seleção das 10, conta IBM, go.
- Agente: protocolo, harness, manifest, ledger, publicação (DOI).
- IBM: execução física (a única parte que não roda offline).

### Entregável
Tabela pública: pergunta · veredito do certificado · concurrence
exata · medidas do QPU com IC95 · job ID · segundos de QPU gastos
pelo certificado (zero) · segundos gastos pela testemunha.
Headline honesta: *"100 respostas custaram 0 segundos de QPU; à
máquina foi dada apenas a chance de discordar."*
