# Instalação do Zephirum Quantum Plugin por plataforma

O plug-in é **Python puro** (wheel `py3-none-any`: zero extensão
compilada, zero dependência obrigatória, Python >= 3.8). Onde um
Python 3 roda, o plug-in roda — sem QPU, sem SDK obrigatório.

## Android — Termux

```
pkg update && pkg install python git -y
pip install git+https://github.com/SerenaSolutions/zephirum.git@main#subdirectory=plugin
zephirum-q arquivo.zeph
```

Alternativa por wheel (sem git):

```
pkg install python -y
pip install zephirum_quantum_plugin-0.3.0-py3-none-any.whl
```

Nota §12: os extras `[qiskit]`/`[cirq]` dependem de numpy — no
Termux podem exigir compilação demorada ou falhar; o plug-in é
AUTÔNOMO sem SDK (contraprova é opcional; SDK ausente = recibo
SKIP declarado, nunca erro).

## Windows

```
py -m pip install git+https://github.com/SerenaSolutions/zephirum.git@main#subdirectory=plugin
zephirum-q arquivo.zeph
```

(ou instale o wheel: `py -m pip install zephirum_quantum_plugin-0.3.0-py3-none-any.whl`)

## iOS — a-Shell / Pythonista

a-Shell (App Store) roda pip para wheels puros:

```
pip install zephirum_quantum_plugin-0.3.0-py3-none-any.whl
python3 -m zephirum_quantum_plugin.cli arquivo.zeph
```

Pythonista: copie a pasta `zephirum_quantum_plugin/` para o iCloud
do app e importe `zephirum_quantum_plugin`.

§12 declarado: a cobertura Windows/Android/iOS é ESTRUTURAL
(python puro, tag `py3-none-any`, instalação verificada em venv
limpa) — a execução em aparelho físico fica a cargo do usuário;
o plug-in não depende de hardware quântico em nenhuma plataforma.
