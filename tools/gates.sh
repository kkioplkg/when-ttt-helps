#!/usr/bin/env bash
# Manuscript gates for paper/is2.  Adapted from paper/BUILD_ENVIRONMENT.md
# sections 6, 6.1 and 6.3, with the source-hygiene sweeps that accompany them.
# Run from anywhere; paths are resolved from this script's own location.
#
#   1. build gate          0 LaTeX errors, 0 undefined references/citations
#   2. ref-artefact gate   no rendered `ef{`/`qref{`/`ite{`/`abel{` and no `??`
#   3. leak gate           the hard phrase set of BUILD_ENVIRONMENT.md 6.3,
#                          over the RENDERED text of both PDFs
#   4. stray-CR sweep      no CR outside a CRLF pair in any .tex/.bib/.md/.txt
#   5. duplicate-line gate no consecutive duplicated non-blank source line
#   6. tab gate            no literal TAB in any .tex source
#   6a. same-statement gate  no statement is numbered by BOTH documents
#                          without an `%% inv: restates <label>' annotation
#                          naming its article counterpart.  Every other gate
#                          checks one document against itself or against a
#                          list; this one compares the two trees' statement
#                          bodies, which is the only way a statement printed
#                          twice -- once per document, under different labels
#                          -- becomes visible.
#   7. release self-rebuild gate
#                          BOTH commands that BUILD_ENVIRONMENT.md section 6.0
#                          prints for a reader -- the packaging utility and the
#                          number reconciliation -- must run from a CLEAN
#                          EXTRACTION of release_archive.zip, with no access
#                          to anything outside it.  Neither once could.  The
#                          reconciler bound a claim to a GPU staging file the
#                          release does not ship, read the absent file as empty
#                          and failed the claim, so the archive's own
#                          documented verification exited 1 for every reader
#                          who ran it as printed -- and passed here, because
#                          here the staging tree exists.  The packager read
#                          four dependency-provenance entries out of the frozen
#                          `paper/is/release_archive.zip`, which the release
#                          does not ship, so the documented default command
#                          died from an extracted release and the archive
#                          could not rebuild itself.  Gates 1-6 could not see
#                          that: they are gates on the manuscript, and this is
#                          a gate on the artefact the manuscript ships with.
#   8. review standalone build
#                          BOTH documents must compile from a clean
#                          extraction of the review ZIP.  The package's file
#                          lists are hand lists and every other check on them
#                          compares the lists with something derived from the
#                          lists, so a forgotten file is invisible to all of
#                          them.  Two supplement \input's were forgotten and
#                          the shipped supplement source did not compile.
#
# Every count below is expected to be 0.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."
cd "$ROOT"

count()  { grep -c  "$@" || true; }
countE() { grep -cE "$@" || true; }
countP() { LC_ALL=C.UTF-8 grep -ciP "$@" || true; }

LEAK='referee|reviewer|earlier form of this|(?<![A-Za-z])rounds?\b(?!ed|ing)|external review|this round|last round|this revision|previous version|earlier versions?|earlier revisions?|earlier draft|prior version|we previously'

fail=0
skipped=0
chk() { # name expected actual
  if [ "$2" != "$3" ]; then echo "FAIL  $1: expected $2, got $3"; fail=1;
  else echo "ok    $1: $3"; fi
}

echo "=== 1. build gate ==="
chk "main: LaTeX errors"            0 "$(count '^!' paper/main.log)"
chk "main: undefined refs/cites"    0 "$(countE 'undefined (references|citations)' paper/main.log)"
chk "main: 'There were undefined'"  0 "$(count 'There were undefined' paper/main.log)"
chk "supp: LaTeX errors"            0 "$(count '^!' supplement/supplement.log)"
chk "supp: undefined refs/cites"    0 "$(countE 'undefined (references|citations)' supplement/supplement.log)"
echo "main pages:  $(pdfinfo paper/main.pdf | awk '/^Pages/{print $2}')"
echo "supp pages:  $(pdfinfo supplement/supplement.pdf | awk '/^Pages/{print $2}')"

# Scratch under a mktemp directory, not a fixed machine path: this script
# ships inside release_archive.zip, whose absolute-path gate treats a fixed
# scratch prefix as a machine path and would need eight declared exceptions.
TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT
pdftotext -layout paper/main.pdf - > "$TMPD/is2_main.txt" 2>/dev/null
pdftotext -layout supplement/supplement.pdf - > "$TMPD/is2_supp.txt" 2>/dev/null

