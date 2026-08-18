"""E4 — GPT-2 single-document TTT: prefix next-token SSL -> continuation ppl.

Protocol per document (EXPERIMENT_PLAN.md M4; THEORY_CORE.md section 0/5):
  tokens[:768]      = PREFIX      (the only thing adaptation ever sees)
  tokens[768:1024]  = CONTINUATION (measurement / evaluation ONLY)

  ell_ssl  = next-token CE on a random contiguous 512-token sub-window of the
             prefix; the window offset is the SSL randomness xi (fresh per step).
  eval     = continuation CE (no_grad forward on the full 1024 tokens; causal
             attention means prefix-position logits never see the continuation).
  alpha    = cos(mean_xi grad ell_ssl(theta0), grad cont-CE(theta0)) on the
             adapted parameter subset (continuation labels = measurement only).
  sigma2   = relative variance of the window gradients over --n-draws draws.
  delta    = frozen cont CE minus wikitext-domain mean frozen cont CE (proxy;
             wikitext runs write wikitext_ref_s<seed>.json, other domains pass
             it via --ref-file; missing ref -> delta_proxy=null, post-process).
  ALTA     = alta_run, K=3 replicas differing ONLY in their window-sampling
             streams. Prediction vector for dispersion/drift = log-prob the
             model assigns to the LAST 32 PREFIX tokens (teacher-forced on the
             prefix): strictly label-free and continuation-free at deployment.
  oracle   = argmin over t in {0..steps} of the replica-mean cont-CE curve
             (uses continuation labels; upper reference only).

Episodic: adapted params are snapshotted at load and restored per replica/doc.
One job = one (domain, seed); output one JSON with per-document records.
"""
import argparse
import json
import os
import sys

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", "workdir/hf_cache")

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.utils import save_json, set_seed, run_meta, flat_grad, cosine  # noqa: E402
from core.alta import ALTAConfig, alta_run  # noqa: E402

PREFIX_LEN = 768
CONT_LEN = 256
WINDOW = 512
TAIL = 32  # prefix-tail positions used as the ALTA prediction vector

DOMAINS = ["pubmed", "code", "legal", "wikitext"]
DEFAULT_LR = {"ln": 1e-4, "lora": 1e-3}


# ---------------- model / parameter subsets ----------------

class LoRAQV(torch.nn.Module):
    """LoRA r=8 on the q and v column blocks of GPT-2's fused attn c_attn.

    c_attn is transformers Conv1D: out = x @ W + b, W (n_embd, 3*n_embd) with
    columns [q | k | v]. B is zero-init, so theta0 predictions are unchanged.
    """

    def __init__(self, base, n_embd, r=8, alpha=16.0):
        super().__init__()
        self.base = base
        self.n = n_embd
        self.scale = alpha / r
        self.lora_Aq = torch.nn.Parameter(torch.randn(n_embd, r) * 0.02)
        self.lora_Bq = torch.nn.Parameter(torch.zeros(r, n_embd))
        self.lora_Av = torch.nn.Parameter(torch.randn(n_embd, r) * 0.02)
        self.lora_Bv = torch.nn.Parameter(torch.zeros(r, n_embd))

    def forward(self, x):
        out = self.base(x)
        dq = (x @ self.lora_Aq) @ self.lora_Bq * self.scale
        dv = (x @ self.lora_Av) @ self.lora_Bv * self.scale
        return torch.cat([out[..., :self.n] + dq,
                          out[..., self.n:2 * self.n],
                          out[..., 2 * self.n:] + dv], dim=-1)


def load_model_and_subset(adapt, device, lora_r, lora_alpha):
    from transformers import GPT2LMHeadModel
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.to(device).eval()  # eval: no dropout; randomness = window sampling only
    for p in model.parameters():
        p.requires_grad_(False)
    if adapt == "ln":
        named = []
        for mn, m in model.named_modules():
            if isinstance(m, torch.nn.LayerNorm):
                for pn, p in m.named_parameters(recurse=False):
                    named.append((f"{mn}.{pn}", p))
    elif adapt == "lora":
        n_embd = model.config.n_embd
        for block in model.transformer.h:
            block.attn.c_attn = LoRAQV(block.attn.c_attn, n_embd,
                                       r=lora_r, alpha=lora_alpha).to(device)
        named = [(n, p) for n, p in model.named_parameters() if "lora_" in n]
    else:
        raise ValueError(adapt)
    params = [p for _, p in named]
    for p in params:
        p.requires_grad_(True)
    names = [n for n, _ in named]
    return model, params, names


def restore(params, snap):
    with torch.no_grad():
        for p, s in zip(params, snap):
            p.copy_(s)


