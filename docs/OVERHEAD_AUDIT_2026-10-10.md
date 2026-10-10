# AUDITORIA DE OVERHEAD HIBRIDO — BOREAS + ZYQL (2026-10-10)

## Objetivo
Medir o custo ponta a ponta da fronteira classico-quantico do BOREAS no
laboratorio IBM real e auditar quanto o portao exato do algoritmo ZYQL evita
de cruzar essa fronteira. [FATO: objetivo definido pelo dono em 2026-10-10]

Origem da pergunta: post QuBits - Quantum & AI (LinkedIn), Topico 01
"The Hybrid Stack": "meca o sistema completo, nao a QPU isolada".
## Método
Carimbos de tempo do proprio IBM (job.metrics()), sem estimativas.
Ferramenta: drivers/overhead_audit.py (permanente, reexecutavel).

## Resultados
### 1. Overhead ponta a ponta no laboratorio (ibm_kingston) [FATO]
| job | programa | veredito | fila (s) | exec parede (s) | total (s) | QPU cobrada (s) | QPU/total |
|-----|----------|----------|----------|-----------------|-----------|-----------------|-----------|
| 1 | bell_phi_plus | HANDSHAKE_OK | 4455.2 | 78.3 | 4533.5 | 2 | 0,044% |
| 8 | ghz3_phi000_111 | HANDSHAKE_OK | 286.5 | 104.0 | 390.4 | 2 | 0,512% |
| 9 | cluster3_qcnn | HANDSHAKE_FAILED | 46.2 | 141.9 | 188.1 | 3 | 1,595% |

Leitura: a QPU fica ativa entre 0,04% e 1,6% do tempo total. O custo dominante
e a fila. Isso e a restricao do post medida em silicio real.
Ressalva [FATO]: n=3 jobs, um backend; os tempos de fila dependem da carga
do laboratorio no momento e nao generalizam.

### 2. Orcamento do plano aberto [FATO, fonte: svc.usage()]
Consumido 234 s de 600 s; restam 366 s. Janela do periodo: ate 2026-10-10 03:22Z.

### 3. Portao exato offline: o que NAO cruzou a fronteira [FATO]
Corpus de 11 programas: 10 decididos sem execucao (veredito exato com
certificado), 3,1 ms de tempo offline somados. 1 fora do compilador de
emaranhamento (familia geometric_inf, tratada pelo transpilador multi-alvo).
Comparacao [INFERENCIA]: as decisoes offline custaram milissegundos; os 3
jobs de hardware custaram 5.112 s de relogio. O portao so e comparavel como
ORDEM DE GRANDEZA: ele responde a pergunta de decisao, nao substitui a
medicao fisica, que serve para validar o dispositivo.

## Validação
### 4. Mapa das 5 camadas do infografico no ZEPHIRUM/BOREAS [INFERENCIA]
1. Data Input      -> fonte .zeph (ASK/CONTRACT/MODEL)
2. Classical       -> nexa_core: decisao exata offline + certificado
3. AI/ML           -> camadas SLM/LLM/RAG/MCP do kernel (authority.json)
4. QPU             -> adaptador Qiskit: apenas o subproblema nao decidivel
5. Post-processing -> HARNESS: veredito do recibo, recusa se limiar falha
Diferencial: portao exato ANTES da camada 4, e HARNESS DEPOIS dela.

## Limitações
### 5. Limites declarados [FATO]
Nao ha benchmark de vantagem quantica aqui. Os jobs sao validacao de
dispositivo (Bell/GHZ/cluster), nao carga de trabalho com ganho. O Job 9
foi recusado pelo HARNESS (S0=0,586 < 0,60) e permanece como falha registrada.

## Autoridade humana
Decisoes sobre uso do orcamento restante (366 s) e publicacao no arXiv
pertencem ao dono (CEO). HIPOTESE aberta: se a fila domina em todos os
horarios, a fronteira so compensa para cargas em lote.