echo "=== 2. rendered cross-reference artefact gate ==="
chk "main: ef{/qref{/ite{/abel{" 0 "$(countE '(^|[^A-Za-z])(ef|qref|ite|abel)\{' "$TMPD/is2_main.txt")"
chk "main: ??"                   0 "$(count -F '??' "$TMPD/is2_main.txt")"
chk "supp: ef{/qref{/ite{/abel{" 0 "$(countE '(^|[^A-Za-z])(ef|qref|ite|abel)\{' "$TMPD/is2_supp.txt")"
chk "supp: ??"                   0 "$(count -F '??' "$TMPD/is2_supp.txt")"
# DOUBLED LABEL WORDS.  Every `\MainXxx` cross-document macro already expands
# to "Section~6.3", "Table~S3", "Definition~4"; writing `Section~\MainSecEthree`
# therefore renders "Section Section 6.3".  Nine of those shipped, in a
# supplement whose every other cross-reference is generated.  The defect is
# invisible in the source -- each half is correct on its own -- and visible in
# one grep of the rendered text, which is where this gate lives.
LBL='Section|Table|Figure|Remark|Theorem|Corollary|Proposition|Lemma|Definition|Assumption|Appendix|Equation'
chk "main: doubled label word" 0 "$(countE "($LBL) ($LBL)" "$TMPD/is2_main.txt")"
chk "supp: doubled label word" 0 "$(countE "($LBL) ($LBL)" "$TMPD/is2_supp.txt")"

echo "=== 3. review-process leak gate (hard set, rendered PDFs) ==="
chk "main: leak hits" 0 "$(countP "$LEAK" "$TMPD/is2_main.txt")"
chk "supp: leak hits" 0 "$(countP "$LEAK" "$TMPD/is2_supp.txt")"

echo "=== 4/5/6. source hygiene (stray CR, duplicate line, tab) ==="
python "$HERE/source_hygiene.py"
rc=$?
[ $rc -ne 0 ] && fail=1

echo "=== 6a. same-statement-in-both-documents gate ==="
# Gates 1-6 are gates on ONE document, or on a list against one document.
# None of them can see a statement that both documents number, because each
# document is internally consistent about its own copy.  This one compares
# the two trees' statement bodies and requires every nontrivial cross-document
# match to be DECLARED as a restatement.
python "$HERE/dup_statement_gate.py"
rc=$?
[ $rc -ne 0 ] && fail=1

echo "=== 7. release self-rebuild gate ==="
# 7.1  THE PACKAGER MUST RESOLVE FROM WHEREVER IT SITS.  --self-rebuild-check
#      resolves the four dependency-provenance records and the whole payload
#      map and writes nothing, so it costs seconds and can run every time.
#      In an extracted release this is already the real test; in the source
#      tree it is the cheap half, and 7.2 below is the real one.
python "$HERE/make_release_zip.py" --self-rebuild-check > "$TMPD/srb_here.log" 2>&1
chk "packager resolves in this tree" 0 "$?"
[ -s "$TMPD/srb_here.log" ] && sed 's/^/      /' "$TMPD/srb_here.log"

