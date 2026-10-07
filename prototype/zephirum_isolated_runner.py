#!/usr/bin/env python3
"""
Runner ISOLADO da VM — processo filho descartável.
====================================================

Lê um job JSON no stdin, executa a VM, imprime o recibo JSON no
stdout. Nada mais: sem arquivos, sem rede, sem estado. Um crash aqui
morre AQUI — o runtime hospedeiro segue de pé.

Uso:  echo '{"program": [...], "data": [...], "budget": N}' | \
      python3 zephirum_isolated_runner.py

Saída: recibo JSON {"answer", "units", "budget", "trace_hash",
      "program_size"} — ou {"fault": "VMFault: ..."} com exit 1.
"""
import json
import sys

from zephirum_vm import ZephirumVM, VMFault


def main():
    try:
        job = json.loads(sys.stdin.read())
        vm = ZephirumVM(job["data"], job["budget"])
        answer, units, trace = vm.run([tuple(i) for i in job["program"]])
        print(json.dumps({"answer": answer, "units": units,
                          "budget": vm.budget, "trace_hash": trace,
                          "program_size": len(job["program"])}))
        return 0
    except VMFault as e:
        print(json.dumps({"fault": "VMFault: %s" % e}))
        return 1
    except Exception as e:              # §12: qualquer crash é explícito
        print(json.dumps({"fault": "%s: %s" % (type(e).__name__, e)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
