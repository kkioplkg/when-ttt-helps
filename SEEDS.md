# Seed manifest

Every random number in the fresh (`is_fresh`) analysis suite comes from a seed
in the 20260801+ range.  The original pipeline used 0, 1, 2, 42, 43, 100+ and
999+; none of those values is reused anywhere in the fresh suite, so a fresh
result can never be a re-report of a tuned original one.

| stage | script | seeds | role of the seed |
|---|---|---|---|
| E1 risk-curve match | `f7_curve_match.py` | 20260801-05 | trajectory simulation |
| E1 one-step boundary | `f1_boundary_onestep.py` | 20260801-05 | trajectory simulation |
| E1 stopped boundary | `f2_boundary_stopped.py` | 20260801-05 | simulation + SELECT/SCORE split |
| E1 three-gain grid | `f10_oracle_grid.py` | 20260801-05 | simulation + SELECT/SCORE split |
| E1 optimal stopping | `f3_optimal_stopping.py` | 20260801-05 | trajectory simulation |
| ALTA vs measured oracle | `f4_alta_measured_oracle.py` | 20260801-05 | ALTA episodes + oracle blocks |
| ALTA vs compute-matched oracle | `f13_compute_matched.py` | 20260801-05 | ALTA episodes + K-group oracle blocks |
| batch variance | `f5_batch_variance.py` | 20260801-05 | trajectory simulation |
| ReLU / PL regime | `f6_relu_multiseed.py` | 20260801-05 | network init + SGD |
| E2 cross-fit (stochastic) | `f8_e2_crossfit.py` | 20260801-05 | commissioning/evaluation split of existing episodes |
| E2 cross-fit (deterministic) | `f8b_e2_crossfit_det.py` | 20260801-05 | same |
| E4 clustered intervals (superseded endpoints; point estimates current) | `f11_e4_cluster_ci.py` | 20260806-10 | bootstrap resampling only |
| E4 clustered PERCENTILE intervals, pooled | `f29_e4_pooled_ci.py` | 20260806-10, pooled | replays f11's streams; no new randomness |
| E4 leave-one-domain-out proxy | `f12_e4_proxy_loo.py` | 20260806-10 | bootstrap resampling only |
| E2 entropy on ResNet-26+GN | `f15_e2_entropy_gn.py` | 20260806 | source training + episode sampling |
| E2 matched-cell cross-fit (all arms) | `f16_e2_gn_analysis.py` | 20260801-05 | commissioning/evaluation split of existing episodes |
| E4 alignment-only vs full statistic (superseded endpoints) | `f17_e4_alignment_only.py` | 20260811-15 | bootstrap resampling only |
| E4 alignment-only, pooled percentile intervals | `f30_e4_alignment_pooled.py` | 20260811-15, pooled | replays f17's streams; no new randomness |
| integer-criterion check on the f10 grid | `f18_integer_boundary_check.py` | 20260801-05 | none of its own: re-reads the f10 replicates |
| local-PL envelope monotonicity audit | `f33_pl_envelope_monotonicity.py` | 20260807 | its own draws over the envelope's admissible constants; reads no record |
| local-PL envelope at zero noise | `f35_pl_zero_noise.py` | 20260808 | its own draws over the admissible constants at sigtot = 0; reads no record |
| flow curve vs exact curve, and sigma = 0 as a value | `f36_flow_integer_bridge.py` | 20260809 | its own draws inside the flow corollary's hypotheses; reads no record |
| ReLU stress-test monotonicity, recounted | `f37_relu_monotonicity_recount.py` | none of its own: re-reads the five f6 per-seed records | -- |
| E2 leave-one-corruption-out sensitivity | `f20_e2gn_loco_sensitivity.py` | 20260801-05 split seeds; 20260817 bootstrap | cross-fit split of existing episodes; deletion bootstrap |
| E2 cross-fit, CORRECTED signed statistic, feature proxy | `f8_e2_crossfit.py --statistic phase_feat --out-prefix f22_e2_crossfit_feat` | 20260801-05 | commissioning/evaluation split of existing episodes |
| E2 cross-fit, CORRECTED signed statistic, deterministic arms | `f8b_e2_crossfit_det.py --statistic phase_loss --out-prefix f22b_e2_crossfit_det` | 20260801-05 | same |
| E2 cross-fit, CORRECTED signed statistic, loss proxy | `f8_e2_crossfit.py --statistic phase_loss --out-prefix f22c_e2_crossfit_loss` | 20260801-05 | same |
| E2 fresh-GN feature proxy, remeasured on the fresh source model | `f38_e2gn_deltafeat_fresh.py` | none of its own: a deterministic forward pass of the retained seed-20260806 checkpoint over the retained episode indices | -- |
| E3 selector recomputed from the released per-step vectors | `f39_e3_vector_selfcheck.py` | none of its own: the admissibility scan is deterministic and reads only `results/is_fresh/e3_vectors/*.npz` | -- |
| Per-member manifest of the unattached replica side archive | `f40_e3_replicas_manifest.py` | none of its own: it hashes the members and arrays of `paper/is2/e3_vectors_replicas.zip` | -- |
| Build and manifest the unattached theory-closure record archive | `f41_closure_records_manifest.py` | none of its own: it packs and hashes `results/is_fresh/closure/records/*.jsonl.gz` into `paper/is2/closure_records.zip` | -- |
| E2 matched-cell cross-fit, CORRECTED | `f16_e2_gn_analysis.py --out-prefix f23_e2_gn` | 20260801-05 | same |
| E2 leave-one-corruption-out, CORRECTED | `f20_e2gn_loco_sensitivity.py --out-name f24_e2gn_loco_sensitivity.json` | 20260801-05 split seeds; 20260817 bootstrap | as `f20` |
| E2 learning-rate ablation | `f25_e2_lr_ablation.py` | 20260801-05 | cross-fit split of existing episodes |
| E1 reporting audit (excess, accuracy and comparison-count census) | `f26_e1_reporting_audit.py` | none of its own: re-reads the f7/f10/f3/f4/f13 records | -- |
| E2 identity-level overlap of the cross-fit split | `f27_e2_identity.py` | 20260801-05 | reproduces f8's commissioning/evaluation split stream exactly |
| E2 temperature-scaling: BOTH estimands of the early-loss statement | `f34_e2_tempscale_estimands.py` | none of its own: re-reads the e2 calibration records | -- |
| Appendix B (P3) counterexample simulation | `f28_p3_montecarlo.py` | 20260801-05 | Pareto draws and the scan, 2e7 replications per seed |
| Fig. 1 risk curves | `fig_f1_curves.py` | 20260801-05 | replays `f7_curve_match.py`'s replicate stream cell for cell |

