"""SUPERSEDED -- the packager of the FROZEN paper/is/ submission.

THIS IS NOT THE VERIFIER OF THIS RELEASE, AND IT WILL REFUSE TO RUN.
--------------------------------------------------------------------
It builds and verifies  paper/is/release_archive.zip, and its path-exception
map is written for THAT package layout.  Run against the package this
submission ships it reports failures that are artefacts of the layout
mismatch and not of the tree, which is exactly the way a stale duplicate
falsifies a hygiene claim.  It ships because experiments/ttt/is_fresh ships
whole, as the analysis suite as it was run; it is kept here as a record and
is quarantined at its command line (see the __main__ guard at the foot of
this file).

The packager and the absolute-path gate of THIS submission are

    python paper/is2/tools/make_release_zip.py --check-paths .

and nothing in this file is authoritative for anything either current
document says.  COMMANDS.md tabulates it under the scripts that ship but are
not part of this submission.

WHY THIS SCRIPT EXISTED
----------------------
A submission is not independently auditable while its referenced code, raw
outputs, per-run records, configurations, generated figures, bibliography and
build dependencies are absent: numerical checking is then limited to
consistency between two authored narratives.

The remedy is a self-contained archive that lets a reader recompute, not just
re-read.  This script assembles one, preserving repository-relative paths so
that no script inside it needs its paths edited after extraction -- which is
NOT the same as "runs unchanged", and the difference has to be stated rather
than left to be inferred: the re-analyses that produce every manuscript number
run from the shipped records once `requirements-analysis.txt` is installed,
whereas
the ORIGINAL model experiments additionally need a GPU, the external
datasets, and regenerated checkpoints and corruption tensors, all of which
are deliberately excluded by size.  This script then VERIFIES
the result by extracting it to a scratch directory and executing four
reproduction checks inside the extracted tree -- one that needs only code, one
that needs the shipped raw records, one that regenerates a manuscript table,
and one that recomputes the corrected E2 statistic.

WHAT GOES IN
  code/            the fresh analysis suite (experiments/ttt/is_fresh) plus the
                   original pipeline modules it imports and the original
                   experiment runners the records came from:
                     experiments/ttt/{core,e1_synthetic,e2_cifar,e3_imagenet,
                                      e4_gpt2,analysis}
                     figures/scripts  (the generators still current
                                      for F5, F6, F7 and T2, plus
                                      _superseded/, the quarantined
                                      original generators)
  results/         experiments/results/is_fresh (every fresh JSON + logs) and
                   the ORIGINAL record sets the fresh analyses consume:
                     results/e2/*_main_*.json     E2 episode records
                     results/e3/*.json            E3 ImageNet-C cells
                     results/e4/*.json            E4 GPT-2 per-document records
                     results/e5/*.json            E5 ablations, delta_feat,
                                                  delta_v2
                     results/provenance/<corruption>/<severity>/manifest.json
                                                  the per-cell ImageNet-C image
                                                  manifests Appendix C's
                                                  Table T3 cites
                     results/e5_gencheck/*.json   the generated-vs-downloaded
                                                  defocus-blur sanity check
                                                  Table T3 cites
  paper/           the manuscript sources as of build time: main.tex,
                   math_commands.tex, sections/, appendix/, figures/ (PDFs and
                   generated tables), references.bib, Highlights.txt, plus the
                   built main.pdf, its main.log (the package load list
                   BUILD_ENVIRONMENT.md greps) and its compiled main.bbl, so
                   the BibTeX-free rebuild BUILD_ENVIRONMENT.md section 1
                   documents works from THIS archive and not only from the
                   review package
  MANIFEST.json    every PAYLOAD file with its size and SHA-256.  Read that
                   word: it covers the files collected from the repository,
                   NOT every entry of the ZIP.  The eight generated root
                   entries below -- MANIFEST.json itself, SEEDS.md,
                   COMMANDS.md, BUILD_INTERPRETER.md, the two requirements
                   files, pip-freeze-full.txt and INDEX.md -- are produced by
                   this script at package time and are not listed in it.  They
                   are authenticated instead by the SHA-256 of the whole ZIP,
                   published in the review manifest, and all eight ARE inside
                   the absolute-path gate's census.  This line must not be
                   abbreviated to "every file": MANIFEST.json covers the
                   payload, the ZIP holds more than the payload, and the
                   distinction is the whole reason the word is there.
  SEEDS.md         the seed manifest: which seeds each stage used and why the
                   fresh range is disjoint from the original one
  COMMANDS.md      the exact command line for every script, in dependency order
  BUILD_INTERPRETER.md  interpreter, platform, machine, CUDA -- metadata only
  requirements-analysis.txt    the resolvable lock for recomputing every
                        manuscript number; verified with `pip install
                        --dry-run` in a clean Python 3.10.9 venv
  requirements-experiment.txt  the ORIGINAL GPU experiment environment as
                        recorded, documented as a build record pip cannot
                        reconstruct
  pip-freeze-full.txt   the complete build-environment freeze, also parseable
  INDEX.md         what each artefact is, which claim it supports, and which
                   defect it answers

EXCLUDED ON PURPOSE (and why -- stated so the omission is not mistaken for an
oversight): model checkpoints (*.pt) and raw image/corruption tensors, which
are large and reconstructible from the public datasets plus the shipped
training scripts; and the working directories of superseded analysis rounds,
which are not inputs to any number in the manuscript.

VERIFICATION (run automatically unless --no-verify)
  1. extract the archive to a scratch directory;
  2. re-hash every payload against MANIFEST.json;
  3. COMMANDS.md must name every script that ships in is_fresh;
  4. NO-COLLISION gate: no generator left in figures/scripts may write a file
     whose basename another current generator also writes.  The original
     generators that did (fig_F1/F2/F3/F4/F8, tab_T4) are quarantined under
     figures/scripts/_superseded/ with a README, are excluded from
     COMMANDS.md, and are not runnable in place;
  5. ABSOLUTE-PATH gate: no shipped text or parsed-JSON member may carry a
     build- or run-machine absolute path OUTSIDE the files enumerated in
     ABS_PATH_EXCEPTIONS, each with its stated reason in that map and each
     disclosed in BUILD_ENVIRONMENT.md 6.4.  The gate itself prints the
     exception-file and path-occurrence counts and is the authority on them;
     no prose in this file or in the generated INDEX.md restates them from
     memory.  Binary members are out of scope and are counted, not scanned;
     the POSIX branch matches the enumerated machine roots rather than every
     leading slash (BUILD_ENVIRONMENT.md 6.4 states both limits).  The checker walks EVERY manifest file,
     PARSES each JSON member and tests every string leaf of the parsed tree,
     and scans every non-JSON text member line by line; it matches both POSIX
     machine roots and Windows/UNC drive paths.  The scope of the checker is
     the scope of the claim.  A "zero absolute paths" statement whose sweep
     is a Windows-only regex over a subset of files does not support a
     universal claim;
  6. inside the extracted tree, run the reproduction checks listed in
     `verify()`, whose count is asserted against that list.  The three
     `--check` checks are read-only; the rest run at REDUCED parameters, so
     every one of them that writes does so under a `verify_*` name, and the
     read-only checks run first: otherwise the reduced f7 run overwrites
     f7_curve_match_summary.json and the table check then scores the
     manuscript against 4,000-replicate numbers.

     WHAT A REDUCED RUN DOES AND DOES NOT ESTABLISH.  The bootstrap checks
     run at B = 200 draws from ONE RNG
     stream, against published endpoints built from 5 x B = 2000 draws pooled
     into 10,000.  They are CODE-PATH checks: they prove that the shipped
     records feed the shipped generator, that it runs to completion inside the
     extracted tree, and that its own internal assertions hold at reduced
     draws.  They are NOT a reproduction of the published endpoints, and no
     statement anywhere in this package may be read as claiming they are.  A
     full replay is a separate, longer operation: run the same scripts at
     their published parameters -- the command lines in COMMANDS.md, with no
     --b and no --boot-seeds override and without --no-audit -- which rebuilds
     each interval from all five streams and, under --audit, asserts the
     result against the archived record.  In order:
       tab_t4_e1_gates.py --check
         (regenerates Table T4 from the shipped five-seed summaries and the
         f26 audit and asserts every number matches the shipped .tex) -- proves
         the manuscript's gate table is generated, not hand-maintained;
       tab_t6_e4_proxy.py --check
         (the same, for the per-domain E4 proxy table and the exclusion counts
         in its caption);
       build_env_section3.py --check
         (the generated blocks of BUILD_ENVIRONMENT.md against the shipped
         build products and the shipped dependency lock);
       f7_curve_match.py --n-rep 4000 --seeds 20260806
         --out-prefix verify_f7
         (code only: simulates risk curves and asserts the
         published-normalisation gate) -- proves the code executes standalone;
       f11_e4_cluster_ci.py --b 200 --boot-seeds 20260806
         --out-name verify_f11_e4_cluster_ci.json
         (data dependent, REDUCED: rebuilds the E4 correlations from the
         shipped raw records; its internal assertion is that the i.i.d.-row
         construction lands within 0.02 of the published i.i.d.-row endpoints,
         which at 200 draws is a records-are-the-right-records check and not a
         reproduction of the published clustered endpoints);
       f29_e4_pooled_ci.py --b 200 --boot-seeds 20260806 --no-audit
         --out-name verify_f29_e4_pooled_ci.json
         (the CURRENT E4 interval generator: the same records through the
         pooled-percentile construction that produces every E4 endpoint the
         manuscript prints.  --no-audit because a 200-draw single-stream run
         must NOT be compared with the archived 10,000-draw record; the point
         of the check is that the generator of the printed endpoints runs in
         the extracted tree, not that it reproduces them here);
       f31_e4_proxy_pooled.py --b 200 --boot-seeds 20260806 --no-audit
         --out-name verify_f31_e4_proxy_pooled.json
         (the CURRENT E4 PROXY interval generator, same reasoning as f29);
       f8b_e2_crossfit_det.py --statistic phase_loss --n-boot 100
         --seeds 20260806 --out-prefix verify_f8b
         (the corrected signed E2 statistic (C.1)/(C.2) recomputed from the
         shipped episode records; it asserts internally that the retained
         unsigned numerator still reproduces the pre-correction values, which
         localises the sign fix) -- proves the E2 re-analysis is
         self-contained.
  Every script asserts internally, so a non-zero exit is a failed audit.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TTT = os.path.dirname(HERE)
REPO = os.path.dirname(TTT)
OUT_DEFAULT = os.path.join(REPO, "paper", "is", "release_archive.zip")

CODE_DIRS = [
    "experiments/ttt/is_fresh",
    "experiments/ttt/core",
    "experiments/ttt/e1_synthetic",
    "experiments/ttt/e2_cifar",
    "experiments/ttt/e3_imagenet",
    "experiments/ttt/e4_gpt2",
    "experiments/ttt/analysis",
    "figures/scripts",
]
RESULT_DIRS = [
    "experiments/results/is_fresh",
    "experiments/results/e2",
    "experiments/results/e3",
    "experiments/results/e4",
    "experiments/results/e5",
    # Appendix C's Table T3 cites the per-(corruption, severity) image
    # manifests and the generated-vs-downloaded defocus-blur sanity check, so
    # both record sets must ship or the table cites nothing.
    "experiments/results/provenance",
    "experiments/results/e5_gencheck",
]
PAPER_DIRS = ["paper/is/paper"]
# The four objects still produced by the original generators.  Those
# generators write into `figures/` (the repository-level staging directory)
# and the file
# is then copied into `paper/is/paper/figures/`.  COMMANDS.md states that the
# two copies are byte-identical *in this archive*, so both copies must ship and
# the identity must be machine-checked -- shipping only the paper copy made
# that sentence false as written.  `verify()` asserts the identity.
STAGING_FILES = ["figures/F5_batch.pdf", "figures/F6_calib.pdf",
                 "figures/F7_imagenet.pdf", "figures/T2_e3_full.tex"]
PAPER_SKIP_EXT = {".aux", ".log", ".out", ".blg", ".abs", ".synctex.gz"}
SKIP_DIR_PARTS = {"__pycache__", ".git", ".ipynb_checkpoints", "ckpt"}
SKIP_EXT = {".pyc", ".pt", ".pth", ".npy", ".tar", ".gz", ".zip"}


def walk(root_rel, want):
    base = os.path.join(REPO, root_rel)
    if not os.path.isdir(base):
        return
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                continue
            if not want(fn, ext):
                continue
            full = os.path.join(dirpath, fn)
            yield full, os.path.relpath(full, REPO).replace("\\", "/")


def collect():
    files = {}
    for d in CODE_DIRS:
        for full, rel in walk(d, lambda fn, ext: ext in {".py", ".sh", ".md",
                                                         ".txt"}):
            files[rel] = full
    for d in RESULT_DIRS:
        for full, rel in walk(d, lambda fn, ext: ext in {".json", ".md",
                                                         ".log", ".txt"}):
            files[rel] = full
    for d in PAPER_DIRS:
        # ".md" is in the whitelist so that paper/is/paper/BUILD_ENVIRONMENT.md
        # -- the pinned LaTeX environment -- travels with the sources it
        # describes.
        for full, rel in walk(
                d, lambda fn, ext: (ext in {".tex", ".bib", ".txt", ".pdf",
                                            ".md"}
                                    and ext not in PAPER_SKIP_EXT
                                    and fn not in {"main.pdf"})):
            files[rel] = full
    for rel in STAGING_FILES:
        full = os.path.join(REPO, rel.replace("/", os.sep))
        paper_twin = os.path.join(REPO, "paper", "is", "paper",
                                  rel.replace("/", os.sep))
        assert os.path.exists(full), (
            f"{rel} is missing -- COMMANDS.md documents it as the staging "
            f"copy the original generator writes; re-run the generator")
        assert os.path.exists(paper_twin), f"{paper_twin} is missing"
        assert sha256(full) == sha256(paper_twin), (
            f"{rel} and its paper copy differ; COMMANDS.md claims they are "
            f"byte-identical, so re-stage before packaging")
        files[rel] = full
    mainpdf = os.path.join(REPO, "paper/is/paper/main.pdf")
    if os.path.exists(mainpdf):
        files["paper/is/paper/main.pdf"] = mainpdf
    # main.log must ship.  BUILD_ENVIRONMENT.md reads the 68-file package
    # load list off it and supplies `grep` commands against it, so a package
    # that omitted it would make a claim it could not honour.  Only main.log:
    # the r*p*.log build transcripts beside it are scratch.
    mainlog = os.path.join(REPO, "paper/is/paper/main.log")
    assert os.path.exists(mainlog), (
        "paper/is/paper/main.log is missing -- BUILD_ENVIRONMENT.md documents "
        "it as shipped; rebuild the PDF before packaging")
    files["paper/is/paper/main.log"] = mainlog
    # main.bbl must ship too.  BUILD_ENVIRONMENT.md section 1 states that
    # "main.bbl ships in the archive, so a reader without the .bib toolchain
    # can skip bibtex".  `.bbl` is not in the PAPER_DIRS extension whitelist
    # above, so without this assertion a reader who extracts this archive and
    # runs pdflatex gets "No file main.bbl" and 96 undefined-citation
    # warnings, and the documented BibTeX-free path does not exist here.
    # Shipping the file is what makes the sentence true rather than narrower:
    # the byte-identical .bbl travels with the sources in BOTH packages, so
    # the cross-package byte-identity check covers it automatically and the
    # two cannot diverge.
    mainbbl = os.path.join(REPO, "paper/is/paper/main.bbl")
    assert os.path.exists(mainbbl), (
        "paper/is/paper/main.bbl is missing -- BUILD_ENVIRONMENT.md section 1 "
        "documents it as shipped in this archive so that a reader without the "
        "'.bib' toolchain can skip bibtex; run bibtex before packaging")
    files["paper/is/paper/main.bbl"] = mainbbl
    return dict(sorted(files.items()))


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


SEEDS_MD = """# Seed manifest

