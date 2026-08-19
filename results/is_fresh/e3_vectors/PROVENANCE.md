# E3 vector rerun — provenance

This file was written where the rerun was staged and travels with the
material it describes. One number in it was recomputed on the way in and is
recorded here rather than silently corrected: §4's fixed-budget row said the
rerun ppl@20 *"agrees with the retained value to 4 decimals on all 12 jobs"*,
which `experiments/ttt/is_fresh/f39_e3_vector_selfcheck.py` shows to be
**false as written** — two of the twelve (`code_ln_s0`, `pubmed_ln_s2`)
straddle a rounding boundary and print a different fourth decimal. The
measured statement, which that row now carries, is agreement to
$1.50\times10^{-5}$ absolute and $6.5\times10^{-7}$ relative on all twelve.
Nothing else in §4 changed.

The rerun exists to remove two gaps in the released record:

* **gap 1** — the E3 retrospective selector was not reproducible from the
  released records, because the per-step mean replica prediction vectors
  $\bar\pi_t \in \mathbb{R}^{32}$ were not retained.
* **gap 2** — the reported source clean accuracies had no primary $m_0$
  evaluation record or source checkpoint in the payload.

It also pins the GPT-2 model and tokenizer revision, which the released
records previously resolved by generic model name.

---

## 1. Compute environment

All compute ran on the remote Ubuntu GPU box; nothing was computed on the
authoring machine (light file transfer only).

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 3080, 10 GB, driver 595.84, CUDA 13.2 |
| OS | Ubuntu 24.04 (noble) |
| Data disk | one NTFS partition, label `Data`, 1.5 TB, mounted under the run root's parent |
| Run root | `<RUN_ROOT>` (mirrors the authoring tree) |
| Python | 3.14.6 (Miniconda, installed under the run root) |
| torch | 2.13.0+cu130 |
| transformers | 5.14.1 |
| numpy | 2.5.1 |

The published E3 run used **RTX 2080 Ti / torch 2.8.0+cu128**, so this is a
different GPU architecture and a different kernel-selection regime. That is why
§4 reports agreement rather than bitwise identity.

## 2. Pinned external artefacts

### GPT-2 (closes the "pin the revision" item)

| | |
|---|---|
| repo | `openai-community/gpt2` (the canonical target of the bare id `gpt2`) |
| revision | `607a30d783dfa663caf39e06633721c8d4cfcd7e` |
| `model.safetensors` sha256 | `248dfc3911869ec493c76e65bf2fcf7f615828b0254c12b473182f0f81d3a707` |
| `model.safetensors` size | 548,105,171 bytes |

The sha256 was taken from the repository's own git-LFS pointer at that revision
and re-verified against the downloaded file on both machines, so the pin is
checkable without trusting either download.

### Domain corpora

`pubmed.jsonl` and `code.jsonl` are the **retained** corpora from
`experiments/data/e4/`, transferred unchanged.

`legal.jsonl` and `wikitext.jsonl` were **not** retained and had to be rebuilt
from upstream:

| domain | dataset | revision |
|---|---|---|
| legal | `pile-of-law/pile-of-law`, `data/train.echr.jsonl.xz` | `2e96169e7e4b43f8ea36230515ebb44b27423b94` |
| wikitext | `Salesforce/wikitext`, `wikitext-103-raw-v1` | `b08601e04326c79dfdd32d625aee71d232d685c3` |

The rebuild used `experiments/ttt/e4_gpt2/vec_rerun/prepare_data_local.py`, whose selection logic is copied
verbatim from `experiments/ttt/e4_gpt2/prepare_data.py` (same order, same
1536-token floor, same 20000-char cap, same dedup, same schema); only the
transport changed, because the GPU box cannot reach the HuggingFace LFS CDN.

**The rebuild is not assumed to have worked — it is tested.** See §4, check A.

## 3. What was run

### Job 1 — E3 with per-step prediction-vector logging

