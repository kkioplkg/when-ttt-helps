#!/usr/bin/env python
"""Fail when one numbered statement is printed by BOTH documents undeclared.

WHY THIS EXISTS
---------------
A round of edits promoted several article statements to numbered supplement
environments with `-s` labels, repointed the article's references at them, and
deleted the article originals.  A concurrent edit to the same file restored an
older copy of it, which silently put the article originals back.  The result
was three statements numbered twice -- once in each document -- and EVERY GATE
WAS GREEN, each for a good reason:

  * LaTeX raises nothing, because the two copies carry different labels
    (`rem:sliver` and `rem:sliver-s`) in two separately compiled documents;
  * the numerical reconciliation keys on printed literals over the UNION of
    both trees, so a duplicated numeral reclassifies from `main` to `both`
    instead of orphaning;
  * the supplement's self-inventory counts ANNOTATIONS, and the annotations
    were present -- they were just wrong, saying `supplement-only` of a
    statement the article also printed.

The common blind spot is that no gate compared the two documents' STATEMENTS.
Each checked a document, or checked a list against a document.  This one
compares the bodies.

WHAT IT CHECKS
--------------
1. BODY SIMILARITY.  Every theorem-like environment in the article and in the
   supplement is reduced to a normalized body -- comments, labels and the
   ARGUMENTS of every cross-reference command removed, whitespace collapsed --
   and every cross-document pair is scored.  A pair that scores at or above
   --threshold on bodies of at least --min-chars is a nontrivial match.

   A nontrivial match is NOT an error by itself: a supplement that restates an
   article result in full before proving it is doing its job, and this
   supplement says in its front matter exactly how many of its statements do
   that.  What is an error is an UNDECLARED one.  So a flagged pair must carry
   `%% inv: restates <article-label>` naming that very statement.  Annotated
   `supplement-only`, or annotated as restating something else, and the gate
   fails.

   That is also the check that makes the generated inventory semantically
   honest rather than merely present: the inventory generator verifies that an
   annotation EXISTS, and this gate verifies that it is TRUE.

2. THE `-s` SUFFIX CONVENTION.  Independently of any text comparison: if the
   article defines `<key>` and the supplement defines `<key>-s`, the two are
   the same statement by the naming convention this project uses, so the
   supplement one must declare `restates <key>`.  This is the cheap check the
   incident report asked for, and it catches a pair that has been reworded far
   enough to fall under the similarity threshold.

Exit status 0 when both checks pass.

Usage:
  python dup_statement_gate.py                 # gate both trees
  python dup_statement_gate.py --show 12       # also print the top pairs
"""
from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "paper" / "is2"
PAPER = ROOT / "paper"
SUPP = ROOT / "supplement"

BS = chr(92)
ENVS = ("theorem", "lemma", "proposition", "corollary", "definition",
        "remark", "assumption", "example", "conjecture", "axiom")
BEGIN = re.compile(BS + BS + r"begin\{(" + "|".join(ENVS) + r")\}")
END_OF = {e: re.compile(BS + BS + r"end\{" + e + r"\}") for e in ENVS}
LABEL = re.compile(BS + BS + r"label\{([^}]+)\}")
ANN = re.compile(r"^%% inv: (supplement-only|restates ([A-Za-z0-9:_-]+))\s*$")

# Cross-reference commands whose ARGUMENT is a label and therefore differs
# between the two documents by construction.  Their arguments are erased so
# that `\ref{cor:flow}` and `\ref{cor:flow-s}` do not make two copies of one
# statement look different.  `\Main...` macros are the supplement's named
# lookups of article objects and are erased whole for the same reason.
REFCMD = re.compile(
    BS + BS + r"(?:s|m|)(?:ref|eqref|qref)\{[^}]*\}|"
    + BS + BS + r"Main[A-Za-z]+\{?\}?")
COMMENT = re.compile(r"(?<!" + BS + BS + r")%.*$")


