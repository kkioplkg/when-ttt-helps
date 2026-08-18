# Result JSON schemas (inferred from the runner scripts, 2026-07-02)

Single source: the `save_json(...)` calls in `e1_synthetic/run_e1.py`,
`e2_cifar/train_source.py`, `e2_cifar/adapt_cifar.py`, `e3_imagenet/run_e3.py`,
`e4_gpt2/run_e4.py`. `analysis/aggregate.py` and any figure code should rely on
exactly what is documented here. Layout under a results root:

```
results/
  m0/<dataset>_<arch>_s<seed>.json
  e1/e1_<part>_seed<seed>.json          part in a..f
     e1_summary_seed<seed>.json         {part: {gate_pass}} (redundant, ignored)
  e2/<dataset>_<method>_<mode>_s<seed>[_bntrain].json
  e3/<corruption>_<method>_<stopping>_s<seed>[_smoke].json
  e4/<domain>_<ln|lora>_s<seed>.json
     wikitext_ref_s<seed>.json
```

All files are written atomically (`save_json`: tmp + rename), `indent=1`.
`*.json.tmp` files may exist after a crash and must be ignored.

Shared `meta` block (train_source / adapt_cifar / run_e3 / run_e4; NOT e1):

```
"meta": {"argv": {<all argparse args as dict>}, "time": str,
         "torch": str, "cuda": str}
```

## m0 -- `train_source.py`

```
{"meta": {...},                       # argv has dataset, arch, seed, ...
 "history": [{"epoch": int, "test_acc": float,
              "rot_acc": float|null,  # null for wrn2810 (no SSL head)
              "minutes": float}],
 "final": <last history entry>,
 "acc_gate": bool, "rot_gate": bool, "gate_pass": bool}
```

## e1 -- `run_e1.py` (no meta block; eta/T/n_rep only in part a)

Part a `e1_a_seed<seed>.json`:
```
{"eta": float, "T": int, "n_rep": int,
 "grid": [{"alpha": float, "delta": float, "sigma": float,
           "emp": [float]*(T+1), "theory": [float]*(T+1),
           "max_rel_err": float}],
 "worst_rel_err": float, "gate_pass": bool}       # gate: < 0.05
```

Part b (phase transition / sign prediction):
```
{"alphas": [25 floats], "ratios": [25 floats],
 "gain": [[25x25]], "phase_stat": [[25x25]],      # phase = (alpha*delta/sigma)^2
 "fit_accuracy": float, "fitted_threshold": float,
 "holdout_accuracy": float, "gate_pass": bool}    # gate: holdout >= 0.95
```
NOTE: part b does NOT record eta. The theoretical threshold eta/2 must be taken
from part a of the same seed (aggregate.py does this; falls back to the
hardcoded default ETA=0.05).

Part c (optimal stopping):
```
{"rows": [{"alpha", "delta", "t_theory": int, "t_emp": int, "risk_star",
           "risk_at_t_emp", "risk_rel_gap"}],
 "frac_risk_within_5pct": float, "frac_time_within_2x": float,
 "gate_pass": bool}                               # gate: risk-frac >= 0.9
```

Part d (ALTA vs oracle):
```
{"rows": [{"alpha", "delta", "t_star": int, "risk_star",
           "median_t_hat", "mean_realized_risk", "median_risk_ratio",
           "p90_risk_ratio", "frac_worse_than_frozen",
           "safe_vs_frozen": bool}],
 "log_Tmax": float, "eps_additive": float,
 "p90_gate": bool, "safety_gate": bool, "gate_pass": bool}
```

Part e (two-layer ReLU, constructed alignment):
```
{"rows": [{"rep": int, "delta_scale", "alpha", "sigma_rel", "E0",
           "best_gain", "final_risk", "diverged": bool, "t_emp": int,
           "curve_sub": [floats]}],
 "alpha0_mean_harm": float,
 "mean_relgain_by_alpha": {"0.0": float, ...},    # keys = str(alpha)
 "monotone": bool, "margin": float, "gate_pass": bool}
```

Part f (batch N):
```
{"rows": [{"N": int, "emp_min_risk", "theory_min_risk",
           "gain_emp", "gain_theory"}],
 "max_rel_err": float, "gate_pass": bool}         # gate: < 0.1
```

