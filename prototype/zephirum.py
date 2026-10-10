"""
ZEPHIRUM (Z) - o numeral que e 0 e 1 ao mesmo tempo.
Logica trivalente da ZEPHIRUM (charter, Adendos 3-5).

  0 -> FALSE  / eliminado / computacao desnecessaria
  1 -> TRUE   / necessario / computacao exigida
  Z -> ZEPHIRUM  / UNKNOWN / a pergunta ainda nao colapsada

O Decision Kernel e o operador de colapso: Z -> 0|1, sempre com certificado.
Nao decidir NAO e falha: Z e um estado valido e honesto.
"""

FALSE = 0
TRUE = 1
ZEPHIRUM = "Z"

# Como cada status do compilador ZCA se traduz na logica zephirum
STATUS_TO_TRIT = {
    "DECIDED_WITHOUT_EXECUTION":
        (FALSE, "colapso alcancado SEM execucao: kernel puramente analitico"),
    "DECIDED_BY_REDUCTION":
        (TRUE, "colapso com execucao parcial: o residuo e o kernel"),
    "RESIDUAL_COMPUTATION_REQUIRED":
        (TRUE, "colapso exige o residuo: a execucao foi justificada"),
    "FULL_EXECUTION_REQUIRED":
        (TRUE, "nenhum kernel encontrado: execucao completa justificada"),
    "UNKNOWN":
        (ZEPHIRUM, "permanece ZEPHIRUM: nem necessidade nem desnecessidade provadas"),
    "REFUSED_BEFORE_COMPUTE":
        (ZEPHIRUM, "PORTGATE: proposito declarado em classe proibida; "
                   "recusa assinada antes de qualquer computo"),
}


def collapse(answer):
    """Colapso do zephirum pelo Decision Kernel.

    True  -> 1  (a computacao e necessaria)
    False -> 0  (a computacao e desnecessaria / eliminada)
    None  -> Z  (UNKNOWN: nada afirmado; nunca vira 0 ou 1 sem evidencia)
    """
    if answer is True:
        return TRUE
    if answer is False:
        return FALSE
    return ZEPHIRUM


# ══════════════════════════════════════════════════════════════════
# CLI — Fase 3 (§15/§16 do prompt de implementação)
#   check | compile | verify | explain | benchmark

def _cli_load(path):
    """Frente dupla, explícita e testada (50k casos de equivalência):
    1) linguagem ZEPHIRUM (lexer próprio, Fase 2);
    2) formato de blocos do motor (canônico dos testes/stress).
    Ambos produzem a MESMA IR. Nenhum fallback silencioso além disso."""
    from pathlib import Path as _P
    from nexa_core import parse_nexa
    from zephirum_lexer import parse_zephirum, ZephirumSyntaxError
    src = _P(path).read_text()
    try:
        return parse_zephirum(src)
    except ZephirumSyntaxError:
        return parse_nexa(src)


def _cli_compile(path):
    from pathlib import Path as _P
    from nexa_core import NCA
    blocks = _cli_load(path)
    return blocks, NCA(blocks, _P(path).name).compile()


