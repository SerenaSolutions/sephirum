# Q-SIM GATEWAY — Desenho do Aplicativo (v1.0, 2026-10-07)

*O primeiro produto da linguagem ZEPHIRUM: decide antes de cobrar.
Prove before you pay.*

## 1. O que é

Um aplicativo web que coloca o portão ZEPHIRUM na frente de SDKs
quânticos (Qiskit, Cirq, PennyLane) e, no futuro, de QPUs reais. O
usuário submete uma pergunta ZEPHIRUM; o portão decide ANALITICAMENTE
com aritmética exata e certificado verificável; o recibo mostra o
veredito, o hash do certificado e as unidades QPU que NÃO foram
cobradas. Só o residual — o que não pode ser provado — é roteado ao
SDK. Hoje a família suportada no portão é EMARANHAMENTO (critério
fechado de Schmidt); a linguagem e o padrão já cobrem as famílias de
soma (Gauss, geométrica infinita e finita, média, limiar, mediana,
determinante triangular).

O protótipo de referência é `prototype/qsim_gateway.py` (CLI, bateria
Q1-Q4 + gateway PASS): 40/40 decisões no portão com ZERO unidades QPU
cobradas, recusa explícita de fora-de-escopo (§12), cross-check do SDK
com SKIP declarado quando ausente — o gateway nunca finge.

## 2. Princípio de produto (§12 como requisito, não como texto)

1. Nenhuma resposta sem certificado verificável pelo caminho
   independente.
2. Nenhuma execução fingida: SDK ausente => "SKIP (§12)" visível.
3. Fora de escopo => NOT ROUTED com motivo e o custo que o caminho do
   SDK teria cobrado — nunca um UNKNOWN silencioso.
4. UNKNOWN (Z) é resposta legítima e registrada.
5. Todo número exibido vem de bateria que corre — nada é promessa.

## 3. Telas (MVP)

1. **Gate (tela principal).** Editor ZEPHIRUM (fonte com blocos
   ASK/CONTRACT/MODEL), botão "Decide at the gate". Resultado: veredito
   0/1/Z, status, cert_hash, input_hash, independent_check OK.
2. **Recibo.** Unidades QPU cobradas (0 quando eliminado), caminho do
   SDK eliminado (statevector + eigendecomposition, N unidades
   salvas), residual roteado (ou "none — the certificate is the
   answer"), cross-check do SDK (valor float como ruído ao redor do
   exato; o certificado é o veredito estável).
3. **Histórico.** Cada submissão vira registro rastreável: fonte,
   veredito, hashes, data, unidades salvas. Auditoria completa.
4. **Verificar.** Colar um certificado + a fonte => o verificador
   independente re-deriva tudo e diz PASS/FAIL — a prova pública de
   que o app não é uma caixa-preta.

## 4. Arquitetura

```
[Frontend]  editor ZEPHIRUM + recibo visual
     │  HTTP/JSON
[API Gateway Service]   wrappers de qsim_gateway.gateway()
     │                      + verify_certificate.verify()
     ├─ [ZCA engine]  nexa_core.NCA (decisão, certificado)
     ├─ [Verificador independente]  verify_certificate (re-derivação)
     ├─ [Adaptadores SDK]  qiskit | cirq | pennylane (opcionais,
     │                      cross-check; ausentes => SKIP §12)
     └─ [Registro]  Question / Receipt / Certificate (entidades)
```

API (esboço normativo):

- `POST /ask` — corpo: fonte ZEPHIRUM + sdk opcional → recibo JSON
  (campos exatos do `gateway()` do protótipo: routed, status, verdict,
  cert_hash, input_hash, independent_check, qpu_units_billed,
  sdk_path_eliminated, residual_to_sdk, sdk_cross_check).
- `POST /verify` — corpo: fonte + certificado → PASS/FAIL + motivo.
- `GET /receipt/{cert_hash}` — recibo arquivado.
- `GET /stats` — agregado honesto: decisões no portão, unidades
  salvas, taxa de NOT ROUTED, taxa de UNKNOWN (Z é exibido, não
  escondido).

## 5. Modelo de dados (entidades)

| Entidade | campos |
|---|---|
| Question | fonte, família, data, dono |
| Receipt | question_id, routed, status, verdict, cert_hash, input_hash, qpu_units_billed, units_saved |
| Certificate | cert_hash, input_hash, rung, evidence_json, verify_ok |

Versionamento dos certificados: imutáveis; nova decisão = novo
registro (nunca sobrescrever).

## 6. Roadmap do app

1. **MVP (esta versão do desenho):** família emaranhamento no portão +
   verificação pública + histórico. Motor: o protótipo Python
   empacotado como serviço.
2. **Fatia 2:** famílias de soma no portão (a linguagem já decide);
   verificador C (zverify) como segunda opinião em produção — o mesmo
   certificado auditado por duas linguagens.
3. **Fatia 3:** transpilador multi-alvo gerando o verificador do
   certificado na linguagem do usuário (Python/C/Java/C# — 90/90
   idênticos).
