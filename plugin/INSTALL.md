# Zephirum Quantum Plugin — installation by platform

The plugin is **pure Python** (`py3-none-any` wheel: zero compiled
extensions, zero mandatory dependencies, Python >= 3.8). Wherever
Python 3 runs, the plugin runs — no QPU, no mandatory SDK.

## Android — Termux

```
pkg update && pkg install python git -y
pip install git+https://github.com/SerenaSolutions/sephirum.git@main#subdirectory=plugin
zephirum-q file.zeph
```

Wheel alternative (no git):

```
pkg install python -y
pip install zephirum_quantum_plugin-0.3.0-py3-none-any.whl
```

§12 note: the `[qiskit]`/`[cirq]` extras depend on numpy — on Termux
they may require slow compilation or fail; the plugin is
SELF-CONTAINED without any SDK (counter-evidence is optional;
missing SDK = declared SKIP receipt, never an error).

## Windows

```
py -m pip install git+https://github.com/SerenaSolutions/sephirum.git@main#subdirectory=plugin
zephirum-q file.zeph
```

(or install the wheel: `py -m pip install zephirum_quantum_plugin-0.3.0-py3-none-any.whl`)

## iOS — a-Shell / Pythonista

a-Shell (App Store) runs pip for pure wheels:

```
pip install zephirum_quantum_plugin-0.3.0-py3-none-any.whl
python3 -m zephirum_quantum_plugin.cli file.zeph
```

Pythonista: copy the `zephirum_quantum_plugin/` folder into the app's
iCloud storage and `import zephirum_quantum_plugin`.

§12 declared: the Windows/Android/iOS coverage is STRUCTURAL (pure
Python, `py3-none-any` tag, install verified in a clean venv) —
execution on physical devices is up to the user; the plugin depends
on no quantum hardware on any platform.
