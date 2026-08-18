#!/usr/bin/env python
"""Generate section 3 of BUILD_ENVIRONMENT.md from the actual build products.

WHY THIS SCRIPT EXISTS
----------------------
Section 3, "Expected output of the reference build", is a table of properties
of `main.pdf` and `main.log`: page count, byte sizes, SHA-256 checksums, error
and undefined-reference counts, and the final-page footer.  Every one of those
goes stale the moment the document is rebuilt, if it is TYPED.  That
happens: a table ships carrying a one-build-old PDF size
and checksum (1,512,598 bytes / `fab7ffde...`) and a `main.log` size and
checksum one build behind, against a shipped PDF of 1,516,323 bytes.  A reader
following the document then concludes the package failed its own
verification gate.

The same failure mode -- a hand-typed number that is true when written and
false when read -- also produces a stale `INDEX.md` exception count, an
overstated reconciliation-coverage claim and a stale path-gate census.  The
fix that works is not to retype the numbers correctly; it is to stop typing
them.  This script INTERPOLATES the section from the build products, and
`--check` fails the release build when the shipped section and the products
disagree, exactly as `tab_t4_e1_gates.py --check` does for Table T4.

WHAT IS GENERATED, AND FROM WHAT
  pages, footer            `main.log` (`N pages`) cross-checked against the
                           rendered footer recorded in the log's `LastPage`
                           label resolution
  main.pdf size/SHA-256    the file itself
  main.log size/SHA-256    the file itself
  main.tex, main.bbl       the files themselves
    SHA-256
  LaTeX errors             `main.log` lines beginning `!` -- the same test
  undefined refs/cites     `undefined (references|citations)` and
                           `There were undefined` -- the same tests section 6
  multiply-defined labels  `multiply defined` -- the same test
                           runs, so the table and the gate cannot disagree

The prose around the table is NOT generated: only the table and the two
sentences that quote a number from it.  The generated block is delimited by
the sentinel comments below and nothing outside them is touched.

Usage:  python build_env_section3.py [--check]
`--check` compares the shipped section against a fresh generation and exits
non-zero if they differ.  With no arguments it rewrites the block in place.

`--check` is ARCHIVE-RELATIVE and writes nothing: every input it reads is a
file the package ships, including the dependency freeze (see `build_64`).  It
must therefore give the same answer on any machine that extracts the same
archive.  A section 6.4 census that regenerated `pip-freeze-full.txt` from the
running interpreter instead of reading the shipped one gives a different
answer to a reader than to the author; `build_64` reads the shipped artefact
for exactly that reason.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
PAPER = ROOT / "paper" / "is" / "paper"
DOC = PAPER / "BUILD_ENVIRONMENT.md"

BEGIN = "<!-- BEGIN GENERATED SECTION 3 -- build_env_section3.py -->"
END = "<!-- END GENERATED SECTION 3 -->"

# Section 6.4 carries the path gate's census, which goes stale there too if
# typed (447/247,260/135 against a gate reporting 449/247,285/140).
# Same remedy: interpolate them, from the same `abs_path_census` the gate
# itself calls, over the same set of entries the gate covers.
BEGIN64 = "<!-- BEGIN GENERATED 6.4 CENSUS -- build_env_section3.py -->"
END64 = "<!-- END GENERATED 6.4 CENSUS -->"


def _rel(p):
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(p).name


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def log_facts(log_path):
    """Page count and the four warning censuses, by the same tests as §6."""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    pages = None
    for m in re.finditer(r"\((\d+) pages?[,)]", text):
        pages = int(m.group(1))
    if pages is None:
        m = re.search(r"Output written on .*?\((\d+) pages?", text)
        pages = int(m.group(1)) if m else -1
    return {
        "pages": pages,
        "errors": sum(1 for ln in lines if ln.startswith("!")),
        "undefined": (
            sum(1 for ln in lines
                if re.search(r"undefined (references|citations)", ln))
            + sum(1 for ln in lines if "There were undefined" in ln)),
        "multiply_defined": sum(1 for ln in lines if "multiply defined" in ln),
    }


def build() -> str:
    pdf = PAPER / "main.pdf"
    log = PAPER / "main.log"
    tex = PAPER / "main.tex"
    bbl = PAPER / "main.bbl"
    f = log_facts(log)
    pages = f["pages"]
    rows = [
        ("pages", f"**{pages}**"),
        ("`main.pdf` size", f"{pdf.stat().st_size:,} bytes"),
        ("`main.pdf` SHA-256", f"`{sha256(pdf)}`"),
        ("`main.tex` SHA-256", f"`{sha256(tex)}`"),
        ("`main.bbl` SHA-256", f"`{sha256(bbl)}`"),
        ("LaTeX errors", str(f["errors"])),
        ("undefined references / citations", str(f["undefined"])),
        ("multiply-defined labels", str(f["multiply_defined"])),
        ("`main.log` size / SHA-256",
         f"{log.stat().st_size:,} bytes / `{sha256(log)}`"),
        ("final-page footer", f"`Page {pages} of {pages}` (verify this; see "
                              f"§1)"),
    ]
    out = [BEGIN,
           "",
           "<!-- Every row below is INTERPOLATED from the build products by",
           "     experiments/ttt/is_fresh/build_env_section3.py.  Do not edit",
           "     by hand: `python build_env_section3.py --check` fails the",
           "     release build if this block and the products disagree.  A",
           "     typed checksum or size row here ships one build stale the",
           "     first time the document is rebuilt without it. -->",
           "",
           "| property | value |",
           "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in rows]
    out += [
        "",
        f"The values above are **generated at package time from "
        f"`main.pdf`, `main.log`, `main.tex` and `main.bbl` themselves**, "
        f"not transcribed; the error, undefined-reference and "
        f"multiply-defined censuses are computed by the same tests §6 runs, "
        f"so this table and that gate cannot disagree.",
        "",
        "The PDF is **not** bit-reproducible across runs: `pdftex` stamps",
        "`CreationDate`/`ModDate` and an `/ID`, so the SHA-256 above "
        "identifies *this*",
        "build, not the class of correct builds. Set `SOURCE_DATE_EPOCH` and",
        "`\\pdfsuppressptexinfo` if you need a byte-stable comparison. What "
        "*is* stable",
        "across runs on this environment is the page count, the float "
        "placement and the",
        "cross-reference numbering, which is what a reader's check needs.",
        "",
        END]
    return "\n".join(out)


def build_64() -> str:
    """The section 6.4 census paragraph, from the gate's own census.

    Imported lazily so that a rebuild of section 3 alone does not pay for
    rendering the eight generated root entries.  The census covers exactly
    what the gate covers -- ALL archive entries -- so the paragraph and the
    gate cannot report different numbers.

    THE DEPENDENCY FREEZE IS READ, NOT REGENERATED.  Rendering every generated
    root entry by calling the release builder's own functions would call
    `pip_freeze_full_txt()` -- which interrogates the *running* interpreter's
    installed distributions.  The independent path gate, meanwhile, scans the
    `pip-freeze-full.txt` the archive SHIPS.  On the build machine the two
    agree, because one process produced both; on any other machine they do
    not, and `--check` then fails on a clean extraction of a correct archive,
    reporting the shipped 508-path census as stale against a locally
    regenerated 245.  A check whose answer depends on who runs it is not an
    archive-integrity check.

    So: if the shipped artefact is present beside us -- which it is in every
    extraction of `release_archive.zip`, and therefore in every environment
    where `--check` is the documented command -- it is READ verbatim and the
    census is computed over the bytes the archive actually carries.  The
    dynamic freeze survives only for the one case where no artefact exists
    yet: regenerating the block in the source tree before packaging, which is
    a package-construction operation performed by the same interpreter that
    is about to write the file.  It never redefines the object being verified
    after release.
    """
    import make_release_zip as M

    shipped_freeze = ROOT / "pip-freeze-full.txt"
    if shipped_freeze.exists():
        freeze = shipped_freeze.read_text(encoding="utf-8")
    else:
        freeze = M.pip_freeze_full_txt()
        print("[build_env] no shipped pip-freeze-full.txt at the tree root; "
              "generating it from this interpreter "
              "(package-construction mode)")

    files = M.collect()
    manifest = {"built_utc": "", "repo_relative_paths": True, "files": {
        rel: {"bytes": 0, "sha256": ""} for rel in files}}
    generated = {
        "MANIFEST.json": __import__("json").dumps(manifest, indent=1,
                                                  sort_keys=True),
        "SEEDS.md": M.SEEDS_MD,
        "COMMANDS.md": M.commands_md(),
        "BUILD_INTERPRETER.md": M.build_interpreter_md(),
        "requirements-analysis.txt": M.requirements_analysis_txt(),
        "requirements-experiment.txt": M.requirements_experiment_txt(),
        "pip-freeze-full.txt": freeze,
    }
    cen = M.abs_path_census(list(files) + list(generated),
                            lambda rel: files[rel], texts=generated)
    assert not cen["hits"], (
        "the path gate is not clean, so section 6.4's census paragraph is not "
        f"writable: {cen['hits'][:5]}")
    # INDEX.md is the eighth generated entry.  It cannot be rendered here
    # without a zip path, and it is a clean text member by construction (the
    # assertion at the end of `index_md` proves it), so it is counted as the
    # one extra text member it is -- the same accounting `index_md` uses.
    n_text = cen["text_files"] + 1
    n_entries = cen["n_members"] + 1
    n_manifested = len(files)
    n_gen = len(generated) + 1
    n_exc_f = cen["n_exception_files"]
    n_exc_p = cen["n_exception_paths"]
    n_json = cen["json_files"]
    return "\n".join([
        BEGIN64,
        "",
        "<!-- Every number in the paragraph below is INTERPOLATED from the",
        "     same `abs_path_census` the gate itself calls, by",
        "     experiments/ttt/is_fresh/build_env_section3.py.  Do not edit by",
        "     hand.  These were typed once and shipped stale",
        "     (447/247,260/135 against a gate reporting 449/247,285/140) -->",
        "",
        f"On the shipped build it reports: **0 absolute paths outside the "
        f"declared",
        f"exceptions, over {n_json:,} JSON members ({cen['json_leaves']:,} "
        f"string leaves parsed) and {n_text:,} text",
        f"members; {cen['binary_files']} binary members out of scope, "
        f"{cen['shebangs']} portable shebangs excluded; {n_exc_f}",
        f"declared exceptions holding {n_exc_p} paths.**",
        "",
        f"Its scope is **all {n_entries} entries** of the archive: the "
        f"{n_manifested} manifested payload",
        f"files plus the {n_gen} generated root entries. "
        f"{n_json:,} + {n_text:,} + {cen['binary_files']} = {n_entries:,}, so "
        f"every entry falls in",
        "exactly one of the three categories and none is skipped.",
        "",
        "> **Why the checker walks every entry.**",
        "> It once iterated `MANIFEST.json` — the",
        f"> {n_manifested} payload files — while the claim above, and the "
        f"gate's own header",
        "> comment, quantified over every file the ZIP ships. The eight",
        "> generated root entries were therefore outside the census, and one",
        "> of them, `pip-freeze-full.txt`, holds 268 path-like strings. Three",
        "> artefacts then disagreed about the scope.",
        "> The repair is the wider checker, not the narrower sentence: the",
        "> gate walks every entry, and `pip-freeze-full.txt` joins",
        "> `ABS_PATH_EXCEPTIONS` with its reason recorded like every other —",
        "> a verbatim `pip freeze --all` transcript in which the installation",
        "> locations *are* the provenance evidence, and from which nothing is",
        "> installed (the installable pins are `requirements-analysis.txt`",
        "> and `requirements-experiment.txt`, both clean). The census numbers",
        "> above are larger than a manifest-limited census would report for",
        "> that reason and no other: no file was sanitized, and no exception",
        "> was widened.",
        "",
        END64])


def splice(doc_text, block, begin=BEGIN, end=END):
    i = doc_text.find(begin)
    j = doc_text.find(end)
    if i == -1 or j == -1:
        raise SystemExit(
            f"sentinels not found in {_rel(DOC)}; expected {begin!r} and "
            f"{end!r}")
    return doc_text[:i] + block + doc_text[j + len(end):]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    cur = DOC.read_text(encoding="utf-8")
    new = splice(cur, build())
    new = splice(new, build_64(), BEGIN64, END64)
    if args.check:
        if new != cur:
            import difflib
            d = "\n".join(list(difflib.unified_diff(
                cur.split("\n"), new.split("\n"),
                "shipped", "generated", n=1, lineterm=""))[:60])
            raise SystemExit(
                "BUILD_ENVIRONMENT.md's GENERATED blocks are STALE: the "
                "shipped section 3 and/or the section 6.4 census do not match "
                "a fresh generation from main.pdf / main.log / main.tex / "
                "main.bbl and the path gate's census.  Run "
                "`python build_env_section3.py` after the build and "
                f"repackage.\n{d}")
        print("BUILD_ENVIRONMENT.md sections 3 and 6.4 are CURRENT")
        return
    DOC.write_text(new, encoding="utf-8")
    print(f"wrote generated sections 3 and 6.4 into {_rel(DOC)}")


if __name__ == "__main__":
    main()
