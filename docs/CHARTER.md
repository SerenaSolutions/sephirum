# MASTER PROMPT — NEXUS / NEXA (ESPECIFICAÇÃO FUNDADORA)
Aprovado por AUŠRA Quantinum em 2026-10-06. Tratado como especificação fundadora do livro e do protótipo NEXA.

---

## PROJETO EDITORIAL E CIENTÍFICO

TÍTULO DE TRABALHO: NEXUS — A Computação Antes da Execução
SUBTÍTULO PROVISÓRIO: Da Pergunta ao Decision Kernel: uma nova arquitetura para decidir o que realmente precisa ser computado

### 1. MISSÃO
Transformar a hipótese de arquitetura computacional em livro técnico-científico + especificação de linguagem + protótipo funcional. Ideia central: "Antes de executar uma computação, devemos determinar se aquela computação é realmente necessária para responder à pergunta formulada sob um determinado contrato."
NÃO apresentar como descoberta absoluta. Reconhecer décadas de prior art: otimização de programas, compilação, partial evaluation, programação orientada a objetivos, análise estática, slicing, query optimization, theorem proving, model checking, symbolic execution, redução algébrica, decision procedures, verificação formal, computação aproximada, seleção de algoritmos, computação quântica, compiladores quânticos, certificados computacionais. Objetivo: composição arquitetural onde a pergunta científica e seu contrato são elementos de primeira classe do processo de compilação.

### 2. PERGUNTA CENTRAL DO LIVRO
1. "Eu realmente preciso executar esta computação para responder à pergunta que fiz?"
2. "Se preciso computar, qual é a menor computação que consigo justificar?"
3. "Como provar que aquilo que foi eliminado realmente não era necessário?"

### 3. MUDANÇA DE PARADIGMA
Convencional: PROBLEMA → ALGORITMO → PROGRAMA → COMPILAÇÃO → EXECUÇÃO → RESULTADO.
NEXUS: PROBLEMA → PERGUNTA → CONTRATO → NECESSIDADE → DECISION KERNEL → CERTIFICADO → RESÍDUO NECESSÁRIO → EXECUÇÃO.
A execução deixa de ser ponto de partida implícito; passa a ser possibilidade justificada pela pergunta e pelo contrato.

### 4. PÚBLICO — TRÊS NÍVEIS SIMULTÂNEOS
N1 leitor geral (exemplos cotidianos: não desmontar uma casa para saber se uma porta está aberta); N2 cientista/engenheiro (pergunta, contrato, hipótese, invariantes, redução, residual computation, certificado, orçamento, runtime, CPU/GPU/HPC/QPU); N3 cientista da computação (semântica, modelo formal, IR, compilador, complexidade, soundness, incompletude, verificadores independentes, benchmarks, comparação com literatura). Nunca misturar níveis sem explicar a transição.

### 5. FRASES FILOSÓFICAS CENTRAIS
"A maior otimização de uma computação não é executá-la mais rápido. É demonstrar que ela não precisava ser executada."
Salvaguarda: "Uma computação somente pode ser declarada desnecessária quando existe evidência suficiente para responder à pergunta sem ela."
Terceira regra: "Não provar necessidade não é provar desnecessidade. Não provar desnecessidade também não é provar necessidade." O terceiro estado UNKNOWN deve existir.

### 6. LINGUAGEM NEXA
NEXA — Necessity-Exploration eXecution Architecture. Nome provisório até verificação de colisões (linguagens, acadêmico, bibliotecas, empresas, marcas, domínios, repositórios, PI). Se conflito: gerar alternativas automaticamente e escolher a melhor sem alterar a filosofia. NEXA não é "a primeira linguagem orientada a objetivos" (GOAL já existe). Diferenciação: QUESTION + CONTRACT + NECESSITY ANALYSIS + DECISION KERNEL + CERTIFICATE + RESIDUAL EXECUTION.

### 7. COMO O PROGRAMADOR NEXA PENSA
De "compute X" para blocos declarativos: ASK / CONTRACT / MODEL / BUDGET / REQUIRE. O programador declara: o que deseja saber; condições a respeitar; erro admissível; hipóteses válidas; recursos disponíveis; custo a minimizar; tipos de evidência aceitáveis.

