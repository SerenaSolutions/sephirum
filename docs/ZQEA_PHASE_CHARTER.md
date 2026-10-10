# Z-QEA Phase Charter — adopted 2026-10-08

**Source:** owner-supplied external audit + master prompt (second
external audit, deliberately hunting for prior art that could kill
the hypothesis). Adopted as the binding charter for the next phase.

**Key verdicts of the external audit (accepted):**
- Hardware-layer prior art is REAL and must not be re-claimed:
  IBM already monitors drift/calibration and can pause queues; Cirq
  offers calibration-based qubit selection; tket does placement and
  routing; calibration-aware compilers and T2/fidelity-aware routing
  papers exist; runtime calibration checking exists.
- Therefore: do NOT "invent qubit stabilization" or "invent
  calibration-based routing". The defensible move is one
  EPISTEMIC LEVEL UP: turn hardware state, constraints, error budget,
  connectivity and execution decisions into verifiable, auditable
  evidence, integrated with the necessity mechanism — without
  pretending to physically fix qubits.
- "QSim Gateway" collides with India's QSim toolkit
  (MeitY/IISc/IIT Roorkee/C-DAC) => WORKING NAME ONLY. A new name
  must be chosen after collision research (paused: external searches
  suspended by owner order to conserve credits).

**Master prompt (verbatim) follows.**

---

Você é o arquiteto-chefe, pesquisador de anterioridade e engenheiro de
sistemas do projeto ZEPHIRUM.

REPOSITÓRIO BASE:
https://github.com/SerenaSolutions/zephirum

OBJETIVO DESTA FASE:
Evoluir o ZEPHIRUM sem destruir sua identidade original e sem
reivindicar como inovação algo que já exista na literatura, em software
comercial, em patentes, em teses ou em projetos open source.

O ZEPHIRUM atualmente é uma linguagem/compilador orientado à
necessidade de computação:

ASK FIRST. PROVE NEXT. COMPUTE LAST.

Seu núcleo possui:

- linguagem ZEPHIRUM;
- ZCA — Zephirum Compilation Algorithm;
- elimination ladder;
- lógica trivalente 0/1/Z;
- Decision Kernel;
- certificados verificáveis;
- SHA-256/CERT_HASH;
- verificador independente;
- princípio de no-trust;
- transpiração/multi-target;
- execução apenas do residual;
- tratamento explícito de UNKNOWN;
- família quântica inicial baseada em decisões exatas, sem
  necessariamente simular o estado quântico.

A nova fase NÃO deve transformar ZEPHIRUM em um clone de Qiskit,
Cirq, PennyLane, tket, CUDA-Q ou outro SDK.

==================================================
1. REGRA ABSOLUTA DE ANTERIORIDADE
==================================================

Antes de implementar qualquer nova funcionalidade, execute uma
auditoria externa exaustiva. Pesquisar obrigatoriamente: arXiv;
Google Scholar; IEEE; ACM; Springer; Nature; Physical Review; GitHub;
GitLab; patentes; teses; IBM Quantum; Google Quantum AI; Microsoft
Quantum; Quantinuum; IonQ; Rigetti; AWS Braket; NVIDIA CUDA-Q;
PennyLane; Cirq; pytket; Qiskit; MQT; universidades e laboratórios.
Priorizar 2024-2026, mas pesquisar trabalhos fundacionais anteriores.
Pesquisar as combinações: noise-aware compilation; calibration-aware
compilation/routing; dynamic qubit routing; adaptive qubit mapping;
T1/T2-aware compilation; coherence-aware routing; fidelity-aware
mapping; qubit selection; qubit health; hardware/calibration drift;
runtime/online calibration; runtime verification; quantum runtime
monitoring; quantum execution validation; error budget;
error-aware compilation; connectivity-aware compilation; dynamic
connectivity; quantum error detection/mitigation/correction;
execution refusal; quantum job admission control; quantum resource
estimation; quantum circuit feasibility; quantum hardware status;
quantum compiler certificates; proof-carrying quantum programs;
verifiable quantum compilation; independently verifiable quantum
execution; quantum hardware attestation.

