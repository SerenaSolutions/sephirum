# ZYQL no ecossistema Quantum+IA — e o mapa honesto

*(Documento de posicionamento, 2026-10-10. Regra da casa: evidência
antes de velocidade. O que está abaixo é classificado em FEITO COM
PROVA, PLANEJADO e NÃO PROMETIDO — nada além disso é prometido.)*

## 1. O ecossistema pesquisado (12 referências + 6 marcas)

Não existe uma única linguagem universal que reúna IA e computação
quântica. O ecossistema combina linguagens, compiladores, bibliotecas
de ML e plataformas de execução:

- Qiskit Machine Learning — redes neurais e kernels quânticos
- TorchQuantum — circuitos no ecossistema PyTorch
- Qibo/Qiboml — simulação + TensorFlow/PyTorch
- Cirq — circuitos conectáveis a pipelines de IA (TF Quantum)
- Amazon Braket — experimentação e execução híbrida
- Strawberry Fields — fotônica (Xanadu)
- ProjectQ — compilação e execução
- NVIDIA cuQuantum — aceleração em GPUs
- Catalyst — compilação/otimização, fluxos diferenciáveis
- OpenQASM — notação de representação
- QIR — representação intermediária entre compiladores e backends
- DeepQuantum — pesquisa QC + deep learning

Comparação de seis marcas (papéis): PennyLane (aprendizado
diferenciável), TensorFlow Quantum (IA híbrida), Qiskit ML (redes
neurais/kernels), CUDA-Q (compilação e execução heterogênea), Catalyst
(compilação e otimização), QIR (representação intermediária).

**O slot vazio:** as seis respondem "como treino, compilo e executo".
Nenhuma responde "isto foi decidido com prova ANTES de rodar?".
ZYQL ocupa o sétimo papel: **linguagem de decisão verificável** —
camada de juízo e recibo que senta sobre qualquer uma delas via
texto (OpenQASM 3/QIR) e C ABI (`c-api/`).

Nota de licença: nenhuma marca de terceiro é reproduzida ou adaptada;
referências são nomes e links. Verificado em 2026-10-10: o repositório
Strawberry Fields (Xanadu) foi arquivado em 16/01/2026 e está em
somente-leitura — para o ZYQL é precedente de NOME (fruta + quântica,
"Lichia Zyko"), sem nenhuma dependência técnica.

## 2. Mapa honesto de uma página

**FEITO COM PROVA (recibo registrado)**
- Kernel state-vector, 12 portas; Bell/GHZ/Grover/QFT verificados.
- Transpilador Zephyron→OpenQASM 3 validado no parser de referência.
- Execução REAL em QPU IBM ibm_fez (jobs registrados: Bell/GHZ/Grover,
  VQE H2 job db4qn304qg6s73c2hrcg, QAOA MaxCut 95% do ótimo job
  db5acno4qg6s73c36rcg).
- Hybrid Stack v0.3.0: VQE H2, IA-substituto 9,5 mHa vs SPSA 173 mHa
  (simulação); hardware mitigado 57 mHa.
- ZYGUARD: 3 muralhas, recusa assinada SHA-256 antes do computo.
- Racionais canônicos no witness_battery (remediação P0 da auditoria).
- C API `zyql.c` (SQLite-style, C99, zero deps): paridade 3/3 com o
  núcleo Python (mesmos vereditos e hashes); ponte v0.2 para linguagens
  quânticas (gate de circuito) e modelos de IA (verificação de recibo),
  bateria 5/5.
- Zephyrum OS v0.3.0 (SVG no navegador) + instalador com chave.

**PLANEJADO (próximas janelas)**
- T2 LiH (4 qubits) com meta <50 mHa; depois T3 NH3 (escada Z-Scale).
- Mitigação de ruído de porta (ZNE) para aproximar precisão química.
- zyql.c compilado para WebAssembly (prova no navegador).
- Selo ML-DSA-44 (FIPS 204) integrado ao fluxo de certificação.

**NÃO PROMETIDO (fronteira honesta)**
- Vantagem quântica: H2 é trivial; sem correção de erro, execuções
  úteis ficam <= 20 qubits.
- Precisão química (1,6 mHa) no hardware atual: medimos 57 mHa
  mitigado; exige ZNE — é roadmap, não promessa.
- FeMoco completo (T5) no hardware atual.
- Boot físico em máquina real: exige hardware dedicado (roadmap).
- Substituir Qiskit/OpenQASM: a posição é camada acima, não concorrência.
- Executar circuitos: ZYQL decide e prova; quem executa é o backend.
