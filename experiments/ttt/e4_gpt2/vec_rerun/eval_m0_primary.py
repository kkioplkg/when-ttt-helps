"""Primary source-model (m0) clean evaluation with a per-example retained record.

is2-R13 finding 2 asks for the primary m0 evaluation records or source
checkpoints behind the reported clean accuracies, and notes that a downstream
audit JSON repeating the values "is repetition rather than independent
evidence".

This script produces the missing artefact *type*: a standalone, seeded, clean
test-set evaluation of a source checkpoint that writes

  * a per-example record  (index, true label, predicted label, correct flag,
    max softmax probability, and the loss), and
  * a summary            (accuracy, mean loss, per-class accuracy, counts),

so the reported clean accuracy is verifiable from a primary record rather than
from a training run's own logging.

It evaluates whatever architecture the checkpoint declares, using the SAME test
transform as the published protocol (experiments/ttt/e2_cifar/data.py
`test_transforms`: ToTensor + per-dataset Normalize, no augmentation,
shuffle=False), so the number is comparable to the published one.
"""
import argparse
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.utils import save_json, set_seed, run_meta  # noqa: E402
from e2_cifar.data import MEAN, STD, get_test_loader  # noqa: E402
from e2_cifar.models import build_model, rotate_batch  # noqa: E402


def npy_test_loader(dataset, root, batch_size=256):
    """Test loader over the retained extracted arrays.

    Reproduces `e2_cifar.data.test_transforms` exactly -- ToTensor is a divide
    by 255 plus an HWC->CHW permute, then a per-channel Normalize -- and keeps
    shuffle=False, so the example order matches the torchvision loader the
    published protocol used.
    """
    from torch.utils.data import DataLoader, TensorDataset
    x = np.load(os.path.join(root, f"{dataset}_np", "test_x.npy"))
    y = np.load(os.path.join(root, f"{dataset}_np", "test_y.npy"))
    t = torch.from_numpy(x).permute(0, 3, 1, 2).float().div_(255.0)
    m = torch.tensor(MEAN[dataset]).view(1, 3, 1, 1)
    s = torch.tensor(STD[dataset]).view(1, 3, 1, 1)
    t = (t - m) / s
    ds = TensorDataset(t, torch.from_numpy(y).long())
    return DataLoader(ds, batch_size=batch_size, shuffle=False)


@torch.no_grad()
def evaluate_per_example(model, loader, device, ssl=False):
    model.eval()
    rows = []
    rot_correct = rot_total = 0
    idx = 0
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        logits = model(x).float()
        prob = F.softmax(logits, dim=1)
        loss = F.cross_entropy(logits, y, reduction="none")
        pred = logits.argmax(1)
        conf, _ = prob.max(1)
        for j in range(y.numel()):
            rows.append({"i": idx + j,
                         "y": int(y[j].item()),
                         "pred": int(pred[j].item()),
                         "ok": int(pred[j].item() == y[j].item()),
                         "conf": round(float(conf[j].item()), 6),
                         "loss": round(float(loss[j].item()), 6)})
        idx += y.numel()
        if ssl:
            xr, yr = rotate_batch(x)
            rot_correct += (model.forward_ssl(xr).argmax(1) == yr).sum().item()
            rot_total += yr.numel()
    return rows, (rot_correct / rot_total if rot_total else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--dataset", required=True, choices=["cifar10", "cifar100"])
    ap.add_argument("--arch", default="", choices=["", "resnet26ttt", "wrn2810"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    set_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    blob = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    ck_args = blob.get("args", {}) if isinstance(blob, dict) else {}
    arch = args.arch or ck_args.get("arch")
    dataset = args.dataset or ck_args.get("dataset")
    if arch is None:
        raise SystemExit("checkpoint declares no arch; pass --arch")
    nc = 10 if dataset == "cifar10" else 100

    model = build_model(arch, nc).to(device)
    state = blob["model"] if isinstance(blob, dict) and "model" in blob else blob
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        print(f"[m0] WARNING load_state_dict missing={len(missing)} "
              f"unexpected={len(unexpected)}", flush=True)

    npy_dir = os.path.join(args.data_root, f"{dataset}_np", "test_x.npy")
    if os.path.exists(npy_dir):
        print(f"[m0] test set from retained arrays {npy_dir}", flush=True)
        loader = npy_test_loader(dataset, args.data_root)
        source = "retained_npy"
    else:
        loader = get_test_loader(dataset, args.data_root)
        source = "torchvision"
    rows, rot_acc = evaluate_per_example(model, loader, device,
                                         ssl=(arch == "resnet26ttt"))

    ok = np.asarray([r["ok"] for r in rows])
    ys = np.asarray([r["y"] for r in rows])
    losses = np.asarray([r["loss"] for r in rows])
    per_class = {int(c): float(ok[ys == c].mean()) for c in sorted(set(ys.tolist()))}
    acc = float(ok.mean())
    # Wilson 95% interval on the accuracy of n independent test examples.
    n = len(ok)
    z = 1.959963984540054
    d = 1 + z * z / n
    centre = (acc + z * z / (2 * n)) / d
    half = z * np.sqrt(acc * (1 - acc) / n + z * z / (4 * n * n)) / d
    summary = {
        "checkpoint": os.path.basename(args.ckpt),
        "checkpoint_sha256": None,
        "arch": arch, "dataset": dataset, "eval_seed": args.seed,
        "test_set_source": source,
        "n_examples": int(n),
        "n_correct": int(ok.sum()),
        "clean_test_acc": acc,
        "clean_test_acc_wilson95": [float(centre - half), float(centre + half)],
        "mean_ce_loss": float(losses.mean()),
        "rot_acc": rot_acc,
        "per_class_acc": per_class,
        "checkpoint_train_args": ck_args,
        "meta": run_meta(args),
    }
    import hashlib
    h = hashlib.sha256()
    with open(args.ckpt, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    summary["checkpoint_sha256"] = h.hexdigest()

    tag = args.tag or os.path.splitext(os.path.basename(args.ckpt))[0]
    os.makedirs(args.out_dir, exist_ok=True)
    save_json(summary, os.path.join(args.out_dir, f"m0_eval_{tag}_summary.json"))
    save_json({"schema": ["i", "y", "pred", "ok", "conf", "loss"],
               "checkpoint": os.path.basename(args.ckpt),
               "checkpoint_sha256": summary["checkpoint_sha256"],
               "dataset": dataset, "arch": arch,
               "n": int(n), "examples": rows},
              os.path.join(args.out_dir, f"m0_eval_{tag}_per_example.json"))
    print(f"[m0] {tag}: acc={acc:.4f} ({int(ok.sum())}/{n}) rot={rot_acc} "
          f"loss={losses.mean():.4f}", flush=True)


if __name__ == "__main__":
    main()