# ---------------- data ----------------

def load_docs(path, tok, n_docs):
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            ids = tok(json.loads(line)["text"],
                      add_special_tokens=False)["input_ids"]
            if len(ids) >= PREFIX_LEN + CONT_LEN:
                docs.append(ids[:PREFIX_LEN + CONT_LEN])
            if len(docs) >= n_docs:
                break
    return docs


# ---------------- measurement / eval ----------------

def cont_loss_from_logits(logits, full):
    """CE over the 256 continuation tokens (logits row i predicts token i+1)."""
    rows = logits[PREFIX_LEN - 1:PREFIX_LEN + CONT_LEN - 1]
    return F.cross_entropy(rows, full[0, PREFIX_LEN:])


@torch.no_grad()
def eval_doc(model, full):
    """One forward -> (cont CE, prefix-tail log-prob vector for ALTA).

    The tail vector uses logits at prefix positions only (causal mask), so it
    is available at deployment without the continuation.
    """
    logits = model(full).logits[0].float()
    cont_ce = float(cont_loss_from_logits(logits, full).item())
    rows = logits[PREFIX_LEN - TAIL - 1:PREFIX_LEN - 1]
    lp = F.log_softmax(rows, dim=-1)
    tgt = full[0, PREFIX_LEN - TAIL:PREFIX_LEN]
    tail = lp[torch.arange(TAIL, device=lp.device), tgt].cpu().numpy()
    return cont_ce, tail


def window_loss(model, prefix_t, off):
    w = prefix_t[:, off:off + WINDOW]
    return model(w, labels=w).loss


def measure_alignment_lm(model, params, full, prefix_t, rng, n_draws):
    """alpha / sigma2_rel / grad norms at theta0 (shared protocol)."""
    def grad_of(loss):
        model.zero_grad(set_to_none=True)
        loss.backward()
        return flat_grad(params).clone()

    logits = model(full).logits[0].float()
    g_task = grad_of(cont_loss_from_logits(logits, full))
    gs = []
    for _ in range(n_draws):
        off = int(rng.integers(0, PREFIX_LEN - WINDOW + 1))
        gs.append(grad_of(window_loss(model, prefix_t, off)))
    G = torch.stack(gs)
    g_mean = G.mean(0)
    sigma2_rel = float(((G - g_mean) ** 2).sum(1).mean().item()
                       / max(float((g_mean ** 2).sum().item()), 1e-20))
    model.zero_grad(set_to_none=True)
    return {"alpha": cosine(g_mean, g_task),
            "sigma2_rel": sigma2_rel,
            "gnorm_ssl": float(g_mean.norm().item()),
            "gnorm_task": float(g_task.norm().item())}


# ---------------- per-document episode ----------------

def run_document(model, params, snap, ids, doc_i, args, device):
    full = torch.tensor(ids, device=device).unsqueeze(0)
    prefix_t = full[:, :PREFIX_LEN]

    frozen_ce, pred0 = eval_doc(model, full)
    meas_rng = np.random.default_rng(args.seed * 9176 + doc_i * 31 + 7)
    meas = measure_alignment_lm(model, params, full, prefix_t,
                                meas_rng, args.n_draws)

    K = 1 if args.stopping == "fixed" else 3
    rep_ce, rep_tails = [], []
    for k in range(K):
        restore(params, snap)
        opt = torch.optim.SGD(params, lr=args.lr, momentum=args.momentum)
        rng = np.random.default_rng(args.seed * 1000003 + doc_i * 97 + k * 13 + 1)
        ces, tails = [], []
        for _ in range(args.steps):
            off = int(rng.integers(0, PREFIX_LEN - WINDOW + 1))
            loss = window_loss(model, prefix_t, off)
            opt.zero_grad()
            loss.backward()
            opt.step()
            ce_t, tail_t = eval_doc(model, full)
            ces.append(ce_t)
            tails.append(tail_t)
        rep_ce.append(ces)
        rep_tails.append(tails)
    restore(params, snap)

    mean_ce = np.asarray(rep_ce).mean(axis=0)            # (steps,)
    curve = np.concatenate([[frozen_ce], mean_ce])       # index t = step t
    fixed = {str(t): float(curve[t]) for t in args.record_steps
             if t <= args.steps}

    t_star = int(np.argmin(curve))
    oracle = {"t_star": t_star, "cont_ce": float(curve[t_star])}

    alta = None
    if K >= 2:
        cfg = ALTAConfig(K=K, T_max=args.steps)
        state = [{"i": 0, "seq": r} for r in rep_tails]

        def mk(st):
            def fn():
                v = st["seq"][st["i"]]
                st["i"] += 1
                return v
            return fn
        tr = alta_run([mk(s) for s in state], cfg, pred0=pred0)
        alta = {"t_hat": int(tr.t_hat),
                "cont_ce": float(curve[tr.t_hat]),
                "dispersion": [float(s) for s in tr.dispersion]}

    return {"doc": doc_i, **meas,
            "frozen_cont_ce": frozen_ce,
            "delta_proxy": None,  # filled by caller
            "cont_ce": [[float(c) for c in r] for r in rep_ce],
            "fixed": fixed, "oracle": oracle, "alta": alta}


