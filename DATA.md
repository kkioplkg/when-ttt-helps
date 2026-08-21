# Data availability

This repository holds **code and the small analysis outputs**. The bulk record
sets are not stored in the Git tree: they are large, they are write-once, and Git
is the wrong tool for them. They are **published as versioned release assets of
this repository**, which is public, so they download with a plain `curl` and no
account:

> **[Release `v1.0.7`](https://github.com/kkioplkg/when-ttt-helps/releases/tag/v1.0.7)** — seven assets, listed below with their exact
> sizes and SHA-256s. The release notes carry the same digests, computed from
> the uploaded files.

This is a versioned publication, not an archival preservation service, and it
carries **no DOI**; nothing here claims otherwise.

> **Cite `v1.0.7`.** Seven earlier releases are left in place as a historical
> record and must not be used. `v1.0.0`'s `release_archive.zip` was replaced
> in place more than once while the surrounding documentation was still being
> corrected, so that version name never denoted one byte object, and its tag
> snapshot predates the corrected data-availability wording — no digest for it
> is published anywhere. `v1.0.1` and `v1.0.2` were each sound in their assets
> and are superseded only because a later correction wave moved something:
> `v1.0.1` because the archive was rebuilt, `v1.0.2` because two published
> side manifests in its tag snapshot still carried superseded availability
> text; `v1.0.3` because its release note still described
> `e3_vectors_replicas.zip` by the wrong census; `v1.0.4` because two
> generated documents still carried a superseded one-line description of what
> the historical runs recorded, and because the reconciler's own
> cross-environment claim count was one too high; `v1.0.5` because a new
> experiment --- the seed-matched re-measurement of `delta_feat` --- landed in
> the archive and brought two further assets with it; and `v1.0.6` because the
> manuscript sources were revised for writing quality and six figures were
> regenerated, so the archive that carries them was rebuilt. No measurement
> record changed in that pass, and no number moved. Every one was superseded
> rather than edited, because editing a published release is the defect being
> avoided — with one narrow exception, stated so it is not mistaken for
> silence: **release *notes* are corrigible metadata and are corrected in
> place when they state something false**, with the correction disclosed on
> the release itself. Assets and tags are never touched. `v1.0.7` is the release whose
> assets, notes, tag snapshot and this file all describe the same bytes. Every
> digest below is `v1.0.7`'s.

## What you can do without the large data

Every number printed in the paper has its analysis JSON **in this
repository**. Re-deriving those JSONs from scratch needs the raw records;
*checking* them does not. One distinction is worth keeping:
`tools/r9_reconcile.py` **machine-binds 508 curated claims** and fails on a
mismatch or an orphan, while the remaining printed numbers are recomputable
from their analysis JSON without being in that curated set — so "traceable"
is the right word for those, not "bound". Concretely:

| Task | Needs a release asset? |
|---|---|
| Read any headline number and trace it to its source JSON | no |
| Re-run the theorem checks (README Level 1) | no |
| Re-run the independent closure verifier's report | no — `results/is_fresh/closure/json/VERIFY_FINAL.json` ships here |
| Regenerate main Figs. 4, 5 and 6 from the analysis JSONs (README Level 2) | no |
| Regenerate main Figs. 7 and 8, and supplement Table S5 | **yes** — they read the per-instance CIFAR/GPT-2 traces, which are inside `release_archive.zip` |
| Re-derive the analysis JSONs from the raw per-instance records | **yes** |
| Re-train the source models and re-measure from scratch | **yes** (plus GPU time) |

Two artefacts need neither a release asset nor a GPU but *do* need the manuscript, which is not in
this repository: supplement Tables S4 and S7 regenerate from records that ship here, but their
`--check` mode is a byte comparison against the manuscript's own `.tex` fragment, and
`tools/r9_reconcile.py` binds curated claims to the text of both documents. Run those three from
`release_archive.zip`, which carries the manuscript sources, rather than from here.

## The archives

Every asset is at `https://github.com/kkioplkg/when-ttt-helps/releases/download/v1.0.7/<name>`. Download and check one
with:

```bash
curl -sSL -O https://github.com/kkioplkg/when-ttt-helps/releases/download/v1.0.7/closure_records.zip
sha256sum closure_records.zip
```

Every archive additionally carries a **per-member** manifest inside
`release_archive.zip`, so any of them can be checked file by file rather than
only against its whole-archive digest. For the two whose members carry
compression of their own the manifest also digests the decompressed bytes,
which is the digest that survives a rebuild at a different compression level;
the seed-matched records are plain JSON, so there a second digest would be the
first one again.

### 1. `closure_records.zip` — closure-experiment records

The per-measurement records behind the binary entropy/calibration identity
check on trained networks.

| | |
|---|---|
| size | 133,340,682 bytes (127.2 MiB) |
| sha256 | `f0b4ae6b9586a3822f140821197af068729699fafe31af1aee43dcaa44037bb0` |
| contents | 71 `.jsonl.gz` record files, 120,100 records, 133,324,801 bytes uncompressed-as-stored |
| unpacks to | `results/is_fresh/closure/records/` |

A member-by-member manifest **ships in this repository** at
`results/is_fresh/closure/CLOSURE_RECORDS_MANIFEST.json`, with a
per-file `sha256` (of the `.jsonl.gz` as stored) and `sha256_uncompressed` (of
the decompressed bytes, which survives a rebuild at a different gzip level).
So the archive can be verified file by file rather than against a single
whole-archive digest. `MANIFEST_staged.sha256` and `MANIFEST_source.sha256` in
the same directory cover the same set.

These are the records that back the "zero violations in 358,709 measurements"
claim; the verifier's own recomputation report
(`closure/json/VERIFY_FINAL.json`, field `route3_n_tested` = 358709,
`route3_violations_recomputed` = 0) is in this repository.

### 2. `e3_vectors_replicas.zip` — E3 language-model replica payloads

Per-token adaptation vectors for the GPT-2 domain-shift replicas.

| | |
|---|---|
| size | 62,525,322 bytes (59.6 MiB) |
| sha256 | `22783827059b250cc5e35f4694ddb649aa3b816c3aba97006c7e8ee44004751e` |
| contents | **13 members**: 12 full-replica `.npz` payloads (`{code,legal,pubmed,wikitext}_ln_s{0,1,2}_vectors_full.npz`, 72 arrays in all) and one `README.md`. This is the archive's own census, from `REPLICAS_MANIFEST.json`; the per-example `.json` records and the reduced `*_vectors.npz` arrays are **not** here — they ship inside `release_archive.zip` |
| unpacks to | `results/is_fresh/e3_vectors/` |

The manifests and provenance for this set **do** ship here:
`results/is_fresh/e3_vectors/REPLICAS_MANIFEST.json`,
`PROVENANCE.md`, `VERIFY_SUMMARY.md`, `verify_report.json` and
`corpus_fingerprints.json`.

### 3. `release_archive.zip` — the complete reproducibility bundle

| | |
|---|---|
| size | 64,241,298 bytes (61.3 MiB) |
| sha256 | `f3b7103041017d4105a47013930eb27fc39409bfba13c0c9983dd72805d7c0a3` |
| contents | 672 members, of which 10 are root files the packager generates at build time; `GENERATED_MANIFEST.json` hashes the other 9, because it cannot hash itself; 237,632,321 bytes uncompressed |

This repository is a **subset** of that bundle: the code, the operational
docs, and every analysis output under ~1.1 MB. What the bundle adds is the raw
per-instance result JSONs listed below. The bundle is produced by
`tools/make_release_zip.py`, which is in this repository, so it can
be rebuilt.

### 4. `seedmatch_records.zip` — seed-matched re-measurement records

The raw per-episode records behind the seed-matched re-measurement of
`delta_feat`: the crossed measurement matrix (every episode measured through
each of three fresh source networks) and the six exposed adaptation runs.

| | |
|---|---|
| size | 10,164,095 bytes (9.7 MiB) |
| sha256 | `aa1701ebe4fbbd609d49388b1a56c7f1d3e051d8b58cdf6b6bd4955b79b5d3fc` |
| contents | **13 members**: 12 record files holding 165,465 per-episode records (58,128,240 bytes of plain JSON) and one `README.md` |
| unpacks to | `results/is_fresh/seedmatch/records/` |

This exclusion is **declared, not inherited**, and the distinction is worth
one sentence. The closure records are `.gz`, which the packager drops by
construction; these are plain `.json` under `results/is_fresh/`, which the
packager's recursive walk would otherwise ship. Leaving them out is therefore
a decision, recorded in `tools/make_release_zip.py` in two places that must
agree — `RESULT_EXCLUDE_PREFIXES`, which enforces it, and `DROPPED_PAYLOAD`,
whose reason string is printed into `INDEX.md`. Everything needed to *check*
a printed number ships here, under `results/is_fresh/seedmatch/`: the analysis
JSONs, the frozen episode manifest, the six source-model evaluation records,
the suite's code, its design and results documents and its two hash lists.

### 5. `checkpoints_seedmatch.zip` — the six retained source networks

| | |
|---|---|
| size | 15,137,236 bytes (14.4 MiB) |
| sha256 | `d6ef8edfe32e563481774a8072f3f15981d389f5e3c0c5cfcb32270d4817097f` |
| contents | **9 members**: 6 ResNet-26+GroupNorm source checkpoints (16,211,929 bytes of weights), the two reconstruction-head records the masking objective needs, and one `README.md` |
| unpacks to | `experiments/ckpt/seedmatch/` |

These are the networks every seed-matched number was measured through, so that
experiment can be **re-measured rather than re-trained**. They are published
separately because model weights cannot ship inside `release_archive.zip` at
all: the packager drops `.pt` by construction.

**They do not recover the eleven lost source checkpoints.** They belong to a
family retrained afterwards under a different execution stack — fresh
realizations of the same nominal recipe, not the weights the published grid
adapted — so the published grid's seed-resolved measurement stays
unreconstructible. What they close is narrower and worth having: the suite
that measured what those lost checkpoints cost did retain its own.

## Raw record sets held back from this repository

Paths below are this repository's, which is where each set unpacks to. The
release assets carry the same trees one level down, under `experiments/`; the
README's "Layout" note gives the full prefix map.

| Path | Files | Size | What it is |
|---|---:|---:|---|
| `results/e2/` | 24 | 140.1 MB | CIFAR-10/100-C per-instance adaptation traces (TENT, TTT-rot, TTT-mask, PL; main runs, batch sweeps, calibration) |
| `results/e4/` | 15 | 15.9 MB | GPT-2 per-document adaptation traces across `wikitext`/`pubmed`/`code`/`legal` |
| `results/e5/` | 12 | 10.2 MB | feature-shift (`delta_feat`) and LR-ablation per-instance dumps |
| `results/is_fresh/e3_vectors/` | 24 | 35.6 MB | the `.npz` + per-example `.json` payloads described above |
| `results/is_fresh/e2_gn/` | 3 | 17.3 MB | GroupNorm-lane per-instance JSONs (`cifar10_tent_main`, `f15_partial_cells`, `delta_feat_fresh`) |
| `results/is_fresh/closure/records/` | 71 | 128 MB | the closure records (`closure_records.zip`) |
| `results/is_fresh/seedmatch/records/` | 12 | 58.1 MB | the seed-matched re-measurement's crossed matrix and exposed adaptation runs (`seedmatch_records.zip`) |

Small companions to each of these — source gates, progress logs, per-seed
training summaries, reference files — **are** in this repository, so the shape
of each set is visible even without the payloads.

## The pretrained language model

This file is the data-asset census and does not repeat the model-provenance
statement; it points at it. The GPT-2 weights are **not** redistributed here or
in any asset. Two facts about them are kept apart — the *historical* runs
recorded **no model field at all** in their retained per-document JSON, the
bare name `gpt2` coming from the shipped runner source, while the
*reproduction* loader is pinned to `openai-community/gpt2` at revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e` with the weight digest recorded, and
the pinned rerun reproduces the retained records. The full two-part statement,
with the agreement figures that make the pin informative, is in
[`README.md`](README.md), in [`COMMANDS.md`](COMMANDS.md) under "External
inputs a complete regeneration needs", in [`INDEX.md`](INDEX.md), and in
[`results/is_fresh/e3_vectors/PROVENANCE.md`](results/is_fresh/e3_vectors/PROVENANCE.md).

## Model checkpoints

Not in the Git tree, and published as release assets of their own:

- `results/is_fresh/e2_gn/cifar10_resnet26ttt_s20260806.pt` — 2,640,259 bytes
- `results/is_fresh/e2_gn/f15_train_partial.pt` — 2,638,813 bytes

| file | sha256 |
|---|---|
| `cifar10_resnet26ttt_s20260806.pt` | `cdf63d2f079f7f3febabd4765824369ba8fffc7bc54e321fcb4f4bd347e19611` |
| `f15_train_partial.pt` | `7588e5ef3908a54efb6644e6df4b44016d521f8af7bc9f8308a72bdcedbefe01` |

Both are also reproducible from `ttt/e2_cifar/train_source.py` with the seeds
recorded in `SEEDS.md`, though not bit-identically. **The other eleven source
checkpoints did not survive and are not recoverable** — no asset substitutes
for them, and the supplement's clean-accuracy paragraph rests on the retained
per-seed evaluation records instead.

A second, later family **was** retained in full: the 6 ResNet-26+GroupNorm
source networks the seed-matched re-measurement trained, published as
`checkpoints_seedmatch.zip` (§5 above) with the per-member digests in
`results/is_fresh/seedmatch/SEEDMATCH_CHECKPOINTS_MANIFEST.json` and in that
directory's `MANIFEST.md`. Those six are a different family and recover none of
the eleven.
