# Auditability archive -- index

Built 2026-08-19 12:59 UTC for the
Information Sciences submission "When Does Single-Instance Test-Time
Adaptation Help?  An Exact Phase Law in a Solvable Model".
It exists so that the submission is independently auditable rather than
merely re-readable.  Extract it and every path below resolves without
editing.

**The submission is two documents.**  `paper/is2/paper/main.pdf` is the
article (39 pp); `paper/is2/supplement/supplement.pdf` is the
Supplementary Material (55 pp).  Both ship here with their sources,
their build transcripts, their compiled bibliographies and the pinned LaTeX
environment that produced them.

**What the supplement adds, stated as its own front matter states it.**  The
supplement introduces no additional model-training or model-evaluation suite:
every experiment reported there is one of the three the article reports, and
no record here supports a suite the article does not describe.  It does
*not* follow -- and it must not be written here -- that every statement in
the supplement has a counterpart in the article.  The supplement
carries **supplement-only numbered formal statements** (the local-PL envelope,
its stopped-process proposition, and the counterexample catalogue that
delimits the frozen-model corollary) and **supplement-only full-grid
quantitative claims** (among them the per-fold leave-one-domain-out ranges,
the interval-construction decompositions, and the intraclass-correlation and
design-effect figures reported with them).  The supplement's own front matter
enumerates all of these explicitly and flags each as subordinate technical
material; read it there rather than here, because that enumeration is the
authoritative one.  Beyond those, the supplement carries the full proofs,
protocols, estimation detail and complete result grids behind what the
article summarizes.

## What is NOT in this archive, and where it lives

This submission reports three experiments -- E1 (solvable model), E2
(CIFAR-10/100-C) and E4 (GPT-2 domains) -- and the archive carries their
records, the fresh re-analyses that consume them, and the two documents.  It
does not carry records whose only role was to support material the submission
does not contain.  Omitting them is a decision, and it is listed rather than
left to be noticed:

| omitted | reason |
|---|---|
| `experiments/results/e3/` | ImageNet-C per-cell records; the experiment they belong to is not reported in this submission.  NB the article's E3 is the GPT-2 suite under experiments/results/e4/, not this directory |
| `experiments/results/e5_gencheck/` | generated-vs-downloaded corruption sanity check, cited by the same provenance table |
| `experiments/results/is_fresh/closure/REVIEW_R*.md` | the two adversarial design-audit transcripts the theory-closure suite's DESIGN.md was revised against. They are process records, not measurement records, and a package meant to be read cold does not carry another audit's transcript -- the same rule that keeps every editorial-history file out of both packages, and the leak gate enforces it. What they forced is not lost: DESIGN.md's changelog states every change either audit produced, which is the part that bears on the measurements |
| `experiments/results/is_fresh/closure/records/*.jsonl.gz` | the theory-closure suite's 71 raw per-episode record files, 127 MB. They are held in the side archive closure_records.zip, whose per-member manifest (size, sha256 of the stored file, sha256 of the decompressed bytes, record count) ships in this archive at experiments/results/is_fresh/closure/CLOSURE_RECORDS_MANIFEST.json. The split is by size and by content, not by relevance: every number printed in either document is bound to an analysis json under closure/json/, which ships here in full, as do the independent verifier's report and the suite's measurement, analysis and verification code. The records are needed only to RE-DERIVE those jsons from scratch. Obtaining the side archive lets a reader verify it member by member; this manifest proves neither possession nor correctness of an archive a reader does not have |
| `experiments/results/is_fresh/f4_*, f13_*` | the two fresh measurement sets of the label-free RETROSPECTIVE SELECTOR (a rule applied after the fact to per-step measurements, not an online stopping time); the selector is disclosed in the discussion as developed-but-not-claimed and is not a contribution here, so its measurements support nothing in either document |
| `experiments/results/provenance/` | per-(corruption, severity) ImageNet-C image manifests; they were cited by a provenance table that is not in this submission |
| `experiments/ttt/e3_imagenet/` | the ImageNet-C experiment runner, for the same reason as its records |

None of it is lost.  The frozen `paper/is/` tree and its own
`release_archive.zip` are the home of record for all of it, complete and
unchanged.

One inclusion is asserted rather than merely intended.  The E4 per-domain
figure (`F8_domains.pdf`) is not typeset by either document -- it is an optional
release visualization that the supplement describes as such and points at --
and its PRESENCE is checked twice
-- once over the collected payload before the ZIP is written and once over
the finished archive's own member list -- so it cannot go missing through a
path the collector did not anticipate.  The other figure and table artefacts
of the 79-page build that neither document includes are excluded, each with
its reason:

| excluded artefact | reason |
|---|---|
| `figures/F1_curves.png` | raster twin of F1_curves.pdf; the build consumes the PDF |
| `figures/F3_alta.pdf` | figure of the label-free retrospective selector; not in either document |
| `figures/F4_e2_phase.png` | raster twin of F4_e2_phase.pdf; the build consumes the PDF |
| `figures/F7_imagenet.pdf` | ImageNet-C figure; not in either document |
| `figures/T1_theory_comparison.tex` | prior-theory comparison table; replaced by prose in section 2 |
| `figures/T2_e3_full.tex` | full ImageNet-C grid (the withdrawn suite); not in either document |
| `figures/T3_provenance.tex` | ImageNet-C provenance table; not in either document |

The analysis CODE directory ships whole, including the modules and generators
of the omitted material.  A partial copy of a suite that was run as a whole is
a worse record than a complete one, and `COMMANDS.md` marks every such script
as not part of this submission.  What the archive does not carry is the
EVIDENCE for claims the submission does not make.

## What "reproducible" means here, precisely

**ANALYSIS REPRODUCTION and ORIGINAL EXPERIMENTAL REGENERATION are two
different operations, and this archive supports one of them turnkey.**  Read
this before reading "reproducible" anywhere in this archive.

