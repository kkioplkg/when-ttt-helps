"""E3 corpus rebuild for `legal` and `wikitext` from locally staged source files.

Why this exists: the published E3 corpora for `pubmed` and `code` are retained
in the experiment tree, but `legal.jsonl` and `wikitext.jsonl` are not, so they
must be rebuilt from the upstream datasets.  The GPU box cannot reach the
HuggingFace LFS CDN reliably, so the upstream files are staged as plain files
and streamed from disk here.

The document-selection logic is copied VERBATIM from
experiments/ttt/e4_gpt2/prepare_data.py (`collect`, `_is_article_header`,
and the wikitext article reconstruction): same order, same >=1536-token floor,
same 20000-char cap, same dedup, same record schema.  Only the *transport*
changes -- `datasets.load_dataset(..., streaming=True)` and
`hf_hub_download(...)` are replaced by a parquet row-group reader and a plain
`lzma.open`, both of which preserve the upstream row order that the streaming
readers also follow.

Whether the rebuild actually reproduces the published corpus is NOT assumed: it
is tested downstream by comparing frozen (t=0) continuation CE per document
against the retained record, which is a pure function of the document and the
frozen weights.

Staged layout expected under --src-dir:
    wikitext/validation-00000-of-00001.parquet
    wikitext/train-00000-of-00002.parquet
    legal/train.echr.jsonl.xz
    legal/validation.echr.jsonl.xz
"""
import argparse
import json
import lzma
import os

DOMAINS = ["legal", "wikitext"]


def stream_legal(src):
    for fname in ["train.echr.jsonl.xz", "validation.echr.jsonl.xz"]:
        path = os.path.join(src, "legal", fname)
        if not os.path.exists(path):
            print(f"[e4:data] skip {fname}: not staged", flush=True)
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


def _parquet_text_rows(path):
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(path)
    for i in range(pf.num_row_groups):
        col = pf.read_row_group(i, columns=["text"])["text"]
        for v in col.to_pylist():
            yield v


def stream_wikitext(src):
    for fname in ["validation-00000-of-00001.parquet",
                  "train-00000-of-00002.parquet"]:
        path = os.path.join(src, "wikitext", fname)
        if not os.path.exists(path):
            print(f"[e4:data] skip {fname}: not staged", flush=True)
            continue
        buf = []
        for line in _parquet_text_rows(path):
            if _is_article_header(line):
                if buf:
                    yield "".join(buf)
                buf = [line]
            elif buf:
                buf.append(line)
        if buf:
            yield "".join(buf)


STREAMS = {"legal": stream_legal, "wikitext": stream_wikitext}


def collect(domain, src, tok, n_docs, min_tokens, cap_chars, out_path):
    n_kept = n_seen = 0
    seen = set()
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for text in STREAMS[domain](src):
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
    ap.add_argument("--src-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--gpt2-path", required=True)
    ap.add_argument("--domains", nargs="*", default=DOMAINS, choices=DOMAINS)
    ap.add_argument("--n-docs", type=int, default=1000)
    ap.add_argument("--min-tokens", type=int, default=1536)
    ap.add_argument("--cap-chars", type=int, default=20000)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    from transformers import AutoTokenizer
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()
    tok = AutoTokenizer.from_pretrained(args.gpt2_path)
    tok.model_max_length = int(1e9)  # silence length warnings

    for domain in args.domains:
        out_path = os.path.join(args.out_dir, f"{domain}.jsonl")
        collect(domain, args.src_dir, tok, args.n_docs, args.min_tokens,
                args.cap_chars, out_path)


if __name__ == "__main__":
    main()
