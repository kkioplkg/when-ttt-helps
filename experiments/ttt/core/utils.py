"""Shared utilities: seeding, result IO, parameter-subset selection.

`torch` is imported lazily, inside the functions that need it, rather than at
module scope.  `save_json` / `_np_default` are pure-numpy, and the analysis
half of the pipeline (`experiments/ttt/is_fresh/*`) reaches this module only
for those two through `run_e1`.  A module-scope `import torch` therefore made
the five documented re-analysis commands -- f7, f8b, f11, f29, f31, i.e. every
check `make_release_zip.py --verify` runs -- fail on an environment without
the ML stack, even though none of them touches a tensor.  The model-side
helpers below still require torch and raise the ordinary ImportError if it is
absent.
"""
import json
import os
import random
import time

import numpy as np


def set_seed(seed: int):
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def save_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=_np_default)
    os.replace(tmp, path)


def _np_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not serializable: {type(o)}")


def run_meta(args) -> dict:
    import torch
    return {
        "argv": vars(args) if hasattr(args, "__dict__") else dict(args),
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "torch": torch.__version__,
        "cuda": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }


def collect_params(model, subset: str):
    """Return (params, names) for the adaptation subset.

    subset: 'bn' -> BatchNorm/GroupNorm/LayerNorm affine only (Tent protocol)
            'encoder' -> parameters flagged model.encoder_params() if present,
                         else everything except final classifier
            'all' -> all parameters
    """
    import torch
    if subset == "all":
        named = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    elif subset == "bn":
        named = []
        for mn, m in model.named_modules():
            if isinstance(m, (torch.nn.BatchNorm1d, torch.nn.BatchNorm2d,
                              torch.nn.GroupNorm, torch.nn.LayerNorm)):
                for pn, p in m.named_parameters(recurse=False):
                    named.append((f"{mn}.{pn}", p))
    elif subset == "encoder":
        if hasattr(model, "encoder_named_params"):
            named = list(model.encoder_named_params())
        else:
            named = [(n, p) for n, p in model.named_parameters()
                     if not n.startswith(("fc", "classifier", "head"))]
    else:
        raise ValueError(subset)
    names = [n for n, _ in named]
    params = [p for _, p in named]
    return params, names


def flat_grad(params):
    """Concatenate .grad of params into one vector (zeros where grad is None)."""
    import torch
    gs = []
    for p in params:
        gs.append(torch.zeros_like(p).view(-1) if p.grad is None else p.grad.detach().view(-1))
    return torch.cat(gs)


def cosine(a, b) -> float:
    import torch
    na, nb = a.norm().item(), b.norm().item()
    if na == 0 or nb == 0:
        return 0.0
    return float(torch.dot(a, b).item() / (na * nb))
