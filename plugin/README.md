# Zephirum Quantum Plugin

Plug-in do **algoritmo Zephirum** para o mundo quântico — nascido do
primeiro artefato da casa (o verificador autônomo transpilado em
Python/C/Java): **prova antes de executar**.

Decide emaranhamento de estados puros de 2 qubits com **aritmética
exata** (Fraction — critério fechado de Schmidt), emite **certificado
verificável** (INPUT_HASH + selo CERT_HASH em SHA-256), cobra **zero
unidades QPU** e trata os SDKs (Qiskit/Cirq) como **gêmeos
adversariais opcionais** de contraprova float — nunca fonte do
veredito.

A fundamentação é matéria universal: concorrência de Wootters
(PRL 80, 2245, 1998), decomposição de Schmidt (1906), Nielsen & Chuang
(cap. 2). Nada de autores individuais de redes sociais.

## Instalação

```
pip install .
# com o gêmeo adversarial:
pip install .[qiskit]
```

## Uso

```
$ zephirum-q examples/bell_phi_plus.zeph --sdk qiskit
STATUS      DECIDED_WITHOUT_EXECUTION
VERDICT     1
CONCURRENCE 1 (exata)
QPU UNITS   0 (faturadas)
INPUT_HASH  ...
CERT_HASH   ...
INDEP CHECK decisão reproduzida e selo confere
SDK CROSS   qiskit float concurrence C = 0.99999... (ruído em volta do exato)
```

API Python:

```python
from zephirum_quantum_plugin import gateway

receipt, ok = gateway(open("examples/separable.zeph").read(),
                      sdk="cirq")
```

## Honestidade (§12)

1. Zero unidades QPU: o critério analítico ELIMINA o caminho do SDK
   (vetor de estado + autodecomposição, 8 unidades).
2. O float do SDK é ruído em volta do exato — o certificado é o
   veredito estável.
3. SDK ausente = recibo `SKIP (§12)`, nunca erro escondido.
4. Família fora do plug-in = recusa com motivo, sem rotear.
5. O certificado é verificável INDEPENDENTEMENTE: `verify()` refaz a
   decisão e confere o selo — adulteração pega no CERT_HASH.