Every random number in the fresh (`is_fresh`) analysis suite comes from a seed
in the 20260801+ range.  The original pipeline used 0, 1, 2, 42, 43, 100+ and
999+; none of those values is reused anywhere in the fresh suite, so a fresh
result can never be a re-report of a tuned original one.

| stage | script | seeds | role of the seed |
|---|---|---|---|
| E1 risk-curve match | `f7_curve_match.py` | 20260801-05 | trajectory simulation |
| E1 one-step boundary | `f1_boundary_onestep.py` | 20260801-05 | trajectory simulation |
| E1 stopped boundary | `f2_boundary_stopped.py` | 20260801-05 | simulation + SELECT/SCORE split |
| E1 three-gain grid | `f10_oracle_grid.py` | 20260801-05 | simulation + SELECT/SCORE split |
| E1 optimal stopping | `f3_optimal_stopping.py` | 20260801-05 | trajectory simulation |
| ALTA vs measured oracle | `f4_alta_measured_oracle.py` | 20260801-05 | ALTA episodes + oracle blocks |
| ALTA vs compute-matched oracle | `f13_compute_matched.py` | 20260801-05 | ALTA episodes + K-group oracle blocks |
| batch variance | `f5_batch_variance.py` | 20260801-05 | trajectory simulation |
| ReLU / PL regime | `f6_relu_multiseed.py` | 20260801-05 | network init + SGD |
| E2 cross-fit (stochastic) | `f8_e2_crossfit.py` | 20260801-05 | commissioning/evaluation split of existing episodes |
| E2 cross-fit (deterministic) | `f8b_e2_crossfit_det.py` | 20260801-05 | same |
| E4 clustered intervals (superseded endpoints; point estimates current) | `f11_e4_cluster_ci.py` | 20260806-10 | bootstrap resampling only |
| E4 clustered PERCENTILE intervals, pooled | `f29_e4_pooled_ci.py` | 20260806-10, pooled | replays f11's streams; no new randomness |
| E4 leave-one-domain-out proxy | `f12_e4_proxy_loo.py` | 20260806-10 | bootstrap resampling only |
| E2 entropy on ResNet-26+GN | `f15_e2_entropy_gn.py` | 20260806 | source training + episode sampling |
| E2 matched-cell cross-fit (all arms) | `f16_e2_gn_analysis.py` | 20260801-05 | commissioning/evaluation split of existing episodes |
| E4 alignment-only vs full statistic (superseded endpoints) | `f17_e4_alignment_only.py` | 20260811-15 | bootstrap resampling only |
| E4 alignment-only, pooled percentile intervals | `f30_e4_alignment_pooled.py` | 20260811-15, pooled | replays f17's streams; no new randomness |
| integer-criterion check on the f10 grid | `f18_integer_boundary_check.py` | 20260801-05 | none of its own: re-reads the f10 replicates |
| E2 leave-one-corruption-out sensitivity | `f20_e2gn_loco_sensitivity.py` | 20260801-05 split seeds; 20260817 bootstrap | cross-fit split of existing episodes; deletion bootstrap |
| E2 cross-fit, CORRECTED signed statistic, feature proxy | `f8_e2_crossfit.py --statistic phase_feat --out-prefix f22_e2_crossfit_feat` | 20260801-05 | commissioning/evaluation split of existing episodes |
| E2 cross-fit, CORRECTED signed statistic, deterministic arms | `f8b_e2_crossfit_det.py --statistic phase_loss --out-prefix f22b_e2_crossfit_det` | 20260801-05 | same |
| E2 cross-fit, CORRECTED signed statistic, loss proxy | `f8_e2_crossfit.py --statistic phase_loss --out-prefix f22c_e2_crossfit_loss` | 20260801-05 | same |
| E2 matched-cell cross-fit, CORRECTED | `f16_e2_gn_analysis.py --out-prefix f23_e2_gn` | 20260801-05 | same |
| E2 leave-one-corruption-out, CORRECTED | `f20_e2gn_loco_sensitivity.py --out-name f24_e2gn_loco_sensitivity.json` | 20260801-05 split seeds; 20260817 bootstrap | as `f20` |
| E2 learning-rate ablation | `f25_e2_lr_ablation.py` | 20260801-05 | cross-fit split of existing episodes |
| E1 reporting audit (excess, accuracy and comparison-count census) | `f26_e1_reporting_audit.py` | none of its own: re-reads the f7/f10/f3/f4/f13 records | -- |
| E2 identity-level overlap of the cross-fit split | `f27_e2_identity.py` | 20260801-05 | reproduces f8's commissioning/evaluation split stream exactly |
| Appendix B (P3) counterexample simulation | `f28_p3_montecarlo.py` | 20260801-05 | Pareto draws and the scan, 2e7 replications per seed |
| Fig. 1 risk curves | `fig_f1_curves.py` | 20260801-05 | replays `f7_curve_match.py`'s replicate stream cell for cell |

`f14_deltafeat_check.py` and `f21_e2_coverage.py` are deterministic: they
re-read existing records and compute rank or frequency statistics, with no
random component.  So are the figure scripts
`fig_f2_phase.py`, `fig_f3_alta.py`, `fig_f4_e2.py` and `fig_f8_domains.py`,
which plot the JSONs the scripts above emit and draw no random numbers, the
table generator `tab_t4_e1_gates.py`, which reads the fresh summaries plus
`f26_e1_reporting_audit.json`, and `f_scope_bench.py`, which measures
wall-clock only.

`fig_f1_curves.py` is the one figure script that draws random numbers: the
risk curves it plots are not stored in any record, so it re-simulates them.
It does so by replaying `f7_curve_match.py`'s loop verbatim -- same seeds,
same 30-cell order, same single `default_rng` stream -- and ASSERTS that all
120 per-cell error statistics per seed reproduce the archived
`f7_curve_match_seed<seed>.json` rows to 1e-9 relative.  The curves in
Figure 1 are therefore, replicate for replicate, the ones Sec. 5.1 and
Table T4 row (a) report on.

The bootstrap seeds are allocated in disjoint blocks so that no two resampling
analyses share a stream: 20260806-10 (`f11`, `f12`), 20260811-15 (`f17`),
20260817 (`f20`, `f24`).

The corrected E2 re-analyses (`f22`, `f22b`, `f22c`, `f23`, `f24`, `f25`) reuse
the split seeds, bootstrap protocol and cell populations of the runs they
correct, unchanged; only the statistic's sign convention changed.  Their
pre-correction counterparts (`f8*`, `f16*`, `f20*`) ship unmodified as the
audit trail.

The ORIGINAL records shipped under `experiments/results/{e2,e3,e4,e5}` carry
their own seeds inside `meta.argv.seed` of each file; those are the original
0/1/2 values and are reported as such.
"""


def curated_claim_counts():
    """(numeric claims, construction claims) read OFF r9_reconcile.py itself.

    A number typed into prose beside a gate is a second, unchecked copy of
    that gate's output, and it rots.  The curated table grows whenever a claim
    is bound, and its count is quoted in COMMANDS.md, INDEX.md,
    BUILD_ENVIRONMENT.md and FRESH_RESULTS.md.
    Importing the module and measuring its own tables is the only way the
    generated documents cannot disagree with the script they describe.
    """
    import importlib
    import sys as _sys
    if HERE not in _sys.path:
        _sys.path.insert(0, HERE)
    r9 = importlib.import_module("r9_reconcile")
    # +4: the four structural checks run_pass1b performs inline (endpoints
    # moved; f29 and f30 replay the superseded draws; verdict counts held).
    return len(r9.CHECKS), len(r9.CONSTRUCTIONS) + 7


def commands_md():
    n_curated, n_construction = curated_claim_counts()
    return """# Exact commands, in dependency order

All paths are relative to the extracted archive root.

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
* **PyTorch is a real dependency of nearly every script here, not an optional
  one.**  Every script in `experiments/ttt/is_fresh` that imports `common.py`
  imports it transitively: `common.py` does `import run_e1`, and
  `experiments/ttt/e1_synthetic/run_e1.py` does `from core.utils import
  save_json`, and `experiments/ttt/core/utils.py` does `import torch` at module
  scope.  So `import torch` must succeed even for the pure-CPU, pure-numpy
  re-analyses.  On top of that, `f6_relu_multiseed.py` and `f_scope_bench.py`
  use torch directly, and `f15_e2_entropy_gn.py` plus the original experiment
  runners under `experiments/ttt/{e2_cifar,e3_imagenet,e4_gpt2}` need torch
  **and** torchvision **and** a GPU.
  The only scripts that run without torch are the four in `figures/scripts`
  (`fig_F5.py`, `fig_F6.py`, `fig_F7.py`, `tab_T2.py`) and their helpers, which
  import only numpy and matplotlib.
* **Installing the dependencies.** Run

  ```
  python -m pip install -r requirements-analysis.txt
  ```

  That single file is everything needed to recompute every manuscript number.
  It is a focused lock -- comments plus plain `name==version` pins, nothing
  else -- and it is *dependency-resolvable*: `pip install --dry-run -r
  requirements-analysis.txt` against a clean Python 3.10.9 virtual
  environment resolves with no conflict.  The transcript is archived in
  `experiments/ttt/is_fresh/RESOLVER_TRANSCRIPT.md` §2.

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
  `experiments/ttt/is_fresh/RESOLVER_TRANSCRIPT.md`; that file also records
  why the pair is a property of the on-disk installation layout rather than
  of conda's own solver, which would not produce it.
  The file names the conflict, gives a resolvable substitution
  (`opencv-python==4.9.0.80`, transcript in `RESOLVER_TRANSCRIPT.md` §2),
  and lists the GPU, dataset and checkpoint
  prerequisites that no requirements file can supply.  The former single
  `requirements.txt` merged the two sets and was therefore not installable as
  advertised; it has been removed rather than
  patched, so no reader can install the unsatisfiable union by accident.

  Interpreter, OS and hardware metadata are in `BUILD_INTERPRETER.md`; the
  complete freeze of the build machine (a Windows/Anaconda environment, most
  of it unrelated to this project, but also pip-parseable) is in
  `pip-freeze-full.txt`.  These files replace the former single
  `ENVIRONMENT.txt`, whose first two uncommented lines were the interpreter
  description and `platform win32`, so `pip install -r ENVIRONMENT.txt`
  failed immediately even though this file claimed it was installable.
* **The LaTeX side is pinned separately** in
  `paper/is/paper/BUILD_ENVIRONMENT.md`, which ships in this archive: TeX
  distribution and engine version, the version of every layout-affecting
  package as loaded, the exact five-pass build command and why five, the
  expected page count and PDF checksum, the disposition of every remaining
  overfull box, and why an independent rebuild can land on a different page
  count without any substantive difference. Read it before reporting a
  page-count mismatch.

Every executable script in `experiments/ttt/is_fresh` appears below exactly
once.  The only two files in that directory with no command line are
`common.py`, which is an imported module (paths, seed lists, JSON helpers) and
has no `main()`, and `make_release_zip.py`, which builds this archive and is
listed separately at the end.

## The fresh suite