### 8. OBJETO FUNDAMENTAL — DECISION KERNEL
"Procedimento certificado suficiente para decidir uma pergunta específica sob um contrato especificado." NÃO afirmar minimalidade global: "o menor kernel encontrado e certificado dentro do espaço de transformações e métodos disponíveis."

### 9. ALGORITMO NCA — Necessity Compilation Algorithm
Entrada: P (problema/modelo/programa), Q (pergunta), C (contrato), B (orçamento), A (recursos/métodos). Saída: K (Decision Kernel), R (residual computation), Π (certificado), S (status).
Degraus: 1 IDENTIDADE, 2 INVARIANTE, 3 SIMPLIFICAÇÃO, 4 REDUÇÃO, 5 LIMITE, 6 SOLUÇÃO ANALÍTICA, 7 APROXIMAÇÃO CERTIFICADA, 8 ALGORITMO CLÁSSICO, 9 PARALELIZAÇÃO, 10 SIMULAÇÃO, 11 COMPUTAÇÃO QUÂNTICA. Ordem alterável por custo/domínio/evidência, com registro obrigatório.

### 10. ESTADOS FORMAIS
DECIDED_WITHOUT_EXECUTION; DECIDED_BY_REDUCTION; RESIDUAL_COMPUTATION_REQUIRED; FULL_EXECUTION_REQUIRED; UNKNOWN. Nunca transformar UNKNOWN automaticamente em necessidade.

### 11. QUATRO PILARES (OBRIGATÓRIOS)
1. LANGUAGE (NEXA): perguntas, contratos, modelos, hipóteses, tolerâncias, objetivos, recursos, restrições.
2. COMPILER: interpretar pergunta; IR; procurar Decision Kernels; transformações; testar condições; gerar certificados; gerar computação residual; selecionar nível de execução.
3. SIMULATOR: instrumento de validação, teste, comparação, falsificação, estimativa, verificação de suficiência do residual (clássica, HPC, Monte Carlo, física, quântica, aproximada).
4. RUNTIME: executa somente o que sobreviver à análise; despacha para CPU/GPU/HPC/SIMULATOR/QPU; QPU não é destino obrigatório.
(NEXA-IR é infraestrutura transversal, não quinto pilar: PROBLEM, QUESTION, CONTRACT, ASSUMPTIONS, EVIDENCE, KERNEL, RESIDUAL, CERTIFICATE, RESOURCE, EXECUTION, RESULT.)

### 12. CERTIFICADO DE NECESSIDADE COMPUTACIONAL
Estrutura: INPUT_HASH, QUESTION, CONTRACT, ASSUMPTIONS, INITIAL_COMPUTATION, ELIMINATION_TRACE, DECISION_KERNEL, RESIDUAL, RESULT, CERTIFICATE, CHECKER, COST_ESTIMATE, FINAL_EXECUTION_LEVEL. Deve responder: "Por que esta parte foi eliminada?" e "Por que esta parte permaneceu?"

### 13. EXEMPLO DIDÁTICO
ASK: 60+30+20+5+4+3+2+1 > 100 → 60+30+20=110; termos restantes não negativos; 110>100. Saída: DECIDED_BY_REDUCTION; ORIGINAL_TERMS 8; REQUIRED_TERMS 3; ELIMINATED 5; ELIMINATION_RATIO 62.5%; CERTIFICATE: remaining_terms >= 0, partial_sum > threshold.

### 14. EXEMPLO DE IMPOSSIBILIDADE
ASK: mean(x1..x10) > 50 com apenas 5 valores conhecidos e hipóteses insuficientes → STATUS: UNKNOWN. Não inventar resposta. Não declarar EXECUTION_REQUIRED sem justificar.

### 15. PAPEL DA COMPUTAÇÃO QUÂNTICA
NEXA não é linguagem quântica disfarçada. Narrativa: PROVA → MATEMÁTICA → REDUÇÃO → ANALÍTICO → APROXIMAÇÃO CERTIFICADA → CLÁSSICO → PARALELO → SIMULAÇÃO → QUÂNTICO. Neutralidade tecnológica obrigatória.