# 7.2  THE GATE THAT CATCHES THE CLASS OF DEFECT.  Extract the release, prove
#      the extraction contains no `paper/is/` at all, drop the CURRENT
#      packager and provenance directory into it, and run the packager THERE.
#      Overlaying the current tools is deliberate: without it this gate tests
#      whichever packager was shipped last, and a dependency reintroduced in
#      the working tree would pass until somebody rebuilt.  With it, the gate
#      goes red in the same commit that reintroduces the dependency -- which
#      is the only time a gate is worth having.
REL="$ROOT/release_archive.zip"
if [ -f "$REL" ]; then
  XD="$TMPD/rel"
  mkdir -p "$XD"
  python -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
      "$REL" "$XD" 2>"$TMPD/extract.err"
  chk "release archive extracts" 0 "$?"
  # The crux: the extracted release must NOT contain the frozen parent tree,
  # so a packager that needs it cannot possibly find it here.
  chk "extraction carries no paper/is/" 0 \
      "$( [ -e "$XD/paper/is" ] && echo 1 || echo 0 )"
  cp "$HERE"/*.py "$HERE"/*.sh "$XD/paper/is2/tools/" 2>/dev/null
  mkdir -p "$XD/paper/is2/provenance"
  cp "$ROOT/provenance/"* "$XD/paper/is2/provenance/" 2>/dev/null
  ( cd "$XD/paper/is2" && python tools/make_release_zip.py --self-rebuild-check ) \
      > "$TMPD/srb_ext.log" 2>&1
  chk "packager runs from a clean extraction" 0 "$?"
  sed 's/^/      /' "$TMPD/srb_ext.log" | tail -8

  # 7.2b  THE OTHER COMMAND THE ARCHIVE TELLS A READER TO RUN.
  #       BUILD_ENVIRONMENT.md section 6.0 prints exactly two verification
  #       commands: gates.sh and `python paper/is2/tools/r9_reconcile.py`.
  #       Until now only the FIRST was ever executed from an extraction, and
  #       the second was not: the reconciler bound a construction to
  #       experiments/results/is_fresh_incoming_gpu/PROVENANCE.md, a working-
  #       tree integration source the release deliberately does not ship, read
  #       the absent file as the empty string, and failed the claim -- so the
  #       archive's own documented reconciliation exited 1 for every reader who
  #       ran it as printed, while passing here.  This costs one command on an
  #       extraction that already exists, and it is the only check that can see
  #       a reconciler which depends on something outside the archive.
  ( cd "$XD" && python paper/is2/tools/r9_reconcile.py ) \
      > "$TMPD/rec_ext.log" 2>&1
  chk "reconciler runs from a clean extraction" 0 "$?"
  grep -E 'GPU staging|construction claims|^RESULT' "$TMPD/rec_ext.log" \
      | sed 's/^/      /'

  # 7.2c  AND THE THREE GENERATED-TABLE CHECKS FROM THE SAME PRINTED BLOCK.
  #       The proxy table's check once defaulted its output path to the FROZEN
  #       tree's copy, which the release does not ship, so it died with a
  #       FileNotFoundError from an extraction while passing here.  Same
  #       defect class as 7.2b, same printed reader recipe, same one-line fix
  #       on an extraction that already exists.
  #       The proxy table's check now runs the is2 GENERATOR OF RECORD.  It
  #       used to run `experiments/ttt/is_fresh/tab_t6_e4_proxy.py`, a
  #       generator shared with the frozen tree: its `--check` compared only
  #       numeric tokens, so every label, symbol and caption sentence in the
  #       is2 copy had drifted away from it unnoticed, and the shared layout
  #       could not be changed without rewriting a frozen artefact.
  #       `tools/tab_s7_e4_proxy.py` owns the is2 table and its `--check` is a
  #       byte comparison, like S4's and S5's.
  ( cd "$XD" && python paper/is2/tools/tab_s4_e1_gates.py --check ) \
      > "$TMPD/t4_ext.log" 2>&1
  chk "exact-model gate table --check from a clean extraction" 0 "$?"
  ( cd "$XD" && python paper/is2/tools/tab_s5_e2_batch.py --check ) \
      > "$TMPD/t5_ext.log" 2>&1
  chk "batch-mechanics table --check from a clean extraction" 0 "$?"
  ( cd "$XD" && python paper/is2/tools/tab_s7_e4_proxy.py --check ) \
      > "$TMPD/t6_ext.log" 2>&1
  chk "proxy table --check from a clean extraction" 0 "$?"
  tail -1 "$TMPD/t6_ext.log" | sed 's/^/      /'
  # 7.3  AND THE SHIPPED ARTEFACT MUST ALREADY CARRY WHAT 7.2 OVERLAID.  If
  #      this line is red the code is fine and the built archive is stale:
  #      rebuild release_archive.zip.
  chk "built archive is current: carries provenance/ (0 => rebuild it)" 4 \
      "$(python -c "import sys,zipfile
z=zipfile.ZipFile(sys.argv[1])
n=set(z.namelist())
print(sum(1 for e in ('BUILD_INTERPRETER.md','requirements-analysis.txt','requirements-experiment.txt','pip-freeze-full.txt') if 'paper/is2/provenance/'+e in n))" "$REL")"
else
  echo "skip  release self-rebuild (extraction): no $REL beside this tree"
  skipped=$((skipped+1))
fi

echo "=== 8. review-package standalone build gate ==="
# The review package's file lists are HAND LISTS, and every other check on
# them is a check between the lists and something derived from the lists, so
# a file the lists FORGOT is invisible to all of them: it is absent from both
# sides of every comparison.  Two supplement \input's were omitted exactly
# that way and the shipped package's supplement source could not be compiled
# at all.  Compiling BOTH documents out of a clean extraction of the built ZIP
# is the check that sees it.  It needs a built package, so it is skipped
# (loudly) when the tag's ZIP is not beside this tree.
REVIEW_TAG="${REVIEW_TAG:-}"
if [ -z "$REVIEW_TAG" ]; then
  REVIEW_TAG="$(ls "$ROOT"/review_is2_r*.zip 2>/dev/null | sed 's#.*/review_##; s#\.zip$##' \
                | sort -V | tail -1)"
fi
if [ -n "$REVIEW_TAG" ] && [ -f "$ROOT/review_$REVIEW_TAG.zip" ]; then
  python "$ROOT/make_review_zip.py" --tag "$REVIEW_TAG" \
      --standalone-build-check > "$TMPD/standalone.log" 2>&1
  chk "review_$REVIEW_TAG.zip builds standalone (both documents)" 0 "$?"
  sed 's/^/      /' "$TMPD/standalone.log" | tail -4
else
  echo "skip  standalone build: no review_*.zip beside this tree"
  skipped=$((skipped+1))
fi

echo
# THE SUMMARY LINE MUST NOT BE STRONGER THAN WHAT RAN.  Two gates need a
# sibling ZIP and are skipped when it is absent -- which is exactly what a
# reader running this from a clean extraction of the release sees, since the
# release does not ship the ZIPs.  Printing "ALL GATES GREEN" there claimed
# more than had been executed.  The count of skipped gates is now carried into
# the summary, so a run that could not do everything says so on the line a
# reader quotes.
if [ $fail -ne 0 ]; then
  echo "GATES FAILED"
elif [ $skipped -eq 0 ]; then
  echo "ALL GATES GREEN"
else
  echo "ALL GATES GREEN THAT COULD RUN HERE ($skipped skipped for want of a"
  echo "sibling ZIP; see the 'skip' lines above.  A clean extraction of the"
  echo "release ships no ZIPs, so those two are expected to skip there.)"
fi
exit $fail