## e2 -- `adapt_cifar.py` (mode in tag; `_bntrain` suffix iff --bn-mode train)

Common `measure_alignment` keys (spread into episode/batch records):
```
alpha, sigma2_rel, sigma2_batch_rel, gnorm_ssl, gnorm_task, frozen_loss
```
For deterministic objectives (tent, pl) at N=1: sigma2_rel == 0.0 exactly.

mode=main `<ds>_<method>_main_s<seed>.json`:
```
{"meta": {...}, "clean_ref_loss": float,
 "results": [                                     # one cell per (corr, sev)
   {"corruption": str, "severity": int,
    "episodes": [
      {"idx": int, <measure_alignment keys>,
       "confidence": float,                       # frozen max softmax
       "frozen_correct": 0|1,
       "delta_proxy": float,                      # frozen_loss - clean_ref (can be < 0)
       "steps": {"<t>": {"loss": float, "correct": 0|1}},  # t in step grid
       "alta": null                               # deterministic methods / --alta off
             | {"t_hat": int, "loss": float, "correct": 0|1}}]}]}
```
Per-episode gain at step t := frozen_loss - steps[t].loss (plan definition).

mode=batch_sweep:
```
{"meta", "clean_ref_loss",
 "results": [{"corruption": str, "severity": 5, "N": int,
              "batches": [{<measure_alignment keys>, "frozen_acc": float,
                           "adapted_loss": float, "adapted_acc": float,
                           "steps": {"<t>": {"loss": float,   # v2 schema
                                             "acc": float}}   # (optional)
                          }]}]}
```
NOTE: batch records have NO delta_proxy field. sigma2_batch_rel is the
batch-mean-gradient variance (sigma2_point/N for deterministic objectives).
v2 (first real data batch onward): each batch record also carries "steps"
with per-step loss/acc at the recorded step grid (1,2,5,10,final). Old files
without "steps" still parse; aggregate.py falls back to final-step gains and
sets "final_only": true on the group output.
Absolute noise reconstruction used by the C3 gates (sigma2_batch_rel
conflates 1/N with the shrinking batch-mean gradient norm):
  sigma2_batch_abs = sigma2_batch_rel * gnorm_ssl^2   (should fall ~1/N)
  sigma2_point_abs = sigma2_batch_abs * N             (should be ~constant)
C3 gating is PER-GROUP with a SOURCE SPLIT (physics-motivated):
- GAIN gates (N=1 nonpositive-to-degrading; step-1 recovery at N>=32) are
  evaluated on bn-TRAIN groups (published-Tent protocol).
- SIGMA^2-mechanics gates (point_abs constancy ratio <= 4; batch_abs ~1/N
  spearman <= -0.8) are evaluated on bn-EVAL groups: in bn-train mode
  BatchNorm couples per-sample gradients through the batch statistics, so
  per-sample gradient dispersion there is NOT the theory's independent
  noise (bn-train point_abs ratios can be ~12 -- an observation, not a
  failure).