`experiments/ttt/e4_gpt2/vec_rerun/run_e4_vec.py` is a copy of `experiments/ttt/e4_gpt2/run_e4.py` with the
scientific path untouched and four additions: the $\bar\pi_t$ dump, periodic
checkpoint/resume, a `--gpt2-revision` / `--gpt2-path` pin, and a heartbeat.
The RNG streams, parameter subset, optimiser, eval protocol and record schema
are unchanged, so the emitted `<tag>.json` is directly comparable to the
retained record for the same `(domain, seed)`.

Grid: 4 domains x 3 seeds = 12 jobs, 500 documents each, K=3 replicas, 20
steps, LayerNorm-only adaptation, lr 1e-4, momentum 0.9 — i.e. exactly the
published `jobs_e4.txt` configuration and seeds.

Per job the run writes `<tag>_vectors.npz` holding

| array | shape | meaning |
|---|---|---|
| `pred0` | (n_docs, 32) | the frozen (t=0) prediction vector |
| `tails` | (n_docs, 3, 20, 32) | every replica's per-step prediction vector |
| `pi_bar` | (n_docs, 20, 32) | the mean replica prediction vector $\bar\pi_t$ |
| `t_hat` | (n_docs,) | the selector's stopping step, for cross-checking |
| `doc` | (n_docs,) | document index |

all in float64. `tails` is the sufficient statistic: `pi_bar`, the dispersion
$s(t)$ and hence $\hat t$ all follow from it, so the selector becomes
recomputable from released records.

**Size**: 5.3 MB per job, **64.5 MB of vectors** for the full grid (78 MB for
this whole staging directory including the per-document JSON records) — far
below the "few GB" threshold, so no reduction or subsampling was applied and
the vectors are stored at full float64 precision rather than downcast.

**How that grid is split across the release.** Everything the selector
consumes — `pred0`, `pi_bar`, the dispersion sequence `s`, and `t_hat` —
travels in this directory at full float64 precision, 19.0 MB for the grid;
`tails`, the per-replica trajectory, is 46 MB of that 64.5 MB on its own and
travels in the side archive `e3_vectors_replicas.zip`. Nothing is downcast
and nothing is dropped: `pi_bar` is bitwise equal to `tails.mean(axis=0)` on
all 6000 documents, checked at integration. `README.md` in this directory
states the split, and why it is by content rather than by precision.

**Wall clock**: 12 jobs x 500 documents, ~88 min per job, three jobs resident
on the one GPU (7.4 GB of 10 GB, GPU at 100% throughout), 09:58 to 16:52 —
just under 7 hours. `experiments/ttt/e4_gpt2/vec_rerun/supervise_lanes.sh` kept three jobs resident as
lanes drained, so the GPU never ran a single job against idle capacity.

### Job 2 — $m_0$ primary evaluation — CLOSED ELSEWHERE; this is corroboration only

**Do not treat the contents of `m0_primary/` as the closure of gap 2.** That
gap is closed independently, and differently, by
`experiments/results/m0/`: the twelve primary $m_0$ evaluation records the
training runs themselves emitted already existed in the experiment tree and
were merely outside the packager's `RESULT_DIRS`, hence absent from the
release archive. They are in the payload now, with parser-asserted
sanitisation; the printed clean accuracies are stated as seed ranges, and
both ends of all four ranges are bound in `tools/r9_reconcile.py`. The clean
accuracies are therefore reconstructible from retained evaluation records,
which is what gap 2 asked for.

No retrain was performed here, and none is needed. Retraining the eleven source
models whose checkpoints did not survive would have cost roughly 25 GPU-hours
and would have produced **different weights with different accuracies**, i.e.
no evidence at all for the figures actually printed in the manuscript. That is
why it was not attempted.