```
cd experiments/ttt/is_fresh

# --- solvable-model measurements (CPU, minutes to ~1 h each) --------------
python f7_curve_match.py                 # risk-curve match, 5 seeds
python f1_boundary_onestep.py            # one-step measured boundary
python f2_boundary_stopped.py            # selected-stopping measured boundary
python f10_oracle_grid.py                # one-step / oracle / selection error
python f18_integer_boundary_check.py     # integer criterion on the f10 grid
#                                          (reads f10 records; run f10 first)
python f3_optimal_stopping.py
python f5_batch_variance.py
python f6_relu_multiseed.py
python f4_alta_measured_oracle.py        # ALTA vs measured K=1 oracle
python f13_compute_matched.py            # ALTA vs compute-matched K=3 oracle

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
python f31_e4_proxy_pooled.py            # the same pooling for the proxy
#                                          validation: f12's own five
#                                          B = 2000 streams, pooled into a
#                                          single 10,000-draw empirical
#                                          distribution per quantity.  Every
#                                          proxy interval endpoint the
#                                          manuscript and Table T6 print comes
#                                          from here.  Asserts it replays
#                                          f12's exact draws, that no point
#                                          estimate or fold selection moved,
#                                          and that the favourable-side and
#                                          adverse-side exclusion counts agree
#                                          between the two constructions
python f17_e4_alignment_only.py          # E4 alignment-only vs full statistic
#                                          -- SUPERSEDED for its endpoints in
#                                          the same way; run before f30.
python f29_e4_pooled_ci.py               # E4 document-clustered PERCENTILE
#                                          intervals: f11's five B = 2000
#                                          streams POOLED into one 10,000-draw
#                                          distribution, one 2.5/97.5 pair off
#                                          it.  Every E4 interval endpoint the
#                                          manuscript prints comes from here.
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
# The archived f16_*/f20_* records are HISTORICAL: the signed-statistic fix
# changed the code these two scripts run, and f16/f20 expose no unsigned mode,
# so re-running the commands below today reproduces the CORRECTED numbers,
# i.e. the f23_*/f24_* records, not the archived f16_*/f20_* ones.  The
# pre-correction E2 cross-fit values that ARE regenerable are the f8 family,
# via --statistic phase_loss_unsigned (see the note at the end of this block).
python f16_e2_gn_analysis.py             # -> f16_* names, corrected values
python f20_e2gn_loco_sensitivity.py      # -> f20_* names, corrected values

# --- E2, CORRECTED SIGNED STATISTIC -- these produce the reported numbers --
# The manuscript defines every proxy phase statistic with a SIGNED alignment
# factor, Phi = alpha_sgn|alpha_sgn| delta_proxy / sigma^2_rel  (App. C, C.1),
# and Phi_0 = alpha_sgn|alpha_sgn| delta_proxy on a zero-noise arm (C.2).  The
# A loss-proxy branch computing alpha**2 drops that sign.  Every E2 number in
# the paper comes from the runs below; the f8/f16/f20 outputs above ship
# unmodified so the difference between the two statistics is auditable.
python f8_e2_crossfit.py  --statistic phase_feat \\
       --out-prefix f22_e2_crossfit_feat       # feature proxy (sign-carrying)
python f8b_e2_crossfit_det.py --statistic phase_loss \\
       --out-prefix f22b_e2_crossfit_det       # tent / pseudo-label
python f8_e2_crossfit.py  --statistic phase_loss \\
       --out-prefix f22c_e2_crossfit_loss      # ttt_rot / ttt_mask, loss proxy
python f16_e2_gn_analysis.py --out-prefix f23_e2_gn        # matched 45 cells
python f20_e2gn_loco_sensitivity.py \\
       --out-name f24_e2gn_loco_sensitivity.json           # LOCO, after f23
python f25_e2_lr_ablation.py             # E5 learning-rate ablation (Sec. 5.5);
#                                          asserts the unsigned numerator still
#                                          reproduces the archived 0.603 /
#                                          0.573 / 0.588
#   The pre-correction values are regenerable with
#     python f8_e2_crossfit.py --statistic phase_loss_unsigned ...
#   and f8b/f25 assert that they reproduce the archived JSONs.

# --- E1 reporting audit (Sec. 5.1 and Table T4) ---------------------------
python f26_e1_reporting_audit.py         # recomputes the E1 reported values
#                                          from the f7/f10/f3/f4/f13 records

# --- E2 identity-level overlap of the cross-fit split (Sec. 7.2, App. C.2) -
python f27_e2_identity.py                # -> f27_e2_identity.json.  Counts the
#                                          image identities that land in both
#                                          shares of the E2 commissioning /
#                                          evaluation split, the episode rows
#                                          they account for, and the shift in
#                                          every headline rho when all of them
#                                          are deleted from BOTH shares.
#                                          Reproduces f8_e2_crossfit.py's split
#                                          stream exactly.

# --- Appendix B (P3) fixed-law counterexample, direct simulation -----------
python f28_p3_montecarlo.py              # -> f28_p3_montecarlo.json.  1e8
#                                          replications over 5 seeds of the
#                                          population-band scan on the fixed
#                                          symmetric Pareto law; reports
#                                          Pr(Excbar(that) > RHS)/gamma at
#                                          gamma = 1e-4, 1e-5, 1e-6 with Monte
#                                          Carlo standard errors.  Takes about
#                                          7 minutes.
python f28_p3_montecarlo.py --reps 200000 \\
       --out verify_f28_p3_montecarlo.json
#                                          minute-scale SMOKE RUN.  --out is
#                                          mandatory here and the script now
#                                          refuses a reduced-parameter run
#                                          without it: writing a 1e6-replicate
#                                          result over the record of record
#                                          f28_p3_montecarlo.json would make
#                                          r9_reconcile.py report three
#                                          spurious Appendix B mismatches.
#                                          Same guard as f7/f8's --out-prefix.

# --- final number reconciliation ----------------------------------------
python r9_reconcile.py                   # {n_curated} CURATED headline claims
#                                          re-derived from the JSONs above and
#                                          compared with the token the
#                                          manuscript prints, plus a
#                                          model-free scan of every .tex for
#                                          one interval printed two ways.
#                                          Exits non-zero on a mismatch.
#                                          Reads only; writes nothing.
#                                          It is a CURATED HEADLINE AUDIT, not
#                                          an exhaustive binding of every
#                                          number in the manuscript: the two
#                                          Appendix B analytic thresholds are
#                                          unbound, the Monte Carlo SEs are
#                                          not separately asserted, the E3
#                                          safety-failure counts, the E3 K = 3
#                                          matched comparison, the E3 seed
#                                          spreads, the E2 leave-one-
#                                          corruption-out fold intervals and
#                                          some E2 conditional calibration
#                                          proportions are all reported and
#                                          none of them is bound, and a purely
#                                          SEMANTIC error (a correct number
#                                          under a wrong label) is invisible
#                                          to a value check.  Report it as
#                                          "{n_curated} curated headline and
#                                          repeated numerical claims", never
#                                          as "every number".  See the
#                                          r9_reconcile.py docstring.
#                                          It also runs {n_construction}
#                                          CONSTRUCTION checks (PASS 1b):
#                                          assertions that the
#                                          E4 brackets are still built by
#                                          POOLING the five bootstrap streams
#                                          into one 10,000-draw distribution
#                                          rather than by averaging five
#                                          percentile endpoints, checked on
#                                          the records AND on the .tex corpus.
#                                          A value check cannot express that,
#                                          which is how the defect it guards
#                                          against once passed a green run.
python r9_reconcile.py --emit-current-values
#                                          regenerates the "CURRENT VALUES"
#                                          table at the top of
#                                          results/is_fresh/FRESH_RESULTS.md

# --- figures and tables (write into paper/is/paper/figures) ---------------
python fig_f1_curves.py                  # Fig. 1 (re-simulates; asserts it
#                                          replays f7 cell for cell)
python fig_f2_phase.py                   # Fig. 2 (needs f10)
python fig_f3_alta.py                    # Fig. 3 (needs f4, f13)
python fig_f4_e2.py                      # Fig. 4 (needs f22, f22b, f22c, f23)
python fig_f8_domains.py                 # Fig. 8.  RESULT-RECORD dependency:
#                                          f30_e4_alignment_pooled.json, and
#                                          that alone -- every number drawn,
#                                          every interval and every annotation
#                                          comes from it.  It additionally
#                                          IMPORTS f11_e4_cluster_ci as a
#                                          Python HELPER MODULE, for its
#                                          record loader and its Spearman
#                                          routine; that is a code dependency,
#                                          not a data one, and it does NOT
#                                          read f11_e4_cluster_ci.json.  It
#                                          does not read f17 at all.  This
#                                          line must not be abbreviated to
#                                          "needs f11 and f17": that describes
#                                          the superseded data path.
python tab_t4_e1_gates.py                # Table T4 (needs f7, f10, f3, f26)
python tab_t4_e1_gates.py --check        # verify the shipped T4 .tex instead
#                                          of overwriting it
python tab_t6_e4_proxy.py                # Table T6, the per-domain E4 proxy
#                                          table of App. D (needs f31)
python tab_t6_e4_proxy.py --check        # verify the shipped T6 .tex instead
#                                          of overwriting it

# --- generated documentation (run AFTER the LaTeX build) -----------------
python build_env_section3.py             # interpolates section 3 of
#                                          paper/is/paper/BUILD_ENVIRONMENT.md
#                                          -- page count, sizes, SHA-256s,
#                                          error and undefined-reference
#                                          censuses -- from main.pdf,
#                                          main.log, main.tex and main.bbl.
#                                          Run it after every rebuild and
#                                          before packaging.
python build_env_section3.py --check     # fails if the shipped section 3 is
#                                          stale; the release build runs this

# --- fix-forward GPU run (one GPU, ~2.5 h) -------------------------------
python f15_e2_entropy_gn.py              # entropy objective on ResNet-26+GN
#   then re-run f16/f23 and f20/f24 to score its records
python f_scope_bench.py                  # wall-clock scoping only, no results

# --- packaging (not part of any result) ----------------------------------
python make_release_zip.py               # rebuilds and verifies this archive.
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

## The original generators that are still current

Four objects in the manuscript are still produced by the original generators.
They write into `figures/` (the repository-level staging directory), from which
the file is copied to `paper/is/paper/figures/`.  **Both copies ship**, and
`make_release_zip.py` asserts at build time and again inside the extracted
archive that each staging file and its paper copy are byte-identical; the
check is the `staging/paper byte-identity` line of the verify output.  They
import only numpy and matplotlib.

```
cd figures/scripts
python fig_F5.py     # -> figures/F5_batch.pdf      (Fig. 5, E2 batch sweep)
python fig_F6.py     # -> figures/F6_calib.pdf      (Fig. 6, entropy calibration)
python fig_F7.py     # -> figures/F7_imagenet.pdf   (Fig. 7, ImageNet-C)
python tab_T2.py     # -> figures/T2_e3_full.tex    (Table T2, full E3 grid)
cp ../F5_batch.pdf ../F6_calib.pdf ../F7_imagenet.pdf ../T2_e3_full.tex \\
   ../../paper/is/paper/figures/

