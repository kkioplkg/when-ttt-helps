"""Build (and verify) the auditability archive  paper/is2/release_archive.zip.

WHY THIS SCRIPT EXISTS
----------------------
A submission is not independently auditable while its referenced code, raw
outputs, per-run records, configurations, generated figures, bibliography and
build dependencies are absent: numerical checking is then limited to
consistency between two authored narratives.

The remedy is a self-contained archive that lets a reader recompute, not just
re-read.  This script assembles one, preserving repository-relative paths so
that no script inside it needs its paths edited after extraction -- which is
NOT the same as "runs unchanged", and the difference has to be stated rather
than left to be inferred: the re-analyses that produce every number either
document prints run from the shipped records once `requirements-analysis.txt`
is installed, whereas the ORIGINAL model experiments additionally need a GPU,
the external datasets, and regenerated checkpoints and corruption tensors, all
of which are deliberately excluded by size.  This script then VERIFIES the
result by extracting it to a scratch directory and executing the reproduction
checks listed in `verify()` inside the extracted tree.

THIS IS THE `is2` PACKAGER, AND THE SUBMISSION IS TWO DOCUMENTS.  The frozen
`paper/is/` tree has its own copy of this script and its own archive, and
neither is touched from here.  The differences that matter are stated once,
here, rather than left to be discovered by diffing:

  * the payload carries BOTH documents -- `paper/is2/paper` (the article) and
    `paper/is2/supplement` (the Supplementary Material) -- with both PDFs,
    both build transcripts and both compiled bibliographies;
  * it also carries `paper/is2/tools`, because a reader is told to run
    `gates.sh`, `r9_reconcile.py` and `tab_s4_e1_gates.py --check`, and a
    document that names a command it does not ship is an unhonoured promise;
  * records that support ONLY material this submission does not contain are
    NOT in the payload.  `DROPPED_PAYLOAD` enumerates them with a reason each
    and `INDEX.md` prints that map, so the omission is a stated decision.
    Nothing is lost: the frozen tree remains their complete home of record;
  * it carries `paper/is2/provenance`, the four dependency-provenance records
    of the interpreter that produced the numbers.  They are a VERBATIM copy of
    the frozen tree's four root entries and are read from that directory, not
    from the frozen archive: a packager that had to open `paper/is/
    release_archive.zip` could not be run from a clean extraction of its own
    release, which is the defect that directory closes.  See
    `provenance_entries()`;
  * the figure and table artefacts of the 79-page build that neither document
    includes are excluded by `PAPER_EXCLUDE`.  The E4 per-domain figure is no
    longer among them -- see `D6_REQUIRED` -- and its PRESENCE is now asserted
    twice, over the payload and over the finished archive.

WHAT GOES IN
  code/            the fresh analysis suite (experiments/ttt/is_fresh) plus the
                   original pipeline modules it imports and the original
                   experiment runners the records came from:
                     experiments/ttt/{core,e1_synthetic,e2_cifar,e4_gpt2,
                                      analysis}
                     figures/scripts  (the generators still current for F5 and
                                      F6, plus _superseded/, the quarantined
                                      original generators)
                     paper/is2/tools  (build drivers, the manuscript gate
                                      suite, the two-document reconciliation,
                                      the Table S4 generator, the
                                      BUILD_ENVIRONMENT generator, and this
                                      script)
  results/         experiments/results/is_fresh (every fresh JSON + logs,
                   less the two measurement sets of the retrospective selector) and
                   the
                   ORIGINAL record sets the fresh analyses consume:
                     results/m0/*.json            E2 SOURCE-MODEL evaluation
                                                  records: the primary
                                                  per-epoch/final clean-test
                                                  accuracy of every source
                                                  model the supplement's
                                                  clean-accuracy paragraph
                                                  reports.  They ship so that
                                                  that paragraph has a
                                                  primary retained record and
                                                  not only a downstream audit
                                                  echo; the CHECKPOINTS those
                                                  runs wrote are still out of
                                                  the payload for size, which
                                                  DROPPED_PAYLOAD and INDEX.md
                                                  state.
                     results/e2/*_main_*.json     E2 episode records
                     results/e4/*.json            E4 GPT-2 per-document records
                     results/e5/*.json            delta_feat, delta_v2 and the
                                                  ablation records
  paper/           BOTH documents as of build time: sources, figures the
                   documents include, references.bib, Highlights.txt, the
                   pinned BUILD_ENVIRONMENT.md, plus the built main.pdf and
                   supplement.pdf, their .log transcripts (the package load
                   lists BUILD_ENVIRONMENT.md greps) and their compiled .bbl
                   files, so the BibTeX-free rebuild BUILD_ENVIRONMENT.md
                   section 1 documents works for each document from THIS
                   archive and not only from the review package
  MANIFEST.json    every PAYLOAD file with its size and SHA-256.  Read that
                   word: it covers the files collected from the repository,
                   NOT every entry of the ZIP.  The generated root entries
                   beside it are produced by this script at package time and
                   are not listed in it.  This line must not be abbreviated to
                   "every file": MANIFEST.json covers the payload, the ZIP
                   holds more than the payload, and the distinction is the
                   whole reason the word is there.
  GENERATED_MANIFEST.json
                   THE OTHER HALF OF THE AUDIT BOUNDARY, so that the boundary
                   is machine-checkable rather than merely disclosed.  It
                   carries the size and SHA-256 of every generated root entry
                   -- MANIFEST.json, SEEDS.md, COMMANDS.md, AUDIT_MAP.json,
                   the four dependency-provenance entries and INDEX.md.  The
                   two manifests together cover every ZIP entry except
                   GENERATED_MANIFEST.json itself, which no manifest can hash
                   from inside and which is authenticated, as before, by the
                   SHA-256 of the whole ZIP published in the review manifest.
                   Both manifests are generated; neither is typed.
  AUDIT_MAP.json   the machine-readable map from a printed manuscript value to
                   the record file it comes from and the command that
                   regenerates that record.  Derived from `r9_reconcile.py`'s
                   curated claim table and from the command lines in
                   COMMANDS.md -- not hand-written -- and therefore PARTIAL in
                   exactly the way that table is partial.  It says so in its
                   own `scope` field and reports its own coverage.
  SEEDS.md         the seed manifest: which seeds each stage used and why the
                   fresh range is disjoint from the original one
  COMMANDS.md      the exact command line for every script, in dependency
                   order, plus the table of shipped scripts that are NOT part
                   of this submission
  BUILD_INTERPRETER.md  interpreter, platform, machine, CUDA -- metadata only
  requirements-analysis.txt    the resolvable lock for ANALYSIS REPRODUCTION
                        -- recomputing the printed numbers FROM THE SHIPPED
                        RECORDS; verified with `pip install --dry-run` in a
                        clean Python 3.10.9 venv.  It is NOT sufficient for
                        ORIGINAL EXPERIMENTAL REGENERATION, which no
                        requirements file can be: that additionally needs the
                        external datasets, the tokenizer and model weights,
                        regenerated checkpoints and corruption tensors, and a
                        GPU.  `external_inputs()` enumerates them from the
                        shipped code and records, and both COMMANDS.md and
                        INDEX.md print that enumeration
  requirements-experiment.txt  the ORIGINAL GPU experiment environment as
                        recorded, documented as a build record pip cannot
                        reconstruct
  pip-freeze-full.txt   the complete build-environment freeze, also parseable
  INDEX.md         what each artefact is, which claim it supports, which
                   defect it answers, and what is deliberately absent

EXCLUDED ON PURPOSE (and why -- stated so the omission is not mistaken for an
oversight): model checkpoints (*.pt) and raw image/corruption tensors, which
are large and reconstructible from the public datasets plus the shipped
training scripts; the working directories of superseded analysis rounds, which
are not inputs to any number in either document; and everything in
`DROPPED_PAYLOAD` and `PAPER_EXCLUDE`, which is evidence for material this
submission does not contain.

VERIFICATION.  IT RUNS BY DEFAULT.  There is no `--verify` switch and there
never was one: `python make_release_zip.py --out <path>` builds AND verifies,
and the only override is `--no-verify`, which turns verification off.  Any
sentence in this package that names a `--verify` flag is wrong; the flag to
look for is its negation.  The steps, in order:
  1. extract the archive to a scratch directory;
  2. re-hash every payload against MANIFEST.json;
  3. staging/paper byte-identity for the two original-generator outputs;
  4. the D6 inclusion, over the finished archive's own member list;
  5. COMMANDS.md must name every script that ships in is_fresh, and must
     repeat no command line or section header;
  6. NO-COLLISION gate: no generator left in figures/scripts, in
     experiments/ttt/is_fresh or in paper/is2/tools may write a file whose
     basename another current generator also writes.  The original generators
     that did are quarantined under figures/scripts/_superseded/ with a
     README, are excluded from COMMANDS.md, and are not runnable in place.
     The is2 tools are in scope because three of the fragments the documents
     typeset are generated there, each superseding an is_fresh generator that
     produces the frozen tree's differently shaped table;
  7. ABSOLUTE-PATH gate: no shipped text or parsed-JSON member may carry a
     build- or run-machine absolute path OUTSIDE the files enumerated in
     ABS_PATH_EXCEPTIONS, each with its stated reason in that map and each
     disclosed in BUILD_ENVIRONMENT.md 6.4.  The gate itself prints the
     exception-file and path-occurrence counts and is the authority on them;
     no prose in this file or in the generated INDEX.md restates them from
     memory.  Binary members are out of scope and are counted, not scanned;
     the POSIX branch matches the enumerated machine roots rather than every
     leading slash (BUILD_ENVIRONMENT.md 6.4 states both limits).  The checker
     walks EVERY manifest file, PARSES each JSON member and tests every string
     leaf of the parsed tree, and scans every non-JSON text member line by
     line; it matches both POSIX machine roots and Windows/UNC drive paths.
     The scope of the checker is the scope of the claim.  A "zero absolute
     paths" statement whose sweep is a Windows-only regex over a subset of
     files does not support a universal claim;
  8. inside the extracted tree, run the reproduction checks listed in
     `verify()`, whose count is asserted against that list.  The three
     `--check` checks are read-only; the rest run at REDUCED parameters, so
     every one of them that writes does so under a `verify_*` name, and the
     read-only checks run first: otherwise the reduced f7 run overwrites
     f7_curve_match_summary.json and the table check then scores the document
     against 4,000-replicate numbers.

     WHAT A REDUCED RUN DOES AND DOES NOT ESTABLISH.  The bootstrap checks
     run at B = 200 draws from ONE RNG stream, against published endpoints
     built from 5 x B = 2000 draws pooled into 10,000.  They are CODE-PATH
     checks: they prove that the shipped records feed the shipped generator,
     that it runs to completion inside the extracted tree, and that its own
     internal assertions hold at reduced draws.  They are NOT a reproduction
     of the published endpoints, and no statement anywhere in this package may
     be read as claiming they are.  A full replay is a separate, longer
     operation: run the same scripts at their published parameters -- the
     command lines in COMMANDS.md, with no --b and no --boot-seeds override
     and without --no-audit -- which rebuilds each interval from all five
     streams and, under --audit, asserts the result against the archived
     record.  In order:
       tools/tab_s4_e1_gates.py --check
         (regenerates supplement Table S4 from the shipped five-seed
         summaries and the f26 audit and asserts the result is BYTE-identical
         to the shipped .tex) -- proves the surviving gate table is generated,
         not hand-maintained, which is exactly what it had become;
       tools/tab_s7_e4_proxy.py --check
         (the same, for supplement Table S7 -- the per-domain E4 proxy table
         and the exclusion counts in its caption);
       tools/build_env_section3.py --check
         (the generated blocks of BUILD_ENVIRONMENT.md against BOTH documents'
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
         documents print.  --no-audit because a 200-draw single-stream run
         must NOT be compared with the archived 10,000-draw record; the point
         of the check is that the generator of the printed endpoints runs in
         the extracted tree, not that it reproduces them here);
       f31_e4_proxy_pooled.py --b 200 --boot-seeds 20260806 --no-audit
         --out-name verify_f31_e4_proxy_pooled.json
         (the CURRENT E4 PROXY interval generator, same reasoning as f29);
       f8b_e2_crossfit_det.py --statistic phase_loss --n-boot 100
         --seeds 20260806 --out-prefix verify_f8b
         (the corrected signed E2 statistic recomputed from the shipped
         episode records; it asserts internally that the retained unsigned
         numerator still reproduces the pre-correction values, which localises
         the sign fix) -- proves the E2 re-analysis is self-contained.
  Every script asserts internally, so a non-zero exit is a failed audit.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))      # paper/is2/tools
IS2 = os.path.dirname(HERE)                            # paper/is2
REPO = os.path.dirname(os.path.dirname(IS2))           # repository root
OUT_DEFAULT = os.path.join(REPO, "paper", "is2", "release_archive.zip")
PAPER_REL = "paper/is2/paper"
SUPP_REL = "paper/is2/supplement"

# THE PINNED BUILD/VERIFY INTERPRETER, as one value rather than as a string
# repeated through the documentation.  Everything that records the pin is
# produced by RUNNING an interpreter, so a build under the wrong one would
# rewrite the pin instead of failing against it; build_interpreter_md()
# asserts against this tuple to make that impossible.
PINNED_PYTHON = (3, 10, 9)
PINNED_PYTHON_STR = ".".join(map(str, PINNED_PYTHON))

CODE_DIRS = [
    "experiments/ttt/is_fresh",
    "experiments/ttt/core",
    "experiments/ttt/e1_synthetic",
    "experiments/ttt/e2_cifar",
    "experiments/ttt/e4_gpt2",
    "experiments/ttt/analysis",
    "figures/scripts",
    # The is2 build, gate and generator tools.  A reader is told to run
    # `tools/gates.sh`, `tools/r9_reconcile.py` and
    # `tools/tab_s4_e1_gates.py --check`, so they have to be inside the
    # archive that documents them.
    "paper/is2/tools",
    # THE THEORY-CLOSURE SUITE'S OWN CODE.  It lives beside its records rather
    # than under experiments/ttt/, because the suite was run as one
    # self-contained job and its measurement, analysis and verification
    # scripts are the record of what produced the jsons next to them.  It is
    # named HERE and not in RESULT_DIRS because the results whitelist admits
    # only .json/.md/.log/.txt/.npz, which would have dropped every .py and
    # .sh in it -- silently, since a walk that finds nothing raises nothing.
    "experiments/results/is_fresh/closure/code",
    # THE DEPENDENCY-PROVENANCE RECORDS, as ordinary files.  They must be in
    # the PAYLOAD -- not only at the ZIP root -- because `make_release_zip.py`
    # reads them from this directory, and a packager that ships inside the
    # archive while its inputs do not cannot be run from that archive.  This
    # is the entry that makes the release self-rebuilding; see
    # `provenance_entries()` and the assertion at the end of `collect()`.
    "paper/is2/provenance",
]
RESULT_DIRS = [
    "experiments/results/is_fresh",
    # THE SOURCE-MODEL EVALUATION RECORDS.  The supplement prints clean test
    # accuracies for the four (dataset, architecture) source models.  Until
    # this entry those figures had no primary retained record in the payload:
    # the only released trace of them was a downstream audit JSON repeating
    # the same values, which is repetition and not evidence.  These twelve
    # records are what the training runs themselves emitted -- per-epoch
    # history, final clean test accuracy, the commissioning gate outcome --
    # so the paragraph is now reconstructible from a record rather than from
    # an echo, and `r9_reconcile.py` binds each printed range to them.  The
    # checkpoints those runs wrote remain out of the payload for size; that
    # exclusion is stated, and it is a different claim from this one.
    "experiments/results/m0",
    "experiments/results/e2",
    "experiments/results/e4",
    "experiments/results/e5",
]

# WHAT LEFT THE PAYLOAD WITH THE MATERIAL IT SUPPORTED, AND WHERE IT LIVES
# NOW.  This submission reports E1, E2 and E3 (the last being the GPT-2 study,
# whose records keep their historical e4 paths).  The ImageNet-C experiment and
# the label-free retrospective selector are not part of it, so their records
# are not
# evidence for anything either document says, and an auditability archive
# whose contents do not map onto the claims it audits is harder to check, not
# easier.  They are not deleted anywhere: the frozen `paper/is/` tree and its
# own `release_archive.zip` remain their home and remain complete.  This map
# is printed into INDEX.md, so the omission is a stated decision rather than
# something a reader has to notice.
DROPPED_PAYLOAD = {
    "experiments/results/e3/":
        "ImageNet-C per-cell records; the experiment they belong to is not "
        "reported in this submission.  NB the article's E3 is the GPT-2 "
        "suite under experiments/results/e4/, not this directory",
    "experiments/results/provenance/":
        "per-(corruption, severity) ImageNet-C image manifests; they were "
        "cited by a provenance table that is not in this submission",
    "experiments/results/e5_gencheck/":
        "generated-vs-downloaded corruption sanity check, cited by the same "
        "provenance table",
    "experiments/ttt/e3_imagenet/":
        "the ImageNet-C experiment runner, for the same reason as its records",
    "experiments/results/is_fresh/f4_*, f13_*":
        "the two fresh measurement sets of the label-free RETROSPECTIVE "
        "SELECTOR (a rule applied after the fact to per-step measurements, "
        "not an online stopping time); the selector is disclosed in the "
        "discussion as developed-but-not-claimed and "
        "is not a contribution here, so its measurements support nothing in "
        "either document",
    "experiments/results/is_fresh/closure/REVIEW_R*.md":
        "the two adversarial design-audit transcripts the theory-closure "
        "suite's DESIGN.md was revised against. They are process records, not "
        "measurement records, and a package meant to be read cold does not "
        "carry another audit's transcript -- the same rule that keeps every "
        "editorial-history file out of both packages, and the "
        "leak gate enforces it. What they forced is not lost: DESIGN.md's "
        "changelog states every change either audit produced, which is the "
        "part that bears on the measurements",
    # THE ONE EXCLUSION THAT IS A SIZE DECISION RATHER THAN A RELEVANCE ONE.
    "experiments/results/is_fresh/closure/records/*.jsonl.gz":
        "the theory-closure suite's 71 raw per-episode record files, 127 MB. "
        "They are held in the side archive closure_records.zip, whose "
        "per-member manifest (size, sha256 of the stored file, sha256 of the "
        "decompressed bytes, record count) ships in this archive at "
        "experiments/results/is_fresh/closure/CLOSURE_RECORDS_MANIFEST.json. "
        "The split is by size and by content, not by relevance: every number "
        "printed in either document is bound to an analysis json under "
        "closure/json/, which ships here in full, as do the independent "
        "verifier's report and the suite's measurement, analysis and "
        "verification code. The records are needed only to RE-DERIVE those "
        "jsons from scratch. Obtaining the side archive lets a reader verify "
        "it member by member; this manifest proves neither possession nor "
        "correctness of an archive a reader does not have",
}
# The record-level half of the map above, as a prefix test over repo-relative
# paths.  Prefixes, not globs, so a new seed file cannot slip in under a name
# the glob did not anticipate.
RESULT_EXCLUDE_PREFIXES = (
    "experiments/results/is_fresh/f4_alta_measured_oracle",
    "experiments/results/is_fresh/f4.log",
    "experiments/results/is_fresh/f13_compute_matched",
    "experiments/results/is_fresh/f13.log",
    "experiments/results/is_fresh/closure/REVIEW_R",
)

ARCH_REL = "paper/is2/archive_tables"
# THE MATERIAL THAT LEFT THE SUPPLEMENT FOR THIS ARCHIVE.  Exhaustive grids,
# gate/audit outputs, provenance ledgers and the local-PL proofs were moved out
# of the Supplementary Material and into the release, verbatim, with pointers
# from the supplement.  They must therefore actually BE in the release: a
# pointer to a path the archive does not carry is worse than the text it
# replaced.  `tools/r9_reconcile.py` scans this directory as its `archive`
# location class, so the numbers in it stay bound to their records.
PAPER_DIRS = [PAPER_REL, SUPP_REL, ARCH_REL]
# FIGURE FILES THAT NEITHER DOCUMENT INCLUDES.  `paper/is2/paper/figures/`
# still holds the artefacts of the 79-page build; \includegraphics and \input
# in the two documents name five PDFs and two .tex tables and nothing else.
# Shipping the rest would put objects in the package that the submission does
# not contain, and one of them would be worse than untidy -- see D6 below.
PAPER_EXCLUDE = {
    "figures/F3_alta.pdf":
        "figure of the label-free retrospective selector; not in either "
        "document",
    "figures/F7_imagenet.pdf":
        "ImageNet-C figure; not in either document",
    # D6 IS GONE FROM THIS MAP.  figures/F8_domains.pdf was excluded here
    # because its y-axis label named the selection rule, which an earlier
    # revision declined to name.  The submission now names and specifies that
    # rule in full (supplement S7.3) and the label was made neutral, so the
    # exclusion had no remaining basis and withholding the figure would itself
    # be the defect.  It is NOT typeset by either document: it is an optional
    # release visualization that the supplement describes as such and points
    # at.  `D6_REQUIRED` asserts its PRESENCE over both the payload and the
    # finished archive, so the pointer resolves.
    "figures/T1_theory_comparison.tex":
        "prior-theory comparison table; replaced by prose in section 2",
    # NOTE: this "e3" is the WITHDRAWN ImageNet-C suite.  The submission
    # now numbers its three suites E1, E2, E3, and its E3 is the GPT-2
    # study whose records live under experiments/results/e4/.  No
    # ImageNet-C record ships, so the two never meet inside an archive.
    "figures/T2_e3_full.tex":
        "full ImageNet-C grid (the withdrawn suite); not in either document",
    "figures/T3_provenance.tex":
        "ImageNet-C provenance table; not in either document",
    "figures/F1_curves.png":
        "raster twin of F1_curves.pdf; the build consumes the PDF",
    "figures/F4_e2_phase.png":
        "raster twin of F4_e2_phase.pdf; the build consumes the PDF",
}
# D6, REVERSED.  This basename was previously forbidden in every is2 package
# because one of the figure's axis labels named the selection rule, which that
# revision of the submission declined to name.  The submission now names and
# fully specifies the rule (supplement S7.3), so the disclosure reason is void;
# the label was additionally made neutral ("CE gain at the selected stop") and
# the figure ships as an optional release visualization, which the supplement
# describes as such and points at rather than typesetting.  Withholding a
# scientifically relevant figure for a reason that no longer applies would be
# the defect, so the gate is inverted rather than deleted: the file must now be
# PRESENT in every package, asserted over the payload and over the archive.
D6_REQUIRED = "F8_domains.pdf"
# Directories under the paper trees that are archives of a build this tree no
# longer performs.
PAPER_SKIP_DIRS = {"_superseded"}
# The four objects still produced by the original generators -- reduced to the
# two whose outputs this submission still includes (main Figures 4 and 5).
# Those generators write into `figures/` (the repository-level staging
# directory) and the file is then copied into `paper/is2/paper/figures/`.
# COMMANDS.md states that the two copies are byte-identical *in this archive*,
# so both copies must ship and the identity must be machine-checked.
# `verify()` asserts the identity.
STAGING_FILES = ["figures/F5_batch.pdf", "figures/F6_calib.pdf"]

# --------------------------------------------------------------------------
# AUTHOR-DRAWN MECHANISM FIGURES -- A THIRD ARTEFACT CLASS.
#
# Every other figure and table this submission typesets is a MEASUREMENT
# artefact: a generator reads a record file and writes a PDF or a `.tex`
# fragment, and the reader-facing guarantee is that re-running the generator
# reproduces the shipped bytes.  `check_no_output_collisions` and the artefact
# table of BUILD_ENVIRONMENT.md section 5 are both built on that guarantee.
#
# Main Figures 1-3 are not of that kind.  They are SCHEMATICS DRAWN BY THE
# AUTHORS -- vector artwork whose source of record is the `.svg` below, not a
# script and not a record file.  They plot no measurement, and the two things
# that follow from that are asserted rather than assumed:
#
#   (1) NO GENERATOR MAY CLAIM THEM.  There is no script to re-run, so the
#       no-collision gate must not silently treat their absence from the
#       generator map as an oversight -- and, more importantly, a future
#       generator that started writing one of these basenames would be
#       overwriting author artwork with a plot.  `check_no_output_collisions`
#       now asserts that no live generator writes any of these three names.
#
#   (2) THE SOURCE SHIPS.  A vector PDF is a derived artefact like any other,
#       so the archive carries the `.svg` it was converted from, at the path
#       it occupies in the repository.  BUILD_ENVIRONMENT.md section 5 records
#       the conversion route, which is the analogue here of a generator
#       command.  The three files total roughly 210 kB.
#
# WHAT DOES NOT SHIP, AND WHY.  `paper/mechanism_figures/README.md` -- the
# delivery note that accompanied the artwork -- is deliberately NOT in this
# list.  It is a working document about the drawing process, it describes an
# earlier raster pipeline that the delivered vector files supersede, and its
# prose is written in the review-process vocabulary that the leak gate exists
# to keep out of anything a reader receives.  The record that ships is the
# artefact table and the conversion note in BUILD_ENVIRONMENT.md section 5,
# which is the same place every other artefact's provenance is written down.
MECHFIG_DIR_REL = "paper/mechanism_figures"
MECHFIG_SOURCES = {
    # source of record (repo-relative)   ->  the PDF it is converted to
    f"{MECHFIG_DIR_REL}/1.svg": "fig_mech_1_phase_law.pdf",
    f"{MECHFIG_DIR_REL}/2.svg": "fig_mech_2_information_boundary.pdf",
    f"{MECHFIG_DIR_REL}/3.svg": "fig_mech_3_entropy_alignment.pdf",
}
MECHFIG_PDFS = tuple(sorted(MECHFIG_SOURCES.values()))

PAPER_SKIP_EXT = {".aux", ".log", ".out", ".blg", ".abs", ".synctex.gz",
                  ".toc"}
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
        # ".npz" is in this whitelist for exactly one record set: the E3
        # per-step prediction vectors under
        # experiments/results/is_fresh/e3_vectors/.  They are the object whose
        # ABSENCE made the retrospective selector non-recomputable from the
        # release, so they are records in the strict sense -- what the run
        # emitted -- and not derived artefacts.  No other directory reachable
        # from RESULT_DIRS contains a .npz; if one ever does, it ships, which
        # is why the payload census in the manifest is generated and not typed.
        #
        # ".sha256" is here for the theory-closure suite's two transfer-
        # integrity lists.  Its MANIFEST.md tells a reader to run
        # `sha256sum -c MANIFEST_staged.sha256`, and an instruction whose
        # object does not ship is worse than no instruction; the two files are
        # the only .sha256 reachable from RESULT_DIRS.
        for full, rel in walk(d, lambda fn, ext: ext in {".json", ".md",
                                                         ".log", ".txt",
                                                         ".npz", ".sha256"}):
            if rel.startswith(RESULT_EXCLUDE_PREFIXES):
                continue
            files[rel] = full
    for d in PAPER_DIRS:
        # ".md" is in the whitelist so that
        # paper/is2/paper/BUILD_ENVIRONMENT.md -- the RECORD of the reference
        # LaTeX environment -- travels with the sources it describes.  It is a
        # detailed version record, not an executable frozen TeX installation:
        # the archive does not ship one, so cross-machine pagination is not
        # guaranteed and is not promised anywhere.
        for full, rel in walk(
                d, lambda fn, ext: (ext in {".tex", ".bib", ".txt", ".pdf",
                                            ".md"}
                                    and ext not in PAPER_SKIP_EXT
                                    and fn not in {"main.pdf",
                                                   "supplement.pdf"})):
            parts = rel.split("/")
            if PAPER_SKIP_DIRS & set(parts):
                continue
            tail = "/".join(parts[3:])          # below paper/is2/<doc>/
            if tail in PAPER_EXCLUDE:
                continue
            files[rel] = full
    for rel in STAGING_FILES:
        full = os.path.join(REPO, rel.replace("/", os.sep))
        paper_twin = os.path.join(REPO, PAPER_REL.replace("/", os.sep),
                                  rel.replace("/", os.sep))
        assert os.path.exists(full), (
            f"{rel} is missing -- COMMANDS.md documents it as the staging "
            f"copy the original generator writes; re-run the generator")
        assert os.path.exists(paper_twin), f"{paper_twin} is missing"
        assert sha256(full) == sha256(paper_twin), (
            f"{rel} and its paper copy differ; COMMANDS.md claims they are "
            f"byte-identical, so re-stage before packaging")
        files[rel] = full

    # THE TWO BUILT DOCUMENTS.  This submission is a PAIR, and the archive
    # carries both of them together with the two build transcripts and the two
    # compiled bibliographies, so that the BibTeX-free rebuild
    # BUILD_ENVIRONMENT.md section 1 documents works for each document from
    # THIS archive and not only from the review package.  `.pdf` is excluded
    # from the walk above for exactly these two names and re-added here;
    # `.log` and `.bbl` are outside the walk's whitelist entirely.  Only the
    # two build logs of record: the r*p*.log transcripts beside them are
    # scratch.
    for doc_rel, stem in ((PAPER_REL, "main"), (SUPP_REL, "supplement")):
        for ext, why in ((".pdf", "the artefact the package exists to "
                                  "deliver"),
                         (".log", "BUILD_ENVIRONMENT.md reads the package "
                                  "load list off it and supplies `grep` "
                                  "commands against it"),
                         (".bbl", "BUILD_ENVIRONMENT.md section 1 documents "
                                  "it as shipped so a reader without the "
                                  "'.bib' toolchain can skip bibtex")):
            rel = f"{doc_rel}/{stem}{ext}"
            full = os.path.join(REPO, rel.replace("/", os.sep))
            assert os.path.exists(full), (
                f"{rel} is missing -- {why}; rebuild the document before "
                f"packaging")
            files[rel] = full

    # THE AUTHOR-DRAWN MECHANISM FIGURES AND THEIR SOURCES.  The three PDFs
    # arrive through the PAPER_DIRS walk above, like every other artefact under
    # `paper/is2/paper/figures/`; what does not is the vector source each was
    # converted from, which lives outside the two document trees.  Both halves
    # are asserted here: a PDF with no shipped source would be an artefact this
    # archive cannot account for, and a source with no PDF would mean the
    # documents stopped typesetting artwork the archive still carries.
    for src_rel, pdf_name in sorted(MECHFIG_SOURCES.items()):
        full = os.path.join(REPO, src_rel.replace("/", os.sep))
        assert os.path.exists(full), (
            f"{src_rel} is missing -- it is the SOURCE OF RECORD for "
            f"{pdf_name}, which the article typesets; see MECHFIG_SOURCES")
        assert f"{PAPER_REL}/figures/{pdf_name}" in files, (
            f"{pdf_name} is absent from the payload although its source "
            f"{src_rel} ships; the article typesets it, so re-run the "
            f"conversion of BUILD_ENVIRONMENT.md section 5 before packaging")
        files[src_rel] = full

    # D6, AT COLLECTION TIME.  The gate is repeated over the finished ZIP in
    # `verify()`; this one fails the build before a byte is written, so a
    # figure the supplement now points at cannot silently go missing.
    d6 = [rel for rel in files if os.path.basename(rel) == D6_REQUIRED]
    assert d6, (
        f"{D6_REQUIRED} is absent from the payload; the supplement points at "
        f"it as a release visualization, so the archive must carry it for the "
        f"pointer to resolve -- see D6_REQUIRED")

    # SELF-REBUILD GATE, AT COLLECTION TIME.  The packager reads the four
    # dependency-provenance records from `paper/is2/provenance/`.  If that
    # directory is not in the PAYLOAD, the extracted release ships the
    # packager without the inputs the packager needs, and the archive stops
    # being able to rebuild itself -- which is exactly the defect this
    # arrangement exists to close.  Asserted here so the state is
    # unpackageable rather than merely undesirable.
    missing_prov = [n for n in PROVENANCE_ENTRIES
                    if f"{PROVENANCE_REL}/{n}" not in files]
    assert not missing_prov, (
        f"the payload does not carry {missing_prov} under {PROVENANCE_REL}/; "
        f"the extracted archive could then not run make_release_zip.py, "
        f"because provenance_entries() reads them from there.  Check that "
        f"{PROVENANCE_REL} is in CODE_DIRS and that the files exist")
    assert f"{PROVENANCE_REL}/README.md" in files, (
        f"{PROVENANCE_REL}/README.md is not in the payload; a verbatim copy "
        f"without a statement of what it is and how to re-verify it is not a "
        f"provenance record")
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


# THE DEPENDENCY-PROVENANCE ENTRIES ARE READ, NOT REGENERATED.
#
# `BUILD_INTERPRETER.md`, the two requirements files and `pip-freeze-full.txt`
# describe THE INTERPRETER THAT PRODUCED THE NUMBERS -- Python 3.10.9 under
# Anaconda on the build machine -- and not the interpreter that happens to run
# the packager.  Rendering them from the running interpreter makes them a
# record of the packaging session instead: the pins become whatever is
# installed here, `RESOLVER_TRANSCRIPT.md`'s resolution claims stop being about
# the shipped file, and `pip-freeze-full.txt` stops carrying the conda-prefix
# and user-site paths that ARE the provenance evidence section 6.4 reasons
# about.  The absolute-path gate noticed exactly that: on a clean non-conda
# interpreter the regenerated freeze is path-free, so a DECLARED exception went
# stale and the build failed rather than shipping a record of the wrong
# machine.
#
# They are therefore SHIPPED VERBATIM.  The four entries are provenance of the
# experiments, not of the package, so copying them forward is what keeps them
# true; regenerating them is what would falsify them.
#
# WHERE THEY ARE READ FROM, AND WHY IT CHANGED.  They used to be read straight
# out of the frozen tree's `release_archive.zip`, which is where that
# interpreter's own packaging run wrote them.  That made this script
# UNRUNNABLE FROM ITS OWN RELEASE: the frozen parent archive is not shipped
# inside `paper/is2/release_archive.zip` (it is a 37 MB archive of a different
# submission), so from a clean extraction the default command died on
#     AssertionError: .../paper/is/release_archive.zip is missing
# and the released archive could not rebuild itself with the packaging utility
# it documents.  A self-contained release that cannot regenerate itself is not
# self-contained.
#
# The four records therefore ship as ordinary files under
# `paper/is2/provenance/`, extracted byte-for-byte from the frozen archive
# once and never edited since.  That directory is the DEFAULT AND ONLY
# REQUIRED source, it is itself part of the payload (see PROVENANCE_REL in
# CODE_DIRS), and the arrangement is transparent and non-recursive: no archive
# contains another archive, and a reader can open the four objects directly.
#
# THE INTEGRITY CHECK IS KEPT, CONDITIONALLY.  Inside the source repository
# the frozen archive IS present, and there the shipped copies are asserted
# byte-identical to its entries, so a drifted or edited copy fails the build
# loudly.  Inside an extracted release the frozen archive is absent BY DESIGN;
# the check is then skipped with a printed statement that it was skipped, and
# the copies are authenticated the way every other shipped file is -- by
# MANIFEST.json and by the SHA-256 of the whole ZIP.  Skipping a check that
# cannot be run is not the same as not having one, and the difference is
# printed rather than left to be inferred.
FROZEN_ARCHIVE = os.path.join(REPO, "paper", "is", "release_archive.zip")
PROVENANCE_REL = "paper/is2/provenance"
PROVENANCE_DIR = os.path.join(IS2, "provenance")
PROVENANCE_ENTRIES = ("BUILD_INTERPRETER.md", "requirements-analysis.txt",
                      "requirements-experiment.txt", "pip-freeze-full.txt")
# The one sentence of the frozen dependency record that the current code
# contradicts.  COMMANDS.md quotes it and states what supersedes it; this
# constant is what ties the quotation to the shipped bytes.
STALE_TORCH_SENTENCE = (
    "torch is a HARD dependency of the CPU-only re-analyses too")


def provenance_entries(quiet=False):
    """The four dependency-provenance root entries, read from `provenance/`.

    Read-only in both directions: nothing under `paper/is/` is ever written by
    this script, and nothing under `paper/is2/provenance/` is either.  The
    directory is the only required source; the frozen archive, when present,
    is used solely to assert that the shipped copies still match it.
    """
    out = {}
    for n in PROVENANCE_ENTRIES:
        p = os.path.join(PROVENANCE_DIR, n)
        assert os.path.exists(p), (
            f"{PROVENANCE_REL}/{n} is missing.  It is a verbatim copy of the "
            f"record of the interpreter that produced every number in this "
            f"submission, it ships in the archive, and it is regenerated by "
            f"nobody -- see provenance/README.md for how to restore it from "
            f"the frozen tree and how to re-verify it")
        with open(p, "rb") as fh:
            out[n] = fh.read()
    # A silently empty or truncated copy would ship a provenance record that
    # says nothing, which is worse than one that says something wrong.
    for n, body in out.items():
        assert len(body) > 500, (
            f"{PROVENANCE_REL}/{n} is empty or truncated ({len(body)} bytes)")

    # THE SUPERSEDED TORCH SENTENCE MUST STILL BE THERE.  `requirements-
    # analysis.txt` is a frozen provenance record and carries a line that was
    # true of the code when it was written and is false of the code shipped
    # here: torch as a hard dependency of the CPU re-analysis.  It is NOT
    # corrected -- correcting a provenance record turns it into a description
    # of the current tree -- so COMMANDS.md supersedes it in words, quoting
    # it.  A quotation of a line that has silently disappeared is worse than
    # no quotation, so the build asserts the line is present.  If this fires,
    # the record changed and the COMMANDS.md paragraph must be rewritten to
    # match, not the other way round.
    assert STALE_TORCH_SENTENCE in out["requirements-analysis.txt"].decode(
        "utf-8", "replace"), (
        f"{PROVENANCE_REL}/requirements-analysis.txt no longer contains the "
        f"superseded torch sentence that COMMANDS.md quotes and supersedes; "
        f"either the record was edited (it must not be) or the quotation in "
        f"commands_md() is stale")

    if os.path.exists(FROZEN_ARCHIVE):
        with zipfile.ZipFile(FROZEN_ARCHIVE) as z:
            names = set(z.namelist())
            missing = [n for n in PROVENANCE_ENTRIES if n not in names]
            assert not missing, (
                f"the frozen archive does not carry {missing}; the shipped "
                f"provenance copies cannot be checked against it")
            drift = [n for n in PROVENANCE_ENTRIES if z.read(n) != out[n]]
        assert not drift, (
            f"the shipped provenance copies under {PROVENANCE_REL}/ are NOT "
            f"byte-identical to the frozen archive's entries: {drift}.  They "
            f"are a verbatim copy by definition, so a difference means one of "
            f"them was edited or regenerated -- restore it from the frozen "
            f"archive rather than relaxing this check")
        if not quiet:
            print(f"[release] provenance integrity OK: all "
                  f"{len(PROVENANCE_ENTRIES)} shipped copies are "
                  f"byte-identical to paper/is/release_archive.zip")
    elif not quiet:
        print(f"[release] provenance: the frozen archive is absent (this is "
              f"an extracted release, not the source repository), so the "
              f"byte-identity cross-check is SKIPPED; the "
              f"{len(PROVENANCE_ENTRIES)} shipped copies under "
              f"{PROVENANCE_REL}/ are used as-is and are authenticated by "
              f"MANIFEST.json")
    return {n: b.decode("utf-8") for n, b in out.items()}


def build_stamp():
    """The archive's build timestamp, derived from the tree, not the clock.

    WHY NOT `datetime.now()`.  Two builds of an identical tree then produce
    byte-different archives, and "the same tree produces the same archive"
    stops being checkable: the only way to compare two builds is to open them
    and diff the payload, which is exactly the work the checksum exists to
    avoid.  The stamp is therefore the modification time of the article's
    `main.pdf` -- the artefact the package exists to deliver, and the file
    whose change is the reason to repackage at all.  Every ZIP entry carries
    it, `MANIFEST.json` records it, and `INDEX.md` prints it, so the whole
    archive is a pure function of the tree and the review package's determinism
    claim covers both packages in the same words.
    """
    mtime = os.path.getmtime(os.path.join(REPO, PAPER_REL, "main.pdf"))
    return datetime.fromtimestamp(mtime, timezone.utc)


def log_pages(log_path):
    """The page count a pdflatex transcript records, or None."""
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    pages = None
    for m in re.finditer(r"\((\d+) pages?[,)]", text):
        pages = int(m.group(1))
    return pages


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
| local-PL envelope monotonicity audit | `f33_pl_envelope_monotonicity.py` | 20260807 | its own draws over the envelope's admissible constants; reads no record |
| local-PL envelope at zero noise | `f35_pl_zero_noise.py` | 20260808 | its own draws over the admissible constants at sigtot = 0; reads no record |
| flow curve vs exact curve, and sigma = 0 as a value | `f36_flow_integer_bridge.py` | 20260809 | its own draws inside the flow corollary's hypotheses; reads no record |
| ReLU stress-test monotonicity, recounted | `f37_relu_monotonicity_recount.py` | none of its own: re-reads the five f6 per-seed records | -- |
| E2 leave-one-corruption-out sensitivity | `f20_e2gn_loco_sensitivity.py` | 20260801-05 split seeds; 20260817 bootstrap | cross-fit split of existing episodes; deletion bootstrap |
| E2 cross-fit, CORRECTED signed statistic, feature proxy | `f8_e2_crossfit.py --statistic phase_feat --out-prefix f22_e2_crossfit_feat` | 20260801-05 | commissioning/evaluation split of existing episodes |
| E2 cross-fit, CORRECTED signed statistic, deterministic arms | `f8b_e2_crossfit_det.py --statistic phase_loss --out-prefix f22b_e2_crossfit_det` | 20260801-05 | same |
| E2 cross-fit, CORRECTED signed statistic, loss proxy | `f8_e2_crossfit.py --statistic phase_loss --out-prefix f22c_e2_crossfit_loss` | 20260801-05 | same |
| E2 fresh-GN feature proxy, remeasured on the fresh source model | `f38_e2gn_deltafeat_fresh.py` | none of its own: a deterministic forward pass of the retained seed-20260806 checkpoint over the retained episode indices | -- |
| E3 selector recomputed from the released per-step vectors | `f39_e3_vector_selfcheck.py` | none of its own: the admissibility scan is deterministic and reads only `results/is_fresh/e3_vectors/*.npz` | -- |
| Per-member manifest of the unattached replica side archive | `f40_e3_replicas_manifest.py` | none of its own: it hashes the members and arrays of `paper/is2/e3_vectors_replicas.zip` | -- |
| Build and manifest the unattached theory-closure record archive | `f41_closure_records_manifest.py` | none of its own: it packs and hashes `results/is_fresh/closure/records/*.jsonl.gz` into `paper/is2/closure_records.zip` | -- |
| E2 matched-cell cross-fit, CORRECTED | `f16_e2_gn_analysis.py --out-prefix f23_e2_gn` | 20260801-05 | same |
| E2 leave-one-corruption-out, CORRECTED | `f20_e2gn_loco_sensitivity.py --out-name f24_e2gn_loco_sensitivity.json` | 20260801-05 split seeds; 20260817 bootstrap | as `f20` |
| E2 learning-rate ablation | `f25_e2_lr_ablation.py` | 20260801-05 | cross-fit split of existing episodes |
| E1 reporting audit (excess, accuracy and comparison-count census) | `f26_e1_reporting_audit.py` | none of its own: re-reads the f7/f10/f3/f4/f13 records | -- |
| E2 identity-level overlap of the cross-fit split | `f27_e2_identity.py` | 20260801-05 | reproduces f8's commissioning/evaluation split stream exactly |
| E2 temperature-scaling: BOTH estimands of the early-loss statement | `f34_e2_tempscale_estimands.py` | none of its own: re-reads the e2 calibration records | -- |
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


def selector_release_facts():
    """Everything INDEX.md says about the E3 selector, READ rather than typed.

    The section this feeds used to be prose.  It said the per-step mean
    prediction vectors were not in the archive; they were added, the prose was
    not, and the archive shipped a clean integrity report wrapped around a
    false description of its own contents.  Nothing about that was catchable:
    every hash matched, every path resolved, and the defect was a sentence.

    So the sentence is generated.  Each field below comes from a record or
    from the shipped files themselves, and the section rendered from them is
    false only if the records are.
    """
    fresh = os.path.join(REPO, "experiments", "results", "is_fresh")
    with open(os.path.join(fresh, "f39_e3_vector_selfcheck.json"),
              encoding="utf-8") as f:
        t = json.load(f)["totals"]
    vdir = os.path.join(fresh, "e3_vectors")
    vecs = sorted(n for n in os.listdir(vdir) if n.endswith("_vectors.npz"))
    d = t["mismatch_directions"]
    assert (d["admitted_here_rejected_there"]
            + d["rejected_here_admitted_there"]
            == t["n_mismatches_vs_retained"]
            == t["n_documents"] - t["vs_retained_matches"]), t
    out = {
        "n_vec_files": len(vecs),
        "n_docs": t["n_documents"],
        "selfcheck": t["selfcheck_matches"],
        "vs_published": t["vs_retained_matches"],
        "pct": 100.0 * t["vs_retained_rate"],
        "n_mismatch": t["n_mismatches_vs_retained"],
        "n_earlier": d["admitted_here_rejected_there"],
        "n_later": d["rejected_here_admitted_there"],
        "worst_slack": t["worst_abs_normalised_slack_at_disputed_step"],
        "ppl_jobs": t["n_jobs_with_ppl20_comparison"],
    }
    # The side archive's member manifest, if this build has it.  It is the
    # answer to "the manifest names an archive I do not have": a reader who
    # obtains it can then verify its CONTENTS member by member and array by
    # array.  It is not evidence of possession, and does not say it is.
    rm = os.path.join(vdir, "REPLICAS_MANIFEST.json")
    if os.path.exists(rm):
        with open(rm, encoding="utf-8") as f:
            r = json.load(f)
        out.update({"rep_have": True, "rep_entries": r["n_entries"],
                    "rep_npz": r["n_npz_members"], "rep_arrays": r["n_arrays"],
                    "rep_bytes": r["archive_bytes"],
                    "rep_sha": r["archive_sha256"],
                    "rep_unc": r["total_uncompressed_bytes"]})
    else:
        out.update({"rep_have": False, "rep_entries": 0, "rep_npz": 0,
                    "rep_arrays": 0, "rep_bytes": 0, "rep_sha": "",
                    "rep_unc": 0})
    return out


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


# --------------------------------------------------------------------------
# EXTERNAL INPUTS THAT COMPLETE REGENERATION NEEDS AND THIS ARCHIVE DOES NOT
# CARRY.
#
# ANALYSIS REPRODUCTION and ORIGINAL EXPERIMENTAL REGENERATION are two
# different operations, and one sentence used to cover both: "that single file
# is everything needed to recompute every manuscript number".  It is true of
# the first -- `requirements-analysis.txt` plus the shipped records recompute
# the printed numbers on a CPU -- and false of the second, which additionally
# needs datasets, tokenizer and model weights, checkpoints, corruption tensors
# and a GPU, none of which any requirements file can supply.
#
# THE LIST IS DERIVED, NOT TYPED.  A hand-kept list of external dependencies
# is a claim that rots the first time a runner changes its corpus.  The
# identifiers below are read out of the SHIPPED experiment runners -- the
# literal `load_dataset`, `repo_id=`, torchvision-dataset and
# `from_pretrained` arguments they pass -- and out of the SHIPPED original
# records' own `meta` blocks, which state the torch build and the GPU each run
# actually used.  Only the per-category REASON is prose, and a reason is not a
# number.
_EXTERNAL_SCAN_DIRS = ("experiments/ttt/e2_cifar", "experiments/ttt/e4_gpt2")
_EXTERNAL_PATTERNS = (
    ("dataset (Hugging Face hub)",
     re.compile(r"""load_dataset\(\s*["']([^"']+)["']"""
                r"""(?:\s*,\s*["']([^"']+)["'])?""")),
    ("dataset (Hugging Face hub)",
     re.compile(r"""repo_id\s*=\s*["']([^"']+)["']""")),
    # `hf_hub_download` takes the repository positionally in the E4 legal
    # corpus loader, so the keyword pattern above does not see it.  The fourth
    # corpus went missing from a hand-kept list exactly once; it cannot go
    # missing from a scan that matches the call itself.
    ("dataset (Hugging Face hub)",
     re.compile(r"""hf_hub_download\(\s*["']([^"']+)["']""")),
    ("dataset (torchvision download)",
     re.compile(r"""datasets\.(CIFAR10|CIFAR100)\b""")),
    ("corruption tensor set (external download or regeneration)",
     re.compile(r"""["'](CIFAR-\d+-C)["']""")),
    ("pretrained weights and tokenizer",
     re.compile(r"""from_pretrained\(\s*["']([^"']+)["']""")),
)
# Why each category is absent.  Reasons, not counts; the identifiers they
# apply to are discovered, never listed here.
_EXTERNAL_REASONS = {
    "dataset (Hugging Face hub)":
        "third-party corpus, redistributed by its own host under its own "
        "terms; not ours to ship",
    "dataset (torchvision download)":
        "third-party dataset fetched by the runner at first use",
    "corruption tensor set (external download or regeneration)":
        "tens of GB of image tensors; excluded by size, regenerable from the "
        "public release or from the shipped generation script",
    "pretrained weights and tokenizer":
        "third-party model weights and tokenizer resolved from the hub by "
        "name at run time; the runs recorded the NAME, not a pinned revision "
        "hash, so an exact re-fetch of the same weights is not guaranteed",
    "GPU (recorded device)":
        "hardware; the original runs are not reproducible on CPU in any "
        "practical time, and results can differ across device and driver",
    "CUDA-linked torch build (recorded)":
        "the archive was packaged on a CPU-only interpreter, so the pin in "
        "requirements-experiment.txt is the CPU wheel; the build named in "
        "the identifier column is the one that actually ran",
    "source checkpoints (*.pt)":
        "excluded by size; regenerable with the shipped training scripts "
        "given the datasets above, but not bit-identically",
    "distribution absent from the build interpreter":
        "needed only by the original data-preparation scripts, which ran on "
        "separate machines; left unpinned rather than pinned to a version "
        "this build never saw",
}


def _scan_external_identifiers():
    """{(category, identifier): [repo-relative files that name it]}."""
    found = {}
    for d in _EXTERNAL_SCAN_DIRS:
        base = os.path.join(REPO, d.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".py"):
                continue
            rel = f"{d}/{fn}"
            with open(os.path.join(base, fn), encoding="utf-8",
                      errors="replace") as fh:
                src = fh.read()
            for cat, pat in _EXTERNAL_PATTERNS:
                for m in pat.finditer(src):
                    parts = [g for g in m.groups() if g]
                    ident = " / ".join(parts)
                    found.setdefault((cat, ident), [])
                    if rel not in found[(cat, ident)]:
                        found[(cat, ident)].append(rel)
    return found


def _recorded_run_hardware():
    """{(category, identifier): [record files that state it]}, from meta.

    The original records carry `meta.torch` and `meta.cuda`: the torch build
    and the GPU each run used.  Those are the hardware-dependent requirements,
    stated by the runs themselves rather than by us.
    """
    found = {}
    for d in ("experiments/results/m0", "experiments/results/e2",
              "experiments/results/e4", "experiments/results/e5"):
        base = os.path.join(REPO, d.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(base, fn), encoding="utf-8") as fh:
                    meta = json.load(fh).get("meta", {})
            except Exception:                    # pragma: no cover
                continue
            for key, cat in (("cuda", "GPU (recorded device)"),
                             ("torch", "CUDA-linked torch build (recorded)")):
                val = meta.get(key)
                if isinstance(val, str) and val:
                    found.setdefault((cat, val), [])
                    if len(found[(cat, val)]) < 3:
                        found[(cat, val)].append(f"{d}/{fn}")
    return found


def external_inputs():
    """Every external input a COMPLETE regeneration needs, derived.

    Returns a sorted list of (category, identifier, named_in, reason).
    `named_in` is the shipped file that names the identifier, so every row is
    checkable against the archive rather than against this docstring.
    """
    rows = []
    found = dict(_scan_external_identifiers())
    found.update(_recorded_run_hardware())
    for (cat, ident), where in found.items():
        named = ", ".join(where[:2]) + (" (+more)" if len(where) > 2 else "")
        rows.append((cat, ident, named,
                     _EXTERNAL_REASONS.get(cat, "not shipped")))
    # The two object classes that are excluded by extension rather than named
    # by a call, and the distributions the build interpreter never carried.
    savers = []
    for d in _EXTERNAL_SCAN_DIRS:
        base = os.path.join(REPO, d.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(base, fn), encoding="utf-8",
                      errors="replace") as fh:
                if "torch.save(" in fh.read():
                    savers.append(f"{d}/{fn}")
    if savers:
        rows.append(("source checkpoints (*.pt)",
                     "written by the shipped training scripts",
                     ", ".join(savers[:2])
                     + (" (+more)" if len(savers) > 2 else ""),
                     _EXTERNAL_REASONS["source checkpoints (*.pt)"]))
    for name, why in _REQ_UNPINNED:
        rows.append(("distribution absent from the build interpreter", name,
                     why.split(" (")[0],
                     _EXTERNAL_REASONS[
                         "distribution absent from the build interpreter"]))
    # A row whose only witness is a file this submission dropped is a
    # disclosure about somebody else's experiment.  `imagenet_c` reaches this
    # table only through `experiments/ttt/e3_imagenet/`, which DROPPED_PAYLOAD
    # removes, so it is filtered out HERE, by the same map the collector
    # applies -- not by a second hand-kept exclusion list that could disagree
    # with it.
    def _dropped(named):
        wits = [w.strip() for w in named.replace(" (+more)", "").split(",")]
        wits = [w for w in wits if "/" in w]
        return bool(wits) and all(
            any(w.startswith(k) for k in DROPPED_PAYLOAD) for w in wits)

    rows = [r for r in rows if not _dropped(r[2])]
    assert rows, (
        "external_inputs() found nothing, which cannot be true of a "
        "submission with GPU experiments: the scan is broken, and a silently "
        "empty disclosure table is worse than none")
    return sorted(rows)


def external_inputs_rows():
    """The derived external-input table, as Markdown rows."""
    return "\n".join(f"| {c} | `{i}` | `{w}` | {r} |"
                     for c, i, w, r in external_inputs())


def document_pages():
    """(main pp, supplement pp), read off the two pdflatex transcripts.

    TYPED PAGE COUNTS ROT, AND THESE DID.  COMMANDS.md carried "(41 pp)" and
    "17 pp" long after the restructuring had taken the article to a different
    length and grown the supplement; both numbers were true when written and
    false when read, and no gate was watching them.  There is
    no defensible reason to type a number the build transcript states, so
    neither is typed anywhere any more: this is the single reader, `index_md`
    and `commands_md` both call it, and a transcript that does not state a
    page count fails the build rather than falling back on a literal.
    """
    n_main = log_pages(os.path.join(REPO, PAPER_REL, "main.log"))
    n_supp = log_pages(os.path.join(REPO, SUPP_REL, "supplement.log"))
    assert n_main and n_supp, (
        "the page count of one of the two documents did not parse out of its "
        f".log (main={n_main}, supplement={n_supp}); rebuild the documents "
        "before packaging rather than typing the counts")
    return n_main, n_supp


def commands_md():
    n_curated, n_construction = curated_claim_counts()
    n_main_pp, n_supp_pp = document_pages()
    return """# Exact commands, in dependency order

All paths are relative to the extracted archive root.

## What this archive audits

The submission is a PAIR of documents: `paper/is2/paper/main.pdf`
({n_main_pp} pp) and
`paper/is2/supplement/supplement.pdf` ({n_supp_pp} pp).  Both ship here with their
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
  `experiments/ttt/is_fresh` inherited a hard torch dependency it never used,
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
  original experiment runners under `experiments/ttt/{e2_cifar,e4_gpt2}`.

  **THE COMPLETE LIST, because `requirements-analysis.txt` contradicts this
  paragraph and cannot be corrected.**  Exactly three shipped scripts import
  torch: `is_fresh/f6_relu_multiseed.py` (CPU, and part of the documented
  re-analysis), `is_fresh/f_scope_bench.py` (a wall-clock benchmark that
  recomputes no manuscript number; needs torchvision and CUDA) and
  `is_fresh/f15_e2_entropy_gn.py` (needs torchvision, CUDA and the unshipped
  CIFAR tensors).  `figures/scripts/` imports it nowhere.  Every other
  documented command -- every other script in `experiments/ttt/is_fresh`,
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
  `paper/is2/provenance/` are a byte-identical record of the interpreter and
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
  `experiments/ttt/is_fresh/RESOLVER_TRANSCRIPT.md` section 2.

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
  (`opencv-python==4.9.0.80`, transcript in `RESOLVER_TRANSCRIPT.md` section
  2), and lists the GPU, dataset and checkpoint
  prerequisites that no requirements file can supply.

  Interpreter, OS and hardware metadata are in `BUILD_INTERPRETER.md`; the
  complete freeze of the build machine (a Windows/Anaconda environment, most
  of it unrelated to this project, but also pip-parseable) is in
  `pip-freeze-full.txt`.
* **The LaTeX side is pinned separately** in
  `paper/is2/paper/BUILD_ENVIRONMENT.md`, which ships in this archive: TeX
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
{external_inputs_rows}

Two consequences are worth stating rather than leaving to be inferred.
**The model and tokenizer are resolved by NAME, not by a pinned revision.**
The runs recorded which model they asked for; they did not record a
commit hash for the weights, so a re-fetch obtains whatever that name
resolves to at the time it is run, and bit-identical weights are not
guaranteed.  **The recorded GPU and the recorded torch build are part of the
experimental conditions**, not incidental: the archive was packaged on a
CPU-only interpreter, floating-point reduction order differs across devices,
and a regeneration on other hardware is a replication rather than a rerun.

Every executable script in `experiments/ttt/is_fresh` appears below exactly
once.  The only file in that directory with no command line is `common.py`,
which is an imported module (paths, seed lists, JSON helpers) and has no
`main()`.

## Building the two documents

```
bash paper/is2/tools/build.sh          # main.pdf   -- pdflatex, bibtex, x4
bash paper/is2/tools/build_supp.sh     # supplement.pdf
bash paper/is2/tools/gates.sh          # the manuscript gate suite, all green
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
cd experiments/ttt/is_fresh

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
python f8_e2_crossfit.py  --statistic phase_feat \\
       --out-prefix f22_e2_crossfit_feat       # feature proxy (sign-carrying)
python f8b_e2_crossfit_det.py --statistic phase_loss \\
       --out-prefix f22b_e2_crossfit_det       # tent / pseudo-label
python f8_e2_crossfit.py  --statistic phase_loss \\
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
# verifiable -- a manifest of absent bytes proves nothing about them.  It needs the side archive, which is an author-side deposit beside
# the DOI release and is NOT in this payload, so from a clean extraction it
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
python f20_e2gn_loco_sensitivity.py \\
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
#  `paper/is2/tools/tab_s7_e4_proxy.py`, below.  `tab_t6_e4_proxy.py` remains
#  the generator of the FROZEN tree's copy and is listed with the other frozen
#  tooling in the table further down.)

# --- fix-forward GPU run (one GPU, ~2.5 h) -------------------------------
python f15_e2_entropy_gn.py              # entropy objective on ResNet-26+GN
#   then re-run f16/f23 and f20/f24 to score its records
python f_scope_bench.py                  # wall-clock scoping only, no results
```

## The is2 manuscript tools

These live in `paper/is2/tools` and act on the two documents this archive
ships.  Run them from that directory.

```
cd paper/is2/tools

python r9_reconcile.py                   # {n_curated} CURATED headline claims
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
#                                          it as "{n_curated} curated headline
#                                          and repeated numerical claims",
#                                          never as "every number".
#                                          It also runs {n_construction}
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
#                                          experiments/ttt/is_fresh/
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
#                                          other's \\label; this reads each
#                                          document's own .aux and writes the
#                                          other's table (main.aux ->
#                                          supplement/xref_main.tex, and
#                                          supplement.aux ->
#                                          paper/xref_supp.tex).  Sources cite
#                                          by LABEL (\\mref, \\sref), never by a
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
#                                          paper/is2/provenance/ inside this
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

`experiments/ttt/is_fresh` ships whole, because it is the analysis suite as it
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
| `tab_t4_e1_gates.py` | the six-part gate table of the frozen tree; `paper/is2/tools/tab_s4_e1_gates.py` generates the table this submission prints | no: it reads a record set that is not here |
| `tab_t6_e4_proxy.py` | the frozen tree's copy of the per-domain proxy table, `paper/is/paper/figures/T6_e4_proxy.tex`; `paper/is2/tools/tab_s7_e4_proxy.py` generates supplement Table S7, which is the table this submission prints and which differs from the frozen one in symbol, label and layout | no: its output target is in the frozen tree, which this archive does not carry |
| `build_env_section3.py` | the frozen tree's copy | no |
| `make_release_zip.py` | the frozen tree's packager, **not** the verifier of this archive: its path-exception map is for the frozen package's layout, so against this one it fails for that reason alone.  This submission's packager and absolute-path gate are `paper/is2/tools/make_release_zip.py` (`--check-paths .`), which is what `BUILD_ENVIRONMENT.md` names throughout | no: quarantined at its command line — it prints the two `paper/is2/tools` commands and exits non-zero unless `TTT_RUN_FROZEN_PACKAGER=1` |
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
`paper/is2/paper/BUILD_ENVIRONMENT.md` records the route in full, including the
one glyph that needed handling.  `make_release_zip.py` asserts, for each of the
three, that the source ships and that the PDF it converts to is in the payload,
and the no-collision gate asserts that **no** live generator writes any of the
three PDF basenames -- a script that did would replace author artwork with a
plot on the next bulk re-run of `figures/scripts`.

## Superseded generators -- do not run

`figures/scripts/_superseded/` holds the original generators for the figures
and the gate table.  Each wrote a file with the same basename as an object
that a current generator now produces, from single-seed or full-sample data,
so running them in bulk would have overwritten a current artifact with a stale
one.  They are kept as the audit trail only, have no command line here, and
are not runnable in place (they `import _style`, which resolves only from
`figures/scripts/`).  See `figures/scripts/_superseded/README.md` for the
one-line reason per file.

Each script prints its headline numbers and asserts its own reproduction check;
a non-zero exit status means the check failed.
""".replace("{n_curated}", str(n_curated)).replace(
        "{n_construction}", str(n_construction)).replace(
        "{n_main_pp}", str(n_main_pp)).replace(
        "{n_supp_pp}", str(n_supp_pp)).replace(
        "{external_inputs_rows}", external_inputs_rows())


# --------------------------------------------------------------------------
# AUDIT_MAP.json -- the machine-readable claim -> record -> command map.
#
# WHY IT EXISTS.  The archive is rich and hard to audit by hand: a reader who
# wants to know where one printed number came from has to read INDEX.md's
# "Where each claim comes from" table, which is at the granularity of a whole
# figure or table, then find the reduction inside a JSON.  AUDIT_MAP.json is
# the same question answered per PRINTED VALUE, in a form a script can read.
#
# WHY IT IS DERIVED AND WHAT THAT COSTS.  Every field is computed:
#   * the claims, printed tokens and record pointers come from
#     `r9_reconcile.CHECKS`, the curated reconciliation table this archive
#     already ships and already runs;
#   * the locations come from `r9_reconcile.occurrences()`, i.e. from the .tex
#     corpus itself, so a claim's file and line are found, not asserted;
#   * the record FILES are resolved by matching the pointer's prefix against
#     the record set that actually ships;
#   * the COMMANDS are parsed out of the generated COMMANDS.md, so the map
#     cannot name a command line the archive does not document.
#
# The cost is that the map is exactly as PARTIAL as the curated table, which
# is not exhaustive and says so.  A hand-written map would look more complete
# and would be less true.  The `scope` field of the emitted JSON states the
# limitation in the object itself rather than in a document beside it, and the
# `coverage` block reports what fraction of rows resolved to a record, a
# command and a location.
_AUDIT_OBJECT_RE = re.compile(
    r"(?:Sec\.?\s*\d+(?:\.\d+)*"
    r"|Section~?\s*\d+(?:\.\d+)*"
    r"|Fig\.?\s*\d+[a-z]?(?:\([a-z]\))?"
    r"|Figure\s*S?-?F?\d+"
    r"|Table\s*S?\d+"
    r"|abstract"
    r"|[TS]\d+[a-z]?)")
_AUDIT_PREFIX_RE = re.compile(r"^([a-z]\d+[a-z]?)\b")
_CMD_OUT_NAME_RE = re.compile(r"--out-name\s+(\S+)")
_CMD_OUT_PREFIX_RE = re.compile(r"--out-prefix\s+(\S+)")
_CMD_SCRIPT_RE = re.compile(r"^python\s+(\S+\.py)")


def _fresh_record_basenames(files):
    """The is_fresh JSON record basenames that actually ship."""
    return sorted(os.path.basename(r) for r in files
                  if r.startswith("experiments/results/is_fresh/")
                  and r.endswith(".json") and "/" not in
                  r[len("experiments/results/is_fresh/"):])


def _commands_by_record(cmds_md, record_basenames):
    """{record basename: [command line]} parsed out of the generated COMMANDS.md.

    Continuation lines (a trailing backslash) are joined first, so a command
    whose `--out` argument wrapped is still one command.  Only lines inside a
    fenced block that begin with `python ` are considered commands.
    """
    joined, buf, fenced = [], "", False
    for raw in cmds_md.split("\n"):
        line = raw.rstrip()
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            continue
        # COMMANDS.md annotates its command lines with trailing `#` comments;
        # they are documentation, not part of the command, and a map that
        # printed them would be handing a reader an unrunnable string.
        stripped = line.split("#", 1)[0].strip()
        if buf:
            buf += " " + stripped.rstrip("\\").strip()
        elif stripped.startswith("python "):
            buf = stripped.rstrip("\\").strip()
        else:
            continue
        if line.endswith("\\"):
            continue
        joined.append(" ".join(buf.split()))
        buf = ""
    out = {}
    for cmd in joined:
        m = _CMD_SCRIPT_RE.match(cmd)
        if not m:
            continue
        script = os.path.basename(m.group(1))
        claims = []
        mo = _CMD_OUT_NAME_RE.search(cmd)
        if mo:
            claims.append(("exact", os.path.basename(mo.group(1))))
        mp = _CMD_OUT_PREFIX_RE.search(cmd)
        if mp:
            claims.append(("prefix", os.path.basename(mp.group(1))))
        if not claims:
            claims.append(("prefix", script[:-3]))
        for kind, key in claims:
            for b in record_basenames:
                if (b == key) if kind == "exact" else b.startswith(key):
                    out.setdefault(b, [])
                    if cmd not in out[b]:
                        out[b].append(cmd)
    return out


_R9_DOC = {"main": "main", "supp": "supplement", "arch": "release"}


def _tex_location(key, files):
    """Turn an r9 corpus key into (document, archive path).

    THREE corpus classes, not two.  r9_reconcile scans `main:`, `supp:` AND
    `arch:` -- the last being the material that was MOVED OUT of the two
    documents into the reproducibility release (`archive_tables/`, plus the
    generated figure fragments no document still `\\input`s).  This resolver
    once knew only the first two, so every claim printed only in release
    material resolved to no path at all and left this map's `locations` list
    empty; 78 rows were empty for that reason.  An empty list then read as
    the map's own description of an ORPHAN, which those rows are not -- and
    r9_reconcile itself has reported `archive` separately from `orphan` since
    the migration.  Resolving the third class is what makes the emitted
    `locations` mean what the description says it means.
    """
    doc, _, tail = key.partition(":")
    roots = ((ARCH_REL, f"{PAPER_REL}/figures") if doc == "arch"
             else (PAPER_REL, SUPP_REL))
    for root in roots:
        cand = f"{root}/{tail}"
        if cand in files:
            return _R9_DOC.get(doc, doc), cand
    return _R9_DOC.get(doc, doc), None


def audit_map(files, cmds_md, stamp):
    """The claim -> record -> command map, as a JSON-serialisable dict."""
    import importlib
    import sys as _sys
    if HERE not in _sys.path:
        _sys.path.insert(0, HERE)
    r9 = importlib.import_module("r9_reconcile")

    basenames = _fresh_record_basenames(files)
    by_record = _commands_by_record(cmds_md, basenames)

    def resolve_records(prefix):
        hit = [b for b in basenames
               if b == f"{prefix}.json" or b.startswith(f"{prefix}_")]
        return sorted(f"experiments/results/is_fresh/{b}" for b in hit)

    claims = []
    last_records, last_pointer = [], None
    n_rec = n_cmd = n_loc = 0
    for i, (label, token, value, fmt, src, note) in enumerate(r9.CHECKS, 1):
        m = _AUDIT_PREFIX_RE.match(src)
        if m:
            records = resolve_records(m.group(1))
            inherited = False
        else:
            # `same record` and its variants refer to the entry above; the
            # convention is r9's, and following it is stated rather than
            # silently assumed.
            records, inherited = list(last_records), True
        if not inherited:
            last_records, last_pointer = records, src
        try:
            recomputed = fmt % value
        except (TypeError, ValueError):           # pragma: no cover
            recomputed = str(value)
        cmds = []
        for rel in records:
            for c in by_record.get(os.path.basename(rel), []):
                if c not in cmds:
                    cmds.append(c)
        locs = []
        for key, line, _text in r9.occurrences(token):
            doc, path = _tex_location(key, files)
            if path:
                locs.append({"document": doc, "file": path, "line": line})
        objects = sorted(set(_AUDIT_OBJECT_RE.findall(label)))
        # DERIVED, not inferred from `locs` being empty: r9_reconcile's own
        # verdict for this token -- 'main', 'supplement', 'both', 'archive'
        # (printed only in release material) or 'orphan' (printed nowhere,
        # which fails the reconciliation run).  Emitting it makes the
        # archive/orphan distinction readable from this file instead of
        # guessable from the length of a list.
        loc_class = r9.where(token)
        if records:
            n_rec += 1
        if cmds:
            n_cmd += 1
        if locs:
            n_loc += 1
        claims.append({
            "id": f"C{i:04d}",
            "label": label,
            "printed_token": token,
            "recomputed": recomputed,
            "rounding": fmt,
            "record_pointer": src if not inherited else (
                f"{src} -> resolved as {last_pointer}"),
            "records": records,
            "record_resolution": "inherited" if inherited else (
                "by pointer prefix" if records else "unresolved"),
            "regenerating_commands": cmds,
            "command_cwd": "experiments/ttt/is_fresh",
            "manuscript_objects": objects,
            "location_class": loc_class,
            "locations": locs,
            "note": note,
        })

    n = len(claims)
    return {
        "schema": "ttt-is2-audit-map/1",
        "built_utc": stamp.isoformat(),
        "what_this_is":
            "A machine-readable map from a value PRINTED in the article or "
            "the supplement to the record file it is computed from, the "
            "command that regenerates that record, and the source locations "
            "where the value appears.  Every field is derived at packaging "
            "time; nothing in it is typed.",
        "scope":
            "PARTIAL, and partial in a stated way.  The rows are the curated "
            "headline and repeated numerical claims of "
            "paper/is2/tools/r9_reconcile.py, which is a curated audit and "
            "not an exhaustive binding of every number: quantities it does "
            "not bind -- among them the E2 leave-one-corruption-out fold "
            "intervals and some E2 conditional calibration proportions -- "
            "are recomputable from the shipped records but have no row here. "
            "A row is evidence about one printed value; the absence of a row "
            "is not evidence that a value is unsupported.",
        "how_each_field_is_derived": {
            "label, printed_token, rounding, record_pointer, note":
                "r9_reconcile.CHECKS",
            "recomputed":
                "the rounding applied to the value r9_reconcile recomputes "
                "from the record; r9_reconcile.py itself asserts it equals "
                "printed_token",
            "records":
                "the pointer's leading record prefix matched against the "
                "is_fresh record set that actually ships",
            "regenerating_commands":
                "parsed out of this archive's own generated COMMANDS.md, so "
                "no command appears here that the archive does not document",
            "location_class":
                "r9_reconcile.where() for this printed token, over the SAME "
                "three corpora r9_reconcile scans: 'main', 'supplement' or "
                "'both' for a token printed in a submitted document; "
                "'archive' for one printed only in release-side material "
                "(archive_tables/, and the generated figure fragments no "
                "document still inputs), which is a legitimate location; "
                "'orphan' for one printed nowhere, which r9_reconcile.py "
                "reports and exits non-zero on.  This field, not the length "
                "of `locations`, is what distinguishes the two",
            "locations":
                "r9_reconcile.occurrences() over the .tex corpus of the two "
                "documents AND of the release-side material, resolved to "
                "shipped archive paths.  Each entry's `document` is 'main', "
                "'supplement' or 'release'.  An EMPTY list does NOT by "
                "itself mean orphan: it means no occurrence resolved to a "
                "path that ships, which also happens for a corpus file the "
                "release does not carry.  Read `location_class` for the "
                "verdict",
            "manuscript_objects":
                "section, figure and table identifiers extracted from the "
                "claim label; a convenience index, not an authority -- "
                "`locations` is the authority",
        },
        "documents": {
            "main": f"{PAPER_REL}/main.pdf",
            "supplement": f"{SUPP_REL}/supplement.pdf",
        },
        "n_claims": n,
        "coverage": {
            "claims_total": n,
            "claims_resolved_to_a_record_file": n_rec,
            "claims_resolved_to_a_regenerating_command": n_cmd,
            "claims_located_in_the_tex_corpus": n_loc,
            "by_location_class": {
                k: sum(1 for c in claims if c["location_class"] == k)
                for k in ("main", "supplement", "both", "archive", "orphan")
            },
        },
        "claims": claims,
    }


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


def index_md(files, zip_path, generated=None, extra_json=None):
    # PATH-HYGIENE PARAGRAPH: generated from the gate's own census, never
    # from a number typed here.  A typed "exactly one declared exception"
    # here stays on the page while the executable gate reports nineteen
    # exception files holding 240 paths: true when written, false when read.
    # Reading the census makes the sentence true by construction at every
    # rebuild.
    #
    # The census covers EVERY ZIP entry, not only the manifested
    # payload.  `generated` carries
    # the root entries rendered before this one; INDEX.md itself cannot be in
    # its own census, so it is counted as the one extra clean text member it
    # is and the assertion at the bottom of this function proves that
    # description true of the string actually returned.  GENERATED_MANIFEST.json
    # is written after INDEX.md, because it hashes it, and enters through
    # `extra_json` with the leaf count `build()` asserts against the object it
    # actually writes.  No count of generated entries is typed anywhere.
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
    # GENERATED_MANIFEST.json is written AFTER this file, because it hashes
    # it, and it is a JSON member of the same archive.  Its string-leaf count
    # is passed in by `build()` and asserted there against the object actually
    # written, so the figures below cover it exactly.
    extra_json = dict(extra_json or {})
    for _rel, _leaves in sorted(extra_json.items()):
        _cen["json_files"] += 1
        _cen["json_leaves"] += _leaves
        _cen["n_members"] += 1
    n_unmanifested = len(generated) + 1 + len(extra_json)
    # GENERATED_MANIFEST.json hashes every generated root entry but itself.
    n_unmanifested_hashed = n_unmanifested - 1
    n_entries = _cen["n_members"]
    n_manifested = len(files)
    n_exc_files = _cen["n_exception_files"]
    n_exc_ctx = _cen["n_exception_contexts"]
    n_exc_occ = _cen["n_exception_occurrences"]
    n_pipfreeze_occ = _cen["exception_occurrences"]["pip-freeze-full.txt"]
    # measured off r9_reconcile.py, never typed -- see curated_claim_counts()
    n_curated, n_construction = curated_claim_counts()
    n_scan_json = _cen["json_files"]
    n_scan_leaves = _cen["json_leaves"]
    n_scan_text = _cen["text_files"]
    n_scan_bin = _cen["binary_files"]
    n_scan_shebang = _cen["shebangs"]
    exc_rows = "\n".join(
        f"| `{r}` | {_cen['exception_contexts'].get(r, 0)} | "
        f"{_cen['exception_occurrences'].get(r, 0)} |"
        for r in sorted(ABS_PATH_EXCEPTIONS))
    n_by_top = {}
    for rel in files:
        top = "/".join(rel.split("/")[:3])
        n_by_top[top] = n_by_top.get(top, 0) + 1
    rows = "\n".join(f"| `{k}` | {v} |" for k, v in sorted(n_by_top.items()))
    n_json, n_result_json, json_rows, _ = json_census(files)
    # The generated root entries are written into the ZIP after `files` is
    # collected, so they are not in `files`; the archive's total JSON count is
    # the payload count plus however many of them are JSON.  COUNTED, not
    # typed: this used to be a literal `+ 1` beside prose that named
    # MANIFEST.json as "the remaining one", and adding a second generated JSON
    # would have made both false in the same edit.
    root_json = sorted([g for g in generated if g.lower().endswith(".json")]
                       + [g for g in extra_json
                          if g.lower().endswith(".json")])
    n_json_total = n_json + len(root_json)
    root_json_list = ", ".join(f"`{g}`" for g in root_json)
    # THE TWO PAGE COUNTS, read off the two build transcripts.  Typing them
    # here is the same defect as typing a checksum: the sentence is true when
    # written and false the first time either document is rebuilt.  COMMANDS.md
    # typed them and was caught printing 41 and 17 against documents of 31 and
    # 36; it now calls the same reader this does.
    n_main_pp, n_supp_pp = document_pages()
    # The two omission tables are rendered from the maps the collector
    # actually applies, so a payload decision cannot be described here in one
    # way and executed there in another.
    dropped_rows = "\n".join(
        f"| `{k}` | {v} |" for k, v in sorted(DROPPED_PAYLOAD.items()))
    paper_excluded_rows = "\n".join(
        f"| `{k}` | {v} |" for k, v in sorted(PAPER_EXCLUDE.items()))
    # The unavailable-external-input census, derived by the same reader
    # COMMANDS.md uses, so the two documents cannot disagree about what a
    # complete regeneration would need.
    ext_rows = external_inputs_rows()
    # THE E3 SELECTOR SECTION IS DERIVED, NOT DESCRIBED.  It was a hand-written
    # paragraph asserting that the per-step mean prediction vectors were not in
    # this archive and could not be regenerated without repeating the GPU run.
    # They ARE in this archive; the paragraph outlived the release it described
    # by one round, passing every integrity gate the whole time, because a gate
    # on bytes cannot see a sentence about bytes.  The remedy is not a better
    # sentence: it is to stop typing the sentence.  Every quantity below is
    # read from `f39_e3_vector_selfcheck.json`, from the shipped vector files
    # and from the side archive's own member manifest, so the paragraph cannot
    # survive a change in what the archive contains.
    sel = selector_release_facts()
    json_block = f"""## JSON census

State this precisely, because the two counts are not the same count:

* **{n_json_total} JSON files in the archive in total**;
* **{n_result_json} result JSON files** under `experiments/results/`;
* the remaining {len(root_json)} are the generated root-level JSON entries
  {root_json_list} --- archive metadata and audit indices, not result
  records.

The result records break down as:

| directory | result JSON files |
|---|---|
{json_rows}
| **total** | **{n_result_json}** |

Do not write "{n_json_total} result JSON files"; write
"{n_result_json} result JSON files plus the {len(root_json)} generated
root-level JSON entries", or "{n_json_total} JSON files in total".
"""
    body = f"""# Auditability archive -- index

Built {build_stamp().strftime('%Y-%m-%d %H:%M UTC')} for the
Information Sciences submission "When Does Single-Instance Test-Time
Adaptation Help?  Exact Phase Laws in a Solvable Model, Class-Level Minimax
Limits, and an Entropy--Alignment Identity".
It exists so that the submission is independently auditable rather than
merely re-readable.  Extract it and every path below resolves without
editing.

**The submission is two documents.**  `paper/is2/paper/main.pdf` is the
article ({n_main_pp} pp); `paper/is2/supplement/supplement.pdf` is the
Supplementary Material ({n_supp_pp} pp).  Both ship here with their sources,
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
{dropped_rows}

None of it is lost.  The frozen `paper/is/` tree and its own
`release_archive.zip` are the home of record for all of it, complete and
unchanged.

One inclusion is asserted rather than merely intended.  The E4 per-domain
figure (`{D6_REQUIRED}`) is not typeset by either document -- it is an optional
release visualization that the supplement describes as such and points at --
and its PRESENCE is checked twice
-- once over the collected payload before the ZIP is written and once over
the finished archive's own member list -- so it cannot go missing through a
path the collector did not anticipate.  The other figure and table artefacts
of the 79-page build that neither document includes are excluded, each with
its reason:

| excluded artefact | reason |
|---|---|
{paper_excluded_rows}

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
{ext_rows}

The model and tokenizer were resolved by NAME, not by a pinned revision hash,
so a re-fetch obtains whatever that name resolves to when it is run; the
recorded GPU and torch build are part of the experimental conditions, and a
regeneration on other hardware is a replication rather than a rerun.

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
  this archive: {sel['n_vec_files']} files under
  `experiments/results/is_fresh/e3_vectors/`, each carrying `pred0`,
  `pi_bar`, `s`, `t_hat` and `doc` at full float64 ---
  and `experiments/ttt/is_fresh/f39_e3_vector_selfcheck.py` reruns the whole
  admissibility scan on those arrays alone, with no model, corpus, GPU or
  network.  It reproduces the index stored with them on
  **{sel['selfcheck']} of {sel['n_docs']}** documents, exactly, and asserts
  that result rather than printing it: a release whose arrays stopped
  rebuilding the selector fails that script.  `r9_reconcile.py` PASS 1b
  asserts both the presence of the arrays and the exactness of the
  reproduction.
* **(H) PROVENANCE OF THE PUBLISHED RUN'S DECISIONS: NOT supported, and not
  claimed.**  The released vectors come from a RERUN of the published grid on
  different hardware.  The published run's own per-step `pi_bar` trajectories
  were not retained and are recoverable from nothing in this archive, so the
  {sel['n_docs']} historical decisions can be COMPARED against but not
  reconstructed.  The comparison: the rerun's indices agree with the
  published ones on **{sel['vs_published']} of {sel['n_docs']}**
  ({sel['pct']:.2f}%), with {sel['n_mismatch']} disagreements, all of them
  boundary near-ties falling in both directions --- {sel['n_earlier']}
  admitting the disputed step where the published run rejected it and
  {sel['n_later']} rejecting it where the published run admitted it --- and a
  worst normalised slack at a disputed step of {sel['worst_slack']:.3e}.
  Fixed-budget perplexity at t = 20 agrees between the two runs on all
  {sel['ppl_jobs']} jobs.  Those magnitudes are CONSISTENT WITH arithmetic
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
Those are in `e3_vectors_replicas.zip`, which is an **author-side deposit
held alongside the DOI release and is not attached to review
correspondence**: at {sel['rep_bytes'] / 1e6:.1f} MB it would put the
attached pair over the correspondence size limit.  Saying so and printing a
single whole-archive digest is not enough for a reader to check anything, so
this archive also ships that archive's own per-member manifest:

`experiments/results/is_fresh/e3_vectors/REPLICAS_MANIFEST.json`, generated
by `experiments/ttt/is_fresh/f40_e3_replicas_manifest.py`, records for each
of the **{sel['rep_entries']} members** its name, its uncompressed size and
the SHA-256 of its uncompressed bytes, and for each of the
{sel['rep_npz']} `.npz` members the name, shape, dtype and SHA-256 of the raw
C-order bytes of every one of the **{sel['rep_arrays']} arrays** inside it
({sel['rep_unc']:,} uncompressed bytes in total).  **Once the side archive is
obtained, its contents can be verified member by member and array by array**,
independently of how the
ZIP was compressed or in what order it was written --- which a whole-archive
digest is not.  For completeness the archive's own size and digest are
{sel['rep_bytes']:,} bytes and `{sel['rep_sha']}`.  Re-derive the manifest
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
  (`r9_reconcile.py`) binds **{n_curated} curated headline and repeated
  numerical claims** to records of record, with {n_construction} further
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

* `MANIFEST.json` covers the **payload** --- the {n_manifested} files
  collected from the repository --- with the size and SHA-256 of each.
* `GENERATED_MANIFEST.json` covers the **generated root entries**: this
  packager writes {n_unmanifested} of them at package time --- they are not
  collected from anywhere and are therefore absent from `MANIFEST.json` by
  construction --- and the manifest carries the size and SHA-256 of
  {n_unmanifested_hashed} of them, every one except itself.
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
field rather than in a document beside it: its rows are the {n_curated}
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
> **{n_exc_files} declared exception files**.  Those files retain
> **{n_exc_ctx}** matching contexts --- lines, or parsed JSON string leaves
> --- between them, containing **{n_exc_occ}** absolute-path occurrences;
> a single context can carry more than one path, which is why the two
> numbers differ and why each is reported under its own noun.  Each is
> enumerated and
> justified in `paper/is2/paper/BUILD_ENVIRONMENT.md` section 6.4 and in the
> `ABS_PATH_EXCEPTIONS` map of `make_release_zip.py`.  Outside them both
> counts are **zero**.
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
quantify over every file in the ZIP, leaves the generated root entries
outside the census -- and one of them, `pip-freeze-full.txt`, holds
{n_pipfreeze_occ} path-like strings.  The answer is the wider checker, not the narrower
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

The declared exceptions of this build, with the number of matching contexts
and the number of absolute-path occurrences retained in each:

| file | matching contexts | path occurrences |
|---|---|---|
{exc_rows}
| **total** | **{n_exc_ctx}** | **{n_exc_occ}** in **{n_exc_files}** files |

The wider statement -- that a repository sweep finds *zero* absolute paths in
the result JSONs -- is **not** made here, because it is **false** of the
unsanitized records: hundreds of absolute-path fields were present in the
result JSONs as produced, every one of them under the run host's scratch
prefix, together with build-machine paths in the analysis logs.  Those fields
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
| every curated number in BOTH documents | `paper/is2/tools/r9_reconcile.py` | exit status; {n_curated} claims, {n_construction} construction checks |
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
* The original record sets under `experiments/results/{{e2,e4,e5}}` are the
  per-episode / per-document raw result records, shipped unmodified.  Every
  re-analysis in `is_fresh` reads them; none rewrites them.  The E1 objects
  under `experiments/results/is_fresh/` are a different level -- per-cell
  simulation summaries -- and the subsection "Two levels of retained record"
  in `INDEX.md` says which is which and what each supports.
* Model checkpoints and corrupted-image tensors are NOT included (size); the
  training and data-preparation scripts that produce them are
  (`e2_cifar/train_source.py`, `e2_cifar/data.py`,
  `e4_gpt2/prepare_data.py`).
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


# NOT USED FOR THE SHIPPED ENTRIES, AND THAT IS THE POINT.  The four root
# entries BUILD_INTERPRETER.md, requirements-analysis.txt,
# requirements-experiment.txt and pip-freeze-full.txt are COPIED from
# `paper/is2/provenance/` by `provenance_entries()`, never rendered from the
# packaging interpreter -- see the long comment above `FROZEN_ARCHIVE` for
# why regenerating them would falsify them.  The renderers below
# (`build_interpreter_md`, `requirements_analysis_txt`,
# `requirements_experiment_txt`, `pip_freeze_full_txt`) are what PRODUCED
# those records on the build machine and are kept so the shipped files have a
# generator of record that a reader can inspect.  They are not called by
# `build()`.  Do not wire them back in.
#
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
    ("torch is needed by f6_relu_multiseed.py and f_scope_bench.py, which "
     "use it directly.  It is NOT needed by the rest of the re-analysis: "
     "core/utils.py imports it lazily, so common.py -> run_e1 -> core.utils "
     "no longer drags it in and the packager's default verification pass "
     "runs without it.  (That pass is the default; the only override is "
     "--no-verify.)  See COMMANDS.md.",
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
    # THE PIN IS RECORDED BY EXECUTION, SO A WRONG INTERPRETER REWRITES IT.
    # This function does not READ the pinned version, it PRINTS whichever
    # interpreter happens to be running -- so building the archive under, say,
    # the 3.14 that sits first on PATH would silently replace the documented
    # 3.10.9 pin with 3.14 everywhere, and every downstream document would
    # then be internally consistent and collectively wrong.  Refuse instead.
    # BUILD_ENVIRONMENT.md section 2 and BUILD_INTERPRETER.md are the two
    # places the pin is asserted; PINNED_PYTHON is the single value both
    # derive from.
    assert sys.version_info[:3] == PINNED_PYTHON, (
        f"this archive is built and verified on Python "
        f"{'.'.join(map(str, PINNED_PYTHON))}, but this process is "
        f"{'.'.join(map(str, sys.version_info[:3]))} ({sys.executable}). "
        f"Building here would rewrite the recorded interpreter pin to the "
        f"wrong version without any other check noticing.  Re-run with the "
        f"pinned interpreter.")
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
`paper/is2/paper/BUILD_ENVIRONMENT.md`, which ships in this archive and
covers both documents of the pair.
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


# --------------------------------------------------------------------------
# GENERATED_MANIFEST.json -- the second half of the audit boundary.
#
# THE AMBIGUITY THIS REMOVES.  MANIFEST.json covers the PAYLOAD -- the files
# collected from the repository -- and says so.  The generated root entries
# were therefore outside every manifest, disclosed in prose and nowhere else,
# which left a reader with a boundary they had to take on trust: "these seven
# documents are outside the manifest on purpose" is a sentence, not a check.
# GENERATED_MANIFEST.json makes the boundary machine-checkable.  Together the
# two manifests cover every entry of the ZIP except GENERATED_MANIFEST.json
# itself -- no manifest can carry its own hash -- and that one entry is
# authenticated the way the whole archive already was, by the ZIP's SHA-256
# published in the review manifest.
#
# It is DERIVED: it hashes the bytes actually written, in the same run that
# writes them.  Nothing about it is typed, including the list of entries it
# covers.
def generated_manifest(generated, stamp):
    """Size and SHA-256 of every generated root entry except this one."""
    entries = {}
    for rel, body in sorted(generated.items()):
        raw = body.encode("utf-8")
        entries[rel] = {"bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest()}
    return {
        "schema": "ttt-is2-generated-manifest/1",
        "built_utc": stamp.isoformat(),
        "what_this_is":
            "The generated root-level entries of this archive, with the size "
            "and SHA-256 of each.  These are produced by "
            "paper/is2/tools/make_release_zip.py at packaging time and are "
            "NOT collected from the repository, so they are deliberately "
            "absent from MANIFEST.json, which covers the payload.",
        "the_audit_boundary":
            "MANIFEST.json covers the payload; this file covers the "
            "generated root entries.  Between them every entry of the ZIP is "
            "manifested except this file, which cannot carry its own hash "
            "and is authenticated by the SHA-256 of the whole archive "
            "published in the review manifest.  There is no third category.",
        "self": "GENERATED_MANIFEST.json",
        "counterpart": "MANIFEST.json",
        "n_files": len(entries),
        "files": entries,
    }


def _n_string_leaves(obj):
    return sum(1 for _ in _json_string_leaves(obj))


def build(zip_path):
    files = collect()
    stamp = build_stamp()
    manifest = {"built_utc": stamp.isoformat(),
                "repo_relative_paths": True, "files": {}}
    total = 0
    for rel, full in files.items():
        size = os.path.getsize(full)
        total += size
        manifest["files"][rel] = {"bytes": size, "sha256": sha256(full)}
    manifest["n_files"] = len(files)
    manifest["total_bytes_uncompressed"] = total

    # The generated root entries are rendered FIRST, so the path-hygiene
    # census inside index_md() can cover them.  They were once outside the
    # census while the claim quantified over the whole ZIP; they are scanned
    # from these strings at build time and from the extracted tree at check
    # time, and both routes must agree.
    cmds = commands_md()
    generated = {
        "MANIFEST.json": json.dumps(manifest, indent=1, sort_keys=True),
        "SEEDS.md": SEEDS_MD,
        "COMMANDS.md": cmds,
        "AUDIT_MAP.json": json.dumps(audit_map(files, cmds, stamp), indent=1,
                                     sort_keys=True),
        **provenance_entries(),
    }
    # ORDER, AND THE ONE SELF-REFERENCE IN IT.  INDEX.md prints the census of
    # every ZIP entry, so it must know about GENERATED_MANIFEST.json, which
    # does not exist yet because it hashes INDEX.md.  The knot is untied by
    # the one quantity that does not depend on the hashes: the number of
    # STRING LEAVES of the generated manifest is fixed by the SET of entries
    # it covers, not by their digests.  So the manifest is built once with a
    # placeholder INDEX.md, its leaf count is handed to index_md(), and the
    # real manifest is asserted to have the same count.  A mismatch means the
    # census INDEX.md printed is not the census a reader's re-scan would
    # report, which is precisely the class of silently-false hygiene claim
    # this archive has produced before.
    _probe = generated_manifest({**generated, "INDEX.md": ""}, stamp)
    _n_gm_leaves = _n_string_leaves(_probe)
    index = index_md(files, zip_path, generated,
                     extra_json={"GENERATED_MANIFEST.json": _n_gm_leaves})
    generated["INDEX.md"] = index
    gm = generated_manifest(generated, stamp)
    assert _n_string_leaves(gm) == _n_gm_leaves, (
        f"GENERATED_MANIFEST.json has {_n_string_leaves(gm)} string leaves "
        f"but INDEX.md's census was written assuming {_n_gm_leaves}; the "
        f"printed coverage figures would not match a re-scan")
    gm_text = json.dumps(gm, indent=1, sort_keys=True)
    # It is inside the hygiene claim it helps to make, so it is checked
    # against that claim rather than assumed clean, exactly as INDEX.md is.
    _gm_hits = [ptr for ptr, s in _json_string_leaves(json.loads(gm_text))
                if _ABS_PATH_RE.search(s)]
    assert not _gm_hits, (
        f"GENERATED_MANIFEST.json carries an absolute path at {_gm_hits[:3]}")
    generated["GENERATED_MANIFEST.json"] = gm_text

    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    # DETERMINISM.  Every entry is stamped with the ONE timestamp above rather
    # than with each source file's own mtime, so a file that was merely
    # rewritten with identical content cannot change the archive's checksum.
    dt = stamp.timetuple()[:6]

    def _info(rel):
        i = zipfile.ZipInfo(rel, date_time=dt)
        i.compress_type = zipfile.ZIP_DEFLATED
        i.external_attr = 0o600 << 16
        return i

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for rel, full in files.items():
            with open(full, "rb") as fh:
                z.writestr(_info(rel), fh.read(), compresslevel=9)
        for rel, body in generated.items():
            z.writestr(_info(rel), body, compresslevel=9)
    return manifest


_SAVE_RE = re.compile(r"""st\.save\(\s*fig\s*,\s*["']([^"']+)["']""")
_OUT_RE = re.compile(r"""OUT_DEFAULT\s*=\s*\[?[^\n]*?/\s*["']([^"']+\.(?:pdf|tex))["']""")
# The is2 generators wrap their `OUT_DEFAULT` across two lines, so the pattern
# above -- deliberately line-bounded, to keep it from running away across a
# file -- cannot see them.  This one is applied to the whitespace-flattened
# source with a bounded window instead of an unbounded `.*?`.
_OUT_RE_WRAPPED = re.compile(
    r"""OUT_DEFAULT\s*=\s*\(?[^=]{0,200}?/\s*["']([^"']+\.(?:pdf|tex))["']""")
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

    # AND THE is2 GENERATORS OF RECORD.  Three of the fragments the two
    # documents typeset are generated here rather than in `is_fresh` --
    # S4_e1_gates.tex, S5_e2_batch.tex, S7_e4_proxy.tex -- each because the
    # is_fresh original produces the FROZEN tree's differently shaped table
    # and must not be repurposed.  That is precisely the arrangement this gate
    # exists to police, and until now it did not look here at all: a new is2
    # generator that claimed a basename an is_fresh generator already writes
    # would have been invisible to it.  Their `OUT_DEFAULT` is a wrapped
    # `Path` expression, so the line-bounded pattern above cannot see it; the
    # source is whitespace-flattened first and matched with a bounded window.
    is2 = os.path.join(tree, "paper", "is2", "tools")
    if os.path.isdir(is2):
        for fn in sorted(os.listdir(is2)):
            if not fn.endswith(".py"):
                continue
            src = open(os.path.join(is2, fn), encoding="utf-8",
                       errors="replace").read()
            for m in _OUT_RE_WRAPPED.finditer(" ".join(src.split())):
                add(m.group(1), f"paper/is2/tools/{fn}")
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

    # THE AUTHOR-DRAWN CLASS, ON THE OTHER SIDE OF THE SAME GATE.  Main
    # Figures 1-3 are schematics whose source of record is an `.svg`, not a
    # script (see MECHFIG_SOURCES).  Their absence from the generator map is
    # therefore CORRECT, and this gate must not be read as having overlooked
    # them.  What would be wrong is the converse: a generator that claimed one
    # of these basenames would silently replace author artwork with a plot on
    # the next bulk re-run of the figure directory -- the same failure mode
    # `_superseded/` exists to prevent, in the one direction the clash check
    # above cannot see, because a single claimant is not a clash.
    claimed = {n: outs[n] for n in MECHFIG_PDFS if n in outs}
    assert not claimed, (
        "a live generator writes an author-drawn mechanism figure: "
        + "; ".join(f"{k} <- {v}" for k, v in sorted(claimed.items()))
        + " -- these three PDFs are converted from the vector sources in "
        + MECHFIG_DIR_REL + " and no script may own their basenames")
    print(f"[release] no-collision gate OK ({len(outs)} distinct figure/table "
          f"outputs, {sum(len(v) for v in outs.values())} generators, "
          f"0 shared basenames; {len(MECHFIG_PDFS)} author-drawn figures "
          f"correctly claimed by none)")
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
# only, so the root-level generated entries -- among them BUILD_INTERPRETER.md,
# COMMANDS.md, INDEX.md, MANIFEST.json, SEEDS.md, pip-freeze-full.txt and the
# two requirements files -- were outside the census, and one of them,
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
    "paper/is2/paper/main.log":
        "verbatim pdflatex transcript; the '0 errors / 0 undefined / N "
        "pages' rows of BUILD_ENVIRONMENT.md section 3 are statements about "
        "THIS file and are read out of it by build_env_section3.py, so "
        "editing it would falsify it as a build record (MiKTeX and "
        "user-profile paths)",
    "paper/is2/supplement/supplement.log":
        "the same, for the second document of the pair; section 3 carries a "
        "supplement column and reads it out of this file",
    "paper/is2/paper/BUILD_ENVIRONMENT.md":
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
    #
    # The ImageNet-C runner's nine entries are gone from this map because the
    # runner itself is gone from the payload -- see DROPPED_PAYLOAD.  The gate
    # below asserts that every file named here still ships, so a stale
    # exemption cannot survive the removal of the file it exempted.
    "experiments/ttt/e2_cifar/adapt_cifar.py": "original GPU runner, as run",
    "experiments/ttt/e2_cifar/delta_feat.py": "original GPU runner, as run",
    "experiments/ttt/e2_cifar/train_source.py": "original GPU runner, as run",
    "experiments/ttt/e2_cifar/train_recon_head.py":
        "original GPU runner, as run",
    "experiments/ttt/e4_gpt2/run_e4.py": "original GPU runner, as run",
    "experiments/ttt/e4_gpt2/prepare_data.py": "original GPU runner, as run",
    "experiments/ttt/e4_gpt2/delta_proxy_v2.py":
        "original GPU runner, as run",
    "experiments/ttt/e4_gpt2/SMOKE.md":
        "remote-host smoke transcript, as run",
    "experiments/ttt/e4_gpt2/jobs_e4.txt":
        "literal command lines executed on the run host",
    # The theory-closure suite's path SANITIZER, whose docstring has to be
    # able to name the shape of path it removes in order to say what it does.
    # The suite's records and analysis jsons are clean precisely because this
    # function ran on them; the only absolute path in the whole closure
    # directory is the one inside the sentence explaining their absence.
    "experiments/results/is_fresh/closure/code/common.py":
        "the sanitizer's own docstring, naming the path shape it strips",
    # The E3 vector rerun's three driver scripts, on the same footing as the
    # runners above: each opens by setting the run host's root prefix, and each
    # ships as the record of what was executed on the RTX 3080 box.  Their
    # python siblings in the same directory carry no absolute path and are NOT
    # exempted -- the gate asserts that too, since an over-broad exemption is
    # the failure mode this map exists to prevent.
    "experiments/ttt/e4_gpt2/vec_rerun/run_all_e3.sh":
        "original GPU driver, as run",
    "experiments/ttt/e4_gpt2/vec_rerun/supervise_lanes.sh":
        "original GPU lane supervisor, as run",
    "experiments/ttt/e4_gpt2/vec_rerun/finalize_e3.sh":
        "original GPU finalization driver, as run",
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
    # The SAME BYTES, in the payload copy the packager reads.  The root entry
    # above is written from this file, so exempting one and not the other
    # would be exempting a file from itself.  The reason is identical and is
    # not restated in different words: a difference in wording between two
    # entries covering one object is a difference a reader has to adjudicate.
    "paper/is2/provenance/pip-freeze-full.txt":
        "the payload copy of the root entry above, byte-identical to it by "
        "construction; same reason, same paths, same evidentiary role",
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
    The generated root entries (COMMANDS.md, SEEDS.md, MANIFEST.json,
    AUDIT_MAP.json, GENERATED_MANIFEST.json, the two requirements files,
    pip-freeze-full.txt, BUILD_INTERPRETER.md and
    INDEX.md) are written straight into the ZIP by `build()` and have no file
    on disk at that moment, so at BUILD time they are censused from their
    strings and at CHECK time from the extracted tree.  Both routes visit the
    same bytes and report the same census; they were once outside the scan
    entirely, which is why they are explicitly in it now.
    Members named in `texts` are scanned instead of, not in addition to,
    `pathfor(rel)`, and `rels` must contain them.

    TWO COUNTS, NOT ONE.  A line, or a JSON string leaf, can contain more
    than one absolute path, so "how many contexts matched" and "how many
    paths are in them" are different numbers.  This census once returned only
    the first and every generated sentence called it "paths"; an independent
    re-implementation of the same recognizer using `findall` counts the
    second and gets a larger number, and it is the one that is right about
    the noun.  The defect was the label, not the scan, and the load-bearing
    "zero outside the declared exceptions" result cannot be affected by it,
    because a context count and an occurrence count are zero together.
    Both are now returned, under names that say which is which,
    and every generated sentence interpolates the one it names.
    """
    texts = texts or {}
    hits = []
    n_json = n_text = n_binary = n_shebang = 0
    n_json_leaves = 0
    exc_ctx = collections.Counter()      # matching lines / string leaves
    exc_occ = collections.Counter()      # absolute-path tokens inside them
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
                found = _ABS_PATH_RE.findall(s)
                if found:
                    if excepted:
                        exc_ctx[rel] += 1
                        exc_occ[rel] += len(found)
                    else:
                        hits.append((rel, ptr, s[:120]))
        else:
            n_text += 1
            for ln, line in enumerate(body.split("\n"), 1):
                if _SHEBANG_RE.match(line):
                    n_shebang += 1
                    continue
                found = _ABS_PATH_RE.findall(line)
                if found:
                    if excepted:
                        exc_ctx[rel] += 1
                        exc_occ[rel] += len(found)
                    else:
                        hits.append((rel, f"line {ln}",
                                     line.strip()[:120]))
    # An occurrence count can never be below its context count: a context is
    # in the census only because at least one path matched inside it.
    assert sum(exc_occ.values()) >= sum(exc_ctx.values()), \
        (dict(exc_occ), dict(exc_ctx))
    assert set(exc_occ) == set(exc_ctx), (sorted(exc_occ), sorted(exc_ctx))
    return {"hits": hits, "json_files": n_json, "json_leaves": n_json_leaves,
            "text_files": n_text, "binary_files": n_binary,
            "shebangs": n_shebang,
            "exception_contexts": dict(exc_ctx),
            "exception_occurrences": dict(exc_occ),
            "n_exception_files": len(ABS_PATH_EXCEPTIONS),
            "n_exception_contexts": sum(exc_ctx.values()),
            "n_exception_occurrences": sum(exc_occ.values()),
            "n_members": len(set(rels))}


def walk_tree(tree_root):
    """Every ARCHIVE ENTRY in an extracted archive, as sorted repo-relative
    POSIX -- and nothing an earlier command in the same recipe created.

    RUNTIME PRODUCTS ARE NOT ARCHIVE ENTRIES.  BUILD_ENVIRONMENT.md section
    6.0 prints a block that runs top to bottom, and one of its earlier steps
    imports two local modules, so CPython writes `tools/__pycache__/*.pyc`
    into the extracted tree before this census runs.  Walking them made the
    gate announce "ALL 516 archive entries" over an archive that ships 514,
    and the same recipe's generated section 6.4 says 514 two commands
    earlier -- a census contradicting the documentation it is supposed to
    certify, produced by the recipe itself.  `__pycache__` is pruned in
    place, so the walk descends into nothing that the ZIP does not carry.
    This mirrors SKIP_DIR_PARTS above, which prunes the same directory for
    the same reason on the packaging side.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(tree_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            out.append(os.path.relpath(p, tree_root).replace(os.sep, "/"))
    return sorted(out)


def check_no_absolute_paths(tree_root, manifest):
    """Fail unless the claim quoted above holds over EVERY archive entry.

    Iterating `manifest["files"]` would cover the payload only, while the
    claim this certifies quantifies over the whole ZIP.  It walks the
    extracted tree instead, so the generated root entries are inside the
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
    exc_hits = collections.Counter(cen["exception_contexts"])
    exc_occ = collections.Counter(cen["exception_occurrences"])
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
          f"{sum(exc_hits.values())} matching contexts in them containing "
          f"{sum(exc_occ.values())} path occurrences, each documented in "
          f"BUILD_ENVIRONMENT.md 6.4 "
          f"(contexts / occurrences per file below):")
    for r in sorted(ABS_PATH_EXCEPTIONS):
        print(f"[release]     {exc_hits[r]:4d} / {exc_occ[r]:4d}  {r}  -- "
              f"{ABS_PATH_EXCEPTIONS[r]}")
    return {k: v for k, v in cen.items() if k != "hits"}


def verify(zip_path, python=sys.executable, check_transcript=True):
    """Extract to a scratch dir and run nine reproduction checks.

    The nine, in the order they run (the four read-only ones first,
    deliberately): `tools/tab_s4_e1_gates.py --check`,
    `tools/tab_s5_e2_batch.py --check`, `tools/tab_s7_e4_proxy.py --check`,
    `tools/build_env_section3.py --check`, then
    `f7_curve_match.py`, `f11_e4_cluster_ci.py`, `f29_e4_pooled_ci.py`,
    `f31_e4_proxy_pooled.py` and `f8b_e2_crossfit_det.py`, the last five at
    reduced parameters and each writing under a `verify_*` name.  See
    VERIFICATION item 6 in the module docstring.

    ALL FOUR read-only checks run from `paper/is2/tools/` rather than from
    `is_fresh`: the three generated table/section artefacts this submission
    typesets have is2 generators of record, and pointing the verifier at the
    is_fresh originals would check the frozen tree's documents instead.

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

        # ---------------------------------------------------------------
        # VERIFY_TRANSCRIPT FRESHNESS, DERIVED RATHER THAN TRUSTED.
        #
        # The archive ships a long-form transcript of a verify() run and
        # presents it as documenting THIS archive.  A claim of that shape --
        # prose about a package, carrying hand-typed counts -- goes stale the
        # moment the payload set changes, and no build notices, because no
        # build reads it.
        #
        # The claim is now DERIVED.  The transcript states its own counts in
        # machine-emitted lines; those lines are parsed here out of the
        # EXTRACTED copy and compared with what this very archive contains.
        # A transcript describing a different package fails the build that
        # would ship it, which is the only moment at which the mismatch is
        # cheap to fix.  This is the same discipline as the docstring binder
        # at the bottom of this function: a hand-typed number about a machine
        # fact is bound to the machine fact.
        #
        # NOTE ON THE SELF-REFERENCE.  A ZIP cannot contain a transcript of a
        # run against itself -- adding the transcript changes the bytes that
        # were hashed -- so the transcript records the immediately preceding
        # build, which differs from this one in the transcript file ALONE.
        # The payload COUNT and the entry COUNT are therefore identical
        # across the two, which is exactly why counts, and not digests, are
        # what this gate binds.
        # `check_transcript=False` is used by --write-verify-transcript, and
        # only there: that mode RUNS this function in order to produce the
        # transcript, so it cannot also require the transcript it is about to
        # replace to be current.  Every other caller leaves the gate armed.
        if check_transcript:
            _tr_rel = "experiments/ttt/is_fresh/VERIFY_TRANSCRIPT.md"
            _tr_path = os.path.join(tmp, _tr_rel.replace("/", os.sep))
            assert os.path.exists(_tr_path), (
                f"{_tr_rel} did not ship, but the archive documentation says it "
                f"carries a complete verify() run")
            _tr = open(_tr_path, encoding="utf-8").read()
            _m = re.search(r"manifest round-trip OK \((\d+) files, (\d+) zip "
                           r"entries\)", _tr)
            assert _m, (
                f"{_tr_rel} carries no machine-emitted 'manifest round-trip OK' "
                f"line, so its currency cannot be checked; regenerate it with "
                f"--write-verify-transcript")
            _tr_files, _tr_entries = int(_m.group(1)), int(_m.group(2))
            assert (_tr_files, _tr_entries) == (len(man["files"]), len(names)), (
                f"{_tr_rel} is STALE: it documents a package of {_tr_files} "
                f"payload files in {_tr_entries} ZIP entries, but this archive "
                f"has {len(man['files'])} payload files in {len(names)} ZIP "
                f"entries.  Regenerate it from a real run against the current "
                f"archive (--write-verify-transcript); do not edit the numbers "
                f"by hand")
            # The same counts are restated in the transcript's own prose table.
            # Bind those too -- the prose is what a reader actually reads, and it
            # is the half that went stale before.
            for _n, _what in ((_tr_files, "payload files"),
                              (_tr_entries, "entries")):
                assert re.search(rf"\b{_n}\b\s+{_what}", _tr) or \
                       re.search(rf"all\s+{_n}\s+{_what}", _tr), (
                    f"{_tr_rel}'s prose does not state '{_n} {_what}', so the "
                    f"prose and the machine output it contains disagree; "
                    f"regenerate the transcript")
            _m2 = re.search(r"(\d+) declared exceptions", _tr)
            assert _m2 and int(_m2.group(1)) == len(ABS_PATH_EXCEPTIONS), (
                f"{_tr_rel} records "
                f"{_m2.group(1) if _m2 else 'no'} declared path exceptions but "
                f"this build declares {len(ABS_PATH_EXCEPTIONS)}")
            print(f"[release] VERIFY_TRANSCRIPT.md is current "
                  f"({_tr_files} payload files, {_tr_entries} entries, "
                  f"{len(ABS_PATH_EXCEPTIONS)} declared path exceptions)")

        # STAGING-COPY IDENTITY GATE.  COMMANDS.md says the repository-level
        # staging file and the paper copy "are byte-identical in this
        # archive".  Check that inside the extracted tree, so the sentence is
        # verified by the reader's own copy rather than asserted.
        for rel in STAGING_FILES:
            a = os.path.join(tmp, rel.replace("/", os.sep))
            b = os.path.join(tmp, PAPER_REL.replace("/", os.sep),
                             rel.replace("/", os.sep))
            assert os.path.exists(a), f"{rel} did not ship"
            assert os.path.exists(b), f"paper copy of {rel} did not ship"
            assert sha256(a) == sha256(b), (
                f"{rel} and its paper copy are not byte-identical in the "
                f"archive")
        print(f"[release] staging/paper byte-identity OK for all "
              f"{len(STAGING_FILES)} original generator outputs")

        wd = os.path.join(tmp, "experiments", "ttt", "is_fresh")
        wd2 = os.path.join(tmp, "paper", "is2", "tools")

        # D6, OVER THE FINISHED ARCHIVE.  `collect()` asserts the same thing
        # over the payload before the ZIP is written; this repeats it over
        # every entry a reader actually receives, because the property that
        # matters is a property of the delivered file and not of the list the
        # builder held in memory.
        d6 = [n for n in names if os.path.basename(n) == D6_REQUIRED]
        assert d6, (
            f"{D6_REQUIRED} is missing from the archive; the supplement "
            f"points at it as a release visualization")
        print(f"[release] D6 inclusion OK: {len(d6)} member(s) named "
              f"{D6_REQUIRED}")

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
            ("table regeneration (supplement S4 --check against the "
             "shipped .tex)",
             [python, os.path.join(wd2, "tab_s4_e1_gates.py"), "--check"]),
            # The E2 batch-mechanics table.  It carries scientific evidence
            # the supplement typesets -- the accuracy sign against batch size
            # and the 1/N dispersion reading -- so it is generated from the
            # per-batch records under the same byte comparison as S4 rather
            # than typed.
            ("table regeneration (supplement S5 --check against the "
             "shipped .tex)",
             [python, os.path.join(wd2, "tab_s5_e2_batch.py"), "--check"]),
            # S7 is the per-domain E4 proxy table Section 7.4 promises, so
            # the appendix has to contain it.  Its caption carries the
            # favourable-side and adverse-side exclusion counts, so this
            # check also binds the "1 of 4" census against the record that
            # a "0 of 4" summary would contradict.
            # IT RUNS FROM `paper/is2/tools` AND NEEDS NO --out.  This check
            # used to invoke the frozen tree's `tab_t6_e4_proxy.py` with an
            # explicit --out into the is2 tree, because one generator owned
            # two tables in two trees and its default target was the frozen
            # one.  That arrangement compared only NUMERIC TOKENS, so the is2
            # copy's labels, symbols and caption had drifted away from the
            # generator entirely, and it also made the table unrestructurable:
            # relaying out the columns rewrote the frozen tree's artefact.
            # The is2 table now has its own generator of record, whose
            # --check is a byte comparison and whose default output is the
            # copy the supplement includes.
            ("table regeneration (supplement S7 --check against the "
             "shipped .tex)",
             [python, os.path.join(wd2, "tab_s7_e4_proxy.py"), "--check"]),
            # BUILD_ENVIRONMENT.md section 3 is interpolated from main.pdf,
            # main.log, main.tex and main.bbl.  It has carried a
            # one-build-stale size and checksum for two of them; this check
            # makes that state unpackageable.
            ("generated BUILD_ENVIRONMENT.md section 3 (--check)",
             [python, os.path.join(wd2, "build_env_section3.py"), "--check"]),
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


VERIFY_TRANSCRIPT_REL = "experiments/ttt/is_fresh/VERIFY_TRANSCRIPT.md"


def write_verify_transcript(zip_path):
    """Run verify() for real and WRITE the long-form transcript from that run.

    WHY THIS IS A MODE OF THIS SCRIPT AND NOT A SEPARATE TOOL.  The transcript
    is a document about what this function does; generating it anywhere else
    would reintroduce exactly the drift the currency gate in verify() exists
    to catch, because the counts would again be produced by something other
    than the thing being described.  Here the prose counts and the machine
    output come from ONE run and cannot disagree.

    THE ORDER THIS IS MEANT TO BE RUN IN.  A ZIP cannot contain a transcript
    of a run against itself: writing the transcript changes the bytes that
    were hashed.  So:

        1.  build with --no-verify            (archive A)
        2.  --write-verify-transcript A       (transcript describes A)
        3.  build again                       (archive B, ships that
                                               transcript; verify() runs and
                                               its currency gate passes,
                                               because A and B differ in the
                                               transcript alone and therefore
                                               have identical counts)

    That is why the gate binds COUNTS and not digests.
    """
    import contextlib
    import datetime
    import platform as _p

    assert sys.version_info[:3] == PINNED_PYTHON, (
        f"the transcript records the interpreter it ran on; run it on the "
        f"pinned Python {PINNED_PYTHON_STR}, not "
        f"{'.'.join(map(str, sys.version_info[:3]))}")

    started = datetime.datetime.now(datetime.timezone.utc)
    buf = io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stdout(buf):
        verify(zip_path, check_transcript=False)
    elapsed = time.time() - t0
    finished = datetime.datetime.now(datetime.timezone.utc)
    run = buf.getvalue().rstrip("\n")
    # The one line the currency gate parses must be present, or the transcript
    # we are about to write could not be checked against any future archive.
    m = re.search(r"manifest round-trip OK \((\d+) files, (\d+) zip entries\)",
                  run)
    assert m, "verify() did not emit its manifest round-trip line"
    n_files, n_entries = int(m.group(1)), int(m.group(2))
    m2 = re.search(r"COMMANDS\.md accounts for all (\d+) is_fresh scripts", run)
    n_scripts = int(m2.group(1)) if m2 else None
    n_exc = len(ABS_PATH_EXCEPTIONS)
    zb = os.path.getsize(zip_path)

    body = f"""# VERIFY_TRANSCRIPT — a complete `verify(zip)` run on the pinned interpreter

## What this file is

A verbatim transcript of `make_release_zip.verify()` executed against this
archive from a **clean extraction**, on the **pinned Python {PINNED_PYTHON_STR}** named in
`BUILD_INTERPRETER.md` and in `BUILD_ENVIRONMENT.md` §2 — captured with its
standard output, its wall-clock duration and its **process exit code**, so that
the statement "the archive verifies" can be read as a machine result rather
than taken on trust.

The result is at the bottom of the transcript: **exit code 0**, {elapsed:.1f} s.

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
| **FULL** | **Integrity and documentation.** All {n_files} payload files re-hash to their `MANIFEST.json` entries from the clean extraction; the staging/paper generator outputs are byte-identical inside the tree; `COMMANDS.md` accounts for all {n_scripts} analysis scripts and repeats no command line; no two live generators collide on an output basename; the absolute-path gate passes over all {n_entries} entries, with {n_exc} declared exceptions. |
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
interpreter: {sys.version.splitlines()[0]}
executable: python.exe
platform  : {_p.platform()}
zip       : {os.path.basename(zip_path)}
zip bytes : {zb}
zip sha256: {sha256(zip_path)}
started   : {started.strftime('%Y-%m-%dT%H:%M:%S')} UTC
----------------------------------------------------------------------
{run}
----------------------------------------------------------------------
finished  : {finished.strftime('%Y-%m-%dT%H:%M:%S')} UTC
elapsed   : {elapsed:.1f} s
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
"""
    out = os.path.join(REPO, VERIFY_TRANSCRIPT_REL.replace("/", os.sep))
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print(f"[release] wrote {VERIFY_TRANSCRIPT_REL} from a real verify() run "
          f"({n_files} payload files, {n_entries} entries, {n_scripts} "
          f"scripts, {n_exc} declared exceptions, {elapsed:.1f} s)")
    return out


def self_rebuild_check():
    """Prove this script can rebuild from wherever it is, WITHOUT writing.

    WHAT IT ESTABLISHES.  The two things whose absence made the packager
    unrunnable from its own release, and nothing more:

      1. `provenance_entries()` RESOLVES -- the four dependency-provenance
         records are readable from `paper/is2/provenance/`, are non-empty, and
         (only when the frozen archive happens to be present) still match it;
      2. the PAYLOAD MAP IS SATISFIABLE -- `collect()` walks the tree and
         every file it names exists, including the provenance directory it
         must ship for (1) to hold in the NEXT extraction.

    WHAT IT DELIBERATELY DOES NOT DO.  It builds no ZIP and runs no
    reproduction check.  Those need the built PDFs, the LaTeX transcripts and
    twenty minutes; this needs neither, so it can run in a gate on every
    commit.  A gate nobody runs is a gate that does not exist.

    Returns a dict of counts.  Raises on failure, like every other gate here.
    """
    prov = provenance_entries()
    assert set(prov) == set(PROVENANCE_ENTRIES), (
        f"provenance_entries() returned {sorted(prov)}, expected "
        f"{sorted(PROVENANCE_ENTRIES)}")
    files = collect()
    missing = [rel for rel, full in files.items() if not os.path.exists(full)]
    assert not missing, (
        f"the payload map names {len(missing)} file(s) that do not exist, so "
        f"a rebuild from here would fail: {missing[:5]}")
    shipped_prov = sorted(r for r in files
                          if r.startswith(f"{PROVENANCE_REL}/"))
    print(f"[release] self-rebuild check: provenance_entries() resolved "
          f"{len(prov)} records "
          f"({sum(len(v) for v in prov.values())} chars) from "
          f"{PROVENANCE_REL}/")
    print(f"[release] self-rebuild check: payload map satisfiable, "
          f"{len(files)} files, all present")
    print(f"[release] self-rebuild check: {len(shipped_prov)} provenance "
          f"file(s) ship in the payload, so the NEXT extraction can do this "
          f"too")
    print(f"[release] self-rebuild check: frozen paper/is/ archive "
          f"{'present (integrity cross-check ran)' if os.path.exists(FROZEN_ARCHIVE) else 'ABSENT (not required)'}")
    return {"provenance_records": len(prov), "payload_files": len(files),
            "provenance_shipped": len(shipped_prov)}


def main():
    ap = argparse.ArgumentParser(
        description="Build and verify the auditability archive.  "
                    "VERIFICATION RUNS BY DEFAULT; --no-verify turns it off.  "
                    "There is no --verify switch, because there is nothing "
                    "for it to turn on.")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the verification pass, which otherwise runs by "
                         "default after the archive is written")
    ap.add_argument("--write-verify-transcript", action="store_true",
                    help="run verify() for real against the built "
                         "archive and regenerate "
                         "experiments/ttt/is_fresh/VERIFY_TRANSCRIPT.md "
                         "from that run; see write_verify_transcript()")
    ap.add_argument("--self-rebuild-check", action="store_true",
                    help="resolve the provenance entries and the payload map "
                         "and report whether a rebuild from THIS tree would "
                         "succeed; writes nothing, builds no ZIP, needs no "
                         "frozen parent archive.  This is the mode the "
                         "release gate runs from a clean extraction")
    ap.add_argument("--check-paths", metavar="TREE", default=None,
                    help="run ONLY the absolute-path gate against an already "
                         "extracted archive TREE (the directory containing "
                         "MANIFEST.json); writes nothing")
    args = ap.parse_args()

    if args.self_rebuild_check:
        self_rebuild_check()
        print("[release] SELF-REBUILD CHECK PASSED")
        return

    if args.write_verify_transcript:
        # Runs against the archive ALREADY on disk, deliberately: this mode
        # documents an existing build rather than making a new one, which is
        # what lets the next build ship a transcript of its predecessor.
        write_verify_transcript(args.out)
        return

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
    main()
