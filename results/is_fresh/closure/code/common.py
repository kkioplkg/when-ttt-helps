"""Shared helpers for the theory-closure suite (P1 binary sign law, P2 A2/Jacobian).

Design rules, enforced across every script in this package:

1.  Every measured quantity is a quantity that appears in the STATEMENT of the
    theorem or assumption being closed.  Where a script computes something that
    is merely related to such a quantity, the name carries a `_proxy` suffix and
    the value never enters a headline number.
2.  The two sides of an identity are always computed by INDEPENDENT routes.  In
    particular `grad_H` and `grad_R` are obtained by autograd on the respective
    losses, never by scaling `grad_s` with the theorem's own coefficients; the
    theorem's factorization is then a testable residual, not an input.
3.  Fresh seeds in the 20260901+ range, disjoint from every seed used by the
    original pipeline (0, 1, 2, 42, 43, 100+, 999+) and by `is_fresh`
    (20260801-20260807).
4.  Labels are used for MEASUREMENT ONLY.  No adaptation objective ever sees a
    label.
5.  No absolute machine path and no host identity is ever written into a record;
    provenance fields go through `rel()`.
"""
import gzip
import json
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_TTT = os.path.dirname(_HERE)                       # experiments/ttt
if _TTT not in sys.path:
    sys.path.insert(0, _TTT)

REPO_DIR = os.path.abspath(os.path.join(_TTT, "..", ".."))

# ---- fresh seeds (20260901+) -------------------------------------------------
MODEL_SEEDS = [20260901, 20260902, 20260903]

# ---- the three class pairs, FIXED before any measurement --------------------
# CIFAR-10 class order: 0 airplane 1 automobile 2 bird 3 cat 4 deer 5 dog
#                       6 frog 7 horse 8 ship 9 truck
PAIRS = {
    "auto_frog":  (1, 6),     # easy
    "plane_ship": (0, 8),     # medium (shared sky/sea background)
    "cat_dog":    (3, 5),     # hard (canonical confusable pair)
}

CORRUPTIONS = ["gaussian_noise", "fog", "contrast", "jpeg_compression"]
SEVERITIES = [1, 3, 5]

MEAN = np.array([0.4914, 0.4822, 0.4465], dtype=np.float32)
STD = np.array([0.2470, 0.2435, 0.2616], dtype=np.float32)


def rel(path):
    """Repository-relative POSIX form of `path`, for provenance fields."""
    p = os.path.abspath(path)
    try:
        r = os.path.relpath(p, REPO_DIR)
    except ValueError:
        return os.path.basename(p)
    r = r.replace("\\", "/")
    return os.path.basename(p) if r.startswith("../") else r


def _default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def save_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=_default)
    os.replace(tmp, path)
    print(f"[closure] wrote {rel(path)}", flush=True)
    return path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class RecordWriter:
    """Append-only gzipped JSONL sink for per-episode records.

    Every episode is retained.  The file is opened in append mode and flushed
    per cell so that a killed run leaves a valid prefix that `--resume` can
    count.
    """

    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._f = gzip.open(path, "at", encoding="utf-8")
        self.n = 0

    def write(self, rec):
        self._f.write(json.dumps(rec, sort_keys=True, default=_default) + "\n")
        self.n += 1

    def flush(self):
        self._f.flush()

    def close(self):
        self._f.close()


def read_records(path):
    """Yield records from a (possibly truncated) gzipped JSONL file.

    A file that is still being appended to, or that a killed run left
    mid-member, raises EOFError from the gzip layer rather than returning short
    -- so analysing a live run has to treat that as "end of the valid prefix",
    exactly like a half-written JSON line.  Both are caught; neither is allowed
    to look like an empty file, because a silently empty read would turn a
    crashed run into a clean zero-violation result.
    """
    with gzip.open(path, "rt", encoding="utf-8") as f:
        while True:
            try:
                line = f.readline()
            except (EOFError, gzip.BadGzipFile, OSError):
                return                       # truncated tail; prefix is valid
            if not line:
                return
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                return