# printed-only helpers:
python k3_baseline.py     # K=3 fixed-budget baseline on the E3 records
#                         # (quoted in sections/experiments.tex)
python bootstrap_ci.py    # E3 across-seed spreads (quoted); its E2 and E4
#                         # branches are SUPERSEDED and quoted nowhere -- see
#                         # below
#                         # (_style.py is an imported module, no command line)
```

`bootstrap_ci.py` needs a word of warning.  Only its `e3_seed_ranges` branch is
current: it is the record of record for the E3 across-seed spread in
Section 7.3.  Its `e2_cis` branch is a same-sample, cell-level bootstrap
superseded by the `f8`/`f22*` cross-fit with a corruption-clustered bootstrap,
and its `e4_cis` branch resamples the **1500 seed-document rows i.i.d.**, not
the 500 document clusters, which understates the width by the design effect of
roughly 1.54--1.77.  Neither prints a number the manuscript uses.  The E4
intervals the manuscript prints come from `f29_e4_pooled_ci.py` and
`f30_e4_alignment_pooled.py`, which resample documents with the three
adaptation seeds nested and pool five bootstrap streams into one 10,000-draw
distribution; `f29` deliberately reproduces the row bootstrap as its
`naive_iid_rows` baseline, and that comparison is the reason `bootstrap_ci.py`
is kept rather than deleted.
Both superseded branches say so in their own output banners.

`figures/T1_theory_comparison.tex` and `figures/T3_provenance.tex` have no
generator: they are hand-written prose tables, edited directly.

## Superseded generators -- do not run

`figures/scripts/_superseded/` holds `fig_F1.py`, `fig_F2.py`, `fig_F3.py`,
`fig_F4.py`, `fig_F8.py` and `tab_T4.py`.  Each wrote a file with the same
basename as an object that a current generator now produces, from single-seed
or full-sample data, so running them in bulk would have overwritten a current
artifact with a stale one.  They are kept as the audit trail only, have no
command line here, and are not runnable in place (they `import _style`, which
resolves only from `figures/scripts/`).  See
`figures/scripts/_superseded/README.md` for the one-line reason per file.

Each script prints its headline numbers and asserts its own reproduction check;
a non-zero exit status means the check failed.
""".replace("{n_curated}", str(n_curated)).replace(
        "{n_construction}", str(n_construction))


def json_census(files):
    """Count the JSON records that ship, split by where they live.

    A package census once described the archive as holding "446 result JSON
    files".  That conflates the 445 result records under
    `experiments/results/` with the root-level `MANIFEST.json`, which is
    archive metadata and not a result.  The census is computed here rather
    than written by hand so the two numbers can never drift apart again.

    Returns (n_total_json, n_result_json, rows_markdown).
    """
    js = [r for r in files if r.endswith(".json")]
    under = [r for r in js if r.startswith("experiments/results/")]
    by_set = {}
    for r in under:
        parts = r.split("/")
        by_set[parts[2]] = by_set.get(parts[2], 0) + 1
    rows = "\n".join(f"| `experiments/results/{k}/` | {v} |"
                     for k, v in sorted(by_set.items()))
    return len(js), len(under), rows, by_set


def index_md(files, zip_path, generated=None):
    # PATH-HYGIENE PARAGRAPH: generated from the gate's own census, never
    # from a number typed here.  A typed "exactly one declared exception"
    # here stays on the page while the executable gate reports nineteen
    # exception files holding 240 paths: true when written, false when read.
    # Reading the census makes the sentence true by construction at every
    # rebuild.
    #
    # The census covers EVERY ZIP entry, not only the manifested
    # payload.  `generated` carries
    # the seven root entries rendered before this one; INDEX.md itself is the
    # eighth and cannot be in its own census, so it is counted as the one
    # extra clean text member it is and the assertion at the bottom of this
    # function proves that description true of the string actually returned.
    generated = dict(generated or {})
    _rels = list(files) + list(generated)
    _cen = abs_path_census(
        _rels, lambda rel: files[rel], texts=generated)
    assert not _cen["hits"], (
        "index_md refuses to write the path-hygiene paragraph: the census "
        "found absolute paths outside the declared exceptions "
        f"({_cen['hits'][:5]})")
    # INDEX.md is a text member of the archive and must be inside the coverage
    # figures it prints, or the printed census would not be what a re-scan of
    # the extracted tree reports.  It contributes exactly one clean text
    # member; that this is true of the returned string is asserted below.
    _cen["text_files"] += 1
    _cen["n_members"] += 1
    n_unmanifested = len(generated) + 1
    n_entries = _cen["n_members"]
    n_manifested = len(files)
    n_exc_files = _cen["n_exception_files"]
    n_exc_paths = _cen["n_exception_paths"]
    # measured off r9_reconcile.py, never typed -- see curated_claim_counts()
    n_curated, n_construction = curated_claim_counts()
    n_scan_json = _cen["json_files"]
    n_scan_leaves = _cen["json_leaves"]
    n_scan_text = _cen["text_files"]
    n_scan_bin = _cen["binary_files"]
    n_scan_shebang = _cen["shebangs"]
    exc_rows = "\n".join(
        f"| `{r}` | {_cen['exception_hits'].get(r, 0)} |"
        for r in sorted(ABS_PATH_EXCEPTIONS))
    n_by_top = {}
    for rel in files:
        top = "/".join(rel.split("/")[:3])
        n_by_top[top] = n_by_top.get(top, 0) + 1
    rows = "\n".join(f"| `{k}` | {v} |" for k, v in sorted(n_by_top.items()))
    n_json, n_result_json, json_rows, _ = json_census(files)
    # MANIFEST.json is written into the zip after `files` is collected, so it
    # is not in `files`; the archive's total JSON count is therefore one more
    # than the payload count.
    n_json_total = n_json + 1
    json_block = f"""## JSON census

State this precisely, because the two counts differ by exactly one file:

* **{n_json_total} JSON files in the archive in total**;
* **{n_result_json} result JSON files** under `experiments/results/`;
* the remaining one is the root-level `MANIFEST.json`, which is archive
  metadata (path, size, SHA-256 for every payload file), not a result record.

The result records break down as:

| directory | result JSON files |
|---|---|
{json_rows}
| **total** | **{n_result_json}** |

Do not write "{n_json_total} result JSON files"; write
"{n_result_json} result JSON files plus `MANIFEST.json`", or
"{n_json_total} JSON files in total".
"""
    body = f"""# Auditability archive -- index

Built {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} for the
Information Sciences submission "When Does Test-Time Training Provably Help?".
It exists so that the submission is independently auditable rather than
merely re-readable.  Extract it and every path below resolves without
editing.

## What "reproducible" means here, precisely

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
  The E1, E2, E3, E4, calibration and clustering analyses behind the
  manuscript are re-executed this way from the shipped raw JSON, and each
  script asserts its own reproduction check.  No download, no GPU, no
  checkpoint.
  **This is a statement about rerunning the analyses, not a certificate that
  every printed number is machine-verified.**  The reconciliation
  (`r9_reconcile.py`) binds **{n_curated} curated headline and repeated
  numerical claims** to records of record, with {n_construction} further
  construction checks; that curated list is not exhaustive and says so, in
  its own docstring and in `FRESH_RESULTS.md`.  Quantities it does not bind
  --- among them the E3 safety-failure counts and magnitudes, the E3 matched
  K = 3 comparison, the E3 seed-spread summaries, the E2
  leave-one-corruption-out fold intervals, some E2 conditional calibration
  proportions, the two Appendix B analytic thresholds and the printed Monte
  Carlo standard errors --- are recomputable from the shipped records but are
  not asserted by any gate.  This narrowing is deliberate: "every number in
  the manuscript" overstates what the binding establishes.
  **Two scripts in `is_fresh` are NOT part of that set and must be skipped:**
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
  from this ZIP alone.**  It additionally requires the external datasets
  (CIFAR-10/100-C, ImageNet-C-compatible subsets, the four E4 corpora),
  regenerated source checkpoints, generated corruption tensors, GPU
  provisioning, and two distributions (`datasets`, `imagenet_c`) that the
  build interpreter did not carry -- see the commented block at the end of
  `requirements-experiment.txt`.  Checkpoints (`*.pt`) and image/corruption tensors are
  excluded by size, not by omission; the training, data-preparation and
  corruption-generation scripts that produce them all ship.
* **Dependency provisioning is a prerequisite, not a given.**  "Every path
  resolves after extraction" is a statement about paths.  `import torch` must
  succeed even for the pure-numpy re-analyses (see `COMMANDS.md`).

## Path hygiene: the exact, gated statement

The claim, and nothing wider --- **every number in it is written by the gate
itself at build time, not typed into this file**:

> Of the entries of this archive that the gate **reads** --- every JSON
> member, parsed to its string leaves, and every other text member, scanned
> line by line --- none carries a build-machine or run-machine **absolute**
> path *of the syntaxes the gate matches*, except for the
> **{n_exc_files} declared exception files**.  Those files retain
> **{n_exc_paths}** path occurrences between them, each enumerated and
> justified in `paper/is/paper/BUILD_ENVIRONMENT.md` section 6.4 and in the
> `ABS_PATH_EXCEPTIONS` map of `make_release_zip.py`.  Outside them the count
> is **zero**.
>
> Two qualifications are inside that claim, not footnotes to it.  **Binary
> members are out of scope**: the gate counts them and does not read inside
> them, so the claim covers {n_scan_json} + {n_scan_text} of the
> {n_entries} ZIP entries and not the {n_scan_bin} binary ones.  **The POSIX
> recognizer matches a fixed list of machine roots** --- `root`, `home`,
> `mnt`, `media`, `opt`, `usr`, `var`, `tmp`, `Users`, `autodl-tmp`,
> `content`, `workspace` --- and not every leading slash, so a path under an
> unlisted root such as `/data`, `/scratch`, `/project` or `/private` would
> not match.  The Windows branch has no such restriction.
> `BUILD_ENVIRONMENT.md` section 6.4 states both limits in the same words.

The claim covers the {n_manifested} manifested payload files and the
{n_unmanifested} generated root entries alike; what it does *not* cover is
the {n_scan_bin} binary members, which is why they are counted and named.

This claim must not be **wider than its checker**.  A checker that iterated
`MANIFEST.json`, i.e. the manifested payload only, while
`BUILD_ENVIRONMENT.md` section 6.4 and the gate's own header comment
quantify over every file in the ZIP, leaves the eight generated root entries
outside the census -- and one of them, `pip-freeze-full.txt`, holds 268
path-like strings.  The answer is the wider checker, not the narrower
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

Coverage of this build's run, over all **{n_entries}** entries:
**{n_scan_json} JSON members** ({n_scan_leaves}
string leaves **parsed**, not regex-matched); **{n_scan_text} text members**
scanned line by line; {n_scan_bin} binary members out of scope and listed as
such; {n_scan_shebang} portable `env`-style shebangs excluded by construction
(they name no machine).  {n_scan_json} + {n_scan_text} + {n_scan_bin} =
{n_entries}: every entry is in exactly one of the three categories, none is
skipped.  The checker matches the twelve enumerated POSIX machine roots listed
in the claim above, and any Windows drive letter or UNC host/share, so the
scope of the checker is exactly the scope of the claim --- neither wider nor
narrower.

A typed count in this paragraph rots: "exactly one declared exception" stays
on the page while the gate it cites reports nineteen, and the sentence is
true when written and false when read.  The count is interpolated from the
census the gate performs, so it cannot drift from the gate that way.

The declared exceptions of this build, with the number of retained
occurrences in each:

| file | retained paths |
|---|---|
{exc_rows}
| **total** | **{n_exc_paths}** in **{n_exc_files}** files |

The wider statement -- that a repository sweep finds *zero* absolute paths in
the result JSONs -- is **not** made here, because it is **false** of the
unsanitized records: 441 absolute-path fields were present in 214 of the 447
result JSONs as produced, every one of them under the run host's scratch
prefix, together with build-machine paths in 24 analysis logs.  Those fields
were sanitized (the machine prefix replaced by the placeholder `<RUN_ROOT>`,
every other byte and every numeric value unchanged and asserted so with a
parser); the log prefixes were stripped and their emitters fixed so
regeneration cannot reintroduce them; `main.log` was kept verbatim; and the
original remote-host GPU runners and job files were kept verbatim as the
record of what was executed.  Every retained case is enumerated with its
reason in `ABS_PATH_EXCEPTIONS`, printed by the gate, and documented in
`BUILD_ENVIRONMENT.md` section 6.4 together with the proof of
value-preservation.

## Contents

| path | files |
|---|---|
{rows}

{json_block}
## Where each claim comes from

| manuscript object | script | output |
|---|---|---|
| Fig. 1, risk-curve match (numbers) | `f7_curve_match.py` | `f7_curve_match_summary.json` |
| Fig. 1, risk-curve match (figure) | `fig_f1_curves.py` | `paper/is/paper/figures/F1_curves.pdf`, `fig_f1_curves.json` |
| Fig. 2(a) one-step signed gain | `f10_oracle_grid.py` | `f10_oracle_grid_summary.json` |
| Fig. 2(b) measured oracle gain | `f10_oracle_grid.py` | same |
| Fig. 2(c) stopping-selection error | `f10_oracle_grid.py` | same |
| Fig. 3 ALTA vs measured oracle | `f4_alta_measured_oracle.py` | `f4_alta_measured_oracle_summary.json` |
| Fig. 3(c) compute-matched oracle | `f13_compute_matched.py` | `f13_compute_matched_summary.json` |
| Fig. 4 E2 cross-fit correlations | `f22*`/`f23` runs of `f8_e2_crossfit.py`, `f8b_e2_crossfit_det.py`, `f16_e2_gn_analysis.py`; plotted by `fig_f4_e2.py` | `f22_*_summary.json`, `f22b_*_summary.json`, `f22c_*_summary.json`, `f23_e2_gn_summary.json` |
| E2 correlations, PRE-correction audit trail | `f8_e2_crossfit.py`, `f8b_e2_crossfit_det.py`, `f16_e2_gn_analysis.py`, `f20_e2gn_loco_sensitivity.py` at their default prefixes | `f8*`, `f8b*`, `f16*`, `f20*` |
| E2 leave-one-corruption-out, corrected | `f20_e2gn_loco_sensitivity.py --out-name f24_...` | `f24_e2gn_loco_sensitivity.json` |
| E5 learning-rate ablation (sign stability) | `f25_e2_lr_ablation.py` | `f25_e2_lr_ablation.json` |
| E1 reported values, Sec. 5.1 | `f26_e1_reporting_audit.py` | `f26_e1_reporting_audit.json` |
| Table T4 E1 verification gates | `tab_t4_e1_gates.py` | `paper/is/paper/figures/T4_e1_gates.tex` |
| Table T3 ImageNet-C provenance | no generator (hand-written); its evidence is shipped | `results/provenance/<corruption>/<severity>/manifest.json`, `results/e5_gencheck/` |
| E2 batch-variance panel | `f5_batch_variance.py` | `f5_batch_variance_summary.json` |
| E4 per-domain correlations + intervals (SUPERSEDED endpoints, retained audit trail) | `f11_e4_cluster_ci.py` | `f11_e4_cluster_ci.json` |
| E4 per-domain correlations + pooled percentile intervals (CURRENT) | `f29_e4_pooled_ci.py` | `f29_e4_pooled_ci.json` |
| E4 proxy validation, selections and point estimates (SUPERSEDED endpoints, retained audit trail) | `f12_e4_proxy_loo.py` | `f12_e4_proxy_loo.json` |
| E4 proxy validation, pooled percentile intervals and both exclusion counts (CURRENT) | `f31_e4_proxy_pooled.py` | `f31_e4_proxy_pooled.json` |
| Table T6 E4 per-domain proxy details (App. D) | `tab_t6_e4_proxy.py` | `paper/is/paper/figures/T6_e4_proxy.tex` |
| `BUILD_ENVIRONMENT.md` sections 3 and 6.4 (generated) | `build_env_section3.py` | `paper/is/paper/BUILD_ENVIRONMENT.md` |
| delta_feat proxy validation | `f14_deltafeat_check.py` | `f14_deltafeat_check.json` |
| E2 architecture-controlled entropy run | `f15_e2_entropy_gn.py` | `results/is_fresh/e2_gn/` |
| Table T5 E2 objective-vs-architecture contrast | `f16_e2_gn_analysis.py` | `f16_e2_gn_summary.json` |
| Fig. 8 E4 alignment-only panels (SUPERSEDED endpoints, retained audit trail) | `f17_e4_alignment_only.py` | `f17_e4_alignment_only.json` |
| Fig. 8 E4 alignment-only panels (CURRENT) | `f30_e4_alignment_pooled.py`, `fig_f8_domains.py` | `f30_e4_alignment_pooled.json` |
| integer one-step criterion, measured | `f18_integer_boundary_check.py` | `f18_integer_boundary_check.json` |
| E2 leave-one-corruption-out sensitivity | `f20_e2gn_loco_sensitivity.py` | `f20_e2gn_loco_sensitivity.json` |
| E2 entropy sign-separation coverage and excluded group | `f21_e2_coverage.py` | `f21_e2_coverage.json` |
| E2 identity-level overlap of the cross-fit split | `f27_e2_identity.py` | `f27_e2_identity.json` |
| Appendix B (P3) counterexample simulation | `f28_p3_montecarlo.py` | `f28_p3_montecarlo.json` |
| dependency-provenance evidence and resolver transcripts | none (captured once, on the build machine) | `experiments/ttt/is_fresh/RESOLVER_TRANSCRIPT.md` |

## Which defect each fresh artefact answers

Every artefact below exists because of a specific defect in the analysis it
replaces.  The defect is stated, not its provenance.

| defect | artefact |
|---|---|
| the submission was not independently auditable | this archive; `MANIFEST.json`, `SEEDS.md`, `COMMANDS.md` |
| figures foregrounded superseded numbers | `fig_f2_phase.py`, `fig_f3_alta.py`, `fig_f4_e2.py` and their data |
| the ALTA oracle comparator was too weak | `f13_compute_matched.py` |
| Fig. 2 conflated the oracle with the selection error | `f10_oracle_grid.py`, `fig_f2_phase.py` |
| the E2 stochastic/deterministic confound | `f15_e2_entropy_gn.py` (architecture control), `f16_e2_gn_analysis.py` (matched-cell correlations), `f14_deltafeat_check.py` (proxy validation) |
| the E4 intervals were pseudoreplicated | `f11_e4_cluster_ci.py` |
| the E4 proxy was selected and evaluated on the same data | `f12_e4_proxy_loo.py` |
| continuous interpolation was conflated with executable integer steps | `f18_integer_boundary_check.py` |
| Fig. 8 contradicted the corrected E4 result | `f17_e4_alignment_only.py`, `fig_f8_domains.py` |
| the E4 brackets were averaged percentile endpoints while being described as single percentile intervals | `f29_e4_pooled_ci.py`, `f30_e4_alignment_pooled.py`, `r9_reconcile.py` PASS 1b |
| the printed "0 of 4" favourable-side census contradicted `f12`'s own record, which says 1 | `f31_e4_proxy_pooled.py`, the `r9_reconcile.py` bindings of both exclusion counts, and the PASS 1b `.tex` assertions |
| `f12` still averaged endpoints while the documents called the pairs intervals | `f31_e4_proxy_pooled.py` (same remedy as `f29`/`f30`; `f12` retained as the audit trail) |
| `BUILD_ENVIRONMENT.md` section 3 carried one-build-stale sizes and checksums | `build_env_section3.py` (section 3 and the 6.4 census are interpolated from the build products and the gate's census) |
| the absolute-path claim was wider than its manifest-limited checker, and 6.4's census was stale | the gate walks every ZIP entry; `pip-freeze-full.txt` is a declared exception; the census is generated |
| Section 7.4 promised a per-domain proxy table the appendix did not contain | `tab_t6_e4_proxy.py` -> Table T6, App. D |
| one corruption family might have been driving the E2 sign | `f20_e2gn_loco_sensitivity.py` |
| the coverage of the entropy sign separation, and what the excluded episodes look like, were undocumented | `f21_e2_coverage.py` |
| the E2 loss proxy dropped the alignment sign | `f22`, `f22b`, `f22c`, `f23`, `f24` runs (corrected statistic) with `f8*`/`f16*`/`f20*` retained as the pre-correction trail |
| the learning-rate ablation had no script | `f25_e2_lr_ablation.py` |
| ten reporting and number defects in Sec. 5.1 and Table T4 | `f26_e1_reporting_audit.py`, `tab_t4_e1_gates.py` |
| there was no fresh F1 generator; `fig_F1.py` read unarchived seed-42 records | `fig_f1_curves.py` (re-simulates and asserts it replays `f7` cell for cell; needs no record file) |
| stale generators wrote current filenames | `figures/scripts/_superseded/` + its `README.md`; the no-collision gate in `make_release_zip.verify` |
| `COMMANDS.md` omitted F5/F6/F7/T2 and misstated the torch dependency | this archive's `COMMANDS.md` |
| `ENVIRONMENT.txt` carried an unportable `file:///` requirement | `pip-freeze-full.txt` (direct references rewritten to `name==version`) |
| a hand-written package census disagrees with the payload it counts | the JSON census above, computed from the payload rather than written by hand |
| `COMMANDS.md` demanded Python 3.11+ against a 3.10.9 build, and called `ENVIRONMENT.txt` pip-installable when it was not | `BUILD_INTERPRETER.md` + `requirements.txt` + `pip-freeze-full.txt`, replacing `ENVIRONMENT.txt`; version policy stated in both |
| "every script runs unchanged after extraction" is unqualified as stated | the "What reproducible means here" section above |
| Table T3 cited manifests and a sanity check that did not ship | `results/provenance/`, `results/e5_gencheck/` |

