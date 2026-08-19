# E3 vector rerun — agreement with the retained records

Generated from `verify_report.json`; kappa = 1.5; 12 jobs.


Diagnostic bands used below (fixed before the numbers were read, from the
cross-model design review of this rerun):

| quantity | consistent | inspect | reproduction failure |
|---|---|---|---|
| frozen (t=0) CE | <= 1e-4 | 1e-4 .. 1e-3 | >= 1e-2 |
| adapted CE through 20 steps | <= 1e-3 | 1e-3 .. 1e-2 | >= 1e-2 systematic |
| domain mean CE | <= 1e-3 | few 1e-3 | ~1e-2 |
| selector exact-match rate | 99-100% | 95-99% with tiny margins | < 95% |


## A — document identity (frozen t=0 continuation CE)

No RNG and no adaptation enter this quantity, so it tests whether the rerun saw the *same documents*. `legal` and `wikitext` were rebuilt from upstream and are the rows that matter most.

| job | n | max abs | median abs | p99 abs | frac < 1e-4 |
|---|---|---|---|---|---|
| code_ln_s0 | 500 | 6.199e-06 | 5.960e-07 | 3.225e-06 | 1.0000 |
| code_ln_s1 | 500 | 6.199e-06 | 5.960e-07 | 3.225e-06 | 1.0000 |
| code_ln_s2 | 500 | 6.199e-06 | 5.960e-07 | 3.225e-06 | 1.0000 |
| legal_ln_s0 | 500 | 2.384e-06 | 4.768e-07 | 1.669e-06 | 1.0000 |
| legal_ln_s1 | 500 | 2.384e-06 | 4.768e-07 | 1.669e-06 | 1.0000 |
| legal_ln_s2 | 500 | 2.384e-06 | 4.768e-07 | 1.669e-06 | 1.0000 |
| pubmed_ln_s0 | 500 | 2.861e-06 | 4.768e-07 | 2.148e-06 | 1.0000 |
| pubmed_ln_s1 | 500 | 2.861e-06 | 4.768e-07 | 2.148e-06 | 1.0000 |
| pubmed_ln_s2 | 500 | 2.861e-06 | 4.768e-07 | 2.148e-06 | 1.0000 |
| wikitext_ln_s0 | 500 | 2.623e-06 | 4.768e-07 | 2.146e-06 | 1.0000 |
| wikitext_ln_s1 | 500 | 2.623e-06 | 4.768e-07 | 2.146e-06 | 1.0000 |
| wikitext_ln_s2 | 500 | 2.623e-06 | 4.768e-07 | 2.146e-06 | 1.0000 |

## B — dispersion s(t) recomputed from the released vectors

| job | vs retained, max abs | vs retained, mean abs | vs this run's own record |
|---|---|---|---|
| code_ln_s0 | 7.052e-04 | 6.993e-05 | 0.000e+00 |
| code_ln_s1 | 2.125e-03 | 7.349e-05 | 0.000e+00 |
| code_ln_s2 | 1.845e-03 | 7.210e-05 | 0.000e+00 |
| legal_ln_s0 | 1.736e-04 | 3.688e-05 | 0.000e+00 |
| legal_ln_s1 | 1.250e-04 | 3.563e-05 | 0.000e+00 |
| legal_ln_s2 | 1.264e-04 | 3.634e-05 | 0.000e+00 |
| pubmed_ln_s0 | 9.600e-04 | 3.786e-05 | 0.000e+00 |
| pubmed_ln_s1 | 5.438e-04 | 3.821e-05 | 0.000e+00 |
| pubmed_ln_s2 | 1.446e-03 | 3.895e-05 | 0.000e+00 |
| wikitext_ln_s0 | 1.215e-04 | 3.510e-05 | 0.000e+00 |
| wikitext_ln_s1 | 1.426e-04 | 3.473e-05 | 0.000e+00 |
| wikitext_ln_s2 | 1.340e-04 | 3.511e-05 | 0.000e+00 |

## C — the selector

`self-check` is the load-bearing column: it asks whether the **released arrays alone** reproduce this run's own `t_hat`. If it is not 1.0000 the release does not make the selector recomputable, whatever the historical agreement is. `vs retained` is the separate question of whether the rerun landed on the published decision.

