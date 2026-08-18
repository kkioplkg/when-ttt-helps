#!/usr/bin/env python
"""Source-hygiene gates for paper/is2: stray CR, duplicate line, literal TAB.

Scope: every `.tex`, `.bib`, `.md` and `.txt` file under `paper/` and
`supplement/` that is part of the manuscript, excluding the frozen baseline
copy and the superseded-figure directory (both of which are archives of
files this tree no longer builds).

  stray-CR sweep     a carriage return that is not part of a CRLF pair is the
                     mechanism that turns `\\ref` into `ef` -- ordinary text
                     that pdflatex ships without complaint.
  duplicate-line     two consecutive identical non-blank lines in a source
                     file are, in a manuscript, always an editing accident.
  tab gate           a literal TAB in a .tex source aligns differently in
                     every editor and silently changes verbatim/tabular
                     content; there are none, and there must stay none.
  nesting gate       a numbered statement environment opened while another is
                     still open.  `\\begin{proposition}` inside a `remark`
                     compiles, numbers correctly and renders almost
                     identically, so no build log, no reference check and no
                     rendered-text gate can see it -- and one shipped that way
                     for several builds.  The defect is visible only in the
                     source, as a stack that is not empty when a statement
                     opens, which is what this sweep computes.  It also
                     reports any statement environment that is never closed.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# `archive_tables/` is in scope even though neither document compiles it: its
# fragments SHIP, the reconciliation reads their printed tokens, and one of
# them carried a TAB + "exttt" for two rounds -- a mangled `\texttt` that no
# gate could see, because the tab gate only looked at the two document trees.
DIRS = [ROOT / "paper", ROOT / "supplement", ROOT / "archive_tables"]
EXTS = {".tex", ".bib", ".md", ".txt"}
SKIP_PARTS = {"paper_BASELINE_BACKUP", "_superseded"}

# EVERY C0 CONTROL CHARACTER, not just CR and TAB.  Both defects this gate has
# actually caught were a backslash escape surviving a tool that interpreted it:
# `\ref` became CR + "ef", `\texttt` became TAB + "exttt", `\allowbreak` became
# BEL + "llowbreak".  CR and TAB were gated; BEL was not, and it shipped.  The
# class is "a control byte in prose", so the gate is on the class.
CTRL_OK = {0x09, 0x0A, 0x0D}          # TAB/LF/CR have their own rules below
CTRL_NAMES = {0x00: "NUL", 0x07: "BEL", 0x08: "BS", 0x0B: "VT", 0x0C: "FF",
              0x1B: "ESC", 0x7F: "DEL"}

# THE STATEMENT ENVIRONMENTS, i.e. everything declared by a `\newtheorem` in
# either preamble, plus `proof`.  Nesting any of these inside another is a
# source defect that the compiler, the numbering and the rendered text all
# forgive: `\begin{proposition}` inside a `remark` prints a correctly numbered
# proposition.  A statement is a top-level object; the stack must be empty
# when one opens.
STMT_ENVS = ("theorem", "lemma", "proposition", "corollary", "conjecture",
             "axiom", "definition", "example", "assumption", "remark",
             "algorithmenv", "proof")
# ASSEMBLED, NOT TYPED.  Written out, this pattern is a backslash-backslash
# followed by a word and a later backslash, which is exactly a UNC share path
# to the release archive's absolute-path gate -- and that gate scans this file
# like every other, with no exemption for checkers.  The escape is built from
# `chr(92)` for the same reason `make_release_zip.py` assembles its own
# fragments at import time: a hygiene tool that has to be excepted from the
# hygiene rule makes the rule unverifiable.
_BSL = chr(92)
_ENV_RE = re.compile(
    re.escape(_BSL) + r"(begin|end)" + re.escape("{")
    + "(" + "|".join(STMT_ENVS) + ")" + re.escape("}"))


def nesting_defects(text: str):
    """Yield (line, kind, detail) for statement environments that nest.

    Computed from the source, because there is nowhere else to compute it
    from: the PDF of a nested statement is the PDF of a well-formed one.
    """
    stack = []
    for m in _ENV_RE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        kind, env = m.group(1), m.group(2)
        if kind == "begin":
            if stack:
                outer_env, outer_line = stack[-1]
                yield (line, "nested",
                       f"{env} opens inside {outer_env} (opened line "
                       f"{outer_line})")
            stack.append((env, line))
        else:
            if not stack:
                yield (line, "unopened", f"end{{{env}}} with nothing open")
            elif stack[-1][0] != env:
                outer_env, outer_line = stack[-1]
                yield (line, "crossed",
                       f"end{{{env}}} closes while {outer_env} (line "
                       f"{outer_line}) is open")
                stack.pop()
            else:
                stack.pop()
    for env, line in stack:
        yield (line, "unclosed", f"{env} opened and never closed")


def files():
    for d in DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.suffix.lower() not in EXTS or not p.is_file():
                continue
            if SKIP_PARTS & set(p.parts):
                continue
            yield p


def main() -> int:
    cr = dup = tab = ctrl = nest = 0
    for p in files():
        raw = p.read_bytes()
        # stray CR: a 0x0d not followed by 0x0a
        for i, b in enumerate(raw):
            if b == 0x0D and (i + 1 >= len(raw) or raw[i + 1] != 0x0A):
                cr += 1
                print(f"  stray CR   {p.relative_to(ROOT)} byte {i}")
            elif (b < 0x20 or b == 0x7F) and b not in CTRL_OK:
                ctrl += 1
                name = CTRL_NAMES.get(b, f"0x{b:02X}")
                print(f"  control    {p.relative_to(ROOT)} byte {i}: {name} "
                      f"({raw[max(0, i - 12):i + 12]!r})")
        text = raw.decode("utf-8", errors="replace")
        if p.suffix == ".tex":
            for line_no, kind, detail in nesting_defects(text):
                nest += 1
                print(f"  nesting    {p.relative_to(ROOT)}:{line_no}  "
                      f"{kind}: {detail}")
        prev = None
        fenced = False
        for n, line in enumerate(text.split("\n"), 1):
            if "\t" in line and p.suffix == ".tex":
                tab += 1
                print(f"  TAB        {p.relative_to(ROOT)}:{n}")
            st = line.strip()
            # A fenced code block in a .md file is a transcript, and a build
            # recipe legitimately repeats one command line: `pdflatex` runs
            # four times in a row. Repetition there is content, not an
            # editing accident, so the gate does not look inside fences.
            if st.startswith("```"):
                fenced = not fenced
                prev = None
                continue
            if fenced:
                prev = None
                continue
            if st and st == prev:
                dup += 1
                print(f"  duplicate  {p.relative_to(ROOT)}:{n}  {st[:60]}")
            prev = st
    ok = True
    for name, val in (("stray CRs", cr), ("duplicate lines", dup),
                      ("literal TABs", tab),
                      ("other control characters", ctrl),
                      ("nested/unbalanced statements", nest)):
        status = "ok   " if val == 0 else "FAIL "
        if val:
            ok = False
        print(f"{status} {name}: {val}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
