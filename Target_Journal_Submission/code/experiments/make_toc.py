"""Generate the ACS graphical Table-of-Contents (TOC) image.
Conceptual + data-driven: chemical-space shift along the applicability-domain axis,
and the real most-out-of-domain-stratum coverage gain (split 0.69 -> ADCC-CP 0.88; target 0.90).
Writes figures/TOC_graphic.png (and .pdf).
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# brand-neutral, color-blind-safe
C_TRAIN = "#4C78A8"   # blue
C_TEST = "#E45756"    # red
C_SPLIT = "#B0B0B0"   # grey
C_ADR = "#D55E00"     # orange (ADCC-CP)
TARGET = 0.90

fig = plt.figure(figsize=(3.25, 1.9), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.45,
                      left=0.03, right=0.97, top=0.82, bottom=0.17)

# ---- left: chemical-space shift schematic
ax = fig.add_subplot(gs[0, 0]); ax.axis("off")
rng = np.random.default_rng(3)
tr = rng.normal([0.32, 0.5], [0.13, 0.16], size=(55, 2))
te = rng.normal([0.78, 0.55], [0.1, 0.14], size=(22, 2))
ax.scatter(tr[:, 0], tr[:, 1], s=7, c=C_TRAIN, alpha=0.75, linewidths=0, label="training")
ax.scatter(te[:, 0], te[:, 1], s=10, c=C_TEST, alpha=0.9, marker="^",
           linewidths=0, label="novel / later")
ax.set_xlim(0, 1.05); ax.set_ylim(0.05, 1.02)
ax.annotate("", xy=(1.02, 0.12), xytext=(0.0, 0.12),
            arrowprops=dict(arrowstyle="->", color="#333333", lw=1.1))
ax.text(0.5, 0.0, "applicability-domain coordinate  a(x)",
        ha="center", va="bottom", fontsize=5.3, color="#333333")
ax.legend(loc="upper left", fontsize=4.8, frameon=False, handletextpad=0.3,
          borderpad=0.1, ncol=2, columnspacing=0.8, bbox_to_anchor=(-0.02, 1.08))

# ---- right: real worst-stratum coverage for out-of-domain compounds
ax2 = fig.add_subplot(gs[0, 1])
vals = [0.686, 0.880]
bars = ax2.bar([0, 1], vals, color=[C_SPLIT, C_ADR], width=0.62, zorder=3)
ax2.axhline(TARGET, ls="--", lw=0.9, color="#333333", zorder=2)
ax2.text(-0.45, TARGET + 0.01, "0.90 target", ha="left", va="bottom", fontsize=4.8,
         color="#333333")
for x, v in zip([0, 1], vals):
    ax2.text(x, v + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=6, zorder=4)
ax2.set_xticks([0, 1]); ax2.set_xticklabels(["split\nCP", "ADCC-CP\n(ours)"], fontsize=5.4)
ax2.set_ylim(0, 1.0); ax2.set_yticks([0, 0.5, 1.0])
ax2.tick_params(axis="y", labelsize=4.8, length=2)
ax2.set_ylabel("coverage of most\nout-of-domain cpds", fontsize=5.4)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.set_title("reliability on\nout-of-domain compounds", fontsize=5.6, pad=3)

fig.suptitle("Conformal coverage over chemical-space shifts, without ratio estimation",
             fontsize=6.6, fontweight="bold", y=0.985)

fig.savefig(FIG / "TOC_graphic.png", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(FIG / "TOC_graphic.pdf", bbox_inches="tight", facecolor="white")
print("wrote", FIG / "TOC_graphic.png")