* **ANALYSIS REPRODUCTION -- supported here, end to end.**  Install
  `requirements-analysis.txt` and rerun the analyses that turn the shipped
  result records into the numbers the two documents print.  CPU only; no
  download, no GPU, no checkpoint, no dataset.  Every input is in this ZIP.
  What "result records" means is NOT uniform across the three suites, and the
  next subsection separates the two levels rather than calling both of them
  "raw".
* **ORIGINAL EXPERIMENTAL REGENERATION -- NOT supported here, and no
  requirements file could make it so.**  Rerunning the CIFAR-10/100-C and
  GPT-2 experiments that PRODUCED those records needs external datasets,
  third-party model weights and a tokenizer, regenerated source checkpoints,
  generated corruption tensors, and a GPU.  The table below enumerates them.
  `requirements-analysis.txt` is a lock for the first operation; it is not,
  and is nowhere described here as, a lock for the second.

### External inputs a complete regeneration needs and this archive lacks

Generated at packaging time from the shipped runners' own calls and the
shipped records' own `meta` blocks -- the "named in" column is the file each
row is checkable against.  `COMMANDS.md` prints the same table.

| what | identifier as the runner names it | named in | why it is not here |
|---|---|---|---|
| CUDA-linked torch build (recorded) | `2.8.0+cu128` | `experiments/results/m0/cifar100_resnet26ttt_s0.json, experiments/results/m0/cifar100_resnet26ttt_s1.json (+more)` | the archive was packaged on a CPU-only interpreter, so the pin in requirements-experiment.txt is the CPU wheel; the build named in the identifier column is the one that actually ran |
| GPU (recorded device) | `NVIDIA GeForce RTX 2080 Ti` | `experiments/results/m0/cifar100_resnet26ttt_s0.json, experiments/results/m0/cifar100_resnet26ttt_s1.json (+more)` | hardware; the original runs are not reproducible on CPU in any practical time, and results can differ across device and driver |
| corruption tensor set (external download or regeneration) | `CIFAR-10-C` | `experiments/ttt/e2_cifar/data.py` | tens of GB of image tensors; excluded by size, regenerable from the public release or from the shipped generation script |
| corruption tensor set (external download or regeneration) | `CIFAR-100-C` | `experiments/ttt/e2_cifar/data.py` | tens of GB of image tensors; excluded by size, regenerable from the public release or from the shipped generation script |
| dataset (Hugging Face hub) | `Salesforce/wikitext / wikitext-103-raw-v1` | `experiments/ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (Hugging Face hub) | `ccdv/pubmed-summarization / document` | `experiments/ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (Hugging Face hub) | `codeparrot/codeparrot-clean-valid` | `experiments/ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (Hugging Face hub) | `pile-of-law/pile-of-law` | `experiments/ttt/e4_gpt2/prepare_data.py` | third-party corpus, redistributed by its own host under its own terms; not ours to ship |
| dataset (torchvision download) | `CIFAR10` | `experiments/ttt/e2_cifar/data.py` | third-party dataset fetched by the runner at first use |
| dataset (torchvision download) | `CIFAR100` | `experiments/ttt/e2_cifar/data.py` | third-party dataset fetched by the runner at first use |
| distribution absent from the build interpreter | `datasets` | `experiments/ttt/e4_gpt2/prepare_data.py` | needed only by the original data-preparation scripts, which ran on separate machines; left unpinned rather than pinned to a version this build never saw |
| pretrained weights and tokenizer | `gpt2` | `experiments/ttt/e4_gpt2/delta_proxy_v2.py, experiments/ttt/e4_gpt2/prepare_data.py (+more)` | third-party model weights and tokenizer resolved from the hub by name at run time; the ORIGINAL runs recorded the NAME and no revision hash, so a bare re-fetch is not guaranteed to obtain the same weights.  The REPRODUCTION loader is pinned to revision 607a30d783dfa663caf39e06633721c8d4cfcd7e and the weight digest, and the pinned rerun reproduces the retained records -- see the two-part statement below the table |
| source checkpoints (*.pt) | `written by the shipped training scripts` | `experiments/ttt/e2_cifar/train_recon_head.py, experiments/ttt/e2_cifar/train_source.py` | excluded by size; regenerable with the shipped training scripts given the datasets above, but not bit-identically |

Two facts about the pretrained model are distinct and are stated apart.  The
ORIGINAL runs recorded only the model **identifier**: they loaded the bare
name `gpt2` and logged no revision hash, so a bare re-fetch obtains whatever
that name resolves to when it is run.  The REPRODUCTION loader is **pinned**
-- repository `openai-community/gpt2`, revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e`, `model.safetensors` sha256
`248dfc3911869ec493c76e65bf2fcf7f615828b0254c12b473182f0f81d3a707` -- and the
pinned rerun **reproduces the retained records of the original runs**: frozen
(`t=0`) continuation cross-entropy to 6.2e-06 on all twelve (domain, seed)
jobs, fixed-budget perplexity at `t=20` to 1.50e-05 absolute (6.5e-07
relative) on all twelve.  That agreement is what makes the pin informative
about the historical run rather than only about future ones; the report is
`experiments/results/is_fresh/e3_vectors/PROVENANCE.md` and
`VERIFY_SUMMARY.md`.  The recorded GPU and torch build are part of the
experimental conditions, and a regeneration on other hardware is a
replication rather than a rerun.

### Two levels of retained record, and which suites have which

"Raw records" is not one thing here, and describing every retained object with
that one word would overstate what parts of E1 retain.  Two levels ship, and
every reproducibility statement in this archive is a statement about one of
them:

| level | what an entry is | suites | what it supports |
|---|---|---|---|
| **PER-EPISODE / PER-DOCUMENT RAW RESULT RECORDS** | one row per adaptation episode (E2) or per document x adaptation seed (E3), as the run emitted it, shipped unmodified | E2 (`experiments/results/e2/`), E5 feature-shift, E3 (`experiments/results/e4/`) | independent recomputation of the article's downstream statistics from below the level of any summary this submission authored |
| **SOURCE-MODEL EVALUATION RECORDS** | one file per (dataset, architecture, seed) source model: the per-epoch clean-test history the training run logged, its final clean test accuracy, and the commissioning gate outcome, as the run emitted it | E2 source models (`experiments/results/m0/`) | independent verification of the supplement's source clean-accuracy paragraph against a primary record rather than against a downstream audit echo.  It does NOT support re-deriving those accuracies from weights: the checkpoints are not in the payload |
| **PER-CELL SIMULATION SUMMARY RECORDS** | one row per grid cell (or per cell x step), already reduced across the replicates simulated inside that cell | parts of E1 -- the curve-match, one-step-grid and oracle-index records (`f7`, `f10`, `f3`, and the audits reading them) | recomputation of the article's E1 aggregate claims from the retained cell/block level, NOT from the individual simulated trajectories |

The distinction is material and we state its consequence rather than leaving
it to be inferred: **the 40,000 individual simulated trajectories per E1 cell
are not retained.**  E1's printed statistics -- the 2.23% mean of seedwise
maxima, the 2.62% grid maximum, the negative-gain counts, the oracle-index
fractions -- are recomputable from the shipped per-cell records, and that is
what any recomputation of them establishes.  Recovering them from the
trajectory level instead means RE-SIMULATING, which for E1 alone this archive
fully supports: the simulator and every seed ship, E1 has no external dataset,
checkpoint or model dependency, and `COMMANDS.md` gives the default
invocations.  For E2 and E3 the retained level is the per-episode /
per-document one, and re-simulation is exactly what this archive cannot do
(see the external-input census above).

So, precisely: E1 is *regenerable from code* but retained only *per cell*;
E2 and E3 are retained *per episode / per document* but are *not regenerable
from this archive alone*.  Neither suite is both, and no sentence here says
otherwise.

### The E3 retrospective selector: the rule is executable here, the published run's trajectories are not

E3's selected-stop column is produced by a RETROSPECTIVE SELECTOR --- a rule
applied after the fact to per-step measurements recorded at every step, not an
online stopping time.  THREE things a reader might want from it are supported
to three different degrees, and they are separated here rather than merged
under one word.  Every number in this section is read from
`experiments/results/is_fresh/f39_e3_vector_selfcheck.json` and from the
shipped files themselves; none of it is transcribed.

* **VERIFICATION of the stored selector OUTCOMES: supported.**  The selected
  index and the quantities evaluated at it are in the shipped per-document
  records, and every E3 interval, point estimate and paired difference the
  documents print is recomputed from those stored outcomes by
  `f29_e4_pooled_ci.py`, `f31_e4_proxy_pooled.py` and
  `f32_e4_fixed_budget_ci.py`, which run here and assert against the archive.
* **(R) RECOMPUTABILITY OF THE RULE: supported, exactly.**  The admissibility
  test consults TWO arrays --- the per-step mean replica prediction vectors
  and the replica dispersion sequence that sets its bands --- and both are in
  this archive: 12 files under
  `experiments/results/is_fresh/e3_vectors/`, each carrying `pred0`,
  `pi_bar`, `s`, `t_hat` and `doc` at full float64 ---
  and `experiments/ttt/is_fresh/f39_e3_vector_selfcheck.py` reruns the whole
  admissibility scan on those arrays alone, with no model, corpus, GPU or
  network.  It reproduces the index stored with them on
  **6000 of 6000** documents, exactly, and asserts
  that result rather than printing it: a release whose arrays stopped
  rebuilding the selector fails that script.  `r9_reconcile.py` PASS 1b
  asserts both the presence of the arrays and the exactness of the
  reproduction.
* **(H) PROVENANCE OF THE PUBLISHED RUN'S DECISIONS: NOT supported, and not
  claimed.**  The released vectors come from a RERUN of the published grid on
  different hardware.  The published run's own per-step `pi_bar` trajectories
  were not retained and are recoverable from nothing in this archive, so the
  6000 historical decisions can be COMPARED against but not
  reconstructed.  The comparison: the rerun's indices agree with the
  published ones on **5989 of 6000**
  (99.82%), with 11 disagreements, all of them
  boundary near-ties falling in both directions --- 7
  admitting the disputed step where the published run rejected it and
  4 rejecting it where the published run admitted it --- and a
  worst normalised slack at a disputed step of 9.697e-04.
  Fixed-budget perplexity at t = 20 agrees between the two runs on all
  12 jobs.  Those magnitudes are CONSISTENT WITH arithmetic
  sensitivity at a decision boundary; with the original trajectories
  unavailable they do not exclude every alternative, and no statement here
  says they do.

The consequence, stated rather than left to be inferred: **the selected
column of E3 rests on (H) and not on (R).**  (R) makes the rule auditable;
it does not re-derive that column.  The article's primary E3 comparison is
the fixed budget, which rests on neither.

### The replica side archive, and how to verify you have it

Regenerating `pi_bar` and `s` FROM the K = 3 replicas --- as opposed to
consuming them, which (R) above does --- needs the per-replica trajectories.
Those are in `e3_vectors_replicas.zip`, which is **published as a versioned
release asset of the code repository and is not attached to review
correspondence**: at 62.5 MB it would put the
attached pair over the correspondence size limit.  It downloads without an
account from
`https://github.com/kkioplkg/when-ttt-helps/releases/download/v1.0.3/e3_vectors_replicas.zip`.
Naming it and printing a single whole-archive digest is not enough for a
reader to check anything, so this archive also ships that archive's own
per-member manifest:

`experiments/results/is_fresh/e3_vectors/REPLICAS_MANIFEST.json`, generated
by `experiments/ttt/is_fresh/f40_e3_replicas_manifest.py`, records for each
of the **13 members** its name, its uncompressed size and
the SHA-256 of its uncompressed bytes, and for each of the
12 `.npz` members the name, shape, dtype and SHA-256 of the raw
C-order bytes of every one of the **72 arrays** inside it
(64,498,225 uncompressed bytes in total).  **Once the side archive is
obtained, its contents can be verified member by member and array by array**,
independently of how the
ZIP was compressed or in what order it was written --- which a whole-archive
digest is not.  For completeness the archive's own size and digest are
62,525,322 bytes and `22783827059b250cc5e35f4694ddb649aa3b816c3aba97006c7e8ee44004751e`.  Re-derive the manifest
with `python f40_e3_replicas_manifest.py --check` once you have the archive.