What `m0_primary/` does contain is one **independent corroboration**, retained
because it is cheap, primary, and of a type nothing else in the release
carries. `experiments/ttt/e4_gpt2/vec_rerun/eval_m0_primary.py` ran a standalone, seeded clean test-set
evaluation of the only source checkpoint surviving in a non-quarantined tree
(`experiments/results/is_fresh/e2_gn/cifar10_resnet26ttt_s20260806.pt`,
sha256 `cdf63d2f079f7f3febabd4765824369ba8fffc7bc54e321fcb4f4bd347e19611`) and
wrote a **per-example** record (index, label, prediction, correct flag, max
softmax probability, per-example loss) alongside a summary (accuracy, Wilson
95% interval, mean loss, per-class accuracy, checkpoint sha256).

Result: **0.9165 (9165/10000)**, Wilson 95% [0.9109, 0.9218], mean CE 0.3052.
That reproduces the value in the checkpoint's own retained record exactly, and
it falls inside the published ResNet-26+GroupNorm CIFAR-10 seed range of
91.5–92.2%. The test set came from the retained extracted arrays
(`experiments/data/cifar10_np/test_x.npy`), under the published test transform
with `shuffle=False`, so example order matches the original protocol.

It is evidence *of a kind the release otherwise lacks* — per-example primary
output rather than a training run's own epoch logging — but it speaks for one
seed of one architecture on one dataset, and it is not the mechanism by which
the finding was closed.

## 4. Agreement with the retained records

`experiments/ttt/e4_gpt2/vec_rerun/verify_vectors.py` performs four checks per `(domain, seed)`:

* **A — document identity.** Frozen (t=0) continuation CE is a pure function of
  the document and the frozen weights, with no RNG and no adaptation in it. It
  is therefore the sharp test of whether the rebuilt `legal` and `wikitext`
  corpora contain *the same documents* as the published run, as distinct from
  float noise.
* **B — dispersion.** $s(t)$ recomputed from the new prediction vectors against
  the retained `alta.dispersion` array (retained at full precision for all 21
  steps). This is the sharpest *corroboration* the retained records permit,
  and it is **not** an identity test on the vectors. It compares one scalar
  sequence per document; many different replica trajectories share a
  dispersion sequence, and the published run's own per-step $\bar\pi_t$ were
  never retained. So agreement here cannot establish that the new vectors are
  the ones the published selector consumed. That is claim **(H)**, and this
  release does not make it — see §S7 of the Supplementary Material for the
  (R)/(H) split.
* **C — $\hat t$.** Recomputed from the new vectors by the same admissibility
  scan, against the retained `alta.t_hat`, with the decision margin recorded at
  the deciding step so any mismatch can be reported as a near-tie or as real.
* **D — trajectory and headline.** Per-replica per-step continuation CE, and
  the fixed-budget $t=20$ aggregate.

Results are in `e3_vectors/verify_report.json` and
`e3_vectors/VERIFY_SUMMARY.md`. The grid completed 12/12.

**Headline: the selector is now recomputable from released records.**