# ---------------- main ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, choices=DOMAINS)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n-docs", type=int, default=500)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--record-steps", default="1,2,5,10,20")
    ap.add_argument("--stopping", default="all",
                    choices=["fixed", "alta", "oracle", "all"])
    ap.add_argument("--adapt-params", default="ln", choices=["ln", "lora"])
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--momentum", type=float, default=0.9)
    ap.add_argument("--n-draws", type=int, default=8)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=float, default=16.0)
    ap.add_argument("--ref-file", default="",
                    help="wikitext_ref_s<seed>.json for delta_proxy")
    ap.add_argument("--data-dir", default="workdir/data/e4")
    ap.add_argument("--out-dir", default="workdir/ttt/results/e4")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.lr is None:
        args.lr = DEFAULT_LR[args.adapt_params]
    if args.smoke:
        args.n_docs = 3
        args.steps = 5
    args.record_steps = sorted({int(s) for s in args.record_steps.split(",")}
                               | {args.steps})
    set_seed(args.seed)
    device = "cuda"

    from transformers import AutoTokenizer
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()
    tok = AutoTokenizer.from_pretrained("gpt2")
    tok.model_max_length = int(1e9)
    model, params, names = load_model_and_subset(
        args.adapt_params, device, args.lora_r, args.lora_alpha)
    snap = [p.detach().clone() for p in params]
    print(f"[e4] adapt subset '{args.adapt_params}': {len(names)} tensors, "
          f"{sum(p.numel() for p in params)} params", flush=True)

    docs = load_docs(os.path.join(args.data_dir, f"{args.domain}.jsonl"),
                     tok, args.n_docs)
    if len(docs) < args.n_docs:
        print(f"[e4] WARNING only {len(docs)}/{args.n_docs} docs available",
              flush=True)

    ref_mean = None
    if args.ref_file:
        with open(args.ref_file, encoding="utf-8") as f:
            ref_mean = float(json.load(f)["mean_frozen_cont_ce"])

    records = []
    for i, ids in enumerate(docs):
        rec = run_document(model, params, snap, ids, i, args, device)
        records.append(rec)
        if (i + 1) % 25 == 0 or args.smoke:
            print(f"[e4] {args.domain} s{args.seed}: doc {i + 1}/{len(docs)} "
                  f"frozen={rec['frozen_cont_ce']:.3f} "
                  f"alpha={rec['alpha']:.3f}", flush=True)

    frozen_mean = float(np.mean([r["frozen_cont_ce"] for r in records]))
    if args.domain == "wikitext" and ref_mean is None:
        ref_mean = frozen_mean  # in-distribution self-reference
        save_json({"mean_frozen_cont_ce": frozen_mean, "n_docs": len(records),
                   "seed": args.seed},
                  os.path.join(args.out_dir, f"wikitext_ref_s{args.seed}.json"))
    if ref_mean is not None:
        for r in records:
            r["delta_proxy"] = r["frozen_cont_ce"] - ref_mean

    tag = f"{args.domain}_{args.adapt_params}_s{args.seed}"
    save_json({"meta": run_meta(args),
               "protocol": {"prefix_len": PREFIX_LEN, "cont_len": CONT_LEN,
                            "window": WINDOW, "tail": TAIL},
               "wikitext_ref_mean": ref_mean,
               "records": records},
              os.path.join(args.out_dir, f"{tag}.json"))
    last = str(args.steps)
    adapted_mean = float(np.mean([r["fixed"][last] for r in records]))
    msg = (f"[e4] DONE {tag}: frozen_ppl={np.exp(frozen_mean):.2f} "
           f"ppl@{last}={np.exp(adapted_mean):.2f}")
    if records[0]["alta"] is not None:
        alta_mean = float(np.mean([r["alta"]["cont_ce"] for r in records]))
        orac_mean = float(np.mean([r["oracle"]["cont_ce"] for r in records]))
        msg += (f" alta_ppl={np.exp(alta_mean):.2f} "
                f"oracle_ppl={np.exp(orac_mean):.2f}")
    print(msg, flush=True)


if __name__ == "__main__":
    main()
