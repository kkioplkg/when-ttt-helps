"""Render verify_report.json into the human-readable VERIFY_SUMMARY.md table.

Kept as a generator rather than hand-written prose so the numbers in the
summary cannot drift from the numbers in the report -- the same failure mode
is2-R13 finding 6 raised about the reconciliation documentation.
"""
import argparse
import json
import os

BANDS = """
Diagnostic bands used below (fixed before the numbers were read, from the
cross-model design review of this rerun):

| quantity | consistent | inspect | reproduction failure |
|---|---|---|---|
| frozen (t=0) CE | <= 1e-4 | 1e-4 .. 1e-3 | >= 1e-2 |
| adapted CE through 20 steps | <= 1e-3 | 1e-3 .. 1e-2 | >= 1e-2 systematic |
| domain mean CE | <= 1e-3 | few 1e-3 | ~1e-2 |
| selector exact-match rate | 99-100% | 95-99% with tiny margins | < 95% |
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rep = json.load(open(args.report, encoding="utf-8"))
    jobs = rep["jobs"]

    L = []
    L.append("# E3 vector rerun — agreement with the retained records\n")
    L.append(f"Generated from `{os.path.basename(args.report)}`; "
             f"kappa = {rep['kappa']}; {len(jobs)} jobs.\n")
    L.append(BANDS)

    L.append("\n## A — document identity (frozen t=0 continuation CE)\n")
    L.append("No RNG and no adaptation enter this quantity, so it tests whether "
             "the rerun saw the *same documents*. `legal` and `wikitext` were "
             "rebuilt from upstream and are the rows that matter most.\n")
    L.append("| job | n | max abs | median abs | p99 abs | frac < 1e-4 |")
    L.append("|---|---|---|---|---|---|")
    for j in jobs:
        L.append(f"| {j['tag']} | {j['n_docs']} | {j['A_frozen_ce_max_abs']:.3e} | "
                 f"{j['A_frozen_ce_median_abs']:.3e} | {j['A_frozen_ce_p99_abs']:.3e} | "
                 f"{j['A_frozen_ce_frac_within_1e4']:.4f} |")

    L.append("\n## B — dispersion s(t) recomputed from the released vectors\n")
    L.append("| job | vs retained, max abs | vs retained, mean abs | vs this run's own record |")
    L.append("|---|---|---|---|")
    for j in jobs:
        L.append(f"| {j['tag']} | {j['B_dispersion_vs_retained_max_abs']:.3e} | "
                 f"{j['B_dispersion_vs_retained_mean_abs']:.3e} | "
                 f"{j['B_dispersion_vs_own_run_max_abs']:.3e} |")

    L.append("\n## C — the selector\n")
    L.append("`self-check` is the load-bearing column: it asks whether the "
             "**released arrays alone** reproduce this run's own `t_hat`. If it "
             "is not 1.0000 the release does not close is2-R13 finding 1, "
             "whatever the historical agreement is. `vs retained` is the "
             "separate question of whether the rerun landed on the published "
             "decision.\n")
    L.append("| job | self-check | vs retained | min abs margin | min normalised margin |")
    L.append("|---|---|---|---|---|")
    for j in jobs:
        L.append(f"| {j['tag']} | {j['C_selfcheck_rate']:.4f} "
                 f"({j['C_selfcheck_release_reproduces_own_t_hat']}/{j['n_docs']}) | "
                 f"{j['C_t_hat_match_rate_vs_retained']:.4f} "
                 f"({j['C_t_hat_recomputed_eq_retained']}/{j['n_docs']}) | "
                 f"{j['C_min_abs_boundary_margin']:.3e} | "
                 f"{j['C_min_normalised_boundary_margin']:.3e} |")

    mism = [(j["tag"], m) for j in jobs for m in j["C_mismatches"]]
    tot_n = sum(j["n_docs"] for j in jobs)
    tot_self = sum(j["C_selfcheck_release_reproduces_own_t_hat"] for j in jobs)
    tot_ret = sum(j["C_t_hat_recomputed_eq_retained"] for j in jobs)
    worst = max((abs(m["slack_at_disputed_t_normalised"]) for _, m in mism),
                default=0.0)
    L.append(f"\n**Grid totals — self-check {tot_self}/{tot_n} "
             f"({tot_self / tot_n:.4f}); t_hat vs retained {tot_ret}/{tot_n} "
             f"({tot_ret / tot_n:.4f}); {len(mism)} mismatches"
             + (f", worst |normalised slack| at a disputed step {worst:.3e}.**"
                if mism else ".**"))
    if mism:
        L.append("\nBecause $\\hat t$ is the *smallest* admissible step, two runs "
                 "that disagree must disagree about the admissibility of the "
                 "**earlier** of their two answers, $t_{disputed} = \\min$. "
                 "`slack at disputed t` evaluates that one inequality with this "
                 "run's vectors: its magnitude is the distance from the decision "
                 "boundary the two runs fell on opposite sides of. Values of "
                 "order 1e-4 normalised place the disagreement within 0.1% of that "
                 "boundary, which is what this measurement establishes; values "
                 "of order 1 would instead indicate genuinely divergent "
                 "trajectories. A slack that small is consistent with "
                 "boundary-sensitive numerical variation, but does not "
                 "demonstrate it and does not exclude a systematic "
                 "cross-hardware difference: the published run's per-step "
                 "trajectories were not retained, so nothing here can "
                 "distinguish the two explanations.\n")
        L.append("| job | doc | recomputed | retained | disputed t | slack there | normalised | admitted here |")
        L.append("|---|---|---|---|---|---|---|---|")
        for tag, m in mism[:60]:
            L.append(f"| {tag} | {m['doc']} | {m['t_hat_recomputed']} | "
                     f"{m['t_hat_retained']} | {m['t_disputed']} | "
                     f"{m['slack_at_disputed_t']:.3e} | "
                     f"{m['slack_at_disputed_t_normalised']:.3e} | "
                     f"{'yes' if m['admitted_by_this_run'] else 'no'} |")

    L.append("\n## D — trajectory and the fixed-budget headline\n")
    L.append("| job | max abs CE over all (doc,k,t) | mean CE @ t=20 new | retained | ppl@20 new | retained |")
    L.append("|---|---|---|---|---|---|")
    for j in jobs:
        L.append(f"| {j['tag']} | {j['D_cont_ce_max_abs']:.3e} | "
                 f"{j['D_fixed20_mean_new']:.6f} | {j['D_fixed20_mean_retained']:.6f} | "
                 f"{j['D_fixed20_ppl_new']:.4f} | {j['D_fixed20_ppl_retained']:.4f} |")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