### 16. RELAÇÃO COM IBM/QISKIT
Mesma família de plataformas programáveis (language/compiler/simulator/runtime), filosofia diferente: Qiskit pergunta "como computar"; NEXA pergunta "a execução é necessária?". Não apresentar como "Qiskit melhor"; apresentar como deslocamento da decisão de necessidade para antes da execução.

### 17. RESPONSABILIDADE CIENTÍFICA
Separar: FATO COMPROVADO / HIPÓTESE / INFERÊNCIA / RESULTADO EXPERIMENTAL / PROPOSTA DE ARQUITETURA / POSSÍVEL CONTRIBUIÇÃO ORIGINAL. Nunca declarar "ninguém fez isso antes" sem pesquisa ampla. Nunca fabricar referência. Nunca transformar analogia em prova de novidade. Nunca transformar benchmark pequeno em prova de superioridade. Nunca afirmar vantagem quântica sem evidência. Nunca esconder resultados negativos.

### 18. TESTE DE ANTERIORIDADE
Pesquisar antes de afirmar contribuição: compiler optimization, semantic query optimization, program slicing, partial evaluation, abstract interpretation, symbolic execution, theorem proving, model checking, property-directed verification, goal-directed evaluation, decision procedures, algorithm selection/portfolios, certified computation, proof-carrying code/data, computational sufficiency, sufficient statistics, residual computation, early termination, non-execution proofs, quantum compilation, quantum resource estimation, dequantization, scientific workflow systems. Parte existente → PRIOR ART; procurar o que permanece original na composição.

### 19. TESTE DE FALSIFICAÇÃO
Benchmarks: A) computação completamente eliminável; B) parcialmente eliminável; C) não eliminável; D) sistema não consegue saber; E) o sistema erra. Caso E crítico: falso certificado de desnecessidade = falha crítica de soundness.

### 20. MÉTRICAS
computation eliminated; execution avoided/reduced; runtime; energy; memory; proof generation cost; certificate verification cost; false elimination rate; unknown rate; residual size. Não medir apenas velocidade. NetBenefit = Cost_baseline − (Cost_analysis + Cost_residual + Cost_verification). NetBenefit < 0 = transformação logicamente válida, computacionalmente desvantajosa. Mostrar honestamente.

### 21. OBJETIVO DO BUILDER BASE44
Não tratar como landing page. Construir progressivamente: NEXA LANGUAGE → PARSER → NEXA-IR → NECESSITY COMPILER → DECISION KERNEL ENGINE → CERTIFICATE GENERATOR → CERTIFICATE CHECKER → SIMULATOR → RUNTIME. Primeiro protótipo: sem física quântica real; provar o conceito em problemas matemáticos e científicos controlados.

### 22. PRIMEIRO PROTÓTIPO OBRIGATÓRIO
Implementar no mínimo: 1. identidade algébrica; 2. soma com limiar; 3. determinante de matriz triangular; 4. limites matemáticos; 5. cálculo analítico; 6. redução de expressão; 7. caso parcialmente decidível; 8. caso impossível de decidir com as informações disponíveis; 9. geração de certificado; 10. verificador independente do certificado. Depois: backends progressivos CPU/GPU/HPC/SIMULATOR/QPU.

### 23. O LIVRO NÃO É MANUAL DE MARKETING
Estrutura narrativa: PROBLEMA → OBSERVAÇÃO → HIPÓTESE → ANTERIORIDADE → FALSIFICAÇÃO → COMPOSIÇÃO → FORMALIZAÇÃO → LINGUAGEM NEXA → ALGORITMO NCA → COMPILADOR → SIMULADOR → RUNTIME → EXPERIMENTOS → LIMITAÇÕES → RESULTADOS → FUTURO. Mostrar ideias abandonadas. O leitor deve ver que a arquitetura nasceu de tentativas de falsificação.

### 24. TOM
Científico, acessível, ambicioso, transparente, intelectualmente humilde, rigoroso, futurista sem ficção científica, crítico da própria hipótese. Proibido: "revolucionário" sem evidência, "inédito" sem busca, "primeiro do mundo", "elimina toda computação", "torna computadores quânticos desnecessários", "resolve qualquer problema".