## Provenance and honesty notes

* `experiments/results/is_fresh/FRESH_RESULTS.md` is the running audit record.
  It documents which published numbers were analytic, same-sample or
  single-seed, and what replaced them.  Read it before the JSONs.
* The original record sets under `experiments/results/{{e2,e3,e4,e5}}` are the
  raw inputs, shipped unmodified.  Every re-analysis in `is_fresh` reads them;
  none rewrites them.
* Model checkpoints and corrupted-image tensors are NOT included (size); the
  training and data-preparation scripts that produce them are
  (`e2_cifar/train_source.py`, `e2_cifar/data.py`,
  `e3_imagenet/prepare_data.py`, `e4_gpt2/prepare_data.py`).
* Archive: `{os.path.basename(zip_path)}`.
"""
    # INDEX.md counts ITSELF as one clean text member in the coverage figures
    # above (it cannot be inside its own census).  That description must be
    # true of the string this function actually returns, or the printed census
    # would differ from what `--check-paths` reports on the extracted tree.
    # It is the same class of self-reference that has produced a false
    # hygiene claim before, so it is asserted rather than assumed.
    _self_hits = [ln for ln in body.split("\n")
                  if _ABS_PATH_RE.search(ln) and not _SHEBANG_RE.match(ln)]
    assert not _self_hits, (
        "INDEX.md itself carries an absolute path, so the coverage figures it "
        f"prints understate the census: {_self_hits[:3]}")
    return body


def _portable_requirement(line):
    """Rewrite a non-portable pip-freeze line into an installable pin.

    `pip freeze` emits a direct-reference requirement for any distribution that
    was installed from a local path -- conda-forge builds routinely produce
      packaging @ file://<builder-home>/conda/feedstock_root/build_artifacts/..
    which names a directory that exists on no other machine, so the file is not
    usable as an environment lock.  Replace
    such a line with the plain `name==version` pin read back from the installed
    distribution's metadata, and record what was rewritten.

    Returns (line, note_or_None).
    """
    if " @ " not in line:
        return line, None
    name, _, ref = line.partition(" @ ")
    name, ref = name.strip(), ref.strip()
    try:
        from importlib.metadata import version as _version
        ver = _version(name)
    except Exception:                            # pragma: no cover
        ver = None
    if ver:
        return (f"{name}=={ver}",
                f"{name}: rewritten from a non-portable direct reference "
                f"({ref}) to {name}=={ver}")
    return (f"# UNPINNABLE {name} (installed from {ref}; no version metadata)",
            f"{name}: installed from {ref} and exposes no version metadata; "
            f"left commented out rather than shipped as an unusable path")


# The direct third-party imports of the shipped code, grouped by which part
# of the archive needs them.  Derived by walking the AST of every shipped .py
# and subtracting the standard library and the archive's own modules; kept
# here explicitly so the locks are focused files and not a dump of the whole
# build environment.
#
# WHY THE LOCK IS SPLIT IN TWO.  A single
# `requirements.txt` merging these groups is NOT dependency-
# resolvable: it pins numpy==1.23.5 alongside opencv-python==4.12.0.88,
# whose metadata requires numpy>=2 on Python >= 3.9, so
# `pip install -r requirements.txt` terminates in ResolutionImpossible on the
# 3.10.9 build interpreter.  The lock is therefore split in two:
#
#   requirements-analysis.txt    what the CPU re-analysis actually imports.
#                                Verified resolvable by `pip install
#                                --dry-run` in a clean 3.10.9 venv.
#   requirements-experiment.txt  the ORIGINAL GPU experiment environment, as
#                                recorded.  Documented as a build record that
#                                pip cannot reconstruct, with the conflicting
#                                pin named and its conda provenance stated.
#
# The analysis set is closed under the transitive imports of every script in
# experiments/ttt/is_fresh and figures/scripts: numpy and matplotlib
# directly, scipy through e1_synthetic/run_e1.py and analysis/aggregate.py,
# and torch through common.py -> run_e1 -> core.utils.  PIL and torchvision
# appear in is_fresh only as function-local imports inside f15 (which needs
# the unshipped CIFAR tensors) and f_scope_bench (a timing benchmark that
# recomputes no manuscript number), so they belong to the experiment set.
_REQ_ANALYSIS = [
    ("core re-analysis -- needed by every script in "
     "experiments/ttt/is_fresh and by figures/scripts",
     ["numpy", "matplotlib"]),
    ("torch is a HARD dependency of the CPU-only re-analyses too: "
     "is_fresh/common.py imports run_e1, which imports core.utils, which "
     "does `import torch` at module scope.  See COMMANDS.md.",
     ["torch"]),
    ("scipy reaches the re-analysis transitively through "
     "e1_synthetic/run_e1.py and analysis/aggregate.py",
     ["scipy"]),
]

_REQ_EXPERIMENT = [
    ("shared with the analysis lock -- pinned again here so this file stands "
     "alone as a record of the experiment environment",
     ["numpy", "scipy", "matplotlib", "torch"]),
    ("original GPU experiment runners under experiments/ttt/{e2_cifar,"
     "e3_imagenet,e4_gpt2}, plus the two function-local imports in "
     "is_fresh/f15_e2_entropy_gn.py (Pillow) and is_fresh/f_scope_bench.py "
     "(torchvision) -- NOT needed to recompute any manuscript number from "
     "the shipped records",
     ["torchvision", "transformers", "tokenizers", "safetensors",
      "huggingface-hub", "Pillow", "scikit-image", "opencv-python",
      "pandas", "tqdm", "requests", "filelock", "fsspec"]),
]

# Needed by the original data-preparation scripts but absent from the build
# interpreter, because the corrupted-image and corpus tensors were prepared
# on separate GPU machines.  Listed unpinned and commented so the file stays
# installable and the omission is not mistaken for an oversight.
_REQ_UNPINNED = [
    ("datasets", "experiments/ttt/e4_gpt2/prepare_data.py (corpus download)"),
    ("imagenet_c", "experiments/ttt/e3_imagenet/prepare_data.py "
                   "(corruption generation)"),
]


def _installed_pins():
    """{canonical-lowercase name: 'name==version'} from a portable pip freeze."""
    try:
        out = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                             capture_output=True, text=True, timeout=180)
        raw = out.stdout.splitlines()
    except Exception:                            # pragma: no cover
        return {}, [], "(pip freeze unavailable)"
    pins, notes = {}, []
    ordered = []
    for ln in raw:
        s = ln.rstrip()
        if not s:
            continue
        fixed, note = _portable_requirement(s)
        ordered.append(fixed)
        if note:
            notes.append(note)
        if fixed.startswith("#"):
            continue
        name = fixed.split("==")[0].strip()
        pins[name.lower().replace("_", "-")] = fixed
    return pins, notes, ordered


def build_interpreter_md():
    """Build metadata.  NOT a requirements file -- see requirements-analysis.txt.

    The old ENVIRONMENT.txt opened with two uncommented
    non-requirement lines (`python ...`, `platform ...`), so
    `pip install -r ENVIRONMENT.txt` failed on line 1 even though COMMANDS.md
    called it installable.  The metadata now lives here and the pins live in
    a file that pip can actually read.
    """
    import platform as _p
    # `sys.version` on Anaconda builds contains literal `|` characters, which
    # would break the Markdown table row it is printed in.
    pyver = sys.version.replace("|", "\\|")
    try:
        import torch as _t
        torch_line = (f"| PyTorch | `{_t.__version__}` |\n"
                      f"| CUDA available at build time | "
                      f"`{bool(_t.cuda.is_available())}` |\n"
                      f"| CUDA runtime linked into PyTorch | "
                      f"`{_t.version.cuda}` |")
    except Exception as e:                       # pragma: no cover
        torch_line = f"| PyTorch | not importable at build time ({e}) |"
    return f"""# Build interpreter and machine

Metadata for the interpreter that built this archive.  **This file is not a
requirements file**; the installable pins are in `requirements-analysis.txt`,
the original GPU experiment environment is recorded in
`requirements-experiment.txt`, and the complete freeze of the build
environment is in `pip-freeze-full.txt`.

| field | value |
|---|---|
| Python | `{pyver}` |
| `sys.platform` | `{sys.platform}` |
| platform | `{_p.platform()}` |
| machine | `{_p.machine()}` |
| processor | `{_p.processor() or 'n/a'}` |
{torch_line}

## Python version policy

**Python {_p.python_version()} is tested.  Other versions are untested.**

The archive was built and all shipped analyses were run on Python
{_p.python_version()}; that is the interpreter the pins in
`requirements-analysis.txt` were taken from, and it is the only one on which
that lock has been resolved and the analyses exercised.

