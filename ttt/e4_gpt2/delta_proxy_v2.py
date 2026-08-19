"""E5 ablation: alternative per-document shift proxy for E4 (C6 follow-up).

Motivation: frozen continuation CE conflates intrinsic document entropy with
distribution shift (documented C6 limitation). Proxy v2 measures shift in
REPRESENTATION space: cosine distance between a document's mean-pooled GPT-2
hidden state (middle layer) and the source-domain (wikitext) reference mean.

Outputs results/e5/delta_v2_<domain>.json with per-doc {doc, delta_v2} that
analysis joins against the existing e4 result JSONs (key: doc index), then
recomputes the within-domain phase-gain correlations with delta_v2.
"""
import argparse
import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.utils import save_json, set_seed  # noqa: E402

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", "workdir/hf_cache")


def doc_hidden(model, tok, text, device, layer, max_tokens=768):
    ids = tok(text, return_tensors="pt", truncation=True,
              max_length=max_tokens).input_ids.to(device)
    with torch.no_grad():
        out = model(ids, output_hidden_states=True)
    h = out.hidden_states[layer][0]          # (T, d)
    return h.mean(dim=0).float().cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", nargs="*",
                    default=["wikitext", "pubmed", "code", "legal"])
    ap.add_argument("--data-dir", default="workdir/data/e4")
    ap.add_argument("--n-docs", type=int, default=500)
    ap.add_argument("--layer", type=int, default=6)
    ap.add_argument("--out-dir", default="workdir/ttt/results/e5")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        args.n_docs = 5
    set_seed(0)
    device = "cuda"
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast
    tok = GPT2TokenizerFast.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2").to(device).eval()

    feats = {}
    for dom in args.domains:
        path = os.path.join(args.data_dir, f"{dom}.jsonl")
        docs = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                docs.append(json.loads(line)["text"])
                if len(docs) >= args.n_docs:
                    break
        H = np.stack([doc_hidden(model, tok, t, device, args.layer)
                      for t in docs])
        feats[dom] = H
        print(f"[e5:delta2] {dom}: {H.shape}", flush=True)

    ref = feats["wikitext"].mean(axis=0)
    ref = ref / (np.linalg.norm(ref) + 1e-12)
    for dom in args.domains:
        H = feats[dom]
        Hn = H / (np.linalg.norm(H, axis=1, keepdims=True) + 1e-12)
        d = 1.0 - Hn @ ref
        save_json({"domain": dom, "layer": args.layer,
                   "ref": "wikitext_mean",
                   "records": [{"doc": i, "delta_v2": float(v)}
                               for i, v in enumerate(d)]},
                  os.path.join(args.out_dir, f"delta_v2_{dom}.json"))
        print(f"[e5:delta2] {dom}: mean={d.mean():.4f} std={d.std():.4f}",
              flush=True)
    print("[e5:delta2] DONE")


if __name__ == "__main__":
    main()
