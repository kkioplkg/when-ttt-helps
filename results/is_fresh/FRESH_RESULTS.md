# FRESH_RESULTS — table of record for the Information Sciences retarget

Fresh-measurement suite for the TTT theory paper. Scope: audit every headline
empirical number in the original manuscript, classify it MEASURED or ANALYTIC,
and regenerate the ANALYTIC ones from genuinely simulated trajectories or real
model records.

* Code: `experiments/ttt/is_fresh/` (`f1`..`f9` for the original
  audit; `f8b`, `f10`..`f15`, `fig_*`, `make_release_zip.py` for the
  review round 1 response in the final section).
* Outputs: `experiments/results/is_fresh/*.json` (this directory).
* Seeds: **20260801–20260805** throughout §§1–5; the round-1 additions use
  **20260806–20260810** for new resampling/GPU work. No seed used by the
  original pipeline (0, 1, 2, 42, 43, 100+, 999+) is reused anywhere.
* Machinery: `simulate_scalar` and `core.alta.alta_run` are imported unchanged
  from the original pipeline. Closed forms appear only inside explicitly
  labelled reproduction checks, never as a headline number.
* Suite identifiers: this file uses the **record-tree** names, which are the
  directory and filename stems (`e1`, `e2`, `e3`, `e4`, `e5`). The article
  numbers the three suites it reports E1, E2 and **E3**, and its E3 is this
  file's **E4** (the GPT-2 domain-shift study under `experiments/results/e4/`,
  runner `experiments/ttt/e4_gpt2/`). The record names are deliberately stable,
  so every archived pointer keeps resolving; nothing is renamed on disk. This
  file's `e3` is the ImageNet-C suite, which is **not** part of the submission
  and whose records do not ship.
* Framing: **fix-forward.** Where a fresh measurement lands near the original
  number, that is a confirmation on stronger evidence and is stated as one.
  Where it differs, the measured value is reported plainly.

Excluded and never read: `_quarantined_versions/`, `results/revision/`,
`results/nn_instrumented/`, `results/e6_casting/`,
`results/e1/e1b_montecarlo.json`, `ttt/nn_instr/`, `ttt/revision/`, `e6/`.
A file `e1_synthetic/run_e1b_montecarlo.py` exists in the original tree whose
output JSON is on the exclusion list; it was **not** opened and nothing here
derives from it. Every script in `is_fresh/` was written from scratch against
`run_e1.py`, `core/alta.py`, and `analysis/aggregate.py`.

---

# CURRENT VALUES — the authoritative table of record (added round 9, 2026-08-04)

**Read this section, not the history below, for any number that goes into the
submission.** External review round 8, item 5.4:

> FRESH_RESULTS.md retains earlier values as an audit trail. That is
> acceptable, but it makes the file difficult to use as the authoritative
> current-value source. Add a final, clearly labelled "current manuscript
> values" section containing every number that should appear in the
> submission. Historical entries should be explicitly labelled superseded.

**Everything after this section is HISTORY.** Sections §1–§5 and every
"Round N" block below record how each number was arrived at, including values
that were later revised. Where a value below disagrees with anything later in
this file, **the value below wins** and the earlier one is superseded. The
history is retained deliberately (it is the audit trail the review process was
run against) and nothing has been deleted from it.

Each row below is machine-checked. `experiments/ttt/is_fresh/`-adjacent script
`r9_reconcile.py` (round-9 fix F8) reloads the JSON of record named in the last
column, re-applies the manuscript's own rounding, and asserts the printed token
matches. At the current build: **197 curated headline and repeated numerical
claims checked, 0 mismatches**, plus **22 construction claims, 0 failures** in
the PASS 1b check. A second,
model-free pass scans every `.tex` of the article (`sections/`, `figures/`)
and of the Supplementary Material for two different printed values of the
same interval; it reports
**0 conflicting intervals** after the round-9 fixes (before them it flagged
exactly the round-8 defect, `[0.37, 0.69]` vs `[0.37, 0.70]` for ttt_rot).

**What the curated table is, and what it is not** (external review round 13,
section 4). It is a **curated headline-value and rounding audit**: a
hand-maintained list of claims — the current count is the one printed two
paragraphs above and by the script itself, and is deliberately not repeated
here — each bound by JSON pointer to a record of record, checked for value and
for the manuscript's own rounding. It is **not**
an exhaustive binding of every number in the manuscript, and it cannot be one:

* the two Appendix B fixed-law numerical thresholds (`4.15e-8`, `4.24e-14`)
  are analytic and are **not bound** by the table — they were verified by
  independent recomputation, not by this gate;
* the three Appendix B Monte Carlo ratios **are** bound, but their printed
  Monte Carlo standard errors are **not separately asserted** as checked
  claims;