IMPORTANTE: Não procurar somente evidências favoráveis. Procurar
deliberadamente trabalhos que possam provar que a nova proposta já
existe. Se existir um sistema essencialmente equivalente:
identificar; citar; explicar a sobreposição; abandonar a
reivindicação de novidade; procurar uma diferenciação real.

NUNCA escrever "ninguém fez isso antes" sem evidência suficiente.
Usar linguagem científica: "não foi localizado nesta busca";
"a combinação encontrada apresenta diferenças em X"; "a contribuição
potencial parece estar em Y".

==================================================
2. AUDITORIA ESPECÍFICA DO ZEPHIRUM ATUAL
==================================================

Leia o repositório inteiro antes de alterar arquitetura. Inspecione:
prototype/; plugin/; docs/; examples/; results/; book/. Leia
especialmente: README.md; documentação do ZCA; Decision Kernel; Phase
3; documentação do plugin; QINTEROP; especificações da linguagem;
testes; resultados; certificados; verificador independente.
Não reimplemente funcionalidades existentes. Não criar uma segunda
linguagem paralela. Não criar outro compilador independente. Não
destruir compatibilidade existente.

==================================================
3. NOVA HIPÓTESE ARQUITETURAL
==================================================

Investigar a criação de uma camada chamada provisoriamente
ZEPHIRUM QUANTUM EXECUTION ASSURANCE LAYER (nome interno temporário:
Z-QEA; nome comercial definitivo somente depois de pesquisa de
anterioridade).

O objetivo NÃO é "consertar fisicamente qubits". O objetivo é
responder: "Dado um circuito lógico, um backend específico e o estado
observável desse backend, é possível produzir uma decisão verificável
sobre se a execução proposta satisfaz os critérios de execução
definidos pelo usuário?"

A camada deve trabalhar ACIMA dos mecanismos existentes de
calibração; routing; placement; error mitigation; error correction;
benchmarking. Ela NÃO deve alegar substituir nenhum deles.

==================================================
4. NOVO PRINCÍPIO
==================================================

ASK -> PROVE -> ASSESS -> CERTIFY -> EXECUTE -> VERIFY

ASK: entender a pergunta computacional.
PROVE: tentar eliminar a necessidade de execução.
ASSESS: avaliar se a execução residual é compatível com o estado
observável do backend.
CERTIFY: produzir uma evidência verificável da decisão.
EXECUTE: encaminhar somente o que foi autorizado.
VERIFY: verificar o resultado e registrar as condições sob as quais
ele foi obtido.

==================================================
5. MODELO DE ESTADO DO HARDWARE
==================================================

Criar um modelo formal de "execution state". Representar, quando
disponível: qubits disponíveis; conectividade; fidelidade de portas;
erros de leitura; T1; T2; duração de portas; erro de portas de dois
qubits; crosstalk; leakage; idade da calibração; timestamp da
calibração; disponibilidade do backend; restrições de gate set;
restrições de scheduling; limites de profundidade; orçamento de erro;
número de shots; demais métricas realmente fornecidas pelo backend.

NÃO inventar métricas ausentes. Se uma métrica não estiver
disponível: UNKNOWN. Nunca converter ausência de informação em
segurança presumida.

==================================================
6. GRAFO TEMPORAL DE EXECUÇÃO
==================================================

Investigar uma representação G(t) = (Q, E, W, T) onde Q = qubits
físicos disponíveis; E = conexões fisicamente permitidas; W =
pesos/métricas observadas; T = validade temporal da informação.
Representar uma rota física como: logical circuit -> physical mapping
-> routing -> expected execution window -> hardware state ->
admissibility decision.

A pergunta NÃO deve ser apenas "Existe conectividade?" Deve ser:
"Existe uma realização física conhecida que satisfaz as restrições
declaradas durante a janela de execução estimada?" Se não puder ser
provado: UNKNOWN ou REFUSE. Nunca GUESS.