def cli(argv=None):
    import argparse
    import json
    import subprocess
    import sys
    from pathlib import Path

    ap = argparse.ArgumentParser(
        prog="zephirum",
        description="ZEPHIRUM — decisão, certificado, verificação independente")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="compila, decide e verifica")
    c.add_argument("file")

    c = sub.add_parser("compile", help="compila e grava o certificado .cert.json")
    c.add_argument("file")

    v = sub.add_parser("verify", help="verifica um certificado (com fonte: verificação completa)")
    v.add_argument("cert")
    v.add_argument("source", nargs="?", help="arquivo .zeph da fonte (recomendado)")

    c = sub.add_parser("explain", help="explica pergunta, escada e decisão")
    c.add_argument("file")

    c = sub.add_parser("benchmark", help="executa o benchmark (default 500000)")

    c = sub.add_parser("simulate", help="kernel vs execução plena independente")
    c.add_argument("file")

    c = sub.add_parser("run", help="executa SOMENTE o que sobreviveu (recibo)")
    c.add_argument("file")
    c.add_argument("--backend", default="cpu_exact")
    c.add_argument("n", nargs="?", type=int, default=500000)

    t = sub.add_parser("trust", help="Passo 7: emitentes e assinaturas")
    ts = t.add_subparsers(dest="trust_cmd", required=True)
    g = ts.add_parser("gen-key", help="gera chave de emitente (sk, pk)")
    g.add_argument("--out", help="grava sk hex no arquivo (guardar em sigilo)")
    sg = ts.add_parser("sign", help="assina um certificado .cert.json")
    sg.add_argument("cert")
    sg.add_argument("key", help="arquivo ou hex com a chave privada")
    sg.add_argument("--out", help="certificado assinado de saída")
    al = ts.add_parser("allow", help="adiciona emitente ao registro")
    al.add_argument("pubkey")
    ls = ts.add_parser("list", help="lista emitentes confiáveis")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            blocks, res = _cli_compile(a.file)
            from verify_certificate import verify
            ok, reason = verify(blocks, res["certificate"])
            ans = "Z (UNKNOWN)" if res["answer"] is None else res["answer"]
            print("RESULT:", ans)
            print("STATUS:", res["status"])
            print("CERTIFICATE:", "VALID" if ok else "INVALID (%s)" % reason)
            req = res["required"] or 0
            print("EXECUTION:", "NOT REQUIRED" if req == 0 else
                  "REQUIRED (%d units)" % req)
            return 0 if ok else 1

        if a.cmd == "trust":
            import zephirum_trust as trust
            if a.trust_cmd == "gen-key":
                sk, pk = trust.gen_issuer()
                if a.out:
                    Path(a.out).write_text(sk + "\n")
                print("PUBKEY:", pk)
                print("PRIVATE KEY:", "written to %s" % a.out if a.out
                      else sk)
                print("registry: zephirum.py trust allow %s" % pk)
                return 0
            if a.trust_cmd == "sign":
                kp = Path(a.key)
                sk = kp.read_text().strip() if kp.exists() else a.key
                cert = json.loads(Path(a.cert).read_text())
                signed = trust.sign_certificate(cert, sk)
                out = Path(a.out or (a.cert + ".signed.json"))
                out.write_text(json.dumps(signed, indent=1, sort_keys=True, default=str))
                print("ISSUER:", signed["ISSUER"])
                print("SIGNED:", out)
                return 0
            if a.trust_cmd == "allow":
                reg = Path(trust.TRUSTED_FILE)
                pk = a.pubkey.strip()
                cur = trust.load_trusted()
                cur.add(pk)
                reg.write_text("\n".join(sorted(cur)) + "\n")
                print("TRUSTED ISSUERS:", len(cur))
                return 0
            if a.trust_cmd == "list":
                cur = trust.load_trusted()
                for pk in sorted(cur):
                    print(pk)
                print("(%d emitentes confiáveis)" % len(cur))
                return 0

        if a.cmd == "compile":
            blocks, res = _cli_compile(a.file)
            out = Path(a.file + ".cert.json")
            out.write_text(json.dumps(res["certificate"], indent=1,
                                      sort_keys=True, default=str))
            k = res["decision_kernel"]
            print("KERNEL:", k["id"], "| VERDICT: Z->%s" % k["verdict"])
            print("CERT_HASH:", res["certificate"]["CERT_HASH"])
            print("WRITTEN:", out)
            return 0

        if a.cmd == "verify":
            cert = json.loads(Path(a.cert).read_text())
            from decision_kernel import check_hash
            from zephirum import STATUS_TO_TRIT
            if a.source:
                blocks = _cli_load(a.source)
                from verify_certificate import verify
                ok, reason = verify(blocks, cert)
            else:
                print("NOTE: fonte ausente — verificação limitada "
                      "(hash + estrutura; sem re-derivação da fonte)")
                ok = check_hash(cert)
                reason = "hash integrity"
                trit, _ = STATUS_TO_TRIT.get(cert.get("STATUS", ""), ("?", ""))
                ok = ok and cert.get("DECISION_KERNEL", {}).get("verdict") == trit
            print("CERTIFICATE:", "VALID" if ok else "INVALID")
            if not ok:
                print("REASON:", reason if a.source else "hash/estrutura inconsistente")
            return 0 if ok else 1

        if a.cmd == "explain":
            blocks, res = _cli_compile(a.file)
            from verify_certificate import verify
            ok, _ = verify(blocks, res["certificate"])
            print("QUESTION")
            print("  " + blocks["ASK"]["question"])
            print("MODEL")
            print("  " + blocks["MODEL"].get("type", ""))
            print("LADDER")
            for e in res["ledger"]:
                print("  [%s] %s — %s" % (e["rung"], e["outcome"], e["detail"]))
            ans = "Z (UNKNOWN)" if res["answer"] is None else res["answer"]
            print("DECISION")
            print("  %s  (%s)" % (ans, res["status"]))
            req = res["required"] or 0
            print("EXECUTION")
            print("  " + ("NOT REQUIRED" if req == 0 else
                          "REQUIRED (%d of %d units; %d eliminated, %.1f%%)"
                          % (req, res["original"], res["eliminated"], res["ratio"])))
            print("CERTIFICATE")
            print("  %s  (hash %s...)" % ("VALID" if ok else "INVALID",
                                         res["certificate"]["CERT_HASH"][:16]))
            return 0 if ok else 1

        if a.cmd == "simulate":
            from zephirum_simulator import compare
            blocks = _cli_load(a.file)
            cc = compare(blocks, "cli")
            res, sim = cc["result"], cc["sim"]
            print("KERNEL:    ", "Z (UNKNOWN)" if res["answer"] is None
                  else res["answer"], "(%s)" % res["status"])
            print("SIMULATOR: ", sim["detail"], "->",
                  "UNDERDETERMINED" if sim["status"] != "DECIDED" else sim["answer"],
                  "| %d units" % sim["units"])
            print("VERDICT:   ", cc["verdict"].upper(), "| certificate:",
                  "VALID" if cc["cert_ok"] else "INVALID")
            print("CONTRACT:  ", "OK" if cc["contract_ok"]
                  else "VIOLATED %r" % cc["contract_violations"])
            print("COMPUTATION AVOIDED: %d of %d units"
                  % (cc["avoided_units"], cc["sim_units"]))
            return 0 if cc["verdict"] != "MISMATCH" and cc["cert_ok"] else 1

        if a.cmd == "run":
            from zephirum_runtime import run as _rt, RuntimeRefusal
            blocks = _cli_load(a.file)
            try:
                r = _rt(blocks, "cli", backend=a.backend)
            except RuntimeRefusal as e:
                print("REFUSED:", e)
                return 1
            print("ANSWER:   ", "Z (UNKNOWN)" if r["answer"] is None
                  else r["answer"])
            print("STATUS:    ", r["status"], "| backend:", r["backend"])
            print("EXECUTED:  ", "%d units (%s)" % (r["units_executed"],
                                                    r["detail"]))
            print("ELIMINATED:", "%d of %d units" % (r["units_eliminated"],
                                                     r["units_original"]))
            print("CROSS-CHECK:", r["cross_check"], "| CERT:",
                  r["cert_hash"][:16] + "...")
            return 0 if not r["refused"] else 1

        if a.cmd == "benchmark":
            r = subprocess.run([sys.executable, "stress_test.py", str(a.n)])
            return r.returncode

    except (ValueError, SyntaxError) as e:
        # §12: erro estrutural falha explicitamente — nunca vira UNKNOWN
        print("STRUCTURAL ERROR:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(cli())
