# PROPOSTA SDUMONT — acesso ao Supercomputador Santos Dumont (LNCC)

Rota escolhida pelo titular em 2026-10-09 para destravar o muro §12
"backend hpc real". Este documento tem duas partes: o mapa de acesso
(regrido ao que foi verificado em busca pública em 2026-10-09) e a
proposta de projeto redigida e pronta para submissão.

---

## PARTE 1 — MAPA DE ACESSO (verificado 2026-10-09)

O SDumont (LNCC, Petrópolis/RJ, ~1,5 Petaflop) é a porta HPC nacional.
Acesso flui por dois caminhos:

### Rota A — direta (recomendada)
- Cadastro de projeto no portal do próprio SDumont:
  https://cgsd-libra.lncc.br/cadastroprojeto
  (formulário do Comitê Gestor de Uso dos Recursos do SDumont;
  cota de armazenamento para projeto: 500 GB a 25 TB)
- Contato oficial para gerenciamento de projetos: sdumont@lncc.br
- Suporte (somente usuários): helpdesk-sdumont@lncc.br
- O Comitê Gestor analisa "demandas de projetos de PD&I" — ou seja,
  proposta de projeto de pesquisa bem redigida é o instrumento.

### Rota B — institucional (parceria)
- Várias instituições com acordo LNCC abrem editais internos
  recorrentes (UFLA, UFOP, IFSP — o do IFSP está em fluxo contínuo
  até 04/12/2026, mas restrito a seus servidores via SUAP).
- Se o titular tiver vínculo com alguma instituição com acordo, a
  submissão por edital interno é a via clássica.
- Sem vínculo: um co-proponente institucional abre essa porta.

### Rota C — estudante (nova informação do titular, 2026-10-09)
- O titular cursou Engenharia de Software / Análise de Sistemas na
  Anhanguera até o 2º semestre e possui carteirinha estudantil.
- Isso abre duas frentes:
  1. verificar se a Anhanguera (rede grande, com initium próprio de
     pesquisa) tem acordo com o LNCC/SINAPSD ou edital interno de
     acesso ao SDumont — pela secretaria/PRP da faculdade;
  2. categorias de "projetos de graduação/iniciação científica" que
     alguns editais institucionais do SDumont contemplam.
- Ressalva honesta: a carteirinha por si não substitui os dados do
  proponente (CPF, identificação completa) nem garante vaga — ela
  qualifica o titular como membro da comunidade acadêmica e pode
  viabilizar a rota institucional via Anhanguera.
- Pendência do titular: mandar a carteirinha (foto) quando for
  submeter; eu mantenho só os dados declarados, não a imagem.

### O que só o titular faz
1. Submeter o cadastro de projeto (rota A) com CPF e identificação —
   ou autorizar envio do e-mail inicial a sdumont@lncc.br.
2. Aprovar a versão final da proposta abaixo.

---

## PARTE 2 — PROPOSTA DE PROJETO (rascunho pronto, PT-BR)

### Título
Certificação exata de estados quânticos em escala: eliminação de
computação com aritmética racional verificável no SDumont

### Proponente
Leonardo Henrique dos Anjos [dados completos a preencher no ato]
Perfil: pesquisador independente; formação em Engenharia de Software /
Análise de Sistemas (Anhanguera, até o 2º semestre, carteirinha
estudantil em vigor); autor do núcleo ZEPHIRUM com validação publicada
em QPU real da IBM.

### Resumo
O projeto ZEPHIRUM (marca em registro INPI) implementa um núcleo de
decisão que prova, offline e com certificado verificável, que uma
computação é desnecessária antes de executá-la. O veredito é
trivalente (0 / 1 / UNKNOWN) e usa aritmética racional exata — sem
ponto flutuante — o que torna a carga essencialmente CPU-bound:
inteiros grandes e frações exatas, ideal para escalonamento massivo
em muitos núcleos. Validação em hardware quântico real da IBM
(ibm_fez, ibm_marrakesh) já foi publicada com recibos (witness GHZ-3
mitigado ≈ +2,9; estabilizadores > +0,89 com IC95 excluindo zero).

### Justificativa da necessidade de HPC
O sandbox local limita baterias de verificação a ~500 mil casos e
estados com dezenas de qubits. No SDumont pretende-se:
1. Escalar as baterias de falsificação (atualmente 2.000 certificados
   adversariais determinísticos, semente pública, 0 falsos aceitos —
   bateria falsification_2000.py, executada em 0,24 s no sandbox) para
   10^7 casos e regimes de parâmetros que não cabem em laptop:
   matrizes grandes, exaustão por família, varredura de forjamento.
2. Certificar por Schmidt exato estados além do limite local
   (esparso GHZ-20 → faixas superiores: a aritmética racional exata
   cresce superlinearmente com 2^n e o re-derivar independente de
   cada certificado dobra o custo — é CPU-bound puro), com verificador
   em C puro (zref) na mesma máquina.
3. Medir a taxa de eliminação por família em escala (hoje 76,51%
   em 500 mil casos) com intervalos de confiança públicos.

Toda a aritmética é exata (Fraction/BigInteger); nenhum passo exige
GPU ou QPU — apenas muitos núcleos CPU e memória. O código é Python
puro + núcleo C, sem dependências proprietárias, pronto para módulos
no agendador do SDumont.

### Recursos solicitados (inicial)
- Núcleo-hora: 50.000 (primeiro ano — cota modesta e justificada)
- Armazenamento: 2 TB (baterias + certificados + recibos JSON)
- Softwares: Python 3, GCC (núcleo C); sem exigência de GPU

### Metodologia
Mesma política do repositório público (evidence-first): nenhum
resultado é reportado sem certificado; recusas são explícitas com
motivo nomeado; resultados forenses (o que quebrou e por quê) são
publicados junto com os sucessos.

### Cronograma (12 meses)
M1–M2: portabilidade e paralelização das baterias; M3–M8: execução
em escala e análise; M9–M12: relatório técnico público + DOI (Zenodo)
+ submissão de artigo com os resultados.

### Produtos
Baterias em escala com resultados e dados abertos; certificados
baterias públicos; artigo submetido; infra de verificação HPC
reutilizável pela comunidade (MIT).

### Resultados prévios que sustentam a proposta (verificáveis)
- Repositório público: github.com/SerenaSolutions/sephirum (MIT)
- Site com recibos: serenasolutions.github.io/sephirum
- 15 releases técnicas (v0.1.0 → v0.9.0), CI verde a cada push
- Validação em QPU real da IBM com ledger público de jobs
- 2.000 certificados adversariais, 0 falsos aceitos (bateria
  determinística pública, semente 20261009, resultados em JSON)

### Referências do projeto
docs/QINTEROP.md; docs/PHASE_5.md; docs/PHASE_6.md; docs/PHASE_7_TRUST.md;
docs/ZQEA_PHASE_CHARTER.md; ledger de hardware (repositório).
```