==================================================
7. NOVO DECISION KERNEL QUÂNTICO
==================================================

Estender o Decision Kernel sem quebrar compatibilidade. Investigar
campos adicionais: backend_id; backend_snapshot;
calibration_timestamp; hardware_state_hash; logical_qubits;
physical_mapping; connectivity_evidence; coherence_evidence;
fidelity_evidence; routing_evidence; error_budget; execution_window;
decision; justification; scope; residual; certificate_hash. Campos
finais definidos após a auditoria. O certificado deverá permitir
reconstruir: "Por que o ZEPHIRUM autorizou ou recusou esta execução?"

==================================================
8. ESTADOS DE DECISÃO
==================================================

Manter a filosofia trivalente 0/1/Z. Investigar estados
complementares internos: ADMISSIBLE; REFUSED; UNKNOWN; STALE;
INVALID. Esses estados NÃO devem substituir automaticamente a
lógica trivalente. Determinar se devem ser estados internos;
metadados; códigos de razão; ou extensões formais.

==================================================
9. EXECUTION REFUSAL
==================================================

O ZEPHIRUM pode recusar uma execução. Exemplos: "EXECUTION REFUSED —
Reason: hardware snapshot stale"; "EXECUTION REFUSED — Reason: no
certified physical mapping satisfies declared error budget";
"UNKNOWN — Reason: backend did not expose sufficient calibration
evidence". A recusa é uma saída VÁLIDA do sistema. Não tentar
"resolver" falta de evidência com heurística silenciosa.

==================================================
10. ADAPTIVE ROUTING
==================================================

Investigar integração com técnicas existentes: SABRE; tket routing;
Cirq routing; Qiskit transpilation; calibration-aware routing;
fidelity-aware mapping; T1/T2-aware mapping; RL routing; dynamic
routing. O ZEPHIRUM não deve reinventar esses algoritmos. Ele deverá
atuar como camada de: seleção; restrição; avaliação; certificação;
recusa. Exemplo conceitual: ROUTE A -> admissible; ROUTE B ->
inadmissible; ROUTE C -> insufficient evidence; então SELECT A com
justificativa verificável.

==================================================
11. RUNTIME WATCHDOG
==================================================

Investigar monitorar mudanças durante a execução, se o backend
permitir: snapshot_0 -> execution -> snapshot_1. Comparar:
calibração; T1; T2; gate error; readout error; conectividade; system
status. Se a condição que sustentava o certificado deixar de ser
válida: INVALIDATE CERTIFICATE e decidir STOP; RECOMPILE; REROUTE;
RETRY; REFUSE; ou UNKNOWN. Não assumir que todo backend suporta
interrupção ou rerouting em runtime. Experimental até haver backend
real que a suporte.

==================================================
12. NÃO PROMETER "ESTABILIZAR QUBITS"
==================================================

É proibido descrever o sistema como: "cura qubits"; "impede
decoerência"; "torna qubits estáveis"; "elimina erros quânticos";
"corrige fisicamente o hardware". A função correta é: "avaliar,
selecionar, certificar e adaptar a execução diante de um estado
físico e operacional variável". A diferença deve aparecer na
documentação, no README, no paper e no código.

==================================================
13. RELAÇÃO COM ERROR MITIGATION E ERROR CORRECTION
==================================================

Não competir artificialmente com: QEC; QED; ZNE; PEC; TREX;
dynamical decoupling; debiasing; readout mitigation. Essas
tecnologias podem ser tratadas como mecanismos que o ZEPHIRUM pode
selecionar; recomendar; incorporar; ou considerar no orçamento.
Investigar se o Decision Kernel pode registrar: MITIGATION REQUIRED;
MITIGATION SELECTED; MITIGATION VERIFIED; MITIGATION INSUFFICIENT —
sem fingir que o ZEPHIRUM implementa todas essas técnicas.

==================================================
14. QSIM GATEWAY — REAVALIAR O NOME
==================================================