* a **semantic** error — for example calling a pair of split-averaged
  endpoints a confidence interval — is invisible to a JSON-pointer value
  check, because the value is right and only the label is wrong; that class of
  defect is caught by reading, not by this gate (it is exactly how the
  round-13 Figure 4 defect, and then round 15's E4 defect, each survived a
  green run. Round 16 closes that hole **for the E4 brackets specifically**
  with the PASS 1b construction check; every other label in the manuscript is
  still verified by reading, not by this gate;
* proof-only constants, boundary-case quantifiers and domain restrictions
  (such as the $t \ge 1$ restriction now carried by Lemma 51(i)) are outside
  its scope entirely.

The count is therefore a coverage statement about a curated list, and
"N claims, 0 mismatches" must never be paraphrased as "every number and every
statistical interpretation in the manuscript is machine-bound".

Known superseded values elsewhere in this file, called out explicitly:

| superseded value | where it still appears below | current value | why |
|---|---|---|---|
| ttt_rot clustered CI `[0.37, 0.70]` | §"Round 1" A9 row and the round-1 handoff map | **`[0.37, 0.69]`** | rounding slip: the record `f22_e2_crossfit_feat_summary.json` (and its pre-correction ancestor `f8_e2_crossfit_summary.json`) both store `hi_mean = 0.6945060330315526`, which is `0.69`. Review round 8, Finding 3. Corrected in place below with a `[R9]` marker |
| E2 loss-proxy correlations computed with an **unsigned** alignment factor (`0.603 / 0.573 / 0.588` and the ttt_rot / ttt_mask loss numbers of the round-1 A9 row) | §"Round 1", §"Round 3" | the signed values in the E2 tables below | a sign-dropping bug in the loss proxy, found and fixed in round 7; see §R7.1. The unsigned runs ship unmodified so the correction stays auditable |
| E2 same-sample (non-cross-fit) correlations `0.622 / 0.686 / 0.694 / 0.742` | §1–§5 claim audit, A9 | the cross-fit values below | the same-sample values are in-sample; the manuscript reports cross-fit and prints the same-sample ones only in grey on Figure 4 |
| E1 single-seed (seed 42) risk-curve error `1.8 %` | §1 claim audit, A1 | **`1.15 %`** (published normalisation) / **`2.23 %`** (pointwise) | superseded by the five-seed fresh measurement `f7`/`f26` |
| "rank-stable across learning rates, ρ = 0.60/0.57/0.59" | §1–§5, and the archived E5 claim | in-sample **`0.77/0.32/0.59`**, cross-fit **`0.49/0.16/0.32`** | those were the unsigned-numerator values; the signed statistic is *positive at all three rates* but *not* stable in magnitude (`f25`, `verdict.rank_stable_claim_survives = false`) |

Provenance convention in the tables below: `fNN/...` is a JSON pointer into
`experiments/results/is_fresh/fNN_*.json`; `results/e3/...` is a raw record
under `experiments/results/e3/`.

**Two labelling corrections made in round 10 (external review round 9,
findings 3.2 and 3.4). Neither changes a number; both change what a number is
called.**

1. **E2 "clustered CI" rows are `lo_mean` / `hi_mean`, i.e. SPLIT-AVERAGED
   ENDPOINTS, not a percentile interval.** The corruption-clustered bootstrap
   (`B = 1000`, 15 corruption clusters) runs *inside* each of the five split
   seeds; the printed pair is the mean over splits of the per-split 2.5 % and
   97.5 % endpoints. That is a stability summary of five separately clustered
   intervals and does not fold the split randomness into one bootstrap
   distribution, so it carries no exact coverage guarantee and must not be
   called a "95 % interval". The manuscript now calls these *split-averaged
   clustered endpoints* everywhere they appear (Section 7.2, Table T5,
   Figure 4 caption, Appendix C). The sign conclusions are unaffected: every
   split-specific interval already excludes zero on its own, the minimum
   per-split lower endpoint being `lo_min = 0.1903982` for ttt_mask mean-final
   and `lo_min = 0.2753899` for ttt_rot mean-final
   (`f22/per_method/*/ci_mean_final_clustered/lo_min`). **Round 11: the
   CURRENT VALUES tables below now carry the label *split-averaged clustered
   endpoint, low/high* directly**, so no reinterpretation is needed.

   **Round 14 correction to the previous sentence of this item (external
   review round 13, section 1.2).** Through round 13 this file stated that the
   phrase "clustered CI" survived *only* in the round-8 correction row above
   and in the superseded HISTORY section. That was **false**, and is
   withdrawn. Two *current* artefacts still carried the wrong label:

   * the labels drawn **inside Figure 4** read `clustered 95% CI`, as did the
     docstring and the annotation code of its generator
     `experiments/ttt/is_fresh/fig_f4_e2.py`; and
   * the console line of `experiments/ttt/is_fresh/f16_e2_gn_analysis.py`
     printed `clustered 95%`, so the *current* Table T5 run log
     `experiments/results/is_fresh/f23.log` repeated it 8 times.

   The prose, captions and Table T5 of the manuscript were already correct;
   the figure's own labels and the analysis console output were not. Both
   generators, the regenerated `F4_e2_phase.pdf` and the regenerated `f23.log`
   now say **split-averaged clustered endpoints**. This matters beyond
   wording: averaging the endpoints of five separately computed intervals does
   not in general produce an interval with the nominal coverage of the
   constituents, so "95% CI" asserts a coverage property these endpoints do
   not have.

   **The precise, scoped statement as of round 14** — stated carefully,
   because the round-13 defect was itself a scope error:

   > No **split-averaged endpoint pair** (`lo_mean` / `hi_mean` of any
   > `ci_*_clustered` block) is labelled a confidence interval in any current
   > artefact: not in `fig_f4_e2.py` or the rendered `F4_e2_phase.pdf`, not in
   > `f16_e2_gn_analysis.py` or the current `f23.log`, not in any `.tex`
   > source, caption or table, and not in the CURRENT VALUES tables of this
   > file. Those pairs are called *split-averaged clustered endpoints*
   > everywhere.

   The literal string `clustered 95%` does still occur, legitimately, in two
   places, and neither is a split-averaged pair:

   * **E4 and Figure 8**, where `f29_e4_pooled_ci.py`,
     `f30_e4_alignment_pooled.py` and `fig_f8_domains.py` report
     *document-clustered 95% intervals* — one percentile pair of a single
     pooled bootstrap distribution of 10,000 resamples over the 500 documents
     of a domain, with no averaging of endpoints across anything. Those
     genuinely are 95% percentile intervals and are correctly named.
     **This bullet was false when written** and is corrected in round 16; see
     the round-16 correction immediately below.
   * the round-8 correction row above and the superseded HISTORY section
     below, which record what earlier revisions printed and are labelled as
     history (external review round 10, finding E2; round 13, section 1.2).

   **Round 15 correction to the scoped statement above (external review round
   14, finding 2).** The round-14 statement was itself still false in its last
   clause. Four rows of the CURRENT VALUES table below — the E2 *loss-proxy*
   endpoint pairs for `ttt_rot` and `ttt_mask` — were labelled **"CI low"**
   and **"CI high"**, so this file contradicted its own guarantee that no
   split-averaged pair is called a confidence interval "in the CURRENT VALUES
   tables of this file". The round-11 sweep quoted above had renamed the
   feature-proxy, tent and pseudo-label rows and missed the loss-proxy ones.
   The four labels are generated, not typed: they come from four `chk(...)`
   entries in `experiments/ttt/is_fresh/r9_reconcile.py`, which now read
   *split-averaged clustered endpoint, low/high* like every sibling row, and
   the CURRENT VALUES section below was regenerated with
   `r9_reconcile.py --emit-current-values`. **The numbers did not move**:
   `-0.13`, `0.25`, `0.27`, `0.70` are the same `lo_mean` / `hi_mean` fields
   of `f22c_e2_crossfit_loss_summary.json` they always were, and the
   regenerated table differs from its predecessor in exactly those four label
   cells and nowhere else. Only the label was wrong — which is precisely the
   class of defect the reconciliation pass cannot see, as its own header
   warns. With those four rows renamed the scoped statement above now holds
   as written.

   **Round 16 correction to the E4 bullet above (external review round 15,
   substantive finding 1).** The bullet said that the E4 brackets were "a
   single clustered bootstrap over the 500 documents of a domain, with no
   averaging of endpoints across anything". That was **not true of the
   analysis of record**. `f11_e4_cluster_ci.py` and `f17_e4_alignment_only.py`
   ran *five* independent document-clustered bootstraps (`B = 2000`, RNG seeds
   20260806–10 and 20260811–15), took the 2.5/97.5 percentile pair of each,
   and reported the arithmetic **mean of the five lower endpoints and the mean
   of the five upper endpoints** — see their `agg()` / `agg_endpoints()`
   helpers. Appendix C disclosed this correctly ("endpoints averaged over five
   bootstrap seeds"); this file, the manuscript body, the Figure 8 caption and
   the generated release documentation contradicted it.

   A mean of five percentile endpoints is not a percentile of anything, so the
   named object was not the computed one. **The fix is the construction, not
   the label.** `f29_e4_pooled_ci.py` and `f30_e4_alignment_pooled.py` replay
   the same five RNG streams — bit-for-bit, asserted at `1e-12` against the
   f11/f17 records — **pool their 5 × 2000 = 10,000 draws into one empirical
   distribution per quantity, and read one 2.5/97.5 percentile pair off it**.
   The two constructions therefore differ *only* in the rule applied to an
   identical set of draws.

   This is a milder defect than the E2 one it resembles, and the difference is
   why the pooled fix is available at all: E2's `lo_mean`/`hi_mean` average
   across five distinct **data splits**, hence across five estimands, which is
   why those pairs are called *split-averaged clustered endpoints* and are
   never called intervals. The five E4 streams differ only in the **bootstrap
   RNG**, so they are five Monte Carlo estimates of one common bootstrap-law
   endpoint.

   **What moved.** No point estimate (asserted equal at `0.0`), no sign, no
   ordering, and none of the five verdict counts behind the alignment-vs-full
   conclusion (`4/4` higher, `3/4` favouring alignment, `1/4` containing zero,
   `0/4` favouring the full statistic — each asserted unchanged inside `f30`).
   The largest change to any endpoint anywhere is **0.0022** (PubMed
   perplexity improvement, seed-averaged upper endpoint); the largest change
   to a design effect is **0.0097**. At printed precision this moves seven
   tokens in the manuscript and this file.

   **A second, independent error was exposed by binding the endpoints.** The
   PubMed paired-difference interval was printed in Section 7.4 as
   `[-0.003, +0.018]`, which matched **no record** in either construction: the
   pooled-row value is `[-0.002, +0.017]` and the seed-averaged value is
   `[-0.003, +0.019]`. That error predates the endpoint-averaging defect and
   is independent of it. It survived every previous green reconciliation run
   for one reason — **no E4 interval endpoint was bound at all**. All of them
   are now bound, together with a new `PASS 1b` construction check that
   asserts the E4 brackets are still built by pooling, in the records *and* in
   the `.tex` corpus.

   `f11_e4_cluster_ci.json` and `f17_e4_alignment_only.json` are retained,
   unmodified, as the audit trail of the superseded construction.

   **Round-17 completion (external review round 16, findings 1.1 and 1.2).**
   Round 16 fixed `f11`/`f17` and explicitly *declined* to fix `f12`, the
   third script with the same construction, on the reasoning that no `f12`
   endpoint was printed and its intervals were reported only qualitatively.
   Both halves of that reasoning were wrong, and the referee found the
   consequence: `f12`'s pairs **were** called bootstrap intervals in
   Section 7.4, Appendix C and this file, and the qualitative report was a
   census — "excludes zero on the favourable side in 0 of 4" — that
   **contradicted `f12`'s own record**, which says 1. `f31_e4_proxy_pooled.py`
   now applies the identical pooling remedy to `f12`, `f12` is retained
   unmodified as its audit trail, every `f31` endpoint and both exclusion
   counts are bound, and the curated table stands at **197 claims with 22
   construction claims**. The lesson this round records for the next one:
   when a defect is repaired in two of three scripts that share a
   construction, the third is not a lower-priority instance of the same
   defect, it is where the defect will next be found.
2. **E4: the document-clustering widening is NOT "almost exactly sqrt(3)".**
   The measured design effect
   (`f29/domains/*/{impr_ci,rho_ci}/cluster_nested/design_effect_vs_naive`) is
   `1.7690` (code), `1.7298` (legal), `1.5420` (PubMed), `1.7302` (WikiText)
   for the perplexity-improvement intervals and `1.6571`, `1.5677`, `1.5660`,
   `1.5524` in the same domain order for the correlation intervals: an overall
   range of roughly **1.54–1.77**, straddling `sqrt(3) = 1.732` rather than
   reproducing it. The manuscript and Appendix C now print the empirical range
   and the per-domain design effects. The claim at line ~695 of the history
   below ("almost exactly sqrt(3)") is **superseded** by this row.
   (Round 16: these are the pooled-draw design effects. The superseded
   endpoint-averaged values were `1.7593` / `1.7271` / `1.5474` / `1.7295` and
   `1.6542` / `1.5701` / `1.5677` / `1.5459`, an overall range of 1.55–1.76;
   the largest change is 0.0097 and the conclusion of this row is unaffected.)

### E1 -- exact-model verification (Sec. 6.1, Figs. 1-2)

| quantity | value as printed | recomputed from the record | record of record |
|---|---|---|---|
| E1 pointwise risk-curve error, mean of the five seedwise maxima (Sec 7.1, S4a, Fig 1 caption, Sec S8) | `2.23` | `2.23` | `f26/item1_and_3_curve_match/pointwise_sup_t_absdiff_over_theory/mean` |
| E1 pointwise error, S4 row (a) as a fraction | `0.0223` | `0.0223` | `same record, S4 prints the fraction` |
| E1 pointwise risk-curve error, largest single (cell, step) value over all five seeds (Sec 7.1, S4a, Fig 1 caption, Sec S8) | `2.62` | `2.62` | `f26/item1_and_3_curve_match/pointwise_sup_t_absdiff_over_theory/max` |
| E1 pointwise error, worst case over the grid, S4 second row as a fraction | `0.0262` | `0.0262` | `same record, S4 prints the fraction` |
| E1 published-normalisation error (Sec 7.1, T4a, Fig 1 caption) | `1.15` | `1.15` | `f26/.../published_normalisation_max_absdiff_over_max_theory/mean` |
| E1 published-norm error, T4 fraction | `0.0115` | `0.0115` | `same record` |
| E1 max deviation in SE units | `3.61` | `3.61` | `f26/.../max_deviation_in_SE_units/true_max_over_all_seeds` |
| E1 number of (cell, step) comparisons over five seeds -- printed with a thin space | `60,150` | `60150` | `f26/.../n_comparisons_all_seeds` |
| E1 comparisons per seed -- printed with a thin space | `12,030` | `12030` | `f26/.../n_comparisons_per_seed` |
| E1 fixed-rule held-out sign accuracy (T4b, Sec 7.1) | `0.984` | `0.984` | `f26/item2_and_6_phase_boundary/fixed_rule_holdout_accuracy/mean` |
| E1 fixed-rule accuracy resolved at 3 SE (T4b) | `1.000` | `1.000` | `f26/.../fixed_rule_holdout_accuracy_resolved3se/mean` |
| E1 fitted-rule held-out accuracy (Sec 7.1) | `0.979` | `0.979` | `f26/.../fitted_rule_holdout_accuracy/mean` |
| E1 largest |z| of a fitted-rule miss (Sec 7.1) | `3.26` | `3.26` | `f26/.../max_abs_z_of_a_miss_fitted_holdout/max` |
| E1 fitted / theoretical one-step threshold (T4b, Fig 2 caption) | `0.968` | `0.968` | `f10/fitted_threshold_onestep/mean divided by eta/2` |
| E1 fraction of cells within 5%% of the measured oracle (T4c, Sec 7.1) | `1.00` | `1.00` | `f3/frac_risk_within_5pct_of_measured_oracle/mean` |
| E1 worst single cell-run relative stopping gap (Sec 7.1) | `0.0402` | `0.0402` | `f26/item4_optimal_stopping/.../true_worst_single_cell_run` |
| E1 per-seed worst cells, average (Sec 7.1) | `0.0212` | `0.0212` | `f26/item4_optimal_stopping/.../mean_of_per_seed_worst` |
| Fig 2 cells with a negative one-step gain, low end (Sec 7.1, Fig 2) | `175` | `175` | `f10/n_cells_onestep_negative` |
| Fig 2 cells with a negative one-step gain, high end | `186` | `186` | `f10/n_cells_onestep_negative` |

### Other

| quantity | value as printed | recomputed from the record | record of record |
|---|---|---|---|
| E1(e) mean relative gain at alpha=0 (T4e) | `0.64` | `0.64` | `f6/mean_relgain_by_alpha/0.0/mean` |
| E1(e) mean relative gain at alpha=1 (T4e) | `1.00` | `1.00` | `f6/mean_relgain_by_alpha/1.0/mean` |
| E1(e) alpha=1 minus alpha=0 margin (Sec 7.1) | `0.361` | `0.361` | `f6/margin_alpha1_minus_alpha0/mean` |
| E1(e) alpha=0 mean excess, 4dp (T4e, App C) | `0.0433` | `0.0433` | `f6/alpha0_mean_harm/mean` |
| E1(e) alpha=0 excess, low end (T4e, Sec 7.1, App C) | `-0.0236` | `-0.0236` | `f6/alpha0_mean_harm/min` |
| E1(e) alpha=0 excess, high end (T4e, App C) | `0.1673` | `0.1673` | `f6/alpha0_mean_harm/max` |
| E1(e) seeds with harm at alpha=0 (T4e, App C) -- printed as 4/5 | `4` | `4` | `f6/n_seeds_alpha0_harmful` |
| E1(f) max relative error of Var(u_t) vs sigma^2/N (T4f) | `0.0057` | `0.0057` | `f5/max_rel_err_variance_vs_sigma2_over_N/mean` |
| Remark 10 strictness witness: boundary_delta2_P (Sec 3, S1.3) -- bisected from the closed form; the script asserts the witness satisfies (P), t* < 1 and G(1) > 0 simultaneously | `9.749134` | `9.749134` | `f18/F_containment_strictness_witness/boundary_delta2_P` |
| Remark 10 strictness witness: boundary_delta2_I (Sec 3, S1.3) -- bisected from the closed form; the script asserts the witness satisfies (P), t* < 1 and G(1) > 0 simultaneously | `10.000625` | `10.000625` | `f18/F_containment_strictness_witness/boundary_delta2_I` |
| Remark 10 strictness witness: boundary_delta2_where_tstar_eq_1 (Sec 3, S1.3) -- bisected from the closed form; the script asserts the witness satisfies (P), t* < 1 and G(1) > 0 simultaneously | `10.260898` | `10.260898` | `f18/F_containment_strictness_witness/boundary_delta2_where_tstar_eq_1` |
| Remark 10 strictness witness: delta2 (Sec 3, S1.3) -- bisected from the closed form; the script asserts the witness satisfies (P), t* < 1 and G(1) > 0 simultaneously | `10.130761` | `10.130761` | `f18/F_containment_strictness_witness/delta2` |
| Remark 10 strictness witness: t_star_continuous (Sec 3, S1.3) -- bisected from the closed form; the script asserts the witness satisfies (P), t* < 1 and G(1) > 0 simultaneously | `0.7506` | `0.7506` | `f18/F_containment_strictness_witness/t_star_continuous` |
| Remark 10 strictness witness: (P) margin at the witness (Sec 3) -- printed as 9.79e-5 in the article and 9.787e-5 in the supplement | `9.79` | `9.79` | `f18/F_containment_strictness_witness/condition_P_margin` |
| Remark 10 strictness witness: one-step gain at the witness (Sec 3) -- positive, so (I) holds and the two criteria AGREE there | `3.25` | `3.25` | `f18/F_containment_strictness_witness/onestep_gain_G1` |

### E2 -- CIFAR-10/100-C phase statistic (Sec. 6.2, Fig. 3)

| quantity | value as printed | recomputed from the record | record of record |
|---|---|---|---|
| E2 ttt_rot mean-final rho (Sec 7.2, Fig 4) | `0.546` | `0.546` | `f22/per_method/ttt_rot/rho_mean_final/mean` |
| E2 ttt_rot split range low (Sec 7.2, Fig 4) | `0.511` | `0.511` | `f22/.../min` |
| E2 ttt_rot split range high (Sec 7.2, Fig 4) | `0.592` | `0.592` | `f22/.../max` |
| E2 ttt_rot split-averaged clustered endpoint, low (Sec 7.2, Fig 4) | `0.37` | `0.37` | `f22/.../ci_mean_final_clustered/lo_mean` |
| E2 ttt_rot split-averaged clustered endpoint, high (Sec 7.2, Fig 4) -- the Section 7 passage that prints this endpoint rounds to 0.69 | `0.69` | `0.69` | `f22/.../ci_mean_final_clustered/hi_mean` |
| E2 ttt_rot median-final rho (Sec 7.2) | `0.630` | `0.630` | `f22/.../rho_median_final/mean` |
| E2 ttt_mask mean-final rho (Sec 7.2, Fig 4) | `0.540` | `0.540` | `f22/per_method/ttt_mask/rho_mean_final/mean` |
| E2 ttt_mask split range low | `0.483` | `0.483` | `f22/.../min` |
| E2 ttt_mask split range high | `0.610` | `0.610` | `f22/.../max` |
| E2 ttt_mask split-averaged clustered endpoint, low | `0.25` | `0.25` | `f22/.../lo_mean` |
| E2 ttt_mask split-averaged clustered endpoint, high | `0.76` | `0.76` | `f22/.../hi_mean` |
| E2 ttt_mask median-final rho | `0.493` | `0.493` | `f22/.../rho_median_final/mean` |
| E2 loss proxy ttt_rot rho | `0.068` | `0.068` | `f22c/per_method/ttt_rot/rho_mean_final/mean` |
| E2 loss proxy ttt_rot range low | `0.014` | `0.014` | `f22c/.../min` |
| E2 loss proxy ttt_rot range high | `0.131` | `0.131` | `f22c/.../max` |
| E2 loss proxy ttt_rot split-averaged clustered endpoint, low | `-0.13` | `-0.13` | `f22c/.../lo_mean` |
| E2 loss proxy ttt_rot split-averaged clustered endpoint, high | `0.25` | `0.25` | `f22c/.../hi_mean` |
| E2 loss proxy ttt_mask rho | `0.504` | `0.504` | `f22c/per_method/ttt_mask/rho_mean_final/mean` |
| E2 loss proxy ttt_mask range low | `0.440` | `0.440` | `f22c/.../min` |
| E2 loss proxy ttt_mask range high | `0.538` | `0.538` | `f22c/.../max` |
| E2 loss proxy ttt_mask split-averaged clustered endpoint, low | `0.27` | `0.27` | `f22c/.../lo_mean` |
| E2 loss proxy ttt_mask split-averaged clustered endpoint, high | `0.70` | `0.70` | `f22c/.../hi_mean` |
| E2 deterministic tent rho (Sec 7.2, Fig 4) | `0.844` | `0.844` | `f22b/per_method/tent/rho_mean_final/mean` |
| E2 tent split range low | `0.832` | `0.832` | `f22b/.../min` |
| E2 tent split range high | `0.854` | `0.854` | `f22b/.../max` |
| E2 tent split-averaged clustered endpoint, low | `0.79` | `0.79` | `f22b/.../lo_mean` |
| E2 tent split-averaged clustered endpoint, high | `0.89` | `0.89` | `f22b/.../hi_mean` |
| E2 pseudo-label rho (Sec 7.2, Fig 4) | `0.828` | `0.828` | `f22b/per_method/pl/rho_mean_final/mean` |
| E2 pseudo-label split range low | `0.806` | `0.806` | `f22b/.../min` |
| E2 pseudo-label split range high | `0.849` | `0.849` | `f22b/.../max` |
| E2 pseudo-label split-averaged clustered endpoint, low | `0.72` | `0.72` | `f22b/.../lo` |
| E2 pseudo-label split-averaged clustered endpoint, high | `0.89` | `0.89` | `f22b/.../hi` |
| E2 fresh-GN feature proxy: episodes covered (Sec S7.3) | `11,520` | `11520` | `f38/fresh_remeasurement/n_matched` |
| E2 superseded cross-model join: episodes matched (Sec S7.3) | `300` | `300` | `f38/old_cross_model_join/n_matched` |
| E2 superseded cross-model join: per-cell minimum (Sec S7.3) | `5` | `5` | `f38/old_cross_model_join/per_cell_min` |
| E2 superseded cross-model join: per-cell maximum (Sec S7.3) | `9` | `9` | `f38/old_cross_model_join/per_cell_max` |
| E2 all-episode Spearman(alpha_ent, correct) | `0.863` | `0.863` | `f21/all_episodes/spearman_alpha_correct` |
| E2 temperature scaling, mean change over steps 1-2 in ABSOLUTE adapted loss (Sec 6.2; printed as a magnitude after "falls by") | `0.576` | `0.576` | `f34/mean_change_absolute_adapted_loss_steps_1_2` |
| E2 temperature scaling, mean change over steps 1-2 in EXCESS loss over each arm's OWN frozen baseline -- the C4-criterion estimand (Sec 6.2) | `0.384` | `0.384` | `f34/mean_change_excess_over_own_frozen_steps_1_2` |
| E2 temperature scaling, shift in the mean FROZEN baseline loss it induces -- the difference between the two estimands above (Sec 6.2) | `0.191` | `0.191` | `f34/frozen_baseline_mean_loss/change` |
| E2 cross-share identities per split seed, low end (Sec 7.2, App C.2) | `165` | `165` | `f27/identities_per_seed_range/0` |
| E2 cross-share identities per split seed, high end (Sec 7.2, App C.2) | `268` | `268` | `f27/identities_per_seed_range/1` |
| E2 cross-share EPISODE RECORDS per split seed, low end (Sec 7.2, App C.2) -- identities vs records: each repeated identity contributes two rows | `330` | `330` | `f27/rows_per_seed_range/0` |
| E2 cross-share EPISODE RECORDS per split seed, high end (Sec 7.2, App C.2) | `536` | `536` | `f27/rows_per_seed_range/1` |
| E2 ttt_mask cross-share identities, low end (App C.2) | `165` | `165` | `f27/arms/ttt_mask,phase_feat/cross_share_identities_per_seed/min` |
| E2 ttt_mask cross-share identities, high end (App C.2) | `188` | `188` | `f27/arms/ttt_mask,phase_feat/cross_share_identities_per_seed/max` |
| E2 ttt_rot cross-share identities, low end (App C.2) | `248` | `248` | `f27/arms/ttt_rot,phase_feat/cross_share_identities_per_seed/min` |
| E2 ttt_rot cross-share identities, high end (App C.2) | `268` | `268` | `f27/arms/ttt_rot,phase_feat/cross_share_identities_per_seed/max` |
| E2 total episode records (Sec 7.2, App C.2) -- printed with a thin space | `134,400` | `134400` | `f27/n_episode_records` |
| E2 identity pruning, ttt_mask feature rho before (App C.2) | `0.5397` | `0.5397` | `f27/arms/ttt_mask/phase_feat/rho_mean_final` |
| E2 identity pruning, ttt_mask feature rho after (App C.2) | `0.5378` | `0.5378` | `f27/arms/ttt_mask/phase_feat/rho_mean_final_identity_pruned` |
| E2 identity pruning, ttt_rot feature rho before (App C.2) | `0.5460` | `0.5460` | `f27/arms/ttt_rot/phase_feat/rho_mean_final` |
| E2 identity pruning, ttt_rot feature rho after (App C.2) | `0.5477` | `0.5477` | `f27/arms/ttt_rot/phase_feat/rho_mean_final_identity_pruned` |
| E2 identity pruning, ttt_mask loss rho before (App C.2) | `0.5043` | `0.5043` | `f27/arms/ttt_mask/phase_loss/rho_mean_final` |
| E2 identity pruning, ttt_mask loss rho after (App C.2) | `0.4965` | `0.4965` | `f27/arms/ttt_mask/phase_loss/rho_mean_final_identity_pruned` |
| E2 identity pruning, ttt_rot loss rho before (App C.2) | `0.0680` | `0.0680` | `f27/arms/ttt_rot/phase_loss/rho_mean_final` |
| E2 identity pruning, ttt_rot loss rho after (App C.2) | `0.0709` | `0.0709` | `f27/arms/ttt_rot/phase_loss/rho_mean_final_identity_pruned` |
| E2 largest absolute rho shift after identity pruning (Sec 7.2, App C.2) | `0.008` | `0.008` | `f27/max_abs_rho_shift` |

### E2 -- matched-architecture arms (Supplement Table S3)

| quantity | value as printed | recomputed from the record | record of record |
|---|---|---|---|
| T5 tent_gn_loss rho mean-final | `0.882` | `0.882` | `f23/arms/tent_gn_loss/rho_mean_final/mean` |
| T5 tent_gn_loss rho median-final | `0.665` | `0.665` | `f23/arms/tent_gn_loss/rho_median_final/mean` |
| T5 tent_gn_loss split-averaged clustered endpoint, low | `0.74` | `0.74` | `f23/arms/tent_gn_loss/ci_mean_final_clustered/lo_mean` |
| T5 tent_gn_loss split-averaged clustered endpoint, high | `0.94` | `0.94` | `f23/arms/tent_gn_loss/ci_mean_final_clustered/hi_mean` |
| T5 tent_gn_loss adaptation episodes/cell | `256` | `256` | `f23/arms/tent_gn_loss/n_episodes_per_cell` |
| T5 tent_gn_loss proxy observations/cell | `256` | `256` | `f23/arms/tent_gn_loss/statistic_support/per_cell_median` |
| T5 tent_wrn_loss rho mean-final | `0.926` | `0.926` | `f23/arms/tent_wrn_loss/rho_mean_final/mean` |
| T5 tent_wrn_loss rho median-final | `0.694` | `0.694` | `f23/arms/tent_wrn_loss/rho_median_final/mean` |
| T5 tent_wrn_loss split-averaged clustered endpoint, low | `0.86` | `0.86` | `f23/arms/tent_wrn_loss/ci_mean_final_clustered/lo_mean` |
| T5 tent_wrn_loss split-averaged clustered endpoint, high | `0.96` | `0.96` | `f23/arms/tent_wrn_loss/ci_mean_final_clustered/hi_mean` |
| T5 tent_wrn_loss adaptation episodes/cell | `384` | `384` | `f23/arms/tent_wrn_loss/n_episodes_per_cell` |
| T5 tent_wrn_loss proxy observations/cell | `384` | `384` | `f23/arms/tent_wrn_loss/statistic_support/per_cell_median` |
| T5 pl_wrn_loss rho mean-final | `0.888` | `0.888` | `f23/arms/pl_wrn_loss/rho_mean_final/mean` |
| T5 pl_wrn_loss rho median-final | `0.702` | `0.702` | `f23/arms/pl_wrn_loss/rho_median_final/mean` |
| T5 pl_wrn_loss split-averaged clustered endpoint, low | `0.81` | `0.81` | `f23/arms/pl_wrn_loss/ci_mean_final_clustered/lo_mean` |
| T5 pl_wrn_loss split-averaged clustered endpoint, high | `0.94` | `0.94` | `f23/arms/pl_wrn_loss/ci_mean_final_clustered/hi_mean` |
| T5 pl_wrn_loss adaptation episodes/cell | `384` | `384` | `f23/arms/pl_wrn_loss/n_episodes_per_cell` |
| T5 pl_wrn_loss proxy observations/cell | `384` | `384` | `f23/arms/pl_wrn_loss/statistic_support/per_cell_median` |
| T5 ttt_rot_loss rho mean-final | `0.273` | `0.273` | `f23/arms/ttt_rot_loss/rho_mean_final/mean` |
| T5 ttt_rot_loss rho median-final | `0.284` | `0.284` | `f23/arms/ttt_rot_loss/rho_median_final/mean` |
| T5 ttt_rot_loss split-averaged clustered endpoint, low | `-0.05` | `-0.05` | `f23/arms/ttt_rot_loss/ci_mean_final_clustered/lo_mean` |
| T5 ttt_rot_loss split-averaged clustered endpoint, high | `0.55` | `0.55` | `f23/arms/ttt_rot_loss/ci_mean_final_clustered/hi_mean` |
| T5 ttt_rot_loss adaptation episodes/cell | `384` | `384` | `f23/arms/ttt_rot_loss/n_episodes_per_cell` |
| T5 ttt_rot_loss proxy observations/cell | `384` | `384` | `f23/arms/ttt_rot_loss/statistic_support/per_cell_median` |
| T5 ttt_mask_loss rho mean-final | `0.591` | `0.591` | `f23/arms/ttt_mask_loss/rho_mean_final/mean` |
| T5 ttt_mask_loss rho median-final | `0.103` | `0.103` | `f23/arms/ttt_mask_loss/rho_median_final/mean` |
| T5 ttt_mask_loss split-averaged clustered endpoint, low | `0.29` | `0.29` | `f23/arms/ttt_mask_loss/ci_mean_final_clustered/lo_mean` |
| T5 ttt_mask_loss split-averaged clustered endpoint, high | `0.80` | `0.80` | `f23/arms/ttt_mask_loss/ci_mean_final_clustered/hi_mean` |
| T5 ttt_mask_loss adaptation episodes/cell | `384` | `384` | `f23/arms/ttt_mask_loss/n_episodes_per_cell` |
| T5 ttt_mask_loss proxy observations/cell | `384` | `384` | `f23/arms/ttt_mask_loss/statistic_support/per_cell_median` |
| T5 tent_gn_feat rho mean-final | `0.694` | `0.694` | `f23/arms/tent_gn_feat/rho_mean_final/mean` |
| T5 tent_gn_feat rho median-final | `0.170` | `0.170` | `f23/arms/tent_gn_feat/rho_median_final/mean` |
| T5 tent_gn_feat split-averaged clustered endpoint, low | `0.38` | `0.38` | `f23/arms/tent_gn_feat/ci_mean_final_clustered/lo_mean` |
| T5 tent_gn_feat split-averaged clustered endpoint, high | `0.85` | `0.85` | `f23/arms/tent_gn_feat/ci_mean_final_clustered/hi_mean` |
| T5 tent_gn_feat adaptation episodes/cell | `256` | `256` | `f23/arms/tent_gn_feat/n_episodes_per_cell` |
| T5 tent_gn_feat proxy observations/cell | `256` | `256` | `f23/arms/tent_gn_feat/statistic_support/per_cell_median` |
| T5 ttt_rot_feat rho mean-final | `0.418` | `0.418` | `f23/arms/ttt_rot_feat/rho_mean_final/mean` |
| T5 ttt_rot_feat rho median-final | `0.598` | `0.598` | `f23/arms/ttt_rot_feat/rho_median_final/mean` |
| T5 ttt_rot_feat split-averaged clustered endpoint, low | `0.07` | `0.07` | `f23/arms/ttt_rot_feat/ci_mean_final_clustered/lo_mean` |
| T5 ttt_rot_feat split-averaged clustered endpoint, high | `0.68` | `0.68` | `f23/arms/ttt_rot_feat/ci_mean_final_clustered/hi_mean` |
| T5 ttt_rot_feat adaptation episodes/cell | `384` | `384` | `f23/arms/ttt_rot_feat/n_episodes_per_cell` |
| T5 ttt_rot_feat proxy observations/cell | `384` | `384` | `f23/arms/ttt_rot_feat/statistic_support/per_cell_median` |
| T5 ttt_mask_feat rho mean-final | `0.610` | `0.610` | `f23/arms/ttt_mask_feat/rho_mean_final/mean` |
| T5 ttt_mask_feat rho median-final | `0.727` | `0.727` | `f23/arms/ttt_mask_feat/rho_median_final/mean` |
| T5 ttt_mask_feat split-averaged clustered endpoint, low | `0.30` | `0.30` | `f23/arms/ttt_mask_feat/ci_mean_final_clustered/lo_mean` |
| T5 ttt_mask_feat split-averaged clustered endpoint, high | `0.82` | `0.82` | `f23/arms/ttt_mask_feat/ci_mean_final_clustered/hi_mean` |
| T5 ttt_mask_feat adaptation episodes/cell | `384` | `384` | `f23/arms/ttt_mask_feat/n_episodes_per_cell` |
| T5 ttt_mask_feat proxy observations/cell | `384` | `384` | `f23/arms/ttt_mask_feat/statistic_support/per_cell_median` |

### E2 -- entropy calibration coverage (Sec. 6.2, Fig. 4)

| quantity | value as printed | recomputed from the record | record of record |
|---|---|---|---|
| E2 calibration total episodes | `7,680` | `7680` | `f21/n_episodes_total` |
| E2 calibration retained confident-right n | `2873` | `2873` | `f21/retained/n_right` |
| E2 calibration retained confident-wrong n | `1554` | `1554` | `f21/retained/n_wrong` |
| E2 calibration excluded n | `3,253` | `3253` | `f21/n_excluded` |
| E2 calibration coverage share | `57.6` | `57.6` | `f21/coverage` |
| E2 calibration excluded share | `42.4` | `42.4` | `f21/excluded_share` |

### E3 -- GPT-2 cross-domain (Sec. 6.3, Table 1)

| quantity | value as printed | recomputed from the record | record of record |
|---|---|---|---|
| E3 code alignment-only rho (Sec 7.4, Fig 8) | `0.679` | `0.679` | `f30/headline/code/rho_alignment_only` |
| E3 legal alignment-only rho (Sec 7.4, Fig 8) | `0.918` | `0.918` | `f30/headline/legal/rho_alignment_only` |
| E3 pubmed alignment-only rho (Sec 7.4, Fig 8) | `0.875` | `0.875` | `f30/headline/pubmed/rho_alignment_only` |
| E3 wikitext alignment-only rho (Sec 7.4, Fig 8) | `0.881` | `0.881` | `f30/headline/wikitext/rho_alignment_only` |
| E3 code full-statistic rho (Sec 7.4, Fig 8) | `0.582` | `0.582` | `f30/headline/code/rho_full_statistic` |
| E3 legal full-statistic rho (Sec 7.4, Fig 8) | `0.905` | `0.905` | `f30/headline/legal/rho_full_statistic` |
| E3 pubmed full-statistic rho (Sec 7.4, Fig 8) | `0.868` | `0.868` | `f30/headline/pubmed/rho_full_statistic` |
| E3 wikitext full-statistic rho (Sec 7.4, Fig 8) | `0.834` | `0.834` | `f30/headline/wikitext/rho_full_statistic` |
| E3 code pooled perplexity improvement (Sec 7.4) | `0.96` | `0.96` | `f29/domains/code/ppl_improvement_pooled` |
| E3 legal pooled perplexity improvement (Sec 7.4) | `0.067` | `0.067` | `f29/domains/legal/ppl_improvement_pooled` |
| E3 pubmed pooled perplexity improvement (Sec 7.4) | `0.570` | `0.570` | `f29/domains/pubmed/ppl_improvement_pooled` |
| E3 wikitext pooled perplexity improvement (Sec 7.4) | `0.210` | `0.210` | `f29/domains/wikitext/ppl_improvement_pooled` |
| E3 code perplexity-improvement clustered interval, low (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.712` | `0.712` | `f29/domains/code/impr_ci/cluster_nested/lo` |
| E3 code perplexity-improvement clustered interval, high (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `1.266` | `1.266` | `f29/domains/code/impr_ci/cluster_nested/hi` |
| E3 legal perplexity-improvement clustered interval, low (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.0626` | `0.0626` | `f29/domains/legal/impr_ci/cluster_nested/lo` |
| E3 legal perplexity-improvement clustered interval, high (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.0705` | `0.0705` | `f29/domains/legal/impr_ci/cluster_nested/hi` |
| E3 pubmed perplexity-improvement clustered interval, low (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.309` | `0.309` | `f29/domains/pubmed/impr_ci/cluster_nested/lo` |
| E3 pubmed perplexity-improvement clustered interval, high (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `1.075` | `1.075` | `f29/domains/pubmed/impr_ci/cluster_nested/hi` |
| E3 wikitext perplexity-improvement clustered interval, low (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.200` | `0.200` | `f29/domains/wikitext/impr_ci/cluster_nested/lo` |
| E3 wikitext perplexity-improvement clustered interval, high (Sec 7.4) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.220` | `0.220` | `f29/domains/wikitext/impr_ci/cluster_nested/hi` |
| E3 code alignment-only rho at the FIXED BUDGET (T7 upper block) | `0.660` | `0.660` | `f30/domains/code/endpoint_fixed_budget/rho_pooled_rows/alignment_only` |
| E3 legal alignment-only rho at the FIXED BUDGET (T7 upper block) | `0.904` | `0.904` | `f30/domains/legal/endpoint_fixed_budget/rho_pooled_rows/alignment_only` |
| E3 pubmed alignment-only rho at the FIXED BUDGET (T7 upper block) | `0.870` | `0.870` | `f30/domains/pubmed/endpoint_fixed_budget/rho_pooled_rows/alignment_only` |
| E3 wikitext alignment-only rho at the FIXED BUDGET (T7 upper block) | `0.881` | `0.881` | `f30/domains/wikitext/endpoint_fixed_budget/rho_pooled_rows/alignment_only` |
| E3 code full-statistic rho at the FIXED BUDGET (Sec 7.4) | `0.570` | `0.570` | `f30/domains/code/endpoint_fixed_budget/rho_pooled_rows/phase_v2` |
| E3 legal full-statistic rho at the FIXED BUDGET (Sec 7.4) | `0.895` | `0.895` | `f30/domains/legal/endpoint_fixed_budget/rho_pooled_rows/phase_v2` |
| E3 pubmed full-statistic rho at the FIXED BUDGET (Sec 7.4) | `0.863` | `0.863` | `f30/domains/pubmed/endpoint_fixed_budget/rho_pooled_rows/phase_v2` |
| E3 wikitext full-statistic rho at the FIXED BUDGET (Sec 7.4) | `0.834` | `0.834` | `f30/domains/wikitext/endpoint_fixed_budget/rho_pooled_rows/phase_v2` |
| E3 code fixed-budget alignment interval, low (T7 upper block) | `0.603` | `0.603` | `f30/domains/code/endpoint_fixed_budget/ci_cluster_nested/alignment_only/lo` |
| E3 code fixed-budget alignment interval, high (T7 upper block) | `0.711` | `0.711` | `f30/domains/code/endpoint_fixed_budget/ci_cluster_nested/alignment_only/hi` |
| E3 legal fixed-budget alignment interval, low (T7 upper block) | `0.883` | `0.883` | `f30/domains/legal/endpoint_fixed_budget/ci_cluster_nested/alignment_only/lo` |
| E3 legal fixed-budget alignment interval, high (T7 upper block) | `0.921` | `0.921` | `f30/domains/legal/endpoint_fixed_budget/ci_cluster_nested/alignment_only/hi` |
| E3 pubmed fixed-budget alignment interval, low (T7 upper block) | `0.838` | `0.838` | `f30/domains/pubmed/endpoint_fixed_budget/ci_cluster_nested/alignment_only/lo` |
| E3 pubmed fixed-budget alignment interval, high (T7 upper block) | `0.895` | `0.895` | `f30/domains/pubmed/endpoint_fixed_budget/ci_cluster_nested/alignment_only/hi` |
| E3 wikitext fixed-budget alignment interval, low (T7 upper block) | `0.858` | `0.858` | `f30/domains/wikitext/endpoint_fixed_budget/ci_cluster_nested/alignment_only/lo` |
| E3 wikitext fixed-budget alignment interval, high (T7 upper block) | `0.898` | `0.898` | `f30/domains/wikitext/endpoint_fixed_budget/ci_cluster_nested/alignment_only/hi` |
| E3 code fixed-budget paired difference, low (T7 upper block) -- printed with an explicit sign | `0.066` | `0.066` | `f30/domains/code/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/lo` |
| E3 code fixed-budget paired difference, high (T7 upper block) -- printed with an explicit sign | `0.116` | `0.116` | `f30/domains/code/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/hi` |
| E3 legal fixed-budget paired difference, low (T7 upper block) -- printed with an explicit sign | `0.003` | `0.003` | `f30/domains/legal/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/lo` |
| E3 legal fixed-budget paired difference, high (T7 upper block) -- printed with an explicit sign | `0.016` | `0.016` | `f30/domains/legal/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/hi` |
| E3 pubmed fixed-budget paired difference, low (T7 upper block) -- printed with an explicit sign | `-0.005` | `-0.005` | `f30/domains/pubmed/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/lo` |
| E3 pubmed fixed-budget paired difference, high (T7 upper block) -- printed with an explicit sign | `0.017` | `0.017` | `f30/domains/pubmed/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/hi` |
| E3 wikitext fixed-budget paired difference, low (T7 upper block) -- printed with an explicit sign | `0.030` | `0.030` | `f30/domains/wikitext/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/lo` |
| E3 wikitext fixed-budget paired difference, high (T7 upper block) -- printed with an explicit sign | `0.065` | `0.065` | `f30/domains/wikitext/endpoint_fixed_budget/paired_diff_alignment_minus_full/cluster_nested/hi` |
| E3 code alignment-only clustered interval, low (Sec 7.4, Fig 8) | `0.625` | `0.625` | `f30/headline/code/ci_alignment_only/0` |
| E3 code alignment-only clustered interval, high (Sec 7.4, Fig 8) | `0.727` | `0.727` | `f30/headline/code/ci_alignment_only/1` |
| E3 legal alignment-only clustered interval, low (Sec 7.4, Fig 8) | `0.900` | `0.900` | `f30/headline/legal/ci_alignment_only/0` |
| E3 legal alignment-only clustered interval, high (Sec 7.4, Fig 8) | `0.931` | `0.931` | `f30/headline/legal/ci_alignment_only/1` |
| E3 pubmed alignment-only clustered interval, low (Sec 7.4, Fig 8) | `0.845` | `0.845` | `f30/headline/pubmed/ci_alignment_only/0` |
| E3 pubmed alignment-only clustered interval, high (Sec 7.4, Fig 8) | `0.899` | `0.899` | `f30/headline/pubmed/ci_alignment_only/1` |
| E3 wikitext alignment-only clustered interval, low (Sec 7.4, Fig 8) | `0.858` | `0.858` | `f30/headline/wikitext/ci_alignment_only/0` |
| E3 wikitext alignment-only clustered interval, high (Sec 7.4, Fig 8) | `0.898` | `0.898` | `f30/headline/wikitext/ci_alignment_only/1` |
| E3 code paired difference (align - full) interval, low (Sec 7.4) -- printed with an explicit + sign | `0.073` | `0.073` | `f30/headline/code/paired_diff_ci/0` |
| E3 code paired difference (align - full) interval, high (Sec 7.4) -- printed with an explicit + sign | `0.122` | `0.122` | `f30/headline/code/paired_diff_ci/1` |
| E3 legal paired difference (align - full) interval, low (Sec 7.4) -- printed with an explicit + sign | `0.007` | `0.007` | `f30/headline/legal/paired_diff_ci/0` |
| E3 legal paired difference (align - full) interval, high (Sec 7.4) -- printed with an explicit + sign | `0.020` | `0.020` | `f30/headline/legal/paired_diff_ci/1` |
| E3 pubmed paired difference (align - full) interval, low (Sec 7.4) -- printed with an explicit + sign | `-0.002` | `-0.002` | `f30/headline/pubmed/paired_diff_ci/0` |
| E3 pubmed paired difference (align - full) interval, high (Sec 7.4) -- printed with an explicit + sign | `0.017` | `0.017` | `f30/headline/pubmed/paired_diff_ci/1` |
| E3 wikitext paired difference (align - full) interval, low (Sec 7.4) -- printed with an explicit + sign | `0.031` | `0.031` | `f30/headline/wikitext/paired_diff_ci/0` |
| E3 wikitext paired difference (align - full) interval, high (Sec 7.4) -- printed with an explicit + sign | `0.063` | `0.063` | `f30/headline/wikitext/paired_diff_ci/1` |
| E3 code design effect, perplexity improvement (App C) | `1.769` | `1.769` | `f29/domains/code/impr_ci/cluster_nested/design_effect_vs_naive` |
| E3 legal design effect, perplexity improvement (App C) | `1.730` | `1.730` | `f29/domains/legal/impr_ci/cluster_nested/design_effect_vs_naive` |
| E3 pubmed design effect, perplexity improvement (App C) | `1.542` | `1.542` | `f29/domains/pubmed/impr_ci/cluster_nested/design_effect_vs_naive` |
| E3 wikitext design effect, perplexity improvement (App C) | `1.730` | `1.730` | `f29/domains/wikitext/impr_ci/cluster_nested/design_effect_vs_naive` |
| E3 code design effect, correlation (App C) | `1.657` | `1.657` | `f29/domains/code/rho_ci/cluster_nested/design_effect_vs_naive` |
| E3 legal design effect, correlation (App C) | `1.568` | `1.568` | `f29/domains/legal/rho_ci/cluster_nested/design_effect_vs_naive` |
| E3 pubmed design effect, correlation (App C) | `1.566` | `1.566` | `f29/domains/pubmed/rho_ci/cluster_nested/design_effect_vs_naive` |
| E3 wikitext design effect, correlation (App C) | `1.552` | `1.552` | `f29/domains/wikitext/rho_ci/cluster_nested/design_effect_vs_naive` |
| E3 design-effect range, perplexity improvement, low end (Sec 7.4, App C) | `1.54` | `1.54` | `f29 min over domains of impr design effect` |
| E3 design-effect range, perplexity improvement, high end (Sec 7.4, App C) | `1.77` | `1.77` | `f29 max over domains of impr design effect` |
| E3 design-effect range, correlations, low end (Sec 7.4) | `1.55` | `1.55` | `f29 min over domains of rho design effect` |
| E3 design-effect range, correlations, high end (Sec 7.4) | `1.66` | `1.66` | `f29 max over domains of rho design effect` |
| E3 per-document gain ICC, low end (Sec 7.4, App C) | `0.972` | `0.972` | `f29 min over domains of gain ICC` |
| E3 per-document gain ICC, high end (Sec 7.4, App C) | `0.9999` | `0.9999` | `f29 max over domains of gain ICC` |
| E3 phase-statistic ICC, low end (App C) | `0.818` | `0.818` | `f29 min over domains of phase_v2 ICC` |
| E3 phase-statistic ICC, high end (App C) | `0.957` | `0.957` | `f29 max over domains of phase_v2 ICC` |
| E3 pooled bootstrap draws behind every printed endpoint (App C) -- 5 RNG streams x B = 2000; printed with a thin space | `10,000` | `10000` | `f29/n_pooled_draws` |
| E3 max endpoint gap, i.i.d.-row construction vs the published one (App C) -- the check that the widening is caused by the resampling unit alone | `0.0062` | `0.0062` | `f29/max_reproduction_gap_vs_published` |
| E3 proxy code partial rho of delta_v2 given alignment (Sec 7.4) -- printed with an explicit sign | `-0.287` | `-0.287` | `f31/folds/code/heldout_partial_rho_delta_v2_given_alignment` |
| E3 proxy legal partial rho of delta_v2 given alignment (Sec 7.4) -- printed with an explicit sign | `0.003` | `0.003` | `f31/folds/legal/heldout_partial_rho_delta_v2_given_alignment` |
| E3 proxy pubmed partial rho of delta_v2 given alignment (Sec 7.4) -- printed with an explicit sign | `0.091` | `0.091` | `f31/folds/pubmed/heldout_partial_rho_delta_v2_given_alignment` |
| E3 proxy wikitext partial rho of delta_v2 given alignment (Sec 7.4) -- printed with an explicit sign | `0.028` | `0.028` | `f31/folds/wikitext/heldout_partial_rho_delta_v2_given_alignment` |
| E3 proxy code partial-rho pooled interval, low (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `-0.368` | `-0.368` | `f31/folds/code/pooled_ci_partial_rho_delta_v2_given_alignment/lo` |
| E3 proxy code partial-rho pooled interval, high (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `-0.203` | `-0.203` | `f31/folds/code/pooled_ci_partial_rho_delta_v2_given_alignment/hi` |
| E3 proxy legal partial-rho pooled interval, low (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `-0.082` | `-0.082` | `f31/folds/legal/pooled_ci_partial_rho_delta_v2_given_alignment/lo` |
| E3 proxy legal partial-rho pooled interval, high (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.090` | `0.090` | `f31/folds/legal/pooled_ci_partial_rho_delta_v2_given_alignment/hi` |
| E3 proxy pubmed partial-rho pooled interval, low (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.00044` | `0.00044` | `f31/folds/pubmed/pooled_ci_partial_rho_delta_v2_given_alignment/lo` |
| E3 proxy pubmed partial-rho pooled interval, high (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.18291` | `0.18291` | `f31/folds/pubmed/pooled_ci_partial_rho_delta_v2_given_alignment/hi` |
| E3 proxy wikitext partial-rho pooled interval, low (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `-0.056` | `-0.056` | `f31/folds/wikitext/pooled_ci_partial_rho_delta_v2_given_alignment/lo` |
| E3 proxy wikitext partial-rho pooled interval, high (Sec 7.4, T6) -- pooled 10,000-draw percentile, not a mean of five endpoints | `0.114` | `0.114` | `f31/folds/wikitext/pooled_ci_partial_rho_delta_v2_given_alignment/hi` |
| E3 proxy code held-out rho of the frozen selection (Sec 7.4, T6) | `0.703` | `0.703` | `f31/folds/code/heldout_rho_selected` |
| E3 proxy legal held-out rho of the frozen selection (Sec 7.4, T6) | `0.927` | `0.927` | `f31/folds/legal/heldout_rho_selected` |
| E3 proxy pubmed held-out rho of the frozen selection (Sec 7.4, T6) | `0.898` | `0.898` | `f31/folds/pubmed/heldout_rho_selected` |
| E3 proxy wikitext held-out rho of the frozen selection (Sec 7.4, T6) | `0.869` | `0.869` | `f31/folds/wikitext/heldout_rho_selected` |
| E3 proxy code held-out selected pooled interval, low (T6) | `0.647` | `0.647` | `f31/folds/code/pooled_ci_selected/lo` |
| E3 proxy code held-out selected pooled interval, high (T6) | `0.751` | `0.751` | `f31/folds/code/pooled_ci_selected/hi` |
| E3 proxy legal held-out selected pooled interval, low (T6) | `0.910` | `0.910` | `f31/folds/legal/pooled_ci_selected/lo` |
| E3 proxy legal held-out selected pooled interval, high (T6) | `0.941` | `0.941` | `f31/folds/legal/pooled_ci_selected/hi` |
| E3 proxy pubmed held-out selected pooled interval, low (T6) | `0.870` | `0.870` | `f31/folds/pubmed/pooled_ci_selected/lo` |
| E3 proxy pubmed held-out selected pooled interval, high (T6) | `0.921` | `0.921` | `f31/folds/pubmed/pooled_ci_selected/hi` |
| E3 proxy wikitext held-out selected pooled interval, low (T6) | `0.840` | `0.840` | `f31/folds/wikitext/pooled_ci_selected/lo` |
| E3 proxy wikitext held-out selected pooled interval, high (T6) | `0.892` | `0.892` | `f31/folds/wikitext/pooled_ci_selected/hi` |
| E3 proxy folds whose partial-rho interval excludes zero on the FAVOURABLE side (Sec 7.4, T6) -- printed as "1 of 4"; a "0 of 4" summary would contradict f12's own record | `1` | `1` | `f31/summary/n_folds_partial_rho_delta_v2_ci_excludes_zero` |
| E3 proxy folds whose partial-rho interval excludes zero on the ADVERSE side (Sec 7.4, T6) -- printed as "1 of 4"; code, and the reason the conclusion is "no consistent incremental benefit" rather than "none" | `1` | `1` | `f31/summary/n_folds_partial_rho_delta_v2_ci_excludes_zero_adverse` |
| E3 proxy folds selecting a delta_v2-family variant (Sec 7.4) | `2` | `2` | `f31/summary/n_folds_selecting_delta_v2_family` |
| E3 proxy pooled bootstrap draws behind every printed proxy endpoint (App C) -- 5 RNG streams x B = 2000; printed with a thin space | `10,000` | `10000` | `f31/n_pooled_draws` |
| E3 proxy max endpoint shift, pooled vs the superseded averaged construction (App C) -- the largest move caused by the endpoint rule alone | `0.00104` | `0.00104` | `f31/audit_vs_f12/max_endpoint_shift_vs_f12` |
| E3 code fixed-budget (t=20) perplexity improvement (Sec 6.3) -- the primary E3 comparison; t = 20 is the run horizon | `1.03` | `1.03` | `f32/domains/code/impr_point/fixed_20` |
| E3 pubmed fixed-budget (t=20) perplexity improvement (Sec 6.3) -- the primary E3 comparison; t = 20 is the run horizon | `0.62` | `0.62` | `f32/domains/pubmed/impr_point/fixed_20` |
| E3 wikitext fixed-budget (t=20) perplexity improvement (Sec 6.3) -- the primary E3 comparison; t = 20 is the run horizon | `0.246` | `0.246` | `f32/domains/wikitext/impr_point/fixed_20` |
| E3 legal fixed-budget (t=20) perplexity improvement (Sec 6.3) -- the primary E3 comparison; t = 20 is the run horizon | `0.077` | `0.077` | `f32/domains/legal/impr_point/fixed_20` |
| E3 code fixed-budget improvement clustered interval, low (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `0.774` | `0.774` | `f32/domains/code/impr_ci/cluster_nested/fixed_20/lo` |
| E3 code fixed-budget improvement clustered interval, high (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `1.344` | `1.344` | `f32/domains/code/impr_ci/cluster_nested/fixed_20/hi` |
| E3 pubmed fixed-budget improvement clustered interval, low (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `0.347` | `0.347` | `f32/domains/pubmed/impr_ci/cluster_nested/fixed_20/lo` |
| E3 pubmed fixed-budget improvement clustered interval, high (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `1.132` | `1.132` | `f32/domains/pubmed/impr_ci/cluster_nested/fixed_20/hi` |
| E3 wikitext fixed-budget improvement clustered interval, low (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `0.235` | `0.235` | `f32/domains/wikitext/impr_ci/cluster_nested/fixed_20/lo` |
| E3 wikitext fixed-budget improvement clustered interval, high (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `0.257` | `0.257` | `f32/domains/wikitext/impr_ci/cluster_nested/fixed_20/hi` |
| E3 legal fixed-budget improvement clustered interval, low (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `0.0729` | `0.0729` | `f32/domains/legal/impr_ci/cluster_nested/fixed_20/lo` |
| E3 legal fixed-budget improvement clustered interval, high (Sec 6.3) -- pooled 10,000-draw percentile, f29's protocol on f29's draws | `0.0819` | `0.0819` | `f32/domains/legal/impr_ci/cluster_nested/fixed_20/hi` |
| E3 code paired difference (fixed 20 - selector), low (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0586` | `0.0586` | `f32/domains/code/paired_fixed20_minus_alta/cluster_nested/lo` |
| E3 code paired difference (fixed 20 - selector), high (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0835` | `0.0835` | `f32/domains/code/paired_fixed20_minus_alta/cluster_nested/hi` |
| E3 legal paired difference (fixed 20 - selector), low (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0100` | `0.0100` | `f32/domains/legal/paired_fixed20_minus_alta/cluster_nested/lo` |
| E3 legal paired difference (fixed 20 - selector), high (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0117` | `0.0117` | `f32/domains/legal/paired_fixed20_minus_alta/cluster_nested/hi` |
| E3 pubmed paired difference (fixed 20 - selector), low (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0367` | `0.0367` | `f32/domains/pubmed/paired_fixed20_minus_alta/cluster_nested/lo` |
| E3 pubmed paired difference (fixed 20 - selector), high (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0586` | `0.0586` | `f32/domains/pubmed/paired_fixed20_minus_alta/cluster_nested/hi` |
| E3 wikitext paired difference (fixed 20 - selector), low (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0340` | `0.0340` | `f32/domains/wikitext/paired_fixed20_minus_alta/cluster_nested/lo` |
| E3 wikitext paired difference (fixed 20 - selector), high (Sec 6.3) -- formed inside each resample, so both arms see the same documents | `0.0382` | `0.0382` | `f32/domains/wikitext/paired_fixed20_minus_alta/cluster_nested/hi` |
| E3 selector relative shortfall against the fixed budget, low end (Sec 6.3) | `6.8` | `6.8` | `f32/verdict/alta_relative_shortfall_vs_fixed20_by_domain (min)` |
| E3 selector relative shortfall against the fixed budget, high end (Sec 6.3) | `14.7` | `14.7` | `f32/verdict/alta_relative_shortfall_vs_fixed20_by_domain (max)` |
| E3 mean selected index, low end (Sec 6.3) | `17.3` | `17.3` | `f32/verdict/mean_t_hat_by_domain (min)` |
| E3 mean selected index, high end (Sec 6.3) | `17.6` | `17.6` | `f32/verdict/mean_t_hat_by_domain (max)` |
| E3 share of documents whose per-document oracle picks t=20, low (Sec 6.3) | `91` | `91` | `f32/domains/*/frac_t_star_eq_20 (min)` |
| E3 share of documents whose per-document oracle picks t=20, high (Sec 6.3) | `98` | `98` | `f32/domains/*/frac_t_star_eq_20 (max)` |
| E3 rank-robustness: largest rho shift when the gain column changes (Sec 6.3) -- alignment table recomputed against the fixed-budget gain | `0.0185` | `0.0185` | `f32/rank_robustness_to_gain_column/max_abs_rho_shift` |

### E3 interval CONSTRUCTION (not a value check)

| construction claim | asserted of | required | forbidden |
|---|---|---|---|
| E3 f29 protocol declares one pooled percentile interval | `f29/protocol` | `pooled`, `no averaging of endpoints` | `endpoints averaged`, `mean endpoint`, `endpoint over the five` |
| E3 f30 protocol declares one pooled percentile interval | `f30/protocol` | `pooled`, `no averaging of endpoints` | `endpoints averaged`, `mean endpoint`, `endpoint over the five` |
| E3 f31 protocol declares one pooled percentile interval | `f31/protocol` | `pooled`, `no averaging of endpoints` | `endpoints averaged`, `mean endpoint`, `endpoint over the five` |
| E3 f29 records which script it supersedes | `f29/supersedes` | `f11_e4_cluster_ci.py` | -- |
| E3 f30 records which script it supersedes | `f30/supersedes` | `f17_e4_alignment_only.py` | -- |
| E3 f31 records which script it supersedes | `f31/supersedes` | `f12_e4_proxy_loo.py` | -- |
| E3 superseded f11 record retained as the audit trail | `f11/script` | `f11_e4_cluster_ci.py` | -- |
| E3 superseded f17 record retained as the audit trail | `f17/script` | `f17_e4_alignment_only.py` | -- |
| E3 superseded f12 record retained as the audit trail | `f12/script` | `f12_e4_proxy_loo.py` | -- |
| no .tex describes an E3 interval as averaged endpoints | `main sections/ + figures/ and the supplement` | -- | `endpoints averaged` |
| The protocols section states the pooled construction explicitly | `supplement/s6_protocols.tex` | `pooled into one`, `percentile` | -- |
| no .tex claims the shift proxy adds nothing measurable | `sections/ + figures/` | -- | `adds no measurable increment`, `contributes nothing measurable`, `added measurable rank information`, `add measurable rank information`, `adds no measurable rank information` |
| The archived E3 proxy ledger states the favourable-side census as 1 of 4, not 0 of 4 | `archive_tables/e3_proxy_ledger.tex` | `favourable-side count is $1$ of` | `favourable side in $0$ of $4$` |
| The full-grid section still reports the shift proxy as resolved in two of four domains with opposite signs, not as null | `supplement/s8_full_results.tex` | `only two of the four`, `opposite signs` | `favourable side in $0$ of $4$` |
| The E3 section still reports the shift proxy as resolving in opposite directions rather than as null | `sections/experiments.tex` | `opposite` | `favourable side in $0$ of $4$` |
| The protocols section states the pooled construction for the proxy analysis too | `supplement/s6_protocols.tex` | `pooled` | `endpoints averaged` |
| The estimation section carries the moved E3 interval passage | `supplement/s7_estimation.tex` | `percentile pair of one pooled bootstrap` | `endpoints averaged` |
| The E2 temperature-scaling sentence names both loss estimands and attributes the excess one to each arm's own frozen baseline | `sections/experiments.tex` | `Two estimands of`, `own frozen`, `absolute`, `excess` | `mean change over
steps 1--2: $-0.38$` |
| The f34 record states why the two temperature-scaling estimands differ | `f34/note` | `frozen baseline` | -- |
| E3 pooled endpoints are not a relabelling of the superseded averaged ones | `f29` endpoint blocks | at least one endpoint moved | -- |
| `f29` replays `f11`'s exact draws | `f29/audit_vs_f11` | per-stream endpoint gap and point-estimate gap `<= 1e-12` | -- |
| `f30` replays `f17`'s exact draws | `f30/audit_vs_f17` | per-stream endpoint gap and point-estimate gap `<= 1e-12` | -- |
| `f31` replays `f12`'s exact draws | `f31/audit_vs_f12` | per-stream endpoint gap and point-estimate gap `<= 1e-12` | -- |
| E3 alignment-vs-full verdict counts unchanged under pooling | `f30/audit_vs_f17` | `verdict_counts_unchanged` | -- |
| E3 proxy pooled endpoints are not a relabelling of the superseded averaged ones | `f31` endpoint blocks | at least one endpoint moved | -- |
| E3 proxy favourable-side exclusion census agrees across the pooled and averaged constructions and with `f12` | `f31/summary` + `f12/summary` | `exclusion_verdicts_unchanged_by_pooling` and three equal counts | -- |


### E5 -- learning-rate ablation: NOT part of this submission

The learning-rate ablation once tabulated here has been removed from the
CURRENT VALUES half. The submission reports three suites -- E1, E2 and the
GPT-2 study -- and no claim in either document rests on the ablation, so a
current-values row for it named an experiment the manuscript does not make.
Its records remain in `experiments/results/is_fresh/f25_e2_lr_ablation.json`
and its rows remain below the HISTORY line.

What `experiments/results/e5/` still supplies to this submission is not an
experiment but a measurement input: the `delta_v2_*.json` and
`delta_feat_*.json` proxy files that the E2 and GPT-2 analyses consume.
Those ship, and are cited as proxy sources rather than as a suite. The E2
feature proxy of the fresh GroupNorm arm is no longer among them: it is
measured on that arm's own source model by
`f38_e2gn_deltafeat_fresh.py` and stored beside its records in
`experiments/results/is_fresh/e2_gn/`.

### Reproducing this table

```
python f38_e2gn_deltafeat_fresh.py           # the fresh-GN feature proxy and
                                             # its coverage census, before f23
python r9_reconcile.py                       # record checks + construction
                                             # checks + interval scan
python r9_reconcile.py --emit-current-values # regenerate the tables above
```

The counts the first command prints, and the number of checks the second
runs, are deliberately not repeated here: a count typed beside a script that
prints it is a second copy that can go stale on its own.

The script is shipped in the reproducibility archive alongside the records it
reads. The build environment for the two documents of this submission is
pinned separately in `paper/BUILD_ENVIRONMENT.md` of the review package
(`paper/is2/paper/BUILD_ENVIRONMENT.md` in the archive).

---

# HISTORY (everything below this line is superseded where it disagrees with CURRENT VALUES)


## 1. Claim audit

| # | Claim (original) | Producing code | Classification |
|---|---|---|---|
| A1 | Simulated risk curves match the closed form to worst-case relative error **1.8 %** over the 30-cell grid | `run_e1.part_a` | **MEASURED**, but single seed (42), and the error is normalised by the *global maximum* of the theory curve, which flatters it |
| A2 | Fitted phase threshold **0.02504** vs predicted η/2 = 0.025, ratio **1.002**; abstract: boundary "within 0.2 % of its predicted position" | `run_e1.part_b` | **ANALYTIC** |
| A3 | Holdout sign-prediction accuracy **1.00** | `run_e1.part_b` | **ANALYTIC** |
| A4 | Risk at the empirical argmin within 5 % of the theoretical minimum in **100 %** of cells | `run_e1.part_c` | **ANALYTIC scoring** (step selected empirically, risk scored by the closed form) |
| A5 | Empirical stopping time within a factor two of *t\** in **88 %** of cells | `run_e1.part_c` | **MEASURED selection, analytic reference** (compared to the theoretical *t\**, and the argmin is taken in sample) |
| A6 | ALTA p90 risk inside the diagnostic bound in **16/16** cells; median risk ratios **0.99–1.37**, dropping to **0.29–0.38** at α = 1; measured constants 1–4 | `run_e1.part_d` | **SEMI-ANALYTIC**: measured numerator, closed-form oracle denominator; single seed |
| A7 | ReLU probe: α = 0 harmful, mean excess **0.0411**; α=1 vs α=0 margin **0.3485** | `run_e1.part_e` | **MEASURED but seed-frozen** — `rng` is never used; every generator is pinned inside the function, so `--seed 43` reproduces it bit for bit |
| A8 | Batch adaptation: "the measured **variance** matches σ²/N to a maximum relative error of **0.35 %**" | `run_e1.part_f` | **MISDESCRIBED + in-sample**: part_f measures no variance; it compares an *in-sample minimum excess risk* to the closed form's minimum |
| A9 | E2 phase statistic ranks gains, Spearman **0.686 / 0.694** (ttt_mask), **0.622 / 0.742** (ttt_rot), rising to **0.762 / 0.840** at the best step | `analysis/aggregate.py` | **MEASURED but SAME-SAMPLE**: statistic and gain from the same episodes; "best step" selected on the sample it is scored from |
| A10 | E2 batch mechanics, E2 calibration identity, E3 (all), E4 (all), E5 lr ablation | `adapt_cifar.py`, `run_e3.py`, `run_e4.py` | **MEASURED — no change needed** (see §4) |

### Evidence for the ANALYTIC classifications

**A2/A3.** `run_e1.part_b` builds its entire gain grid from
`t_star_theory(...)` and `excess_risk(...)`. Verified directly: calling
`part_b` with `default_rng(42)` and `default_rng(20260801)` returns
byte-identical output (`fitted_threshold = 0.025044195974408885`,
`holdout_accuracy = 1.0` in both). The `rng` argument appears exactly once in
the function — in its signature.

Worse, the argmin scan runs over `t ∈ [0, T]`, and `excess_risk(0) = δ²`
exactly, so the plotted "gain" `δ² − min_t Exc(t)` is **non-negative by
construction**. In the published grid (`results/e1/e1_b_seed42.json`) the
minimum gain is `−1.07e−14`, 184 of 625 cells are exactly zero, and 441 are
positive. The classifier's label is therefore "is the closed-form argmin
strictly greater than 0, at a 1e−9 tolerance" — not "does TTT help or hurt".
Figure 2's caption ("TTT helps above the curve, hurts below") describes a
quantity that the producing code cannot make negative.

**A4.** `part_c` computes `risk_at_emp_t = excess_risk(emp_t, ...)`, i.e. the
closed form at the selected step, and compares it to the closed form's own
minimum. In the published JSON the gap is exactly `0.0` in 6 of 25 cells
(those where `t_emp == t_theory`) and the **maximum** gap over all 25 cells is
`0.00149` — the 5 % gate is passed by a factor of 33 because the analytic curve
is flat near its minimum, not because any achieved risk was measured.

**A7.** `inspect.getsource(part_e)` contains the token `rng` once (the
signature). Randomness comes from `torch.manual_seed(0)` and generators seeded
`100+rep`, `999+rep*7+…`, `rep*31+1`.

**A8.** `part_f` reports `max_rel_err` over `|emp.min() − theo.min()| /
theo.min()`. `emp.min()` is the minimum of a curve estimated from the same
12,000 replicates, so it is optimistically biased; and it is a risk, not a
variance.

**A9.** `aggregate.py::analyze_e2_main` computes `mean_phase_feat` and
`gain_by_step` from the same episode list, then correlates the cell means;
`gain_best = max(gains)` maximises over steps on that same sample.

---

## 2. Table of record

Original number → classification → fresh measured replacement.
Every fresh value is mean over 5 seeds with the across-seed range in brackets.

| # | Original | Class | Fresh measured | Source JSON | Verdict |
|---|---|---|---|---|---|
| A1 | worst rel. error **1.8 %** (30 cells, seed 42) | MEASURED, 1 seed | **1.15 %** [0.85, 1.58] same normalisation; **2.23 %** [1.76, 2.62] pointwise; worst deviation **3.35 SE** [3.09, 3.61] over 12,030 (cell, step) comparisons | `f7_curve_match_summary.json` | **Confirmed**, tightened; the residual is pure Monte-Carlo noise |
| A2 | fitted threshold **0.02504**, ratio **1.002** | ANALYTIC | fitted threshold **0.02413** [0.02326, 0.02504], ratio **0.965** [0.931, 1.002]. Grid-resolution-free statement: at **every** seed the largest phase value with a measured *negative* gain is **0.02326** and the smallest with a measured *positive* gain is **0.02732**; η/2 = 0.025 lies strictly inside that bracket at all 5 seeds | `f1_boundary_onestep_summary.json`, `f9_phase_figure_data.json` | **Confirmed on measured evidence.** The abstract's "within 0.2 %" must be revised — 0.2 % is below the grid's own resolution. Report the bracket, or "within 7 %" |
| A3 | holdout sign accuracy **1.00** | ANALYTIC | **0.9942** [0.9904, 0.9968] over all 313 holdout cells; **1.0000** [1.000, 1.000] over the 96 % of cells whose gain sign is resolved at 3 Monte-Carlo SE | `f1_boundary_onestep_summary.json` | **Confirmed, revised to 0.994** (1.00 on resolved cells). Every miss is a near-boundary cell whose true gain is within Monte-Carlo noise of zero |
| A4 | risk at empirical argmin within 5 % of the theoretical minimum in **100 %** of cells | ANALYTIC | **100 %** [100, 100] of cells within 5 % of a *measured* oracle (step chosen on block A, oracle step chosen on independent block C, both scored on block B). Median relative gap **0.0000**, max **0.021** [0.010, 0.040] | `f3_optimal_stopping_summary.json` | **Confirmed on measured evidence.** The measured worst-cell gap is 14× the analytic one (0.0015) but still 2.4× inside the gate |
| A5 | stopping time within 2× of *t\** in **88 %** of cells | MEASURED selection / analytic reference | **96 %** [92, 100] against a *measured* oracle step; **90.4 %** [88, 96] against the theoretical *t\** | `f3_optimal_stopping_summary.json` | **Confirmed**; 88 % reproduces as the low end of the theory-referenced range |
| A6 | p90 bound holds **16/16**; median ratios **0.99–1.37**, **0.29–0.38** at α=1; measured constants 1–4 | SEMI-ANALYTIC | p90 bound holds **16/16** and safety-vs-frozen holds **16/16** at *every* one of the 5 seeds. Median risk ratios against the **measured** oracle: **1.003–1.365** in the contracting cells (α ≤ 0.75), **0.313–0.346** at α = 1. Worst-cell p90 ratio **2.33** [2.27, 2.42], i.e. measured constants **1–2.4** against the theorem's ≤ 12 | `f4_alta_measured_oracle_summary.json` | **Confirmed on measured evidence, essentially unchanged.** The closed-form denominator it used was accurate: the measured oracle risk agrees with `risk_star` to < 1 % in all 16 cells. The published 0.99–1.37 / 0.29–0.38 reproduce as 1.003–1.365 / 0.313–0.346 |
| A7 | α=0 mean excess **0.0411**; margin **0.3485** | MEASURED, seed-frozen | α=0 mean excess **0.0433** [**−0.0236**, 0.1673]; margin **0.3611** [0.2224, 0.5133]; monotone in α at **5/5** seeds; α=0 harmful at **4/5** seeds | `f6_relu_multiseed_summary.json` | **Margin confirmed and strengthened.** The α=0 harm number must be **revised**: its mean matches (0.043 vs 0.041) but it is seed-fragile — at seed 20260802 adaptation at α=0 is marginally *helpful* (−0.024). Report the range, and state the monotonicity/margin claim as the robust one |
| A8 | "measured variance matches σ²/N to **0.35 %**" | MISDESCRIBED + in-sample | **Variance, measured directly:** max relative error vs the closed form at σ/√N is **0.57 %** [0.48, 0.68], against a Monte-Carlo SE of **0.22 %** on the variance estimate itself. **Closed-form-free version:** N·Var(u_t) is constant in N to a max/min ratio of **1.0082** [1.0068, 1.0113] across N ∈ {1..64}. **The quantity part_f actually reported**, rescored out of sample: max relative error **0.21 %** [0.16, 0.26] | `f5_batch_variance_summary.json` | **Confirmed, with the sentence rewritten.** The σ²/N law holds; but "0.35 %" was a min-risk agreement, and a variance claim at this replicate count resolves to ≈0.6 %, not 0.35 % |
| A9 | ttt_mask **0.686**/**0.694**, best step **0.762**/**0.840**; ttt_rot **0.622**/**0.742** | MEASURED, same-sample | Cross-fit (statistic on a fresh-seed commissioning half, gain on the disjoint evaluation half): ttt_mask **0.540** [0.483, 0.610] mean-final, **0.493** [0.436, 0.543] median-final, **0.524**/**0.509** at a cross-fit best step; ttt_rot **0.546** [0.511, 0.592] mean-final, **0.630** [0.572, 0.683] median-final, **0.223**/**0.111** at a cross-fit best step. Corruption-clustered 95 % CIs: ttt_mask mean-final **[0.25, 0.76]**, ttt_rot mean-final **[0.37, 0.69] `[R9: printed as [0.37, 0.70] in this historical entry; the record hi_mean = 0.694506 rounds to 0.69 -- review round 8, Finding 3]`** | `f8_e2_crossfit_summary.json` | **Revised downward.** The C2 gate (ρ ≥ 0.5 for ≥2 stochastic methods) still passes **2/2**. The "rising to 0.762/0.840 at the best step" claim does **not** survive: cross-fit best-step ρ is *lower* than final-step ρ for both methods |
| A2/A3 (stopped-gain variant) | Figure 2's heatmap: "realized risk improvement of optimally-stopped TTT over the frozen model"; caption "TTT helps above the curve, hurts below" | ANALYTIC (the plotted quantity cannot be negative) | Realized gain with the stopping step chosen on a disjoint replicate half: **75 of 625 cells** [73, 77] carry a genuinely **negative** gain, worst cell **−0.117** [−0.280, −0.039]; **28.1 %** of cells correctly choose t̂ = 0 (decline to adapt). Fitted threshold **0.02484** [0.02454, 0.02504], ratio to η/2 **0.9936** [0.981, 1.002]. Holdout sign accuracy **0.982** [0.974, 0.987] over all cells, **1.000** over cells resolved at 3 SE. In-sample scoring is optimistic by **+0.0106** [0.0096, 0.0128] in gain units | `f2_boundary_stopped_summary.json`, `f9_phase_figure_data.json` | **Confirmed, and the caption becomes literally true.** The boundary location is confirmed to 0.6 % on this quantity; the "hurts below" half of the caption is now backed by 75 measured negative cells instead of 0 |

---

## 3. Protocols

### f1 — measured phase boundary (replaces A2, A3)
`f1_boundary_onestep.py`. The paper's boundary α²δ²/σ² = η/2 is the flow-limit
statement that the risk *starts* decreasing at t = 0. The directly measurable,
genuinely sign-flipping version is the one-step gain
`G1 = δ² − E[u_1²]`, estimated by Monte-Carlo from `simulate_scalar`
trajectories. `u_0 = δ` holds deterministically, so the frozen risk needs no
estimate. Grid 25 × 25 (the original part_b grid), 400,000 replicates per cell
split 50/50, threshold fitted on even cells and evaluated on the disjoint odd
cells, 5 seeds. Per seed: 180–183 cells have a measured *negative* gain and
442–445 a positive one — the sign the analytic grid could not produce.
Reproduction check (asserted): on cells resolved at 5 SE the measured sign
agrees with the closed-form sign in 100 % of cells at every seed.

### f2 — measured optimally-stopped gain (Figure 2's stated quantity)
`f2_boundary_stopped.py`. `t_hat = argmin` of the risk curve on a SELECT
replicate half; realized gain `δ² − E_B[u_{t_hat}²]` on the disjoint SCORE
half, with `t_hat = 0` (decline to adapt) on the menu. Two asserted checks: no
cell's realized gain may beat the population optimum by more than 5 SE, and the
in-sample version must be optimistic relative to the held-out one. Grid
25 × 25, 20,000 replicates per cell split 50/50, 5 seeds. Both checks pass at
every seed; the measured in-sample optimism is +0.0106 gain units.

Note on the two thresholds: f2's fit (ratio **0.9936**) is closer to η/2 than
f1's (ratio **0.965**) purely because the two quantities put the boundary in
slightly different places within the same coarse grid; both bracket η/2. For
the manuscript, quote **f1** for the "does adaptation start to help" boundary
(it is the flow-limit statement the theorem makes) and **f2** for the Figure 2
heatmap.

### f3 — measured optimal stopping (replaces A4, A5)
`f3_optimal_stopping.py`. Three disjoint replicate blocks per cell: A selects
the empirical stopping step, C independently estimates the true optimal step,
B scores both. 60,000 replicates per cell (20,000 per block), 25 cells, 5
seeds. Asserted: the measured risk at the oracle step matches the closed form
within 5 SE in 100 % of cells at every seed.

### f4 — ALTA against a measured oracle (replaces A6)
`f4_alta_measured_oracle.py`. Unchanged `core.alta.alta_run` (K = 3,
κ = 1.5, T_max = 400); the oracle is simulated and evaluated out of sample
(step on one half, risk on the other) instead of taken from `t_star_theory`.
400 ALTA episodes and 40,000 oracle replicates per cell, 16 cells, 5 seeds.

### f5 — batch variance law (replaces A8)
`f5_batch_variance.py`. Three separate measurements, described in the table.
400,000 replicates per N, streamed in 25,000-replicate chunks. Asserted: the
N = 1 variance matches the closed form within 6 SE at every probe step.

### f6 — ReLU probe at fresh seeds (replaces A7)
`f6_relu_multiseed.py`. Identical design to part_e — same architecture, same
source task, same synthetic (α, σ) construction, same statistics — with every
pinned seed replaced by a fresh one and threaded properly. 2× RTX 3080, ~3 min
per seed. No divergent runs at any seed.

### f7 — risk-curve match at fresh seeds (multi-seed pass on A1)
`f7_curve_match.py`. 30-cell grid, 40,000 replicates per cell, 5 seeds.
Reports the published normalisation (÷ max of the theory curve), a pointwise
relative error, and the statistically correct |err| / SE.

### f8 — E2 cross-fit (replaces A9)
`f8_e2_crossfit.py`. Re-analysis of the **original** E2 episode records
(`results/e2/*_main_*.json`, 134,400 episodes over 390 cells) and the original
E5 `delta_feat_*.json` files — no new model runs. Within each cell a
fresh-seed permutation splits episodes into a commissioning share (phase
statistic) and a disjoint evaluation share (realized gain); the best step is
chosen on commissioning and scored on evaluation. CIs come from a
**corruption-clustered** bootstrap (1000 resamples of the 15 corruptions, all
severities of a sampled corruption travelling together), which is the right
cluster because cells sharing a corruption share images, shift, and
`delta_feat` reference. The paper's bootstrap resampled the 105 cells
independently, treating five severities of one corruption as five independent
observations; that is why its CI ([0.52, 0.81]) is much narrower than the
clustered one ([0.25, 0.76]).
Asserted before anything else runs: with `--commission 1.0` (no split) the
script reproduces the published same-sample values 0.686 / 0.694 / 0.762 /
0.840 / 0.622 / 0.742 to within 0.02. It does — see
`f8_e2_reproduction_check.json`.

### f9 — figure data
`f9_figure_data.py` emits `f9_phase_figure_data.json`: the 25 × 25 grid, both
measured gain heatmaps (mean and across-seed min/max), per-seed fitted
thresholds and holdout accuracies, and the theory boundary curve, each tagged
with its protocol string. This is what the figure track needs to redraw
`F2_phase.pdf` without any analytic quantity.

---

## 4. Claims classified MEASURED and requiring no change

The manuscript team needs to touch **none** of the following. They come from
real model runs and no closed form enters their computation (verified by
grepping the whole non-excluded tree for `excess_risk`, `t_star_theory`,
`mean_u`, `var_u`: outside `run_e1.py` there are no hits in E2/E3/E4/E5 code).

* **E2 batch mechanics** — step-1 gain 0.0000 at N=1 (bn-train), −0.52 points at
  10 steps, +0.13 at N=16, +0.19 at N=64; Spearman(N, σ²_batch) = −1.000;
  per-point variance max/min ratio 2.73; the CIFAR-100 eval-BN negative result.
* **E2 calibration identity (C4)** — α_ent < 0 in 100 % of confident-wrong
  episodes (n = 1554) and 0 % of confident-right (n = 2873); ρ(α_ent, correct)
  = 0.863; mean fitted T = 1.19; mean α_ent 0.0957 → 0.1019; early adapted-loss
  change −0.38. Temperature is fitted on a disjoint clean split already.
* **E3 (all)** — motion blur sev 3 EATA 37.9 % → 51.5 % (t̂ = 2.6, BN floor
  51.0 %); contrast sev 3 tent fixed-10 45.6 % → 63.9 %; pooled ALTA gap
  −0.65 points over 90 cells; seed spread ≤ 1.0 point (median 0.42 over 24
  multi-seed cells); the K=3-ensembled fixed-10 control 33.6 % vs 33.1 % vs
  ALTA 32.4 % and 45/45 cells; the 6/90 safety violations and the 13-of-14
  defocus-blur diagnosis.
  *Caveat to keep in the text (already disclosed there): "best fixed" is
  selected per cell with test labels, which makes the ALTA gap conservative.*
* **E4 (all)** — perplexity improvements 0.96 (code) / 0.57 (PubMed) / 0.21
  (WikiText) / 0.067 (legal); α ∈ [0.24, 0.46]; mean t̂ ≈ 17.5; within-domain
  ρ = 0.582 / 0.905 / 0.868 / 0.834; the loss-proxy failure (−0.33 to 0.28);
  the cross-domain sign-transfer collapse 0.99 → 0.31 (a genuine held-out
  transfer test).
* **E5 learning-rate ablation** — mean best-step gains 0.193 / 0.088 / 0.217;
  rank stability ρ_s = 0.60 / 0.57 / 0.59.
* **M0 source models** — all accuracies.

Note: the E5 ALTA seed-robustness ablation (`results/e5/e1_d_seed43.json`)
inherits A6's closed-form oracle denominator; f4 supersedes it with five fresh
seeds and a measured oracle.

---

## 5. Handoff map for the manuscript agent

Anchors given for `paper/is/paper/`; the same lines exist in `paper/` (the
`introduction.tex` anchors are one line lower in the IS tree).

| Original text (short quote) | File : line | Replacement | Source JSON |
|---|---|---|---|
| "the fitted threshold is $0.02504$ against the predicted flow-limit value $\eta/2 = 0.025$---a ratio of $1.002$" | `sections/experiments.tex:75-76` | fitted threshold **0.0241** [0.0233, 0.0250], ratio **0.965** [0.931, 1.002]; preferred phrasing: the measured boundary is bracketed by **[0.0233, 0.0273]** at all five seeds and η/2 = 0.025 lies inside it | `f1_boundary_onestep_summary.json` |
| "holdout sign-prediction accuracy is $1.00$" | `sections/experiments.tex:78` | **0.994** [0.990, 0.997] over all holdout cells; **1.000** over the 96 % of cells resolved at 3 Monte-Carlo SE | `f1_boundary_onestep_summary.json` |
| "the fitted phase threshold is $1.002$ times the predicted $\eta/2$ … with holdout sign-prediction accuracy $1.00$" | `sections/introduction.tex:126-128` | ratio **0.965** [0.931, 1.002]; accuracy **0.994** | `f1_boundary_onestep_summary.json` |
| "$1.002$ times its predicted location" | `sections/conclusion.tex:20` | **0.965×** [0.931, 1.002] | `f1_boundary_onestep_summary.json` |
| "within $0.2\%$ of its predicted position" | `sections/abstract.tex:27` | **must be revised** — 0.2 % is finer than the 25 × 25 grid resolves. Use "within the resolution of the simulated grid, bracketed by [0.0233, 0.0273] around the predicted 0.025" or "within 7 %" | `f1_boundary_onestep_summary.json` |
| "fitted / theoretical threshold  1.002" | `figures/T4_e1_gates.tex:9` | **0.965** (mean over 5 seeds; range 0.931–1.002) | `f1_boundary_onestep_summary.json` |
| holdout sign accuracy row | `figures/T4_e1_gates.tex:8` | **0.994** (all cells) / **1.000** (resolved cells) | `f1_boundary_onestep_summary.json` |
| Figure 2 (`figures/F2_phase.pdf`) heatmap + fitted-boundary overlay; caption "dashed: threshold fitted to the data (ratio $1.002$). TTT helps above the curve, hurts below" | `sections/experiments.tex:135-148`, `figures/latex_includes.tex:29` | redraw from measured gains. Fitted-boundary ratio **0.994** [0.981, 1.002] on the optimally-stopped gain (or **0.965** on the one-step gain). The caption's "hurts below" is now literally true: **75 of 625 cells** carry a measured negative realized gain (one-step version: **181 of 625**), where the published analytic grid had **zero** | `f9_phase_figure_data.json`, `f2_boundary_stopped_summary.json` |
| "worst-case relative error of $1.8\%$ over the 30-cell grid" | `sections/experiments.tex:71`, `sections/introduction.tex:123-125`, `sections/experiments.tex:130`, `figures/latex_includes.tex:17` | **1.15 %** [0.85, 1.58] at 5 fresh seeds and 40k replicates (same normalisation); optionally add the pointwise **2.23 %** | `f7_curve_match_summary.json` |
| "within $5\%$ of the theoretical minimum in $100\%$ of cells" | `sections/experiments.tex:85-86`, `appendix/experimental_details.tex:91` | **100 %** of cells within 5 % of a **measured** oracle; median gap 0.000, max 0.021 | `f3_optimal_stopping_summary.json` |
| "within a factor of two of $\tstar$ in $88\%$ of cells" | `sections/experiments.tex:87` | **96 %** [92, 100] vs a measured oracle step; **90.4 %** [88, 96] vs the theoretical $t^\star$ | `f3_optimal_stopping_summary.json` |
| "the p90 realized risk stays within … in 16 of 16 cells"; "median risk ratios … range from $0.99$ to $1.37$ … drop to $0.29$--$0.38$ at $\alpha=1$"; "measured constants are 1--4" | `sections/experiments.tex:95-106` | **16/16 at all 5 seeds** (both gates); median ratios **1.00–1.37** and **0.31–0.35** at α=1; measured constants **1–2.4**. Only change needed: say the oracle is measured out of sample, and that it now holds at 5 independent seeds rather than 1 | `f4_alta_measured_oracle_summary.json` |
| "Part~d was reproduced at a second seed as an E5 ablation" / "at seed 43 the p90 diagnostic gate and the safety-versus-frozen gate both pass in 16 of 16 cells, with worst-cell p90 risk ratio $2.53$ … and worst-cell median ratio $1.37$" | `sections/experiments.tex:109`, `sections/experiments.tex:509-516` | supersede with 5 fresh seeds and a measured oracle: worst-cell p90 ratio **2.33** [2.27, 2.42], worst-cell median ratio **1.365** [1.317, 1.426] | `f4_alta_measured_oracle_summary.json` |
| "adaptation at $\alpha=0$ is harmful (mean excess $0.0411$)" | `sections/experiments.tex:115` | **0.043** [**−0.024**, 0.167] over 5 fresh seeds — harmful at 4/5 seeds. Recommend demoting to "harmful on average, though the effect is small and not present at every seed" | `f6_relu_multiseed_summary.json` |
| "the $\alpha{=}1$ versus $\alpha{=}0$ margin is $0.3485$" | `sections/experiments.tex:116` | **0.361** [0.222, 0.513]; monotone in α at 5/5 seeds | `f6_relu_multiseed_summary.json` |
| "the measured variance matches $\sigma^2/N$ to a maximum relative error of $0.35\%$" | `sections/experiments.tex:120-121` | rewrite: measured variance matches σ²/N to **0.57 %** [0.48, 0.68] (Monte-Carlo SE 0.22 %); equivalently N·Var is constant in N to **0.8 %**. The old 0.35 % was a min-risk agreement, not a variance | `f5_batch_variance_summary.json` |
| "Spearman $\rho$ of $0.686$ … and $0.694$ … for ttt\_mask, rising to $0.762$/$0.840$ at the best step, and $0.622$ … /$0.742$ … for ttt\_rot" | `sections/experiments.tex:189-196`, `sections/introduction.tex:133-135` | cross-fit: ttt_mask **0.540**/**0.493**; ttt_rot **0.546**/**0.630**; best-step cross-fit **0.524**/**0.509** and **0.223**/**0.111** — i.e. the "rising at the best step" clause must be **dropped**. Corruption-clustered CIs [0.25, 0.76] and [0.37, 0.69] `[R9: printed as [0.37, 0.70] in this historical entry; the record hi_mean = 0.694506 rounds to 0.69 -- review round 8, Finding 3]`. C2 gate still 2/2 | `f8_e2_crossfit_summary.json` |
| "bootstrap $95\%$ CI over the 105 cells $[0.52, 0.81]$" | `sections/experiments.tex:191-194` | replace with the corruption-clustered CI **[0.25, 0.76]**; the cell-level bootstrap treats five severities of one corruption as independent | `f8_e2_crossfit_summary.json` |

**No change needed** (see §4): all E2 batch and calibration numbers, all E3
numbers, all E4 numbers, the E5 learning-rate ablation, and the M0 source-model
table.

---

# Round 1 — external review response (computation & figures)

Scope: the computation/figure half of external review round 1
(`paper/is/REVIEW_ROUNDS.md`, Round 1). New code lives in
`experiments/ttt/is_fresh/` as `f10`–`f15`, `f8b`, `fig_f2_phase.py`,
`fig_f3_alta.py`, `fig_f4_e2.py`, `make_release_zip.py`, `f_scope_bench.py`.
Solvable-model reruns keep the established seeds **20260801–05**; every new
resampling procedure uses **20260806–10**, and the one new GPU run uses
**20260806**. No original-pipeline seed is reused.

Same framing as §1–§5: **fix-forward**. Where the corrected measurement
confirms the published one, that is said plainly; where it does not — and in
three places it does not — the corrected number is the one reported.

---

## R1.1 Figure 2 conflated the oracle phase with stopping-selection error (finding #8)

`f10_oracle_grid.py` measures all three gain quantities on the SAME replicates
of the same 25 x 25 grid (eta = 0.05, sigma = 1, T = 400, 20,000 replicates per
cell split 50/50 into SELECT / SCORE, five seeds):

| quantity | definition | sign |
|---|---|---|
| one-step | `G1 = d^2 - E_B[u_1^2]` | genuinely signed |
| oracle | `G_ora = max_{0<=t<=T} (d^2 - E_B[u_t^2])` | **>= 0 by construction** (t = 0 is on the menu) |
| selected | `G_sel = d^2 - E_B[u_that^2]`, `that = argmin_t E_A[u_t^2]` | signed |
| selection error | `G_sel - G_ora` | **<= 0 identically** |

| measurement | mean over 5 seeds | range |
|---|---|---|
| cells with one-step gain **< 0** | **181.8 / 625** | 175–186 |
| … of those, resolved at 3 Monte-Carlo SE | **138.6** | 136–142 |
| cells where the oracle **declines to adapt** (t = 0) | **174.2 / 625** | 167–177 |
| cells with oracle gain > 0 | **450.8 / 625** | 448–458 |
| cells with **genuinely** negative selected-stopping gain | **11.6 / 625** | 10–13 |
| cells with non-zero selection error | **430 / 625** | 421–437 |
| mean selection error, relative to delta^2 | **-0.103 %** | -0.117 % … -0.096 % |
| worst-cell selection error, relative to delta^2 | **-3.13 %** | -4.05 % … -2.13 % |
| Monte-Carlo optimism of the oracle scan (audited on a split of B) | +0.11 % of delta^2 | 0.09 %–0.13 % |
| fitted threshold / (eta/2), one-step | **0.968** | 0.785–1.093 |
| fitted threshold / (eta/2), oracle-adapts | **0.922** | 0.785–0.981 |
| holdout sign accuracy, one-step | **0.979** | 0.965–0.987 |
| … on cells resolved at 3 SE | **0.9993** | 0.996–1.000 |
| holdout accuracy, oracle-adapts label | **0.985** | 0.974–0.994 |
| measured vs closed-form one-step sign agreement (5 SE cells) | **1.000** | 1.000 |

**A correction to this document's own earlier number.** The §5 handoff line
says "75 of 625 cells carry a measured negative realized gain" for the
selected-stopping panel. That count has no tolerance floor, and at cells where
the rule correctly declines (that = 0) the realized gain is 0 only up to float
rounding — `u_0 = delta(1-alpha^2) + alpha*delta*alpha` is not bit-identical to
delta. At seed 20260801, 137 cells are raw-negative and **126 of them have
that = 0**, i.e. they are rounding noise of order 1e-16 * delta^2. With a 1e-9
relative floor the honest count is **11**. The claim "TTT hurts below the
boundary" should rest on the **one-step** panel (175–186 negative cells, 136–142
of them resolved at 3 SE), not on the selected-stopping panel.

**SUPERSESSION (integration decision, round 1).** For every E1
boundary/sign quantity, `f10_oracle_grid_summary.json` **supersedes**
`f1_boundary_onestep_summary.json`, `f2_boundary_stopped_summary.json` and
`f9_phase_figure_data.json`, and the manuscript now quotes f10 everywhere
(text, Figure 2 caption, Table T4, introduction). Reason: f10 measures the
one-step, oracle and selected-stopping gains on the *same* replicates of the
same grid at the same five seeds, so the text and the figure cannot drift
apart and the three quantities are directly comparable; f1/f2/f9 measured
them on separate simulations, which is what allowed the caption to describe
one quantity while the text quoted another. Concretely, the manuscript's
fitted ratio 0.965 (f1, one-step) becomes **0.968**, 0.994 (f2, stopped)
becomes **0.922** for the oracle-adapts label, holdout sign accuracy 0.994
[0.990, 0.997] becomes **0.979** [0.965, 0.987] (resolved-cell 1.000 becomes
**0.999**), and the grid-resolution bracket [0.0233, 0.0273] becomes
**[0.0225, 0.0299]** — wider because f10 runs 20,000 rather than 400,000
replicates per cell, and stated only over cells resolved at 3 Monte-Carlo SE,
which is the qualifier the original bracket claim omitted (without it the
bracket is false at every seed, in f1 and f10 alike). No f9-era number is
quoted anywhere in the manuscript, labelled or otherwise.

**Boundaries.** Four reference curves are emitted, all closed forms and all
labelled as predictions under test, never fitted:

* exact one-step discrete: `alpha^2 delta^2 (2 - eta alpha^2) = sigma^2 eta`
  (from `Exc(1) = Exc(0)`);
* exact finite-horizon oracle: `min_{0<=t<=T} Exc(t) = delta^2`, solved
  numerically per alpha — the exact boundary of the quantity in panel (b);
* exact continuous-derivative form (the condition quoted in the review):
  `2 log(1/(1-eta)) alpha^2 (delta^2 - eta sigma^2/(2-eta)) = (1-alpha^2) eta^2 sigma^2`;
* flow limit `alpha^2 delta^2 / sigma^2 = eta/2`, the line the published figure
  overlaid.

At eta = 0.05 the exact and flow boundaries differ by well under 1 % over most
of the alpha range and by about 1.3 % at alpha = 1; the figure plots both, so
the reader sees the size of the approximation instead of being told it is
small.

**Figure.** `fig_f2_phase.py` -> `paper/is/paper/figures/F2_phase.pdf`, now
three panels: (a) one-step signed gain (diverging, centred at zero, cells
negative at every seed stippled); (b) measured oracle gain (sequential from 0,
labelled ">= 0 by construction"); (c) selection error. Exact boundary, flow
limit and measured fitted boundary overlaid on (a) and (b).

---

## R1.2 Figures 3 and 4 regenerated from the fresh pipeline (finding #4)

**F3_alta.pdf** — `fig_f3_alta.py`, three panels, five seeds (20260801–05), one
marker per (seed, cell):

* (a) median selected step that against the **measured** oracle step;
* (b) realized-risk ratio against the measured single-trajectory oracle, with
  the 3 log T = 18.0 diagnostic line retained. Max p90 ratio **2.42**; the
  diagnostic bound holds in **80/80 (seed, cell) pairs**;
* (c) the same realized risks against the **compute-matched** K = 3 oracle
  (see R1.3).

The published panel plotted seeds 42 and 43 against a closed-form oracle and is
fully superseded.

**F4_e2_phase.pdf** — `fig_f4_e2.py`, annotated with cross-fit correlations
only. Per-cell markers are averaged over the five commissioning/evaluation
split seeds; each panel carries the cross-fit rho, its across-seed range, its
corruption-clustered 95 % interval, and the superseded same-sample value in
grey:

| panel | cross-fit rho (mean, range over 5 splits) | clustered 95 % CI | same-sample (superseded) |
|---|---|---|---|
| (a) ttt_rot | **0.546** (0.511–0.592) | [0.37, 0.69] | 0.622 |
| (b) ttt_mask | **0.540** (0.483–0.610) | [0.25, 0.76] | 0.686 |
| (c) tent | **-0.676** (-0.687 … -0.664) | — | -0.686 |
| (c) pl | **-0.849** (-0.870 … -0.836) | — | -0.868 |

The deterministic panel is new work: `f8b_e2_crossfit_det.py` applies f8's
cross-fit, unchanged, to tent and pl with the loss-proxy statistic, so no number
on the figure is same-sample any more.

**Panel (c) updated after R1.7 landed.** It originally carried the title
"(exploratory: arch. also differs)". Once the architecture control existed that
title was stale, so panel (c) now also plots the matched-architecture entropy
arm (tent @ ResNet-26+GN, rho = **-0.902**, open triangles) and is titled
"(architecture controlled)". The caption states explicitly that the filled
markers are the full grid (105 / 75 cells) while the triangles are the 45 cells
the control run covers, and points at Table T5 for the like-for-like comparison
in which every arm is recomputed on those same 45 cells.

---

## R1.3 ALTA against a compute-matched oracle (finding #5)

`f13_compute_matched.py` measures, per cell and per seed, the risk of the
**mean of K = 3 independent trajectories** at every step, picks the best step on
a SELECT block of groups and scores it on a disjoint SCORE block. In population
this is `min_t {m_t^2 + V_t/K}`; the measured value agrees with that closed form
to within 5 Monte-Carlo SE at every cell (asserted).

| | vs single-trajectory oracle | vs compute-matched K = 3 oracle |
|---|---|---|
| median risk ratio, over all cells and seeds | **0.26 – 1.43** | **0.78 – 1.71** |
| worst-cell p90 ratio (mean over seeds) | **2.36** (2.25–2.48) | **5.58** (5.36–5.95) |
| cells of 16 where ALTA's median beats the oracle | **4.2** (4–5) | **2.6** (1–3) |
| Theorem-5 diagnostic bound 3 log T = 18.0 | holds 16/16, 5/5 seeds | holds 16/16, 5/5 seeds |

The decisive detail is the alpha = 1 column, where the manuscript reports ALTA
"beating the oracle" with median ratios 0.29–0.38:

| alpha | delta/sigma | median vs K = 1 | median vs compute-matched | R1/RK |
|---|---|---|---|---|
| 1.00 | 1 | 0.30 | **0.90** | 2.98 |
| 1.00 | 2 | 0.34 | **1.00** | 2.96 |
| 1.00 | 4 | 0.34 | **1.02** | 3.01 |
| 1.00 | 8 | 0.33 | **0.99** | 3.01 |

The apparent 3x advantage over the oracle is **exactly the K = 3 variance
reduction** (R1/RK ~ 3.00 at alpha = 1, where the trajectory is pure noise
around a converged mean). Against a comparator allowed the same compute, ALTA
is at parity, not ahead. The empirical contribution is adaptive label-free
stopping; it is not superior accuracy at matched compute, and the manuscript
should say so. The theorem's diagnostic bound survives both comparators.

---

## R1.4 E4 confidence intervals were pseudoreplicated (finding #11)

`f11_e4_cluster_ci.py`, over the original `results/e4/*_ln_s{0,1,2}.json`
records: three interval constructions on the same statistic, B = 2000, five
bootstrap seeds (20260806–10), endpoints averaged over bootstrap seeds. The
**point estimates do not change**; only the intervals do.

| domain | rho | published CI (1500 pooled rows, i.i.d.) | **document-clustered CI** (500 documents, seeds nested) | width ratio |
|---|---|---|---|---|
| code | 0.582 | [0.55, 0.62] | **[0.517, 0.639]** | x1.65 |
| legal | 0.905 | [0.89, 0.92] | **[0.884, 0.921]** | x1.57 |
| PubMed | 0.868 | [0.85, 0.88] | **[0.837, 0.892]** | x1.57 |
| WikiText | 0.834 | [0.81, 0.85] | **[0.802, 0.861]** | x1.55 |

Seed-averaged (500 independent units, one row per document) as a secondary
estimand: rho = 0.606 [0.542, 0.667] code, 0.928 [0.910, 0.942] legal,
0.890 [0.861, 0.914] PubMed, 0.862 [0.831, 0.886] WikiText.

Perplexity-improvement intervals at the ALTA stop widen by the same factor:

| domain | improvement | published CI | clustered CI |
|---|---|---|---|
| code | 0.956 | [0.811, 1.125] | **[0.713, 1.265]** |
| legal | 0.0666 | [0.0643, 0.0688] | **[0.0626, 0.0705]** |
| PubMed | 0.570 | [0.360, 0.855] | **[0.309, 1.075]** |
| WikiText | 0.210 | [0.204, 0.215] | **[0.200, 0.220]** |

The manuscript's quoted legal CI `[0.064, 0.069]` becomes `[0.0626, 0.0705]`.
The widening is almost exactly sqrt(3), which is what it must be: the
intraclass correlation of the per-document gain is **0.972–0.9999** across the
four domains (0.818–0.957 for the phase statistic), so the three adaptation
seeds of a document are near-duplicates and the effective sample size is 500,
not 1500. Every table and interval should state **n = 500 documents x 3
adaptation seeds**, not 1500.

The script reproduces the published intervals under the original i.i.d.-row
construction (max endpoint gap <= 0.006), which is asserted, so the widening is
attributable to the resampling unit and nothing else.

> **SUPERSEDED IN ROUND 16 — interval endpoints only** (external review round
> 15, substantive finding 1). Everything above is the round-1 record and is
> kept as written. Two things in it are now known to be wrong.
>
> 1. *"endpoints averaged over bootstrap seeds"* is what `f11` actually did,
>    but every other document then described the result as a single
>    document-clustered percentile interval. A mean of five percentile
>    endpoints is not a percentile. `f29_e4_pooled_ci.py` replays f11's exact
>    five streams (per-stream endpoint gap asserted at `0.0`), **pools the
>    5 × 2000 = 10,000 draws into one distribution and reads one 2.5/97.5
>    percentile pair off it**. Point estimates are asserted unchanged at `0.0`.
> 2. *"The widening is almost exactly sqrt(3)"* was already superseded in the
>    CURRENT VALUES section above; the design effects straddle sqrt(3) rather
>    than reproducing it.
>
> The current endpoints, from `f29_e4_pooled_ci.json`:
>
> | domain | rho | i.i.d.-row CI (published construction, reproduced) | **document-clustered CI** (pooled 10,000 draws) | width ratio |
> |---|---|---|---|---|
> | code | 0.582 | [0.544, 0.617] | **[0.517, 0.639]** | x1.657 |
> | legal | 0.905 | [0.892, 0.916] | **[0.885, 0.921]** | x1.568 |
> | PubMed | 0.868 | [0.849, 0.884] | **[0.837, 0.892]** | x1.566 |
> | WikiText | 0.834 | [0.814, 0.852] | **[0.802, 0.861]** | x1.552 |
>
> | domain | improvement | i.i.d.-row CI | **clustered CI** (pooled 10,000 draws) |
> |---|---|---|---|
> | code | 0.956 | [0.811, 1.124] | **[0.712, 1.266]** |
> | legal | 0.0666 | [0.0643, 0.0688] | **[0.0626, 0.0705]** |
> | PubMed | 0.570 | [0.360, 0.857] | **[0.309, 1.075]** |
> | WikiText | 0.210 | [0.204, 0.215] | **[0.200, 0.220]** |
>
> Seed-averaged secondary estimand: rho = 0.606 [0.542, 0.666] code,
> 0.928 [0.910, 0.942] legal, 0.890 [0.861, 0.914] PubMed,
> 0.862 [0.831, 0.886] WikiText.
>
> Against the round-1 table above, three printed endpoints move: legal rho low
> 0.884 → 0.885, code improvement [0.713, 1.265] → [0.712, 1.266], and the
> seed-averaged code high 0.667 → 0.666. The largest change to any endpoint,
> printed or not, is **0.0022**. The asserted i.i.d.-row reproduction gap is
> **0.0062** (the round-1 text rounded it to "<= 0.006"; the record has always
> said 0.0062, and the value is now bound in the reconciliation).
> `f11_e4_cluster_ci.json` is retained unmodified as the audit trail.

---

## R1.5 E4 proxy: leave-one-domain-out validation (finding #12)

`f12_e4_proxy_loo.py`. Unit of analysis is the **document** (three seeds
averaged, so R1.4's problem does not recur). For each held-out domain, the proxy
variant is selected by mean within-domain Spearman on the **other three**
domains, frozen, and scored on the held-out domain's 500 documents. Eleven
candidates, including the paper's `phase_v2 = alpha|alpha| d_v2 / sigma^2`, the
loss proxy, a document-difficulty baseline (`frozen_ce`), and a pure alignment
statistic (`alpha_only = alpha|alpha|/sigma^2`) with no shift term at all.

**Result: PARTIAL — the transfer succeeds, the attribution does not.**

Per-domain Spearman on seed-averaged documents (the selection table):

| variant | code | legal | PubMed | WikiText | mean |
|---|---|---|---|---|---|
| `alpha_only` (**no delta at all**) | +0.703 | +0.942 | +0.898 | +0.913 | **+0.864** |
| `phase_v2_gnorm` | +0.757 | +0.927 | +0.895 | +0.869 | +0.862 |
| `phase_v2` (**the paper's**) | +0.606 | +0.928 | +0.890 | +0.862 | +0.822 |
| `phase_v2_nosigma` | +0.517 | +0.931 | +0.892 | +0.862 | +0.800 |
| `delta_v2_raw` (**delta alone**) | -0.388 | -0.019 | +0.044 | +0.120 | **-0.061** |
| `frozen_ce` = `delta_ce_raw` (difficulty) | +0.442 | -0.385 | +0.100 | -0.288 | -0.033 |
| `phase_ce` (loss proxy) | -0.215 | -0.819 | +0.188 | -0.242 | -0.272 |

Per fold (**superseded endpoints** — these brackets are the round-1
endpoint-averaged pairs from `f12`; the current pooled percentile endpoints
are in the CURRENT VALUES table above, in `f31_e4_proxy_pooled.json` and in
the manuscript's Table T6. No point estimate below moved):

| held out | selected on the other 3 | held-out rho (selected) | held-out rho (`phase_v2`) | difficulty baseline | partial rho of d_v2 given alignment (95 % CI) |
|---|---|---|---|---|---|
| code | `alpha_only` | +0.703 [0.648, 0.751] | +0.606 | +0.442 | **-0.287** [-0.368, -0.203] |
| legal | `phase_v2_gnorm` | +0.927 [0.910, 0.941] | +0.928 | -0.385 | +0.003 [-0.082, +0.090] |
| PubMed | `alpha_only` | +0.898 [0.870, 0.921] | +0.890 | +0.100 | +0.091 [+0.001, +0.183] |
| WikiText | `phase_v2_gnorm` | +0.869 [0.840, 0.892] | +0.862 | -0.288 | +0.028 [-0.055, +0.114] |

What survives:

* the frozen selection **transfers**: held-out rho is +0.70 to +0.93 in all four
  folds, and `phase_v2` itself transfers at +0.61 to +0.93. The high
  within-domain correlations are therefore **not** a post-selection artefact of
  the four domains, and the circularity criticism is answered on that point;
* the correlations **beat the document-difficulty baseline** decisively in every
  fold (baseline -0.385 to +0.442, mean -0.033).

What does not survive:

* the paper's exact proxy `phase_v2` is selected in **0 of 4** folds, and a
  delta_v2-family variant in only **2 of 4**;
* `alpha_only` — the alignment/noise factor with **no shift magnitude
  whatsoever** — matches or exceeds the full statistic in every domain
  (mean +0.864 vs +0.822);
* `delta_v2_raw` alone has essentially no within-domain signal (mean -0.061),
  and the partial Spearman of delta_v2 with the gain, controlling for
  `alpha_only`, is **about 0 in two folds, +0.091 in PubMed and -0.287 in
  code**. Its bootstrap CI excludes zero on the favourable side in
  **1 of 4** folds and on the adverse side in **1 of 4**.

  > **Round-17 correction (external review round 16, finding 1.1). The
  > sentence above read "about 0 in three folds and -0.29 in code" and
  > "excludes zero on the favourable side in 0 of 4 folds". The second half
  > was FALSE, and had been false since it was written.** `f12`'s own record
  > has always reported
  > `summary/n_folds_partial_rho_delta_v2_ci_excludes_zero = 1`: PubMed's
  > partial correlation is `+0.0913` with an interval of
  > `[+0.001475, +0.183007]` under the endpoint-averaged construction and
  > `[+0.000440, +0.182915]` pooled, and **both exclude zero on the positive
  > side**. The census was typed into this file and into
  > `sections/experiments.tex`, contradicted the JSON stored beside it, and
  > survived sixteen rounds because no `f12` quantity was bound by
  > `r9_reconcile.py` at all -- structurally the same hole that let round
  > 15's E4 endpoint defect through. Every `f31` endpoint and **both**
  > exclusion counts are now bound (PASS 1), and PASS 1b asserts on the
  > `.tex` corpus that Section 7.4 states the favourable-side census as
  > "1 of 4" and that no `.tex` claims the shift proxy adds "nothing
  > measurable". The conclusion of this section does not reverse; it
  > narrows, from *no measurable increment* to **no consistent incremental
  > benefit**, because the increment is resolved in two of four folds with
  > opposite signs.

Conclusion to be reported: within a domain, the per-document phase statistic
predicts per-document gain — but what carries the prediction is
alpha|alpha|/sigma^2, not the representation-distance proxy for delta. The E4
result supports the alignment half of the theory and **does not** establish that
the theoretically defined delta has been recovered. The manuscript's own
"delta-identifiability lesson" should be strengthened accordingly rather than
softened.

A structural note worth stating in the text: within a domain,
`delta_ce = frozen_cont_ce - (a per-domain constant)`, so the "loss-based proxy"
and the "document-difficulty baseline" are the **same rank statistic**. They
cannot be distinguished by any within-domain rank test.

---

## R1.6 delta_feat is not monotone in the shift level (finding #9, cheap half)

`f14_deltafeat_check.py` validates delta_feat against two yardsticks that never
entered its construction: the CIFAR-10/100-C corruption **severity** (1–5,
externally defined) and the frozen model's **labelled** cross-entropy and error
rate.

| check | result |
|---|---|
| (dataset, arch, corruption) triples with mean delta_feat strictly increasing in severity | **23 / 60** |
| … with Spearman(severity, mean delta_feat) = +1 | **7 / 60** |
| episode-level Spearman(severity, delta_feat), median over the 60 triples | **-0.015** (min -0.502, max +0.663) |
| within-cell Spearman(delta_feat, frozen labelled loss), median over 390 cells | **-0.144** |
| … fraction of cells positive | **20 %** |
| … fraction above +0.3 | **1 %** |

Cell-level, by method (and therefore by architecture):

| method | arch | rho vs mean frozen loss | rho vs frozen error rate | rho vs severity |
|---|---|---|---|---|
| ttt_mask | ResNet-26+GN | **+0.784** | +0.773 | +0.434 |
| ttt_rot | ResNet-26+GN | **+0.764** | +0.747 | +0.429 |
| tent | WRN-28-10+BN | **-0.543** | -0.536 | -0.378 |
| pl | WRN-28-10+BN | **-0.921** | -0.932 | -0.519 |

Two things follow, and both matter for finding #9.

1. "delta_feat estimates delta up to an unknown monotone transform" is **not
   supported**. It is not monotone in the externally defined shift level
   (23/60 triples), and within a corruption-severity cell it is, if anything,
   *negatively* related to the labelled risk. It must be described as a
   heuristic representation-distance diagnostic.
2. Its relationship to labelled risk **reverses sign with the architecture**
   (+0.78 on ResNet-26+GN, -0.92 on WRN-28-10+BN). The published E2 sign flip
   between the stochastic and deterministic regimes is therefore consistent with
   a property of the *proxy in that feature space*, not necessarily with the
   objective violating assumption A2. This is a second, independent reason the
   current E2 comparison cannot identify the claimed mechanism — and it is
   measurable without any new run.

---

## R1.7 Architecture-controlled entropy run (finding #9, fix-forward) — DONE

`f15_e2_entropy_gn.py` runs the deterministic **entropy** objective on the
**ResNet-26 + GroupNorm** architecture the stochastic objectives use, under the
unchanged original E2 episodic protocol. The single intervention is
`adapt_cifar.METHOD_ARCH["tent"] = "resnet26ttt"`; the episode sampler,
alignment measurement, adaptation subset, loss, step grid and record schema are
the original code, imported not copied. This yields two contrasts with one
factor held fixed each:

* tent @ ResNet-26+GN vs ttt_rot / ttt_mask @ ResNet-26+GN — objective only;
* tent @ ResNet-26+GN vs tent @ WRN-28-10+BN — architecture only.

Grid: CIFAR-10-C, 15 corruptions x severities {1, 3, 5}, 256 episodes/cell,
N = 1, 20 steps, lr 1e-3, bn-mode eval, seed **20260806**. The source model is
trained from scratch here (200 epochs) because the only local ResNet-26+GN
checkpoints sit under directories this work stream is not permitted to read.

**Source gate, restated and audited.** The first launch asserted
`train_source.py`'s CIFAR-10 threshold for `resnet26ttt`, test acc >= 0.93. The
**published** E2 source models do not meet it: `results/m0/cifar10_resnet26ttt_s{0,1,2}.json`
record test acc 0.9203 / 0.9152 / 0.9216 (rot 0.9121 / 0.9061 / 0.9064) and
`"gate_pass": false` in all three. The 0.93 in the training script is an
aspiration the paper's own models fail. The gate is therefore restated as the
**comparability criterion** it was meant to be — rot acc >= 0.85 (the original
rotation gate, which the published models do pass) and test acc >= 0.905, i.e.
the weakest published model (0.9152) less a one-point tolerance — and the
published range is loaded from the m0 records and written into the output for
audit. This changes no random number, so the seed stayed 20260806.

Measured (`e2_gn/f15_source_gate.json`): **test acc 0.9165, rot acc 0.9058**,
inside the published range 0.9152–0.9216. Gate passes. Run wall clock 156.2 min
on one RTX 3080 (81.5 min source training, 74.7 min adaptation), 45/45 cells,
11,520 episodes, no crash.

### Correlation result (`f16_e2_gn_analysis.py` -> `f16_e2_gn_summary.json`)

The cross-fit is f8's, unchanged. **Every arm is recomputed on the same 45
cells the new run covers** (CIFAR-10-C, 15 corruptions x severities {1,3,5}), so
no row is compared against a different grid. 5 split seeds (20260801–05),
corruption-clustered bootstrap over the 15 corruptions.

| objective | arch | statistic | eps/cell | same-sample | cross-fit rho (mean-final) | across-seed range | clustered 95% | rho (median-final) |
|---|---|---|---|---|---|---|---|---|
| entropy (tent) | **ResNet-26+GN** | loss proxy | 256 | -0.973 | **-0.902** | -0.912 … -0.876 | [-0.950, -0.780] | -0.156 |
| entropy (tent) | WRN-28-10+BN | loss proxy | 384 | -0.966 | **-0.939** | -0.948 … -0.926 | [-0.966, -0.886] | -0.085 |
| pseudo-label | WRN-28-10+BN | loss proxy | 384 | -0.916 | -0.905 | -0.942 … -0.858 | [-0.945, -0.837] | -0.068 |
| ttt_rot | ResNet-26+GN | loss proxy | 384 | +0.090 | **+0.151** | +0.031 … +0.310 | [-0.222, +0.509] | +0.525 |
| ttt_mask | ResNet-26+GN | loss proxy | 384 | +0.252 | **+0.253** | +0.226 … +0.297 | [-0.146, +0.577] | +0.396 |
| entropy (tent) | **ResNet-26+GN** | feature proxy | 256 | +0.071 | **+0.092** | -0.030 … +0.347 | [-0.211, +0.375] | -0.044 |
| ttt_rot | ResNet-26+GN | feature proxy | 384 | +0.516 | +0.418 | +0.353 … +0.449 | [+0.067, +0.677] | +0.598 |
| ttt_mask | ResNet-26+GN | feature proxy | 384 | +0.690 | +0.610 | +0.561 … +0.718 | [+0.297, +0.817] | +0.727 |

**Verdict: the negative correlation reproduces on the matched architecture.**
A double dissociation, both halves on the same cells:

* **objective fixed, architecture changed:** -0.902 (GN) vs -0.939 (BN).
  Clustered intervals overlap almost completely. Architecture and
  normalisation account for essentially none of the sign.
* **architecture fixed at ResNet-26+GN, objective changed:** -0.902 (entropy)
  vs +0.151 / +0.253 (ttt_rot / ttt_mask), same statistic, same cells. Under the
  feature proxy — the statistic the stochastic panels use, and joined from the
  *same* delta_feat records, i.e. at the architecture where R1.6 shows that proxy
  is *positively* related to labelled risk — entropy gives +0.092 with a
  clustered interval [-0.211, +0.375] spanning zero, against +0.418 / +0.610.

So the R1.6 alternative explanation (the sign flip is a property of delta_feat in
that feature space) is also ruled out by measurement: at the architecture where
delta_feat behaves *well*, the deterministic objective still carries no rank
information while the stochastic ones do. The objective is the factor.

**Statistic control.** The strong negative sign is not an artefact of the
loss-proxy statistic: applied to the stochastic arms on the same cells it gives
+0.151 and +0.253, not negatives.

**What this does NOT establish, and is stated in the paper:**

1. The theory does not predict the negative sign. Failure of A2 withdraws the
   guarantee; it does not assert an anti-correlation. The run identifies which
   factor produces the observed sign, not a prediction of the theory.
2. The anti-correlation is specific to the loss proxy and to the **mean**
   aggregation. Under the feature proxy the matched-architecture entropy arm is a
   null, not a negative; under the median aggregation the deterministic arms are
   weak on this subset (-0.156 GN, -0.085 BN). The robust claim is that the two
   objective families differ, not that a particular negative magnitude is stable.
3. The new arm is **one** source-model seed at 256 episodes/cell against three
   pooled seeds at 384 for the published arms.
4. `phase_feat` for the new arm joins delta_feat from the **published**
   seed-0/1/2 ResNet-26+GN E5 records, not remeasured on the fresh model. The
   join is across source-model instances of the same architecture.
5. The matched-subset recomputation of tent@WRN is -0.939, not the -0.676 the
   manuscript quotes for the **full** grid (CIFAR-10 sev 1–5 + CIFAR-100). Both
   are reported; they are different cell populations and are not interchangeable.

Manuscript integration: `sections/experiments.tex` paragraph "The architecture
confound, removed by an added run." + Table T5; F4 caption rescoped (panel (c)
is no longer labelled exploratory, and points at T5); `sections/discussion.tex`
"Self-amplifying objectives violate persistent alignment";
`appendix/experimental_details.tex` E2 paragraph "Architecture-matched entropy
run" (states the gate audit).

---

## R1.7-appendix Original protocol notes

The clean CIFAR-10 split is served from `experiments/data/cifar10_np/*.npy`
because the cached `cifar-10-python.tar.gz` in this checkout is a 1 MB truncated
stub. The substitution is loader-route only, and its integrity is asserted: the
local clean test labels must equal each of the five 10,000-image label blocks of
`CIFAR-10-C/labels.npy`, and both splits must be exactly class-balanced. They
are.

Budget, measured by `f_scope_bench.py` on the local RTX 3080: 16.4 ms/train step
-> ~0.5 GPU-h source training (9.1 s/epoch steady state with 8 loader workers);
280 ms/episode -> ~0.9 GPU-h adaptation plus alignment measurement; ~2.5 GPU-h
total, inside the 6 GPU-h ceiling.

Outputs land in `experiments/results/is_fresh/e2_gn/`. The correlation analysis
over them is a separate pass reusing `f8_e2_crossfit.py`'s cross-fit
(`f16_e2_gn_analysis.py`); measured budget was 2.6 GPU-h.

---

## R1.8 Auditability archive (finding #3)

`make_release_zip.py` -> **`paper/is/release_archive.zip`**: 458 hashed payload
files (463 zip entries: the 458 payload files plus the 5 archive-root metadata
files, which are the manifest *about* the archive and not entries inside it),
205.0 MB uncompressed, **39.5 MB zipped**, repository-relative paths so every
script runs unchanged after extraction.

The **458 / 205.0 MB** pair supersedes the round-3 count of 455 / 204.8 MB:
this round's rebuild adds exactly three files, the round-3 analysis artefacts
`f20_e2gn_loco_sensitivity.py`, `f20_e2gn_loco_sensitivity.json` and the run
log `f20.log`. Round 3 in turn added seven files to round 2's 448
(`f17_e4_alignment_only.{py,json}`, `f18_integer_boundary_check.{py,json}`,
`fig_f8_domains.py`, `f17.log`, `f18.log`). Any document still carrying 455 or
448, or the older stale triple 399 / 188.1 MB / 36.5 MB, is describing an
earlier build of the same archive, not a different archive.

**The zipped byte size and the archive's SHA-256 are deliberately not restated
here.** This file ships *inside* the archive, so it cannot state the hash of
the object that contains it without being stale by construction. Those two
volatile numbers live in `paper/is/review_r4_manifest.md` §2, which ships
beside the archive rather than inside it, and they are measured on the finished
zip. Contents: the `is_fresh` suite plus
every original pipeline module it imports and every original runner the records
came from; the raw record sets `results/{e2,e3,e4,e5}` and all of
`results/is_fresh`; the manuscript sources including `references.bib` and the
figure PDFs; `MANIFEST.json` (per-file SHA-256), `SEEDS.md`, `COMMANDS.md`
(every command in dependency order), `ENVIRONMENT.txt` (`pip freeze`) and
`INDEX.md` (claim -> script -> output, and finding -> artefact). `COMMANDS.md`
was incomplete through round 4 and is now complete *and* checked by the build
itself; see §R4.1.

Excluded on purpose and stated as such: model checkpoints and corrupted-image
tensors (large, reconstructible from the public datasets plus the shipped
training/preparation scripts).

Verified by round trip, automatically, on every build:

1. extract to a scratch directory and re-hash every file against
   `MANIFEST.json` — 458/458 match;
2. run `f7_curve_match.py --n-rep 4000 --seeds 20260806` **inside the extracted
   tree** (code-only reproduction; passes its own gate);
3. run `f11_e4_cluster_ci.py --b 200 --boot-seeds 20260806` inside the extracted
   tree (data-dependent; asserts the shipped raw records reproduce the published
   E4 intervals). Both exit 0.

---

## R1.9 E3 multi-seeding: scoped, NOT launched (finding #13)

Measured on the local RTX 3080 (`f_scope_bench.py`): ResNet-50 entropy step at
batch 64, 224 px, **117.9 ms**. The E3 protocol uses 5000-image subsets
(78 batches), 10 steps for `fixed`, K = 3 x 10 for `alta`.

| unit | cost |
|---|---|
| one (method, severity) `fixed` run | 1.5 min |
| one (method, severity) `alta` run | 4.6 min |
| defocus-blur family, one seed (3 methods x {fixed, alta} x severities {3,5}) | **0.61 GPU-h** |
| full 15-corruption summary row, one seed | **9.2 GPU-h** |
| both, for the two additional seeds requested | **~19.6 GPU-h** |

**Decision: not launched.** 19.6 GPU-h exceeds the ~8 GPU-h ceiling by 2.5x.
Two further blockers, reported so the estimate is not mistaken for the whole
cost:

* **no ImageNet-C locally.** E3 ran on a remote machine; `prepare_data.py`
  streams per-corruption tars from Zenodo (the blur group alone is several GB)
  and needs a class-structured ImageNet validation directory for the EATA Fisher
  estimate. Neither is present, and download time is not a GPU-hour cost that
  can be bounded here.
* any local ImageNet or ResNet-50 assets that might exist sit under directories
  this work stream is not permitted to read.

The defocus-blur family **alone** (0.61 GPU-h/seed, ~1.2 GPU-h for two extra
seeds) would fit comfortably once the data is staged; that is the recommended
next increment, not the full summary row.

---

## R1.10 Files added in this round

| file | role |
|---|---|
| `ttt/is_fresh/f10_oracle_grid.py` | three gain quantities on one simulation (finding #8) |
| `ttt/is_fresh/f11_e4_cluster_ci.py` | document-clustered E4 intervals (#11) |
| `ttt/is_fresh/f12_e4_proxy_loo.py` | leave-one-domain-out proxy validation (#12) |
| `ttt/is_fresh/f13_compute_matched.py` | compute-matched ALTA comparator (#5) |
| `ttt/is_fresh/f14_deltafeat_check.py` | delta_feat validation vs severity and labelled risk (#9) |
| `ttt/is_fresh/f15_e2_entropy_gn.py` | entropy on ResNet-26+GN (#9, fix-forward) |
| `ttt/is_fresh/f16_e2_gn_analysis.py` | cross-fit correlation over the e2_gn records + matched-cell reference arms (#9) |
| `ttt/is_fresh/f8b_e2_crossfit_det.py` | cross-fit for tent / pl (#4) |
| `ttt/is_fresh/fig_f2_phase.py` | three-panel Figure 2 |
| `ttt/is_fresh/fig_f3_alta.py` | five-seed measured-oracle Figure 3 |
| `ttt/is_fresh/fig_f4_e2.py` | cross-fit-annotated Figure 4 |
| `ttt/is_fresh/make_release_zip.py` | auditability archive + round-trip verification (#3) |
| `ttt/is_fresh/f_scope_bench.py` | wall-clock scoping for #9 and #13 (produces no results) |
| `results/is_fresh/f10_oracle_grid_{seed*,summary}.json` | Figure 2 data |
| `results/is_fresh/f11_e4_cluster_ci.json` | corrected E4 intervals |
| `results/is_fresh/f12_e4_proxy_loo.json` | proxy validation |
| `results/is_fresh/f13_compute_matched_{seed*,summary}.json` | compute-matched comparator |
| `results/is_fresh/f14_deltafeat_check.json` | delta_feat validation |
| `results/is_fresh/f8b_e2_crossfit_det_*.json` | deterministic cross-fit |
| `results/is_fresh/e2_gn/` | architecture-controlled entropy run (complete: 45 cells, 11,520 episodes, gate audit in `f15_source_gate.json`) |
| `results/is_fresh/f16_e2_gn_*.json` | matched-cell cross-fit correlations for every E2 arm (per-seed rows + summary) |
| `paper/is/release_archive.zip` | auditability archive |

---

# Round 2 — external review response (computation & figures)

Scope: the computation/figure half of external review round 2
(`paper/is/REVIEW_ROUNDS.md`, Round 2). New code lives in
`experiments/ttt/is_fresh/` as `f17_e4_alignment_only.py`,
`f18_integer_boundary_check.py` and `fig_f8_domains.py`. Both analyses run over
**records that already exist** — the original E4/E5 GPT-2 records for f17, the
round-1 `f10` grid for f18 — so no simulation and no GPU run was launched in
this round. Every new resampling procedure uses the fresh bootstrap seeds
**20260811–15** (round 1 used 20260806–10; the original pipeline used
0/1/2/42/43/100+/999+, and none of those is reused). `f18` draws no random
numbers at all.

Same framing as round 1: **fix-forward**, and where the corrected measurement
disagrees with the published presentation, the corrected one is reported.

---

## R2.1 Figure 8 promoted the full statistic after the LOO result had retired it (round-2 fresh finding #4)

The round-1 leave-one-domain-out analysis (R1.5, `f12`) concluded that what
transfers across GPT-2 domains is the **alignment** factor
`alpha|alpha|/sigma^2` alone and that the representation-distance factor
`delta_v2` adds no measurable increment — but Figure 8 and the introduction
still plotted and advertised the full statistic
`alpha|alpha| delta_v2 / sigma^2` at rho = 0.58–0.90. The reviewer is right that
the figure advertises the pre-revision interpretation.

`f17_e4_alignment_only.py` measures the alignment-only statistic with **exactly
f11's protocol** so the two series are comparable: the original
`results/e4/*_ln_s{0,1,2}.json` records, the same realized gain
(`frozen_cont_ce - alta.cont_ce` at the ALTA stop), document-clustered
percentile bootstrap over **500 document clusters with the three adaptation
seeds nested**, B = 2000, endpoints averaged over five bootstrap seeds
(20260811–15). Three statistics are carried through the same resamples:
alignment-only, the paper's full statistic, and `delta_v2` on its own.

| domain | **alignment only** `a\|a\|/s^2` | full statistic `a\|a\| d_v2/s^2` (published) | `delta_v2` alone | paired diff (align − full) |
|---|---|---|---|---|
| code | **0.679** [0.625, 0.727] | 0.582 [0.517, 0.640] | −0.386 [−0.461, −0.308] | **[+0.073, +0.123]** |
| legal | **0.918** [0.900, 0.931] | 0.905 [0.885, 0.920] | −0.020 [−0.106, +0.068] | **[+0.007, +0.020]** |
| PubMed | **0.875** [0.845, 0.899] | 0.868 [0.838, 0.892] | +0.044 [−0.046, +0.133] | [−0.003, +0.018] |
| WikiText | **0.881** [0.858, 0.898] | 0.834 [0.802, 0.861] | +0.120 [+0.032, +0.207] | **[+0.031, +0.063]** |

All values are the pooled-row Spearman (the manuscript's estimand: 1500 rows =
500 documents x 3 seeds) with document-clustered intervals. On the
seed-averaged estimand (500 independent units) the picture is identical:
alignment-only 0.703 / 0.942 / 0.898 / 0.913 against 0.606 / 0.928 / 0.890 /
0.862, paired differences [+0.070, +0.123], [+0.007, +0.021], [−0.003, +0.019],
[+0.035, +0.069].

The **paired** difference is the load-bearing quantity: the two statistics are
correlated inside every resample because they are computed on the same drawn
documents, so comparing their marginal intervals would understate the evidence.

**Result — stronger than "indistinguishable".** Alignment-only matches or
exceeds the full statistic in **4 of 4** domains; the paired interval excludes
zero **on the alignment side in 3 of 4** domains and contains zero in PubMed;
it favours the full statistic in **0 of 4**. Dropping `delta_v2` from the
plotted statistic costs nothing anywhere and gains between +0.007 and +0.123
in three domains. The shift factor on its own carries no consistent
within-domain signal (−0.386 to +0.120, mean −0.060), and in code its
correlation with the gain is strongly *negative* — the full statistic's 0.582
there is the alignment factor working against a mis-signed shift term, which is
exactly why removing it helps most in that domain.

Reproduction checks (asserted inside the script, so a silent protocol drift
cannot pass): the full statistic's pooled-row rho reproduces the four published
values to **4.2e-4**; its document-clustered interval reproduces f11's to
**1.1e-3** in the worst endpoint despite the fresh bootstrap seeds; and the
seed-averaged alignment-only correlations reproduce f12's `alpha_only` column
**exactly** (gap 0.0).

**Figure 8 regenerated** — `fig_f8_domains.py` ->
`paper/is/paper/figures/F8_domains.pdf` (six panels, replaces the four-panel
original):

* (a)–(d) one scatter per domain, x = the **alignment-only** statistic (symlog,
  so the negative-alignment documents are visible and are the ones that do not
  gain), y = realized CE gain; each panel annotates the alignment-only rho with
  its clustered interval and, directly underneath in grey, the full statistic's
  rho, so both series are on the figure;
* (e) per-domain forest of all three statistics with document-clustered 95%
  intervals — the alignment-only / full / `delta_v2`-only comparison the review
  asked the figure to make;
* (f) the paired difference rho(alignment) − rho(full) per domain, zero marked,
  point and interval drawn in black where the interval excludes zero and grey
  where it does not (PubMed).

> **SUPERSEDED IN ROUND 16 — interval endpoints only** (external review round
> 15, substantive finding 1). Everything above is the round-2 record and is
> kept as written. *"endpoints averaged over five bootstrap seeds"* is what
> `f17` did; every other document called the result a single
> document-clustered percentile interval, and a mean of five percentile
> endpoints is not a percentile.
> `f30_e4_alignment_pooled.py` replays f17's exact five streams (per-stream
> endpoint gap asserted at `0.0`), **pools the 5 × 2000 = 10,000 draws — the
> paired difference as paired draws — and reads one 2.5/97.5 percentile pair
> off each pooled distribution.** Point estimates are asserted unchanged at
> `0.0` and all five verdict counts are asserted unchanged, so the "Result"
> paragraph above stands verbatim.
>
> Current endpoints, from `f30_e4_alignment_pooled.json`:
>
> | domain | **alignment only** | full statistic | `delta_v2` alone | paired diff (align − full) |
> |---|---|---|---|---|
> | code | **0.679** [0.625, 0.727] | 0.582 [0.517, 0.640] | −0.386 [−0.461, −0.307] | **[+0.073, +0.122]** |
> | legal | **0.918** [0.900, 0.931] | 0.905 [0.885, 0.920] | −0.020 [−0.107, +0.068] | **[+0.007, +0.020]** |
> | PubMed | **0.875** [0.845, 0.899] | 0.868 [0.838, 0.892] | +0.044 [−0.046, +0.133] | [−0.002, +0.017] |
> | WikiText | **0.881** [0.858, 0.898] | 0.834 [0.802, 0.861] | +0.120 [+0.032, +0.207] | **[+0.031, +0.063]** |
>
> Seed-averaged estimand: alignment-only 0.703 / 0.942 / 0.898 / 0.913 against
> 0.606 / 0.928 / 0.890 / 0.862; paired differences [+0.070, +0.123],
> [+0.007, +0.021], [−0.003, +0.019], [+0.035, +0.069].
>
> Four printed endpoints move against the round-2 table: code paired-diff high
> +0.123 → +0.122, code `delta_v2` high −0.308 → −0.307, legal `delta_v2` low
> −0.106 → −0.107, and "gains between +0.007 and +0.123" → "+0.007 and
> +0.122". The largest change to any endpoint is **0.0011**.
>
> **The PubMed paired-difference row was independently wrong.** The round-2
> table and Section 7.4 both printed `[−0.003, +0.018]`. That matched **no**
> record: `f17` said `[−0.002, +0.017]` pooled-row and `[−0.003, +0.019]`
> seed-averaged, and so does `f30`. This error is unrelated to endpoint
> averaging and predates it; it survived every green reconciliation run
> because **no E4 interval endpoint was bound**. Section 7.4 now prints
> `[−0.002, +0.017]` and all four paired-difference intervals are bound.
>
> Reproduction checks now assert against `f29` rather than `f11`: the full
> statistic's pooled-row rho reproduces the four published values to
> **4.2e-4**, its clustered interval reproduces `f29`'s to **1.3e-3** in the
> worst endpoint despite the different bootstrap seeds, and the seed-averaged
> alignment-only correlations reproduce `f12`'s `alpha_only` column **exactly**
> (gap 0.0). `f17_e4_alignment_only.json` is retained unmodified as the audit
> trail.

Caption text handed to the manuscript agent (numbers verified against
`f17_e4_alignment_only.json`):

> GPT-2 domain shift (E4): the **alignment** factor is what predicts the
> realized gain. (a)–(d) per-document alignment statistic
> `alpha|alpha|/sigma^2` against the continuation-CE gain at the ALTA stop, one
> panel per domain; Spearman rho with a document-clustered 95% interval (500
> documents, three adaptation seeds nested, B = 2000). (e) the same correlation
> for three statistics: alignment only, the full phase statistic
> `alpha|alpha| delta_v2/sigma^2` we set out to validate, and the shift proxy
> `delta_v2` alone. (f) the paired difference rho(alignment) − rho(full),
> computed inside each resample so both statistics see the same documents;
> intervals excluding zero are drawn in black. Alignment alone attains
> rho = 0.68–0.92 and matches or exceeds the full statistic in all four
> domains, while `delta_v2` alone carries no consistent signal
> (−0.39 to +0.12). The representation-distance factor is not what carries the
> correlation, and the figure reports the simpler statistic that survives.

---

## R2.2 The integer one-step criterion, measured (round-2 fresh finding #1)

The reviewer's critical finding is that the exact "if and only if" is a
statement about the **continuous interpolation** of the risk curve to real `t`,
while the protocol executes only integer SGD steps: condition (P) is the
negative-derivative-at-zero condition and guarantees a beneficial *fractional*
minimiser, not a beneficial executable step. The proposed replacement is the
exact one-step condition the paper already displays in Figure 2,
`alpha^2 delta^2 (2 - eta alpha^2) > eta sigma^2`, plus the claim that — given
the proved unimodality — an integer stopping time beats freezing **iff the
first integer step does**.

`f18_integer_boundary_check.py` tests that claim against measurement.
Everything it needs is already in the round-1 `f10` records, so it is **pure
re-analysis: no simulation, no RNG, five existing seeds (20260801–05), the same
25 x 25 grid (eta = 0.05, sigma = 1, T = 400, 20,000 replicates per cell)**.

**(A) The two boundaries are the same curve.** `f10` already emits both
`boundary_onestep_exact` (the closed-form `G(1) = 0` locus) and
`boundary_oracle_exact` (the locus where `min_{t=0..T} Exc(t) = Exc(0)`, found
by bisection on the exact risk curve over integer `t`, never using the one-step
formula). They agree to **1.3e-8 relative** at every one of the 25 grid alphas.
Recomputed independently on 40 alphas at step sizes `f10` never ran —
eta in {0.01, 0.02, 0.05, 0.1, 0.2, 0.4} — the agreement is **< 1e-8 relative
everywhere**. The integer criterion is therefore not an artefact of eta = 0.05.

**(B) The measured labels coincide.** For every cell of every seed, two labels
are formed from measured quantities only: `onestep_positive`
(`delta^2 - E_B[u_1^2] > 0`) and `oracle_adapts`
(`argmin_t E_B[u_t^2] > 0` with gain above the 1e-9 relative floor).

| measurement | mean over 5 seeds | range |
|---|---|---|
| cells where the two labels agree | **617.4 / 625 (98.8%)** | 615–621 |
| … restricted to cells whose one-step gain is resolved at 3 Monte-Carlo SE | **100.0%** | 100% in all 5 seeds |
| resolved cells per seed | 545.8 | 543–551 |
| disagreements per seed | 7.6 | 4–10 |
| largest \|z\| among the disagreeing cells | 1.42 | 0.71–2.16 |

Every disagreement in all five seeds is of one kind — the measured oracle
adapts while the measured one-step gain is (unresolvedly) negative — which is
the Monte-Carlo optimism of an argmin over 401 noisy curve values that `f10`
already quantifies, not a violation of the criterion. **No disagreement is
resolved at 3 SE in any seed.**

**(C) Fitted threshold against each curve.** The exact one-step boundary is not
a constant in the plain phase statistic — it is `eta/(2 - eta alpha^2)`,
running from 0.025000 at alpha -> 0 to 0.025641 at alpha = 1, i.e. at most
**2.56% above** the flow boundary eta/2 = 0.025. The threshold fit (fit on the
even-indexed cells, scored on the disjoint odd cells, labels from the measured
one-step gain) is therefore reported twice:

| ratio | mean over 5 seeds | range |
|---|---|---|
| fitted threshold / **flow** boundary (eta/2) | **0.968** | 0.785–1.093 |
| fitted threshold on the exact statistic `a^2 d^2 (2 - eta a^2)` / **exact** boundary (eta) | **0.955** | 0.768–1.072 |

Held-out sign accuracy is 0.979 (phase statistic) and 0.979 (exact statistic),
both 0.999 on the 3-SE-resolved cells; the two *fixed, unfitted* criteria score
0.983 and 0.983 on the measured signs. **The 20,000-replicate grid cannot
separate the two boundaries**, and this is stated rather than glossed: at
eta = 0.05 they are 1.3% apart in `delta/sigma`, far inside the width of one
grid cell (the log-spaced ratio axis steps by 23.5% per cell).

**(D) The sliver.** The region where (P) fires but the integer criterion does
not is where "TTT helps iff (P)" is false. On `f10`'s grid it contains
**2 of 625 cells** (and the one-step and flow criteria disagree on 1 of 625).
Both sliver cells sit on the boundary: their closed-form one-step gains are
−2.1e-6 and −1.5e-5, against Monte-Carlo standard errors of ~1.6e-3 and
~2.9e-4, so the largest \|z\| observed at them across the five seeds is 2.6 and
**neither is resolved**. The honest statement is that the sliver is real,
geometrically located, and **below the resolution of this grid** — which is a
statement about eta = 0.05, not about the criterion:

| eta | max relative width of the sliver in `delta/sigma` |
|---|---|
| 0.01 | 0.25% |
| 0.05 | 1.28% |
| 0.1 | 2.64% |
| 0.2 | 5.61% |
| 0.4 | 12.95% |

The band is widest as alpha -> 0 and closes exactly at alpha = 1 for every eta.
It shrinks like the step size, which is why the flow limit is a good
approximation for small eta and a false "iff" for the step sizes real TTT uses.

**(E) The counterexample reproduces with our own closed form.** The reviewer's
instance (eta = 0.2, alpha = 0.4, sigma = 1, delta = 0.78), evaluated with the
pipeline's own `run_e1.excess_risk`:

* condition (P): `2 lambda a^2 (d^2 - nu) = 0.035509 > 0.033600 = (1-a^2) eta^2 sigma^2` — **holds**;
* one-step: `a^2 d^2 (2 - eta a^2) = 0.191573 < 0.200000 = eta sigma^2` — **fails**;
* continuous minimiser `t* = 0.2545` with gain **+2.41e-4 > 0**;
* every executable step is harmful: gains at t = 1..5 are −1.69e-3, −9.63e-3,
  −2.26e-2, −3.97e-2, −6.00e-2, and the best gain over all integer t >= 1 is
  **−1.69e-3 < 0** (t = 0 gives exactly 0 because `u_0` is deterministic).

The script asserts all five of these, so the counterexample is certified against
the repository's code rather than against a re-derivation.

**What this gives the theory side.** The integer-step theorem it needs is not
merely consistent with the data — the equality of the two independently
computed boundaries (A) and the 100%-on-resolved-cells label agreement (B) are
a direct measured verification of "an integer stopping time helps iff the first
step helps", on 625 cells x 5 seeds, at the eta the paper simulates. The
manuscript's *fitted* boundary is unchanged by the correction (C): the ratio
moves from 0.968 (flow) to 0.955 (exact), both well inside the across-seed
range, so no reported number has to move — only the claim attached to it.

---

## R2.3 The review package, so finding #3 cannot recur (round-2 finding #3)

Round 2's "not independently auditable" verdict was about the package the
reviewer received (22 files, no archive), not about whether the archive exists.
`paper/is/review_r3_manifest.md` is the one-page index that ships **inside the
round-3 zip, next to the archive itself**. It states, from the shipped files
rather than from memory:

* `release_archive.zip` = **453 zip entries = 448 hashed payload files + 5
  archive-root metadata files**, **204.8 MB uncompressed -> 39.51 MB zipped**,
  SHA-256 `d28ea4ee…46b45f4b`, build stamp 2026-08-03T09:28:12Z;
* the per-directory file/byte table, the deliberate exclusions (checkpoints,
  corruption tensors) and the scripts that regenerate them;
* the verification transcript actually executed on the shipped zip —
  `manifest round-trip OK (448 files, 453 zip entries)`, plus the two
  reproduction checks run *inside the extracted tree* (`f7` code-only,
  `f11` against the shipped raw records), both exit 0;
* a three-command recipe for the reviewer to repeat both checks and re-hash
  every file;
* the projected round-3 package size, **≈ 41–42 MB against the 80 MB budget**
  (39.51 MB archive + ≈ 2 MB of sources; the archive is already compressed, so
  the outer zip adds nothing to it).

It also reconciles the conflicting statistics the reviewer caught: the
**448 / 204.8 MB / 39.5 MB** triple is canonical; the **399 / 188.1 MB /
36.5 MB** triple that §R1.8 used to carry was a stale pre-rebuild count that
was never updated after the archive was rebuilt with the round-1 fix-forward
artefacts. §R1.8 has since been corrected in place (round 2), so both
documentary accounts now agree.

**The archive must be rebuilt after the last manuscript edit**, because it
ships `paper/is/paper/` alongside the code and records; the currently shipped
build predates this round's `f17`/`f18` artefacts and the regenerated
`F8_domains.pdf`. One command, which builds and then verifies:
`cd experiments/ttt/is_fresh && python make_release_zip.py`.

---

## R2.4 Files added in this round

| file | role |
|---|---|
| `ttt/is_fresh/f17_e4_alignment_only.py` | alignment-only E4 correlations with document-clustered and paired intervals (round-2 finding #4) |
| `ttt/is_fresh/f18_integer_boundary_check.py` | measured verification of the integer one-step criterion; re-analysis of the f10 grid (round-2 fresh finding #1) |
| `ttt/is_fresh/fig_f8_domains.py` | six-panel Figure 8 built on the alignment-only statistic |
| `results/is_fresh/f17_e4_alignment_only.json` | per-domain rho + clustered/paired intervals for the three statistics |
| `results/is_fresh/f18_integer_boundary_check.json` | boundary equality, measured label agreement, threshold ratios, sliver geometry, counterexample audit |
| `results/is_fresh/f17.log`, `results/is_fresh/f18.log` | run transcripts |
| `paper/is/paper/figures/F8_domains.pdf` | regenerated Figure 8 |
| `paper/is/review_r3_manifest.md` | one-page index of the round-3 review package and of `release_archive.zip` |


---

# Round 3 — external review response (computation)

Scope: the computation half of external review round 3
(`paper/is/REVIEW_ROUNDS.md`, Round 3). Round 3's findings were overwhelmingly
about the theory chain and about presentation; the single **computational** item
was the leave-one-corruption-out sensitivity for the E2 architecture control —
the last cheap piece of round-1 finding #9, which rounds 1 and 2 had scoped but
not run, and which the round-3 manuscript still carried as a stated limit
("no leave-one-corruption-out sensitivity analysis ... has been performed").
New code: `experiments/ttt/is_fresh/f20_e2gn_loco_sensitivity.py`. It re-analyses
**records that already exist** — the `e2_gn/` records from `f15` and the original
`results/e2/` episode records — so no simulation and no GPU run was launched in
this round. Its bootstrap uses the fresh seed **20260817** (rounds 1 and 2 used
20260806–10 and 20260811–15; the original pipeline used 0/1/2/42/43/100+/999+,
and none is reused).

Same framing as rounds 1 and 2: **fix-forward**, and where the corrected
measurement disagrees with the published presentation, the corrected one is
reported.

---

## R3.1 Leave-one-corruption-out sensitivity for the E2 architecture control (round-1 finding #9, last piece) — DONE

**The question.** `f16`'s four headline correlations come with
corruption-clustered bootstrap intervals. Those bound *sampling variation across
corruptions*; they do not answer the deletion question, because a bootstrap
keeps any given cluster in a large majority of its resamples and can therefore
stay tight while one influential cluster carries the correlation. The reviewer
asked whether a single corruption family drives the reported signs. That needs
a deletion diagnostic, and `f16` stored only aggregate rho plus clustered CIs,
so the per-cell statistics had to be recomputed from the raw per-episode
records.

**Protocol.** Identical to `f8`/`f16` and importing their code, not copying it:
within each cell a fresh-seed permutation splits episodes 50/50 into a
commissioning share (which defines the phase statistic) and a disjoint
evaluation share (which defines the realized gain), at the same five split seeds
20260801–05. Cell population is `f16`'s matched subset — CIFAR-10-C, 15
corruptions x severities {1,3,5}, 45 cells, so no two arms are compared across
different grids. Then, for each of the 15 corruptions in turn, that corruption's
3 cells are deleted and Spearman is recomputed on the remaining 42; each fold
value is the mean over the five split seeds. Inside each fold a
corruption-clustered bootstrap over the **14 surviving** clusters (1000
resamples, seed 20260817) gives an interval. The same bootstrap stream is also
run on the undeleted 15 clusters, so "a fold interval contains zero" can be
compared against a like-for-like full-sample interval instead of against `f16`'s
five-split-seed average.

### Result (`f20_e2gn_loco_sensitivity.py` -> `f20_e2gn_loco_sensitivity.json`)

| arm | full rho | full 15-cluster CI (same stream) | LOCO min | LOCO median | LOCO max | max abs deviation | any fold flips sign | fold-CI envelope (worst lo / worst hi) |
|---|---|---|---|---|---|---|---|---|
| entropy (tent) @ ResNet-26+GN, loss proxy | -0.902 | [-0.950, -0.715] | -0.912 (frost) | -0.901 | -0.885 (gaussian_noise) | 0.017 | no | -0.963 / -0.653 |
| entropy (tent) @ WRN-28-10+BN, loss proxy | -0.939 | [-0.965, -0.889] | -0.947 (defocus_blur) | -0.938 | -0.933 (impulse_noise) | 0.008 | no | -0.969 / -0.879 |
| ttt_rot @ ResNet-26+GN, loss proxy | +0.151 | [-0.326, +0.436] | +0.063 (gaussian_noise) | +0.154 | +0.252 (glass_blur) | 0.102 | no | -0.423 / +0.518 |
| ttt_mask @ ResNet-26+GN, loss proxy | +0.253 | [-0.208, +0.589] | +0.153 (gaussian_noise) | +0.265 | +0.311 (zoom_blur) | 0.100 | no | -0.340 / +0.626 |
| entropy (tent) @ ResNet-26+GN, feat proxy | +0.092 | [-0.248, +0.321] | +0.055 (brightness) | +0.086 | +0.186 (pixelate) | 0.094 | no | -0.328 / +0.371 |
| ttt_rot @ ResNet-26+GN, feat proxy | +0.418 | [-0.016, +0.638] | +0.328 (gaussian_noise) | +0.425 | +0.466 (fog) | 0.090 | no | -0.118 / +0.671 |
| ttt_mask @ ResNet-26+GN, feat proxy | +0.610 | [+0.291, +0.819] | +0.554 (pixelate) | +0.610 | +0.686 (frost) | 0.076 | no | +0.200 / +0.853 |
| pseudo-label @ WRN-28-10+BN, loss proxy | -0.905 | [-0.949, -0.858] | -0.914 (defocus_blur) | -0.903 | -0.897 (brightness) | 0.009 | no | -0.956 / -0.839 |

**No sign is corruption-driven.** Across all 8 arms and all 15 folds, not one
fold changes the sign of its arm's correlation. The two entropy arms — the ones
the architecture-control argument rests on — are almost unmoved by deletion:
the largest single-fold shift is **0.017** (entropy on ResNet-26+GN, deleting
frost) and **0.008** (entropy on WRN-28-10+BN), and every fold's 14-cluster
interval stays strictly negative (worst upper bounds -0.653 and -0.879). The
stochastic arms are more sensitive in relative terms, with Gaussian noise the
most influential single cluster for both — deleting it takes ttt_rot from +0.151
to +0.063 and ttt_mask from +0.253 to +0.153 under the loss proxy — but neither
crosses zero, and the feature-proxy versions move less (+0.418 -> [+0.328,
+0.466], +0.610 -> [+0.554, +0.686]).

**Two qualifications, stated rather than absorbed.**

1. The fold intervals of the two *loss-proxy* stochastic arms do contain zero.
   So does their **full 15-cluster interval on the same bootstrap stream**
   ([-0.326, +0.436] and [-0.208, +0.589]). What leaves those two unresolved is
   the smallness of the correlations, not the deletion; the verdict field
   `headline_arms_where_deletion_ALONE_loses_the_sign` is empty. `f16` already
   reported both as intervals containing zero.
2. `ttt_rot` under the feature proxy is borderline at full sample too: `f16`'s
   five-split-seed averaged interval is [+0.067, +0.677], excluding zero by a
   small margin, while this script's single-split-seed, fresh-stream interval
   over the same 15 clusters is [-0.016, +0.638], which does not. That is a
   bootstrap-stream and split-seed difference at a genuinely borderline
   quantity, not a deletion effect, and we report the weaker of the two
   readings. `ttt_mask` under the feature proxy is not borderline: every fold
   interval is strictly positive (worst lower bound +0.200).

**What this licenses, and no more.** The diagnostic removes one competing
explanation for the objective-versus-architecture dissociation — that a single
corruption family carries it. It does not make the small positive correlations
larger, and it does not upgrade the architecture control to a causal claim: the
arms still differ in source-model seed, checkpoint, episodes per cell and proxy
provenance, and the balanced same-checkpoint/same-episode/same-proxy comparison
that would close that gap remains unrun (it needs the mirror-control run scoped
at 12–20 GPU-h in `REVISION_NOTES_R3.md`).

**Manuscript effect.** `sections/experiments.tex` carried this as the fourth
limit on the architecture-control paragraph, worded as "no leave-one-corruption-out
sensitivity analysis over the 15 corruption clusters has been performed". That
item is **replaced by the result above**; the sentence in the same paragraph
that listed the sensitivity alongside the balanced comparison as "neither has
been run" now scopes the negative to the balanced comparison alone.
`sections/discussion.tex` carried the same "no leave-one-corruption-out
sensitivity was run" clause and is corrected in the same direction.

---

## R3.2 Files added in this round

| file | role |
|---|---|
| `ttt/is_fresh/f20_e2gn_loco_sensitivity.py` | leave-one-corruption-out deletion diagnostic over the 15 corruption clusters for the four headline E2 architecture-control correlations (round-1 finding #9, last piece) |
| `results/is_fresh/f20_e2gn_loco_sensitivity.json` | per-arm full rho, 15 fold values with 14-cluster intervals, min/median/max, sign-flip verdict |
| `results/is_fresh/f20.log` | run transcript |
| `paper/is/REVISION_NOTES_R3.md` | round-3 finding-to-action map |
| `paper/is/review_r4_manifest.md` | one-page index of the round-4 review package and of `release_archive.zip` |

---

# Round 4 — external review response (no new computation)

Round 4 returned **minor revision**. Its five fresh findings are all statement-
and wording-level: Proposition 13's $K=2$ constant, the infinite-horizon oracle
endpoint in Theorem 9, the conditional PL–ALTA corollary's hypotheses, the
Figure 4 caption, and the $1/K$ description of the ALTA additive term. **No
experiment, analysis or figure changed in this round**, and no number in this
file is superseded by it. What changed is the manuscript text and the archive's
own indexing, recorded below so the archive's contents are not silently
different from its description.

## R4.1 Two defects we found ourselves in the archive's indexing

Neither is a result defect; both are auditability defects, which is exactly the
class round 1's finding #3 was about.

**(a) `COMMANDS.md` was incomplete.** It is generated by
`make_release_zip.py:commands_md()` and claims "the exact command line for every
script, in dependency order". It listed 21 of the 25 analysis and figure
scripts in
`experiments/ttt/is_fresh`. The four omissions were exactly the artefacts added
after the first build: `f17_e4_alignment_only.py` and `fig_f8_domains.py`
(round 2), `f18_integer_boundary_check.py` (round 2) and
`f20_e2gn_loco_sensitivity.py` (round 3). A reviewer following `COMMANDS.md`
could therefore not reproduce Figure 8, the integer-criterion check, or the
leave-one-corruption-out sensitivity, even though all three scripts and all
three JSONs shipped. `COMMANDS.md` now lists **every** script, with its
dependency noted, and states which two files deliberately have no command line
(`common.py`, an imported module; `make_release_zip.py`, the builder).

**(b) The claim is now enforced by the build, not promised by it.** `verify()`
reads `COMMANDS.md` out of the *extracted* archive and asserts that every `.py`
in `experiments/ttt/is_fresh` is mentioned; a missing one fails the build with a
non-zero exit. The gate reports `COMMANDS.md accounts for all 27 is_fresh
scripts` (27 = the 25 analysis and figure scripts, plus `common.py` and
`make_release_zip.py`, both of which the file names explicitly). This is the
same discipline
the manifest round-trip already applies to file hashes: an archive that cannot
be reproduced from its own documentation should not be declared good.

`SEEDS.md` had the parallel omission and is corrected in the same commit: it now
carries rows for `f17` (bootstrap seeds 20260811–15), `f18` (no seeds of its
own; re-reads the f10 replicates) and `f20` (split seeds 20260801–05, deletion
bootstrap 20260817), states that the four figure scripts and `f_scope_bench.py`
draw no random numbers, and records that the bootstrap streams are allocated in
disjoint blocks (20260806–10 for `f11`/`f12`, 20260811–15 for `f17`, 20260817
for `f20`). `INDEX.md` gains the three missing claim→script→output rows and
three finding→artefact rows for the round-2 and round-3 artefacts.

## R4.2 Files added in this round

| file | role |
|---|---|
| `paper/is/REVISION_NOTES_R4.md` | round-4 finding-to-action map |
| `paper/is/review_r5_manifest.md` | one-page index of the round-5 review package and of `release_archive.zip` |

No script, record or figure was added, changed or deleted. The archive's payload
count is unchanged at 458; what changed inside it is the manuscript sources, the
regenerated `main.pdf`, and the three generated root files `COMMANDS.md`,
`SEEDS.md` and `INDEX.md`.

## R6.1 Coverage of the E2 entropy sign separation, and what the excluded 42.4% look like

The manuscript reports that the sign of the per-episode entropy alignment
`alpha_ent` separates confidently-right from confidently-wrong episodes
exactly. That statement is conditional on a selection — the confidence
threshold 0.7 — and the review asked for the coverage to be foregrounded and
the excluded episodes characterised. `f21_e2_coverage.py` re-analyses the
ORIGINAL E2 calibration records (`results/e2/cifar10_tent_calib_s0.json` and
`cifar100_tent_calib_s0.json`, temp_scaled=False cells, pooled — the same
pooling the manuscript text and Figure 6 use). It simulates nothing, draws no
random numbers and uses no seed; it asserts that the retained group reproduces
the published `n = 2873` right / `1554` wrong and the 100% / 0% sign fractions
before writing anything.

**Coverage.** 4,427 of 7,680 episodes clear the threshold: **57.6%**. The
excluded group is 3,253 episodes, **42.4%**.

**What the excluded episodes are.** They are the low-confidence,
mostly-incorrect tail: frozen accuracy 21.5% against 64.9% on the retained
group, confidence in [0.0402, 0.6999] with mean 0.386.

**The alignment is not degenerate there.** `alpha_ent` still spans essentially
the whole range on the excluded group (min -0.999, max 1.000; 5–95% interval
[-0.939, 0.989]), and only 5.4% of those episodes have |alpha_ent| < 0.1, so
the sign is well defined for the overwhelming majority of them — the relation
is testable outside the selected band, not untestable.

**It degrades gracefully rather than breaking.** On the excluded group
P(alpha_ent < 0 | wrong) = 0.898 and P(alpha_ent < 0 | right) = 0.003, so
"predict wrong iff alpha_ent < 0" is right on 91.9% of them against 100.0% on
the retained group; Pearson correlation of `alpha_ent` with correctness is
0.870 there against 0.997 on the retained group and 0.956 over all 7,680
episodes. (The `rho = 0.863` the manuscript quotes is the *Spearman*
correlation over all 7,680 episodes, not a selected-subset number: it is 0.827
on the retained group and 0.708 on the excluded group. `f21` asserts the 0.863
as a second reproduction check, and the manuscript sentence now says
"all 7,680 episodes" explicitly.) The degradation is monotone in confidence
and one-sided — the
right-hand side of the separation never fails:

| confidence band | n | accuracy | P(a<0 \| wrong) | P(a<0 \| right) | sign-rule accuracy |
|---|---|---|---|---|---|
| [0.0,0.2) | 688 | 0.116 | 0.753 | 0.000 | 78.2% |
| [0.2,0.3) | 495 | 0.148 | 0.860 | 0.000 | 88.1% |
| [0.3,0.4) | 499 | 0.204 | 0.927 | 0.000 | 94.2% |
| [0.4,0.5) | 503 | 0.245 | 0.955 | 0.016 | 96.2% |
| [0.5,0.6) | 553 | 0.269 | 0.990 | 0.000 | 99.3% |
| [0.6,0.7) | 515 | 0.336 | 0.997 | 0.000 | 99.8% |
| [0.7,0.8) | 555 | 0.362 | 1.000 | 0.000 | 100.0% |
| [0.8,0.9) | 628 | 0.459 | 1.000 | 0.000 | 100.0% |
| [0.9,1.0] | 3244 | 0.735 | 1.000 | 0.000 | 100.0% |

The exactness at 100% is therefore a property of the confident band and not an
artefact of discarding an ambiguous population in which the relation reverses:
what the threshold removes is episodes where a wrong prediction sometimes has
positive alignment, and the rate at which that happens falls smoothly to zero
as confidence rises.

Output: `f21_e2_coverage.json`.

## R6.2 Figures 5–7 regenerated through the figure pipeline

Review checklist item 4 asked for Figures 5–7 either to be regenerated through
the audited pipeline or to have their exact provenance stated. They were
regenerated on 2026-08-03 by re-running the original producing scripts
unchanged:

| figure | script | input records |
|---|---|---|
| Fig. 5 `F5_batch.pdf` | `figures/scripts/fig_F5.py` | `results/e2/cifar10_tent_batch_sweep_s0_bntrain.json`, `..._s{0,1,2}.json` |
| Fig. 6 `F6_calib.pdf` | `figures/scripts/fig_F6.py` | `results/e2/cifar10_tent_calib_s0.json`, `cifar100_tent_calib_s0.json` |
| Fig. 7 `F7_imagenet.pdf` | `figures/scripts/fig_F7.py` | `results/e3/<corruption>_<method>_{fixed,alta}_s0.json` |

None of the three scripts draws a random number; all three re-derive their
annotations from the records and print them. Every printed diagnostic
reproduced the value the manuscript quotes: `rho_s(N, median sigma^2) =
-1.000` and the bn-train gains (0.00 pp at N=1 step 1, -0.52 pp at 10 steps)
for F5; `n = 2873 / 1554` with `frac alpha_ent < 0` equal to 0.000 / 1.000 and
mean fitted `T = 1.19` for F6; a mean ALTA-minus-best-fixed gap of -0.67 points
over the 90 cells for F7. The PDFs are not byte-identical to the shipped ones
because the regeneration ran under a newer matplotlib (3.10.9), which changes
text metrics; the plotted content is unchanged. This also resolved a
discrepancy we found while checking: the copy of `F7_imagenet.pdf` under
`paper/is/paper/figures/` was an older build than the one under `figures/`, and
both are now the same regenerated file.

## R7.1 A sign-dropping bug in the E2 loss proxy, and the full rerun that replaces it

**The defect.** The manuscript defines every proxy phase statistic as

```
Phi = alpha_sgn * |alpha_sgn| * delta_proxy / sigma^2_rel
```

with the **signed** alignment factor (Appendix C.1). The feature-proxy branch
implemented that correctly (`a * abs(a)`). The **loss**-proxy branch did not:
it computed `a ** 2`, discarding the sign of the alignment, in two places —
`experiments/ttt/is_fresh/f8_e2_crossfit.py:121-136` (inherited by
`f8b_e2_crossfit_det.py` and `f20_e2gn_loco_sensitivity.py`, which call into
it) and again inline in `f16_e2_gn_analysis.py:31-39`. Every loss-proxy E2
number in the round-6 manuscript was therefore an estimate of a statistic the
paper does not define. External review round 7, §3.1.

The defect had a second half. When `sigma2_rel == 0` the code silently
returned the numerator instead of flagging the ratio as undefined. That branch
was not exotic: **every** deterministic episode lands in it. All 32,640 tent,
28,800 pseudo-label and 11,520 ResNet-26+GroupNorm entropy episode records
carry `sigma2_rel == 0` exactly — the N=1 degeneracy Theorem 4 (entropy)
describes — while every ttt_rot / ttt_mask record carries `sigma2_rel > 0`.

**The fix, and why this convention.** `a ** 2` → `a * abs(a)` in both places,
now routed through a single `f8_e2_crossfit.phase_value`. For the zero-noise
case we replaced the silent fallback with a **declared definition**. Ranks are
the only thing these analyses consume, and `sigma2_rel` is *constant* across
every episode of a zero-noise arm, so dividing by it is division by a common
positive constant and leaves every Spearman correlation unchanged. The
`sigma^2 -> 0` rank limit of the manuscript's statistic is therefore its
numerator, and that is what we now define the statistic to be on such an arm:

```
Phi_0 = alpha_sgn * |alpha_sgn| * delta_proxy         (equation (C.2))
```

We considered the alignment-only statistic `alpha_sgn|alpha_sgn|` for this
role — E4/f17 already found alignment-only the stronger predictor across GPT-2
domains (0.68–0.92) — but it is *not* the limit of the quantity the manuscript
defines: it discards `delta_proxy`, which is a real factor of the statistic and
which varies across cells. `Phi_0` is the honest limit; alignment-only is
carried alongside as a secondary robustness statistic (`phase_align`), which is
what it is in E4 too.

Crucially, the convention is no longer a branch that can fire unnoticed.
`assert_noise_homogeneous` **raises** unless `sigma2_rel` is either strictly
positive for every episode of an arm or exactly zero for every episode of it,
so the ratio form and its zero-noise limit can never be ranked against each
other inside one correlation. Both forms are stated in the manuscript
(Appendix C.1, equations (C.1) and (C.2)).

An audit key `phase_loss_unsigned` = `alpha^2 * delta_proxy` is retained so the
archived pre-correction JSONs stay mechanically reproducible. `f8b` and `f25`
**assert** that it reproduces them. Nothing in the manuscript is computed from
it.

**What was rerun.** Everything E2, end to end, on the stored per-episode JSONs
(CPU re-analysis; no GPU retraining, no new model runs). Seeds, splits,
bootstrap protocol and cell populations are unchanged from the originals: the
same 50/50 commissioning/evaluation cross-fit, the same five split seeds
20260801–20260805, the same 1000-resample corruption-clustered bootstrap, the
same LOCO bootstrap seed 20260817. The pre-correction outputs are **kept on
disk untouched** (`f8*`, `f16*`, `f20*`) as the audit trail; the corrected runs
write under fresh f-numbers.

| corrected output | supersedes | what it is |
|---|---|---|
| `f22_e2_crossfit_feat_*` | `f8_e2_crossfit_*` | stochastic arms, feature proxy (full grid) |
| `f22b_e2_crossfit_det_*` | `f8b_e2_crossfit_det_*` | deterministic arms, loss proxy (full grid) |
| `f22c_e2_crossfit_loss_*` | — (new) | stochastic arms, loss proxy (full grid) |
| `f23_e2_gn_*` | `f16_e2_gn_*` | architecture-controlled 45-cell comparison |
| `f24_e2gn_loco_sensitivity.json` | `f20_e2gn_loco_sensitivity.json` | leave-one-corruption-out |
| `f25_e2_lr_ablation.json` | — (new; the ablation had no script) | learning-rate ablation |

**Localisation check.** `f22` reproduces `f8` **bit for bit** on every one of
its twelve reported correlations. The feature-proxy branch always carried the
sign and the stochastic arms never hit the zero-noise case, so the primary E2
result — the C2 gate — is untouched by the bug. The change is confined to the
loss proxy.

**Corrected numbers.** Cross-fit Spearman, mean-final, mean over five split
seeds:

| arm | cells | published (unsigned) | corrected (signed) |
|---|---:|---:|---:|
| tent, full grid, loss proxy | 105 | −0.676 | **+0.844** (0.832–0.854; clustered [+0.79, +0.89]) |
| pseudo-label, full grid, loss proxy | 75 | −0.849 | **+0.828** (0.806–0.849; [+0.72, +0.89]) |
| ttt_rot, full grid, loss proxy | 105 | −0.027 | **+0.068** (0.014–0.131; [−0.13, +0.25]) |
| ttt_mask, full grid, loss proxy | 105 | +0.425 | **+0.504** (0.440–0.538; [+0.27, +0.70]) |
| tent @ ResNet-26+GN, 45 cells | 45 | −0.902 | **+0.882** (0.845–0.895; [+0.74, +0.94]) |
| tent @ WRN-28-10+BN, 45 cells | 45 | −0.939 | **+0.926** (0.912–0.935; [+0.86, +0.96]) |
| pseudo-label @ WRN-28-10+BN, 45 cells | 45 | −0.905 | **+0.888** (0.833–0.929; [+0.81, +0.94]) |
| ttt_rot @ ResNet-26+GN, 45 cells | 45 | +0.151 | **+0.273** (0.052–0.492; [−0.05, +0.55]) |
| ttt_mask @ ResNet-26+GN, 45 cells | 45 | +0.253 | **+0.591** (0.573–0.612; [+0.29, +0.80]) |
| ttt_rot, feature proxy, 45 cells | 45 | +0.418 | +0.418 (unchanged) |
| ttt_mask, feature proxy, 45 cells | 45 | +0.610 | +0.610 (unchanged) |
| tent @ GN, feature proxy, 45 cells | 45 | +0.092 | +0.092 (unchanged) |
| ttt_rot / ttt_mask, feature proxy, full grid | 105 | +0.546 / +0.540 | +0.546 / +0.540 (unchanged) |

Every one of these reproduces the reviewer's own independent recompute to
three decimals. The feature-proxy rows are unchanged because that branch was
already signed (and for the `tent @ GN` row, because the zero-noise limit of
the feature statistic was also already signed).

Median-final aggregation moves too, and in the opposite direction from the
mean: on the 45 cells the deterministic arms go from −0.156/−0.085/−0.068 to
+0.665/+0.694/+0.702, while the stochastic loss-proxy arms go from
+0.525/+0.396 to +0.284/+0.103.

**LOCO (f24).** No fold flips a sign in any arm. entropy@GN +0.882 →
[+0.861, +0.896] (median +0.882, largest shift 0.021); entropy@BN +0.926 →
[+0.917, +0.937] (0.011); pl@BN +0.888 → [+0.880, +0.902] (0.014);
ttt_rot loss +0.273 → [+0.219, +0.327] (0.054, shot noise); ttt_mask loss
+0.591 → [+0.538, +0.672] (0.081, Gaussian noise); ttt_rot feat +0.418 →
[+0.328, +0.466]; ttt_mask feat +0.610 → [+0.554, +0.686]. Only ttt_rot's
intervals contain zero, and its *full* 15-cluster interval on the same
bootstrap stream does too, so what leaves it unresolved is the smallness of
the correlation and not the deletion.

**Learning-rate ablation (f25).** The manuscript called the three rates
"rank-stable" at ρ = 0.60 / 0.57 / 0.59. Those are the unsigned values, and
`f25` asserts that the unsigned numerator reproduces them (0.603 / 0.573 /
0.588) together with the archived mean best-step gains (0.1931 / 0.0883 /
0.2166), which localises the change to the sign. Corrected: **0.77 / 0.32 /
0.59** in the manuscript's in-sample convention and **0.49 / 0.16 / 0.32**
under the cross-fit the rest of E2 uses. Positive at every rate, spread 0.45
in-sample and 0.33 cross-fitted. The claim that survives is *sign* stability,
not rank stability, and the manuscript now says so.

**What the corrected data says, and what the manuscript now claims.** The
signed statistic ranks realized gain **positively in every arm and on every
architecture measured**. The withdrawn claims — that the statistic
"anti-predicts" gain for deterministic objectives, that the negative sign was
experimental evidence of persistent-alignment failure, that objective and
architecture form a negative/positive double dissociation, and that E2 splits
methods into two theoretical regimes — are gone, not softened.

Two structural facts fix what the corrected correlation means for the
deterministic arms, and both are now stated in the paper. Every one of the 105
tent cells and 75 pseudo-label cells has a **negative** mean realized gain:
these objectives lose in every cell of this grid. And the statistic is
**negative in every one of those cells too** — the alignment factor is negative
exactly on the confidently-wrong episodes, which are also the episodes carrying
the largest loss-based shift proxy, so the product is negative throughout. The
correlation is therefore a *within-sign* ordering: it says which cells lose
most, not that the statistic separates help from harm for these objectives.
There is no cell in this grid where they help.

The architecture-matched run keeps a job, a smaller one: entropy reproduces at
+0.882 on ResNet-26+GroupNorm against +0.926 on WRN-28-10+BatchNorm, so the
entropy result is not an artifact of WRN-28-10 or of BatchNorm. Where the
families genuinely part company is the **proxy**: on the same 45 cells the
loss proxy carries the signal for entropy while the feature proxy is a null
(+0.092, [−0.21, +0.37]), whereas the stochastic objectives are predicted by
both. That is the same lesson E4 reaches, and it is a statement about proxies,
not about the theory.

Manuscript passages rewritten: `sections/experiments.tex` (E2 subsection,
Table T5, Figure F4 caption, E5 learning-rate ablation),
`appendix/experimental_details.tex` (the statistic definition and its
zero-noise limit), `sections/discussion.tex` (the deterministic-objective
paragraph), `sections/introduction.tex`, `sections/conclusion.tex`. Figure 4
regenerated from the corrected outputs by `fig_f4_e2.py`.

## R7.2 Reporting and number corrections (review round 7, §4)

Ten reporting defects, all settled from records already on disk. Items 1–4, 6,
7 and 9 are recomputed by the new `f26_e1_reporting_audit.py` →
`f26_e1_reporting_audit.json`; item 5 was already correct in the experiments
section and stale only in the discussion; items 8 and 10 are textual.

| # | claim | was | is |
|---|---|---|---|
| 1 | T4 row (a) label vs statistic | labelled `sup_t \|Ê−E\|/E`, computed `max\|Δ\|/max E` = 0.0115 | pointwise `sup_t \|Ê−E\|/E` = **0.0223** (1.76–2.62%); the max/max value 0.0115 kept as an unscored continuity row |
| 2 | T4 row (b) sign accuracy | 0.979 (0.999 resolved) — a **fitted** threshold under a fixed-rule label | fixed theory rule `α²δ²/σ² ≷ η/2`: **0.984** (0.981–0.987), **1.000** resolved at every seed |
| 3 | curve-match worst deviation | "worst of the 12,030 comparisons is 3.35 SE" — a mean of per-seed maxima | **3.61** SE is the true maximum; 12,030 comparisons **per seed**, **60,150** across the five |
| 4 | optimal-stopping worst cell | 0.021 — a mean of per-seed worst cells | true worst single cell-run **0.0402**; per-seed worst average 0.0212 |
| 5 | oracle constants in the discussion | "measured constants 1–4" | **2.36** (2.25–2.48) vs the single-trajectory oracle, **5.58** (5.36–5.95) vs the compute-matched K=3 oracle |
| 6 | phase-boundary misses | "every miss is within simulation noise of zero" | true of the **fixed** rule (largest miss \|z\| = **1.50**); the **fitted** threshold misses one holdout cell at \|z\| = **3.257**, now reported |
| 7 | E4 alignment | "positive throughout (α_sgn ∈ [0.24, 0.46])" | that is the range of the four **per-domain means** ([0.235, 0.460]); per-document α_sgn runs −0.162 to +0.782 and is negative in **67 of 6,000** records (1.1%; 3.1% in legal) |
| 8 | Fig 3(c) caption | "the same realized risks" | panel (c) is an **independent rerun** (f13) at the same configuration and seeds, not a rescoring of the (a,b) sample |
| 9 | E1 replicate count | "12,000 replicates per cell" everywhere | per-part census: **40,000** (a), **20,000** (b), **60,000** in 3 blocks (c), 400 ALTA episodes + **40,000** oracle replicates (d), 90 rows (e), **400,000** per N (f) |
| 10 | "pre-registered" | asserted, with no timestamped protocol in the archive | **"pre-specified"** throughout, with a new appendix paragraph defining it as *gate criteria written as literals in the analysis script that produces the number*, and explicitly disclaiming a timestamped pre-registration |

`T4_e1_gates.tex` is no longer hand-maintained: `tab_t4_e1_gates.py` generates
it from the fresh five-seed summaries plus `f26`, and `--check` verifies the
committed table against a regeneration.

Item 10 also touches `sections/alta.tex:508`, which the theory track owns; that
one occurrence of "pre-registered" is **left for the theory agent** and recorded
in `REVISION_NOTES_R7.md`.

## R7.3 Files added in this round

Scripts (`experiments/ttt/is_fresh/`):

| file | role |
|---|---|
| `f25_e2_lr_ablation.py` | the learning-rate ablation, which previously existed only as a source comment |
| `f26_e1_reporting_audit.py` | recomputes review-round-7 §4 items 1–4, 6, 7, 9 from archived records |
| `tab_t4_e1_gates.py` | generates `T4_e1_gates.tex` from the fresh suite |

Modified: `f8_e2_crossfit.py` (signed statistic, declared zero-noise limit,
homogeneity assertion, `--out-prefix`), `f8b_e2_crossfit_det.py` (same, plus
the unsigned audit assertion replacing the old "must be negative" assertion),
`f16_e2_gn_analysis.py` (statistic construction imported from f8; sign-agnostic
verdict fields; `--out-prefix`), `f20_e2gn_loco_sensitivity.py` (`--out-name`),
`fig_f4_e2.py` (reads the corrected outputs; panel (c) axis relabelled).

Outputs (`experiments/results/is_fresh/`): `f22_e2_crossfit_feat_*`,
`f22b_e2_crossfit_det_*`, `f22c_e2_crossfit_loss_*`, `f23_e2_gn_*`,
`f24_e2gn_loco_sensitivity.json`, `f25_e2_lr_ablation.json`,
`f26_e1_reporting_audit.json`, and the run logs `f22.log`, `f22b.log`,
`f22c.log`, `f23.log`, `f24.log`.

The pre-correction `f8*`, `f16*` and `f20*` outputs are deliberately left in
place and unmodified. They are the audit trail for R7.1 and are reproducible
from the current code via `--statistic phase_loss_unsigned`.

---

## R16.1 Files added in round 16 (external review round 15, finding 1)

Scripts (`experiments/ttt/is_fresh/`):

| file | role |
|---|---|
| `f29_e4_pooled_ci.py` | E4 correlations and perplexity improvements: one percentile pair of a **pooled** 10,000-draw document-clustered bootstrap. Supersedes the interval endpoints of `f11_e4_cluster_ci.py`. |
| `f30_e4_alignment_pooled.py` | the E4 alignment-only comparison and the paired difference, same pooled construction. Supersedes the interval endpoints of `f17_e4_alignment_only.py`. |

Outputs (`experiments/results/is_fresh/`): `f29_e4_pooled_ci.json`,
`f30_e4_alignment_pooled.json`, and the run logs `f29.log`, `f30.log`.

Modified: `fig_f8_domains.py` (reads `f30`; asserts `n_pooled_draws == 10000`
and that the record's protocol still says *no averaging of endpoints* before
drawing anything; panel (e) axis label names the pooled construction);
`r9_reconcile.py` (42 new E4 endpoint, design-effect, ICC and census bindings,
taking the curated table from 152 to **194** claims, plus a new **PASS 1b**
construction check that a value comparison structurally cannot express);
`fig_f1_curves.py` (a comment containing two literal tab bytes where
`\textwidth` and `\topfraction` were intended — cosmetic, execution
unaffected); `make_release_zip.py` (ships `main.bbl`; withdraws an unsupported
`opencv-python` superlative); `RESOLVER_TRANSCRIPT.md` (records what the
resolver evidence does and does not establish).

`f11_e4_cluster_ci.py`, `f17_e4_alignment_only.py` and their JSON outputs are
deliberately left in place and unmodified. They are the audit trail of the
superseded endpoint-averaged construction, and `f29`/`f30` assert against them
that the pooled draws are the same draws (per-stream endpoint gap `0.0`) and
that no point estimate or verdict count moved. `f12_e4_proxy_loo.py` also
averages endpoints across its five bootstrap seeds; it was left unchanged in
round 16, on the reasoning that its held-out intervals were reported
qualitatively and that no endpoint of it was printed anywhere.

> **Round-17 correction (external review round 16, findings 1.1 and 1.2).
> Both halves of that reasoning were wrong.** The qualitative report was the
> census "excludes zero on the favourable side in 0 of 4", and that census
> was **false**: `f12`'s record says **1**, PubMed. And the manuscript did
> describe the resulting pairs as *bootstrap intervals*, which a mean of five
> percentile endpoints is not. Leaving `f12` alone in round 16 therefore left
> the same defect that round in place in the one place it had not been
> looked for. `f31_e4_proxy_pooled.py` applies the identical remedy: it
> replays `f12`'s exact draws (per-stream endpoint gap `0.0`, point-estimate
> gap `0.0`, fold selections asserted identical), pools the
> `5 x 2000 = 10,000` draws per quantity and reads one 2.5/97.5 percentile
> pair off each. The largest endpoint move is **0.00104** (PubMed's
> favourable-side lower endpoint, `+0.001475` to `+0.000440`), and neither
> exclusion count changes. `f12` and its JSON ship unmodified as the audit
> trail, exactly as `f11`/`f17` do.

---

## R17.1 Files added in round 17 (external review round 16)

Scripts (`experiments/ttt/is_fresh/`):

| file | role |
|---|---|
| `f31_e4_proxy_pooled.py` | the E4 leave-one-domain-out proxy intervals: one percentile pair of a **pooled** 10,000-draw document-clustered bootstrap per quantity. Supersedes the interval endpoints of `f12_e4_proxy_loo.py`, replays its exact draws, and asserts that the favourable-side and adverse-side exclusion counts agree across both constructions (findings 1.1, 1.2). |
| `tab_t6_e4_proxy.py` | generates Table T6, the per-domain proxy table Section 7.4 promised and the appendix did not contain (finding 6.2). Its caption's exclusion counts are read off the record, and `--check` fails the release build if the shipped `.tex` and the record disagree. |
| `build_env_section3.py` | interpolates section 3 of `BUILD_ENVIRONMENT.md` — page count, sizes, SHA-256s, error and undefined-reference censuses — from `main.pdf`, `main.log`, `main.tex` and `main.bbl`. Round 16 found that section one build stale (finding 1.3); `--check` now makes that state unpackageable. |

Outputs: `experiments/results/is_fresh/f31_e4_proxy_pooled.json`, the run log
`f31.log`, and `paper/is/paper/figures/T6_e4_proxy.tex`.

**What did not change.** No E1, E2, E3 or E5 result JSON; no raw record; no
point estimate anywhere in E4, including every `f12` selection and every
held-out correlation (all asserted equal at `0.0`); and no qualitative
verdict. `f12_e4_proxy_loo.py` and its JSON ship unmodified as the audit
trail. `F8_domains.pdf` was regenerated after `fig_f8_domains.py`'s stale
`f17`/`d17` local variables were renamed to `f30`/`d30` (finding 5.5); the
regenerated figure prints byte-for-byte the same values — its four
alignment-only correlations and intervals were re-verified against the
console output of the previous build — and differs only in the embedded
creation timestamp.

**Scope changes worth stating plainly.** Two counts in this file moved for
reasons that are not new measurements:

* the reconciliation went from **194 to 225** curated claims and from **12 to
  21** construction claims, the 31 new rows being every `f31` endpoint, both
  `f31` exclusion counts, the four held-out selections and their pooled
  intervals, and the two E5 aggregation-scope claims;
* the absolute-path gate's census went from the manifested payload files to
  **every archive entry** (finding 1.4), which is why its printed JSON,
  string-leaf and text-member counts are larger than round 16's: the eight
  generated root entries are now inside the scan, and `pip-freeze-full.txt` is
  a declared exception carrying 268 provenance paths. The claim did not
  weaken; the checker widened to the claim.

## R18.1 The E2 fresh-GroupNorm feature proxy, measured on the model that produced the episodes

**What was wrong.** The architecture-control arm `tent_gn` adapts a freshly
trained seed-20260806 ResNet-26+GroupNorm model over 45 cells x 256 = 11,520
episodes (`f15_e2_entropy_gn.py`). Its episode records carry every quantity
the phase statistic needs *except* `delta_feat`, which is not computed in the
adaptation loop. `f16` therefore joined `delta_feat` by (corruption,
severity, idx) from the published-model E5 file. That join was across source
models -- documented since the arm was added -- and, undocumented, **sparse**:
the two runs drew different episode indices, so only **300 of the 11,520**
episodes matched (2.60%), leaving 5-9 proxy observations per cell (mean 6.67)
and about three per cell after the 50/50 commissioning split, with one or two
cells carrying none. The arm nevertheless reported 256 episodes/cell, which
is true of the adaptation run and not of the statistic. The five split
correlations behind the `+0.092` it printed were
`0.077, -0.030, 0.043, 0.347, 0.023`.

**What was done.** `f38_e2gn_deltafeat_fresh.py` measures `delta_feat` where
it should have been measured: on the retained seed-20260806 checkpoint, over
that run's own 11,520 episode indices, under the published definition
imported from `experiments/ttt/e2_cifar/delta_feat.py` (pooled shared-encoder
features, cosine distance to the clean-test feature mean of the same model).
CPU only, about 70 seconds; it writes nothing until it reproduces the
checkpoint's recorded clean test accuracy (0.9164 recomputed against the
0.9165 in `f15_source_gate.json`, tolerance 0.002).

**What changed, and what did not.** Rerunning `f16 --out-prefix f23_e2_gn`
and `f20 --out-name f24_...` moves `tent_gn_feat` from `+0.092`
(endpoints [-0.21, +0.37], median -0.044) to **`+0.694`** (endpoints
[+0.38, +0.85], median +0.170) at 256 observations per cell, and its
leave-one-corruption-out range to [+0.643, +0.772]. **Every other arm is
unchanged to the last stored digit**: a key-by-key diff of both summaries
against the previous ones reports differences only inside `tent_gn_feat` and
in the newly added `statistic_support` blocks. The pre-correction audit
trails `f16_*` and `f20_*` were not touched.

**Why the reconciliation could not have caught it, and what now can.** The
reconciliation's question is whether a printed token equals its record, and
it did: the correlation matched `f23`, and 256 matched
`n_episodes_per_cell`. The two simply described different sets of episodes.
Every T5 row now binds **both** cardinalities, `f16` writes a
`statistic_support` block for every arm, PASS 1b requires the two to be equal
on all eight rows, and the coverage census of both record sets --
`f38_e2gn_deltafeat_fresh.json`, which also retains the superseded join's
five split correlations and per-split commissioning counts (145, 146, 149,
159, 142) -- is a shipped record rather than a claim in prose.
