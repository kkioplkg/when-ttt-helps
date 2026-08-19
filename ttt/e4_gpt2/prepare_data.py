"""E4 data prep — shift corpora + in-distribution control for GPT-2 TTT.

Downloads ~500-1000 documents per domain to <out-dir>/<domain>.jsonl, each
verified >= --min-tokens when GPT-2-tokenized (default 1536 = 768 prefix +
256 continuation + slack). Total on disk << 2GB (texts are char-capped).

Verified dataset sources (HF hub, 2026-07-02):
  pubmed   : ccdv/pubmed-summarization, config 'document', split train
             (native parquet; field 'article' = full PubMed paper body).
             NOTE: bare abstracts are ~250 tokens < 1536 floor, so we use the
             full-text article bodies from the same PubMed corpus.
  code     : codeparrot/codeparrot-clean-valid, split train (native json.gz,
             61,373 Python files; field 'content').
  legal    : pile-of-law/pile-of-law, file data/train.echr.jsonl.xz (20.1 MB,
             European Court of Human Rights opinions; field 'text').
             NOTE: r_legaladvice Reddit posts are far below the token floor;
             echr gives long English legal opinions in a single small file.
  wikitext : Salesforce/wikitext, config 'wikitext-103-raw-v1' (native
             parquet). IN-DISTRIBUTION control. Articles reconstructed from
             the line stream (validation split first, ~60 articles, then
             topped up from train via streaming).

All access is streaming / single-file, so bandwidth stays small. Set
HF_ENDPOINT=https://hf-mirror.com for AutoDL (done below via setdefault).
"""
import argparse
import json
import lzma
import os

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", "workdir/hf_cache")

DOMAINS = ["wikitext", "pubmed", "code", "legal"]


def stream_pubmed():
    from datasets import load_dataset
    ds = load_dataset("ccdv/pubmed-summarization", "document",
                      split="train", streaming=True)
    for ex in ds:
        yield ex["article"]


def stream_code():
    from datasets import load_dataset
    ds = load_dataset("codeparrot/codeparrot-clean-valid",
                      split="train", streaming=True)
    for ex in ds:
        yield ex["content"]


def stream_legal():
    from huggingface_hub import hf_hub_download
    for fname in ["data/train.echr.jsonl.xz", "data/validation.echr.jsonl.xz"]:
        try:
            path = hf_hub_download("pile-of-law/pile-of-law", fname,
                                   repo_type="dataset")
        except Exception as e:
            print(f"[e4:data] skip {fname}: {e}", flush=True)
            continue
        with lzma.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)["text"]
                except (json.JSONDecodeError, KeyError):
                    continue


def _is_article_header(line):
    # top-level wikitext header: ' = Title = ' (sections are ' = = ... = = ')
    s = line.strip()
    return (len(s) > 3 and s.startswith("=") and s.endswith("=")
            and not s.startswith("= ="))


def stream_wikitext():
    from datasets import load_dataset
    for split in ["validation", "train"]:
        ds = load_dataset("Salesforce/wikitext", "wikitext-103-raw-v1",
                          split=split, streaming=True)
        buf = []
        for ex in ds:
            line = ex["text"]
            if _is_article_header(line):
                if buf:
                    yield "".join(buf)
                buf = [line]
            elif buf:
                buf.append(line)
        if buf:
            yield "".join(buf)


STREAMS = {"pubmed": stream_pubmed, "code": stream_code,
           "legal": stream_legal, "wikitext": stream_wikitext}


def collect(domain, tok, n_docs, min_tokens, cap_chars, out_path):
    n_kept = n_seen = 0
    seen = set()
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for text in STREAMS[domain]():
            n_seen += 1
            if not isinstance(text, str) or len(text) < 2 * min_tokens:
                continue  # cheap char-length prefilter
            snippet = text[:cap_chars]
            h = hash(snippet[:2000])
            if h in seen:
                continue
            n_tok = len(tok(snippet, add_special_tokens=False)["input_ids"])
            if n_tok < min_tokens:
                continue
            seen.add(h)
            f.write(json.dumps({"id": n_kept, "n_tokens": n_tok,
                                "text": snippet}, ensure_ascii=False) + "\n")
            n_kept += 1
            if n_kept % 100 == 0:
                print(f"[e4:data] {domain}: {n_kept}/{n_docs} "
                      f"(scanned {n_seen})", flush=True)
            if n_kept >= n_docs:
                break
    os.replace(tmp, out_path)
    print(f"[e4:data] {domain}: DONE {n_kept} docs -> {out_path} "
          f"({os.path.getsize(out_path) / 1e6:.1f} MB)", flush=True)
    return n_kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="workdir/data/e4")
    ap.add_argument("--domains", nargs="*", default=DOMAINS, choices=DOMAINS)
    ap.add_argument("--n-docs", type=int, default=1000)
    ap.add_argument("--min-tokens", type=int, default=1536)
    ap.add_argument("--cap-chars", type=int, default=20000)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        args.n_docs = 8
    os.makedirs(args.out_dir, exist_ok=True)

    from transformers import AutoTokenizer
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()
    tok = AutoTokenizer.from_pretrained("gpt2")
    tok.model_max_length = int(1e9)  # silence length warnings

    for domain in args.domains:
        out_path = os.path.join(args.out_dir, f"{domain}.jsonl")
        if os.path.exists(out_path) and not args.smoke:
            n = sum(1 for _ in open(out_path, encoding="utf-8"))
            if n >= args.n_docs:
                print(f"[e4:data] {domain}: exists ({n} docs), skip", flush=True)
                continue
        n = collect(domain, tok, args.n_docs, args.min_tokens,
                    args.cap_chars, out_path)
        if n < args.n_docs:
            print(f"[e4:data] WARNING {domain}: only {n}/{args.n_docs} docs "
                  f"met the {args.min_tokens}-token floor", flush=True)


if __name__ == "__main__":
    main()
