# VERIFY_TRANSCRIPT — a complete `verify(zip)` run on the pinned interpreter

## What this file is

A verbatim transcript of `make_release_zip.verify()` executed against this
archive from a **clean extraction**, on the **pinned Python 3.10.9** named in
`BUILD_INTERPRETER.md` and in `BUILD_ENVIRONMENT.md` §2 — captured with its
standard output, its wall-clock duration and its **process exit code**, so that
the statement "the archive verifies" can be read as a machine result rather
than taken on trust.

The result is at the bottom of the transcript: **exit code 0**, 86.2 s.

**This file is generated, not written.** It is produced by
`python tools/make_release_zip.py --write-verify-transcript`, which runs
`verify()` and renders this document from that one run, so the counts in the
prose below and the counts in the machine output cannot disagree with each
other. And its *currency* is enforced from the other side: `verify()` parses
this file out of the extracted archive and asserts its payload count, its ZIP
entry count and its declared-exception count against the archive that is
actually being shipped, so a transcript describing a different package fails
the build that would ship it. Both halves exist because a hand-written
document about a machine artefact goes stale the moment the artefact changes,
and nothing in a build notices unless something in the build reads it.

`verify()` does the extraction itself: it unpacks the ZIP into a fresh
temporary directory, runs every check inside that directory, and removes it.
Nothing in the transcript is run against the working tree the archive was
built from, and nothing it runs writes into this archive — the recomputations
write `verify_*` names inside the throwaway extraction only. Those paths appear
relative to the extraction root, which is why no machine-specific path occurs
anywhere below.

## READ THIS BEFORE READING "VERIFIED"

A passing run is two different things at once, and conflating them overstates
what has been reproduced.

| | what a passing run establishes |
|---|---|
| **FULL** | **Integrity and documentation.** All 627 payload files re-hash to their `MANIFEST.json` entries from the clean extraction; the staging/paper generator outputs are byte-identical inside the tree; `COMMANDS.md` accounts for all 50 analysis scripts and repeats no command line; no two live generators collide on an output basename; the absolute-path gate passes over all 637 entries, with 6 declared exceptions. |
| **FULL** | **Artefact regenerations at published parameters** — the `--check` modes of the shipped generators. Each regenerates a shipped artefact from the shipped records and compares it number for number. |
| **REDUCED** | **Code-path recomputations, at cut-down parameters.** `f7` at `--n-rep 4000` against a published default of 40,000 replicates per cell; `f11`, `f29`, `f31` at `--b 200` from a single bootstrap stream against published intervals built from 5 × 2000 = 10,000 pooled draws; `f8b` at `--n-boot 100`, one seed. `f29` and `f31` additionally run `--no-audit`, precisely *because* a 200-draw single-stream result must not be compared against the archived record. What each establishes is that the shipped generator runs inside the extracted tree on the shipped inputs and that its own internal assertions hold at reduced draws. |

**A passing `verify(zip)` is therefore NOT a regeneration of the published
numerical endpoints.** "Verified" here means: the archive is internally
consistent and complete, its generated documents and tables are current, and
its numerical pipeline executes end to end. It does not mean every published
number was recomputed.

**Where the full numerical reproduction lives.** It is the *default*
invocation of the same scripts — the `COMMANDS.md` command lines with no
`--b`, no `--boot-seeds`, no `--n-rep` and no `--no-audit` — under which each
script's own audit compares its output against the archived record. That is a
separate and much longer operation, and it is the one that reproduces the
published values. `r9_reconcile.py`, also listed in `COMMANDS.md`, binds the
curated headline values in the manuscript to the records of record and is
independent of both.

## Which build this transcript records, and why it cannot be this one

A ZIP cannot contain a transcript of a run made against itself: adding the
transcript changes the bytes that were hashed. The run below was therefore
made against the immediately preceding build of this archive, which is
identical to the shipped one in **every payload file except this transcript**.
That build's identity is printed in the transcript header (`zip bytes`,
`zip sha256`), so the two are distinguishable rather than conflated. It is
also why the currency gate in `verify()` binds payload and entry **counts**
rather than digests: the counts are exactly what the two builds share.

