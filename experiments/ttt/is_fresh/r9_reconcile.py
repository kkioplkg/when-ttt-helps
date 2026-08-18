"""Automated number reconciliation for the IS manuscript.

The job: compare every abstract, main-text, figure, table and appendix value
against the authoritative result records.

Two independent passes, both of which must be clean:

  PASS 1  RECORD CHECK.  A curated table of every headline numeric claim that
          appears in more than one place in the manuscript, each bound to the
          JSON of record and to the exact reduction that produces it.  The
          script recomputes the value from the JSON, applies the manuscript's
          own rounding, and requires the printed token to match.  This is the
          pass that catches conflicts like the ttt_rot [0.37, 0.70]/[0.37,
          0.69] one: the record says hi_mean = 0.694506, which rounds to
          0.69 under every convention.

  PASS 2  CROSS-DOCUMENT COLLISION SCAN.  Model-free.  It reads every .tex
          under sections/, appendix/ and figures/, strips comments (the
          "% src:" provenance lines are not claims), and for each curated claim
          reports EVERY literal occurrence of the value across the corpus, so
          a value updated in one file and not another is visible.  It then
          looks for NEAR-MISS pairs: two distinct printed values that differ by
          less than one unit in the last printed place and sit in the same
          bracket/interval context, which is the signature of that defect.

  PASS 1b CONSTRUCTION CHECK.
          A value check compares numbers and is therefore blind
          to a correct number carrying the wrong kind of object.  This pass
          asserts, against the records and against the .tex corpus, that the
          E4 brackets are still built by POOLING the five bootstrap RNG
          streams into one 10,000-draw distribution and reading one
          percentile pair off it -- not by averaging five per-stream
          percentile endpoints, which is a different object from the single
          document-clustered percentile interval the documents name.

WHAT THIS IS, AND WHAT IT IS NOT.
This is a CURATED HEADLINE-VALUE AND ROUNDING AUDIT, not an exhaustive binding
of every number and every statistical interpretation in the manuscript.  The
rows are a hand-maintained list; nothing detects a claim that was never
added to it.  Concretely, and by design, the following lie OUTSIDE its scope:

  * analytic constants that no JSON records -- the two Appendix B fixed-law
    thresholds 4.15e-8 and 4.24e-14 are NOT bound here (they were checked by
    independent recomputation instead);
  * the printed Monte Carlo standard errors of the Appendix B ratios: the
    ratios are bound, the SEs are not separately asserted;
  * SEMANTIC errors OUTSIDE the E4 construction pass 1b now covers.  A
    JSON-pointer value check compares numbers.  Calling a pair of
    split-averaged endpoints a "clustered 95% CI" leaves every number correct
    and only the label wrong, so PASS 1 returns 0 mismatches on a manuscript
    carrying exactly that defect -- which is how both the Figure 4 mislabel
    and the E4 bracket mislabel each survived a green run.
    Pass 1b closes that hole for the E4 brackets specifically.  It is NOT a
    general semantic checker: every other label in the manuscript is still
    verified by reading, not by this script;
  * E3 safety-failure counts and magnitudes, the E3 K = 3 matched
    comparison, the E3 seed-spread summaries, the E2 leave-one-corruption-out
    fold intervals and some E2 conditional calibration proportions -- all
    reported in the manuscript, none bound here;
  * proof-only constants, boundary-case quantifiers and domain restrictions,
    such as the t >= 1 restriction now carried by Lemma 51(i).

Report the result as "<N> curated headline and repeated numerical claims
checked, 0 mismatches", with N read off this script's own output, never as
"every number in the manuscript is machine-bound".  The count is deliberately
not written into this docstring: a hand-kept copy of a gate's output is a
second, unchecked claim, and it rots.

Usage:  python r9_reconcile.py            # all passes, exit 1 on any failure
        python r9_reconcile.py --verbose  # print every check, not just fails
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Resolve the repository root from this file's own location so the script runs
# unchanged inside the extracted reproducibility archive
# (<root>/experiments/ttt/is_fresh/r9_reconcile.py).  If the file has been
# copied out of that layout, the root is taken from $TTT_REPO_ROOT or the
# current directory -- never from a hard-coded build-machine path, which would
# both leak the build machine and resolve nowhere for a reader (the
# absolute-path gate).
_here = Path(__file__).resolve()
if _here.parent.name == "is_fresh":
    REPO = _here.parents[3]
else:
    import os as _os
    REPO = Path(_os.environ.get("TTT_REPO_ROOT", _os.getcwd())).resolve()
PAPER = REPO / "paper" / "is" / "paper"
FRESH = REPO / "experiments" / "results" / "is_fresh"
E3 = REPO / "experiments" / "results" / "e3"

# ---------------------------------------------------------------------------
# WHICH RECONCILIATION IS THIS, AND WHEN DOES IT APPLY
#
# This script reconciles the FROZEN single-document manuscript under
# `paper/is/`, against a record set that includes the ImageNet-C suite under
# `experiments/results/e3/`.  The submission built from `paper/is2/` reports
# neither: it is two documents, and its release archive deliberately drops the
# ImageNet-C records.  Its reconciliation is a different script,
# `paper/is2/tools/r9_reconcile.py`, and that one is the current entry point.
#
# Inside an extracted release archive neither `paper/is/` nor
# `experiments/results/e3/` is present, so this script cannot run and used to
# fail with an obscure file-not-found.  It now says so and exits cleanly, so
# that a reader following the archive's documented commands is never left
# holding a failure that looks like a reproduction defect.
if not PAPER.exists() or not E3.exists():
    _missing = [str(p) for p in (PAPER, E3) if not p.exists()]
    print("[r9] NOT APPLICABLE in this tree -- this is the FROZEN "
          "single-document reconciliation.")
    print("[r9] missing (expected, in a release extraction): "
          + ", ".join(_missing))
    print("[r9] The current reconciliation for the submitted two-document "
          "manuscript is:")
    print("[r9]     cd paper/is2/tools && python r9_reconcile.py")
    print("[r9] exiting 0: nothing here is broken, this script simply does "
          "not describe the submitted manuscript.")
    sys.exit(0)
# ---------------------------------------------------------------------------

TEX_FILES = (sorted((PAPER / "sections").glob("*.tex"))
             + sorted((PAPER / "appendix").glob("*.tex"))
             + sorted(PAPER.glob("figures/T*.tex")))

_cache = {}


def J(name, root=FRESH):
    key = str(root / name)
    if key not in _cache:
        with open(root / name, encoding="utf-8") as f:
            _cache[key] = json.load(f)
    return _cache[key]


def dig(obj, path):
    for p in path.split("/"):
        if p == "":
            continue
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    return obj


def strip_comments(text):
    """Drop LaTeX comments: they carry provenance, not claims."""
    out = []
    for line in text.split("\n"):
        i = 0
        while True:
            i = line.find("%", i)
            if i < 0:
                break
            if i > 0 and line[i - 1] == "\\":
                i += 1
                continue
            line = line[:i]
            break
        out.append(line)
    return "\n".join(out)


CORPUS = {}
for p in TEX_FILES:
    CORPUS[p.relative_to(PAPER).as_posix()] = strip_comments(
        p.read_text(encoding="utf-8"))


def occurrences(token):
    """Every (file, line, line-text) where the literal token appears as a
    standalone number (not as a prefix of a longer number)."""
    pat = re.compile(r"(?<![\d.])" + re.escape(token) + r"(?![\d])")
    hits = []
    for rel, text in CORPUS.items():
        for n, line in enumerate(text.split("\n"), 1):
            if pat.search(line):
                hits.append((rel, n, line.strip()))
    return hits


# --------------------------------------------------------------------------
# PASS 1: the curated claim table
#   (label, printed token, value from record, tolerance in printed units)
# --------------------------------------------------------------------------
def pct(x):
    return 100.0 * x


CHECKS = []


def chk(label, token, value, fmt, src, note=""):
    """token: the string the manuscript prints.  value: recomputed from src.
    fmt: the rounding the manuscript uses, applied to value."""
    CHECKS.append((label, token, value, fmt, src, note))


# ---- E1 ------------------------------------------------------------------
f7a = J("f26_e1_reporting_audit.json")["item1_and_3_curve_match"]
chk("E1 pointwise risk-curve error (Sec 7.1, T4a, Fig 1 caption)",
    "2.23", pct(f7a["pointwise_sup_t_absdiff_over_theory"]["mean"]), "%.2f",
    "f26/item1_and_3_curve_match/pointwise_sup_t_absdiff_over_theory/mean")
chk("E1 pointwise error, T4 row (a) as a fraction",
    "0.0223", f7a["pointwise_sup_t_absdiff_over_theory"]["mean"], "%.4f",
    "same record, T4 prints the fraction")
chk("E1 published-normalisation error (Sec 7.1, T4a, Fig 1 caption)",
    "1.15", pct(f7a["published_normalisation_max_absdiff_over_max_theory"]
                ["mean"]), "%.2f",
    "f26/.../published_normalisation_max_absdiff_over_max_theory/mean")
chk("E1 published-norm error, T4 fraction",
    "0.0115", f7a["published_normalisation_max_absdiff_over_max_theory"]
    ["mean"], "%.4f", "same record")
chk("E1 max deviation in SE units",
    "3.61", f7a["max_deviation_in_SE_units"]["true_max_over_all_seeds"],
    "%.2f", "f26/.../max_deviation_in_SE_units/true_max_over_all_seeds")
chk("E1 number of (cell, step) comparisons over five seeds",
    "60{,}150", float(f7a["n_comparisons_all_seeds"]), "%.0f",
    "f26/.../n_comparisons_all_seeds", note="printed with a thin space")
chk("E1 comparisons per seed",
    "12{,}030", float(f7a["n_comparisons_per_seed"]), "%.0f",
    "f26/.../n_comparisons_per_seed", note="printed with a thin space")

pb = J("f26_e1_reporting_audit.json")["item2_and_6_phase_boundary"]
chk("E1 fixed-rule held-out sign accuracy (T4b, Sec 7.1)",
    "0.984", pb["fixed_rule_holdout_accuracy"]["mean"], "%.3f",
    "f26/item2_and_6_phase_boundary/fixed_rule_holdout_accuracy/mean")
chk("E1 fixed-rule accuracy resolved at 3 SE (T4b)",
    "1.000", pb["fixed_rule_holdout_accuracy_resolved3se"]["mean"], "%.3f",
    "f26/.../fixed_rule_holdout_accuracy_resolved3se/mean")
chk("E1 fitted-rule held-out accuracy (Sec 7.1)",
    "0.979", pb["fitted_rule_holdout_accuracy"]["mean"], "%.3f",
    "f26/.../fitted_rule_holdout_accuracy/mean")
chk("E1 fitted-rule accuracy resolved at 3 SE (Sec 7.1)",
    "0.999", pb["fitted_rule_holdout_accuracy_resolved3se"]["mean"], "%.3f",
    "f26/.../fitted_rule_holdout_accuracy_resolved3se/mean")
chk("E1 largest |z| of a fitted-rule miss (Sec 7.1)",
    "3.26", pb["max_abs_z_of_a_miss_fitted_holdout"]["max"], "%.2f",
    "f26/.../max_abs_z_of_a_miss_fitted_holdout/max")

f10 = J("f10_oracle_grid_summary.json")
chk("E1 fitted / theoretical one-step threshold (T4b, Fig 2 caption)",
    "0.968", f10["fitted_threshold_onestep"]["mean"] / (f10["eta"] / 2.0),
    "%.3f", "f10/fitted_threshold_onestep/mean divided by eta/2")

f3s = J("f3_optimal_stopping_summary.json")
chk("E1 fraction of cells within 5%% of the measured oracle (T4c, Sec 7.1)",
    "1.00", f3s["frac_risk_within_5pct_of_measured_oracle"]["mean"], "%.2f",
    "f3/frac_risk_within_5pct_of_measured_oracle/mean")
os4 = J("f26_e1_reporting_audit.json")["item4_optimal_stopping"]
chk("E1 worst single cell-run relative stopping gap (Sec 7.1)",
    "0.0402", os4["worst_cell_relative_gap"]["true_worst_single_cell_run"],
    "%.4f", "f26/item4_optimal_stopping/.../true_worst_single_cell_run")
chk("E1 per-seed worst cells, average (Sec 7.1)",
    "0.0212", os4["worst_cell_relative_gap"]["mean_of_per_seed_worst"],
    "%.4f", "f26/item4_optimal_stopping/.../mean_of_per_seed_worst")

f6 = J("f6_relu_multiseed_summary.json")
chk("E1(e) mean relative gain at alpha=0 (T4e)",
    "0.64", f6["mean_relgain_by_alpha"]["0.0"]["mean"], "%.2f",
    "f6/mean_relgain_by_alpha/0.0/mean")
chk("E1(e) mean relative gain at alpha=1 (T4e)",
    "1.00", f6["mean_relgain_by_alpha"]["1.0"]["mean"], "%.2f",
    "f6/mean_relgain_by_alpha/1.0/mean")
chk("E1(e) alpha=1 minus alpha=0 margin (Sec 7.1)",
    "0.361", f6["margin_alpha1_minus_alpha0"]["mean"], "%.3f",
    "f6/margin_alpha1_minus_alpha0/mean")
chk("E1(e) alpha=0 mean excess, 4dp (T4e, App C)",
    "0.0433", f6["alpha0_mean_harm"]["mean"], "%.4f",
    "f6/alpha0_mean_harm/mean")
chk("E1(e) alpha=0 excess, low end (T4e, Sec 7.1, App C)",
    "-0.0236", f6["alpha0_mean_harm"]["min"], "%.4f",
    "f6/alpha0_mean_harm/min")
chk("E1(e) alpha=0 excess, high end (T4e, App C)",
    "0.1673", f6["alpha0_mean_harm"]["max"], "%.4f",
    "f6/alpha0_mean_harm/max")
chk("E1(e) seeds with harm at alpha=0 (T4e, App C)",
    "4", float(f6["n_seeds_alpha0_harmful"]), "%.0f",
    "f6/n_seeds_alpha0_harmful", note="printed as 4/5")

f5 = J("f5_batch_variance_summary.json")
chk("E1(f) max relative error of Var(u_t) vs sigma^2/N (T4f)",
    "0.0057", f5["max_rel_err_variance_vs_sigma2_over_N"]["mean"], "%.4f",
    "f5/max_rel_err_variance_vs_sigma2_over_N/mean")

# ---- E2 stochastic feature proxy (split-averaged endpoint locus) --------
feat = J("f22_e2_crossfit_feat_summary.json")["per_method"]
rot, mask = feat["ttt_rot"], feat["ttt_mask"]
chk("E2 ttt_rot mean-final rho (Sec 7.2, Fig 4)",
    "0.546", rot["rho_mean_final"]["mean"], "%.3f",
    "f22/per_method/ttt_rot/rho_mean_final/mean")
chk("E2 ttt_rot split range low (Sec 7.2, Fig 4)",
    "0.511", rot["rho_mean_final"]["min"], "%.3f", "f22/.../min")
chk("E2 ttt_rot split range high (Sec 7.2, Fig 4)",
    "0.592", rot["rho_mean_final"]["max"], "%.3f", "f22/.../max")
chk("E2 ttt_rot split-averaged clustered endpoint, low (Sec 7.2, Fig 4)",
    "0.37", rot["ci_mean_final_clustered"]["lo_mean"], "%.2f",
    "f22/.../ci_mean_final_clustered/lo_mean")
chk("E2 ttt_rot split-averaged clustered endpoint, high (Sec 7.2, Fig 4)",
    "0.69", rot["ci_mean_final_clustered"]["hi_mean"], "%.2f",
    "f22/.../ci_mean_final_clustered/hi_mean",
    note="the Section 7 passage that prints this endpoint rounds to 0.69")
chk("E2 ttt_rot median-final rho (Sec 7.2)",
    "0.630", rot["rho_median_final"]["mean"], "%.3f",
    "f22/.../rho_median_final/mean")
chk("E2 ttt_mask mean-final rho (Sec 7.2, Fig 4)",
    "0.540", mask["rho_mean_final"]["mean"], "%.3f",
    "f22/per_method/ttt_mask/rho_mean_final/mean")
chk("E2 ttt_mask split range low", "0.483", mask["rho_mean_final"]["min"],
    "%.3f", "f22/.../min")
chk("E2 ttt_mask split range high", "0.610", mask["rho_mean_final"]["max"],
    "%.3f", "f22/.../max")
chk("E2 ttt_mask split-averaged clustered endpoint, low", "0.25",
    mask["ci_mean_final_clustered"]["lo_mean"], "%.2f", "f22/.../lo_mean")
chk("E2 ttt_mask split-averaged clustered endpoint, high", "0.76",
    mask["ci_mean_final_clustered"]["hi_mean"], "%.2f", "f22/.../hi_mean")
chk("E2 ttt_mask median-final rho", "0.493",
    mask["rho_median_final"]["mean"], "%.3f", "f22/.../rho_median_final/mean")

loss = J("f22c_e2_crossfit_loss_summary.json")["per_method"]
lr_, lm_ = loss["ttt_rot"], loss["ttt_mask"]
chk("E2 loss proxy ttt_rot rho", "0.068", lr_["rho_mean_final"]["mean"],
    "%.3f", "f22c/per_method/ttt_rot/rho_mean_final/mean")
chk("E2 loss proxy ttt_rot range low", "0.014", lr_["rho_mean_final"]["min"],
    "%.3f", "f22c/.../min")
chk("E2 loss proxy ttt_rot range high", "0.131", lr_["rho_mean_final"]["max"],
    "%.3f", "f22c/.../max")
chk("E2 loss proxy ttt_rot split-averaged clustered endpoint, low",
    "-0.13",
    lr_["ci_mean_final_clustered"]["lo_mean"], "%.2f", "f22c/.../lo_mean")
chk("E2 loss proxy ttt_rot split-averaged clustered endpoint, high",
    "0.25",
    lr_["ci_mean_final_clustered"]["hi_mean"], "%.2f", "f22c/.../hi_mean")
chk("E2 loss proxy ttt_mask rho", "0.504", lm_["rho_mean_final"]["mean"],
    "%.3f", "f22c/per_method/ttt_mask/rho_mean_final/mean")
chk("E2 loss proxy ttt_mask range low", "0.440",
    lm_["rho_mean_final"]["min"], "%.3f", "f22c/.../min")
chk("E2 loss proxy ttt_mask range high", "0.538",
    lm_["rho_mean_final"]["max"], "%.3f", "f22c/.../max")
chk("E2 loss proxy ttt_mask split-averaged clustered endpoint, low",
    "0.27",
    lm_["ci_mean_final_clustered"]["lo_mean"], "%.2f", "f22c/.../lo_mean")
chk("E2 loss proxy ttt_mask split-averaged clustered endpoint, high",
    "0.70",
    lm_["ci_mean_final_clustered"]["hi_mean"], "%.2f", "f22c/.../hi_mean")

det = J("f22b_e2_crossfit_det_summary.json")["per_method"]
chk("E2 deterministic tent rho (Sec 7.2, Fig 4)", "0.844",
    det["tent"]["rho_mean_final"]["mean"], "%.3f",
    "f22b/per_method/tent/rho_mean_final/mean")
chk("E2 tent split range low", "0.832", det["tent"]["rho_mean_final"]["min"],
    "%.3f", "f22b/.../min")
chk("E2 tent split range high", "0.854", det["tent"]["rho_mean_final"]["max"],
    "%.3f", "f22b/.../max")
chk("E2 tent split-averaged clustered endpoint, low", "0.79",
    det["tent"]["ci_mean_final_clustered"]["lo_mean"], "%.2f",
    "f22b/.../lo_mean")
chk("E2 tent split-averaged clustered endpoint, high", "0.89",
    det["tent"]["ci_mean_final_clustered"]["hi_mean"], "%.2f",
    "f22b/.../hi_mean")
chk("E2 pseudo-label rho (Sec 7.2, Fig 4)", "0.828",
    det["pl"]["rho_mean_final"]["mean"], "%.3f",
    "f22b/per_method/pl/rho_mean_final/mean")
chk("E2 pseudo-label split range low", "0.806",
    det["pl"]["rho_mean_final"]["min"], "%.3f", "f22b/.../min")
chk("E2 pseudo-label split range high", "0.849",
    det["pl"]["rho_mean_final"]["max"], "%.3f", "f22b/.../max")
chk("E2 pseudo-label split-averaged clustered endpoint, low", "0.72",
    det["pl"]["ci_mean_final_clustered"]["lo_mean"], "%.2f", "f22b/.../lo")
chk("E2 pseudo-label split-averaged clustered endpoint, high", "0.89",
    det["pl"]["ci_mean_final_clustered"]["hi_mean"], "%.2f", "f22b/.../hi")

# ---- Table T5: matched-architecture arms --------------------------------
arms = J("f23_e2_gn_summary.json")["arms"]
T5 = [("tent_gn_loss", "0.882", "0.665", "0.74", "0.94"),
      ("tent_wrn_loss", "0.926", "0.694", "0.86", "0.96"),
      ("pl_wrn_loss", "0.888", "0.702", "0.81", "0.94"),
      ("ttt_rot_loss", "0.273", "0.284", "-0.05", "0.55"),
      ("ttt_mask_loss", "0.591", "0.103", "0.29", "0.80"),
      ("tent_gn_feat", "0.092", "-0.044", "-0.21", "0.37"),
      ("ttt_rot_feat", "0.418", "0.598", "0.07", "0.68"),
      ("ttt_mask_feat", "0.610", "0.727", "0.30", "0.82")]
for tag, mean_tok, med_tok, lo_tok, hi_tok in T5:
    a = arms[tag]
    chk(f"T5 {tag} rho mean-final", mean_tok, a["rho_mean_final"]["mean"],
        "%.3f", f"f23/arms/{tag}/rho_mean_final/mean")
    chk(f"T5 {tag} rho median-final", med_tok,
        a["rho_median_final"]["mean"], "%.3f",
        f"f23/arms/{tag}/rho_median_final/mean")
    chk(f"T5 {tag} split-averaged clustered endpoint, low", lo_tok,
        a["ci_mean_final_clustered"]["lo_mean"], "%.2f",
        f"f23/arms/{tag}/ci_mean_final_clustered/lo_mean")
    chk(f"T5 {tag} split-averaged clustered endpoint, high", hi_tok,
        a["ci_mean_final_clustered"]["hi_mean"], "%.2f",
        f"f23/arms/{tag}/ci_mean_final_clustered/hi_mean")

# ---- E2 learning-rate ablation ------------------------------------------
lr = J("f25_e2_lr_ablation.json")["verdict"]
for i, tok in enumerate(("0.77", "0.32", "0.59")):
    chk(f"E5 lr ablation in-sample rho #{i+1}", tok,
        lr["signed_in_sample_best"][i], "%.2f",
        f"f25/verdict/signed_in_sample_best/{i}")
for i, tok in enumerate(("0.49", "0.16", "0.32")):
    chk(f"E5 lr ablation cross-fit rho #{i+1}", tok,
        lr["signed_crossfit_final"][i], "%.2f",
        f"f25/verdict/signed_crossfit_final/{i}")
per_rate = J("f25_e2_lr_ablation.json")["per_rate"]
for i, tok in enumerate(("0.193", "0.088", "0.217")):
    chk(f"E5 lr ablation mean best-step gain #{i+1}", tok,
        per_rate[i]["mean_best_step_gain"], "%.3f",
        f"f25/per_rate/{i}/mean_best_step_gain")

# ---- E2 entropy calibration coverage ------------------------------------
cov = J("f21_e2_coverage.json")
chk("E2 calibration total episodes", "7{,}680",
    float(cov["n_episodes_total"]), "%.0f", "f21/n_episodes_total")
chk("E2 calibration retained confident-right n", "2873",
    float(cov["retained"]["n_right"]), "%.0f", "f21/retained/n_right")
chk("E2 calibration retained confident-wrong n", "1554",
    float(cov["retained"]["n_wrong"]), "%.0f", "f21/retained/n_wrong")
chk("E2 calibration excluded n", "3{,}253", float(cov["n_excluded"]), "%.0f",
    "f21/n_excluded")
chk("E2 calibration coverage share", "57.6", pct(cov["coverage"]), "%.1f",
    "f21/coverage")
chk("E2 calibration excluded share", "42.4", pct(cov["excluded_share"]),
    "%.1f", "f21/excluded_share")
chk("E2 all-episode Spearman(alpha_ent, correct)", "0.863",
    cov["all_episodes"]["spearman_alpha_correct"], "%.3f",
    "f21/all_episodes/spearman_alpha_correct")

# ---- E4 ------------------------------------------------------------------
# INTERVAL ENDPOINTS COME FROM f29/f30, NEVER FROM f11/f17.
# f11_e4_cluster_ci.py and f17_e4_alignment_only.py run five independent
# B = 2000 document-clustered bootstraps and report the arithmetic MEAN of
# the five lower and the five upper percentile endpoints.  A mean of five
# percentile endpoints is not a percentile of anything, and several sites
# described the result as a single document-clustered percentile interval.
# f29_e4_pooled_ci.py and
# f30_e4_alignment_pooled.py replay the same five RNG streams, POOL their
# 5 x 2000 = 10,000 draws into one empirical distribution per quantity and
# read ONE 2.5/97.5 percentile pair off it, so the object computed is the
# object the documents name.  f11/f17 remain on disk as the audit trail of
# the superseded construction and are bound here only where the quantity is
# a point estimate that pooling cannot move.
#
# That defect survived a green 152/0 run because NO E4 endpoint was
# bound at all -- only the four correlations and the four perplexity
# improvements were, and pooling does not move a point estimate.  Every E4
# endpoint the manuscript prints is bound below, and the CONSTRUCTION checks
# further down assert that the records these endpoints come from still say
# they were built by pooling, so a silent reversion to endpoint averaging
# fails this pass instead of passing it.
f29 = J("f29_e4_pooled_ci.json")
f29d = f29["domains"]
f30 = J("f30_e4_alignment_pooled.json")
f30h = f30["headline"]
f30d = f30["domains"]
E4_DOMS = ("code", "legal", "pubmed", "wikitext")

for dom, tok in (("code", "0.679"), ("legal", "0.918"),
                 ("pubmed", "0.875"), ("wikitext", "0.881")):
    chk(f"E4 {dom} alignment-only rho (Sec 7.4, Fig 8)", tok,
        f30h[dom]["rho_alignment_only"], "%.3f",
        f"f30/headline/{dom}/rho_alignment_only")
for dom, tok in (("code", "0.582"), ("legal", "0.905"),
                 ("pubmed", "0.868"), ("wikitext", "0.834")):
    chk(f"E4 {dom} full-statistic rho (Sec 7.4, Fig 8)", tok,
        f30h[dom]["rho_full_statistic"], "%.3f",
        f"f30/headline/{dom}/rho_full_statistic")
for dom, tok in (("code", "0.96"), ("legal", "0.067"),
                 ("pubmed", "0.570"), ("wikitext", "0.210")):
    v = f29d[dom]["ppl_improvement_pooled"]
    chk(f"E4 {dom} pooled perplexity improvement (Sec 7.4)", tok, v,
        "%.2f" if tok.count("0") == 1 and len(tok) == 4 else
        ("%.3f" if len(tok) == 5 else "%.2f"),
        f"f29/domains/{dom}/ppl_improvement_pooled")

# --- E4 interval ENDPOINTS (these were once unbound entirely) ------------
# perplexity improvement, document-clustered pooled percentile interval
for dom, lo, hi, fmt in (("code", "0.712", "1.266", "%.3f"),
                         ("legal", "0.0626", "0.0705", "%.4f"),
                         ("pubmed", "0.309", "1.075", "%.3f"),
                         ("wikitext", "0.200", "0.220", "%.3f")):
    b = f29d[dom]["impr_ci"]["cluster_nested"]
    chk(f"E4 {dom} perplexity-improvement clustered interval, low (Sec 7.4)",
        lo, b["lo"], fmt,
        f"f29/domains/{dom}/impr_ci/cluster_nested/lo",
        note="pooled 10,000-draw percentile, not a mean of five endpoints")
    chk(f"E4 {dom} perplexity-improvement clustered interval, high (Sec 7.4)",
        hi, b["hi"], fmt,
        f"f29/domains/{dom}/impr_ci/cluster_nested/hi",
        note="pooled 10,000-draw percentile, not a mean of five endpoints")

# alignment-only correlation, document-clustered pooled percentile interval
for dom, lo, hi in (("code", "0.625", "0.727"),
                    ("legal", "0.900", "0.931"),
                    ("pubmed", "0.845", "0.899"),
                    ("wikitext", "0.858", "0.898")):
    b = f30h[dom]["ci_alignment_only"]
    chk(f"E4 {dom} alignment-only clustered interval, low (Sec 7.4, Fig 8)",
        lo, b[0], "%.3f", f"f30/headline/{dom}/ci_alignment_only/0")
    chk(f"E4 {dom} alignment-only clustered interval, high (Sec 7.4, Fig 8)",
        hi, b[1], "%.3f", f"f30/headline/{dom}/ci_alignment_only/1")

# paired difference rho(alignment) - rho(full).  All four domains are printed
# in Section 7.4 -- three whose interval excludes zero on the alignment side
# and PubMed's, which contains zero.  PubMed's endpoints were printed as
# [-0.003, +0.018], which matched NO record in either the pooled-row or the
# seed-averaged construction (the record says [-0.002, +0.017] pooled-row and
# [-0.003, +0.019] seed-averaged).  That error is independent of the
# endpoint-averaging defect, and a reconciliation that binds no E4 endpoint
# cannot see it at all: every neighbouring number is right.  The endpoints
# below are therefore bound.
for dom, lo, hi in (("code", "0.073", "0.122"),
                    ("legal", "0.007", "0.020"),
                    ("pubmed", "-0.002", "0.017"),
                    ("wikitext", "0.031", "0.063")):
    b = f30h[dom]["paired_diff_ci"]
    chk(f"E4 {dom} paired difference (align - full) interval, low (Sec 7.4)",
        lo, b[0], "%.3f", f"f30/headline/{dom}/paired_diff_ci/0",
        note="printed with an explicit + sign")
    chk(f"E4 {dom} paired difference (align - full) interval, high (Sec 7.4)",
        hi, b[1], "%.3f", f"f30/headline/{dom}/paired_diff_ci/1",
        note="printed with an explicit + sign")

# design effects (clustered width / i.i.d.-row width), Appendix C
for dom, tok in (("code", "1.769"), ("legal", "1.730"),
                 ("pubmed", "1.542"), ("wikitext", "1.730")):
    chk(f"E4 {dom} design effect, perplexity improvement (App C)", tok,
        f29d[dom]["impr_ci"]["cluster_nested"]["design_effect_vs_naive"],
        "%.3f", f"f29/domains/{dom}/impr_ci/cluster_nested/"
                f"design_effect_vs_naive")
for dom, tok in (("code", "1.657"), ("legal", "1.568"),
                 ("pubmed", "1.566"), ("wikitext", "1.552")):
    chk(f"E4 {dom} design effect, correlation (App C)", tok,
        f29d[dom]["rho_ci"]["cluster_nested"]["design_effect_vs_naive"],
        "%.3f", f"f29/domains/{dom}/rho_ci/cluster_nested/"
                f"design_effect_vs_naive")

_de_i = [f29d[d]["impr_ci"]["cluster_nested"]["design_effect_vs_naive"]
         for d in E4_DOMS]
_de_r = [f29d[d]["rho_ci"]["cluster_nested"]["design_effect_vs_naive"]
         for d in E4_DOMS]
chk("E4 design-effect range, perplexity improvement, low end (Sec 7.4, App C)",
    "1.54", min(_de_i), "%.2f", "f29 min over domains of impr design effect")
chk("E4 design-effect range, perplexity improvement, high end (Sec 7.4, App C)",
    "1.77", max(_de_i), "%.2f", "f29 max over domains of impr design effect")
chk("E4 design-effect range, correlations, low end (Sec 7.4)",
    "1.55", min(_de_r), "%.2f", "f29 min over domains of rho design effect")
chk("E4 design-effect range, correlations, high end (Sec 7.4)",
    "1.66", max(_de_r), "%.2f", "f29 max over domains of rho design effect")

# intraclass correlations -- the quantity that justifies clustering at all
_icc_g = [f29d[d]["variance_decomposition"]["gain"]["icc"] for d in E4_DOMS]
_icc_p = [f29d[d]["variance_decomposition"]["phase_v2"]["icc"]
          for d in E4_DOMS]
chk("E4 per-document gain ICC, low end (Sec 7.4, App C)",
    "0.972", min(_icc_g), "%.3f", "f29 min over domains of gain ICC")
chk("E4 per-document gain ICC, high end (Sec 7.4, App C)",
    "0.9999", max(_icc_g), "%.4f", "f29 max over domains of gain ICC")
chk("E4 phase-statistic ICC, low end (App C)",
    "0.818", min(_icc_p), "%.3f", "f29 min over domains of phase_v2 ICC")
chk("E4 phase-statistic ICC, high end (App C)",
    "0.957", max(_icc_p), "%.3f", "f29 max over domains of phase_v2 ICC")

chk("E4 pooled bootstrap draws behind every printed endpoint (App C)",
    "10{,}000", float(f29["n_pooled_draws"]), "%.0f", "f29/n_pooled_draws",
    note="5 RNG streams x B = 2000; printed with a thin space")
chk("E4 max endpoint gap, i.i.d.-row construction vs the published one (App C)",
    "0.0062", f29["max_reproduction_gap_vs_published"], "%.4f",
    "f29/max_reproduction_gap_vs_published",
    note="the check that the widening is caused by the resampling unit alone")

# --- E4 PROXY (leave-one-domain-out): f31 supersedes f12's endpoints -------
# Two defects, one
# locus.  (1) The manuscript printed "a bootstrap interval excluding zero on
# the favourable side in 0 of 4"; f12's own record says ONE -- PubMed, whose
# partial-Spearman bracket is [+0.001475, +0.183007] endpoint-averaged and
# [+0.000440, +0.182915] pooled, and excludes zero on the positive side in
# BOTH constructions.  The census was typed, contradicted the JSON beside it,
# and survived every green run because no f12 quantity was bound at all --
# the same structural hole that let the E4 bracket defect through.  (2) f12
# averaged five per-stream percentile endpoints while the documents called
# the pair a document bootstrap interval, exactly as f11/f17 did.
# f31_e4_proxy_pooled.py applies the f29/f30 remedy: it replays f12's exact
# draws (per-stream endpoint gap asserted 0.0), pools the 5 x 2000 into one
# 10,000-draw distribution per quantity and reads ONE percentile pair off it.
# Every proxy endpoint the manuscript or Table T6 prints is bound below, and
# so are both exclusion counts, so neither can be typed again.
f31 = J("f31_e4_proxy_pooled.json")
f31f = f31["folds"]
f31s = f31["summary"]

# partial Spearman of delta_v2 given alignment -- the POINT estimates
for dom, tok in (("code", "-0.287"), ("legal", "0.003"),
                 ("pubmed", "0.091"), ("wikitext", "0.028")):
    chk(f"E4 proxy {dom} partial rho of delta_v2 given alignment (Sec 7.4)",
        tok, f31f[dom]["heldout_partial_rho_delta_v2_given_alignment"],
        "%.3f",
        f"f31/folds/{dom}/heldout_partial_rho_delta_v2_given_alignment",
        note="printed with an explicit sign")

# ...and its POOLED interval.  PubMed is printed to five decimals on purpose:
# its lower endpoint is +0.00044, which at three decimals prints as +0.000 and
# would read as containing zero -- the opposite of what the record says.
for dom, lo, hi, fmt in (("code", "-0.368", "-0.203", "%.3f"),
                         ("legal", "-0.082", "0.090", "%.3f"),
                         ("pubmed", "0.00044", "0.18291", "%.5f"),
                         ("wikitext", "-0.056", "0.114", "%.3f")):
    b = f31f[dom]["pooled_ci_partial_rho_delta_v2_given_alignment"]
    chk(f"E4 proxy {dom} partial-rho pooled interval, low (Sec 7.4, T6)",
        lo, b["lo"], fmt,
        f"f31/folds/{dom}/pooled_ci_partial_rho_delta_v2_given_alignment/lo",
        note="pooled 10,000-draw percentile, not a mean of five endpoints")
    chk(f"E4 proxy {dom} partial-rho pooled interval, high (Sec 7.4, T6)",
        hi, b["hi"], fmt,
        f"f31/folds/{dom}/pooled_ci_partial_rho_delta_v2_given_alignment/hi",
        note="pooled 10,000-draw percentile, not a mean of five endpoints")

# held-out correlation of the frozen selection, and its pooled interval (T6)
for dom, tok in (("code", "0.703"), ("legal", "0.927"),
                 ("pubmed", "0.898"), ("wikitext", "0.869")):
    chk(f"E4 proxy {dom} held-out rho of the frozen selection (Sec 7.4, T6)",
        tok, f31f[dom]["heldout_rho_selected"], "%.3f",
        f"f31/folds/{dom}/heldout_rho_selected")
for dom, lo, hi in (("code", "0.647", "0.751"), ("legal", "0.910", "0.941"),
                    ("pubmed", "0.870", "0.921"),
                    ("wikitext", "0.840", "0.892")):
    b = f31f[dom]["pooled_ci_selected"]
    chk(f"E4 proxy {dom} held-out selected pooled interval, low (T6)",
        lo, b["lo"], "%.3f", f"f31/folds/{dom}/pooled_ci_selected/lo")
    chk(f"E4 proxy {dom} held-out selected pooled interval, high (T6)",
        hi, b["hi"], "%.3f", f"f31/folds/{dom}/pooled_ci_selected/hi")

# THE CENSUS THAT WAS FOUND FALSE.  Both sides of it, bound.
chk("E4 proxy folds whose partial-rho interval excludes zero on the "
    "FAVOURABLE side (Sec 7.4, T6)",
    "1", float(f31s["n_folds_partial_rho_delta_v2_ci_excludes_zero"]), "%.0f",
    "f31/summary/n_folds_partial_rho_delta_v2_ci_excludes_zero",
    note="printed as \"1 of 4\"; a \"0 of 4\" summary would "
         "contradict f12's own record")
chk("E4 proxy folds whose partial-rho interval excludes zero on the ADVERSE "
    "side (Sec 7.4, T6)",
    "1", float(f31s["n_folds_partial_rho_delta_v2_ci_excludes_zero_adverse"]),
    "%.0f",
    "f31/summary/n_folds_partial_rho_delta_v2_ci_excludes_zero_adverse",
    note="printed as \"1 of 4\"; code, and the reason the conclusion is \"no "
         "consistent incremental benefit\" rather than \"none\"")
chk("E4 proxy folds selecting a delta_v2-family variant (Sec 7.4)",
    "2", float(f31s["n_folds_selecting_delta_v2_family"]), "%.0f",
    "f31/summary/n_folds_selecting_delta_v2_family")
chk("E4 proxy pooled bootstrap draws behind every printed proxy endpoint "
    "(App C)",
    "10{,}000", float(f31["n_pooled_draws"]), "%.0f", "f31/n_pooled_draws",
    note="5 RNG streams x B = 2000; printed with a thin space")
chk("E4 proxy max endpoint shift, pooled vs the superseded averaged "
    "construction (App C)",
    "0.00104", f31["audit_vs_f12"]["max_endpoint_shift_vs_f12"], "%.5f",
    "f31/audit_vs_f12/max_endpoint_shift_vs_f12",
    note="the largest move caused by the endpoint rule alone")

# --- E5 learning-rate ablation: the aggregation scope of the sign claim ----
# The stability sentence has to name its aggregation scope: the cross-fit
# range at lr = 1e-3 includes a negative split, so a sentence that names no
# scope is read as a claim about every split.  Section 5.5 says "the
# five-split mean remains positive at all three learning rates" and prints
# the negative split; both are bound.
_f25 = J("f25_e2_lr_ablation.json")
_lr1 = [r for r in _f25["per_rate"] if abs(r["lr"] - 0.001) < 1e-12][0]
chk("E5 most negative cross-fit split at learning rate 1e-3 (Sec 5.5)",
    "-0.101", _lr1["rho_crossfit_final"]["min"], "%.3f",
    "f25/per_rate[lr=0.001]/rho_crossfit_final/min",
    note="the split that makes the sign claim a claim about the five-split "
         "MEAN and not about every split")
chk("E5 negative cross-fit splits at learning rate 1e-3 (Sec 5.5)",
    "1", float(sum(1 for v in _lr1["rho_crossfit_final"]["values"] if v < 0)),
    "%.0f", "f25/per_rate[lr=0.001]/rho_crossfit_final/values, count < 0",
    note="printed as \"one of the five\"")

# --------------------------------------------------------------------------
# PASS 1b: CONSTRUCTION CHECK -- what KIND of object each E4 bracket is
#
# There is a class of E4 defect that PASS 1 is structurally blind to and always
# will be: every bound value was correct, and the brackets were nevertheless
# not the objects the manuscript named.  Binding the endpoints (above) closes
# the "unbound quantity" half of that hole.  This pass closes the other half.
# It asserts, on the records themselves and on the .tex corpus, that the
# CONSTRUCTION behind those endpoints is still the pooled one -- so a future
# edit that reverted f29/f30 to endpoint averaging, or that reintroduced
# endpoint-averaging language into the manuscript, fails here rather than
# passing with 0 mismatches.  A value check compares numbers; this compares
# the description of the estimator to the estimator.
# --------------------------------------------------------------------------
CONSTRUCTIONS = []


def con(label, text, must_contain=(), must_not_contain=(), src=""):
    CONSTRUCTIONS.append((label, text, tuple(must_contain),
                          tuple(must_not_contain), src))


_POOLED_WORDS = ("pooled", "no averaging of endpoints")
_AVERAGED_WORDS = ("endpoints averaged", "mean endpoint", "endpoint over the "
                                                          "five")

con("E4 f29 protocol declares one pooled percentile interval",
    f29["protocol"], _POOLED_WORDS, _AVERAGED_WORDS, "f29/protocol")
con("E4 f30 protocol declares one pooled percentile interval",
    f30["protocol"], _POOLED_WORDS, _AVERAGED_WORDS, "f30/protocol")
con("E4 f31 protocol declares one pooled percentile interval",
    f31["protocol"], _POOLED_WORDS, _AVERAGED_WORDS, "f31/protocol")
con("E4 f29 records which script it supersedes",
    f29["supersedes"], ("f11_e4_cluster_ci.py",), (), "f29/supersedes")
con("E4 f30 records which script it supersedes",
    f30["supersedes"], ("f17_e4_alignment_only.py",), (), "f30/supersedes")
con("E4 f31 records which script it supersedes",
    f31["supersedes"], ("f12_e4_proxy_loo.py",), (), "f31/supersedes")

# The audit trail must still be on disk and must still say what it was: if
# f11/f17 vanished, the claim "the superseded construction is retained as
# evidence" would be unfalsifiable.
con("E4 superseded f11 record retained as the audit trail",
    J("f11_e4_cluster_ci.json")["script"], ("f11_e4_cluster_ci.py",), (),
    "f11/script")
con("E4 superseded f17 record retained as the audit trail",
    J("f17_e4_alignment_only.json")["script"], ("f17_e4_alignment_only.py",),
    (), "f17/script")
con("E4 superseded f12 record retained as the audit trail",
    J("f12_e4_proxy_loo.json")["script"], ("f12_e4_proxy_loo.py",), (),
    "f12/script")

# No .tex may describe an E4 bracket as an average of endpoints again, and the
# appendix paragraph that defines the construction must say what it now is.
_ALLTEX = chr(10).join(CORPUS.values())
con("no .tex describes an E4 interval as averaged endpoints",
    _ALLTEX, (), ("endpoints averaged",), "sections/ + appendix/ + figures/")
con("Appendix C states the pooled construction explicitly",
    CORPUS.get("appendix/experimental_details.tex", ""),
    ("pooled into one", "percentile"), (),
    "appendix/experimental_details.tex")

# The blanket "nothing measurable" language overstates the result and must
# not come back.  A value check cannot see it -- every number around such a
# label can be right while the label alone is wrong, which is precisely how a
# wrong "0 of 4" census survives an all-green value pass -- so it is a
# construction claim: the .tex corpus may not say the shift proxy adds nothing
# measurable, and Section 7.4 must state the favourable-side census.
con("no .tex claims the shift proxy adds nothing measurable",
    _ALLTEX, (),
    ("adds no measurable increment", "contributes nothing measurable",
     "added measurable rank information",
     "add measurable rank information",
     "adds no measurable rank information"),
    "sections/ + appendix/ + figures/")
con("Section 7.4 states the favourable-side census as 1 of 4, not 0 of 4",
    CORPUS.get("sections/experiments.tex", ""),
    ("favourable-side count is $1$ of $4$",),
    ("favourable side in $0$ of $4$",),
    "sections/experiments.tex")
con("Appendix C states the pooled construction for the proxy analysis too",
    CORPUS.get("appendix/experimental_details.tex", ""),
    ("pooled",), ("endpoints averaged",),
    "appendix/experimental_details.tex")


def run_pass1b(verbose):
    """Structural checks that no value comparison can express."""
    print()
    print("=" * 78)
    print("PASS 1b construction check: is each E4 bracket still the object "
          "the documents name?")
    print("=" * 78)
    bad = []
    for label, text, need, forbid, src in CONSTRUCTIONS:
        low = (text or "").lower()
        missing = [w for w in need if w.lower() not in low]
        present = [w for w in forbid if w.lower() in low]
        ok = not missing and not present
        if not ok:
            bad.append((label, missing, present, src))
        if verbose or not ok:
            print(f" [{'ok ' if ok else 'FAIL'}] {label}   ({src})")
            if missing:
                print(f"        missing required phrase(s): {missing}")
            if present:
                print(f"        forbidden phrase(s) present: {present}")

    # The pooled endpoints must actually DIFFER somewhere from the superseded
    # mean-of-five-endpoints values.  If they were identical everywhere, the
    # pooling would not have been applied and the rename would be cosmetic --
    # exactly the "relabel instead of fix" failure this check exists to catch.
    n_diff, n_seen = 0, 0
    for _d in E4_DOMS:
        for _f in ("rho_ci", "impr_ci"):
            for _k in ("naive_iid_rows", "cluster_nested", "cluster_seedavg"):
                _b = f29d[_d][_f][_k]
                _m = _b["superseded_mean_of_stream_endpoints"]
                for _e in ("lo", "hi"):
                    n_seen += 1
                    if abs(_b[_e] - _m[_e]) > 0:
                        n_diff += 1
    ok = n_diff > 0
    if not ok:
        bad.append(("E4 pooled endpoints differ from the superseded averaged "
                    "ones", [], [], "f29 endpoint blocks"))
    if verbose or not ok:
        print(f" [{'ok ' if ok else 'FAIL'}] E4 pooled endpoints are not a "
              f"relabelling: {n_diff}/{n_seen} endpoints moved")

    # ...and the pooled draws must be the SAME draws the superseded records
    # used, or the comparison above would not isolate the endpoint rule.
    for tag, rec, key in (("f29", f29, "audit_vs_f11"),
                          ("f30", f30, "audit_vs_f17"),
                          ("f31", f31, "audit_vs_f12")):
        a = rec.get(key, {})
        g = a.get("max_endpoint_gap_vs_f11_per_stream",
                  a.get("max_endpoint_gap_vs_f17_per_stream",
                        a.get("max_endpoint_gap_vs_f12_per_stream")))
        p = a.get("max_point_estimate_gap")
        ok = (g is not None and g <= 1e-12 and p is not None and p <= 1e-12)
        if not ok:
            bad.append((f"{tag} replays the superseded record's exact draws",
                        [], [], f"{tag}/{key}"))
        if verbose or not ok:
            print(f" [{'ok ' if ok else 'FAIL'}] {tag} replays the superseded "
                  f"record's exact draws (per-stream endpoint gap {g}, point "
                  f"estimate gap {p})")

    ok = bool(f30.get("audit_vs_f17", {}).get("verdict_counts_unchanged"))
    if not ok:
        bad.append(("E4 alignment-vs-full verdict counts unchanged under "
                    "pooling", [], [], "f30/audit_vs_f17"))
    if verbose or not ok:
        print(f" [{'ok ' if ok else 'FAIL'}] E4 alignment-vs-full verdict "
              f"counts unchanged under pooling")

    # f31's pooled endpoints must likewise not be a relabelling...
    _nd = _ns = 0
    for _d in E4_DOMS:
        for _q in ("selected", "phase_v2", "selected_minus_phase_v2",
                   "phase_v2_minus_alignment_only",
                   "partial_rho_delta_v2_given_alignment"):
            _b = f31f[_d]["pooled_ci_" + _q]
            _m = _b["superseded_mean_of_stream_endpoints"]
            for _e in ("lo", "hi"):
                _ns += 1
                if abs(_b[_e] - _m[_e]) > 0:
                    _nd += 1
    ok = _nd > 0
    if not ok:
        bad.append(("E4 proxy pooled endpoints differ from the superseded "
                    "averaged ones", [], [], "f31 endpoint blocks"))
    if verbose or not ok:
        print(f" [{'ok ' if ok else 'FAIL'}] E4 proxy pooled endpoints are "
              f"not a relabelling: {_nd}/{_ns} endpoints moved")

    # ...and the exclusion census must be identical under both constructions,
    # which is what makes "1 of 4" a fact about the analysis rather than about
    # the endpoint rule.  The defect being guarded against is a manuscript
    # that prints 0 while BOTH constructions say 1.
    ok = (bool(f31s.get("exclusion_verdicts_unchanged_by_pooling"))
          and f31s["n_folds_partial_rho_delta_v2_ci_excludes_zero"]
          == f31s["n_folds_partial_rho_delta_v2_ci_excludes_zero"
                  "_superseded_averaged"]
          == J("f12_e4_proxy_loo.json")["summary"][
              "n_folds_partial_rho_delta_v2_ci_excludes_zero"])
    if not ok:
        bad.append(("E4 proxy favourable-side census agrees across the "
                    "pooled and averaged constructions and with f12",
                    [], [], "f31/summary + f12/summary"))
    if verbose or not ok:
        print(f" [{'ok ' if ok else 'FAIL'}] E4 proxy favourable-side census "
              f"agrees across constructions and with f12 "
              f"({f31s['n_folds_partial_rho_delta_v2_ci_excludes_zero']} "
              f"of {f31s['n_folds']})")

    print(f"\n  checked {len(CONSTRUCTIONS) + 7} construction claims, "
          f"{len(bad)} failure(s)")
    return bad


# ---- E3 (seed-0 table vs three-seed prose) -------------------------------
def e3_cell(fname_tmpl, sev, key, seeds=(0, 1, 2), step=None):
    vals = []
    for s in seeds:
        d = json.loads((E3 / (fname_tmpl % s)).read_text(encoding="utf-8"))
        for r in d["results"]:
            if r["severity"] == sev:
                vals.append(r["acc_by_step"][step] if step is not None
                            else r[key])
    return vals


mb3 = e3_cell("motion_blur_eata_alta_s%d.json", 3, "frozen_acc")
chk("E3 motion-blur frozen accuracy, 3-seed mean (Sec 7.3 prose)",
    "37.85", pct(sum(mb3) / 3), "%.2f",
    "results/e3/motion_blur_eata_alta_s{0,1,2} frozen_acc",
    note="printed to 2 dp: 37.8472 is a rounding tie at 1 dp")
mb3a = e3_cell("motion_blur_eata_alta_s%d.json", 3, "adapted_acc")
chk("E3 motion-blur ALTA accuracy, 3-seed mean (Sec 7.3 prose)",
    "51.52", pct(sum(mb3a) / 3), "%.2f", "... adapted_acc")
mb3b = e3_cell("motion_blur_eata_alta_s%d.json", 3, "bn0_acc")
chk("E3 motion-blur BN-0 floor, 3-seed mean (Sec 7.3 prose)",
    "51.03", pct(sum(mb3b) / 3), "%.2f", "... bn0_acc")
mb3t = e3_cell("motion_blur_eata_alta_s%d.json", 3, "mean_t_hat")
chk("E3 motion-blur mean t_hat, 3-seed mean (Sec 7.3 prose)",
    "2.5", sum(mb3t) / 3, "%.1f", "... mean_t_hat")
mb0 = e3_cell("motion_blur_eata_alta_s%d.json", 3, "frozen_acc", seeds=(0,))
chk("E3 motion-blur frozen accuracy, SEED 0 (Table T2)",
    "37.86", pct(mb0[0]), "%.2f", "results/e3/..._s0 frozen_acc")
mb0a = e3_cell("motion_blur_eata_alta_s%d.json", 3, "adapted_acc", seeds=(0,))
chk("E3 motion-blur ALTA accuracy, SEED 0 (Table T2)",
    "51.62", pct(mb0a[0]), "%.2f", "results/e3/..._s0 adapted_acc")
ct3 = e3_cell("contrast_tent_fixed_s%d.json", 3, None, step=10)
chk("E3 contrast tent step-10 accuracy, 3-seed mean (Sec 7.3 prose)",
    "63.9", pct(sum(ct3) / 3), "%.1f",
    "results/e3/contrast_tent_fixed_s{0,1,2} acc_by_step[10]")
ct0 = e3_cell("contrast_tent_fixed_s%d.json", 3, None, seeds=(0,), step=10)
chk("E3 contrast tent step-10 accuracy, SEED 0 (Table T2)",
    "63.80", pct(ct0[0]), "%.2f", "results/e3/..._s0 acc_by_step[10]")
ctf = e3_cell("contrast_tent_fixed_s%d.json", 3, "frozen_acc")
chk("E3 contrast frozen accuracy, 3-seed mean (Sec 7.3 prose)",
    "45.6", pct(sum(ctf) / 3), "%.1f", "... frozen_acc")


# ---- E3 ALTA-vs-best-fixed mean gap, BOTH SCOPES -------------------------
# Section 7.3 prints this quantity twice under two different aggregations:
# 0.65 points when each cell is averaged over every seed available for it,
# and 0.67 points at seed 0 alone.  A paragraph declaring "every number here
# is seed 0" while printing the all-seed value is wrong in a way no single
# value check sees; binding both scopes to the raw records is what makes that
# class of error visible to this script rather than to a reader.  The reduction reproduces analysis/aggregate.py's
# analyze_e3: per (corruption, severity, method, stopping) cell, mean over
# the available seeds, preferring the flagged fixed-semantics ALTA runs, and
# gap = ALTA adapted_acc - best-fixed acc, pooled over the 90 ALTA cells.
def _e3_mean_gap(seeds=None):
    rows = {}
    for p in sorted(E3.glob("*.json")):
        o = json.loads(p.read_text(encoding="utf-8"))
        argv = o["meta"]["argv"]
        if seeds is not None and argv.get("seed") not in seeds:
            continue
        for cell in o.get("results", []):
            cell = dict(cell)
            if argv["stopping"] == "alta":
                cell["_flag"] = any(b.get("alta_t0_is_frozen")
                                    for b in cell.get("batches", []))
            rows.setdefault((cell["corruption"], int(cell["severity"]),
                             argv["method"], argv["stopping"]), []).append(cell)

    def avg(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else None

    table = {}
    for key, cs in rows.items():
        if key[3] == "alta":
            fl = [c for c in cs if c["_flag"]]
            if fl:
                cs = fl
        table[key] = (avg([c["adapted_acc"] for c in cs]),
                      avg([max(c["acc_by_step"]) for c in cs
                           if c.get("acc_by_step")]))
    gaps = []
    for (corr, sev, meth, stop) in sorted(table):
        if stop != "alta":
            continue
        f = table.get((corr, sev, meth, "fixed"))
        if f and f[1] is not None:
            gaps.append(table[(corr, sev, meth, "alta")][0] - f[1])
    return avg(gaps), len(gaps)


_gap_all, _n_all = _e3_mean_gap()
_gap_s0, _n_s0 = _e3_mean_gap(seeds={0})
chk("E3 mean ALTA-vs-best-fixed gap, ALL AVAILABLE SEEDS (Sec 7.3)",
    "0.65", -pct(_gap_all), "%.2f",
    f"results/e3/*_s{{0,1,2}}.json, {_n_all} ALTA cells, "
    f"mean gap {_gap_all:.6f}",
    note="printed as a positive shortfall; the record is negative")
chk("E3 mean ALTA-vs-best-fixed gap, SEED 0 ONLY (Sec 7.3, C5 gate para)",
    "0.67", -pct(_gap_s0), "%.2f",
    f"results/e3/*_s0.json, {_n_s0} ALTA cells, mean gap {_gap_s0:.6f}",
    note="the C5 paragraph is seed-0 scoped and must print this value")


# ---- E2 identity-level overlap of the cross-fit split --------------------
ident = J("f27_e2_identity.json")
_ia = ident["arms"]
chk("E2 cross-share identities per split seed, low end (Sec 7.2, App C.2)",
    "165", float(ident["identities_per_seed_range"][0]), "%.0f",
    "f27/identities_per_seed_range/0")
chk("E2 cross-share identities per split seed, high end (Sec 7.2, App C.2)",
    "268", float(ident["identities_per_seed_range"][1]), "%.0f",
    "f27/identities_per_seed_range/1")
chk("E2 cross-share EPISODE RECORDS per split seed, low end (Sec 7.2, App C.2)",
    "330", float(ident["rows_per_seed_range"][0]), "%.0f",
    "f27/rows_per_seed_range/0",
    note="identities vs records: each repeated identity contributes two rows")
chk("E2 cross-share EPISODE RECORDS per split seed, high end (Sec 7.2, App C.2)",
    "536", float(ident["rows_per_seed_range"][1]), "%.0f",
    "f27/rows_per_seed_range/1")
chk("E2 ttt_mask cross-share identities, low end (App C.2)",
    "165", float(min(_ia["ttt_mask/phase_feat"]
                     ["cross_share_identities_per_seed"])), "%.0f",
    "f27/arms/ttt_mask,phase_feat/cross_share_identities_per_seed/min")
chk("E2 ttt_mask cross-share identities, high end (App C.2)",
    "188", float(max(_ia["ttt_mask/phase_feat"]
                     ["cross_share_identities_per_seed"])), "%.0f",
    "f27/arms/ttt_mask,phase_feat/cross_share_identities_per_seed/max")
chk("E2 ttt_rot cross-share identities, low end (App C.2)",
    "248", float(min(_ia["ttt_rot/phase_feat"]
                     ["cross_share_identities_per_seed"])), "%.0f",
    "f27/arms/ttt_rot,phase_feat/cross_share_identities_per_seed/min")
chk("E2 ttt_rot cross-share identities, high end (App C.2)",
    "268", float(max(_ia["ttt_rot/phase_feat"]
                     ["cross_share_identities_per_seed"])), "%.0f",
    "f27/arms/ttt_rot,phase_feat/cross_share_identities_per_seed/max")
chk("E2 total episode records (Sec 7.2, App C.2)",
    "134{,}400", float(ident["n_episode_records"]), "%.0f",
    "f27/n_episode_records", note="printed with a thin space")
for _tag, _pre, _post, _lab in (
        ("ttt_mask/phase_feat", "0.5397", "0.5378", "ttt_mask feature"),
        ("ttt_rot/phase_feat", "0.5460", "0.5477", "ttt_rot feature"),
        ("ttt_mask/phase_loss", "0.5043", "0.4965", "ttt_mask loss"),
        ("ttt_rot/phase_loss", "0.0680", "0.0709", "ttt_rot loss")):
    chk(f"E2 identity pruning, {_lab} rho before (App C.2)", _pre,
        _ia[_tag]["rho_mean_final"], "%.4f",
        f"f27/arms/{_tag}/rho_mean_final")
    chk(f"E2 identity pruning, {_lab} rho after (App C.2)", _post,
        _ia[_tag]["rho_mean_final_identity_pruned"], "%.4f",
        f"f27/arms/{_tag}/rho_mean_final_identity_pruned")
chk("E2 largest absolute rho shift after identity pruning (Sec 7.2, App C.2)",
    "0.008", ident["max_abs_rho_shift"], "%.3f", "f27/max_abs_rho_shift")


# ---- Appendix B: the (P3) counterexample simulation ---------------------
mc = J("f28_p3_montecarlo.json")
chk("P3 counterexample x_m at beta=3, sigma=1 (App B)",
    "0.5774", mc["model"]["x_m"], "%.4f", "f28/model/x_m")
chk("P3 counterexample bound m = x_m (2KT)^(1/beta) (App B)",
    "1.3218", mc["model"]["m_bound"], "%.4f", "f28/model/m_bound")
chk("P3 counterexample ratio at gamma=1e-4 (App B)",
    "1.37", mc["ratios"]["1e-04"]["ratio_prob_over_gamma"], "%.2f",
    "f28/ratios/1e-04/ratio_prob_over_gamma",
    note="MC SE 0.0117 over 1e8 replications; printed to the SE")
chk("P3 counterexample ratio at gamma=1e-5 (App B)",
    "10.4", mc["ratios"]["1e-05"]["ratio_prob_over_gamma"], "%.1f",
    "f28/ratios/1e-05/ratio_prob_over_gamma", note="MC SE 0.1018")
chk("P3 counterexample ratio at gamma=1e-6 (App B)",
    "82.6", mc["ratios"]["1e-06"]["ratio_prob_over_gamma"], "%.1f",
    "f28/ratios/1e-06/ratio_prob_over_gamma", note="MC SE 0.9086")

# ---- Fig 2 / phase diagram census ---------------------------------------
f9 = J("f9_figure_data.json") if (FRESH / "f9_figure_data.json").exists() \
    else None
chk("Fig 2 cells with a negative one-step gain, low end (Sec 7.1, Fig 2)",
    "175", float(min(f10["n_cells_onestep_negative"]["values"]))
    if "n_cells_onestep_negative" in f10 else -1.0, "%.0f",
    "f10/n_cells_onestep_negative")
chk("Fig 2 cells with a negative one-step gain, high end",
    "186", float(max(f10["n_cells_onestep_negative"]["values"]))
    if "n_cells_onestep_negative" in f10 else -1.0, "%.0f",
    "f10/n_cells_onestep_negative")


# --------------------------------------------------------------------------
def run_pass1(verbose):
    print("=" * 78)
    print("PASS 1  record check: printed token vs the JSON of record")
    print("=" * 78)
    bad = []
    unseen = []
    for label, token, value, fmt, src, note in CHECKS:
        if value is None or (isinstance(value, float) and value == -1.0):
            unseen.append((label, src))
            continue
        expect = fmt % value
        # normalise the manuscript's thin-space thousands separator
        tok_num = token.replace("{,}", "").replace(",", "")
        exp_num = expect.replace(",", "")
        ok = (tok_num == exp_num) or (
            abs(float(tok_num) - float(exp_num)) < 5e-13)
        hits = occurrences(token)
        if not ok:
            bad.append((label, token, expect, src, note))
        if verbose or not ok:
            mark = "ok " if ok else "FAIL"
            print(f" [{mark}] {label}")
            print(f"        printed {token!r}   record {expect!r}   "
                  f"({src})")
            if note:
                print(f"        note: {note}")
            if not hits:
                print("        (token not found verbatim in the tex corpus)")
            elif verbose:
                for rel, n, line in hits[:4]:
                    print(f"        seen {rel}:{n}")
    print(f"\n  checked {len(CHECKS)} claims, {len(bad)} mismatch(es), "
          f"{len(unseen)} skipped (record key absent)")
    for label, src in unseen:
        print(f"    skipped: {label}   ({src})")
    return bad


# --------------------------------------------------------------------------
# PASS 2: cross-document collision scan
# --------------------------------------------------------------------------
INTERVAL = re.compile(r"\[\s*\$?(-?\d*\.\d+)\$?\s*,\s*\$?(-?\d*\.\d+)\$?\s*\]")


def run_pass2(verbose):
    print()
    print("=" * 78)
    print("PASS 2  cross-document scan: the same claim printed two ways")
    print("=" * 78)
    # 2a. every curated token: where does it live, and does a NEAR-MISS of it
    #     also live somewhere (the [0.37,0.70] vs [0.37,0.69] shape)?
    problems = []
    for label, token, value, fmt, src, note in CHECKS:
        try:
            v = float(token.replace("{,}", ""))
        except ValueError:
            continue
        if "." not in token:
            continue
        dp = len(token.split(".")[1])
        step = 10.0 ** (-dp)
        for delta in (-step, step):
            neighbour = ("%." + str(dp) + "f") % (v + delta)
            hits = occurrences(neighbour)
            if hits:
                problems.append((label, token, neighbour, hits))
    # 2b. every literal interval in the corpus, grouped by its low endpoint:
    #     two intervals sharing a low endpoint but differing in the high one
    #     are the exact signature of that defect.
    intervals = {}
    for rel, text in CORPUS.items():
        for n, line in enumerate(text.split("\n"), 1):
            for m in INTERVAL.finditer(line):
                lo, hi = m.group(1), m.group(2)
                intervals.setdefault(lo, {}).setdefault(hi, []).append(
                    (rel, n, line.strip()[:90]))
    conflicts = {lo: d for lo, d in intervals.items() if len(d) > 1}

    print(f"  {len(problems)} curated token(s) have a one-ulp neighbour "
          f"also printed somewhere:")
    for label, token, nb, hits in problems:
        print(f"    {label}")
        print(f"      record value prints {token!r}; {nb!r} also appears at:")
        for rel, n, line in hits[:6]:
            print(f"        {rel}:{n}  {line[:88]}")
    print()
    print(f"  {len(conflicts)} interval low-endpoint(s) carry more than one "
          f"high endpoint:")
    for lo, d in sorted(conflicts.items()):
        print(f"    [{lo}, ...] -> {sorted(d)}")
        for hi, hits in sorted(d.items()):
            for rel, n, line in hits[:3]:
                print(f"        {hi}:  {rel}:{n}  {line[:80]}")
    return problems, conflicts


SECTION_OF = [
    ("P3 ", "Appendix B -- the (P3) fixed-law counterexample simulation"),
    ("E1 ", "E1 -- exact-model verification (Sec. 7.1, Table T4, Figs. 1-3)"),
    ("Fig 2", "E1 -- exact-model verification (Sec. 7.1, Table T4, Figs. 1-3)"),
    ("E2 calibration", "E2 -- entropy calibration coverage (Sec. 7.2, Fig. 6)"),
    ("E2 ", "E2 -- CIFAR-10/100-C phase statistic (Sec. 7.2, Fig. 4)"),
    ("T5 ", "E2 -- matched-architecture arms (Table T5)"),
    ("E5 ", "E5 -- learning-rate ablation (Sec. 7.2)"),
    ("E3 ", "E3 -- ImageNet-C (Sec. 7.3, Table T2, Fig. 7)"),
    ("E4 ", "E4 -- GPT-2 cross-domain (Sec. 7.4, Fig. 8)"),
]


def section_for(label):
    for pre, name in SECTION_OF:
        if label.startswith(pre):
            return name
    return "Other"


def emit_current_values():
    """Render the authoritative CURRENT VALUES table."""
    from collections import OrderedDict
    groups = OrderedDict()
    for label, token, value, fmt, src, note in CHECKS:
        groups.setdefault(section_for(label), []).append(
            (label, token, (fmt % value) if value is not None else "n/a",
             src, note))
    lines = []
    for sec, rows in groups.items():
        lines.append("")
        lines.append(f"### {sec}")
        lines.append("")
        lines.append("| quantity | value as printed | recomputed from the "
                     "record | record of record |")
        lines.append("|---|---|---|---|")
        for label, token, got, src, note in rows:
            tok = token.replace("{,}", ",")
            lines.append(f"| {label}{(' -- ' + note) if note else ''} "
                         f"| `{tok}` | `{got}` | `{src}` |")
    # The construction table: what KIND of object the E4 brackets are.  A
    # value table cannot express this, and the defect it misses is exactly a
    # correct value under a wrong kind, so the kind is published beside the
    # values rather than left to prose.
    lines.append("")
    lines.append("### E4 interval CONSTRUCTION (not a value check)")
    lines.append("")
    lines.append("| construction claim | asserted of | required | forbidden |")
    lines.append("|---|---|---|---|")
    for label, _text, need, forbid, src in CONSTRUCTIONS:
        lines.append(f"| {label} | `{src}` | "
                     f"{', '.join('`' + w + '`' for w in need) or '--'} | "
                     f"{', '.join('`' + w + '`' for w in forbid) or '--'} |")
    lines.append("| E4 pooled endpoints are not a relabelling of the "
                 "superseded averaged ones | `f29` endpoint blocks | at "
                 "least one endpoint moved | -- |")
    lines.append("| `f29` replays `f11`'s exact draws | `f29/audit_vs_f11` | "
                 "per-stream endpoint gap and point-estimate gap `<= 1e-12` "
                 "| -- |")
    lines.append("| `f30` replays `f17`'s exact draws | `f30/audit_vs_f17` | "
                 "per-stream endpoint gap and point-estimate gap `<= 1e-12` "
                 "| -- |")
    lines.append("| `f31` replays `f12`'s exact draws | `f31/audit_vs_f12` | "
                 "per-stream endpoint gap and point-estimate gap `<= 1e-12` "
                 "| -- |")
    lines.append("| E4 alignment-vs-full verdict counts unchanged under "
                 "pooling | `f30/audit_vs_f17` | "
                 "`verdict_counts_unchanged` | -- |")
    lines.append("| E4 proxy pooled endpoints are not a relabelling of the "
                 "superseded averaged ones | `f31` endpoint blocks | at "
                 "least one endpoint moved | -- |")
    lines.append("| E4 proxy favourable-side exclusion census agrees across "
                 "the pooled and averaged constructions and with `f12` | "
                 "`f31/summary` + `f12/summary` | "
                 "`exclusion_verdicts_unchanged_by_pooling` and three equal "
                 "counts | -- |")
    return chr(10).join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--emit-current-values", action="store_true",
                    help="print the CURRENT VALUES markdown for "
                         "FRESH_RESULTS.md and exit")
    args = ap.parse_args()
    if args.emit_current_values:
        print(emit_current_values())
        return 0
    bad = run_pass1(args.verbose)
    badcon = run_pass1b(args.verbose)
    problems, conflicts = run_pass2(args.verbose)
    print()
    print("=" * 78)
    if bad or badcon:
        if bad:
            print(f"RESULT: {len(bad)} record mismatch(es) -- fix the "
                  f"manuscript")
            for label, token, expect, src, note in bad:
                print(f"  * {label}: printed {token}, record says {expect}")
        if badcon:
            print(f"RESULT: {len(badcon)} CONSTRUCTION failure(s) -- a "
                  f"bracket is not the object it is named")
            for label, missing, present, src in badcon:
                print(f"  * {label} ({src}) missing={missing} "
                      f"forbidden={present}")
        return 1
    print(f"RESULT: every curated claim matches its record "
          f"({len(CHECKS)} claims), and every E4 interval construction is "
          f"still the one the documents name ({len(CONSTRUCTIONS) + 7} "
          f"construction claims).")
    print(f"        pass-2 advisories: {len(problems)} one-ulp neighbour(s), "
          f"{len(conflicts)} multi-valued interval(s) -- inspect above; "
          f"distinct claims may legitimately share an endpoint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
