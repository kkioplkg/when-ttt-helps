"""Adaptation methods + alignment measurement shared by E2/E3.

Episodic protocol: model state is snapshotted before each episode and restored
after. All methods expose:
    ssl_loss_fn(model, x, rng_seed) -> scalar loss   (the adaptation objective)
and adaptation runs plain SGD on a parameter subset.

Measurement protocol (EXPERIMENT_PLAN.md "Measurement protocol"):
    alpha  = cos( E_xi grad ssl_loss , grad task_loss ) on the adapted subset
    sigma2 = E || g - E g ||^2 / || E g ||^2   (relative SSL gradient noise)
    y* is used ONLY for measurement/evaluation, never for adaptation.
"""
import copy

import numpy as np
import torch
import torch.nn.functional as F

from .utils import collect_params, flat_grad, cosine


# ---------------- SSL objectives ----------------

def rotation_loss(model, x, seed):
    """TTT rotation prediction: 4 SEEDED-random rotations of x as a batch
    (stochastic across seeds — required for sigma^2 estimation and ALTA
    replicas; the all-4-rotations variant is deterministic)."""
    g = torch.Generator(device="cpu").manual_seed(seed)
    ks = torch.randint(0, 4, (4 * x.size(0),), generator=g)
    xs, ys = [], []
    for j, k in enumerate(ks.tolist()):
        xs.append(torch.rot90(x[j % x.size(0)], k, dims=(1, 2)))
        ys.append(k)
    xr = torch.stack(xs)
    yr = torch.tensor(ys, dtype=torch.long, device=x.device)
    return F.cross_entropy(model.forward_ssl(xr), yr)


def masked_recon_loss(model, x, seed):
    """Masked reconstruction; requires model.forward_recon(x_masked) -> x_hat."""
    g = torch.Generator(device="cpu").manual_seed(seed)
    B, C, H, W = x.shape
    patch = 4
    mask = (torch.rand(B, 1, H // patch, W // patch, generator=g) < 0.5).float()
    mask = mask.repeat_interleave(patch, 2).repeat_interleave(patch, 3).to(x.device)
    x_in = x * (1 - mask)
    x_hat = model.forward_recon(x_in)
    return ((x_hat - x) ** 2 * mask).sum() / mask.sum().clamp(min=1) / C


def entropy_loss(model, x, seed):
    """Tent: mean prediction entropy (deterministic given x)."""
    logits = model(x)
    logp = F.log_softmax(logits, dim=1)
    return -(logp.exp() * logp).sum(1).mean()


def pseudo_label_loss(model, x, seed):
    """Hard pseudo-label self-training (labels from current model, detached)."""
    logits = model(x)
    yhat = logits.argmax(1).detach()
    return F.cross_entropy(logits, yhat)


SSL_LOSSES = {"ttt_rot": rotation_loss, "ttt_mask": masked_recon_loss,
              "tent": entropy_loss, "pl": pseudo_label_loss}

# which parameter subset each method adapts (Tent protocol: norm affine only)
METHOD_SUBSET = {"ttt_rot": "encoder", "ttt_mask": "encoder",
                 "tent": "bn", "pl": "bn"}

# whether the SSL objective has intrinsic randomness (for sigma^2 estimation;
# deterministic objectives get sigma^2 from batch-member dispersion instead)
STOCHASTIC = {"ttt_rot": True, "ttt_mask": True, "tent": False, "pl": False}


# ---------------- measurement ----------------

def measure_alignment(model, x, y, method, n_draws=8, base_seed=0):
    """Return dict(alpha, sigma2_rel, gnorm_ssl, gnorm_task, frozen_loss).

    Gradients on the method's adapted subset. For deterministic objectives
    (tent/pl), sigma2 is estimated from per-sample gradient dispersion within
    the batch (the batch-composition noise of batch-TTA); for stochastic ones
    from SSL randomness draws.
    """
    params, _ = collect_params(model, METHOD_SUBSET[method])
    loss_fn = SSL_LOSSES[method]

    def grad_of(loss):
        model.zero_grad(set_to_none=True)
        loss.backward()
        return flat_grad(params).clone()

    # task gradient (y used for MEASUREMENT only)
    g_task = grad_of(F.cross_entropy(model(x), y))
    frozen_loss = float(F.cross_entropy(model(x), y).item())

    N = x.size(0)
    if STOCHASTIC[method]:
        gs = [grad_of(loss_fn(model, x, base_seed + i)) for i in range(n_draws)]
        G = torch.stack(gs)
        g_mean = G.mean(0)
        sigma2_point = float(((G - g_mean) ** 2).sum(1).mean().item())
        sigma2_batch = sigma2_point  # randomness is the draw, not the batch
    else:
        # batch-composition noise: per-sample gradients on an unbiased random
        # subset; the MEAN gradient is the exact full-batch gradient
        g_mean = grad_of(loss_fn(model, x, base_seed))
        if N > 1:
            sub = np.random.default_rng(base_seed).choice(
                N, size=min(16, N), replace=False)
            gs = [grad_of(loss_fn(model, x[i:i + 1], base_seed)) for i in sub]
            G = torch.stack(gs)
            sigma2_point = float(((G - g_mean) ** 2).sum(1).mean().item())
            sigma2_batch = sigma2_point / N   # variance of the batch mean
        else:
            sigma2_point = sigma2_batch = 0.0  # deterministic at N=1
    gm2 = max(float((g_mean ** 2).sum().item()), 1e-20)
    model.zero_grad(set_to_none=True)
    return {"alpha": cosine(g_mean, g_task),
            "sigma2_rel": sigma2_point / gm2,
            "sigma2_batch_rel": sigma2_batch / gm2,
            "gnorm_ssl": float(g_mean.norm().item()),
            "gnorm_task": float(g_task.norm().item()),
            "frozen_loss": frozen_loss}


# ---------------- episodic adaptation ----------------

class EpisodeRunner:
    """Snapshot/restore + SGD adaptation on the method's parameter subset."""

    def __init__(self, model, method, lr, momentum=0.9):
        self.model = model
        self.method = method
        self.lr = lr
        self.momentum = momentum
        self.loss_fn = SSL_LOSSES[method]
        self.params, self.names = collect_params(model, METHOD_SUBSET[method])
        self._snap = None

    def snapshot(self):
        self._snap = [p.detach().clone() for p in self.params]
        self._bn_stats = {k: v.clone() for k, v in self.model.state_dict().items()
                          if "running_" in k or "num_batches" in k}

    def restore(self):
        with torch.no_grad():
            for p, s in zip(self.params, self._snap):
                p.copy_(s)
        msd = self.model.state_dict()
        for k, v in self._bn_stats.items():
            msd[k].copy_(v)

    def adapt(self, x, steps, seed=0, record_logits_at=None):
        """SGD on ssl loss; returns list of logits snapshots if requested."""
        opt = torch.optim.SGD(self.params, lr=self.lr, momentum=self.momentum)
        recorded = []
        for t in range(1, steps + 1):
            loss = self.loss_fn(self.model, x, seed * 10007 + t)
            self.model.zero_grad(set_to_none=True)   # clear ALL params, not
            loss.backward()                          # just the adapted subset
            opt.step()
            if record_logits_at and t in record_logits_at:
                with torch.no_grad():
                    recorded.append((t, self.model(x).detach().cpu()))
        return recorded
