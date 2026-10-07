# Prototype ZEPHIRUM — motor NCA + verificador independente

Pipeline: ZEPHIRUM → IR → escada → decisão 0/1/Z → certificado → CERT_HASH
→ `verify_certificate.py` (re-deriva da fonte, sem confiar no motor).

## Uso

```bash
python3 zephirum.py check example.zeph
python3 zephirum.py explain example.zeph
python3 zephirum.py compile example.zeph
python3 zephirum.py verify example.zeph.cert.json example.zeph
python3 zephirum.py benchmark 500000
python3 zephirum.py simulate example.zeph
```

## Baterias (todas exit 0)

```bash
python3 run_tests.py                        # casos didáticos + soundness
python3 test_adversarial_certificates.py    # §6: 100% adulterações rejeitadas
python3 test_properties.py                  # §11 propriedades + §12 robustez
python3 test_equivalence.py                # §10: tripla 10.000 casos
python3 test_entanglement.py               # família emaranhado (Schmidt)
python3 falsification_200.py               # 200 adversariais: 0 falsos
python3 test_zephirum_lang.py              # linguagem: 50k equivalência
python3 test_zephirum_ir.py                # IR transversal
python3 stress_test.py 500000              # benchmark + soundness
python3 ai_layer.py                       # camada consultiva (nunca decisória)
python3 test_simulator.py                # gêmeo adversarial: 20k diferenciais
python3 test_contracts.py                 # contrato como máquina (3 camadas)
python3 test_models.py                   # modelos: exact vs float64 (10k+armadilhas)
```

## Módulos

| arquivo | papel |
|---|---|
| zephirum.py | lógica trivalente 0/1/Z + CLI |
| nexa_core.py | motor NCA: escada, famílias, certificado |
| decision_kernel.py | kernel de primeira classe + CERT_HASH |
| verify_certificate.py | verificador independente (não-confiança) |
| zephirum_lexer.py / zephirum_transpiler.py / zephirum_repl.py | linguagem (Fase 2) |
| zephirum_ir.py | IR transversal (Fase 2) |
| zephirum_simulator.py | Fase 4: execução plena independente (gêmeo adversarial) |
