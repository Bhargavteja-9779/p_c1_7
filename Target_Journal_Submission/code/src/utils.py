"""Shared utilities: seeding, hardware detection, config, logging, IO."""
from __future__ import annotations
import os, sys, json, random, logging, platform, hashlib
from pathlib import Path
import numpy as np

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


def set_global_seed(seed: int) -> None:
    """Deterministic seeding for stdlib, numpy. (Models receive the seed explicitly.)"""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)


def detect_hardware() -> dict:
    """Report available compute. CPU-only environments are fully supported; CUDA/MPS
    are detected if torch is present but are NOT required by this pipeline."""
    info = {"platform": platform.platform(), "python": sys.version.split()[0],
            "n_cpu": os.cpu_count(), "device": "cpu"}
    try:
        import torch  # optional
        if torch.cuda.is_available():
            info["device"] = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            info["device"] = "mps"
        info["torch"] = torch.__version__
    except Exception:
        info["torch"] = None
    return info


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if yaml is None:
        raise RuntimeError("pyyaml is required to read the config")
    with open(path) as f:
        return yaml.safe_load(f)


def apply_quick_overrides(cfg: dict) -> dict:
    """Reduce the workload for a fast pipeline-correctness run."""
    cfg = json.loads(json.dumps(cfg))  # deep copy
    cfg["seed_list"] = [0, 1, 2]
    cfg["alphas"] = [0.1]
    cfg["primary_alpha"] = 0.1
    cfg["models"] = ["lgbm"]
    cfg["primary_model"] = "lgbm"
    cfg["ablation_models"] = ["rf"]
    cfg["ablation_seeds"] = 2
    cfg["split"]["n_ad_strata"] = 2
    cfg["scaffold_datasets"] = ["esol", "freesolv"]
    cfg["temporal_datasets"] = ["chembl_vegfr2"]
    cfg["sweep_datasets"] = ["bace"]
    cfg["robustness"]["calib_sizes"] = [100, 200]
    cfg["robustness"]["shift_sweep_quantiles"] = [0.0, 0.5, 0.9]
    cfg["_mode"] = "quick"
    return cfg


def get_logger(name: str = "adwcp", logfile: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if logfile:
        Path(logfile).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logfile)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def ensure_dir(p: str | Path) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_json(obj, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# Repo root = parent of src/
ROOT = Path(__file__).resolve().parents[1]
