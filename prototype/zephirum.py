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


if __name__ == "__main__":
    print("ZEPHIRUM (Z) - logica trivalente | etimologia: latim zephirum (Fibonacci, 1202)")
    print("-" * 64)
    for status, (trit, meaning) in STATUS_TO_TRIT.items():
        print("%-30s Z->%s  %s" % (status, trit, meaning))
    print("-" * 64)
    # Demonstracao: a pergunta nasce zephirum; o kernel colapsa com certificado
    for label, ans, st in [
        ("A: soma > 100 decidida com 3/8 termos", True, "DECIDED_BY_REDUCTION"),
        ("I: bounds provam sem executar nada", True, "DECIDED_WITHOUT_EXECUTION"),
        ("B: incognita avaliada como residuo", False, "RESIDUAL_COMPUTATION_REQUIRED"),
        ("C: mediana exige tudo", True, "FULL_EXECUTION_REQUIRED"),
        ("D: media com dados insuficientes", None, "UNKNOWN"),
    ]:
        trit = collapse(ans)
        print("%-38s -> Z->%s  [%s]" % (label, trit, st))
