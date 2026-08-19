# Exact commands, in dependency order

> **You are reading the repository copy.** This file originates in the
> reproducibility archive, where every path below resolves exactly as written.
> Here it is re-laid-out for the Git tree: five directory prefixes differ (the
> README's "Layout" note gives the map), the manuscript sources are **not** in
> this repository, and two things below therefore do not apply — the "Building
> the two documents" section, and any step that *re-derives* an analysis JSON
> from raw per-instance records, since those records are release assets rather
> than Git-tree files. Everything that *checks* a printed number runs from a
> clean clone. For the archive copy, open `release_archive.zip`.

## What this archive audits

The submission is a PAIR of documents: `paper/is2/paper/main.pdf`
(39 pp) and
`paper/is2/supplement/supplement.pdf` (55 pp).  Both ship here with their
sources, their build transcripts and their compiled bibliographies.  The
experiments they report are E1 (solvable model), E2 (CIFAR-10/100-C) and E4
(GPT-2 domains), and the records of those three, together with the fresh
re-analyses that produce every number either document prints, are what this
archive carries.

Records that support only material this submission does not contain are NOT
here, and their absence is a decision rather than an oversight.  `INDEX.md`
lists each omission with its reason; all of it remains complete and unchanged
in the frozen `paper/is/` tree, which is the home of record for it.

## Dependencies (stated precisely, each claim within its evidence)

* **Python: 3.10.9 tested; other versions untested.**  3.10.9 is the
  interpreter recorded in `BUILD_INTERPRETER.md`, the one that produced every
  number in the manuscript, and the one the pins were taken from.  Neither
  "Python 3.11+" nor "3.9--3.12 with the same pins" is supportable here.  The
  second is
  false
  on the pins themselves: `scipy==1.15.3` declares `Requires-Python >= 3.10`,
  which excludes 3.9, and `numpy==1.23.5` publishes no wheel for 3.12.  We
  make no compatibility claim we have not exercised: a claimed range would
  require a resolvable lock demonstrated on each interpreter in it.
* **numpy, matplotlib** -- required by everything below.
* **PyTorch is needed for the experiment runners, and NO LONGER for the
  re-analyses.**  It used to be needed for both: `common.py` imports
  `run_e1`, which imports `core.utils`, which did `import torch` at module
  scope -- so every pure-CPU, pure-numpy re-analysis in
  `ttt/is_fresh` inherited a hard torch dependency it never used,
  and the reproduction checks `make_release_zip.py` runs could not be run at
  all without the ML stack.  `core/utils.py` now imports torch lazily, inside
  the functions that actually touch a tensor, so `save_json` and the analysis
  path are pure numpy.  The consequence is concrete: **the packager's
  verification pass now runs to completion on an interpreter with no torch
  installed**, which is how the archive shipped with this submission was
  verified.

  A note on that pass, because the wording has been wrong here before.
  **Verification runs by DEFAULT.  There is no `--verify` switch; the only
  override is `--no-verify`, which turns verification off.**  `python
  make_release_zip.py --out <path>` therefore builds *and* verifies.
  Torch is still a genuine requirement for `f6_relu_multiseed.py` and
  `f_scope_bench.py`, which use it directly, and torch **and** torchvision
  **and** a GPU are still required by `f15_e2_entropy_gn.py` and by the
  original experiment runners under `ttt/{e2_cifar,e4_gpt2}`.

  **THE COMPLETE LIST, because `requirements-analysis.txt` contradicts this
  paragraph and cannot be corrected.**  Exactly three shipped scripts import
  torch: `is_fresh/f6_relu_multiseed.py` (CPU, and part of the documented
  re-analysis), `is_fresh/f_scope_bench.py` (a wall-clock benchmark that
  recomputes no manuscript number; needs torchvision and CUDA) and
  `is_fresh/f15_e2_entropy_gn.py` (needs torchvision, CUDA and the unshipped
  CIFAR tensors).  `figures/` imports it nowhere.  Every other
  documented command -- every other script in `ttt/is_fresh`,
  every figure and table generator, the reconciliation, and this packager's
  own verification pass -- runs on an interpreter with no torch at all.
  That is not an inference from the import graph: it is measured, by
  installing a `sys.meta_path` finder that raises on `torch` and any
  `torch.*` submodule and then importing `is_fresh/common.py`, which is the
  module that used to drag torch in.  The import succeeds and `torch` is
  absent from `sys.modules` afterwards.

  **The contradiction, named.**  Line 51 of the shipped
  `requirements-analysis.txt` reads *"torch is a HARD dependency of the
  CPU-only re-analyses too: is_fresh/common.py imports run_e1, which imports
  core.utils, which does `import torch` at module scope."*  That was true of
  the code when the record was written and is false of the code shipped
  here.  The line is **not corrected**, and the reason is a rule this
  archive applies everywhere else: the four files under
  `provenance/` are a byte-identical record of the interpreter and
  environment that produced the numbers, copied forward and regenerated by
  nobody, and asserted byte-identical to their originals on every build in
  the source tree.  Editing one to agree with today's code would turn a
  provenance record into a description of the current tree, which is exactly
  the failure mode `provenance/README.md` exists to prevent.  So the record
  keeps its line, this paragraph supersedes it, and the pin `torch==2.3.0`
  stays -- correctly, since `f6_relu_multiseed.py` is part of the documented
  analysis suite and does need it.  The build asserts that the superseded
  sentence is still present in the shipped record, so this paragraph cannot
  quietly describe a line that is no longer there.
* **Installing the dependencies.** Run

  ```
  python -m pip install -r requirements-analysis.txt
  ```

  **What that file is, and is not, sufficient for.**  It is sufficient for
  ANALYSIS REPRODUCTION: recomputing the numbers the two documents print
  *from the records shipped here*, on a CPU, with no download, no GPU and no
  checkpoint.  That is the operation every command in "The fresh suite"
  below performs.  It is **not** sufficient for ORIGINAL EXPERIMENTAL
  REGENERATION -- rerunning the CIFAR-10/100-C and GPT-2 experiments that
  produced those records -- and no requirements file could be: that needs
  external datasets, third-party model weights and a tokenizer, regenerated
  source checkpoints, generated corruption tensors, and a GPU.  The section
  "External inputs a complete regeneration needs" below enumerates them,
  derived from the shipped runners and records rather than written by hand.

  It is a focused lock -- comments plus plain `name==version` pins, nothing
  else -- and it is *dependency-resolvable*: `pip install --dry-run -r
  requirements-analysis.txt` against a clean Python 3.10.9 virtual
  environment resolves with no conflict.  The transcript is archived in
  `ttt/is_fresh/RESOLVER_TRANSCRIPT.md` section 2.

  **Do not install `requirements-experiment.txt`.**  It records the original
  GPU experiment environment and pip cannot reconstruct it: that environment
  holds `numpy==1.23.5` and `opencv-python==4.12.0.88` at the same time, and
  the OpenCV metadata requires numpy >= 2 on any Python >= 3.9, so pip exits
  with `ResolutionImpossible`.  The two coexist because they were installed
  by different installers into different site directories -- `numpy` by conda
  into the environment prefix, `opencv-python` by pip into the per-user site
  -- so the interpreter imports both although no single pip resolution would
  produce the pair.  The installer metadata and the conda transaction log
  that show this, together with the `pip install --dry-run` transcripts for
  all three requirement sets, are archived in
  `ttt/is_fresh/RESOLVER_TRANSCRIPT.md`; that file also records
  why the pair is a property of the on-disk installation layout rather than
  of conda's own solver, which would not produce it.
  The file names the conflict, gives a resolvable substitution
  (`opencv-python==4.9.0.80`, transcript in `RESOLVER_TRANSCRIPT.md` section
  2), and lists the GPU, dataset and checkpoint
  prerequisites that no requirements file can supply.

  Interpreter, OS and hardware metadata are in `BUILD_INTERPRETER.md`; the
  complete freeze of the build machine (a Windows/Anaconda environment, most
  of it unrelated to this project, but also pip-parseable) is in
  `pip-freeze-full.txt`.
* **The LaTeX side is pinned separately** in
  `provenance/BUILD_ENVIRONMENT.md`, which ships in this archive: TeX
  distribution and engine version, the version of every layout-affecting
  package as loaded, the exact build command for each of the two documents
  and why five passes, the expected page counts and PDF checksums, the
  disposition of every remaining overfull box, and why an independent rebuild
  can land on a different page count without any substantive difference. Read
  it before reporting a page-count mismatch.

## External inputs a complete regeneration needs

Everything below is required to rerun the ORIGINAL experiments and is NOT in
this archive.  Nothing below is required to recompute a printed number from
the shipped records.  The table is generated at packaging time by
`external_inputs()` in `make_release_zip.py`, which reads the identifiers out
of the shipped runners' own calls and out of the shipped records' own `meta`
blocks; the "named in" column is the file you can check each row against.

| what | identifier as the runner names it | named in | why it is not here |
|---|---|---|---|
| CUDA-linked torch build (recorded) | `2.8.0+cu128` | `results/m0/cifar100_resnet26ttt_s0.json, results/m0/cifar100_resnet26ttt_s1.json (+more)` | the archive was packaged on a CPU-only interpreter, so the pin in requirements-experiment.txt is the CPU wheel; the build named in the identifier column is the one that actually ran |
| GPU (recorded device) | `NVIDIA GeForce RTX 2080 Ti` | `results/m0/cifar100_resnet26ttt_s0.json, results/m0/cifar100_resnet26ttt_s1.json (+more)` | hardware; the original runs are not reproducible on CPU in any practical time, and results can differ across device and driver |
| corruption tensor set (external download or regeneration) | `CIFAR-10-C` | `ttt/e2_cifar/data.py` | tens of GB of image tensors; excluded by size, regenerable from the public release or from the shipped generation script |
| corruption tensor set (external download or regeneration) | `CIFAR-100-C` | `ttt/e2_cifar/data.py` | tens of GB of image tensors; excluded by size, regenerable from the public release or from the shipped generation script |
| dataset (Hugging Face hub) | `Salesforce/wikitext / wikitext-103-raw-v1` | `ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (Hugging Face hub) | `ccdv/pubmed-summarization / document` | `ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (Hugging Face hub) | `codeparrot/codeparrot-clean-valid` | `ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (Hugging Face hub) | `pile-of-law/pile-of-law` | `ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (torchvision download) | `CIFAR10` | `ttt/e2_cifar/data.py` | third-party dataset fetched by the runner at first use |
| dataset (torchvision download) | `CIFAR100` | `ttt/e2_cifar/data.py` | third-party dataset fetched by the runner at first use |
| distribution absent from the build interpreter | `datasets` | `ttt/e4_gpt2/prepare_data.py` | needed only by the original data-preparation scripts, which ran on separate machines; left unpinned rather than pinned to a version this build never saw |
| pretrained weights and tokenizer | `gpt2` | `ttt/e4_gpt2/delta_proxy_v2.py, ttt/e4_gpt2/prepare_data.py (+more)` | third-party model weights and tokenizer resolved from the hub by name at run time; the ORIGINAL runs recorded NEITHER the name nor a revision -- the retained per-document JSON has no model field at all, and the bare name comes from the shipped runner source -- so a re-fetch is not guaranteed to obtain the same weights.  The REPRODUCTION loader is pinned to revision 607a30d783dfa663caf39e06633721c8d4cfcd7e and the weight digest, and the pinned rerun reproduces the retained records -- see the two-part statement below the table |
| source checkpoints (*.pt) | `written by the shipped training scripts` | `ttt/e2_cifar/train_recon_head.py, ttt/e2_cifar/train_source.py` | excluded by size; regenerable with the shipped training scripts given the datasets above, but not bit-identically |

Two consequences are worth stating rather than leaving to be inferred.

**The model was resolved by NAME in the original runs; the reproduction
loader is pinned, and the pin is verified against those runs.**  These are
two different facts and neither may be written as the other.

* *Historical experiment -- the records do not identify the model at all.*
  The retained per-document JSON carries **no model field**: each `meta` holds
  the invocation, the timestamp and the torch and CUDA versions, and nothing
  about the model.  What identifies it is the shipped runner SOURCE, which
  loads the bare name `gpt2` (`ttt/e4_gpt2/run_e4.py`).  So the
  records neither fix the weights nor name them, and a bare re-fetch obtains
  whatever that name resolves to at the time it is run.
* *Reproduction loader -- pinned.*  The vector rerun and every loader after
  it pin repository `openai-community/gpt2`, revision
  `607a30d783dfa663caf39e06633721c8d4cfcd7e`, `model.safetensors`
  548,105,171 bytes, sha256
  `248dfc3911869ec493c76e65bf2fcf7f615828b0254c12b473182f0f81d3a707`.  The
  digest was read from the repository's own git-LFS pointer at that revision
  and re-verified against the downloaded file.
* *And the pin is not asserted across the gap -- it is checked.*  The pinned
  rerun **reproduces the retained records of the original runs**: frozen
  (`t=0`) continuation cross-entropy agrees to **6.2e-06** on all twelve
  (domain, seed) jobs -- a quantity with no RNG and no adaptation in it,
  hence a sharp test of which weights and which documents were seen -- and
  fixed-budget perplexity at `t=20` agrees to **1.50e-05** absolute
  (6.5e-07 relative) on all twelve.  That agreement is what makes the pin
  informative about the historical run rather than only about future ones.
  The full report is
  `results/is_fresh/e3_vectors/PROVENANCE.md` (section 2 and
  section 4) and `VERIFY_SUMMARY.md` (sections A and D) beside it.

**The recorded GPU and the recorded torch build are part of the
experimental conditions**, not incidental: the archive was packaged on a
CPU-only interpreter, floating-point reduction order differs across devices,
and a regeneration on other hardware is a replication rather than a rerun.

Every executable script in `ttt/is_fresh` appears below exactly
once.  The only file in that directory with no command line is `common.py`,
which is an imported module (paths, seed lists, JSON helpers) and has no
`main()`.

## Building the two documents

```
bash tools/build.sh          # main.pdf   -- pdflatex, bibtex, x4
bash tools/build_supp.sh     # supplement.pdf
bash tools/gates.sh          # the manuscript gate suite, all green
```

`gates.sh` is the executable form of the recipe in `BUILD_ENVIRONMENT.md`
section 6: build gate, rendered cross-reference artefact gate, the
process-vocabulary sweep of section 6.3, the three source-hygiene sweeps
of `source_hygiene.py`, the same-statement-in-both-documents gate of
`dup_statement_gate.py`, the release self-rebuild gate (in this tree and from
a clean extraction carrying no frozen parent), and the review-package
standalone build gate.  It needs `pdftotext` and `pdfinfo` on the path.
The three tools it drives that are also useful on their own —
`dup_statement_gate.py`, `xref_sync.py` and `supp_inventory.py` — have their
own entries under *The is2 manuscript tools* below.

## The fresh suite

```
cd ttt/is_fresh

# --- solvable-model measurements (CPU, minutes to ~1 h each) --------------
python f7_curve_match.py                 # risk-curve match, 5 seeds
python f1_boundary_onestep.py            # one-step measured boundary
python f2_boundary_stopped.py            # selected-stopping measured boundary
python f10_oracle_grid.py                # one-step / oracle / selection error
python f18_integer_boundary_check.py     # integer criterion on the f10 grid
#                                          (reads f10 records; run f10 first)
python f33_pl_envelope_monotonicity.py   # local-PL envelope: refutes global
#                                          monotonicity, certifies the
#                                          branch-wise statement; closed form
#                                          only, reads no record
python f35_pl_zero_noise.py              # local-PL envelope at sigtot = 0:
#                                          which constants are defined there,
#                                          which are not, and the non-strict
#                                          form of the zero-noise threshold;
#                                          closed form only, reads no record
python f36_flow_integer_bridge.py        # the flow curve is not the exact
#                                          curve: refutes the "a fortiori"
#                                          step and certifies the exact-
#                                          criterion repair; also exhibits
#                                          sigma = 0 as an admissible value
#                                          of the exact model's noise scale
python f3_optimal_stopping.py
python f5_batch_variance.py
python f6_relu_multiseed.py
python f37_relu_monotonicity_recount.py  # recounts BOTH readings of the
#                                          ReLU stress test's alpha-
#                                          monotonicity from the five
#                                          per-seed records: exact, and
#                                          at the runner's 0.02 tolerance

# --- re-analyses of the original records (CPU, minutes) -------------------
python f11_e4_cluster_ci.py              # E4 document-clustered intervals --
#                                          SUPERSEDED for its endpoints (it
#                                          averages five per-stream percentile
#                                          pairs); still the record for the
#                                          point estimates and the audit trail
#                                          f29 asserts against.  Run it first:
#                                          f29 reads its output.
python f12_e4_proxy_loo.py               # E4 leave-one-domain-out proxy test
#                                          -- SUPERSEDED for its interval
#                                          endpoints (it averages five
#                                          per-stream percentile pairs); still
#                                          the record for the selections and
#                                          the point estimates, and the audit
#                                          trail f31 asserts against.  Run it
#                                          before f31, which reads its output.
python f32_e4_fixed_budget_ci.py         # the E3 (GPT-2) FIXED-BUDGET arms,
#                                          on f11/f29's own draws.  This is
#                                          the record behind the primary E3
#                                          comparison: the improvement over
#                                          the frozen model at each recorded
#                                          budget t in {1,2,5,10,20}, its
#                                          document-clustered pooled
#                                          percentile intervals, and the
#                                          PAIRED difference against the
#                                          retrospective selector formed
#                                          inside every resample.  It
#                                          recomputes the selector arm and
#                                          asserts it reproduces f29's
#                                          endpoints to Monte Carlo zero,
#                                          which is what makes the paired
#                                          comparison exact.  Run it after
#                                          f11 and f29.
python f31_e4_proxy_pooled.py            # the same pooling for the proxy
#                                          validation: f12's own five
#                                          B = 2000 streams, pooled into a
#                                          single 10,000-draw empirical
#                                          distribution per quantity.  Every
#                                          proxy interval endpoint the
#                                          documents print comes from here.
#                                          Asserts it replays f12's exact
#                                          draws, that no point estimate or
#                                          fold selection moved, and that the
#                                          favourable-side and adverse-side
#                                          exclusion counts agree between the
#                                          two constructions
python f17_e4_alignment_only.py          # E4 alignment-only vs full statistic
#                                          -- SUPERSEDED for its endpoints in
#                                          the same way; run before f30.
python f29_e4_pooled_ci.py               # E4 document-clustered PERCENTILE
#                                          intervals: f11's five B = 2000
#                                          streams POOLED into one 10,000-draw
#                                          distribution, one 2.5/97.5 pair off
#                                          it.  Every E4 interval endpoint the
#                                          documents print comes from here.
#                                          Asserts it replays f11's exact
#                                          draws and that no point estimate
#                                          moved.
python f30_e4_alignment_pooled.py        # the same pooling for the
#                                          alignment-only comparison and the
#                                          paired difference (paired draws
#                                          pooled as pairs).  Also asserts the
#                                          five verdict counts are unchanged.
python f14_deltafeat_check.py            # delta_feat validation vs severity
python f21_e2_coverage.py                # E2 entropy sign-separation coverage
#                                          and excluded-group characterisation
python f9_figure_data.py                 # consolidated figure data

# --- E2, PRE-CORRECTION (kept only as the audit trail; see below) ---------
python f8_e2_crossfit.py                 # -> f8_*   (unsigned loss proxy)
python f8b_e2_crossfit_det.py            # -> f8b_*
# The archived f16_*/f20_* records are HISTORICAL, on two counts.  The
# signed-statistic fix changed the code these two scripts run and neither
# exposes an unsigned mode; and the tent_gn feature proxy now comes from a
# measurement on the fresh source model rather than from a cross-model join,
# which f16 selects with --dfeat-source (default `fresh', the join available
# as `legacy').  Re-running the commands below today therefore reproduces the
# CORRECTED numbers -- the f23_*/f24_* records -- and not the archived
# f16_*/f20_* ones.  The pre-correction E2 cross-fit values that ARE
# regenerable are the f8 family, via --statistic phase_loss_unsigned (see the
# note at the end of this block).
python f16_e2_gn_analysis.py             # -> f16_* names, corrected values
python f20_e2gn_loco_sensitivity.py      # -> f20_* names, corrected values

# --- E2, CORRECTED SIGNED STATISTIC -- these produce the reported numbers --
# Both documents define every proxy phase statistic with a SIGNED alignment
# factor, Phi = alpha_sgn|alpha_sgn| delta_proxy / sigma^2_rel, and
# Phi_0 = alpha_sgn|alpha_sgn| delta_proxy on a zero-noise arm; the
# construction is stated in the main text and detailed in supplement section
# S5.  A loss-proxy branch computing alpha**2 drops that sign.  Every E2
# number in either document comes from the runs below; the f8/f16/f20 outputs
# above ship unmodified so the difference between the two statistics is
# auditable.
python f8_e2_crossfit.py  --statistic phase_feat \
       --out-prefix f22_e2_crossfit_feat       # feature proxy (sign-carrying)
python f8b_e2_crossfit_det.py --statistic phase_loss \
       --out-prefix f22b_e2_crossfit_det       # tent / pseudo-label
python f8_e2_crossfit.py  --statistic phase_loss \
       --out-prefix f22c_e2_crossfit_loss      # ttt_rot / ttt_mask, loss proxy
# delta_feat for the fresh GroupNorm arm, measured on the fresh source model
# over the fresh episodes.  CPU, about a minute; it gates itself on
# reproducing that model's recorded clean test accuracy, and f16 refuses to
# run its feature arm without its output.  Run it BEFORE f23.
python f38_e2gn_deltafeat_fresh.py
# The E3 retrospective selector, recomputed from the RELEASED arrays alone:
# no model, corpus, GPU or network, a few seconds on a CPU.  It reruns the
# admissibility test on results/is_fresh/e3_vectors/*.npz and ASSERTS that
# the released arrays reproduce every run's own selected index, so a release
# whose arrays stopped supporting the claim fails here rather than printing a
# quieter number.
python f39_e3_vector_selfcheck.py
# The per-member manifest of the UNATTACHED replica side archive, written
# INTO this release so that ONCE THAT ARCHIVE IS OBTAINED its contents can be
# verified member by member and array by array rather than by one opaque
# whole-archive digest.  It does not make possession of the archive
# verifiable -- a manifest of absent bytes proves nothing about them.  It needs the side archive, which is published as a versioned
# release asset of the code repository and is NOT in this payload, so from a clean extraction it
# is a --check that has nothing to check against; run it where the archive
# is, or skip it.  Everything else here runs without it.
python f40_e3_replicas_manifest.py --check   # needs e3_vectors_replicas.zip
# The theory-closure suite's raw per-episode records are the second side
# archive, and for the same reason: 127 MB of gzip that would put the
# attached pair far over the correspondence budget, with no precision trade
# available.  Its manifest ships here too, at
# results/is_fresh/closure/CLOSURE_RECORDS_MANIFEST.json, and hashes each
# member twice -- as stored, and decompressed -- so a rebuilt archive at a
# different gzip level still verifies.  Same standing as above: from a clean
# extraction this is a --check with nothing to check against.  NOTHING
# printed in either document is recomputed from it; the analysis JSONs it
# would regenerate all ship in this payload under closure/json/.
python f41_closure_records_manifest.py --check   # needs closure_records.zip
python f16_e2_gn_analysis.py --out-prefix f23_e2_gn        # matched 45 cells
python f20_e2gn_loco_sensitivity.py \
       --out-name f24_e2gn_loco_sensitivity.json           # LOCO, after f23
#   The pre-correction values are regenerable with
#     python f8_e2_crossfit.py --statistic phase_loss_unsigned ...
#   and f8b asserts that they reproduce the archived JSONs.

# --- E1 reporting audit ---------------------------------------------------
python f34_e2_tempscale_estimands.py     # the E2 temperature-scaling early-loss
#                                          statement has TWO estimands -- the
#                                          absolute adapted loss and the excess
#                                          over each arm's own frozen baseline.
#                                          Scaling moves the frozen baseline
#                                          too, so they differ; this record
#                                          computes both, under their own
#                                          names, and r9_reconcile.py binds
#                                          both.  Deterministic, no seeds.

python f26_e1_reporting_audit.py         # recomputes the E1 reported values
#                                          from the f7/f10/f3 records.  Its
#                                          replicate census also reports the
#                                          retrospective-selector measurement
#                                          sets when
#                                          they are present; they are not in
#                                          this archive, and the census omits
#                                          them.

# --- E2 identity-level overlap of the cross-fit split --------------------
python f27_e2_identity.py                # -> f27_e2_identity.json.  Counts the
#                                          image identities that land in both
#                                          shares of the E2 commissioning /
#                                          evaluation split, the episode rows
#                                          they account for, and the shift in
#                                          every headline rho when all of them
#                                          are deleted from BOTH shares.
#                                          Reproduces f8_e2_crossfit.py's split
#                                          stream exactly.

# --- figures the two documents include -----------------------------------
# READ THIS BEFORE RUNNING ANY GENERATOR IN THIS BLOCK.  The three figure
# generators below carry an OUT_DEFAULT that points into the FROZEN
# 79-page tree, because that is where they wrote when they were run.  Running
# one without an explicit output path therefore writes into the frozen tree
# and not into the tree this archive ships.  Pass the is2 path instead, or
# copy the result afterwards.
python fig_f1_curves.py                  # main Fig. 4 (re-simulates; asserts
#                                          it replays f7 cell for cell)
python fig_f2_phase.py                   # main Fig. 5 (needs f10)
python fig_f4_e2.py                      # main Fig. 6 (needs f22, f22b,
#                                          f22c, f23)
# (`tab_t6_e4_proxy.py` used to be listed here with an explicit --out into the
#  is2 tree.  It no longer is: the per-domain proxy table this submission
#  prints is supplement Table S7 and its generator of record is
#  `tools/tab_s7_e4_proxy.py`, below.  `tab_t6_e4_proxy.py` remains
#  the generator of the FROZEN tree's copy and is listed with the other frozen
#  tooling in the table further down.)

# --- fix-forward GPU run (one GPU, ~2.5 h) -------------------------------
python f15_e2_entropy_gn.py              # entropy objective on ResNet-26+GN
#   then re-run f16/f23 and f20/f24 to score its records
python f_scope_bench.py                  # wall-clock scoping only, no results
```

## The is2 manuscript tools

These live in `tools` and act on the two documents this archive
ships.  Run them from that directory.

```
cd tools

python r9_reconcile.py                   # 405 CURATED headline claims
#                                          re-derived from the JSONs above and
#                                          compared with the token the two
#                                          documents print, plus a model-free
#                                          scan of every .tex for one interval
#                                          printed two ways.  Exits non-zero on
#                                          a mismatch.  Reads only; writes
#                                          nothing.
#                                          It scans BOTH documents, reports
#                                          where each claim binds, and fails on
#                                          an ORPHAN -- a curated claim whose
#                                          printed token appears in neither
#                                          document.  That check is what a
#                                          restructuring needs: a binding whose
#                                          text was deleted would otherwise
#                                          keep passing forever while its
#                                          number stopped being a claim about
#                                          anything.
#                                          It is a CURATED HEADLINE AUDIT, not
#                                          an exhaustive binding of every
#                                          number: the E2 leave-one-corruption-
#                                          out fold intervals and some E2
#                                          conditional calibration proportions
#                                          are reported and unbound, and a
#                                          purely SEMANTIC error (a correct
#                                          number under a wrong label) is
#                                          invisible to a value check.  Report
#                                          it as "405 curated headline
#                                          and repeated numerical claims",
#                                          never as "every number".
#                                          It also runs 105
#                                          CONSTRUCTION checks (PASS 1b):
#                                          assertions that the E4 brackets are
#                                          still built by POOLING the five
#                                          bootstrap streams into one
#                                          10,000-draw distribution rather than
#                                          by averaging five percentile
#                                          endpoints, checked on the records
#                                          AND on the .tex corpus of both
#                                          documents.  A value check cannot
#                                          express that, which is how the
#                                          defect it guards against once passed
#                                          a green run.
python tab_s4_e1_gates.py                # supplement Table S4, the E1
#                                          verification gates, generated from
#                                          f7/f10/f3/f5/f6 and the f26 audit.
#                                          The six-part table of the frozen
#                                          tree carried a retrospective-
#                                          selector diagnostic as its part (d);
#                                          this
#                                          submission does not contain it, so
#                                          the parts are relettered and no
#                                          record of it is read.
python tab_s4_e1_gates.py --check        # BYTE comparison against the shipped
#                                          .tex, not a digit comparison: a
#                                          relettering that left the numbers
#                                          alone would pass the weaker test.
python tab_s7_e4_proxy.py                # supplement Table S7, the GPT-2
#                                          leave-one-domain-out proxy
#                                          validation, generated from f31.
#                                          The frozen tree's copy of this
#                                          table is generated by
#                                          ttt/is_fresh/
#                                          tab_t6_e4_proxy.py, which is a
#                                          DIFFERENT table: this one carries
#                                          the manuscript's relative-noise
#                                          symbol, its own label, and a
#                                          two-block layout that is set at the
#                                          supplement's own type size instead
#                                          of being scaled to the text width.
python tab_s7_e4_proxy.py --check        # BYTE comparison, for the same
#                                          reason as S4's: the shared frozen
#                                          generator's --check compares
#                                          NUMERIC TOKENS, and every label in
#                                          this table had been rewritten under
#                                          it without the check noticing.
python build_env_section3.py             # interpolates section 3 and the
#                                          section 6.4 census of
#                                          BUILD_ENVIRONMENT.md -- page counts,
#                                          sizes, SHA-256s, error and
#                                          undefined-reference censuses -- from
#                                          BOTH documents' build products.  Run
#                                          it after every rebuild and before
#                                          packaging.
python build_env_section3.py --check     # fails if the shipped blocks are
#                                          stale; the release build runs this
python xref_sync.py                      # the two cross-document lookup
#                                          tables.  The article and the
#                                          supplement are SEPARATE LaTeX
#                                          documents, so neither resolves the
#                                          other's \label; this reads each
#                                          document's own .aux and writes the
#                                          other's table (main.aux ->
#                                          supplement/xref_main.tex, and
#                                          supplement.aux ->
#                                          paper/xref_supp.tex).  Sources cite
#                                          by LABEL (\mref, \sref), never by a
#                                          typed number, and a label the other
#                                          document does not define is a hard
#                                          error here.  Run it after a build
#                                          that renumbered anything, then
#                                          rebuild both documents.
python supp_inventory.py                 # supplement/inventory_generated.tex:
#                                          the supplement's front-matter
#                                          inventory of its own numbered
#                                          statements, split into those that
#                                          restate an article result and those
#                                          with no article counterpart.  The
#                                          split is read off a machine-readable
#                                          `%% inv:` annotation above every
#                                          numbered environment, and the
#                                          NUMBERS come from the two .aux
#                                          files, never typed.  A numbered
#                                          statement with no annotation is a
#                                          hard error.
python dup_statement_gate.py             # the same-statement-in-both-documents
#                                          gate, also run by gates.sh.  It is
#                                          the check supp_inventory.py cannot
#                                          make: the inventory counts
#                                          ANNOTATIONS, so an annotation that
#                                          says `supplement-only` of a
#                                          statement the article also prints is
#                                          accepted -- and once was.  This
#                                          normalises every theorem-like
#                                          environment in BOTH trees, scores
#                                          every cross-document pair, and fails
#                                          on any nontrivial body match not
#                                          declared `%% inv: restates <label>`;
#                                          independently, it fails when the
#                                          article defines `<key>` and the
#                                          supplement defines `<key>-s` without
#                                          that declaration.  Exits non-zero on
#                                          either.  Reads only; writes nothing.
python make_release_zip.py --self-rebuild-check
#                                          resolves the four dependency-
#                                          provenance records and the whole
#                                          payload map and reports whether a
#                                          rebuild FROM THIS EXTRACTED TREE
#                                          would succeed.  Writes nothing,
#                                          needs no frozen parent archive,
#                                          takes seconds.  Run this first: it
#                                          is the check that the archive can
#                                          rebuild itself.
python make_release_zip.py               # rebuilds and verifies this archive.
#                                          VERIFICATION IS THE DEFAULT: there
#                                          is no --verify switch, and the only
#                                          override is --no-verify, which
#                                          turns verification off.
#                                          The four dependency-provenance
#                                          entries are read from
#                                          provenance/ inside this
#                                          archive, so the command above works
#                                          from a clean extraction.
#                                          Its in-tree bootstrap checks run at
#                                          B = 200 from ONE RNG stream and are
#                                          CODE-PATH checks: they prove the
#                                          shipped records feed the shipped
#                                          generator and that it completes.
#                                          They are NOT a reproduction of the
#                                          published endpoints, which come
#                                          from five B = 2000 streams pooled
#                                          into 10,000 draws.  To reproduce
#                                          those, run f11/f12 and then f29/
#                                          f30/f31 above at their DEFAULT
#                                          parameters -- no --b, no
#                                          --boot-seeds, no --no-audit -- and
#                                          let each script's own audit compare
#                                          the result with the archived
#                                          record.  That is the full replay;
#                                          the packaging run is the smoke one.
```

## Scripts that ship but are NOT part of this submission

`ttt/is_fresh` ships whole, because it is the analysis suite as it
was run and a partial copy of it would be a worse record than a complete one.
Several of its scripts belong to material this submission does not contain, and
four more are the frozen tree's own tooling, superseded here by the `is2` pair
above.  They are listed so that every shipped script is accounted for; none of
them is part of reproducing anything either document says.

| script | what it belongs to | runnable here? |
|---|---|---|
| `f4_alta_measured_oracle.py` | the label-free retrospective selector | no: its records are not in this archive |
| `f13_compute_matched.py` | the same | no: its records are not in this archive |
| `fig_f3_alta.py` | the figure of the same | no |
| `fig_f8_domains.py` | the E3 per-domain scatter.  Its output `F8_domains.pdf` **does ship**, in this archive as `paper/is2/paper/figures/F8_domains.pdf` and in the submission archive as `paper/figures/F8_domains.pdf`; the supplement's E3 per-domain subsection describes it as a release visualization and points at it rather than typesetting it, and every number it plots is in main Table 2 and supplement Tables S2 and S3.  `D6_REQUIRED` asserts its presence over the payload and over the finished archive.  No sentence in this archive may describe the file as absent, excluded or not shipped: the submission names and fully specifies the selection rule behind its y-axis (supplement S7.3), the axis label is neutral, and no disclosure reason applies | yes; its output already ships and a rerun must reproduce it |
| `f25_e2_lr_ablation.py` | the learning-rate ablation | yes; its records ship under `results/e5` |
| `f28_p3_montecarlo.py` | a heavy-tail counterexample simulation | yes |
| `tab_t4_e1_gates.py` | the six-part gate table of the frozen tree; `tools/tab_s4_e1_gates.py` generates the table this submission prints | no: it reads a record set that is not here |
| `tab_t6_e4_proxy.py` | the frozen tree's copy of the per-domain proxy table, `paper/is/paper/figures/T6_e4_proxy.tex`; `tools/tab_s7_e4_proxy.py` generates supplement Table S7, which is the table this submission prints and which differs from the frozen one in symbol, label and layout | no: its output target is in the frozen tree, which this archive does not carry |
| `build_env_section3.py` | the frozen tree's copy | no |
| `make_release_zip.py` | the frozen tree's packager, **not** the verifier of this archive: its path-exception map is for the frozen package's layout, so against this one it fails for that reason alone.  This submission's packager and absolute-path gate are `tools/make_release_zip.py` (`--check-paths .`), which is what `BUILD_ENVIRONMENT.md` names throughout | no: quarantined at its command line — it prints the two `tools` commands and exits non-zero unless `TTT_RUN_FROZEN_PACKAGER=1` |
| `r9_reconcile.py` | the frozen tree's single-document reconciliation | no |

## The original generators that are still current

Two objects in the submission are still produced by the original generators.
They write into `figures/` (the repository-level staging directory), from which
the file is copied to `paper/is2/paper/figures/`.  **Both copies ship**, and
`make_release_zip.py` asserts at build time and again inside the extracted
archive that each staging file and its paper copy are byte-identical; the
check is the `staging/paper byte-identity` line of the verify output.  They
import only numpy and matplotlib.

```
cd figures/scripts
python fig_F5.py     # -> figures/F5_batch.pdf   (supplement S9.2, batch mech.)
python fig_F6.py     # -> figures/F6_calib.pdf   (main Fig. 7, entropy calib.)
cp ../F5_batch.pdf ../F6_calib.pdf ../../paper/is2/paper/figures/

# (_style.py is an imported module, no command line)
```

`figures/scripts` also ships `fig_F7.py`, `tab_T2.py`, `k3_baseline.py` and
`bootstrap_ci.py`.  All four read the ImageNet-C record set, which this
submission does not report and which is therefore not in this archive, so none
of them runs here and none produces an object either document contains.  They
ship as part of the generator directory rather than as instructions.

## Main Figures 1-3 have no command, and that is not an omission

The article's first three figures are **author-drawn schematics**: the protocol
and phase plane (Fig. 1), the hard-pair construction (Fig. 2), and the
calibration geometry of the entropy identity (Fig. 3).  They plot no
measurement, so there is no record to re-read and no script to re-run, and no
command line for them appears anywhere in this file.

What stands in place of a generator is a conversion.  The source of record for
each is the vector artwork this archive ships beside the sources:

```
paper/mechanism_figures/1.svg  ->  paper/is2/paper/figures/fig_mech_1_phase_law.pdf
paper/mechanism_figures/2.svg  ->  paper/is2/paper/figures/fig_mech_2_information_boundary.pdf
paper/mechanism_figures/3.svg  ->  paper/is2/paper/figures/fig_mech_3_entropy_alignment.pdf
```

`pdflatex` cannot include SVG, so each was converted once, with **cairosvg
2.9.0** under the pinned interpreter; the result is vector throughout, with
embedded font subsets and no raster image object.  Section 5 of
`provenance/BUILD_ENVIRONMENT.md` records the route in full, including the
one glyph that needed handling.  `make_release_zip.py` asserts, for each of the
three, that the source ships and that the PDF it converts to is in the payload,
and the no-collision gate asserts that **no** live generator writes any of the
three PDF basenames -- a script that did would replace author artwork with a
plot on the next bulk re-run of `figures/scripts`.

## Superseded generators -- do not run

`figures/_superseded/` holds the original generators for the figures
and the gate table.  Each wrote a file with the same basename as an object
that a current generator now produces, from single-seed or full-sample data,
so running them in bulk would have overwritten a current artifact with a stale
one.  They are kept as the audit trail only, have no command line here, and
are not runnable in place (they `import _style`, which resolves only from
`figures/`).  See `figures/_superseded/README.md` for the
one-line reason per file.

Each script prints its headline numbers and asserts its own reproduction check;
a non-zero exit status means the check failed.
