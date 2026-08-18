"""Shared matplotlib style for all paper figures.

Colorblind-safe categorical palette (validated: worst adjacent CVD dE 24.2,
light surface) + publication defaults: 9pt fonts, recessive grid/axes,
vector PDF output. Every fig_*.py imports this module first.
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[2]          # repo root (TTT/)
RESULTS = ROOT / "experiments" / "results"
FIGDIR = ROOT / "figures"
PREVIEW = FIGDIR / "preview"

# ------------------------------------------------- categorical palette
# fixed slot order is the CVD-safety mechanism -- never reorder/cycle
BLUE = "#2a78d6"
AQUA = "#1baf7a"
YELLOW = "#eda100"
GREEN = "#008300"
VIOLET = "#4a3aa7"
RED = "#e34948"
MAGENTA = "#e87ba4"
ORANGE = "#eb6834"
SERIES = [BLUE, AQUA, YELLOW, GREEN, VIOLET, RED, MAGENTA, ORANGE]

INK = "#0b0b0b"          # primary ink
INK2 = "#52514e"         # secondary ink
MUTED = "#898781"        # axis/labels
GRID = "#e1e0d9"         # hairline grid
BASE = "#c3c2b7"         # baseline/axis

SINGLE = 5.5             # single-column width (in)
FULL = 6.8               # full-width (in)

plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,               # embed TrueType (editable text)
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.edgecolor": BASE,
    "axes.linewidth": 0.8,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "lines.linewidth": 2.0,
    "lines.markersize": 5,
})


def save(fig, name):
    """Save vector PDF into figures/ and a PNG preview for visual inspection."""
    FIGDIR.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    pdf = FIGDIR / f"{name}.pdf"
    png = PREVIEW / f"{name}.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(png, bbox_inches="tight", pad_inches=0.02)
    print(f"saved {pdf}  ({os.path.getsize(pdf)} bytes)")


def spearman(x, y):
    """Spearman rank correlation (average ranks for ties) without scipy."""
    import numpy as np

    def rank(a):
        a = np.asarray(a, dtype=float)
        order = np.argsort(a, kind="mergesort")
        r = np.empty(len(a), dtype=float)
        sa = a[order]
        i = 0
        while i < len(a):
            j = i
            while j + 1 < len(a) and sa[j + 1] == sa[i]:
                j += 1
            r[order[i:j + 1]] = 0.5 * (i + j) + 1.0
            i = j + 1
        return r

    rx, ry = rank(x), rank(y)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = (rx ** 2).sum() ** 0.5 * (ry ** 2).sum() ** 0.5
    import numpy as np
    return float(np.dot(rx, ry) / denom) if denom > 0 else float("nan")
