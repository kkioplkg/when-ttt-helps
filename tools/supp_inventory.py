#!/usr/bin/env python
"""Generate the supplement's inventory of its own numbered formal statements.

WHY THIS EXISTS.  The supplement's front matter has to say, exactly, which of
its numbered statements have no counterpart in the article and which are
restatements of article results.  Written by hand that sentence goes stale the
first time a lemma is added, split, or promoted -- and a front-matter claim
about a document's own contents is precisely the kind of claim a reader checks.

The classification lives at the STATEMENT, as a machine-readable comment
immediately above each numbered environment:

    %% inv: supplement-only
    %% inv: restates <article-label>

Every numbered environment in supplement/s*.tex must carry exactly one.  A new
statement without an annotation is a hard error here, so the inventory cannot
silently fall behind the document.

The NUMBERS are never typed.  Supplement numbers come from
supplement/supplement.aux and article numbers from paper/main.aux -- the two
documents' own records of what LaTeX actually numbered -- exactly as
tools/xref_sync.py does for cross-document references.

Output: supplement/inventory_generated.tex, input by the front matter.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "paper" / "is2"
PAPER = ROOT / "paper"
SUPP = ROOT / "supplement"
OUT = SUPP / "inventory_generated.tex"

BS = chr(92)
NEWLABEL = re.compile(BS + BS + r"newlabel\{([^}]+)\}\{\{([^{}]*)\}\{")
BEG = re.compile(
    r"^" + BS + BS + r"begin\{(theorem|lemma|proposition|corollary|definition"
    r"|remark|assumption|example)\}")
LAB = re.compile(BS + BS + r"label\{([^}]+)\}")
TITLE = re.compile(r"\[(.*)$")
ANN = re.compile(r"^%% inv: (supplement-only|restates ([A-Za-z0-9:_-]+))$")

# The environment name a reader sees, keyed by the LaTeX environment.
KIND = {"theorem": "Theorem", "lemma": "Lemma", "proposition": "Proposition",
        "corollary": "Corollary", "definition": "Definition",
        "remark": "Remark", "assumption": "Assumption",
        "example": "Example"}


def read_labels(aux: pathlib.Path) -> dict[str, str]:
    if not aux.exists():
        sys.exit(f"supp_inventory: {aux} does not exist; build that document "
                 f"first")
    out = {}
    for key, num in NEWLABEL.findall(aux.read_text(encoding="utf-8",
                                                   errors="replace")):
        out.setdefault(key, num)
    return out


def strip_title(raw: str) -> str:
    """The bracketed title of an environment, brace-balanced, one line."""
    depth = 0
    buf = []
    for ch in raw:
        if ch == "[":
            depth += 1
        elif ch == "]":
            if depth == 0:
                break
            depth -= 1
        buf.append(ch)
    return " ".join("".join(buf).split())


def scan() -> list[dict]:
    found = []
    for path in sorted(SUPP.glob("s*.tex")):
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        for i, ln in enumerate(lines):
            if not BEG.match(ln):
                continue
            env = BEG.match(ln).group(1)
            ann = ANN.match(lines[i - 1]) if i else None
            if ann is None:
                sys.exit(f"supp_inventory: {path.name}:{i + 1} numbered "
                         f"{env} carries no '%% inv:' annotation; every "
                         f"numbered statement must declare whether it is "
                         f"supplement-only or restates an article result")
            key = None
            title = ""
            for j in range(i, min(i + 4, len(lines))):
                m = LAB.search(lines[j])
                if m:
                    key = m.group(1)
                    break
            if key is None:
                sys.exit(f"supp_inventory: {path.name}:{i + 1} numbered "
                         f"{env} carries no label")
            head = " ".join(lines[i:i + 4])
            mt = TITLE.search(head)
            title = strip_title(mt.group(1)) if mt else ""
            found.append({"env": env, "key": key, "title": title,
                          "only": ann.group(2) is None,
                          "counterpart": ann.group(2), "file": path.name})
    return found


def main() -> int:
    supp = read_labels(SUPP / "supplement.aux")
    art = read_labels(PAPER / "main.aux")
    items = scan()

    bad = 0
    for it in items:
        if it["key"] not in supp:
            print(f"  UNNUMBERED: supplement label {it['key']!r} is not in "
                  f"supplement.aux")
            bad += 1
        if it["counterpart"] and it["counterpart"] not in art:
            print(f"  UNRESOLVED: {it['key']!r} declares a counterpart "
                  f"{it['counterpart']!r} the article does not define")
            bad += 1
    if bad:
        print(f"supp_inventory: {bad} unresolved inventory entry/entries")
        return 1

    def num(it):
        return supp[it["key"]]

    def sortkey(it):
        n = num(it)
        return (int(re.sub(r"[^0-9]", "", n) or 0), n)

    only = sorted([i for i in items if i["only"]], key=sortkey)
    rest = sorted([i for i in items if not i["only"]], key=sortkey)

    def phrase(it):
        return f"{KIND[it['env']]}~\\ref{{{it['key']}}} ({it['title']})"

    def joinlist(seq):
        seq = [phrase(i) for i in seq]
        if len(seq) == 1:
            return seq[0]
        return ", ".join(seq[:-1]) + " and " + seq[-1]

    L = []
    L.append("%% GENERATED by tools/supp_inventory.py -- do not edit.")
    L.append("%% Source of truth: the '%% inv:' annotation above each numbered")
    L.append("%% statement, plus supplement.aux and main.aux for the numbers.")
    L.append("\\newcommand{\\SuppOnlyCount}{" + str(len(only)) + "}")
    L.append("\\newcommand{\\SuppRestatedCount}{" + str(len(rest)) + "}")
    L.append("\\newcommand{\\SuppTotalCount}{" + str(len(items)) + "}")
    L.append("\\newcommand{\\SuppOnlyList}{" + joinlist(only) + "}")
    L.append("\\newcommand{\\SuppRestatedList}{" + joinlist(rest) + "}")
    L.append("")
    OUT.write_text("\n".join(L), encoding="utf-8", newline="")
    print(f"supp_inventory: {len(items)} numbered supplement statements "
          f"({len(only)} supplement-only, {len(rest)} restated) -> "
          f"{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