"QSim" NÃO deve ser considerado definitivo (colisão: toolkit
quântico indiano MeitY/IISc/IIT Roorkee/C-DAC). QSim Gateway =
WORKING NAME ONLY. Pesquisar colisões de nome antes de criar
identidade comercial. Propor pelo menos 10 nomes alternativos. O
nome deverá representar ZEPHIRUM + quantum execution + verification
+ gateway/assurance.

==================================================
15. INTEROPERABILIDADE
==================================================

Continuar podendo conversar com Qiskit; Cirq; PennyLane; OpenQASM;
outros formatos quando justificável. Interoperabilidade como camada.
O ZEPHIRUM não deve depender conceitualmente de uma única plataforma.
Arquitetura: ZEPHIRUM -> IR -> Execution Assurance -> Backend Adapter
-> Qiskit/Cirq/PennyLane/OpenQASM/outro backend.

==================================================
16. O QUE É REALMENTE NOVO?
==================================================

Depois da auditoria, produzir a matriz FEATURE / EXISTE? / ONDE? /
DATA / OVERLAP / DIFFERENCE / POTENTIAL CONTRIBUTION. Separar:
A. conhecido; B. combinação conhecida; C. combinação com diferença
arquitetural; D. hipótese potencialmente nova; E. ainda não
demonstrada. NÃO chamar C ou D automaticamente de "invenção".

==================================================
17. TESTES EXPERIMENTAIS
==================================================

Suíte experimental reproduzível. Baseline: Qiskit transpilation; Cirq
routing; tket; SABRE; noise-aware mapper; calibration-aware routing —
versus ZEPHIRUM QEA. Medir: circuit depth; número de SWAPs;
fidelidade; erro esperado; execução recusada/aceita; falsos ACCEPT;
falsos REFUSE; UNKNOWN; tempo de decisão; overhead; estabilidade da
decisão; validade do certificado. NUNCA otimizar apenas para "menor
erro". Também medir o custo computacional da própria camada ZEPHIRUM.

==================================================
18. TESTE MAIS IMPORTANTE
==================================================

CASO A: circuito pode ser resolvido sem QPU -> NO EXECUTION.
CASO B: precisa de QPU e existe rota adequada -> CERTIFIED EXECUTION.
CASO C: existe conectividade mas o orçamento de erro não é satisfeito
-> REFUSE.
CASO D: várias rotas, uma admissível -> selecionar com justificativa.
CASO E: calibração obsoleta -> UNKNOWN/STALE.
CASO F: duas fontes em conflito -> não escolher silenciosamente.
CASO G: hardware muda depois da decisão -> detectar invalidação do
certificado, quando o backend permitir observar isso.

==================================================
19. ADVERSARIAL TESTING
==================================================

Tentar quebrar o sistema: certificados falsos; calibrações antigas;
métricas manipuladas; conectividade falsa; erros NaN; valores
impossíveis; hashes alterados; mappings inválidos; backends
inexistentes; dados parcialmente ausentes; estados inconsistentes. O
verificador independente deve rejeitar tudo que não possa ser
validado.

==================================================
20. INDEPENDENT VERIFIER
==================================================

Preservar ENGINE != VERIFIER. O motor gera a decisão; o verificador
verifica a evidência por caminho independente. Se possível: Python
engine + C verifier (ou outro segundo mecanismo). A auditoria deve
verificar se a independência é real ou apenas duas implementações
equivalentes usando a mesma lógica defeituosa.

==================================================
21. BASE44
==================================================

O Base44 será utilizado como ambiente para construir/prototipar a
interface e a instanciação operacional da nova arquitetura. O prompt
para o Base44 deve criar: dashboard; backend selector; hardware
snapshot; connectivity graph; qubit health map; calibration age;
execution budget; certificate viewer; refusal explanation; UNKNOWN
explanation; execution receipt; audit trail. A interface NÃO pode ser
a fonte da verdade. O núcleo científico deve permanecer
determinístico, testável e independente da interface.

==================================================
22. LINGUAGEM ZEPHIRUM
==================================================