**What the manifest is not.**  A manifest of bytes a reader does not have
proves neither possession nor correctness of those bytes; it is a
verification *specification*, usable after the archive is obtained and not
before.  Against the attached pair alone the manifest's internal arithmetic
can be checked and nothing else can, and this release makes no stronger claim
for it.  The release states elsewhere that an archive a reader cannot open is
a claim rather than evidence, and that applies to this one.

**The limit this places on the attached release.**  The attached
`pi_bar`, `s` and `t_hat` arrays are *selector-consistent* --- that is
exactly what (R) above establishes, and it is established from the attached
bytes alone.  What cannot be checked from the attached pair is the
*construction* of the first two from the replicas: that
`pi_bar` equals `tails.mean(axis=...)` and that `s` is the dispersion of
those same replica arrays are claims about `tails`, and `tails` lives only in
the side archive.  So (R) does not depend on the side archive and the
construction claim does; a reader who has only the two attached archives can
verify the former and must take the latter on the manifest's word until the
side archive is obtained.

Nothing in the side archive is needed to reproduce a number printed in
either document, and nothing in it is needed to rerun the selector.

### Reduced verification versus full replay

**FULL reproduction and REDUCED verification are two different operations,
and only one of them regenerates the published numbers.**  Read this before
reading "verified" anywhere in this archive.

* **REDUCED (fast, automatic).**  `make_release_zip.py` rebuilds this ZIP and
  calls `verify()` on it, and `verify()` also runs standalone against an
  existing ZIP from a clean extraction.  It establishes *integrity in full* --
  every payload re-hashes, every declared identity holds, every path and
  documentation gate passes, and three shipped artefacts regenerate at
  published parameters and match number for number -- but its five numerical
  recomputations run at **cut-down parameters** (`f7` at `--n-rep 4000`
  against a 40,000 default; `f11`/`f29`/`f31` at `--b 200` from one bootstrap
  stream against published intervals built from 5 x 2000 = 10,000 pooled
  draws; `f8b` at `--n-boot 100`), two of them under `--no-audit` precisely
  because a reduced result must not be compared with the archived record.
  They write `verify_*` names for the same reason.  **A passing `verify(zip)`
  therefore does not mean every published number was recomputed.**
  `experiments/ttt/is_fresh/VERIFY_TRANSCRIPT.md` carries a complete such run
  on the pinned interpreter, with its exit code.
* **FULL (slow, manual).**  The published endpoints are regenerated by the
  *default* invocations in `COMMANDS.md` -- no `--b`, no `--boot-seeds`, no
  `--n-rep`, no `--no-audit` -- under which each script's own audit compares
  its output against the archived record.  That is the operation described in
  the bullet immediately below, and it is the one that reproduces published
  values.

* **The reported analyses and figures are independently rerunnable from the
  supplied records.**  Install `requirements-analysis.txt`, then run, from
  `experiments/ttt/is_fresh`, the CPU re-analysis, reconciliation and
  figure-generation commands of `COMMANDS.md`, in the order given there.
  The E1, E2, E4, calibration and clustering analyses behind the two
  documents are re-executed this way from the shipped records at the level
  each suite retains -- per-episode/per-document for E2 and E3, per-cell
  summaries for the E1 curve-match, one-step-grid and oracle-index parts --
  and each script asserts its own reproduction check.  No download, no GPU, no
  checkpoint.
  **This is a statement about rerunning the analyses, not a certificate that
  every printed number is machine-verified.**  The reconciliation
  (`r9_reconcile.py`) binds **405 curated headline and repeated
  numerical claims** to records of record, with 104 further
  construction checks; that curated list is not exhaustive and says so, in
  its own docstring and in `FRESH_RESULTS.md`.  Quantities it does not bind
  --- among them the E2 leave-one-corruption-out fold intervals and some E2
  conditional calibration proportions --- are recomputable from the shipped
  records but are not asserted by any gate.  This narrowing is deliberate: "every number in
  the manuscript" overstates what the binding establishes.
  **Two scripts in `is_fresh` are NOT part of that set and must be skipped**
  (`COMMANDS.md` additionally tabulates the scripts that belong to material
  this submission does not contain):
  `f15_e2_entropy_gn.py`, which trains and samples on a GPU and reaches
  Pillow and torchvision and the unshipped CIFAR tensors, and
  `f_scope_bench.py`, which imports torchvision and requires CUDA and
  recomputes no manuscript number.  `COMMANDS.md` places both under its
  fix-forward GPU section, and the packaging commands
  (`make_release_zip.py`) are likewise not part of the rerun.  No manuscript
  number depends on running any of them: `f15`'s records ship, and the
  matched-architecture numbers are recomputed from them on CPU by
  `f16_e2_gn_analysis.py`.
* **Complete re-execution of the original model experiments is not turnkey
  from this ZIP alone.**  Every input it additionally requires is enumerated
  in "External inputs a complete regeneration needs and this archive lacks"
  above, generated from the shipped runners and records rather than listed by
  hand.  Checkpoints (`*.pt`) and image/corruption tensors are excluded by
  size, not by omission; the training, data-preparation and
  corruption-generation scripts that produce them all ship.
* **Dependency provisioning is a prerequisite, not a given.**  "Every path
  resolves after extraction" is a statement about paths.  The re-analysis
  path itself needs only numpy, matplotlib, scipy and the standard library;
  torch is required by the experiment runners and by the two re-analysis
  scripts that use it directly (see `COMMANDS.md`).

## The audit boundary, and how to audit one number

**Two manifests, no third category.**  The boundary used to be a sentence a
reader had to take on trust; it is now machine-checkable.

