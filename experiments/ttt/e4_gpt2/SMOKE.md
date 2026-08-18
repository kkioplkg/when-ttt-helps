# E4 smoke test (run on remote, cwd = workdir/ttt)

Order matters: jobs 1-2 of `jobs_e4.txt` (pip + data) must complete before any
`run_e4.py` job. Wikitext jobs must finish before pubmed/code/legal jobs of the
same seed (they consume `wikitext_ref_s<seed>.json` for the delta proxy).

```bash
# 0. deps (transformers/datasets not assumed installed)
pip install -q transformers datasets huggingface_hub

# 1. data smoke: 8 docs/domain, streaming, hf-mirror endpoint is the default
python e4_gpt2/prepare_data.py --smoke --out-dir workdir/data/e4_smoke

# 2. wikitext control first (writes wikitext_ref_s0.json; --smoke = 3 docs, 5 steps)
python e4_gpt2/run_e4.py --domain wikitext --seed 0 --smoke \
    --data-dir workdir/data/e4_smoke --out-dir workdir/ttt/results/e4_smoke

# 3. one shift domain, ln params, with delta proxy vs the wikitext ref
python e4_gpt2/run_e4.py --domain pubmed --seed 0 --smoke \
    --data-dir workdir/data/e4_smoke --out-dir workdir/ttt/results/e4_smoke \
    --ref-file workdir/ttt/results/e4_smoke/wikitext_ref_s0.json

# 4. lora variant (optional path)
python e4_gpt2/run_e4.py --domain code --seed 0 --smoke --adapt-params lora \
    --data-dir workdir/data/e4_smoke --out-dir workdir/ttt/results/e4_smoke
```

## Pass criteria

- `prepare_data.py --smoke` writes 4 files `{wikitext,pubmed,code,legal}.jsonl`
  with 8 lines each; every line has `n_tokens >= 1536`.
- Each `run_e4.py` smoke prints `adapt subset 'ln': 50 tensors` (GPT-2 has 25
  LayerNorms: 2 per block x 12 + ln_f) or `'lora': 48 tensors` (4 x 12 blocks),
  then `DONE <tag>` with finite perplexities (wikitext frozen ppl should be
  roughly 20-40; shifted domains higher).
- Output JSON has 3 records, each with: `alpha` in [-1, 1], `sigma2_rel > 0`,
  `cont_ce` = 3 replicas x 5 steps, `fixed` keyed by `{1, 2, 5}`, `oracle.t_star`
  in [0, 5], `alta.t_hat` in [0, 5], and (step 3 only) `delta_proxy != null`.
- Runtime: each smoke run well under 2 minutes on one 2080 Ti.

## Full run

Use `e4_gpt2/jobs_e4.txt` (14 lines: pip, prepare, then 4 domains x 3 seeds,
wikitext first). ~500 docs x 3 replicas x 20 steps x (1 backward@512 +
1 forward@1024) per doc + 9 measurement backwards -> roughly 25-40 min per job
on one 2080 Ti; 12 jobs over 2 GPUs comfortably under the 8 GPU-h target.
