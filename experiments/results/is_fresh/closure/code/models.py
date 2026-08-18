"""Models for the theory-closure suite.

`ResNet26GN` is the MAIN PATH of the manuscript's existing `ResNet26TTT`
(`experiments/ttt/e2_cifar/models.py`) -- same blocks, same widths, same
GroupNorm, imported from that module rather than re-typed -- with the rotation
branch removed.  The branch is removed rather than left unused because P1
measures gradients on parameter subsets including `all`, and an untrained,
never-evaluated branch would put dead coordinates into that subset and make the
`all` variant of the identity check meaningless.

GroupNorm (not BatchNorm) is what makes the N = 1 protocol of Theorem 5.2 well
posed: the forward map is a function of the single instance, with no batch
statistics.  The BatchNorm architecture is still available for the robustness
arm, run with frozen running statistics (eval mode), which is the theory-aligned
protocol the manuscript already uses.
"""
import os
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

_TTT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TTT not in sys.path:
    sys.path.insert(0, _TTT)

from e2_cifar.models import BasicBlockGN, WRN2810, _group, gn  # noqa: E402,F401


class ResNet26GN(nn.Module):
    """ResNet-26 (n=4 basic blocks/group, widths 16/32/64), GroupNorm, K-way head."""

    def __init__(self, num_classes=2):
        super().__init__()
        n = 4
        self.conv1 = nn.Conv2d(3, 16, 3, 1, 1, bias=False)
        self.n1 = gn(16)
        self.group1 = _group(16, 16, n, 1)
        self.group2 = _group(16, 32, n, 2)
        self.group3 = _group(32, 64, n, 2)
        self.fc = nn.Linear(64, num_classes)

    def features(self, x):
        z = self.group2(self.group1(F.relu(self.n1(self.conv1(x)))))
        return F.adaptive_avg_pool2d(self.group3(z), 1).flatten(1)

    def forward(self, x):
        return self.fc(self.features(x))

    def encoder_named_params(self):
        for prefix in ["conv1", "n1", "group1", "group2"]:
            mod = getattr(self, prefix)
            for n_, p in mod.named_parameters():
                yield f"{prefix}.{n_}", p


class TemperedHead(nn.Module):
    """Divide the logits of a wrapped model by a fixed temperature T.

    This is a *model*, not a post-hoc rescaling of recorded numbers: the forward
    pass is `z(theta)/T`, so `s = (z_1 - z_2)/T` and `grad_theta s` is the true
    gradient of the tempered network.  Every hypothesis of Theorem 5.2 is a
    hypothesis about the network being differentiated, and that network is this
    one.  T is a constant, carries no parameters, and is never fitted.
    """

    def __init__(self, model, T: float):
        super().__init__()
        self.model = model
        self.T = float(T)

    def forward(self, x):
        return self.model(x) / self.T

    # subset selection must see through the wrapper
    def encoder_named_params(self):
        return self.model.encoder_named_params()


def build(arch, num_classes=2):
    if arch == "resnet26gn":
        return ResNet26GN(num_classes)
    if arch == "wrn2810":
        return WRN2810(num_classes)
    raise ValueError(arch)


def norm_affine_params(model):
    """(params, names) for normalization-layer affine parameters -- Tent's
    adapted subset, which is the subset Section 5 names."""
    named = []
    for mn, m in model.named_modules():
        if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, nn.GroupNorm, nn.LayerNorm)):
            for pn, p in m.named_parameters(recurse=False):
                named.append((f"{mn}.{pn}", p))
    return [p for _, p in named], [n for n, _ in named]


def subset_params(model, subset):
    """Adapted parameter subset.  'norm' is primary (Tent protocol); 'all' and
    'encoder' are the subset-invariance robustness arms."""
    if subset == "norm":
        return norm_affine_params(model)
    if subset == "all":
        named = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    elif subset == "encoder":
        base = model.model if isinstance(model, TemperedHead) else model
        if hasattr(base, "encoder_named_params"):
            named = list(base.encoder_named_params())
        else:
            named = [(n, p) for n, p in base.named_parameters()
                     if not n.startswith(("fc", "classifier", "head"))]
    else:
        raise ValueError(subset)
    return [p for _, p in named], [n for n, _ in named]


def flat_grad(params):
    gs = []
    for p in params:
        gs.append(torch.zeros_like(p).reshape(-1) if p.grad is None
                  else p.grad.detach().reshape(-1))
    return torch.cat(gs)
