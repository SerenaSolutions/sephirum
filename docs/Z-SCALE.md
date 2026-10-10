# Z-SCALE — The verified quantum chemistry ladder (ZYQL for green fertilizers)

ZYQL's applied thesis: verified simulation of nitrogen fixation chemistry.
Brazil imports ~45.5 Mt of fertilizers (2025 record); national production covers
only ~10.7% of demand. Nitrogen comes from Haber-Bosch. How nitrogenase (FeMoco)
fixes N2 at room temperature is an open problem of chemistry and a canonical
motivation for quantum computing (Reiher et al., arXiv:1605.03590).

The bottleneck is not running the calculation - it is trusting the result.
Every rung of the ladder ships with a signed receipt: declared, judge, receipt.

| Tier | System | Qubits | Status |
|------|--------|--------|--------|
| T1 | H2 dissociation | 2 | DONE - 57 mHa mitigated on ibm_fez (job db4qn304qg6s73c2hrcg) |
| T2 | LiH (2e/3o active space, parity-reduced) | 4 | PREPARED - exact ref -7.8631 Ha vs -7.8824 full (19 mHa gap) |
| T3 | NH / NH3 active space | 6-8 | planned |
| T4 | N2 triple bond | 10-12 | planned |
| T5 | FeMoco fragment | 16-20+ | honest horizon |

Rules: predicted-before-measured (simulation first, receipt signed, then QPU);
error mitigation documented (per-qubit readout calibration, ZNE next window);
useful runs on noisy hardware stay <= ~20 qubits - no marketing numbers.
Evidence: results/qaoa_maxcut_calibration_ibm_fez.json (QAOA p=1 MaxCut triangle:
1.90/2.00 QPU vs 1.48 control), results/vqe_h2_hybrid_stack_ibm_fez.json,
results/lih_hamiltonian_4q_prep.json.

Attribution: methodology per literature (Peruzzo et al. 2014; Farhi et al. 2014;
Reiher et al. 2017); implementation and receipts by the ZYQL prototype.
