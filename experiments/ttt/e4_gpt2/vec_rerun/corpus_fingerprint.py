"""Per-document token-ID fingerprints for the E3 corpora.

Motivation: dataset name + revision is NOT sufficient to prove that a rerun saw
the same documents -- upstream files can be repacked, and the selection filter
depends on the tokenizer. The only unambiguous identifier of what the model
actually consumed is the exact 1024-token id sequence
(768 prefix + 256 continuation) that `run_e4.load_docs` produces.

This writes, per domain, a sha256 over those token ids per document plus a
corpus-level rollup, so any FUTURE rerun can prove corpus identity directly
instead of inferring it from agreement in frozen continuation CE.

(The present rerun could not use this: the published run retained no such
fingerprint, so corpus identity had to be established through the frozen-CE
comparison in verify_vectors.py check A. Emitting it now removes that
indirection for everyone downstream.)
"""
import argparse
import hashlib
import json
import os

import numpy as np

PREFIX_LEN = 768
CONT_LEN = 256


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--gpt2-path", required=True)
    ap.add_argument("--domains", nargs="*",
                    default=["pubmed", "code", "legal", "wikitext"])
    ap.add_argument("--n-docs", type=int, default=500)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from transformers import AutoTokenizer
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()
    tok = AutoTokenizer.from_pretrained(args.gpt2_path)
    tok.model_max_length = int(1e9)

    out = {"n_docs": args.n_docs, "prefix_len": PREFIX_LEN,
           "cont_len": CONT_LEN, "domains": {}}
    for domain in args.domains:
        path = os.path.join(args.data_dir, f"{domain}.jsonl")
        if not os.path.exists(path):
            print(f"[fp] {domain}: missing", flush=True)
            continue
        per_doc, rollup = [], hashlib.sha256()
        with open(path, encoding="utf-8") as f:
            for line in f:
                ids = tok(json.loads(line)["text"],
                          add_special_tokens=False)["input_ids"]
                if len(ids) < PREFIX_LEN + CONT_LEN:
                    continue
                ids = ids[:PREFIX_LEN + CONT_LEN]
                raw = np.asarray(ids, dtype=np.int32).tobytes()
                h = hashlib.sha256(raw).hexdigest()
                per_doc.append(h)
                rollup.update(bytes.fromhex(h))
                if len(per_doc) >= args.n_docs:
                    break
        out["domains"][domain] = {"n": len(per_doc),
                                  "corpus_sha256": rollup.hexdigest(),
                                  "per_doc_sha256": per_doc}
        print(f"[fp] {domain}: {len(per_doc)} docs, corpus "
              f"{rollup.hexdigest()[:16]}...", flush=True)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