* `MANIFEST.json` covers the **payload** --- the 627 files
  collected from the repository --- with the size and SHA-256 of each.
* `GENERATED_MANIFEST.json` covers the **generated root entries**: this
  packager writes 10 of them at package time --- they are not
  collected from anywhere and are therefore absent from `MANIFEST.json` by
  construction --- and the manifest carries the size and SHA-256 of
  9 of them, every one except itself.
* Between them every entry of this ZIP is manifested **except**
  `GENERATED_MANIFEST.json` itself, which cannot carry its own hash.  That
  one entry is authenticated as the whole archive always was: by the ZIP's
  SHA-256, published in the review manifest.

Both manifests are generated in the run that writes the bytes they describe.
Neither is typed, and neither can be stale.

**Auditing a single printed number.**  `AUDIT_MAP.json` answers, per printed
value: which record file it is computed from, which command regenerates that
record, and where it appears --- in the two documents' sources, or, for a
value that prints only in material moved out of them into this release, in
that material.  Which of the two is the case is the row's own
`location_class` field, carrying `r9_reconcile.py`'s verdict verbatim, so
`archive` (a legitimate release-only location) is never confused with
`orphan` (printed nowhere, which fails the reconciliation run).  It is derived
at package time from `r9_reconcile.py`'s curated claim table, from that
script's own scan of the `.tex` corpus, and from the command lines in
`COMMANDS.md` --- so it can name no command this archive does not document
and no location that is not in the sources shipped here.

It is **partial in a stated way**, and the file says so in its own `scope`
field rather than in a document beside it: its rows are the 405
curated headline and repeated claims, which are a curated audit and not an
exhaustive binding of every number.  The absence of a row is not evidence
that a value is unsupported; it means that value is outside the curated
binding, is recomputable from the shipped records, and is not asserted by
any gate.  A larger map would have to be written by hand, and a hand-written
map would look more complete while being less true.

## Path hygiene: the exact, gated statement

The claim, and nothing wider --- **every number in it is written by the gate
itself at build time, not typed into this file**:

> Of the entries of this archive that the gate **reads** --- every JSON
> member, parsed to its string leaves, and every other text member, scanned
> line by line --- none carries a build-machine or run-machine **absolute**
> path *of the syntaxes the gate matches*, except for the
> **6 declared exception files**.  Those files retain
> **757** matching contexts --- lines, or parsed JSON string leaves
> --- between them, containing **772** absolute-path occurrences;
> a single context can carry more than one path, which is why the two
> numbers differ and why each is reported under its own noun.  Each is
> enumerated and
> justified in `paper/is2/paper/BUILD_ENVIRONMENT.md` section 6.4 and in the
> `ABS_PATH_EXCEPTIONS` map of `make_release_zip.py`.  Outside them both
> counts are **zero**.
>
> Two qualifications are inside that claim, not footnotes to it.  **Binary
> members are out of scope**: the gate counts them and does not read inside
> them, so the claim covers 384 + 226 of the
> 637 ZIP entries and not the 27 binary ones.  **The POSIX
> recognizer matches a fixed list of machine roots** --- `root`, `home`,
> `mnt`, `media`, `opt`, `usr`, `var`, `tmp`, `Users`, `autodl-tmp`,
> `content`, `workspace` --- and not every leading slash, so a path under an
> unlisted root such as `/data`, `/scratch`, `/project` or `/private` would
> not match.  The Windows branch has no such restriction.
> `BUILD_ENVIRONMENT.md` section 6.4 states both limits in the same words.

The claim covers the 627 manifested payload files and the
10 generated root entries alike; what it does *not* cover is
the 27 binary members, which is why they are counted and named.

This claim must not be **wider than its checker**.  A checker that iterated
`MANIFEST.json`, i.e. the manifested payload only, while
`BUILD_ENVIRONMENT.md` section 6.4 and the gate's own header comment
quantify over every file in the ZIP, leaves the generated root entries
outside the census -- and one of them, `pip-freeze-full.txt`, holds
268 path-like strings.  The answer is the wider checker, not the narrower
sentence: the gate walks every entry, and `pip-freeze-full.txt` is a
declared exception with its reason recorded like every other --- a
`pip freeze --all` transcript in which the installation paths *are* the
provenance evidence, and from which nothing is installed (the installable
pins are `requirements-analysis.txt` and `requirements-experiment.txt`, both
clean).

**The gate, not this paragraph, is the authority.**  Run it and read its own
report:

```
python make_release_zip.py --check-paths <extracted-archive-root>
```

It prints the exception count, the per-file occurrence counts and its own
coverage, and it fails the build if a single path appears outside the map --
or if a declared exception has become clean and the exemption is therefore
wider than the facts.

Coverage of this build's run, over all **637** entries:
**384 JSON members** (130225
string leaves **parsed**, not regex-matched); **226 text members**
scanned line by line; 27 binary members out of scope and listed as
such; 34 portable `env`-style shebangs excluded by construction
(they name no machine).  384 + 226 + 27 =
637: every entry is in exactly one of the three categories, none is
skipped.  The checker matches the twelve enumerated POSIX machine roots listed
in the claim above, and any Windows drive letter or UNC host/share, so the
scope of the checker is exactly the scope of the claim --- neither wider nor
narrower.

A typed count in this paragraph rots: "exactly one declared exception" stays
on the page while the gate it cites reports nineteen, and the sentence is
true when written and false when read.  The count is interpolated from the
census the gate performs, so it cannot drift from the gate that way.

The declared exceptions of this build, with the number of matching contexts
and the number of absolute-path occurrences retained in each:

| file | matching contexts | path occurrences |
|---|---|---|
| `experiments/results/is_fresh/closure/code/common.py` | 1 | 2 |
| `paper/is2/paper/BUILD_ENVIRONMENT.md` | 7 | 8 |
| `paper/is2/paper/main.log` | 122 | 128 |
| `paper/is2/provenance/pip-freeze-full.txt` | 268 | 268 |
| `paper/is2/supplement/supplement.log` | 91 | 98 |
| `pip-freeze-full.txt` | 268 | 268 |
| **total** | **757** | **772** in **6** files |

