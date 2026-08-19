# Data availability

This repository holds **code and the small analysis outputs**. The bulk record
sets are not stored here: they are large, they are write-once, and Git is the
wrong tool for them. They will be deposited as a versioned archive with a DOI.

> **DOI: TBD** — the deposit has not been made yet. This line will be replaced
> with the resolved DOI once the archive is registered. Until then, the
> archives are available from the authors on request.

## What you can do without the large data

Every number printed in the paper is bound to an analysis JSON **that is in
this repository**. Re-deriving those JSONs from scratch needs the raw records;
*checking* them does not. Concretely:

| Task | Needs the DOI deposit? |
|---|---|
| Read any headline number and trace it to its source JSON | no |
| Re-run the theorem checks (README Level 1) | no |
| Re-run the independent closure verifier's report | no — `results/is_fresh/closure/json/VERIFY_FINAL.json` ships here |
| Regenerate main Figs. 4, 5 and 6 from the analysis JSONs (README Level 2) | no |
| Regenerate main Figs. 7 and 8, and supplement Table S5 | **yes** — they read the per-instance CIFAR/GPT-2 traces |
| Re-derive the analysis JSONs from the raw per-instance records | **yes** |
| Re-train the source models and re-measure from scratch | **yes** (plus GPU time) |

Two artefacts need neither the deposit nor a GPU but *do* need the manuscript, which is not in
this repository: supplement Tables S4 and S7 regenerate from records that ship here, but their
`--check` mode is a byte comparison against the manuscript's own `.tex` fragment, and
`tools/r9_reconcile.py` binds curated claims to the text of both documents. Run those three from
`release_archive.zip`, which carries the manuscript sources, rather than from here.

## The archives

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
| contents | 12 `.npz` vector payloads (`{code,legal,pubmed,wikitext}_ln_s{0,1,2}_vectors.npz`, ~1.6 MB each) and their 12 matching per-example `.json` (~1.38 MB each) |
| unpacks to | `results/is_fresh/e3_vectors/` |

The manifests and provenance for this set **do** ship here:
`results/is_fresh/e3_vectors/REPLICAS_MANIFEST.json`,
`PROVENANCE.md`, `VERIFY_SUMMARY.md`, `verify_report.json` and
`corpus_fingerprints.json`.

### 3. `release_archive.zip` — the complete reproducibility bundle

| | |
|---|---|
| size | 62,928,529 bytes (60.0 MiB) |
| sha256 | `d40602e17e093158f2143a47f120384be30d72d7b8e780a5f0f008adc6b72989` |
| contents | 637 members, of which 9 are the root files the packager generates at build time (`GENERATED_MANIFEST.json` lists exactly those 9); 234,403,061 bytes uncompressed |

This repository is a **subset** of that bundle: the code, the operational
docs, and every analysis output under ~1.1 MB. What the bundle adds is the raw
per-instance result JSONs listed below. The bundle is produced by
`tools/make_release_zip.py`, which is in this repository, so it can
be rebuilt.

## Raw record sets held back from this repository

Paths below are this repository's, which is where each set unpacks to. The
deposit and `release_archive.zip` carry the same trees one level down, under
`experiments/`; the README's "Layout" note gives the full prefix map.

| Path | Files | Size | What it is |
|---|---:|---:|---|
| `results/e2/` | 24 | 140.1 MB | CIFAR-10/100-C per-instance adaptation traces (TENT, TTT-rot, TTT-mask, PL; main runs, batch sweeps, calibration) |
| `results/e4/` | 15 | 15.9 MB | GPT-2 per-document adaptation traces across `wikitext`/`pubmed`/`code`/`legal` |
| `results/e5/` | 12 | 10.2 MB | feature-shift (`delta_feat`) and LR-ablation per-instance dumps |
| `results/is_fresh/e3_vectors/` | 24 | 35.6 MB | the `.npz` + per-example `.json` payloads described above |
| `results/is_fresh/e2_gn/` | 3 | 17.3 MB | GroupNorm-lane per-instance JSONs (`cifar10_tent_main`, `f15_partial_cells`, `delta_feat_fresh`) |
| `results/is_fresh/closure/records/` | 71 | 128 MB | the closure records (`closure_records.zip`) |

Small companions to each of these — source gates, progress logs, per-seed
training summaries, reference files — **are** in this repository, so the shape
of each set is visible even without the payloads.

## Model checkpoints

Not deposited in either archive and not in this repository:

- `results/is_fresh/e2_gn/cifar10_resnet26ttt_s20260806.pt` — 2,640,259 bytes
- `results/is_fresh/e2_gn/f15_train_partial.pt` — 2,638,813 bytes

Both are reproducible from `ttt/e2_cifar/train_source.py` with the
seeds recorded in `SEEDS.md`. They will be added to the DOI deposit alongside
the record archives.