`f14_deltafeat_check.py` and `f21_e2_coverage.py` are deterministic: they
re-read existing records and compute rank or frequency statistics, with no
random component.  So are the figure scripts
`fig_f2_phase.py`, `fig_f3_alta.py`, `fig_f4_e2.py` and `fig_f8_domains.py`,
which plot the JSONs the scripts above emit and draw no random numbers, the
table generator `tab_t4_e1_gates.py`, which reads the fresh summaries plus
`f26_e1_reporting_audit.json`, and `f_scope_bench.py`, which measures
wall-clock only.

`fig_f1_curves.py` is the one figure script that draws random numbers: the
risk curves it plots are not stored in any record, so it re-simulates them.
It does so by replaying `f7_curve_match.py`'s loop verbatim -- same seeds,
same 30-cell order, same single `default_rng` stream -- and ASSERTS that all
120 per-cell error statistics per seed reproduce the archived
`f7_curve_match_seed<seed>.json` rows to 1e-9 relative.  The curves in
Figure 1 are therefore, replicate for replicate, the ones Sec. 5.1 and
Table T4 row (a) report on.

The bootstrap seeds are allocated in disjoint blocks so that no two resampling
analyses share a stream: 20260806-10 (`f11`, `f12`), 20260811-15 (`f17`),
20260817 (`f20`, `f24`).

The corrected E2 re-analyses (`f22`, `f22b`, `f22c`, `f23`, `f24`, `f25`) reuse
the split seeds, bootstrap protocol and cell populations of the runs they
correct, unchanged; only the statistic's sign convention changed.  Their
pre-correction counterparts (`f8*`, `f16*`, `f20*`) ship unmodified as the
audit trail.

The ORIGINAL records shipped under `results/{e2,e3,e4,e5}` carry
their own seeds inside `meta.argv.seed` of each file; those are the original
0/1/2 values and are reported as such.