4. **Fatia 4:** contabilidade real de economia (US$/QPU-hora evitada,
   medido com tabela pública de preço por provedor).
5. **Fatia 5:** QPU real no residual (quando houver hardware): o
   orçamento do certificado vira limite de cobrança.

## 7. O que o app NÃO é (§12)

Não é um simulador quântico; não promete vantagem quântica; não
executa circuitos por execução própria; não esconde UNKNOWN; não
cobrança de unidades QPU sem recibo. O SDK é sempre o executor — o
portão só decide e certifica.

## 8. Construção

O desenho está pronto para virar aplicativo no Base44 (entidades +
backend functions + páginas) no comando do dono. O custo de créditos
da construção fica a critério dele — por isto este documento entra
primeiro no repositório: o desenho é a evidência antes da velocidade.


## PLUG-IN QUÂNTICO INSTALÁVEL (2026-10-07, direção do dono)

O algoritmo saiu do repositório e virou PRODUTO: `plugin/` contém o
pacote pip `zephirum-quantum-plugin` (v0.3.0) — o algoritmo Zephirum
de emaranhamento *self-contained*, nascido do primeiro artefato da
casa (o verificador autônomo transpilado em Python/C/Java).

O que o plug-in faz:
  - decide emaranhamento de 2 qubits puros com Fraction exata
    (critério de Schmidt; Wootters PRL 1998 / N&C cap. 2);
  - emite certificado verificável (INPUT_HASH + selo CERT_HASH
    SHA-256) e verificação independente que REFAZ a decisão;
  - cobra ZERO unidades QPU (o caminho SDK de 8 unidades é
    eliminado pelo critério fechado);
  - Qiskit/Cirq como gêmeos adversariais OPCIONAIS de contraprova
    float — o SDK é ruído em volta do exato, nunca o veredito;
  - recusa honesta (§12): família fora, SDK ausente -> SKIP com
    motivo, nunca erro escondido;
  - CLI `zephirum-q` (console script) + API Python `gateway()`.

Bateria `test_plugin_quantum.py` (17ª da conformidade, PASS):
7/7 vereditos == teoria; adulteração de ENTRADA pega na concorrência
exata e de RESPOSTA pega na verificação (duas camadas); CLI
end-to-end com contraprova Qiskit real.

Instalação: `pip install plugin/` · extras: `[qiskit]`, `[cirq]`.

## v0.4.0 — O PLUG-IN É ZEPHIRUM (direção do dono, 2026-10-07)

O dono corrigiu a rota: o algoritmo do plug-in NÃO é Python — é
ZEPHIRUM. O pacote `zephirum-quantum-plugin` v0.4.0 compila a
pergunta e o estado para BYTECODE da linguagem (módulo
`zephirum_plugin_lang.py`, 18ª bateria) e a decisão é executada pela
VM; o Python no pacote é só emissor/interpretador (o papel de
javac/JVM), e executando o mesmo programa no zvm C NÃO HÁ PYTHON no
runtime.

Em linguagem, agora: parse das 4 amplitudes COM SINAL ('-' unário,
máscara 1-2·SIGN), determinante de Schmidt, norma, |det| por máscara
de sinal, concorrência exata por MULTIPLICAÇÃO CRUZADA
(4·det²·q² ~ p²·n² — a comparação nunca divide), comparação por
diferença vs literal 0, guarda de div/0 por máscara ==0, estados
inválidos por FLAG (4 amplitudes, n>0), nunca crash.

Muro §12 verificado na prática: estados de 17 dígitos (Bell com
decimais longos) excedem o muro C de 10^12 e o zvm FALHA com recibo
declarado — a VM Python decide exata; dentro do muro, tripla
concordância VM == zvm == referência (16/16 estados).

A verificação do certificado usa a referência Fraction direta
(implementação INDEPENDENTE) — duas camadas: bytecode (decisão) e
referência (contraprova).

## MODO STANDBY (direção do dono, 2026-10-07)

"Vou dificultar um pouquinho": o plug-in agora é o SOFTWARE QUÂNTICO
QUE O MUNDO INSTALA HOJE — smartphones (Termux/Pydroid/iOS a-Shell),
computadores e sistemas operacionais clássicos — e AGUARDA a
computação quântica.

  - serviço ATIVO hoje: decisão clássica EXATA em bytecode Zephirum
    (runtime stdlib puro — bateria SB2 prova que não importa
    numpy/qiskit/cirq no processo: apto a qualquer aparelho);
  - probe honesto (§12): QPU_REAL=False, STATUS=AGUARDANDO, SDKs
    declarados SIMULADORES, nunca encenação (bateria SB1);
  - standby é ESTADO, não degradação: mesmo veredito e MESMO
    CERT_HASH do caminho normal (SB3);
  - QPU-ready: quando o hardware existir no aparelho, o MESMO
    caminho de certificado (INPUT_HASH/CERT_HASH) roteia — só o
    probe muda (SB4).

CLI: `zephirum-q <arquivo> --standby` · `zephirum-q --qpu-probe`.
Bateria: `test_standby.py` (19ª da conformidade).