def normalize(body: str) -> str:
    """The comparable text of a statement body."""
    lines = [COMMENT.sub("", ln) for ln in body.split("\n")]
    txt = " ".join(lines)
    txt = LABEL.sub(" ", txt)
    txt = REFCMD.sub(" ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip().lower()


def scan(paths) -> list[dict]:
    found = []
    for path in paths:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        for i, ln in enumerate(lines):
            m = BEGIN.search(ln)
            if not m:
                continue
            env = m.group(1)
            # body: from this line to the matching \end{env}
            j = i
            while j < len(lines) and not END_OF[env].search(lines[j]):
                j += 1
            body = "\n".join(lines[i:j + 1])
            lab = LABEL.search(body)
            ann = ANN.match(lines[i - 1]) if i else None
            found.append({
                "file": path.name, "line": i + 1, "env": env,
                "label": lab.group(1) if lab else None,
                "body": normalize(body),
                "declared": (ann.group(2) if ann and ann.group(2)
                             else ("supplement-only" if ann else None)),
            })
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.80)
    ap.add_argument("--min-chars", type=int, default=200)
    ap.add_argument("--show", type=int, default=0,
                    help="print the N highest-scoring cross-document pairs")
    args = ap.parse_args()

    art = scan(sorted((PAPER / "sections").glob("*.tex"))
               + sorted(PAPER.glob("main.tex")))
    sup = scan(sorted(SUPP.glob("s*.tex")))
    print(f"dup_statement_gate: {len(art)} article and {len(sup)} supplement "
          f"numbered statements")

    art_by_label = {a["label"]: a for a in art if a["label"]}

    # EVERY CROSS-DOCUMENT PAIR IS STILL CONSIDERED, but the expensive
    # comparison is reached only by pairs that can possibly matter.
    # `SequenceMatcher.ratio()` is quadratic in body length and this gate
    # scores every pair, which took over a minute here and TIMED OUT in an
    # independent auditor's sandbox -- a gate an auditor cannot finish is a
    # gate they must take on trust.  `real_quick_ratio()` (a length bound)
    # and `quick_ratio()` (a character-multiset bound) are difflib's own
    # UPPER BOUNDS on `ratio()`, so a pair either of them places below the
    # threshold provably cannot reach it and skipping the exact call changes
    # no verdict.  Pairs kept on a bound are marked `exact=False`; the
    # verdict loop below asserts that nothing it acts on is one of them.
    pairs = []
    for s in sup:
        # One matcher per supplement body, `set_seq1` per article body:
        # difflib caches the second sequence's index and character counts
        # across `set_seq1` calls and discards them on `set_seq2`, so this
        # builds each supplement body's tables once instead of once per pair.
        sm = difflib.SequenceMatcher(None, autojunk=False)
        sm.set_seq2(s["body"])
        for a in art:
            if min(len(s["body"]), len(a["body"])) < args.min_chars:
                continue
            sm.set_seq1(a["body"])
            ub = sm.real_quick_ratio()
            if ub < args.threshold:
                pairs.append((ub, a, s, False))
                continue
            ub = min(ub, sm.quick_ratio())
            if ub < args.threshold:
                pairs.append((ub, a, s, False))
                continue
            pairs.append((sm.ratio(), a, s, True))
    pairs.sort(key=lambda t: -t[0])

    if args.show:
        print(f"  top {args.show} cross-document body similarities "
              f"(`<=` marks an upper bound on a pair pruned below "
              f"--threshold):")
        for r, a, s, exact in pairs[:args.show]:
            print(f"    {'' if exact else '<='}{r:.3f}  {a['label']}  <->  "
                  f"{s['label']} [{s['declared']}]")

    failures = []

    # ---- 1. undeclared nontrivial matches
    for r, a, s, exact in pairs:
        if r < args.threshold:
            break
        assert exact, (
            "a pair kept on an upper bound reached the threshold; the "
            "prefilter is unsound")
        if s["declared"] == a["label"]:
            print(f"  ok   {s['label']} restates {a['label']} "
                  f"(similarity {r:.3f}), declared")
            continue
        failures.append(
            f"{s['file']}:{s['line']} {s['env']} {s['label']!r} has body "
            f"similarity {r:.3f} with article {a['env']} {a['label']!r} "
            f"({a['file']}:{a['line']}) but declares "
            f"{s['declared']!r}.  One statement printed and numbered by both "
            f"documents must either be removed from one of them or declared "
            f"with '%% inv: restates {a['label']}'.")

    # ---- 2. the `-s` suffix convention, independent of any text comparison
    for s in sup:
        if not s["label"] or not s["label"].endswith("-s"):
            continue
        base = s["label"][:-2]
        if base not in art_by_label:
            continue
        if s["declared"] == base:
            continue
        failures.append(
            f"{s['file']}:{s['line']} {s['env']} {s['label']!r} shadows "
            f"article {base!r} by the `-s` naming convention but declares "
            f"{s['declared']!r}; the article statement must be removed or "
            f"the annotation must read '%% inv: restates {base}'.")

    if failures:
        print()
        for f in sorted(set(failures)):
            print(f"FAIL  {f}")
        print(f"\ndup_statement_gate: {len(set(failures))} "
              f"same-statement-in-both-documents failure(s)")
        return 1
    print("dup_statement_gate: no undeclared statement is printed by both "
          "documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
