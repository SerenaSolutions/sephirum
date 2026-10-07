#!/usr/bin/env python3
"""
ZEPHIRUM ISOLATE — isolamento de processo para o residual.
=====================================================================

A VM é enjaulada em um processo filho descartável. O que pode dar
errado no filho morre no filho:

  MUROS do isolamento (aplicados ao filho):
  - CPU:      RLIMIT_CPU 5s        (além disso: SIGKILL do kernel)
  - MEMÓRIA:  RLIMIT_AS 128 MB    (além disso: MemoryError)
  - TIMEOUT:  10s de parede       (pai mata o filho no relógio)
  - PROCESSO: crash => exit != 0; o hospedeiro segue de pé

  DECLARAÇÃO HONESTA (§12): em Python puro NÃO há isolamento de
  sistema de arquivos nem de rede (sem seccomp/containers aqui).
  Os muros declarados são processo + CPU + memória + tempo. Quem
  precisar de mais roda o filho em container/jail do sistema
  operacional — camada aditiva, documentada, nunca fingida.

API:
  run_isolated(prog, data, budget, timeout=10.0) -> recibo dict
  IsolationFault                                -> filho morreu (motivo)
"""
import json
import os
import resource
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_RUNNER = os.path.join(_HERE, "zephirum_isolated_runner.py")

CPU_SECONDS = 5
MEMORY_BYTES = 128 * 1024 * 1024


class IsolationFault(Exception):
    """O processo isolado morreu — com motivo explícito (§12)."""


def _child_limits():
    def apply():
        resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
        resource.setrlimit(resource.RLIMIT_AS,
                           (MEMORY_BYTES, MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    return apply


def run_isolated(prog, data, budget, timeout=10.0):
    """Executa o bytecode num processo filho limitado; devolve o recibo.

    prog  -> lista de tuplas de opcode
    data  -> valores carregáveis
    budget-> unidades autorizadas pelo certificado
    """
    job = {"program": [list(i) for i in prog], "data": data,
           "budget": budget}
    with tempfile.TemporaryDirectory() as jail:      # cwd sem nada útil
        try:
            proc = subprocess.Popen(
                [sys.executable, _RUNNER],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=jail,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"},
                preexec_fn=_child_limits())
        except OSError as e:
            raise IsolationFault("spawn failed: %s" % e)
        try:
            out, err = proc.communicate(json.dumps(job).encode(),
                                        timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise IsolationFault(
                "TIMEOUT: filho não terminou em %.1fs — morto pelo relógio "
                "do pai (muro de tempo)" % timeout)
    if proc.returncode == 0:
        try:
            return json.loads(out.decode())
        except ValueError:
            raise IsolationFault("filho respondeu lixo (stdout não-JSON)")
    # filho morreu: o motivo vem DELE, explícito
    try:
        fault = json.loads(out.decode()).get("fault", "sem detalhe")
    except ValueError:
        fault = err.decode().strip()[-200:] or "exit %d sem saída" \
            % proc.returncode
    raise IsolationFault("child fault (exit %d): %s"
                         % (proc.returncode, fault))
