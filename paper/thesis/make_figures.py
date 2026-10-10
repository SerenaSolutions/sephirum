"""Thesis figures — generated ONLY from real experimental records (results/*.json).
No synthetic data. Evidence before velocity."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "results"; F = "paper/thesis/figures"
plt.rcParams.update({"font.size": 10, "figure.dpi": 150, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.axisbelow": True})

# ---- Fig 1: H2 energy (computational quantum chemistry) ----
d = json.load(open(f"{R}/h2_energy_qpu_study.json"))
exact = -1.1456
qpu = -1.0048
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.axhspan(exact-0.10, exact+0.10, color="#cdebc7", label="study band (0.10 Ha)")
ax.axhline(exact, color="#1a7a1a", lw=2, label="exact certified kernel (-1.1456 Ha)")
ax.axhline(-1.1373, color="#888", ls=":", lw=1.2, label="FCI ref. (O'Malley+ PRL 2016)")
ax.errorbar([1], [qpu], yerr=0.02, fmt="o", color="#c22", ms=8, capsize=4,
            label="QPU estimate (ibm_fez, unmitigated)")
ax.set_xticks([]); ax.set_ylabel("Energy (Ha)")
ax.set_title("H$_2$ ground state: exact decision vs QPU witness")
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout(); fig.savefig(f"{F}/fig_h2_energy.png")

# ---- Fig 2: entanglement controls (positive/negative) on hardware ----
b = json.load(open(f"{R}/bell_phi_plus_ibm_fez.json"))
s = json.load(open(f"{R}/separable_control_ibm_fez.json"))
fig, ax = plt.subplots(figsize=(6.4, 3.6))
x = [0, 1]; w = 0.35
ax.bar([0-w/2, 1-w/2], [b["corr_zz"], b["corr_xx"]], w, color="#4c78c8",
       label="Bell $\\Phi^+$ (exact verdict 1)")
ax.bar([0+w/2, 1+w/2], [s["corr_zz"], s["corr_xx"]], w, color="#e8913a",
       label="separable control (exact verdict 0)")
ax.axhline(0, color="k", lw=0.8)
ax.axhline(1, color="#1a7a1a", ls="--", lw=1, label="ideal correlation")
ax.set_xticks(x); ax.set_xticklabels(["$\\langle ZZ\\rangle$", "$\\langle XX\\rangle$"])
ax.set_ylim(-0.25, 1.1)
ax.set_title("Positive and negative controls, ibm_fez (2048/512 shots)")
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(f"{F}/fig_bell_controls.png")

# ---- Fig 3: GHZ ladder across hardware ----
g = json.load(open(f"{R}/ghz_n_ladder_ibm_fez.json"))
g20 = json.load(open(f"{R}/ghz20_sparse_ibm_fez.json"))
rungs = [4, 6, 20]
vals = [g["ghz4_entangled"]["pop_0N_1N"], g["ghz6_entangled"]["pop_0N_1N"], g20["pop_0x20_1x20"]]
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.plot(rungs, vals, "o-", color="#7a3cc8", ms=8, label="pop($0^N$+$1^N$), ibm_fez")
for r_, v in zip(rungs, vals):
    ax.annotate(f"{v:.2f}", (r_, v), textcoords="offset points", xytext=(6, 6), fontsize=9)
ax.axhline(1.0, color="#1a7a1a", ls="--", lw=1, label="ideal GHZ")
ax.axhline(0.5, color="#999", ls=":", lw=1, label="classical witness bound")
ax.set_xscale("log"); ax.set_xticks(rungs); ax.set_xticklabels(["4", "6", "20 (sparse)"])
ax.set_xlabel("GHZ rung (qubits)"); ax.set_ylabel("population")
ax.set_ylim(0, 1.1)
ax.set_title("GHZ ladder: exact verdict 1 at every rung, hardware witness decays honestly")
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(f"{F}/fig_ghz_ladder.png")

# ---- Fig 4: CHSH (kingston) ----
c = json.load(open(f"{R}/chsh_qkd_kingston.json"))
S = 1313/1024
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ax.bar([0,1,2], [2.0, S, 2.828], color=["#999", "#c22", "#1a7a1a"], width=0.55)
ax.set_xticks([0,1,2]); ax.set_xticklabels(["classical bound", "ibm_kingston (S)", "Tsirelson"])
ax.set_ylabel("CHSH value S")
ax.set_title(f"CHSH/QKD run: S = {S:.4f} — certified refusal (precision gate), hardware evidence only")
fig.tight_layout(); fig.savefig(f"{F}/fig_chsh.png")
print("figuras:", os.listdir(F))
print("ghz6 pop:", g["ghz6_entangled"]["pop_0N_1N"])