Missing source falls back to all groups (flagged in "gain_gate_source" /
"sigma_gate_source"). bn-eval gain behavior stays a secondary finding
("Tent in eval-BN mode does not gain at any N on clean-calibrated CIFAR
models"), never a gate failure. C3 = supported iff e1 part f plus all four
gates from their respective sources.

mode=calib (tent only; runs both temp settings in one file):
```
{"meta", "clean_ref_loss",
 "results": {"temperature": float,                # fitted on clean idx [0,5000)
             "cells": [{"corruption": str, "temp_scaled": bool,
                        "episodes": [{"alpha_ent": float, "confidence": float,
                                      "correct": 0|1, "frozen_loss": float,
                                      "adapted_loss": float,
                                      "adapted_correct": 0|1,
                                      "steps": {"<t>": {"loss": float,  # v2
                                                        "correct": 0|1}}
                                     }]}]}}
```
NOTE: results is a DICT here (list in the other two modes).
v2 (first real data batch onward): episodes also carry per-step
{loss, correct}. The C4 "temp scaling does not hurt adapted loss" criterion
is evaluated on steps 1-2 (the 20-step endpoint is deliberately in the
collapse regime, outside the claim's scope). Old files without "steps" fall
back to the final adapted_loss, flagged via "final_only" /
"early_criterion_basis" in the aggregator output.

## e3 -- `run_e3.py`

`<corruption>_<method>_<stopping>_s<seed>.json`, stopping in fixed|alta|oracle:
```
{"meta": {...},                                   # argv.severities e.g. "3,5"
 "clean_ref_loss": float|null,
 "results": [                                     # one cell per severity
   {"corruption": str, "severity": int, "n_batches": int, "n_images": int,
    "alignment": [{"batch": int, <measure_alignment keys>}],  # ~10 subsampled
    "batches": [{"batch": int, "frozen_correct": int,         # counts, not fracs
                 "t_hat": int,
                 "loss_by_step": [floats]          # fixed/oracle only, len steps+1
                 "dispersion": [floats],           # alta only
                 "alta_t0_is_frozen": true,        # alta only, v2 (see below)
                 "bn0_correct": int, "adapted_correct": int,
                 "acc_by_step": [ints],            # correct counts, len steps+1
                 "n": int}],
    "frozen_acc": float, "bn0_acc": float, "adapted_acc": float,
    "mean_t_hat": float, "t_hat_hist": [ints],     # len steps+1
    "acc_by_step": [floats],                       # cell-level fractions, index t=0..steps
    "frozen_loss_mean": float|null,
    "delta_proxy": float|null}]}                   # frozen_loss_mean - clean_ref
```
Semantics: index 0 of acc_by_step = t=0 batch-stat BN ("bn0"); "frozen" =
eval-mode running-stat BN. For stopping=fixed, t_hat == steps always, and the
best fixed-step baseline = max(acc_by_step). For stopping=oracle, t_hat is the
per-batch label-optimal step. Safety criterion: adapted_acc < frozen_acc - 0.002.
v2 (post ALTA safety fix): alta batches carry "alta_t0_is_frozen": true --
ALTA's t=0 candidate is the TRUE eval-BN frozen prediction, so ALTA can
decline to adapt. Unflagged alta files use the STALE semantics (t=0 was the
batch-stat state) and are progressively overwritten by reruns. aggregate.py:
(a) when both exist for the same (corruption, severity, method), only the
flagged cells are aggregated (stale ones dropped and counted); (b) the C5
safety gate counts an unflagged alta row only if no flagged alta run covers
that corruption.

## e4 -- `run_e4.py`

`<domain>_<ln|lora>_s<seed>.json`:
```
{"meta": {...},
 "protocol": {"prefix_len": 768, "cont_len": 256, "window": 512, "tail": 32},
 "wikitext_ref_mean": float|null,
 "records": [
   {"doc": int,
    "alpha": float, "sigma2_rel": float,          # NO sigma2_batch_rel here
    "gnorm_ssl": float, "gnorm_task": float,      # (measure_alignment_lm)
    "frozen_cont_ce": float,
    "delta_proxy": float|null,                    # frozen_ce - wikitext ref mean;
                                                  # null if no --ref-file was passed
    "cont_ce": [[float]*steps]*K,                 # per-replica CE curve (K=1 fixed, 3 else)
    "fixed": {"<t>": float},                      # replica-MEAN cont CE at recorded steps
    "oracle": {"t_star": int, "cont_ce": float},  # argmin over replica-mean curve
    "alta": null                                  # stopping=fixed
          | {"t_hat": int, "cont_ce": float, "dispersion": [floats]}}]}
```

`wikitext_ref_s<seed>.json` (written by the wikitext run):
```
{"mean_frozen_cont_ce": float, "n_docs": int, "seed": int}
```
aggregate.py fills null delta_proxy from this file (matching seed), falling
back to the wikitext run's own mean frozen CE.

## e5 -- representation-space shift proxies (delta_v2 / delta_feat)

`e5/delta_v2_<domain>.json` (E4/C6):
```
{"domain": str, "layer": int,                     # GPT-2 layer (6)
 "ref": str,                                      # reference identifier
 "records": [{"doc": int, "delta_v2": float}]}    # cosine distance >= 0
```
delta_v2 = cosine distance of the doc's mean-pooled GPT-2 layer-6 hidden
state to the wikitext reference mean, at theta0 (seed-independent; joined to
e4 records by doc id). When present, the C6 within-domain analysis uses the
PRIMARY statistic phase = alpha * |alpha| * delta_v2 / sigma^2 (delta_v2 is
a direct shift measure -- NO centering; alpha sign preserved via
alpha*|alpha|); the centered-frozen-CE variant remains as the secondary
statistic. Gate unchanged: rho >= 0.3 in >= 3 of 4 domains, either gain
basis (gain@ALTA or gain@best-fixed).

`e5/delta_feat_<dataset>_<arch>.json` (E2/C2, mirror of delta_v2):
```
{"dataset": str, "arch": str,                     # resnet26ttt | wrn2810
 "ref": str, "model_seed": int,
 "records": [{"corruption": str, "severity": int,
              "idx": int, "delta_feat": float}]}  # feature distance >= 0
```
Joined to e2 main-mode episodes by (dataset, arch, corruption, severity,
idx); arch is the method's source model (resnet26ttt for ttt_*, wrn2810 for
tent/pl). When present, the C2 per-episode PRIMARY phase statistic becomes
alpha * |alpha| * delta_feat / sigma^2 (loss-based delta_proxy stays
secondary; both cell-level mean and median variants are reported). Gate
unchanged: rho >= 0.5 for >= 2 stochastic methods, on the primary statistic,
any of mean/median x gain-final/gain-best.

## Known ambiguities / caveats found while inferring these schemas

1. e1 part b omits eta; the eta/2 comparison needs part a of the same seed
   (or the hardcoded default 0.05). Consider adding "eta" to part b output.
2. e2 delta_proxy is a per-episode excess LOSS (not squared parameter shift)
   and can be negative on easy corrupted points; the phase statistic
   alpha^2*delta_proxy/sigma^2 therefore can be negative too.
3. tent/pl at N=1 have sigma2_rel == 0 exactly (deterministic objective);
   the phase statistic degenerates. aggregate.py uses alpha^2*delta_proxy for
   such cells and flags them (`deterministic_sigma`), and flags pooled
   correlations that mix the two statistics.
4. e2 calib files: `results` is a dict, unlike main/batch_sweep (a list).
   The tag still contains the --method argument even though the calib runner
   always adapts with tent.
5. e3 fixed runs double as ALL fixed-step baselines via acc_by_step; there is
   no separate per-step-count file.
6. e3 "frozen_acc" (eval BN) != "bn0_acc" (test-batch BN at t=0). The safety
   property in the plan is stated vs frozen; aggregate.py follows that.
7. e4 `fixed` values are replica-mean CE; for stopping=fixed K=1, so they are
   single-trajectory. Per-doc gain uses ALTA stop when present, else the
   largest recorded fixed step.
7b. e4 delta_proxy (frozen CE - wikitext mean) is INVALID as a cross-domain
   shift measure: it is confounded by intrinsic domain entropy (code has far
   lower frozen ppl than wikitext, so its "shift" is hugely negative while
   its adaptation gains are the largest). The C6 analysis therefore centers
   delta WITHIN each domain (per-doc frozen CE minus the domain mean) for
   the phase statistic, uses within-domain spearman(phase, gain at ALTA /
   at best fixed step) as the primary test (gate: rho >= 0.3 in >= 3 of 4
   domains) plus qualitative criteria (positive ppl improvement in all
   domains at ALTA; ALTA within 15% relative of best fixed), and keeps the
   old cross-domain sign test only as a labeled diagnostic. With E5
   delta_v2 files present, the within-domain PRIMARY statistic becomes
   alpha*|alpha|*delta_v2/sigma^2 (representation-space shift; no centering
   needed) and the centered-CE variant is secondary. Metric-design lesson
   for the paper's limitations section: loss-based delta proxies are
   confounded by intrinsic domain entropy; representation-distance proxies
   recover the theory's prediction.
8. e1 has no meta block and no per-seed eta except part a; all other runners
   embed full argv under meta.argv.
9. Smoke files: e3 appends `_smoke` to the tag; e2/e4 smoke runs are NOT
   tagged in the filename (only visible via meta.argv.smoke / episode counts).
   aggregate.py filters only the `_smoke` filename convention by default.
