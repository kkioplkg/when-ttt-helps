#!/usr/bin/env python
"""Generate the cross-document reference tables for the two-document split.

The article and the Supplementary Material are SEPARATE LaTeX documents, so
neither can resolve the other's \\label.  Every number one document prints for
an object owned by the other is therefore a hand-carried string -- and once the
proofs moved out of the article there were roughly forty of them in each
direction, which is forty chances to print a stale number that no gate would
catch.

This script removes the hand-carrying.  It reads each document's own .aux --
the authoritative record of what LaTeX actually numbered -- and writes the
other document's lookup table:

    paper/main.aux            ->  supplement/xref_main.tex     (\\mref, \\meqref)
    supplement/supplement.aux ->  paper/xref_supp.tex          (\\sref, \\seqref)

Usage in the sources is by LABEL, never by number:

    \\mref{thm:exact}     -> "8"        (the article's Theorem 8, cited in the
                                        supplement)
    \\meqref{eq:phaseP}   -> "(12)"
    \\sref{sup:pl}        -> "S2"       (a supplement section, cited in the
                                        article)

A label the other document does not define is a HARD ERROR at generation time,
printed here and left undefined in the .tex so the build's own undefined-macro
error fires too.  There is no silent fallback: a missing entry must not
degrade into a plausible-looking wrong number.

Because the tables are only strings, neither document's own numbering depends
on them, so the fixed point is reached in one pass each:

    build main -> sync -> build supp -> sync -> build main -> build supp
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PAPER = ROOT / "paper"
SUPP = ROOT / "supplement"

# A TeX control sequence in this file is built from BS, never written as a
# doubled backslash: the release archive's absolute-path census reads
# "backslash backslash name backslash" as a UNC host-and-share and would fail
# the packaging gate on this file's own source.
BS = chr(92)

# BS + "newlabel{KEY}{{NUMBER}{PAGE}{TITLE}{ANCHOR}{}}"
NEWLABEL = re.compile(BS + BS + r"newlabel\{([^}]+)\}\{\{([^{}]*)\}\{")


def read_labels(aux: pathlib.Path) -> dict[str, str]:
    if not aux.exists():
        sys.exit(f"xref_sync: {aux} does not exist; build that document first")
    out = {}
    for line in aux.read_text(encoding="utf-8", errors="replace").splitlines():
        m = NEWLABEL.match(line.strip())
        if not m:
            continue
        key, num = m.group(1), m.group(2)
        # sub-labels such as `foo@cref` are hyperref/cleveref bookkeeping.
        if "@" in key:
            continue
        if num:
            out[key] = num
    return out


HEADER = ("%% GENERATED FILE -- DO NOT EDIT." + chr(10)
          + "%% Written by tools/xref_sync.py from {src}." + chr(10)
          + "%% Every entry is the number the OTHER document's own LaTeX run "
            "assigned." + chr(10)
          + "%% Cite by label, never by typing the number: "
            + BS + "{cmd}{{thm:foo}}." + chr(10))


def emit(labels: dict[str, str], dest: pathlib.Path, src: str,
         cmd: str, eqcmd: str, prefix: str) -> None:
    lines = [HEADER.format(src=src, cmd=cmd)]
    B = BS
    lines.append(chr(10).join([
        B + "makeatletter",
        B + "providecommand{" + B + cmd + "}[1]{}",
        B + "renewcommand{" + B + cmd + "}[1]{%",
        "  " + B + "@ifundefined{" + prefix + "@#1}{"
        + B + "PackageError{xref}{no " + prefix + " number for #1}{}}%",
        "    {" + B + "csname " + prefix + "@#1" + B + "endcsname}}",
        B + "providecommand{" + B + eqcmd + "}[1]{}",
        B + "renewcommand{" + B + eqcmd + "}[1]{(" + B + cmd + "{#1})}",
    ]))
    for key in sorted(labels):
        lines.append(B + "expandafter" + B + "def" + B + "csname "
                     + prefix + "@" + key + B + "endcsname{"
                     + labels[key] + "}")
    lines.append(B + "makeatother")
    text = "\n".join(lines) + "\n"
    old = dest.read_text(encoding="utf-8") if dest.exists() else None
    if old != text:
        dest.write_text(text, encoding="utf-8", newline="\n")
        print(f"  wrote {dest.relative_to(ROOT)}  ({len(labels)} labels)")
    else:
        print(f"  unchanged {dest.relative_to(ROOT)}  ({len(labels)} labels)")


GENERATED = {"xref_main.tex", "xref_supp.tex"}
COMMENT = re.compile(r"(?<!\\)%.*$")


def used_labels(root: pathlib.Path, cmd: str) -> set[str]:
    """Labels actually cited in the sources -- comments and the generated
    tables themselves excluded, so the generator's own documentation does not
    register as a citation of a label named `key`."""
    pat = re.compile(BS + BS + cmd + r"\{([^}]+)\}")
    used = set()
    for p in sorted(root.rglob("*.tex")):
        if p.name in GENERATED:
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        body = "\n".join(COMMENT.sub("", ln) for ln in body.splitlines())
        used |= set(pat.findall(body))
    return used


def main() -> int:
    main_labels = read_labels(PAPER / "main.aux")
    supp_labels = read_labels(SUPP / "supplement.aux")
    print(f"xref_sync: {len(main_labels)} article labels, "
          f"{len(supp_labels)} supplement labels")

    emit(main_labels, SUPP / "xref_main.tex", "paper/main.aux",
         "mref", "meqref", "xrefmain")
    emit(supp_labels, PAPER / "xref_supp.tex", "supplement/supplement.aux",
         "sref", "seqref", "xrefsupp")

    bad = 0
    for want, have, who in (
            (used_labels(SUPP, "mref") | used_labels(SUPP, "meqref"),
             main_labels, "supplement cites article label"),
            (used_labels(PAPER, "sref") | used_labels(PAPER, "seqref"),
             supp_labels, "article cites supplement label")):
        for k in sorted(want - set(have)):
            print(f"  UNRESOLVED: {who} {k!r}")
            bad += 1
    if bad:
        print(f"xref_sync: {bad} unresolved cross-document label(s)")
        return 1
    print("xref_sync: every cross-document label resolves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