### 25. TESE FINAL
"Uma plataforma computacional pode ser construída de modo que a pergunta científica, e não a execução de um algoritmo específico, seja o objeto primário da compilação; nessa arquitetura, o compilador procura um Decision Kernel certificado capaz de responder à pergunta com a menor computação justificável disponível e somente encaminha ao Runtime o resíduo computacional que permanece necessário." Se os experimentos demonstrarem recombinação sem valor prático, o livro deve dizer isso. A conclusão é determinada pela evidência.

### 26. ENCERRAMENTO
"E se o próximo salto da computação não vier de fazer máquinas calcularem mais, mas de ensiná-las a saber quando não precisam calcular?"
"NEXA não promete eliminar a computação. NEXA tenta eliminar aquilo que pode ser demonstravelmente dispensado."

### 27. REGRA SUPREMA
NÃO EXECUTE PRIMEIRO. PERGUNTE PRIMEIRO. PROVE O QUE PODE SER ELIMINADO. CALCULE APENAS O QUE SOBRAR. E QUANDO NÃO SOUBER, DIGA: UNKNOWN.

FIM DO PROMPT-MESTRE.

---
Adendo do chefe: o projeto deixou de ser ideia abstrata. Tema, finalidade, público, filosofia, linguagem NEXA, algoritmo NCA, quatro pilares, IR, certificados, estados, testes e o papel do Base44 como construtor do protótipo. A porta fica aberta para a ciência dizer "não": o sistema deve nascer testável, não como afirmação de marketing.

---

## ADENDO — RENOMEAÇÃO COMERCIAL (autorizada pelo chefe, 2026-10-06)
- Livro (adotado provisoriamente): **"PERGUNTE PRIMEIRO — A Computação Antes da Execução"** (EN: *ASK FIRST: Computation Before Execution*). É a própria Regra Suprema como marca. Alternativas: "O COMPUTADOR QUE DIZ NÃO"; "ZERO — A Máquina que Recusa Calcular".
- Linguagem: **NEXA → ZERA** — *Zero-Execution Reasoning Architecture*. Curto, pronunciável globalmente, verbo real em português ("zerar" = reduzir a zero) e o backronym traduz exatamente a filosofia. NEXA permanece como codinome interno.
- Algoritmo: **NCA → ZCA** — *ZERA Compilation Algorithm* (alternativa: P2Z — Proof-to-Zero).
- Colisões: NEXUS tem uso pesado no setor tech (Sonatype Nexus, Google Nexus, Nexus Mods) — descartado como marca; NEXA sem linguagem encontrada; ZERA sem linguagem/produto de software encontrados em busca preliminar (2026-10-06). Verificação formal de marcas/PI permanece pendente antes de cravar comercialmente.
- Vocabulário técnico inalterado: Decision Kernel, estados formais, certificados, ledger.

---

## ADENDO 2 — NOMES DEFINITIVOS EM OUTRA LÍNGUA (2026-10-06)
- **Livro: PRASHNA — A Computação Antes da Execução.** Prashna (sânscrito प्रश्न, "a pergunta"). Ancorado no Prashna Upanishad, texto milenar composto de perguntas ao sábio Pippalada, que só responde a quem pergunta corretamente — a tese exata do livro: a pergunta como objeto primário. Sonoro (PRAHSH-na), global, sem colisões encontradas em busca preliminar.
- **Linguagem: SIFR** (árabe صفر, "zero") — a raiz etimológica da própria palavra "zero" (ṣifr → zephirum → zero). A linguagem que devolve a execução ao zero, nomeada com o nascimento do zero. Curto, sonoro, comercial, sem colisão encontrada no espaço de linguagens (Shunya foi descartado: colide com Shunya Labs/Shunya Ekai, empresas de IA na Índia).
- **Algoritmo: SCA — SIFR Compilation Algorithm** (ex-ZCA; também citável como "Ask-to-Zero"). Vocabulário técnico inalterado (Decision Kernel, estados, certificados).
- Verificação formal de marcas/PI permanece pendente antes de uso comercial.

---

