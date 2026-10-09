OPENQASM 3.0;
include "stdgates.inc";
// Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM
// Pergunta: entangled == 1 (decidida EXATAMENTE pelo núcleo Zephirum, sem execução)
// Estado exato (Fraction): 7071/10000|0|0|0|0|0|0|7071/10000
qubit[3] q;
ry(1.5707963267948966) q[0];
cx q[0], q[1];
cx q[0], q[2];