| | result |
|---|---|
| release-only self-check (released arrays reproduce each run's own $\hat t$) | **6000 / 6000 — exact** |
| $\hat t$ vs the retained record | **5989 / 6000 = 99.82%** |
| mismatches | 11, every one a boundary near-tie |
| worst \|normalised slack\| at a disputed step | **9.70e-04** (< 0.1% of the band width) |
| frozen (t=0) CE vs retained | max 6.2e-06 across all 12 jobs; 100% within 1e-4 |
| dispersion vs each run's own record | **exactly 0.0** on all 12 jobs |
| dispersion vs retained | max 2.1e-03, mean 3.5e-05 – 7.3e-05 |
| per-step continuation CE vs retained | max 4.5e-04 over all (doc, replica, step) |
| fixed-budget ppl@20 | agrees with the retained value to $1.50\times10^{-5}$ absolute ($6.5\times10^{-7}$ relative) on all 12 jobs |

The self-check is the row that closes gap 1: it asks whether the
**released arrays alone** rebuild the selector, independently of whether this
rerun happened to land on the published decision. It is exact.

The 99.82% row is the separate, weaker question of cross-hardware agreement,
and the residual is *consistent with* boundary sensitivity — not accounted
for in any sense that excludes alternatives. All 11 disagreements sit within
0.1% of an admissibility decision boundary, and they fall in **both**
directions — 7 documents admitted the disputed step here where the published
run rejected it, 4 rejected it where the published run admitted it (the
split is `totals/mismatch_directions` of
`../f39_e3_vector_selfcheck.json`, and is recomputable from the eleven
`C_mismatches` entries of `verify_report.json`). A
systematic error would be expected to push one way, and these do not. Given
that the per-step CE differs by up to 4.5e-04 between the two GPUs, an
inequality whose slack is 1e-05 sits below the arithmetic resolution of the
comparison, so a crossing there is what one would expect to see.

That is a **reading of the evidence, not an exclusion of every systematic
alternative.** With the published run's per-step trajectories unretained,
no observation available here can rule one out; what the numbers establish
is consistency, and the Supplementary Material states it in exactly those
terms. This file uses the same standard.

**Delta-proxy reference cross-check.** Every non-wikitext domain's
`delta_proxy` is measured from the wikitext mean frozen continuation CE, so a
drift there would silently move a whole column of the E3 tables. The
regenerated references reproduce the retained ones to **5.53e-08**
(3.148176995754 vs 3.148176940441, all three seeds), recorded in
`e3_vectors/wikitext_ref_check.json`. The three seeds agree exactly with each
other, which is the expected signature: the reference is a mean over frozen
predictions and cannot depend on the adaptation seed.

**Transfer integrity.** All 31 artefacts were compared by SHA-256 between the
GPU box and this staging directory: 31 identical, 0 differing.

## 5. Limits

Stated here so they are not rediscovered downstream.

* The reruns are **not** bitwise reproductions: different GPU, different CUDA
  and torch. Agreement is reported numerically rather than asserted.
* **TF32 was checked, not assumed.** An RTX 3080 is Ampere and can silently use
  TF32 where the 2080 Ti cannot, which would be a change of arithmetic regime
  rather than ordinary rounding noise. On the run environment
  `torch.backends.cuda.matmul.allow_tf32` is `False` and
  `torch.get_float32_matmul_precision()` is `highest`, so the matmul path is
  full FP32. (`cudnn.allow_tf32` is `True` but GPT-2 has no convolutions.) The
  ~1e-6 frozen-CE agreement in §4 independently confirms this: TF32 would show
  up around 1e-3.
* **The released `pi_bar` is the array the selector actually consumed.** A
  design review raised the possibility that averaging float64 copies could
  differ from the average ALTA computed. It does not: `core/alta.py` already
  upcasts each prediction vector with `np.asarray(..., dtype=float)`, i.e. to
  float64, before averaging, and float32 to float64 is exact. This is confirmed
  empirically rather than argued — dispersion recomputed from the released
  arrays equals each run's own retained `alta.dispersion` to **exactly 0.0**
  (column "vs this run's own record" in `VERIFY_SUMMARY.md` §B).
* **Corpus identity for the two rebuilt domains rests on check A**, not on the
  dataset revision alone. The published run retained no token-level
  fingerprint, so identity had to be established through frozen-CE agreement.
  `experiments/ttt/e4_gpt2/vec_rerun/corpus_fingerprint.py` now emits per-document SHA-256 over the exact
  1024 token ids for all four domains
  (`e3_vectors/corpus_fingerprints.json`), so any future rerun can prove
  corpus identity directly instead of inferring it.
* **Resume was not exercised.** The partial-checkpoint files key only on
  `(domain, adapt, seed)` and do not bind corpus or revision, so a resume
  across a changed corpus could in principle mix runs. No job resumed — the
  logs contain no `resume:` line — so every artefact here is a single
  uninterrupted RTX 3080 run. Anyone reusing this runner across a data change
  should add a run fingerprint to the partial files first.
* Gap 2 is closed by the retained m0 records and not by this directory; see §3.
