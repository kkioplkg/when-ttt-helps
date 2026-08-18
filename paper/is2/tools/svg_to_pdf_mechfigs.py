#!/usr/bin/env python
"""Convert the three author-drawn mechanism figures from SVG to PDF.

WHAT THIS IS, AND WHAT IT IS NOT.  Every other figure and table this
submission typesets has a GENERATOR: a script that reads a record file and
writes the artefact, whose `--check` proves the shipped bytes are what the
records produce.  Main Figures 1-3 have none, because they are not
measurements.  They are schematics DRAWN BY THE AUTHORS, and their source of
record is the vector artwork under `paper/mechanism_figures/`.

This script is therefore a CONVERTER, not a generator.  It reads no record and
asserts no scientific claim; it exists because `pdflatex` cannot include SVG,
so the artwork has to be turned into PDF once, and because a conversion that
lives only in a shell history is not documented.  `BUILD_ENVIRONMENT.md`
section 5 is the prose form of what happens here.

THE DELIVERED SVGs ARE NEVER WRITTEN TO.  They are the authors' source of
record.  Every transformation below happens in a temporary copy.

ROUTE.  Inkscape and rsvg-convert are not installed on the build machine, so
the converter of record is **cairosvg**, which was already present in the
pinned interpreter -- nothing was installed for this, and the pinned
environment is unchanged.  The output is genuine vector: embedded font
subsets, zero raster image objects, an extractable text layer.

THE ONE GLYPH THAT NEEDS HELP.  cairo's *toy* text API, which cairosvg drives,
cannot map astral-plane (>U+FFFF) code points on this build: U+1D4AC
MATHEMATICAL SCRIPT CAPITAL Q -- the instance class the manuscript writes
\\mathcal{Q}, and which appears in figure 2 only -- comes out as a .notdef box,
while the BMP script letters in the same files (U+2112 script L, U+2115
blackboard N) are fine.  Verified on a two-glyph minimal SVG, so it is a
property of the backend and not of these files.  Every `<text>` run holding an
astral code point is therefore replaced, in the temporary copy, by the same
glyph's OUTLINE, taken from the very font the element already names and
emitted as an SVG `<path>` at the same baseline origin and in the same fill.
Same font, same glyph: this changes the encoding of the mark, not the mark.

Headless Chrome renders the glyph correctly and was the alternative route.  It
was not taken because it emits a **Type 3** font in figure 3, which is worse
for an Elsevier submission than this substitution is.

CROPPING.  cairosvg emits a page the size of the SVG canvas, and two of the
three drawings place their outer panel borders within a pixel of that edge
while the third carries uneven slack.  The page box is therefore set to the
drawing's own INK bounding box plus a small uniform pad.  The bounding box is
measured on an oversized canvas, so a stroke the delivered canvas would clip
is still seen: cropping to a box measured under that clip would shave the
border rather than keep it.  No `pdfcrop` pass, and so no ghostscript
dependency, is involved.

Usage:  python tools/svg_to_pdf_mechfigs.py [--check]

`--check` re-converts into a temporary directory and compares against the
shipped PDFs, reporting whether each is byte-identical.  Note that byte
identity across MACHINES is not promised and is not claimed anywhere: the
output embeds subsets of system fonts, so a machine with a different Cambria
or Calibri build produces different bytes for the same drawing.  What the
check is for is the same machine, where a silent drift between the artwork and
the shipped PDF is exactly the failure it catches.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
IS2 = HERE.parent
REPO = IS2.parent.parent
SRC = REPO / "paper" / "mechanism_figures"
DST = IS2 / "paper" / "figures"

# source of record  ->  the PDF the article typesets
FIGURES = [
    ("1.svg", "fig_mech_1_phase_law.pdf"),
    ("2.svg", "fig_mech_2_information_boundary.pdf"),
    ("3.svg", "fig_mech_3_entropy_alignment.pdf"),
]

# The only font any astral run in these three files names.  A `.ttc` face
# index, not a path guess: Cambria Math is the second face of the collection.
MATHFONT_NAME = "cambria.ttc"
MATHFONT_INDEX = 1

PAD = 8  # user units of white kept around the ink, all four sides

TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
FS_RE = re.compile(r'font-size="([0-9.]+)"')
FILL_RE = re.compile(r'fill="([^"]+)"')
MTX_RE = re.compile(
    r'transform="matrix\(([-0-9.eE]+) ([-0-9.eE]+) ([-0-9.eE]+) '
    r'([-0-9.eE]+) ([-0-9.eE]+) ([-0-9.eE]+)\)"')
SVG_OPEN_RE = re.compile(r'<svg width="(\d+)" height="(\d+)"[^>]*>')


def _mathfont():
    from fontTools.ttLib import TTFont
    # WINDIR rather than a typed drive: this file ships inside
    # release_archive.zip, whose absolute-path gate treats a drive-letter
    # literal as a build-machine path and would need a declared exception.
    root = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or ""
    p = pathlib.Path(root) / "Fonts" / MATHFONT_NAME
    if not p.exists():
        raise SystemExit(
            f"{MATHFONT_NAME} not found under the system font directory; it "
            f"supplies the one outlined glyph (see the module docstring)")
    return TTFont(str(p), fontNumber=MATHFONT_INDEX)


def deastralize(svg_text):
    """Replace every <text> run holding a >U+FFFF code point with its outline."""
    if all(ord(c) <= 0xFFFF for c in svg_text):
        return svg_text, 0
    from fontTools.pens.svgPathPen import SVGPathPen
    font = _mathfont()
    glyphset = font.getGlyphSet()
    cmap = font.getBestCmap()
    upem = font["head"].unitsPerEm
    n = [0]

    def sub(m):
        attrs, body = m.group(1), m.group(2)
        if all(ord(c) <= 0xFFFF for c in body):
            return m.group(0)
        assert all(ord(c) > 0xFFFF for c in body), \
            "mixed BMP/astral run is not handled: " + repr(body)
        fs = float(FS_RE.search(attrs).group(1))
        fill = FILL_RE.search(attrs).group(1)
        a, b, c, d, e, f = (float(x) for x in MTX_RE.search(attrs).groups())
        assert (a, b, c, d) == (1.0, 0.0, 0.0, 1.0), \
            "rotated or scaled astral run is not handled: " + attrs
        s = fs / upem
        parts = []
        for ch in body:
            pen = SVGPathPen(glyphset)
            glyphset[cmap[ord(ch)]].draw(pen)
            parts.append(pen.getCommands())
        n[0] += 1
        # SVG text baselines run y-down, glyph outlines y-up: flip with -s.
        return ('<path fill="%s" transform="translate(%s %s) scale(%s %s)" '
                'd="%s"/>' % (fill, e, f, s, -s, " ".join(parts)))

    return TEXT_RE.sub(sub, svg_text), n[0]


def reframe(svg_text, x0, y0, x1, y1):
    """Same drawing, on a canvas that is exactly the given box plus PAD."""
    m = SVG_OPEN_RE.match(svg_text)
    body = svg_text[m.end():]
    x0, y0 = x0 - PAD, y0 - PAD
    w, h = (x1 - x0) + PAD, (y1 - y0) + PAD
    head = ('<svg width="%d" height="%d" viewBox="%d %d %d %d" '
            'xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve">'
            % (w, h, x0, y0, w, h))
    return head + body


def ink_box(svg_text, w, h, probe=200):
    """True ink bounding box of the drawing, in its own user units."""
    import cairosvg
    import numpy as np
    from PIL import Image
    big = reframe(svg_text, -probe, -probe, w + probe, h + probe)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "probe.svg")
        q = os.path.join(td, "probe.png")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(big)
        cairosvg.svg2png(url=p, write_to=q,
                         output_width=w + 2 * probe + PAD,
                         output_height=h + 2 * probe + PAD,
                         background_color="white")
        a = np.asarray(Image.open(q).convert("L"))
    ink = a < 250
    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    off = probe + PAD
    return (int(cols[0]) - off, int(rows[0]) - off,
            int(cols[-1]) - off, int(rows[-1]) - off)


def convert_one(src_svg, out_pdf):
    import cairosvg
    raw = pathlib.Path(src_svg).read_text(encoding="utf-8")
    fixed, n_outlined = deastralize(raw)
    m = SVG_OPEN_RE.match(fixed)
    w, h = int(m.group(1)), int(m.group(2))
    box = ink_box(fixed, w, h)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "cropped.svg")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(reframe(fixed, *box))
        cairosvg.svg2pdf(url=p, write_to=str(out_pdf))
    return n_outlined, (w, h), box


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="convert to a temporary directory and compare with "
                         "the shipped PDFs instead of overwriting them")
    args = ap.parse_args()

    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for svg, pdf in FIGURES:
            src = SRC / svg
            if not src.exists():
                sys.exit(f"{src} is missing; it is the source of record for "
                         f"{pdf}")
            shipped = DST / pdf
            out = pathlib.Path(td) / pdf if args.check else shipped
            n, (w, h), box = convert_one(src, out)
            note = f"{n} astral run(s) outlined" if n else "no astral run"
            print(f"  {svg} ({w}x{h}) -> {pdf}: {note}, "
                  f"ink box {box}, {out.stat().st_size} bytes")
            if args.check:
                if not shipped.exists():
                    print(f"    MISSING: {shipped}")
                    bad += 1
                elif shipped.read_bytes() != out.read_bytes():
                    print(f"    DIFFERS from the shipped {pdf} "
                          f"({shipped.stat().st_size} bytes shipped)")
                    bad += 1
                else:
                    print("    byte-identical to the shipped PDF")
    if args.check:
        print("svg_to_pdf_mechfigs: "
              + ("OK, all three match" if not bad else f"{bad} mismatch(es)"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
