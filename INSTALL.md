# Install (local)

```bash
./install.sh                 # installs to ~/.zephirum (or $ZEPHIRUM_HOME)
qsim-gateway examples/entangled.zeph          # a decision at the gate
zephirum-decide examples/geometric.zeph       # boot-family decision + receipt
python3 prototype/conformance_v03.py         # the executable standard (9 batteries)
```

Requirements: Python 3. Pure stdlib. No cloud, no LLM.
§12: this is a local prototype installer; pip/PyPI packaging arrives with
the parser milestone. Optional SDK cross-check: `pip install qiskit` then
`qsim-gateway prog.zeph --sdk qiskit`.