Two weaker statements of this policy are not supportable and are not made
anywhere in this archive.  "Python 3.11+" contradicts the recorded
build interpreter above.  "3.9 through 3.12, given the same third-party
versions" is false on the pins
themselves: `scipy==1.15.3` declares `Requires-Python >= 3.10`, so 3.9 is
excluded outright, and `numpy==1.23.5` publishes no wheel for 3.12.  It is
true that the analysis code uses no syntax or standard-library feature newer
than Python 3.9 (no `match` statements, no `tomllib`, no PEP 604 `X | Y`
annotations evaluated at runtime, no `itertools.batched`), but source-level
compatibility is not interpreter compatibility once the pins are fixed.
Supporting a range would require a resolvable lock demonstrated on each
interpreter in it, and we have not built one.

## The LaTeX side

The TeX toolchain is pinned separately in
`paper/is/paper/BUILD_ENVIRONMENT.md`, which ships in this archive.
"""


def _emit_pins(groups, pins):
    """Render `# comment` + `name==version` blocks; return (lines, missing)."""
    out, missing = [], []
    for comment, names in groups:
        out.append(f"# {comment}")
        for n in names:
            key = n.lower().replace("_", "-")
            if key in pins:
                out.append(pins[key])
            else:                                # pragma: no cover
                missing.append(n)
                out.append(f"# {n}  (not installed in the build interpreter)")
        out.append("")
    return out, missing


def requirements_analysis_txt():
    """The resolvable lock: everything the CPU re-analysis actually imports.

    This replaced a former single `requirements.txt`, which pinned
    numpy==1.23.5 and opencv-python==4.12.0.88 together and therefore had no
    pip solution on any Python >= 3.9.
    """
    pins, _, _ = _installed_pins()
    out = [
        "# Dependency lock for RECOMPUTING THE MANUSCRIPT NUMBERS.",
        "#",
        "#     python -m pip install -r requirements-analysis.txt",
        "#",
        "# This is the file to install.  It contains exactly the",
        "# distributions that the CPU re-analysis imports, directly or",
        "# transitively: the CPU re-analysis, reconciliation and",
        "# figure-generation commands of COMMANDS.md -- every script in",
        "# experiments/ttt/is_fresh and figures/scripts EXCEPT the two",
        "# GPU-requiring ones -- run with these and nothing else.  It is",
        "# dependency-resolvable: `pip install --dry-run -r` against a clean",
        "# Python 3.10.9 virtual environment resolves it with no conflict.",
        "#",
        "# THE TWO EXCEPTIONS, which these pins do NOT cover and which the",
        "# no-GPU rerun must skip:",
        "#   is_fresh/f15_e2_entropy_gn.py  trains and samples on a GPU;",
        "#                                  function-local Pillow and",
        "#                                  torchvision; needs CUDA and the",
        "#                                  unshipped CIFAR tensors.  Its",
        "#                                  records ship, and f16 recomputes",
        "#                                  the matched-architecture numbers",
        "#                                  from them on CPU.",
        "#   is_fresh/f_scope_bench.py      wall-clock scoping only; imports",
        "#                                  torchvision, requires CUDA,",
        "#                                  recomputes no manuscript number.",
        "# Both are listed under the fix-forward GPU section of COMMANDS.md,",
        "# and their extra distributions are pinned in",
        "# requirements-experiment.txt.",
        "#",
        "# Every line below is a comment or a plain `name==version` pin, so",
        "# pip accepts the file as supplied.  Interpreter, OS and hardware",
        "# metadata are in BUILD_INTERPRETER.md.  The dependencies of the",
        "# ORIGINAL GPU experiments -- which recompute no manuscript number",
        "# and which pip cannot reconstruct -- are in",
        "# requirements-experiment.txt, and the complete freeze of the build",
        "# machine is in pip-freeze-full.txt.",
        "#",
        "# Versions are those of the build interpreter recorded in",
        "# BUILD_INTERPRETER.md.  Nothing here is platform-specific except",
        "# the PyTorch wheel, which pip resolves per platform.",
        "#",
        "# NOTE ON PYTHON.  These pins were taken from, and are tested on,",
        "# Python 3.10.9 only.  Other interpreter versions are UNTESTED: in",
        "# particular scipy 1.15.3 declares Requires-Python >= 3.10, which",
        "# excludes 3.9, and numpy 1.23.5 publishes no wheel for 3.12.",
        "",
    ]
    body, missing = _emit_pins(_REQ_ANALYSIS, pins)
    out += body
    if missing:                                  # pragma: no cover
        out.append(f"# NOTE: {len(missing)} expected distribution(s) were not "
                   f"found in the build interpreter: {', '.join(missing)}")
        out.append("")
    return "\n".join(out)


def requirements_experiment_txt():
    """The ORIGINAL GPU experiment environment, as recorded.

    Deliberately NOT advertised as installable: the recorded set has no pip
    solution, and saying so precisely is more useful than shipping a lock
    that fails at the first `pip install`.
    """
    pins, _, _ = _installed_pins()
    out = [
        "# Recorded dependency set of the ORIGINAL GPU EXPERIMENTS.",
        "#",
        "# READ THIS BEFORE RUNNING pip.  This file is a RECORD of the",
        "# environment in which the CIFAR-10/100-C, ImageNet-C and GPT-2",
        "# experiments were executed.  It is NOT a lock that pip can",
        "# reconstruct, and `pip install -r requirements-experiment.txt`",
        "# is EXPECTED TO FAIL with ResolutionImpossible.  To recompute the",
        "# manuscript numbers you do not need this file at all -- install",
        "# requirements-analysis.txt instead.",
        "#",
        "# WHY IT DOES NOT RESOLVE.  The recorded environment contains",
        "# numpy 1.23.5 and opencv-python 4.12.0.88 simultaneously, and the",
        "# metadata of that OpenCV release requires numpy >= 2 on any Python",
        "# >= 3.9.  WHICH INSTALLER WROTE WHICH TARGET, as recorded by the",
        "# installer metadata: numpy 1.23.5 was installed by conda into the",
        "# Anaconda prefix (INSTALLER=conda, and a conda-meta/history",
        "# transaction); opencv-python 4.12.0.88 was installed by pip",
        "# into the PER-USER site directory (INSTALLER=pip), which pip",
        "# treats as a separate installation target.  This is a statement",
        "# about installer and location only -- the metadata does NOT",
        "# record installation ORDER, so no claim is made that either was",
        "# installed before or after the other.  The interpreter",
        "# imports numpy from the prefix and cv2 from the user site, so an",
        "# environment no single pip resolution would produce can and does",
        "# exist on disk.  pip-freeze-full.txt therefore lists a",
        "# combination pip will not install; that is a property of the",
        "# machine, not a transcription error.  The evidence is archived in",
        "# experiments/ttt/is_fresh/RESOLVER_TRANSCRIPT.md, which also",
        "# records why this is a property of the on-disk installation",
        "# layout and not of conda's own solver.",
        "#",
        "# A RESOLVABLE APPROXIMATION.  Substituting",
        "# opencv-python==4.9.0.80 -- a tested release whose metadata is",
        "# compatible with the pinned numpy 1.23.5 -- makes the whole set",
        "# below resolve on Python 3.10.9, verified with",
        "# `pip install --dry-run` in a clean virtual environment; the",
        "# transcript is in RESOLVER_TRANSCRIPT.md section 2.",
        "#",
        "# SCOPE OF THAT EVIDENCE.  The transcript establishes exactly one",
        "# thing: that the set resolves with this pin and does not resolve",
        "# with 4.12.0.88.  It tests no other release, so nothing here",
        "# claims that 4.9.0.80 is the LAST, the newest or the only",
        "# opencv-python release whose metadata accepts numpy 1.x.  A",
        "# superlative such as \"the last release whose metadata accepts",
        "# numpy 1.x\" is not supported by the archived evidence and is",
        "# therefore not stated.",
        "# Establishing it would require a",
        "# release-by-release metadata sweep, which is not performed and",
        "# is not needed: any pin that resolves is sufficient here.",
        "#",
        "# OpenCV is used only by",
        "# experiments/ttt/e3_imagenet/generate_imagenet_c.py, for corruption",
        "# generation, and no manuscript number depends on the OpenCV",
        "# version.  We record the version that actually ran rather than",
        "# silently substituting one that installs.",
        "#",
        "# ADDITIONAL PREREQUISITES, none of which pip provides:",
        "#   * an NVIDIA GPU with a CUDA runtime matching the torch build;",
        "#     the archive was assembled on a CPU-only interpreter, so the",
        "#     torch pin below is the CPU wheel and the experiments were run",
        "#     with the corresponding CUDA build on separate machines;",
        "#   * the external datasets: CIFAR-10-C and CIFAR-100-C, an",
        "#     ImageNet-C-compatible validation subset, and the four E4",
        "#     corpora (code, legal, PubMed, WikiText);",
        "#   * regenerated source checkpoints (*.pt) and generated corruption",
        "#     tensors, both excluded from this archive by size; the training,",
        "#     data-preparation and corruption-generation scripts that produce",
        "#     them all ship.",
        "",
    ]
    body, missing = _emit_pins(_REQ_EXPERIMENT, pins)
    out += body
    out += [
        "# --------------------------------------------------------------",
        "# Needed only by the original data-preparation scripts, and NOT",
        "# installed in the build interpreter: the corrupted-image and",
        "# corpus tensors were prepared on separate GPU machines, and those",
        "# tensors are excluded from this archive by size.  No manuscript",
        "# number is recomputed from them.  Left commented out rather than",
        "# pinned to a version this build never saw.",
        "# --------------------------------------------------------------",
    ]
    for n, why in _REQ_UNPINNED:
        out.append(f"# {n}    # {why}")
    out.append("")
    if missing:                                  # pragma: no cover
        out.append(f"# NOTE: {len(missing)} expected distribution(s) were not "
                   f"found in the build interpreter: {', '.join(missing)}")
        out.append("")
    return "\n".join(out)


def pip_freeze_full_txt():
    """The complete build-environment freeze, still pip-parseable."""
    _, notes, ordered = _installed_pins()
    if isinstance(ordered, str):                 # pragma: no cover
        return f"# {ordered}\n"
    head = [
        "# Complete `pip freeze` of the interpreter that built this archive.",
        "#",
        "# This is the exact build record, not a recommended install: it is a",
        "# Windows/Anaconda environment and most of it is unrelated to this",
        "# project.  For running the analyses use",
        "# `requirements-analysis.txt`.",
        "#",
        "# It is nevertheless valid `pip install -r` input: every line is a",
        "# comment or a plain name==version pin.  pip emits a direct",
        "# reference (`name @ file:///...`) for any distribution installed",
        "# from a local path, naming a directory that exists on no other",
        "# machine; every such line has been rewritten to the plain",
        "# name==version pin read back from the installed distribution's",
        "# metadata.",
    ]
    if notes:
        head.append("#")
        head.append("# rewritten:")
        head += [f"#   {n}" for n in notes]
    else:
        head.append("# (no line needed rewriting in this build)")
    head.append("")
    return "\n".join(head + ordered) + "\n"


def build(zip_path):
    files = collect()
    manifest = {"built_utc": datetime.now(timezone.utc).isoformat(),
                "repo_relative_paths": True, "files": {}}
    total = 0
    for rel, full in files.items():
        size = os.path.getsize(full)
        total += size
        manifest["files"][rel] = {"bytes": size, "sha256": sha256(full)}
    manifest["n_files"] = len(files)
    manifest["total_bytes_uncompressed"] = total

    # The eight generated root entries are rendered FIRST, so the path-hygiene
    # census inside index_md() can cover them.  They were once outside the
    # census while the claim quantified over the whole ZIP; they are scanned
    # from these strings at build time and from the extracted tree at check
    # time, and both routes must agree.
    generated = {
        "MANIFEST.json": json.dumps(manifest, indent=1, sort_keys=True),
        "SEEDS.md": SEEDS_MD,
        "COMMANDS.md": commands_md(),
        "BUILD_INTERPRETER.md": build_interpreter_md(),
        "requirements-analysis.txt": requirements_analysis_txt(),
        "requirements-experiment.txt": requirements_experiment_txt(),
        "pip-freeze-full.txt": pip_freeze_full_txt(),
    }
    index = index_md(files, zip_path, generated)
    generated["INDEX.md"] = index

    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for rel, full in files.items():
            z.write(full, rel)
        for rel, body in generated.items():
            z.writestr(rel, body)
    return manifest


_SAVE_RE = re.compile(r"""st\.save\(\s*fig\s*,\s*["']([^"']+)["']""")
_OUT_RE = re.compile(r"""OUT_DEFAULT\s*=\s*\[?[^\n]*?/\s*["']([^"']+\.(?:pdf|tex))["']""")
_WRITE_RE = re.compile(r"""FIGDIR\s*/\s*["']([^"']+\.(?:tex|pdf))["']""")


def _figure_outputs(tree):
    """Map basename -> [generators that write it], over both generator sets."""
    out = {}

    def add(name, who):
        out.setdefault(name, []).append(who)

    legacy = os.path.join(tree, "figures", "scripts")
    if os.path.isdir(legacy):
        for fn in sorted(os.listdir(legacy)):
            if not fn.endswith(".py"):
                continue
            src = open(os.path.join(legacy, fn), encoding="utf-8",
                       errors="replace").read()
            for m in _SAVE_RE.finditer(src):
                add(m.group(1) + ".pdf", f"figures/scripts/{fn}")
            for m in _WRITE_RE.finditer(src):
                add(m.group(1), f"figures/scripts/{fn}")

    fresh = os.path.join(tree, "experiments", "ttt", "is_fresh")
    for fn in sorted(os.listdir(fresh)):
        if not fn.endswith(".py"):
            continue
        src = open(os.path.join(fresh, fn), encoding="utf-8",
                   errors="replace").read()
        for m in _OUT_RE.finditer(src):
            add(m.group(1), f"experiments/ttt/is_fresh/{fn}")
    return out


def check_no_output_collisions(tree):
    """No two live generators may write the same output basename.

    `figures/scripts` once held the original generators for F1-F4, F8 and T4,
    each writing the basename that a current `is_fresh` generator writes, from
    single-seed or full-sample data.  A reader running the directory in bulk
    would have silently replaced a current artifact with a stale one.  They
    now live under
    `figures/scripts/_superseded/`, which this gate keeps empty of live
    duplicates -- and which is excluded from the scan precisely because nothing
    there is meant to run.
    """
    sup = os.path.join(tree, "figures", "scripts", "_superseded")
    assert os.path.isdir(sup), (
        "figures/scripts/_superseded/ is missing; the original generators for "
        "F1-F4, F8 and T4 must stay quarantined")
    assert os.path.exists(os.path.join(sup, "README.md")), (
        "figures/scripts/_superseded/README.md is missing; a quarantine "
        "without a stated reason is not a quarantine")
    outs = _figure_outputs(tree)
    clashes = {k: v for k, v in outs.items() if len(v) > 1}
    assert not clashes, (
        "two live generators write the same output basename: "
        + "; ".join(f"{k} <- {v}" for k, v in sorted(clashes.items())))
    print(f"[release] no-collision gate OK ({len(outs)} distinct figure/table "
          f"outputs, {sum(len(v) for v in outs.values())} generators, "
          f"0 shared basenames)")
    return outs


# --------------------------------------------------------------------------
# ABSOLUTE-PATH GATE
#
# THE CLAIM this gate certifies, stated first so the checker can be matched
# to it:
#
#   "No textual or parsed-JSON member of this archive -- EVERY ZIP ENTRY, not
#    only the manifested payload -- carries a build-machine or run-machine
#    ABSOLUTE path OUTSIDE the files declared in ABS_PATH_EXCEPTIONS below.
#    Those files retain their paths deliberately, each for the reason recorded
#    against it in that map and each enumerated in BUILD_ENVIRONMENT.md
#    section 6.4."
#
# WHY THE CHECKER WALKS EVERY ENTRY.  A manifest-driven checker is narrower
# than this comment, BUILD_ENVIRONMENT.md 6.4 and the module docstring, which
# all quantify over every file in the ZIP.  MANIFEST.json lists the payload
# only, so the eight root-level generated entries -- BUILD_INTERPRETER.md, COMMANDS.md,
# INDEX.md, MANIFEST.json, SEEDS.md, pip-freeze-full.txt and the two
# requirements files -- were outside the census, and one of them,
# pip-freeze-full.txt, holds 268 path-like strings: three artefacts then
# disagreed about the scope.  The fix is the wider checker, not the narrower
# sentence: the gate walks EVERY entry, the generated root members are censused
# from
# their in-memory text at build time and from the extracted tree at check
# time, and pip-freeze-full.txt is a DECLARED exception with its reason
# recorded like every other.
#
# HOW MANY EXCEPTIONS, AND HOW MANY PATHS.  Deliberately not written down
# here.  The exception set is exactly `ABS_PATH_EXCEPTIONS`, and the number
# of retained occurrences is whatever the gate counts in this build; both are
# printed by the gate and both are interpolated into the generated INDEX.md
# from the gate's own census (see `abs_path_census` and `index_md`).  This
# comment, the INDEX.md template and the module docstring once all still said
# "exactly one declared exception" long after the map had grown to nineteen --
# a hand-maintained count is a claim that rots, so no hand-maintained count
# survives here.
#
# SCOPE.  The claim quantifies over EVERY shipped file, so the gate walks
# every entry of the archive -- the manifested payloads AND the eight
# generated root entries -- not a sampled subset, and not one operating
# system's path syntax.  A "zero absolute paths" claim whose checker is a
# Windows-only regular expression over a subset does not support a universal
# claim, and a manifest-limited checker is the same mismatch in a narrower
# form.
#
# METHOD.  Text-shaped members are read; JSON members are PARSED and every
# string LEAF of the resulting tree is tested, so a path is caught wherever it
# sits in the structure -- nested dicts, lists, argv arrays -- and no
# assumption is made about key names, indentation or line breaking.  Non-JSON
# text members are scanned line by line.  Binary members (PDF, PNG, .pt) are
# out of scope and are listed as such rather than silently skipped.
#
# PATTERN.  Both syntaxes, and both directions of slash:
#   * POSIX absolute roots that identify a machine -- the twelve names in
#     `_MACHINE_ROOTS` below, each anchored to a leading slash;
#   * Windows drive-letter absolute paths (a drive letter, a colon and a
#     separator) and UNC host/share paths.
# Repository-relative paths (experiments/..., paper/...) are not absolute and
# are the intended form.
#
# NOTE ON THIS FILE'S OWN TEXT.  The gate scans every shipped text member, and
# this module is one of them.  Every pattern fragment that would otherwise
# match is therefore assembled at import time from parts, and the prose above
# describes the syntaxes in words instead of spelling them out.  Writing them
# as literals would have forced an exemption for the gate's own source -- and
# an exempted checker is exactly the hole that makes a hygiene claim
# unverifiable.

# The drive-letter branch carries a lookbehind: without it the tails of
# `https:` + separator, `arXiv:` + backslash and `gate_pass:` + backslash all
# match as drive letters.  A real Windows path is never preceded by an
# alphanumeric character.
_MACHINE_ROOTS = ("root", "home", "mnt", "media", "opt", "usr", "var", "tmp",
                  "Users", "autodl-tmp", "content", "workspace")
_SEP = r"[\\/]"
_ABS_PATH_RE = re.compile(
    r"(?:(?<![A-Za-z0-9])[A-Za-z]:" + _SEP                # drive-letter form
    + r"|\\\\[^\\/\s]+\\[^\\/\s]"                         # UNC host and share
    + r"|/(?:" + "|".join(_MACHINE_ROOTS) + r")(?:/|\b))")

# The portable shebang -- `#!` then a slash then usr/bin/env then a name -- is
# NOT a machine path: it names no machine and resolves everywhere POSIX.  It is
# excluded by construction, and the pattern is likewise assembled from parts.
_SHEBANG_RE = re.compile(r"^#!\s*/" + "usr/bin/env" + r"\s")

# DECLARED EXCEPTIONS, each with the reason it is not sanitized.  The gate
# asserts that every file outside this map is clean AND that every file inside
# it still ships, so the list cannot silently rot into a blanket amnesty.
ABS_PATH_EXCEPTIONS = {
    "paper/is/paper/main.log":
        "verbatim pdflatex transcript; the '0 errors / 0 undefined / N "
        "pages' rows of BUILD_ENVIRONMENT.md section 3 are statements about "
        "THIS file and are read out of it by build_env_section3.py, so "
        "editing it would falsify it as a build record (MiKTeX and "
        "user-profile paths)",
    "paper/is/paper/BUILD_ENVIRONMENT.md":
        "the document whose PURPOSE is to record the reference build machine; "
        "it must name the TEXMF root, and section 6.4 discloses every "
        "exception in this map",
    # The original remote-host GPU experiment code and job files.  These ship
    # UNMODIFIED as the record of what was executed: `jobs_*.txt` are the
    # literal command lines that ran, and the argparse defaults are the
    # configuration the result records' meta/argv reproduce.  Rewriting them
    # would make the shipped script differ from the executed one, which is a
    # worse defect than disclosing that the run host kept its data under
    # its scratch prefix.  No analysis in this archive executes them.
    "experiments/ttt/e2_cifar/adapt_cifar.py": "original GPU runner, as run",
    "experiments/ttt/e2_cifar/delta_feat.py": "original GPU runner, as run",
    "experiments/ttt/e2_cifar/train_source.py": "original GPU runner, as run",
    "experiments/ttt/e2_cifar/train_recon_head.py":
        "original GPU runner, as run",
    "experiments/ttt/e3_imagenet/run_e3.py": "original GPU runner, as run",
    "experiments/ttt/e3_imagenet/prepare_data.py":
        "original GPU runner, as run",
    "experiments/ttt/e3_imagenet/generate_imagenet_c.py":
        "original GPU runner, as run",
    "experiments/ttt/e3_imagenet/SMOKE.md":
        "remote-host smoke transcript, as run",
    "experiments/ttt/e3_imagenet/jobs_e3.txt":
        "literal command lines executed on the run host",
    "experiments/ttt/e3_imagenet/jobs_e3gen.txt":
        "literal command lines executed on the run host",
    "experiments/ttt/e3_imagenet/jobs_e3gen_gpu0.txt":
        "literal command lines executed on the run host",
    "experiments/ttt/e3_imagenet/jobs_e3gen_gpu1.txt":
        "literal command lines executed on the run host",
    "experiments/ttt/e4_gpt2/run_e4.py": "original GPU runner, as run",
    "experiments/ttt/e4_gpt2/prepare_data.py": "original GPU runner, as run",
    "experiments/ttt/e4_gpt2/delta_proxy_v2.py":
        "original GPU runner, as run",
    "experiments/ttt/e4_gpt2/SMOKE.md":
        "remote-host smoke transcript, as run",
    "experiments/ttt/e4_gpt2/jobs_e4.txt":
        "literal command lines executed on the run host",
    # Generated root entry, inside the census like every other.
    # `pip freeze --all` output is a
    # PROVENANCE RECORD of the build interpreter, and the paths ARE the
    # record: the conda-prefix and user-site locations of each distribution
    # are what distinguishes the mixed installation this archive documents
    # from a clean one.  Rewriting them would destroy the evidence
    # RESOLVER_TRANSCRIPT.md section 3 reasons about.  The installable pins
    # live in requirements-analysis.txt and requirements-experiment.txt,
    # which are clean; nothing installs from this file.
    "pip-freeze-full.txt":
        "verbatim `pip freeze --all` provenance record of the build "
        "interpreter; the conda-prefix and user-site paths ARE the evidence "
        "of the mixed installation, and the installable pins are in the two "
        "requirements files instead",
}

_BINARY_EXT = (".pdf", ".png", ".jpg", ".pt", ".zip", ".ttf", ".otf",
               ".pyc", ".npz", ".npy")


def _json_string_leaves(obj, ptr=""):
    """Yield (json_pointer, string) for every string leaf of a parsed tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _json_string_leaves(v, ptr + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _json_string_leaves(v, ptr + "/" + str(i))
    elif isinstance(obj, str):
        yield ptr, obj


def abs_path_census(rels, pathfor, texts=None):
    """Scan `rels` for absolute paths; return the raw census, assert nothing.

    `pathfor(rel) -> filesystem path`.  This is the single implementation of
    the sweep: `check_no_absolute_paths` wraps it with the gate's assertions
    and printout, and `index_md` calls it so the archive's own hygiene
    paragraph is written FROM the census rather than from a hand-kept number.
    INDEX.md once claimed "exactly one declared exception" against a gate
    reporting nineteen; a generated sentence cannot drift from the gate that
    way.

    `texts` is an optional `{rel: str}` of members that exist only in memory.
    The eight generated root entries (COMMANDS.md, SEEDS.md, MANIFEST.json,
    the two requirements files, pip-freeze-full.txt, BUILD_INTERPRETER.md and
    INDEX.md) are written straight into the ZIP by `build()` and have no file
    on disk at that moment, so at BUILD time they are censused from their
    strings and at CHECK time from the extracted tree.  Both routes visit the
    same bytes and report the same census; they were once outside the scan
    entirely, which is why they are explicitly in it now.
    Members named in `texts` are scanned instead of, not in addition to,
    `pathfor(rel)`, and `rels` must contain them.
    """
    texts = texts or {}
    hits = []
    n_json = n_text = n_binary = n_shebang = 0
    n_json_leaves = 0
    exc_hits = collections.Counter()
    for rel in sorted(rels):
        excepted = rel in ABS_PATH_EXCEPTIONS
        if rel.lower().endswith(_BINARY_EXT):
            n_binary += 1
            continue
        if rel in texts:
            body = texts[rel]
        else:
            with open(pathfor(rel), encoding="utf-8",
                      errors="replace") as fh:
                body = fh.read()
        if rel.lower().endswith(".json"):
            n_json += 1
            obj = json.loads(body)           # PARSER, not regex
            for ptr, s in _json_string_leaves(obj):
                n_json_leaves += 1
                if _ABS_PATH_RE.search(s):
                    (exc_hits.__setitem__(rel, exc_hits[rel] + 1) if excepted
                     else hits.append((rel, ptr, s[:120])))
        else:
            n_text += 1
            for ln, line in enumerate(body.split("\n"), 1):
                if _SHEBANG_RE.match(line):
                    n_shebang += 1
                    continue
                if _ABS_PATH_RE.search(line):
                    if excepted:
                        exc_hits[rel] += 1
                    else:
                        hits.append((rel, f"line {ln}",
                                     line.strip()[:120]))
    return {"hits": hits, "json_files": n_json, "json_leaves": n_json_leaves,
            "text_files": n_text, "binary_files": n_binary,
            "shebangs": n_shebang, "exception_hits": dict(exc_hits),
            "n_exception_files": len(ABS_PATH_EXCEPTIONS),
            "n_exception_paths": sum(exc_hits.values()),
            "n_members": len(set(rels))}


def walk_tree(tree_root):
    """Every file in an extracted archive, as sorted repo-relative POSIX."""
    out = []
    for dirpath, _dirnames, filenames in os.walk(tree_root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            out.append(os.path.relpath(p, tree_root).replace(os.sep, "/"))
    return sorted(out)


def check_no_absolute_paths(tree_root, manifest):
    """Fail unless the claim quoted above holds over EVERY archive entry.

    Iterating `manifest["files"]` would cover the payload only, while the
    claim this certifies quantifies over the whole ZIP.  It walks the
    extracted tree instead, so the eight generated root entries are inside the
    scope of the sentence that describes it.
    """
    rels = walk_tree(tree_root)
    unmanifested = [r for r in rels if r not in manifest["files"]]
    cen = abs_path_census(
        rels,
        lambda rel: os.path.join(tree_root, rel.replace("/", os.sep)))
    cen["n_manifested"] = len(manifest["files"])
    cen["n_unmanifested"] = len(unmanifested)
    cen["unmanifested"] = unmanifested
    hits = cen["hits"]
    n_json, n_json_leaves = cen["json_files"], cen["json_leaves"]
    n_text, n_binary = cen["text_files"], cen["binary_files"]
    n_shebang = cen["shebangs"]
    exc_hits = collections.Counter(cen["exception_hits"])
    assert not hits, (
        "absolute-path gate FAILED; the archive's hygiene claim is false.\n"
        + "\n".join(f"  {r}  {w}  {s}" for r, w, s in hits[:20])
        + (f"\n  ... and {len(hits) - 20} more" if len(hits) > 20 else ""))
    # The exception list must not rot: every declared exception must still
    # ship, and (except for main.log, whose content the build controls) must
    # still be the reason it was declared -- i.e. still carry a path.  A
    # declared exception that no longer needs to be one is removed, not kept.
    missing = [r for r in ABS_PATH_EXCEPTIONS if r not in set(rels)]
    assert not missing, (
        f"declared absolute-path exceptions no longer ship: {missing}; "
        f"remove them from ABS_PATH_EXCEPTIONS")
    stale = [r for r in ABS_PATH_EXCEPTIONS if exc_hits[r] == 0]
    assert not stale, (
        f"declared absolute-path exceptions are now clean and the exemption "
        f"is unnecessary: {stale}; remove them from ABS_PATH_EXCEPTIONS so "
        f"the exemption list stays exactly as wide as the facts")
    print(f"[release] absolute-path gate OK: 0 absolute paths outside the "
          f"declared exceptions, over {n_json} JSON members "
          f"({n_json_leaves} string leaves parsed) and {n_text} text members; "
          f"{n_binary} binary members out of scope, {n_shebang} "
          f"portable shebangs excluded by construction")
    print(f"[release]   scope: ALL {cen['n_members']} archive entries "
          f"({cen['n_manifested']} manifested payloads + "
          f"{cen['n_unmanifested']} generated root entries: "
          f"{', '.join(unmanifested)})")
    print(f"[release]   {len(ABS_PATH_EXCEPTIONS)} declared exceptions, "
          f"{sum(exc_hits.values())} paths in them, each documented in "
          f"BUILD_ENVIRONMENT.md 6.4:")
    for r in sorted(ABS_PATH_EXCEPTIONS):
        print(f"[release]     {exc_hits[r]:4d}  {r}  -- "
              f"{ABS_PATH_EXCEPTIONS[r]}")
    return {k: v for k, v in cen.items() if k != "hits"}


def verify(zip_path, python=sys.executable):
    """Extract to a scratch dir and run eight reproduction checks.

    The eight, in the order they run (the three read-only ones first,
    deliberately): `tab_t4_e1_gates.py --check`, `tab_t6_e4_proxy.py --check`,
    `build_env_section3.py --check`, then `f7_curve_match.py`,
    `f11_e4_cluster_ci.py`, `f29_e4_pooled_ci.py`, `f31_e4_proxy_pooled.py`
    and `f8b_e2_crossfit_det.py`, the last five at
    reduced parameters and each writing under a `verify_*` name.  See
    VERIFICATION item 6 in the module docstring.

    This docstring's own count has been a recurring defect: it has said "two
    reproduction checks" while running four, and "five" while listing more.
    It is checked against `len(checks)` at the bottom of this function, so it
    cannot be wrong silently again.
    """
    tmp = tempfile.mkdtemp(prefix="is_release_verify_")
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            z.extractall(tmp)
        # manifest round-trip
        man = json.loads(open(os.path.join(tmp, "MANIFEST.json"),
                              encoding="utf-8").read())
        bad = []
        for rel, info in man["files"].items():
            p = os.path.join(tmp, rel.replace("/", os.sep))
            if not os.path.exists(p):
                bad.append((rel, "missing"))
            elif sha256(p) != info["sha256"]:
                bad.append((rel, "hash mismatch"))
        assert not bad, f"manifest round-trip failed for {bad[:5]}"
        print(f"[release] manifest round-trip OK "
              f"({len(man['files'])} files, {len(names)} zip entries)")

        # STAGING-COPY IDENTITY GATE.  COMMANDS.md says the repository-level
        # staging file and the paper copy "are byte-identical in this
        # archive".  Check that inside the extracted tree, so the sentence is
        # verified by the reader's own copy rather than asserted.
        for rel in STAGING_FILES:
            a = os.path.join(tmp, rel.replace("/", os.sep))
            b = os.path.join(tmp, "paper", "is", "paper",
                             rel.replace("/", os.sep))
            assert os.path.exists(a), f"{rel} did not ship"
            assert os.path.exists(b), f"paper copy of {rel} did not ship"
            assert sha256(a) == sha256(b), (
                f"{rel} and its paper copy are not byte-identical in the "
                f"archive")
        print(f"[release] staging/paper byte-identity OK for all "
              f"{len(STAGING_FILES)} original generator outputs")

        wd = os.path.join(tmp, "experiments", "ttt", "is_fresh")

        # COMMANDS.md must account for every script that ships, or the claim
        # "the exact command line for every script" is false.  An omission
        # of four scripts is invisible to a reader of either document, so
        # this makes the claim self-enforcing rather than a promise.
        cmds = open(os.path.join(tmp, "COMMANDS.md"), encoding="utf-8").read()
        scripts = sorted(f for f in os.listdir(wd) if f.endswith(".py"))
        missing = [f for f in scripts if f not in cmds]
        assert not missing, (
            f"COMMANDS.md does not mention {missing}; either add the command "
            f"or document why the file has none")
        print(f"[release] COMMANDS.md accounts for all {len(scripts)} "
              f"is_fresh scripts")

        # DUPLICATE-LINE GATE.  A generated document that repeats a line --
        # a duplicated "CONSTRUCTION checks" comment line, say -- has usually
        # had a block pasted twice, and the repetition is easy to read past.
        # Rather than inspect for it once, assert it.
        #
        # SCOPE, chosen so the gate has no false positives.  It covers the two
        # kinds of line that MUST be unique: the command lines themselves --
        # the same command listed twice is either a paste error or an
        # ambiguous instruction -- and the `# --- section ---` headers.  It
        # deliberately does NOT cover wrapped comment continuations: two
        # scripts that do parallel things are described in parallel prose, and
        # a shared continuation fragment there is correct rather than
        # duplicated.  A gate that fired on those would be noise, and a noisy
        # gate gets disabled.
        _lines = [ln.rstrip() for ln in cmds.split("\n")]
        _unique = [ln for ln in _lines
                   if ln.startswith("python ")
                   or (ln.startswith("# ---") and ln.rstrip().endswith("-"))]
        _dups = {k: v for k, v in collections.Counter(_unique).items()
                 if v > 1}
        assert not _dups, (
            "COMMANDS.md repeats a command line or a section header, which is "
            "the signature of a block pasted twice: "
            + "; ".join(f"{v}x {k.strip()[:70]!r}" for k, v in
                        sorted(_dups.items())[:5]))
        print(f"[release] COMMANDS.md duplicate-line gate OK "
              f"({len(_unique)} command lines and section headers, "
              f"0 repeated)")

        check_no_output_collisions(tmp)

        # Absolute-path gate, run on the EXTRACTED tree so it tests exactly
        # what a reader receives.
        check_no_absolute_paths(tmp, man)

        # NOTE ON ORDER AND OUTPUT NAMES.  Every check below runs at reduced
        # parameters, so none of them may write to a name the manuscript
        # reads: letting the reduced f7 run overwrite
        # f7_curve_match_summary.json inside the extracted tree makes the T4
        # check compare the table against 4,000-replicate numbers.
        # Each write therefore goes to a `verify_*` name, and the read-only
        # T4 check runs first regardless.
        checks = [
            ("table regeneration (T4 --check against the shipped .tex)",
             [python, "tab_t4_e1_gates.py", "--check"]),
            # T6 is the per-domain E4 proxy table Section 7.4 promises, so
            # the appendix has to contain it.  Its caption carries the
            # favourable-side and adverse-side exclusion counts, so this
            # check also binds the "1 of 4" census against the record that
            # a "0 of 4" summary would contradict.
            ("table regeneration (T6 --check against the shipped .tex)",
             [python, "tab_t6_e4_proxy.py", "--check"]),
            # BUILD_ENVIRONMENT.md section 3 is interpolated from main.pdf,
            # main.log, main.tex and main.bbl.  It has carried a
            # one-build-stale size and checksum for two of them; this check
            # makes that state unpackageable.
            ("generated BUILD_ENVIRONMENT.md section 3 (--check)",
             [python, "build_env_section3.py", "--check"]),
            ("code-only reproduction (f7 risk-curve gate)",
             [python, "f7_curve_match.py", "--n-rep", "4000",
              "--seeds", "20260806", "--out-prefix", "verify_f7"]),
            ("data reproduction (f11 published-CI check)",
             [python, "f11_e4_cluster_ci.py", "--b", "200",
              "--boot-seeds", "20260806",
              "--out-name", "verify_f11_e4_cluster_ci.json"]),
            # the CURRENT E4 interval generator, exercised on the pooled path.
            # --no-audit because a 200-draw single-stream run cannot and must
            # not be compared with the archived 10,000-draw record; the point
            # of this check is that the script runs and its own reproduction
            # assertion holds inside the extracted tree.
            ("pooled E4 intervals (f29 percentile construction)",
             [python, "f29_e4_pooled_ci.py", "--b", "200",
              "--boot-seeds", "20260806", "--no-audit",
              "--out-name", "verify_f29_e4_pooled_ci.json"]),
            # the CURRENT E4 PROXY interval generator, same reasoning as f29.
            ("pooled E4 proxy intervals (f31 percentile construction)",
             [python, "f31_e4_proxy_pooled.py", "--b", "200",
              "--boot-seeds", "20260806", "--no-audit",
              "--out-name", "verify_f31_e4_proxy_pooled.json"]),
            ("corrected E2 statistic (f8b signed re-analysis)",
             [python, "f8b_e2_crossfit_det.py", "--statistic", "phase_loss",
              "--n-boot", "100", "--seeds", "20260806",
              "--out-prefix", "verify_f8b"]),
        ]
        # The count in this function's docstring is a hand-typed number about
        # this list, which is exactly the class of claim that rots.  Bind it.
        _n_words = {5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
        assert f"run {_n_words.get(len(checks), len(checks))} reproduction " \
               f"checks" in verify.__doc__, (
            f"verify()'s docstring does not say it runs {len(checks)} "
            f"reproduction checks, but it runs {len(checks)}")
        for label, cmd in checks:
            r = subprocess.run(cmd, cwd=wd, capture_output=True, text=True,
                               timeout=1800)
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-6:])
            assert r.returncode == 0, (
                f"{label} FAILED inside the extracted archive:\n{tail}")
            print(f"[release] {label}: OK")
            for line in tail.splitlines():
                print(f"           {line}")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--check-paths", metavar="TREE", default=None,
                    help="run ONLY the absolute-path gate against an already "
                         "extracted archive TREE (the directory containing "
                         "MANIFEST.json); writes nothing")
    args = ap.parse_args()

    if args.check_paths:
        root = os.path.abspath(args.check_paths)
        man = json.loads(open(os.path.join(root, "MANIFEST.json"),
                              encoding="utf-8").read())
        check_no_absolute_paths(root, man)
        print("[release] absolute-path gate VERIFIED")
        return

    man = build(args.out)
    size = os.path.getsize(args.out)
    print(f"[release] wrote {args.out}")
    print(f"[release] {man['n_files']} files, "
          f"{man['total_bytes_uncompressed']/1e6:.1f} MB uncompressed -> "
          f"{size/1e6:.1f} MB zipped")
    if not args.no_verify:
        verify(args.out)
        print("[release] VERIFIED")


if __name__ == "__main__":
    # QUARANTINE GUARD.  This file is the frozen paper/is/ submission's
    # packager.  Its exception map is for that package layout, so running it
    # against the package this submission ships produces failures that are
    # artefacts of the mismatch -- a stale duplicate reporting a false
    # negative about a claim that is in fact true.  A banner in a docstring
    # is read only by someone who already opened the file; the command line
    # is where the mistake is actually made, so it is closed here.  Importing
    # the module is unaffected: build_env_section3.py of this same frozen
    # pair imports it, and that import still works.
    sys.stderr.write(
        "experiments/ttt/is_fresh/make_release_zip.py is SUPERSEDED.\n"
        "It packages and verifies the FROZEN paper/is/ submission, and its\n"
        "path-exception map is for that package layout; against the package\n"
        "this submission ships it fails for that reason and for no other.\n"
        "\n"
        "The packager and the absolute-path gate of this submission are:\n"
        "    python paper/is2/tools/make_release_zip.py\n"
        "    python paper/is2/tools/make_release_zip.py --check-paths .\n"
        "\n"
        "Set TTT_RUN_FROZEN_PACKAGER=1 to run this file anyway.\n")
    if os.environ.get("TTT_RUN_FROZEN_PACKAGER") != "1":
        sys.exit(2)
    main()