| job | self-check | vs retained | min abs margin | min normalised margin |
|---|---|---|---|---|
| code_ln_s0 | 1.0000 (500/500) | 1.0000 (500/500) | 1.307e-06 | 7.563e-06 |
| code_ln_s1 | 1.0000 (500/500) | 1.0000 (500/500) | 4.557e-06 | 1.446e-05 |
| code_ln_s2 | 1.0000 (500/500) | 1.0000 (500/500) | 4.352e-06 | 4.455e-06 |
| legal_ln_s0 | 1.0000 (500/500) | 0.9980 (499/500) | 3.114e-08 | 7.723e-07 |
| legal_ln_s1 | 1.0000 (500/500) | 0.9980 (499/500) | 6.500e-07 | 1.590e-05 |
| legal_ln_s2 | 1.0000 (500/500) | 0.9940 (497/500) | 1.905e-06 | 3.964e-05 |
| pubmed_ln_s0 | 1.0000 (500/500) | 1.0000 (500/500) | 7.221e-07 | 4.458e-05 |
| pubmed_ln_s1 | 1.0000 (500/500) | 1.0000 (500/500) | 9.971e-07 | 5.328e-05 |
| pubmed_ln_s2 | 1.0000 (500/500) | 0.9980 (499/500) | 2.091e-07 | 2.753e-05 |
| wikitext_ln_s0 | 1.0000 (500/500) | 1.0000 (500/500) | 1.379e-06 | 5.024e-05 |
| wikitext_ln_s1 | 1.0000 (500/500) | 0.9960 (498/500) | 2.116e-07 | 7.356e-06 |
| wikitext_ln_s2 | 1.0000 (500/500) | 0.9940 (497/500) | 3.666e-07 | 2.486e-05 |

**Grid totals — self-check 6000/6000 (1.0000); t_hat vs retained 5989/6000 (0.9982); 11 mismatches, worst |normalised slack| at a disputed step 9.697e-04.**

Because $\hat t$ is the *smallest* admissible step, two runs that disagree must disagree about the admissibility of the **earlier** of their two answers, $t_{disputed} = \min$. `slack at disputed t` evaluates that one inequality with this run's vectors: its magnitude is the distance from the decision boundary the two runs fell on opposite sides of. Values of order 1e-4 normalised place the disagreement within 0.1% of that boundary, which is what this measurement establishes; values of order 1 would instead indicate genuinely divergent trajectories. A slack that small is consistent with boundary-sensitive numerical variation, but does not demonstrate it and does not exclude a systematic cross-hardware difference: the published run's per-step trajectories were not retained, so nothing here can distinguish the two explanations.

| job | doc | recomputed | retained | disputed t | slack there | normalised | admitted here |
|---|---|---|---|---|---|---|---|
| legal_ln_s0 | 136 | 17 | 16 | 16 | -1.031e-05 | -1.777e-04 | no |
| legal_ln_s1 | 327 | 16 | 15 | 15 | -3.477e-05 | -9.115e-04 | no |
| legal_ln_s2 | 7 | 16 | 17 | 16 | 5.137e-05 | 9.697e-04 | yes |
| legal_ln_s2 | 193 | 18 | 17 | 17 | -2.301e-06 | -4.373e-05 | no |
| legal_ln_s2 | 262 | 15 | 16 | 15 | 5.474e-06 | 7.485e-05 | yes |
| pubmed_ln_s2 | 83 | 16 | 17 | 16 | 1.145e-05 | 1.136e-04 | yes |
| wikitext_ln_s1 | 272 | 16 | 17 | 16 | 1.253e-05 | 2.116e-04 | yes |
| wikitext_ln_s1 | 472 | 17 | 16 | 16 | -3.786e-06 | -4.362e-05 | no |
| wikitext_ln_s2 | 35 | 15 | 16 | 15 | 1.050e-04 | 8.782e-04 | yes |
| wikitext_ln_s2 | 354 | 17 | 18 | 17 | 2.304e-05 | 5.255e-04 | yes |
| wikitext_ln_s2 | 451 | 16 | 17 | 16 | 3.530e-05 | 4.398e-04 | yes |

## D — trajectory and the fixed-budget headline

| job | max abs CE over all (doc,k,t) | mean CE @ t=20 new | retained | ppl@20 new | retained |
|---|---|---|---|---|---|
| code_ln_s0 | 1.631e-04 | 1.712203 | 1.712201 | 5.5412 | 5.5411 |
| code_ln_s1 | 1.669e-04 | 1.711930 | 1.711928 | 5.5396 | 5.5396 |
| code_ln_s2 | 1.860e-04 | 1.711898 | 1.711896 | 5.5395 | 5.5395 |
| legal_ln_s0 | 1.097e-05 | 2.578702 | 2.578703 | 13.1800 | 13.1800 |
| legal_ln_s1 | 1.287e-05 | 2.578686 | 2.578687 | 13.1798 | 13.1798 |
| legal_ln_s2 | 1.121e-05 | 2.578679 | 2.578680 | 13.1797 | 13.1797 |
| pubmed_ln_s0 | 4.463e-04 | 3.044659 | 3.044659 | 21.0029 | 21.0029 |
| pubmed_ln_s1 | 2.933e-04 | 3.044688 | 3.044689 | 21.0035 | 21.0035 |
| pubmed_ln_s2 | 3.314e-04 | 3.044739 | 3.044739 | 21.0045 | 21.0046 |
| wikitext_ln_s0 | 1.025e-05 | 3.137561 | 3.137561 | 23.0476 | 23.0476 |
| wikitext_ln_s1 | 1.144e-05 | 3.137569 | 3.137569 | 23.0478 | 23.0478 |
| wikitext_ln_s2 | 1.121e-05 | 3.137576 | 3.137576 | 23.0479 | 23.0479 |