The wider statement -- that a repository sweep finds *zero* absolute paths in
the result JSONs -- is **not** made here, because it is **false** of the
unsanitized records: hundreds of absolute-path fields were present in the
result JSONs as produced, every one of them under the run host's scratch
prefix, together with build-machine paths in the analysis logs.  Those fields
were sanitized (the machine prefix replaced by the placeholder `<RUN_ROOT>`,
every other byte and every numeric value unchanged and asserted so with a
parser); the log prefixes were stripped and their emitters fixed so
regeneration cannot reintroduce them; the original remote-host GPU runners,
job list, smoke transcript and vec_rerun drivers had the same run-host prefix
substituted in the same prefix-only way, so their flags, ordering and path
suffixes still read as the record of what was executed; and `main.log`, the
`pip freeze --all` transcript and this document's own build-machine record
were kept verbatim.  Every retained case is enumerated with its
reason in `ABS_PATH_EXCEPTIONS`, printed by the gate, and documented in
`BUILD_ENVIRONMENT.md` section 6.4 together with the proof of
value-preservation.

## Contents

| path | files |
|---|---|
| `experiments/results/e2` | 24 |
| `experiments/results/e4` | 15 |
| `experiments/results/e5` | 12 |
| `experiments/results/is_fresh` | 387 |
| `experiments/results/m0` | 12 |
| `experiments/ttt/analysis` | 5 |
| `experiments/ttt/core` | 3 |
| `experiments/ttt/e1_synthetic` | 2 |
| `experiments/ttt/e2_cifar` | 6 |
| `experiments/ttt/e4_gpt2` | 14 |
| `experiments/ttt/is_fresh` | 52 |
| `figures/F5_batch.pdf` | 1 |
| `figures/F6_calib.pdf` | 1 |
| `figures/scripts/_style.py` | 1 |
| `figures/scripts/_superseded` | 7 |
| `figures/scripts/bootstrap_ci.py` | 1 |
| `figures/scripts/fig_F5.py` | 1 |
| `figures/scripts/fig_F6.py` | 1 |
| `figures/scripts/fig_F7.py` | 1 |
| `figures/scripts/k3_baseline.py` | 1 |
| `figures/scripts/tab_T2.py` | 1 |
| `paper/is2/archive_tables` | 7 |
| `paper/is2/paper` | 34 |
| `paper/is2/provenance` | 5 |
| `paper/is2/supplement` | 16 |
| `paper/is2/tools` | 14 |
| `paper/mechanism_figures/1.svg` | 1 |
| `paper/mechanism_figures/2.svg` | 1 |
| `paper/mechanism_figures/3.svg` | 1 |

## JSON census

State this precisely, because the two counts are not the same count:

* **384 JSON files in the archive in total**;
* **381 result JSON files** under `experiments/results/`;
* the remaining 3 are the generated root-level JSON entries
  `AUDIT_MAP.json`, `GENERATED_MANIFEST.json`, `MANIFEST.json` --- archive metadata and audit indices, not result
  records.

The result records break down as:

| directory | result JSON files |
|---|---|
| `experiments/results/e2/` | 24 |
| `experiments/results/e4/` | 15 |
| `experiments/results/e5/` | 12 |
| `experiments/results/is_fresh/` | 318 |
| `experiments/results/m0/` | 12 |
| **total** | **381** |

Do not write "384 result JSON files"; write
"381 result JSON files plus the 3 generated
root-level JSON entries", or "384 JSON files in total".

## Where each claim comes from

`main` is `paper/is2/paper/main.pdf`, `supp` is
`paper/is2/supplement/supplement.pdf`.

The table below is at the granularity of a whole figure or table.  For the
per-printed-value map --- printed token, record file, regenerating command,
and file-and-line locations in both documents --- read `AUDIT_MAP.json`,
which is machine-readable and derived, and see "The audit boundary" above for
what it does and does not cover.

