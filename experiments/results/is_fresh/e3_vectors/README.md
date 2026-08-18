# E3 per-step prediction vectors — the selector, made recomputable

Until this release the E3 retrospective selector could not be rerun by a
reader. Its admissibility test compares the per-step **mean replica prediction
vectors** $\bar\pi_t \in \mathbb{R}^{32}$ against bands built from the
replica dispersion sequence $s(\cdot)$ — it consumes both arrays, not the
vectors alone — and the vectors were not retained:
the records stored the selected index $\hat t$, the dispersion sequence
$s(\cdot)$ and the continuation cross-entropies, so every aggregate reported
*at* the stored $\hat t$ was reconstructible while $\hat t$ itself was not.
This directory removes that limitation.

Provenance of the run that produced these arrays — hardware, pinned GPT-2
revision, corpus rebuild, and the four agreement checks against the published
records — is `PROVENANCE.md` here; the per-job agreement tables are
`VERIFY_SUMMARY.md` and `verify_report.json`.

## What is here

| file | contents |
|---|---|
| `<tag>_vectors.npz` (12) | `pred0` (n,32), `pi_bar` (n,20,32), `s` (n,21), `t_hat` (n,), `doc` (n,), `meta` |
| `<tag>.json` (12) | the rerun's own per-document records, same schema as `experiments/results/e4/<tag>.json` |
| `verify_report.json`, `VERIFY_SUMMARY.md` | the four agreement checks against the published records |
| `corpus_fingerprints.json` | per-document SHA-256 over the exact 1024 token ids, all four domains |
| `wikitext_ref_check.json`, `wikitext_ref_s*.json` | the regenerated delta-proxy reference, against the retained one |
| `m0_primary/` | one independent per-example clean evaluation of the surviving source checkpoint (corroboration; see `PROVENANCE.md` §3) |
| `PROVENANCE.md` | how the run was produced and what its limits are |

`tag` is `<domain>_ln_s<seed>` over four domains and three seeds.
`meta` carries the domain, seed, `steps=20`, `K=3`, `tail=32`, `kappa=1.5`
and the pinned GPT-2 revision.

**All arrays are float64. Nothing here is downcast.**

## The one thing that is not here, and why

The staged rerun also emitted `tails` of shape `(n, 3, 20, 32)` — every
replica's per-step prediction vector. That array is **46 MB of the grid's
64.5 MB on its own**, and it is in the side archive
`e3_vectors_replicas.zip`, whose SHA-256 is recorded in the reproducibility
manifest.

The split is by **content, not by precision**, and that choice was measured
rather than assumed. These `.npz` files are already deflate-compressed, so
storing them as float32 saves 12% (64.5 MB → 56.6 MB), not half, and leaves
the archive over the attachment budget anyway; whereas `tails` is a single
array carrying 72% of the bytes. Downcasting would have bought little and
cost precision; moving `tails` buys everything and costs nothing, because:

* `pi_bar` is **bitwise equal** to `tails.mean(axis=0)` on all 6000 documents
  — verified elementwise at integration, not argued; and
* `s` is the per-step replica spread of the same array, released here in full.

So `tails` lets a reader *regenerate* `pi_bar` and `s` instead of consuming
them. It is not needed to recompute the selector, and it is not needed to
reproduce any number printed in either submitted document.

## Recomputing the selector

```
python experiments/ttt/is_fresh/f39_e3_vector_selfcheck.py
```

reads only the `.npz` files here, reruns the admissibility scan of
`core/alta.py` on them ($\kappa = 1.5$; $\hat t$ is the smallest step after
which no later movement exceeds the replica-noise band), and writes
`experiments/results/is_fresh/f39_e3_vector_selfcheck.json`. It needs no GPU,
no model, no corpus and no network.

The script **asserts** its load-bearing result rather than printing it: if the
released arrays ever fail to reproduce every run's own $\hat t$, it exits
non-zero, so a release that does not support the claim cannot pass quietly.

Its three headline outputs, on the arrays in this directory:

| quantity | value |
|---|---|
| release-only self-check — released arrays reproduce each run's own $\hat t$ | **6000 / 6000, exact** |
| $\hat t$ vs the published RTX 2080 Ti record | 5989 / 6000 = 99.82%, 11 boundary near-ties |
| worst $\lvert$normalised slack$\rvert$ at a disputed step | $9.697\times10^{-4}$ |
| fixed-budget ppl@20, rerun vs retained | agrees to $1.50\times10^{-5}$ absolute on all 12 jobs |

The first row is the one that closes the limitation: it asks whether the
**released arrays alone** rebuild the selector, independently of whether a
rerun on different hardware landed on the published decision. The second row
is the separate, weaker question of cross-hardware agreement; all 11
disagreements sit within 0.1% of a decision boundary and fall in both
directions (7 admitted here and rejected there, 4 the reverse). Those two
facts -- bidirectional, and within 0.1% of the boundary -- are the whole of
what is measured. They are consistent with boundary-sensitive numerical
variation, but they do not demonstrate it and they do not exclude a
systematic cross-hardware difference: the published run's per-step
trajectories were not retained, so no comparison available here can
distinguish the two explanations.

## What this does not make reproducible

The reruns are not bitwise reproductions of the published ones — different
GPU, different CUDA, different torch — and the release still contains no
frozen model checkpoint or tokenizer snapshot, so a model-level rerun remains
a replication rather than a reconstruction. `PROVENANCE.md` §5 states the
limits in full.
