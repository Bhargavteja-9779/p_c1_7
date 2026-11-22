"""Compact message-passing graph neural network (D-MPNN-style) for molecular property
regression, as a modern graph-based baseline. CPU-only, small by design.

Interface mirrors RegressorWrapper: fit(smiles, y) / predict(smiles). The conformal
layer is model-agnostic and consumes only the predictions, so the GNN plugs into the
same pipeline as RF/LightGBM/MLP.
"""
from __future__ import annotations
import numpy as np

try:
    import torch
    import torch.nn as nn
    from rdkit import Chem
    _HAS = True
except Exception:  # pragma: no cover
    _HAS = False

_ATOM_LIST = list(range(1, 54))  # atomic numbers H..I
_HYB = ["SP", "SP2", "SP3", "SP3D", "SP3D2", "UNSPECIFIED"]


def _onehot(v, choices):
    x = [0.0] * (len(choices) + 1)
    x[choices.index(v) if v in choices else -1] = 1.0
    return x


def _atom_features(a):
    return (_onehot(a.GetAtomicNum(), _ATOM_LIST)
            + _onehot(a.GetDegree(), [0, 1, 2, 3, 4, 5])
            + _onehot(a.GetFormalCharge(), [-1, 0, 1])
            + _onehot(str(a.GetHybridization()), _HYB)
            + [float(a.GetIsAromatic()), float(a.GetTotalNumHs())])


def _mol_graph(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None or m.GetNumAtoms() == 0:
        return None
    af = np.array([_atom_features(a) for a in m.GetAtoms()], dtype=np.float32)
    src, dst = [], []
    for b in m.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        src += [i, j]; dst += [j, i]
    if not src:  # single atom / no bonds: self loop
        src, dst = [0], [0]
    return af, np.array(src), np.array(dst)


class _MPNN(nn.Module):
    def __init__(self, in_dim, hidden=128, steps=3):
        super().__init__()
        self.lin_in = nn.Linear(in_dim, hidden)
        self.msg = nn.ModuleList([nn.Linear(hidden, hidden) for _ in range(steps)])
        self.upd = nn.ModuleList([nn.GRUCell(hidden, hidden) for _ in range(steps)])
        self.steps = steps
        self.out = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    def forward(self, af, src, dst, batch, n_graphs):
        h = torch.relu(self.lin_in(af))
        for t in range(self.steps):
            m = torch.zeros_like(h)
            msg = self.msg[t](h)[src]
            m.index_add_(0, dst, msg)
            h = self.upd[t](m, h)
        # mean readout per graph
        pooled = torch.zeros(n_graphs, h.shape[1])
        cnt = torch.zeros(n_graphs, 1)
        pooled.index_add_(0, batch, h)
        cnt.index_add_(0, batch, torch.ones(h.shape[0], 1))
        pooled = pooled / cnt.clamp(min=1)
        return self.out(pooled).squeeze(-1)


class GNNRegressor:
    name = "gnn"

    def __init__(self, seed=0, hidden=128, steps=3, epochs=40, lr=1e-3, batch_size=64):
        if not _HAS:
            raise RuntimeError("torch/rdkit required for GNN")
        self.seed = seed; self.hidden = hidden; self.steps = steps
        self.epochs = epochs; self.lr = lr; self.batch_size = batch_size

    def _featurize(self, smiles):
        graphs = []
        for s in smiles:
            g = _mol_graph(s)
            graphs.append(g)
        return graphs

    def _batch(self, graphs, idx):
        afs, srcs, dsts, batch = [], [], [], []
        off = 0
        for bi, gi in enumerate(idx):
            af, src, dst = graphs[gi]
            afs.append(af); srcs.append(src + off); dsts.append(dst + off)
            batch.append(np.full(len(af), bi)); off += len(af)
        return (torch.tensor(np.vstack(afs)), torch.tensor(np.concatenate(srcs)),
                torch.tensor(np.concatenate(dsts)), torch.tensor(np.concatenate(batch)), len(idx))

    def fit(self, smiles, y):
        torch.manual_seed(self.seed); np.random.seed(self.seed)
        self.graphs = self._featurize(smiles)
        ok = [i for i, g in enumerate(self.graphs) if g is not None]
        in_dim = self.graphs[ok[0]][0].shape[1]
        self.model = _MPNN(in_dim, self.hidden, self.steps)
        y = np.asarray(y, dtype=np.float32)
        self.y_mean, self.y_std = float(y.mean()), float(y.std() + 1e-6)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        lossf = nn.MSELoss()
        rng = np.random.default_rng(self.seed)
        self.model.train()
        for ep in range(self.epochs):
            rng.shuffle(ok)
            for i in range(0, len(ok), self.batch_size):
                idx = ok[i:i + self.batch_size]
                if not idx:
                    continue
                af, src, dst, batch, ng = self._batch(self.graphs, idx)
                target = torch.tensor((y[idx] - self.y_mean) / self.y_std)
                opt.zero_grad()
                pred = self.model(af, src, dst, batch, ng)
                loss = lossf(pred, target)
                loss.backward(); opt.step()
        return self

    def predict(self, smiles):
        graphs = self._featurize(smiles)
        self.model.eval()
        out = np.full(len(smiles), self.y_mean, dtype=np.float32)
        ok = [i for i, g in enumerate(graphs) if g is not None]
        with torch.no_grad():
            for i in range(0, len(ok), 256):
                idx = ok[i:i + 256]
                af, src, dst, batch, ng = self._batch(graphs, idx)
                p = self.model(af, src, dst, batch, ng).numpy()
                for k, j in enumerate(idx):
                    out[j] = p[k] * self.y_std + self.y_mean
        return out

    def ensemble_std(self, smiles):
        return None