def heartbeat(path, payload):
    """Overwrite a small status file so a watcher can see liveness."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    payload = dict(payload)
    payload["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, default=_default)
    os.replace(tmp, path)


def _scrub_paths(d):
    """Replace absolute filesystem paths in recorded arguments by their
    repository-relative form.

    A result record that carries `/mnt/.../home/<user>/...` pins the run to one
    machine and one account: the path resolves nowhere in an extracted archive,
    and it leaks the host account name into a shippable artifact.  The suite's
    `rel()` convention exists for exactly this, and the recorded argv is the one
    place it was easy to forget.
    """
    out = {}
    for k, v in d.items():
        if isinstance(v, str) and (v.startswith("/") or (len(v) > 2 and v[1] == ":")):
            out[k] = rel(v)
        else:
            out[k] = v
    return out


def run_meta(args, extra=None):
    import torch
    m = {
        "argv": _scrub_paths(vars(args) if hasattr(args, "__dict__") else dict(args)),
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "torch": torch.__version__,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "code": rel(_HERE),
    }
    if extra:
        m.update(extra)
    return m


def set_seed(seed: int):
    import random
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------------- data -------

def _normalize(x_uint8):
    """(N,32,32,3) uint8 -> (N,3,32,32) float32, CIFAR-10 normalized."""
    x = x_uint8.astype(np.float32) / 255.0
    x = (x - MEAN) / STD
    return np.ascontiguousarray(x.transpose(0, 3, 1, 2))


def load_cifar10_np(data_root):
    d = os.path.join(data_root, "cifar10_np")
    return (np.load(os.path.join(d, "train_x.npy")),
            np.load(os.path.join(d, "train_y.npy")),
            np.load(os.path.join(d, "test_x.npy")),
            np.load(os.path.join(d, "test_y.npy")))


def binary_train_set(data_root, pair):
    """Train images/labels for a class pair, labels remapped to {0,1}.

    Label convention, fixed here and used everywhere downstream:
        class index PAIRS[pair][1]  ->  binary label 1  ("class 1")
        class index PAIRS[pair][0]  ->  binary label 0
    so `p := p_1` of Theorem 5.2 is the model's probability for the SECOND
    class of the tuple.
    """
    c0, c1 = PAIRS[pair]
    tx, ty, _, _ = load_cifar10_np(data_root)
    m = (ty == c0) | (ty == c1)
    x = tx[m]
    y = (ty[m] == c1).astype(np.int64)
    return x, y


def binary_test_ids(data_root, pair):
    """Indices into the 10 000-image CIFAR-10 test set belonging to the pair,
    plus their binary labels.  CIFAR-10-C severity blocks are corrupted copies
    of the SAME test identities in the SAME order, so these indices address the
    corrupted sets too."""
    c0, c1 = PAIRS[pair]
    _, _, _, sy = load_cifar10_np(data_root)
    idx = np.nonzero((sy == c0) | (sy == c1))[0]
    lab = (sy[idx] == c1).astype(np.int64)
    return idx, lab


def clean_test_images(data_root, ids):
    _, _, sx, _ = load_cifar10_np(data_root)
    return _normalize(sx[ids])


def corrupted_test_images(data_root, corruption, severity, ids):
    """CIFAR-10-C images for the given test identities at one severity.

    Asserts the block/label alignment rather than assuming it: the labels file
    must reproduce the clean test labels inside every severity block, which is
    the property that makes `ids` meaningful across corruptions.
    """
    cdir = os.path.join(data_root, "CIFAR-10-C")
    lab = np.load(os.path.join(cdir, "labels.npy"))
    _, _, _, sy = load_cifar10_np(data_root)
    i0 = (severity - 1) * 10000
    block_lab = lab[i0:i0 + 10000]
    if not np.array_equal(block_lab.astype(np.int64), sy.astype(np.int64)):
        raise RuntimeError(
            f"CIFAR-10-C block alignment failed for severity {severity}: the "
            "severity block's labels do not equal the clean test labels")
    x = np.load(os.path.join(cdir, f"{corruption}.npy"), mmap_mode="r")
    sel = np.asarray(x[i0:i0 + 10000][ids])
    return _normalize(sel)


def shift_cells():
    """The 13 shift conditions: clean + 4 corruptions x 3 severities."""
    cells = [("clean", 0)]
    for c in CORRUPTIONS:
        for s in SEVERITIES:
            cells.append((c, s))
    return cells
