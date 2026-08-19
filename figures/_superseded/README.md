# Superseded figure/table generators — DO NOT RUN

Every file in this directory is a **superseded generator that produces no
object in the Information Sciences manuscript**. They are retained only as
an audit trail: they document how the *superseded* figure or table was drawn,
so a reader can see how it differs from the current one and why.

They were moved here because each of them wrote a file with the **same
basename** as an object that is now produced by a different, current generator.
A reproducer who ran `figures/*.py` in bulk would therefore have
silently overwritten a current artifact with a stale one. Nothing left in
`figures/` shares an output basename with anything in
`ttt/is_fresh/`.

They are deliberately **not runnable from this directory**: they `import _style`,
which resolves only from `figures/`. Running one from here raises
`ModuleNotFoundError` rather than quietly writing a stale file. None of them
appears in `COMMANDS.md`.

| superseded file | wrote | superseded by | why |
|---|---|---|---|
| `fig_F1.py` | `figures/F1_curves.pdf` | `ttt/is_fresh/fig_f1_curves.py` → `paper/is/paper/figures/F1_curves.pdf` | read the single-seed `results/e1/e1_a_seed42.json`; the manuscript reports the five-seed `f7_curve_match` measurement |
| `fig_F2.py` | `figures/F2_phase.pdf` | `ttt/is_fresh/fig_f2_phase.py` | single seed 42; one gain quantity; the current figure plots the three distinct gain quantities of `f10_oracle_grid.py` on the same replicates, five seeds |
| `fig_F3.py` | `figures/F3_alta.pdf` | `ttt/is_fresh/fig_f3_alta.py` | seeds 42/43 against an **analytic** oracle; the current figure uses the measured oracle (`f4`) and the compute-matched oracle (`f13`), five seeds |
| `fig_F4.py` | `figures/F4_e2_phase.pdf` | `ttt/is_fresh/fig_f4_e2.py` | annotated **full-sample** correlations from `results/summary_final.json`; the current figure annotates cross-fitted correlations from the signed statistic (`f22`, `f22b`, `f22c`, `f23`) |
| `fig_F8.py` | `figures/F8_domains.pdf` | `ttt/is_fresh/fig_f8_domains.py` | full-sample per-domain correlations; the current figure uses the document-clustered intervals of `f11`/`f17` |
| `tab_T4.py` | `figures/T4_e1_gates.tex` | `ttt/is_fresh/tab_t4_e1_gates.py` | read the single-seed `results/e1/e1_{a..f}_seed42.json`; the current table is generated from the five-seed fresh summaries plus `f26_e1_reporting_audit.json`, and its row (a) uses the pointwise normalization the label states |

**Their inputs are deliberately not in the release archive.** Every file above
reads either `results/e1/e1_{a..f}_seed42.json` or
`results/summary_final.json`, and neither ships: they are not
inputs to any number in the manuscript, and shipping them would invite exactly
the confusion this directory exists to prevent. So these scripts cannot run
from the archive even if the `_style` import were satisfied — which is the
intended state, not an omission. Everything the manuscript actually reports is
regenerable from the archive; see `COMMANDS.md`.

The generators that remain in `figures/` (`fig_F5.py`, `fig_F6.py`,
`fig_F7.py`, `tab_T2.py`, plus the helpers `_style.py`, `bootstrap_ci.py`,
`k3_baseline.py`) are **current**: each still produces exactly the object of
that name in `paper/is/paper/figures/`, and each is listed in `COMMANDS.md`.