The shipped archive is not left unverified by that: `make_release_zip.py`
calls the same `verify()` on the archive it has just written, from the same
pinned interpreter, and refuses to finish the build if any check fails. The
shipped ZIP passed that run; this file is the readable long-form record of an
identical run one build earlier.

## Transcript, verbatim

```
command   : python tools/make_release_zip.py --write-verify-transcript
interpreter: 3.10.9 | packaged by Anaconda, Inc. | (main, Mar  1 2023, 18:18:15) [MSC v.1916 64 bit (AMD64)]
executable: python.exe
platform  : Windows-10-10.0.19045-SP0
zip       : release_archive.zip
zip bytes : 62889458
zip sha256: 5b7e269436ef4158ad9554482576a5822b7093e5651b29b37c64fcf07df60779
started   : 2026-08-19T04:06:30 UTC
----------------------------------------------------------------------
[release] manifest round-trip OK (627 files, 637 zip entries)
[release] staging/paper byte-identity OK for all 2 original generator outputs
[release] D6 inclusion OK: 1 member(s) named F8_domains.pdf
[release] COMMANDS.md accounts for all 50 is_fresh scripts
[release] COMMANDS.md duplicate-line gate OK (65 command lines and section headers, 0 repeated)
[release] no-collision gate OK (13 distinct figure/table outputs, 13 generators, 0 shared basenames; 3 author-drawn figures correctly claimed by none)
[release] absolute-path gate OK: 0 absolute paths outside the declared exceptions, over 384 JSON members (129771 string leaves parsed) and 226 text members; 27 binary members out of scope, 34 portable shebangs excluded by construction
[release]   scope: ALL 637 archive entries (627 manifested payloads + 10 generated root entries: AUDIT_MAP.json, BUILD_INTERPRETER.md, COMMANDS.md, GENERATED_MANIFEST.json, INDEX.md, MANIFEST.json, SEEDS.md, pip-freeze-full.txt, requirements-analysis.txt, requirements-experiment.txt)
[release]   6 declared exceptions, 756 matching contexts in them containing 771 path occurrences, each documented in BUILD_ENVIRONMENT.md 6.4 (contexts / occurrences per file below):
[release]        1 /    2  experiments/results/is_fresh/closure/code/common.py  -- the sanitizer's own docstring, naming the path shape it strips
[release]        7 /    8  paper/is2/paper/BUILD_ENVIRONMENT.md  -- the document whose PURPOSE is to record the reference build machine; it must name the TEXMF root, and section 6.4 discloses every exception in this map
[release]      122 /  128  paper/is2/paper/main.log  -- verbatim pdflatex transcript; the '0 errors / 0 undefined / N pages' rows of BUILD_ENVIRONMENT.md section 3 are statements about THIS file and are read out of it by build_env_section3.py, so editing it would falsify it as a build record (MiKTeX and user-profile paths)
[release]      268 /  268  paper/is2/provenance/pip-freeze-full.txt  -- the payload copy of the root entry above, byte-identical to it by construction; same reason, same paths, same evidentiary role
[release]       90 /   97  paper/is2/supplement/supplement.log  -- the same, for the second document of the pair; section 3 carries a supplement column and reads it out of this file
[release]      268 /  268  pip-freeze-full.txt  -- verbatim `pip freeze --all` provenance record of the build interpreter; the conda-prefix and user-site paths ARE the evidence of the mixed installation, and the installable pins are in the two requirements files instead
[release] table regeneration (supplement S4 --check against the shipped .tex): OK
           S4 MATCHES its generator (paper/is2/paper/figures/S4_e1_gates.tex)
[release] table regeneration (supplement S5 --check against the shipped .tex): OK
           ok paper/is2/paper/figures/S5_e2_batch.tex matches the records
[release] table regeneration (supplement S7 --check against the shipped .tex): OK
           S7 MATCHES its generator (paper/is2/paper/figures/S7_e4_proxy.tex)
[release] generated BUILD_ENVIRONMENT.md section 3 (--check): OK
           BUILD_ENVIRONMENT.md sections 3, 4 and 6.4 are CURRENT
[release] code-only reproduction (f7 risk-curve gate): OK
           [is_fresh] wrote experiments/results/is_fresh/verify_f7_seed20260806.json
           [f7] seed 20260806: published-norm 0.0410, pointwise 0.0655, max |err|/SE 2.98
           [is_fresh] wrote experiments/results/is_fresh/verify_f7_summary.json
           [f7] DONE
[release] data reproduction (f11 published-CI check): OK
           [f11] wikitext  rho=+0.834 (published +0.834)
                   naive  1500 rows  [+0.814, +0.850] (published [+0.810, +0.850])
                   nested  500 docs  [+0.806, +0.862]  x1.57 wider
                   seedavg 500 docs  [+0.831, +0.883]  rho_avg=+0.862
           [is_fresh] wrote experiments/results/is_fresh/verify_f11_e4_cluster_ci.json
           [f11] DONE
[release] pooled E4 intervals (f29 percentile construction): OK
           [f29] code      rho=+0.582  pooled clustered [+0.509429, +0.632849]  (f11 mean-of-5 [+0.509429, +0.632849])  x1.674 wider;  impr [0.710171, 1.267247]
           [f29] legal     rho=+0.905  pooled clustered [+0.883595, +0.919832]  (f11 mean-of-5 [+0.883595, +0.919832])  x1.572 wider;  impr [0.062727, 0.070356]
           [f29] pubmed    rho=+0.868  pooled clustered [+0.839392, +0.894823]  (f11 mean-of-5 [+0.839392, +0.894823])  x1.664 wider;  impr [0.311032, 1.076356]
           [f29] wikitext  rho=+0.834  pooled clustered [+0.806137, +0.862345]  (f11 mean-of-5 [+0.806137, +0.862345])  x1.568 wider;  impr [0.199502, 0.220054]
           [is_fresh] wrote experiments/results/is_fresh/verify_f29_e4_pooled_ci.json
           [f29] DONE
[release] pooled E4 proxy intervals (f31 percentile construction): OK
           [f31] hold out pubmed   : selected=alpha_only        -> held-out rho=+0.898 [+0.870630, +0.918123]; partial rho of delta_v2 given alignment =+0.091298 [+0.005267, +0.165163]  EXCLUDES ZERO (+)
           [f31] hold out wikitext : selected=phase_v2_gnorm    -> held-out rho=+0.869 [+0.847210, +0.891018]; partial rho of delta_v2 given alignment =+0.028296 [-0.075405, +0.118791]
           [is_fresh] wrote experiments/results/is_fresh/verify_f31_e4_proxy_pooled.json
           [f31] PARTIAL: the frozen proxy transfers to every untouched domain and beats the document-difficulty baseline in every fold, so the correlations are NOT a post-selection artefact of the four domains; but the shift term delta_v2 is not what carries them -- the alignment/noise factor alpha|alpha|/sigma^2 alone matches or exceeds the full statistic, and delta_v2 adds NO CONSISTENT incremental within-domain signal once alignment is held fixed: its pooled partial-Spearman interval excludes zero on the favourable side in 1 of 4 folds (pubmed) and on the ADVERSE side in 1 of 4 (code)
           [f31] partial-rho interval excludes zero on the FAVOURABLE side in 1/4 folds (pubmed) and on the ADVERSE side in 1/4 (code)
           [f31] DONE
[release] corrected E2 statistic (f8b signed re-analysis): OK
           [is_fresh] wrote experiments/results/is_fresh/verify_f8b_tent_seed20260806.json
           [f8b] tent: same-sample +0.851 -> cross-fit +0.849 (range +0.849..+0.849)
           [is_fresh] wrote experiments/results/is_fresh/verify_f8b_pl_seed20260806.json
           [f8b] pl: same-sample +0.858 -> cross-fit +0.820 (range +0.820..+0.820)
           [is_fresh] wrote experiments/results/is_fresh/verify_f8b_summary.json
           [f8b] DONE
----------------------------------------------------------------------
finished  : 2026-08-19T04:07:57 UTC
elapsed   : 86.2 s
exit code : 0
```

## Reproducing it

From the repository root, with the pinned interpreter:

```
python paper/is2/tools/make_release_zip.py --write-verify-transcript
echo $?     # 0
```

or, equivalently, rebuild the archive and let the build run the same function
as its final step:

```
python paper/is2/tools/make_release_zip.py
```

The second form ends in `[release] VERIFIED` and writes a new ZIP; the first
writes this file and nothing else outside its own temporary extraction.
