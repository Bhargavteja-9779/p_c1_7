"""Round-6 Figure: the ADCC-CP 'AD calibration curve' a -> half-width, versus split CP
(constant) and ADR-CP (estimated 1-D weights), with empirical |residual| quantiles of the
temporal-test compounds binned by a (uses test labels ONLY for this illustration).
Representative targets; LightGBM; window w30; seed 0."""
from __future__ import annotations
import sys, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["CP_NJOBS"] = "1"
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.utils import load_config
from src.data.datasets import load_panel_target
from src.pipeline import run_single

FIG = Path(__file__).resolve().parents[2] / "figures"
TARGETS = ["egfr", "herg", "dpp4"]


def main():
    cfg = load_config("config/default.yaml")
    fig, axes = plt.subplots(1, len(TARGETS), figsize=(12, 3.8), sharey=False)
    summ = {}
    for ax, t in zip(axes, TARGETS):
        df = load_panel_target(t, cfg)
        meta, rows = run_single(df, cfg, f"panel_{t}", "lgbm", 0, "temporal", 0.1,
                                methods=["split", "weighted_ad", "adcc"], fracs=(0.6, 0.1, 0.3),
                                window="w30", return_arrays=True)
        a = meta["ad_test"]; y = meta["y_test"]; yh = meta["yhat_test"]
        r = np.abs(y - yh); o = np.argsort(a)
        col = {"split": "#888888", "weighted_ad": "#009E73", "adcc": "#D55E00"}
        lab = {"split": "Split CP", "weighted_ad": "ADR-CP (estimated weights)", "adcc": "ADCC-CP"}
        for m in ["split", "weighted_ad", "adcc"]:
            hw = (meta["arrays"][m]["hi"] - meta["arrays"][m]["lo"]) / 2
            ax.plot(a[o], hw[o], c=col[m], lw=2 if m == "adcc" else 1.3, label=lab[m])
        bins = np.quantile(a, np.linspace(0, 1, 9))
        mids, q90 = [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            s = (a >= lo) & (a <= hi)
            if s.sum() >= 15:
                mids.append(np.median(a[s])); q90.append(np.quantile(r[s], 0.9))
        ax.scatter(mids, q90, c="k", s=18, zorder=4, label="Observed 90th pct |error| (test)")
        ax.set_title(t.upper(), loc="left"); ax.set_xlabel("AD coordinate a(x) (max Tanimoto to training)")
        summ[t] = {"q90_test_bins": [float(v) for v in q90], "a_mid": [float(v) for v in mids]}
    axes[0].set_ylabel("Interval half-width (log units)")
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"fig_adcc_curve.{ext}", dpi=300)
    json.dump(summ, open("results/ad_curve.json", "w"), indent=1)


if __name__ == "__main__":
    main()
