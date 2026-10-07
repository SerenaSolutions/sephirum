#!/usr/bin/env python3
"""
SIFR REPL — a linguagem que você digita.

Uso interativo:   python3 sifr_repl.py
Uso por pipe:     cat programa.sifr | python3 sifr_repl.py

Cole (ou digite) um programa SIFR; linha vazia compila. O resultado traz o
estado (5 possíveis), a resposta (0/1/Z) na lógica zerum, e a verificação do
certificado pelo módulo INDEPENDENTE (nexa_checker).
"""
import sys

from nexa_core import parse_nexa, NCA
from nexa_checker import verify
from zerum import STATUS_TO_TRIT

BANNER = """
SIFR 0.2 — a linguagem da computação antes da execução
PERGUNTE PRIMEIRO. PROVE DEPOIS. COMPUTE POR ÚLTIMO.
Comandos: :exemplo  :ajuda  :sair   (linha vazia = compilar)
"""

EXAMPLE = """ASK:
    question: sum > 40
CONTRACT:
    absolute_error: 0
MODEL:
    type: threshold_sum
    terms: 3, 7, 12, 40
    assumption: terms_nonnegative
    unknown: x in 0..50
    unknown_value: 7
"""


def run_program(src):
    try:
        blocks = parse_nexa(src)
    except Exception as e:
        print("ERRO DE SINTAXE:", e)
        return
    if "ASK" not in blocks:
        print("ERRO: bloco ASK obrigatório (veja :exemplo)")
        return
    res = NCA(blocks, "repl").compile()
    ok, reason = verify(blocks, res["certificate"])
    trit, trit_msg = STATUS_TO_TRIT[res["status"]]
    cert = res["certificate"]
    original = cert["EVIDENCE"].get("original_terms", 0)
    executed = cert["EVIDENCE"].get("required_terms", 0)
    answer = "Z" if trit == "Z" else ("0 (desnecessário)" if trit == 0 else "1 (necessário)")
    print("─" * 56)
    print("ESTADO   :", res["status"])
    print("RESPOSTA :", answer)
    print("ZERUM    :", trit_msg)
    print("KERNEL   :", cert["KERNEL"], "| degrau:", cert["RUNG"])
    print("UNIDADES : demandadas %s | executadas %s | eliminadas %s"
          % (original, executed, original - executed))
    print("CERTIF.  : %s — %s" % ("VERIFICADO" if ok else "REJEITADO", reason))
    print("─" * 56)
    if not ok:
        print("AVISO: certificado rejeitado pelo verificador independente!")


def main():
    print(BANNER)
    buf, piped = [], not sys.stdin.isatty()
    if piped:
        run_program(sys.stdin.read())
        return 0
    while True:
        try:
            line = input("sifr> " if not buf else "  ...> ")
        except EOFError:
            print()
            return 0
        if line.strip() == ":sair":
            return 0
        if line.strip() == ":ajuda":
            print(BANNER)
            continue
        if line.strip() == ":exemplo":
            print(EXAMPLE)
            continue
        if line.strip() == "" and buf:
            run_program("\n".join(buf))
            buf = []
            continue
        if line.strip():
            buf.append(line)


if __name__ == "__main__":
    sys.exit(main())