## ADENDO 3 — O NUMERAL ZERUM (criado em 2026-10-06, por solicitação do chefe)
**ZERUM (Z)** — o numeral que é 0 e 1 ao mesmo tempo. Zero + um (PT) / unum (latim); rima com "quantum" deliberadamente.

Definições por contexto (hierarquia de evidência respeitada):
1. Leitura quântica: Z ≡ (|0⟩+|1⟩)/√2 = |+⟩. HONESTIDADE: o estado |+⟩ já existe na física; zerum é um NOME para o conceito, não uma nova matemática.
2. Leitura lógica SIFR (central do livro): Z é o terceiro valor de verdade — 0 = falso/eliminado; 1 = verdadeiro/necessário; Z = UNKNOWN, a pergunta ainda não colapsada. O Decision Kernel é o operador de colapso Z → 0 ou 1, sempre com certificado.
3. Leitura filosófica: toda pergunta nasce zerum; a execução só entra quando o colapso exige. "O zerum é o estado natural de toda pergunta."

- LIVRO: "ZERUM — A Computação Antes da Execução" (subtítulo: "Da Pergunta ao Decision Kernel"). Prashna aposentado como título (dúvida do chefe sobre origem indiana); reaproveitado como homenagem: bloco de pergunta da linguagem SIFR pode se chamar PRASHNA.
- LINGUAGEM: SIFR (mantido, aprovado: zephirum/árabe, a raiz de "zero").
- ALGORITMO: SCA — SIFR Compilation Algorithm.
- Colisões ZERUM (busca 2026-10-06): empresa brasileira de TI/cibersegurança (@zerum_it) e construtora britânica Zerum — classes diferentes das nossas (livro/linguagem científica); verificação formal INPI/marcas pendente antes de uso comercial. Alternativas se necessário: ZERUN, ZUNO, ZERONE, ZHEN.

---

## ADENDO 4 — INQUÉRITO LINGUÍSTICO MUNDIAL DO NUMERAL (2026-10-06)
Mundo: ~7.100 línguas vivas (Ethnologue). Europa ~250; Ásia ~2.300; África ~2.000; Pacífico ~1.100; Américas ~1.000.
Jornada do zero (fato histórico): śūnya (sânscrito) → ṣifr (árabe) → ṣiprā (siríaco/aramaico científico medieval; o aramaico ANTIGO não tinha zero — o conceito nasceu depois, na Índia) → zephirum (latim medieval, via Fibonacci) → zero. ZERUM entra nesse mesmo rio.
Fusões zero+um por idioma: EN zerone; PT zerum/zeroum; ES ceruno (COLIDE: Ceruno AG suíça de TI + marca australiana classe 9 IA — descartado); IT zeruno (COLIDE: Italdesign Zerouno + marca de luminárias — descartado); AR **SIWAHID** (ṣifr+wāḥid, limpo); HE efechad; GR medhén; SK śunyeka; JA reiichi (零一); ZH língyī (零一; coincidência: 灵异 = sobrenatural); RU nolodin; siríaco ṣipraḥad.
INSIGHT DO ÁRABE: o árabe possui o DUAL gramatical ("-ayn/-ān"): ṣifrayn (صفرين) = "os dois zeros, juntos" — a língua-mãe da SIFR já gramaticaliza "dois ao mesmo tempo" há mais de um milênio. O zerum tem ancestral gramatical.
DECISÃO REGISTRADA: ZERUM permanece o numeral e o título global do livro; SIWAHID (limpo de colisões) fica registrado como o nome árabe-irmão do numeral (usável na edição árabe e no vocabulário da linguagem SIFR, ex.: operador de colapso). Runner-up EN: ZERONE.

---

## ADENDO 5 — CONFIRMAÇÃO DO CHEFE (2026-10-06): "SIWAHID? PROSSIGA"
SIWAHID adotado como nome-irmão árabe do numeral ZERUM (edição árabe do livro + vocabulário SIFR).
Milestone executado: (1) lógica trivalente Z formalizada no protótipo (zerum.py: 0/1/Z, colapso pelo Decision Kernel); (2) estrutura completa do livro criada em livro_zerum/ESTRUTURA.md (5 partes, 18 capítulos, narrativa de investigação §24, 4 apêndices).