Investigar extensões da linguagem que permitam expressar intenção de
execução. Exemplo conceitual (apenas exemplo — não implementar
sintaxe definitiva antes de verificar consistência com a gramática
atual; necessidade real; possibilidade de formalização; sobreposição
com linguagens existentes):

  ASK quantum_job {
      qubits: 8
      error_budget: 0.01
      coherence_margin: required
      connectivity: required
  }
  ASSESS backend
  CERTIFY execution
  EXECUTE IF CERTIFIED
  REFUSE OTHERWISE

==================================================
23. REGRA DE HONESTIDADE CIENTÍFICA
==================================================

O ZEPHIRUM deve possuir três respostas fundamentais: EXECUTE; REFUSE;
UNKNOWN. Nunca EXECUTE porque "parece seguro". A filosofia central
deve continuar sendo NO GUESSING.

==================================================
24. RESULTADO FINAL OBRIGATÓRIO
==================================================

1. relatório de anterioridade; 2. tabela de tecnologias semelhantes;
3. mapa de sobreposição; 4. pontos abandonados; 5. pontos
preservados; 6. nova arquitetura; 7. especificação do Z-QEA; 8.
especificação do Decision Kernel estendido; 9. especificação do
certificado; 10. proposta do novo plugin; 11. proposta de novo nome;
12. gramática preliminar; 13. API preliminar; 14. arquitetura
Base44; 15. plano de implementação; 16. plano de testes; 17.
benchmark contra sistemas existentes; 18. threat model; 19.
limitações; 20. possíveis contribuições científicas; 21. o que NÃO
pode ser reivindicado; 22. proposta de paper; 23. proposta de
documentação; 24. roadmap de implementação.

==================================================
25. CRITÉRIO DE SUCESSO
==================================================

1. algumas execuções quânticas podem ser eliminadas pelo ZEPHIRUM
antes do backend; 2. execuções necessárias podem ser avaliadas
segundo evidências disponíveis do hardware; 3. decisões podem ser
acompanhadas por certificados verificáveis; 4. dados insuficientes
resultam em UNKNOWN, não em adivinhação; 5. condições incompatíveis
resultam em REFUSE; 6. o sistema consegue incorporar métodos
existentes de routing, calibração e mitigação sem reivindicá-los como
invenção própria; 7. a camada acrescenta valor mensurável sobre o uso
direto dos compiladores existentes; 8. o verificador independente
consegue detectar adulterações; 9. os resultados são reproduzíveis;
10. qualquer alegação de novidade é sustentada por comparação
explícita com o estado da arte.

==================================================
DECLARAÇÃO FINAL DO PROJETO
==================================================

Não construir "mais um compilador quântico". Não construir "mais um
simulador". Não construir "mais um roteador". Não construir "mais um
sistema de correção de erro". Construir e testar uma hipótese mais
específica:

ZEPHIRUM é uma linguagem de computação orientada à necessidade e à
evidência. Na camada quântica, sua função é transformar:

INTENÇÃO -> NECESSIDADE -> ESTADO DO HARDWARE -> VIABILIDADE ->
EVIDÊNCIA -> EXECUÇÃO -> VERIFICAÇÃO.

O sistema deve saber dizer: "não precisa executar"; "pode executar e
consigo justificar"; "não deve executar"; ou "não tenho evidência
suficiente para decidir". Essa honestidade deve ser uma propriedade
formal da arquitetura, não apenas uma frase de marketing.

Somente depois de toda a auditoria e dos experimentos definir se essa
composição constitui uma contribuição científica original e
exatamente qual é a contribuição.

NÃO INVENTAR RESULTADOS. NÃO INVENTAR BENCHMARKS. NÃO INVENTAR
ANTERIORIDADE. NÃO DECLARAR ORIGINALIDADE SEM EVIDÊNCIA. NÃO CONFUNDIR
INTEGRAÇÃO COM INVENÇÃO.

Primeiro auditar. Depois eliminar sobreposições. Depois formalizar.
Depois implementar. Depois medir. Somente então reivindicar.