| manuscript object | script | output |
|---|---|---|
| main Fig. 4, risk-curve match (numbers) | `f7_curve_match.py` | `f7_curve_match_summary.json` |
| main Fig. 4, risk-curve match (figure) | `fig_f1_curves.py` | `paper/is2/paper/figures/F1_curves.pdf`, `fig_f1_curves.json` |
| main Fig. 5(a) one-step signed gain | `f10_oracle_grid.py` | `f10_oracle_grid_summary.json` |
| main Fig. 5(b) measured oracle gain | `f10_oracle_grid.py` | same |
| main Fig. 5(c) stopping-selection error | `f10_oracle_grid.py` | same |
| main Fig. 6 E2 cross-fit correlations | `f22*`/`f23` runs of `f8_e2_crossfit.py`, `f8b_e2_crossfit_det.py`, `f16_e2_gn_analysis.py`; plotted by `fig_f4_e2.py` | `f22_*_summary.json`, `f22b_*_summary.json`, `f22c_*_summary.json`, `f23_e2_gn_summary.json` |
| supplement S9.2 batch mechanics | `f5_batch_variance.py`, plotted by `figures/scripts/fig_F5.py` | `f5_batch_variance_summary.json` |
| main Fig. 7 entropy calibration | plotted by `figures/scripts/fig_F6.py` | `figures/F6_calib.pdf` |
| main Table 1, E2 matched-architecture arms | `f16_e2_gn_analysis.py` | `f16_e2_gn_summary.json`, `f23_e2_gn_summary.json` |
| main Table 2, compact non-selective E4 block | `f29_e4_pooled_ci.py`, `f30_e4_alignment_pooled.py` | `f29_e4_pooled_ci.json`, `f30_e4_alignment_pooled.json` |
| E2 correlations, PRE-correction audit trail | `f8_e2_crossfit.py`, `f8b_e2_crossfit_det.py`, `f16_e2_gn_analysis.py`, `f20_e2gn_loco_sensitivity.py` at their default prefixes | `f8*`, `f8b*`, `f16*`, `f20*` |
| E2 leave-one-corruption-out, corrected | `f20_e2gn_loco_sensitivity.py --out-name f24_...` | `f24_e2gn_loco_sensitivity.json` |
| E1 reported values, main section 6.1 | `f26_e1_reporting_audit.py` | `f26_e1_reporting_audit.json` |
| E2 temperature scaling, both loss estimands (main section 6.2) | `f34_e2_tempscale_estimands.py` | `f34_e2_tempscale_estimands.json` |
| E1 verification gate table (RELEASE ONLY: moved out of the supplement) | `paper/is2/tools/tab_s4_e1_gates.py` | `paper/is2/paper/figures/S4_e1_gates.tex` |
| E4 per-domain proxy details (typeset in the supplement, Table S7) | `paper/is2/tools/tab_s7_e4_proxy.py` | `paper/is2/paper/figures/S7_e4_proxy.tex` |
| E2 batch mechanics, the two halves as a table (typeset in the supplement) | `paper/is2/tools/tab_s5_e2_batch.py` | `paper/is2/paper/figures/S5_e2_batch.tex` |
| supp per-domain grid, and the RELEASE-ONLY per-severity grid `paper/is2/archive_tables/e2_severity_grid.tex` | `f16_e2_gn_analysis.py`, `f29_e4_pooled_ci.py` | `f16_e2_gn_summary.json`, `f29_e4_pooled_ci.json` |
| `BUILD_ENVIRONMENT.md` sections 3, 4 and 6.4 (generated) | `paper/is2/tools/build_env_section3.py` | `paper/is2/paper/BUILD_ENVIRONMENT.md` |
| E4 per-domain correlations + intervals (SUPERSEDED endpoints, retained audit trail) | `f11_e4_cluster_ci.py` | `f11_e4_cluster_ci.json` |
| E4 per-domain correlations + pooled percentile intervals (CURRENT) | `f29_e4_pooled_ci.py` | `f29_e4_pooled_ci.json` |
| E3 fixed-budget arms, clustered intervals and the paired difference against the selector (CURRENT, the primary E3 comparison) | `f32_e4_fixed_budget_ci.py` | `f32_e4_fixed_budget_ci.json` |
| E4 proxy validation, selections and point estimates (SUPERSEDED endpoints, retained audit trail) | `f12_e4_proxy_loo.py` | `f12_e4_proxy_loo.json` |
| E4 proxy validation, pooled percentile intervals and both exclusion counts (CURRENT) | `f31_e4_proxy_pooled.py` | `f31_e4_proxy_pooled.json` |
| E4 alignment-only comparison (SUPERSEDED endpoints, retained audit trail) | `f17_e4_alignment_only.py` | `f17_e4_alignment_only.json` |
| E4 alignment-only comparison and paired difference (CURRENT) | `f30_e4_alignment_pooled.py` | `f30_e4_alignment_pooled.json` |
| delta_feat proxy validation | `f14_deltafeat_check.py` | `f14_deltafeat_check.json` |
| E2 architecture-controlled entropy run | `f15_e2_entropy_gn.py` | `results/is_fresh/e2_gn/` |
| E2 fresh-GN feature proxy and its coverage census | `f38_e2gn_deltafeat_fresh.py` | `results/is_fresh/e2_gn/delta_feat_fresh_cifar10_resnet26ttt_s20260806.json`, `f38_e2gn_deltafeat_fresh.json` |
| E3 selector, recomputed from the released per-step vectors | `f39_e3_vector_selfcheck.py` | `f39_e3_vector_selfcheck.json` |
| Side-archive per-member manifest (name/bytes/sha256 per member, plus name/shape/dtype/sha256 per array) | `f40_e3_replicas_manifest.py` | `results/is_fresh/e3_vectors/REPLICAS_MANIFEST.json` |
| Theory-closure record side archive and its per-member manifest (bytes, sha256 as stored, sha256 of the decompressed bytes, record count) | `f41_closure_records_manifest.py` | `results/is_fresh/closure/CLOSURE_RECORDS_MANIFEST.json` |
| integer one-step criterion, measured | `f18_integer_boundary_check.py` | `f18_integer_boundary_check.json` |
| local-PL envelope monotonicity | `f33_pl_envelope_monotonicity.py` | `f33_pl_envelope_monotonicity.json` |
| local-PL envelope at zero noise | `f35_pl_zero_noise.py` | `f35_pl_zero_noise.json` |
| flow curve vs exact curve; sigma = 0 admissible | `f36_flow_integer_bridge.py` | `f36_flow_integer_bridge.json` |
| ReLU alpha-monotonicity, both readings | `f37_relu_monotonicity_recount.py` | `f37_relu_monotonicity_recount.json` |
| E2 leave-one-corruption-out sensitivity | `f20_e2gn_loco_sensitivity.py` | `f20_e2gn_loco_sensitivity.json` |
| E2 entropy sign-separation coverage and excluded group | `f21_e2_coverage.py` | `f21_e2_coverage.json` |
| E2 identity-level overlap of the cross-fit split | `f27_e2_identity.py` | `f27_e2_identity.json` |
| every curated number in BOTH documents | `paper/is2/tools/r9_reconcile.py` | exit status; 405 claims, 104 construction checks |
| dependency-provenance evidence and resolver transcripts | none (captured once, on the build machine) | `experiments/ttt/is_fresh/RESOLVER_TRANSCRIPT.md` |

## Which defect each fresh artefact answers

Every artefact below exists because of a specific defect in the analysis it
replaces.  The defect is stated, not its provenance.

