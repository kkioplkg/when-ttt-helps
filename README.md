# When Does Single-Instance Test-Time Adaptation Help?

**An exact phase law for test-time training in a solvable model, the class-level information
limit around it, and the entropy--alignment identity behind the mechanism.**

Test-time training (TTT) adapts a model to a single unlabeled test instance by self-supervised
descent. This paper settles *when that helps*, exactly, inside a solvable linear model. Because
the protocol executes whole steps, the criterion is an integer one: for step sizes `η ≤ 1/2` and
at `η = 1`, some executable step count lowers excess risk exactly when the first step does, i.e.
when `α²δ²(2 − ηα²) > ησ²`, for label-measured alignment `α`, initial excess risk `δ²` and
label-free per-coordinate noise `σ²`. Where an interior optimum exists within the horizon the
optimal count is its integer neighbour, and the gain is capped at `2α²δ²`. Two results bound that
answer rather than extend it: two environments can emit identical scalar self-supervised
transcripts, so no label-free rule improves on freezing, uniformly over a nested environment
class; and away from degenerate cases entropy minimization injects no auxiliary randomness, its
binary first-order alignment sign being exactly its pointwise calibration sign.

This repository contains the experiment runners, the fresh re-analysis suite that recomputes
every printed number from the records, the closure measurement and verification suite, the
figure and table generators, **and the analysis records behind all of them** (`results/`, see
below). What it deliberately does not contain is the manuscript and the bulk raw record sets:
the per-instance CIFAR/GPT-2 traces, the closure `.jsonl.gz` records, the E3 replica payloads and
the source checkpoints are published as **versioned release assets of this repository**
([release `v1.0.7`](https://github.com/kkioplkg/when-ttt-helps/releases/tag/v1.0.7)), described
file by file with sizes and SHA-256 in [`DATA.md`](DATA.md). The split is deliberate and the
boundary is the useful one — **every printed number has its analysis JSON here**, so checking a
number needs nothing downloaded; only re-deriving one from raw records does. Stated exactly,
because "bound" and "traceable" are not the same guarantee: `tools/r9_reconcile.py`
machine-binds **508 curated claims** to their records and fails on a mismatch or an orphan;
every other printed number has an analysis JSON it is recomputable from, but is not necessarily
in that curated binding set. `r9_reconcile.py` says so of itself, and names examples it does not
bind.

> **Paper:** *When Does Single-Instance Test-Time Adaptation Help? An Exact Phase Law in a
> Solvable Model* (under review). The citation will be finalized on publication.

## Reproduce the paper in 3 levels

Start here. Everything below this section is the audit detail; these are the three things a
reader actually wants to run, in increasing cost. Install
`requirements-analysis.txt` first (see [Requirements](#requirements)); Levels 1 and 2 are CPU
only and need no download, no GPU and no checkpoint.

**Level 1 — check the theorems. Three commands, minutes, no records needed beyond what ships.**

```bash
cd ttt/is_fresh
python f18_integer_boundary_check.py     # the integer criterion: "some executable step helps"
                                         # against "the first step helps", on the shipped grid
python f36_flow_integer_bridge.py        # the flow curve is not the exact curve, and the
                                         # exact-criterion repair, closed form only
python f33_pl_envelope_monotonicity.py   # the local-PL envelope: what is and is not monotone
```

Each prints its verdict and rewrites its own JSON under `results/is_fresh/`. Those rewrites are
**byte-identical to the copies committed here**, so `git status` staying clean after a run is
itself the check.

**Level 2 — regenerate the figures whose inputs ship. One command, minutes.**

```bash
mkdir -p repro && cd ttt/is_fresh && for f in fig_f1_curves fig_f2_phase fig_f4_e2; do python $f.py --out ../../repro/$f.pdf; done
```

That is main Fig. 4 (re-simulated from the seeds, and it asserts it replays the committed `f7`
records cell for cell), main Fig. 5 and main Fig. 6. **Pass `--out`**: their built-in default
points at the authoring tree, not at this one.

Two more printed figures and two supplement tables are *not* at this level, and the reason is
stated rather than left to be discovered: main Fig. 7 (`fig_F6.py`) and Fig. 8
(`fig_f8_domains.py`) read the per-instance CIFAR and GPT-2 traces, and supplement Table S5
(`tools/tab_s5_e2_batch.py`) reads the CIFAR batch-sweep traces — all three record sets are in
the release assets, not in the Git tree (see [`DATA.md`](DATA.md)). Supplement Tables S4 and S7
(`tools/tab_s4_e1_gates.py`, `tools/tab_s7_e4_proxy.py`) regenerate from records that *do* ship,
but their `--check` mode compares against the manuscript's own `.tex` fragment, and the
manuscript is not in this repository; run them against the reproducibility archive instead.
`tools/r9_reconcile.py`, which binds every curated claim to its evidence file, needs both
documents for the same reason and likewise runs from the archive.

**Level 3 — reconstruct from raw records.** Download the
[release assets](https://github.com/kkioplkg/when-ttt-helps/releases/tag/v1.0.7), verify each
against the per-member manifests that ship inside `release_archive.zip`, and unpack them into the
paths [`DATA.md`](DATA.md) names. That is enough to re-derive every analysis JSON from the
per-instance records. Re-running the *original* CIFAR-10/100-C and GPT-2 experiments on top of
that additionally needs a GPU and the third-party datasets and model weights, which are not ours
to ship; [`COMMANDS.md`](COMMANDS.md) gives every command in dependency order and names each
external input.

---

See [`COMMANDS.md`](COMMANDS.md) for the full protocol: every command in dependency order, the
external inputs a complete regeneration needs, and what each script reads and writes.
[`INDEX.md`](INDEX.md) is the file-by-file index, with the omissions and the reason for each;
[`SEEDS.md`](SEEDS.md) is every seed, per experiment.

## Requirements

- **Python 3.10.9 is the tested interpreter, and this is a pin rather than a preference**:
  `scipy==1.15.3` requires ≥ 3.10 and `numpy==1.23.5` publishes no wheel for 3.12. See
  [`BUILD_INTERPRETER.md`](BUILD_INTERPRETER.md) for the policy and the recorded build machine
- NumPy, SciPy, Matplotlib. PyTorch only for the three scripts that touch a tensor
- A GPU only for the original runners and for two scripts in the re-analysis suite; everything
  that recomputes a printed number runs on CPU

```bash
python -m venv .venv                  # on Python 3.10.9
. .venv/bin/activate                  # Windows: .venv\Scripts\activate
python -m pip install -r requirements-analysis.txt
```

Nothing here needs an environment variable to recompute a number. The GPU runners do: the Python
ones default to a relative `workdir/` and take `--data-root`, `--ckpt-dir` and `--out-dir`, and
the three shell drivers under `ttt/e4_gpt2/vec_rerun/` open with

```bash
R="${TTT_ROOT:?set TTT_ROOT to the project root on the run host}"
```

so an unset `TTT_ROOT` stops the script with exit status 1 and that message rather than writing
into the wrong tree. Export it to the project root on the run host before invoking any of them.

`requirements-analysis.txt` is the file to install. It covers every script under `ttt/is_fresh`
and `figures/` **except** the two that need a GPU — `f15_e2_entropy_gn.py`, which trains and
samples, and `f_scope_bench.py`, a wall-clock benchmark that recomputes no printed number. Torch
is *not* dragged in by the re-analyses (`ttt/core/utils.py` imports it lazily); the three shipped
scripts that do import it are `f6_relu_multiseed.py`, `f15_e2_entropy_gn.py` and
`f_scope_bench.py`. The original GPU runners under `ttt/e2_cifar` and `ttt/e4_gpt2` have their
own recorded environment in `requirements-experiment.txt`, and `pip-freeze-full.txt` is the
complete freeze of the machine that produced the numbers. One superseded line survives in
`requirements-analysis.txt` on purpose; `provenance/README.md` says which, and why correcting it
would falsify the record.

## Repository layout

```
COMMANDS.md            every command, in dependency order -- the entry point
INDEX.md               file-by-file index, with the omissions and their reasons
SEEDS.md               every seed used, per experiment
DATA.md                the release assets: what is held back, with sizes and SHA-256
MANIFEST.json          sha256 + size for every archive file
AUDIT_MAP.json         claim -> evidence-file map for the manuscript
GENERATED_MANIFEST.json  which shipped files are generated, and by what
BUILD_INTERPRETER.md   the tested interpreter and the recorded build machine

ttt/core/              shared adaptation, ALTA and utility code
ttt/e1_synthetic/      E1 -- the solvable linear model (run_e1.py is also the
                       simulation kernel the fresh suite imports unchanged)
ttt/e2_cifar/          E2 -- CIFAR-10/100-C source training, adaptation, delta-feat
ttt/e4_gpt2/           E4 -- GPT-2 domain-shift runners, plus vec_rerun/ replicas
ttt/analysis/          shared aggregation helpers, record SCHEMAS.md, fixtures
ttt/is_fresh/          the fresh re-analysis suite: f1..f41, fig_*, tab_*, and the
                       RESOLVER_ and VERIFY_ transcripts. This is what recomputes
                       the printed numbers; nothing in it is scored with the
                       paper's own closed forms, and its seeds (20260801+) are
                       disjoint from every seed the original pipeline used
figures/               the figure and table generators of the earlier round, and
                       figures/_superseded/ for the ones a later generator replaced
tools/                 packaging, reconciliation and manuscript-gate tooling:
                       make_release_zip.py builds the release archive, r9_reconcile.py
                       binds every curated claim to its evidence file
provenance/            the four dependency records, shipped verbatim, and
                       BUILD_ENVIRONMENT.md -- the reference build environment
results/m0/            source-model evaluation summaries (12 JSON)
results/is_fresh/      the released analysis records -- the JSONs the numbers cite
  closure/             the closure experiment as a self-contained unit: code/,
                       json/ (incl. VERIFY_FINAL.json), DESIGN.md, RESULTS.md,
                       and its record manifests
  e3_vectors/          E3 replica manifests, provenance and verification reports
  e2_gn/               GroupNorm-lane source gate and progress log
```

## Released results

`results/` holds **360 files under `is_fresh/` and 12 under `m0/`**: 207 analysis JSONs and 25
run logs at the top of `is_fresh/`, plus three self-contained subtrees. The convention across the
suite is one `*_summary.json` per script, next to the per-seed records it was computed from, so a
recomputation can be diffed against the committed copy file by file rather than eyeballed.

| Tree | Contents | Backs |
|---|---|---|
| `results/is_fresh/*.json` | 207 JSON + 25 `.log` + `FRESH_RESULTS.md` | the whole fresh suite: the solvable-model measurements (f1, f2, f3, f7, f10, f18, f33, f35, f36), the E2 cross-fit family (f8, f8b, f22*, f23, f24, f27, f34), the E3/E4 interval work (f11, f12, f17, f29, f30, f31, f32) and the reporting audits (f26, f37) |
| `results/is_fresh/closure/` | 84 JSON + 22 code files + `DESIGN.md`, `RESULTS.md`, three manifests | the entropy--calibration identity on trained networks. `json/VERIFY_FINAL.json` is the verifier's own recomputation: `route3_n_tested` = 358709, `route3_violations_recomputed` = 0 |
| `results/is_fresh/e3_vectors/` | 12 JSON/MD | the GPT-2 replica set: `REPLICAS_MANIFEST.json`, `PROVENANCE.md`, `VERIFY_SUMMARY.md`, `verify_report.json`, `corpus_fingerprints.json` and the `wikitext_ref` references |
| `results/is_fresh/e2_gn/` | 3 | the GroupNorm lane's source gate and progress log |
| `results/m0/` | 12 JSON | source-model evaluation for the two architectures on CIFAR-10/100, three seeds each |

**Not released here.** Seven sets are held back and every one of them is described in
[`DATA.md`](DATA.md) with its file count, byte size and SHA-256: the per-instance CIFAR-10/100-C
traces (`e2/`, 24 files, 140.1 MB), the GPT-2 per-document traces (`e4/`, 15 files, 15.9 MB), the
feature-shift dumps (`e5/`, 12 files, 10.2 MB), the E3 replica `.npz` payloads (24 files,
35.6 MB), the GroupNorm per-instance JSONs (3 files, 17.3 MB) and the closure records (71
`.jsonl.gz`, 128 MB) and the seed-matched re-measurement's per-episode records
(12 files, 58.1 MB). Two source checkpoints are held back as well, and are reproducible from
`ttt/e2_cifar/train_source.py` with the seeds in `SEEDS.md`, and are release assets in their own
right, as are the 6 seed-matched source networks, which were retained in full and
recover none of the eleven that were not. Every one of these is inside the seven assets of
[release `v1.0.7`](https://github.com/kkioplkg/when-ttt-helps/releases/tag/v1.0.7); `DATA.md`
gives each asset's size and SHA-256. There is no DOI, and no archival-preservation claim is
made.
Small companions to each held-back set — source gates, progress logs, per-seed summaries,
reference files — do ship, so the shape of every set is visible without its payload. The
manuscript sources and PDFs are not here at all; this is the code repository.

## Quick start — the closed-form results (run first)

These need no GPU, no dataset and nothing downloaded. They re-simulate the solvable model
from fresh seeds and check the integer criterion against the closed forms.

```bash
cd ttt/is_fresh
python f1_boundary_onestep.py         # one-step measured boundary
python f2_boundary_stopped.py         # selected-stopping measured boundary
python f10_oracle_grid.py             # one-step / oracle / selection error (run before f18, f3)
python f18_integer_boundary_check.py  # the integer criterion on the f10 grid
python f3_optimal_stopping.py
```

Each writes its `*_summary.json` into `results/is_fresh/` beside the committed copy, so `git
diff` after a run is itself the check. `f33_pl_envelope_monotonicity.py`, `f35_pl_zero_noise.py`
and `f36_flow_integer_bridge.py` are closed-form only and read no record at all.

## Reproducing the paper

[`COMMANDS.md`](COMMANDS.md) is authoritative and lists every command in dependency order, with
the ordering constraints spelled out (f10 before f18 and f3; f11 before f29 and f32; f12 before
f31; f17 before f30; f38 before f23; f23 before f24). Two of its sections do not apply to this
repository: "Building the two documents", because the manuscript sources are not here, and any
step that *re-derives* an analysis JSON from raw per-instance records, because those records are
in the release assets rather than the Git tree. Everything that *checks* a printed number runs
from a clean clone.

```bash
cd ttt/is_fresh

# Re-analyses of the recorded runs (CPU, minutes each)
python f11_e4_cluster_ci.py            # E4 document-clustered intervals
python f29_e4_pooled_ci.py             # pooled percentile intervals (needs f11)
python f32_e4_fixed_budget_ci.py       # the E3 fixed-budget arms (needs f11, f29)
python f12_e4_proxy_loo.py             # leave-one-domain-out proxy test
python f31_e4_proxy_pooled.py          # the same pooling for the proxy (needs f12)
python f17_e4_alignment_only.py        # alignment-only vs the full statistic
python f14_deltafeat_check.py          # delta_feat validation against severity
python f21_e2_coverage.py              # E2 entropy sign-separation coverage

# E2 with the corrected signed statistic -- these are the reported numbers
python f38_e2gn_deltafeat_fresh.py     # fresh-source delta_feat; run before f23
python f8_e2_crossfit.py  --statistic phase_feat --out-prefix f22_e2_crossfit_feat
python f8b_e2_crossfit_det.py --statistic phase_loss --out-prefix f22b_e2_crossfit_det
python f8_e2_crossfit.py  --statistic phase_loss --out-prefix f22c_e2_crossfit_loss
python f16_e2_gn_analysis.py --out-prefix f23_e2_gn
python f20_e2gn_loco_sensitivity.py --out-name f24_e2gn_loco_sensitivity.json
# The pre-correction f8/f16/f20 outputs ship unmodified, so the difference the
# sign makes stays auditable; regenerate them with --statistic phase_loss_unsigned.

# Audits and self-checks
python f26_e1_reporting_audit.py       # recomputes the E1 reported values
python f27_e2_identity.py              # identity-level overlap of the cross-fit split
python f37_relu_monotonicity_recount.py
python f39_e3_vector_selfcheck.py      # asserts the released arrays still support the claim

# The two manifest checks need their side archive; from a clean clone they have
# nothing to check against. Run them where the archive is, or skip them.
python f40_e3_replicas_manifest.py --check      # needs e3_vectors_replicas.zip
python f41_closure_records_manifest.py --check  # needs closure_records.zip
```

The closure result — **zero violations in 358,709 measurements** — is already recorded in
`results/is_fresh/closure/json/VERIFY_FINAL.json`. To recompute it from the records rather than
read it, fetch `closure_records.zip` per [`DATA.md`](DATA.md), unpack it to
`results/is_fresh/closure/records/`, and run `results/is_fresh/closure/code/verify_closure.py`.

Claim-to-file tracing goes through `AUDIT_MAP.json`; file integrity goes through `MANIFEST.json`
and the per-directory `MANIFEST_*.sha256` files.

## Figures and tables

All of these run on the released tree as cloned; none of them needs a GPU.

```bash
cd ttt/is_fresh
python f9_figure_data.py               # consolidated figure data
python fig_f1_curves.py --out ...      # risk curves (re-simulates and asserts the match)
python fig_f2_phase.py  --out ...      # the phase figure (needs f10)
python fig_f3_alta.py   --out ...
python fig_f4_e2.py     --out ...      # E2 (needs f22, f22b, f22c)
python fig_f8_domains.py --out ...
python tab_t4_e1_gates.py              # the E1 gate table
python tab_t6_e4_proxy.py              # the E4 proxy table
```

**Pass an explicit output path to the `fig_*` generators.** Their `OUT_DEFAULT` points into the
frozen figure tree of the earlier round, because that is where they wrote when they ran; without
`--out` they write there and not into this tree. `COMMANDS.md` repeats this warning at the block
itself. `figures/` holds the earlier round's generators (`fig_F5.py`, `fig_F6.py`, `fig_F7.py`,
`tab_T2.py`, `k3_baseline.py`, the shared `_style.py` and `bootstrap_ci.py`); the ones a later
generator replaced sit in `figures/_superseded/` with a README saying what replaced them. The
supplement's tables come from `tools/tab_s4_e1_gates.py`, `tools/tab_s5_e2_batch.py` and
`tools/tab_s7_e4_proxy.py`, and `tab_s5` reads a held-back tree.

## Data

The datasets and weights the runners consume — CIFAR-10/100 and their -C corruption sets,
WikiText-103, `ccdv/pubmed-summarization`, `codeparrot/codeparrot-clean-valid`,
`pile-of-law/pile-of-law`, and the pretrained `gpt2` — are third-party and are not redistributed
here. `COMMANDS.md`, "External inputs a complete regeneration needs", names each one, the file
that names it, and why it is absent; two consequences are stated there rather than left to be
inferred.

The first concerns the pretrained language model, and it is **two facts, not one**. The
*historical* experiment left no record of the model at all: the retained per-document JSON has
**no model field** — each `meta` carries the invocation, the timestamp and the torch and CUDA
versions, and nothing else — so those records neither fix the weights nor name them. What
identifies the model is the shipped runner source, which loads the bare name `gpt2`
(`ttt/e4_gpt2/run_e4.py`). The *reproduction* loader is **pinned** — repository `openai-community/gpt2`,
revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`, `model.safetensors` 548,105,171 bytes,
sha256 `248dfc3911869ec493c76e65bf2fcf7f615828b0254c12b473182f0f81d3a707` — and the pin is not
left as an assertion across that gap: the pinned rerun **reproduces the retained records of the
original runs**, agreeing to 6.2e-06 in frozen (`t=0`) continuation cross-entropy on all twelve
(domain, seed) jobs and to 1.50e-05 absolute (6.5e-07 relative) in fixed-budget perplexity at
`t=20`. That agreement is what makes the pin informative about the historical run rather than
only about future ones. The report is
[`results/is_fresh/e3_vectors/PROVENANCE.md`](results/is_fresh/e3_vectors/PROVENANCE.md) §2 and
§4 and `VERIFY_SUMMARY.md` beside it; the paper states the same two facts in its Data
availability statement and in supplement §S7.3.

The second is that the recorded GPU and torch build are part of the experimental conditions, so
a rerun on other hardware is a replication.

The record sets held back from this repository are in [`DATA.md`](DATA.md), with a per-file
manifest shipping here for the two that have one.

## Notes

- **Host paths.** The twelve runner and driver files that once carried the run host's absolute
  prefixes were sanitized *in the source tree*, not in this copy, so what ships here is what the
  archive ships. The substitution was prefix-only — `/root/autodl-tmp` to a relative `workdir/`,
  the conda interpreter paths to bare `python`/`pip`, and the drivers' project root to a required
  `TTT_ROOT` — leaving every flag, ordering, seed and path suffix byte-identical to what ran.
  `provenance/BUILD_ENVIRONMENT.md` §6.4 records the rules and names the prefixes it removed,
  which is why that one file still contains them: a record of a substitution that cannot name the
  substituted string is not a record. `pip-freeze-full.txt` keeps the conda-prefix and user-site
  locations for the same reason — they *are* the provenance evidence.
- **Layout, and which paths were rewritten.** This repository is laid out as a code repository,
  not as an extracted archive. Five prefixes differ from the reproducibility archive:

  | archive | here |
  |---|---|
  | `experiments/ttt/` | `ttt/` |
  | `experiments/results/` | `results/` |
  | `paper/is2/tools/` | `tools/` |
  | `paper/is2/provenance/` | `provenance/` |
  | `figures/scripts/` | `figures/` |

  The scripts' own root anchors were re-pointed to match, and so were the paths in
  `COMMANDS.md`, `SEEDS.md` and `DATA.md`, so a command from those docs resolves in a clean
  clone. **`INDEX.md`, `MANIFEST.json`, `AUDIT_MAP.json`, `GENERATED_MANIFEST.json`, the
  `provenance/` records and every JSON under `results/` keep the archive's paths on purpose**:
  the first four describe the archive (`INDEX.md` says as much in its own first paragraph), and
  the rest are records of runs that happened in that layout. Rewriting a record to agree with
  today's directory names is the falsification `provenance/README.md` argues against. References
  to `paper/is2/paper/` and `paper/is2/supplement/` are left everywhere: those are manuscript
  sources, and they are not here under any name.
- **Manifest digests.** The path sanitization above is now applied in the source tree rather
  than to the published copy, so the runners here *are* the archive's bytes and their `sha256`
  in `MANIFEST.json` matches. **456 of the 488 manifest-covered files in this repository match
  their manifest entry exactly.** The 32 that do not are the 31 scripts whose root anchor was
  re-pointed for the layout change — 17 under `ttt/is_fresh/`, 11 under `tools/`, 3 under
  `figures/` — plus `figures/_superseded/README.md`; `COMMANDS.md` and `SEEDS.md` were re-pathed
  too but are root entries the manifest does not cover. Every one of those edits is confined to
  a path constant or a path in prose. No result record, and nothing that carries a measurement,
  differs from the archive by a byte.
- The fresh suite never scores anything with the paper's own closed forms; a closed form appears
  only as a reference curve for a documented reproduction check whose tolerance the script
  states.
- Wherever a step, threshold or stopping time is chosen from noisy data, it is chosen on one
  block of replicates and scored on another. Nothing is selected and evaluated on the same
  sample.
- `provenance/` is copied forward rather than regenerated, on purpose: rendering those four files
  from whatever interpreter runs the packager would turn a record of the experiments into a
  record of the packaging session. `provenance/README.md` gives the argument and the failure it
  once caught.

## License

MIT, see [`LICENSE`](LICENSE). It covers the code and the result records in this repository. No
third-party dataset or model weight is redistributed here, so nothing in the repository falls
outside it; the inputs the runners fetch for themselves stay under their own hosts' terms, as the
LICENSE addendum and `COMMANDS.md` both record.

## Citation

```bibtex
@article{whenttthelps,
  title  = {When Does Single-Instance Test-Time Adaptation Help?
            An Exact Phase Law in a Solvable Model},
  author = {Junfei Yi and Yuxiang Wang},
  note   = {Under review},
  year   = {2026}
}
```