| defect | artefact |
|---|---|
| the submission was not independently auditable | this archive; `MANIFEST.json`, `SEEDS.md`, `COMMANDS.md` |
| figures foregrounded superseded numbers | `fig_f2_phase.py`, `fig_f4_e2.py` and their data |
| the measured phase figure conflated the oracle with the selection error | `f10_oracle_grid.py`, `fig_f2_phase.py` |
| the E2 stochastic/deterministic confound | `f15_e2_entropy_gn.py` (architecture control), `f16_e2_gn_analysis.py` (matched-cell correlations), `f14_deltafeat_check.py` (proxy validation) |
| the fresh GroupNorm arm's feature proxy was a cross-source-model join covering 300 of its 11,520 episodes while the row printed 256 episodes/cell | `f38_e2gn_deltafeat_fresh.py` (remeasurement on the fresh model, plus the coverage census of both record sets), the `statistic_support` block `f16_e2_gn_analysis.py` now writes for every arm, and the `r9_reconcile.py` bindings of BOTH cardinalities |
| the E4 intervals were pseudoreplicated | `f11_e4_cluster_ci.py` |
| the E4 proxy was selected and evaluated on the same data | `f12_e4_proxy_loo.py` |
| continuous interpolation was conflated with executable integer steps | `f18_integer_boundary_check.py` |
| the local-PL envelope was said to decrease over its whole range, which the early branch does not | `f33_pl_envelope_monotonicity.py` |
| the E4 brackets were averaged percentile endpoints while being described as single percentile intervals | `f29_e4_pooled_ci.py`, `f30_e4_alignment_pooled.py`, `r9_reconcile.py` PASS 1b |
| the printed "0 of 4" favourable-side census contradicted `f12`'s own record, which says 1 | `f31_e4_proxy_pooled.py`, the `r9_reconcile.py` bindings of both exclusion counts, and the PASS 1b `.tex` assertions |
| `f12` still averaged endpoints while the documents called the pairs intervals | `f31_e4_proxy_pooled.py` (same remedy as `f29`/`f30`; `f12` retained as the audit trail) |
| `BUILD_ENVIRONMENT.md` section 3 carried one-build-stale sizes and checksums | `paper/is2/tools/build_env_section3.py` (section 3 and the 6.4 census are interpolated from the build products and the gate's census) |
| the absolute-path claim was wider than its manifest-limited checker, and 6.4's census was stale | the gate walks every ZIP entry; `pip-freeze-full.txt` is a declared exception; the census is generated |
| the per-domain E4 proxy detail was promised and not tabulated | `paper/is2/tools/tab_s7_e4_proxy.py` -> supplement Table S7 |
| the per-domain proxy table was set well below the surrounding type size, scaled to the text width, and its is2 copy was owned by a generator shared with the frozen tree whose `--check` compares only numeric tokens | `paper/is2/tools/tab_s7_e4_proxy.py`: an is2 generator of record with a BYTE `--check`, and a two-block layout that needs no scaling |
| one corruption family might have been driving the E2 sign | `f20_e2gn_loco_sensitivity.py` |
| the coverage of the entropy sign separation, and what the excluded episodes look like, were undocumented | `f21_e2_coverage.py` |
| the E2 loss proxy dropped the alignment sign | `f22`, `f22b`, `f22c`, `f23`, `f24` runs (corrected statistic) with `f8*`/`f16*`/`f20*` retained as the pre-correction trail |
| the E1 gate table was hand-edited into a five-part table with no generator, so its `--check` failed | `paper/is2/tools/tab_s4_e1_gates.py`, whose `--check` is a BYTE comparison and is run by this archive's verifier |
| a claim could keep passing after the text that printed it was deleted | the ORPHAN check of `paper/is2/tools/r9_reconcile.py`, which fails when a curated claim's token appears in neither document |
| there was no fresh F1 generator; the original read unarchived seed-42 records | `fig_f1_curves.py` (re-simulates and asserts it replays `f7` cell for cell; needs no record file) |
| stale generators wrote current filenames | `figures/scripts/_superseded/` + its `README.md`; the no-collision gate in `make_release_zip.verify` |
| `ENVIRONMENT.txt` carried an unportable `file:///` requirement | `pip-freeze-full.txt` (direct references rewritten to `name==version`) |
| a hand-written package census disagrees with the payload it counts | the JSON census above, computed from the payload rather than written by hand |
| "every script runs unchanged after extraction" is unqualified as stated | the "What reproducible means here" section above |
| the packager could not be run from the release it packages: it read four dependency-provenance entries out of a frozen parent archive that is not shipped, so `make_release_zip.py` failed from a clean extraction | `paper/is2/provenance/` (the four records shipped verbatim, with a README), `provenance_entries()` reading from there, and the payload assertion in `collect()` |
| the audit boundary was disclosed in prose only: the generated root documents sat outside every manifest | `GENERATED_MANIFEST.json`, generated in the same run that writes the bytes it hashes |
| auditing one printed number meant reading a figure-level table and then a JSON by hand | `AUDIT_MAP.json`, derived per printed value from the curated claim table, the `.tex` corpus and `COMMANDS.md` |
| documented page counts were typed and went stale against the built PDFs | `document_pages()`, read off the two pdflatex transcripts and interpolated into both generated documents |
| one requirements file was described as sufficient to recompute every number, conflating analysis reproduction with original experimental regeneration | the two-operation split above and the derived external-input census that says what the second one needs |
| the selector behind E3's selected-stop column was described as reproducible from the released records, which it is not | the retrospective-selector section above, which separates verification of stored outcomes from reconstruction of the selector |

## Provenance and honesty notes

* `experiments/results/is_fresh/FRESH_RESULTS.md` is the running audit record.
  It documents which published numbers were analytic, same-sample or
  single-seed, and what replaced them.  Read it before the JSONs.
* The original record sets under `experiments/results/{e2,e4,e5}` are the
  per-episode / per-document raw result records, shipped unmodified.  Every
  re-analysis in `is_fresh` reads them; none rewrites them.  The E1 objects
  under `experiments/results/is_fresh/` are a different level -- per-cell
  simulation summaries -- and the subsection "Two levels of retained record"
  in `INDEX.md` says which is which and what each supports.
* Model checkpoints and corrupted-image tensors are NOT included (size); the
  training and data-preparation scripts that produce them are
  (`e2_cifar/train_source.py`, `e2_cifar/data.py`,
  `e4_gpt2/prepare_data.py`).
* Archive: `release_archive.zip`.
