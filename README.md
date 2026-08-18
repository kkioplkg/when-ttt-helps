# When Does Single-Instance Test-Time Adaptation Help? An Exact Phase Law in a Solvable Model

Experiment and analysis code for the paper of that title, together with the
analysis outputs and provenance records needed to check its numbers.

The manuscript itself is not in this repository. This is the code repository;
the large raw record sets live in a separate DOI deposit described in
[`DATA.md`](DATA.md).

## What the paper says, and what the code does

Test-time training (TTT) adapts a model to a single unlabeled test instance by
self-supervised descent. The paper settles *when that helps* exactly, inside a
solvable linear model:

- **Excess risk after `t` steps is closed-form.** Because the protocol executes
  whole steps, the criterion is an integer one: for step sizes `η ≤ 1/2` and at
  `η = 1`, some executable step count lowers risk exactly when the first step
  does, i.e. when `α²δ²(2 − ηα²) > ησ²` — for label-measured alignment `α`,
  initial excess risk `δ²`, and label-free per-coordinate noise `σ²`. Where an
  interior optimum exists within the horizon, the optimal count is its integer
  neighbour, and the gain is capped at `2α²δ²`.
- **Information.** Two environments can emit identical scalar self-supervised
  transcripts, so no label-free rule improves on freezing, uniformly over a
  nested environment class (a class-level minimax statement, not a converse to
  the phase law).
- **Mechanism.** Away from degenerate cases, entropy minimization injects no
  auxiliary randomness, and its binary first-order alignment sign is exactly its
  pointwise calibration sign — an *account* of that objective, not a special
  case of the phase law.
- **Evidence.** Simulation matches the closed forms and the integer boundary.
  The binary identity holds on trained networks under a declared target law:
  **zero violations in 358,709 measurements**. On CIFAR-10/100-C and GPT-2 the
  theory's diagnostics buy rank order only, the shift proxies add no consistent
  increment, and no deployable stopping rule follows.

The code here is what produced all of that: the experiment runners, the fresh
re-analysis suite that recomputes every printed number from the records, the
closure-experiment measurement and verification suite, and the packaging and
gate tooling that binds each number to its evidence file.

## Layout

Paths follow the reproducibility archive, so the paths quoted in `COMMANDS.md`,
`INDEX.md` and `MANIFEST.json` resolve here unchanged.

```
COMMANDS.md            every command, in dependency order — the entry point
INDEX.md               file-by-file index of the archive, with omissions and reasons
SEEDS.md               every seed used, per experiment
MANIFEST.json          sha256 + size for all 625 archive files
AUDIT_MAP.json         claim -> evidence-file map for the manuscript
GENERATED_MANIFEST.json  which shipped files are generated, and by what
BUILD_INTERPRETER.md   the tested interpreter (Python 3.10.9) and build machine
requirements-analysis.txt    install this to recompute the numbers (CPU)
requirements-experiment.txt  the original GPU experiment environment
pip-freeze-full.txt          complete freeze of the build environment

experiments/ttt/
  core/                shared model / utility code
  e1_synthetic/        E1 — the solvable linear model
  e2_cifar/            E2 — CIFAR-10/100-C runners (train, adapt, delta-feat)
  e4_gpt2/             E4 — GPT-2 domain-shift runners (+ vec_rerun/ replicas)
  analysis/            shared analysis helpers and fixtures
  is_fresh/            the fresh re-analysis suite: f1..f41, fig_*, tab_*
                       RESOLVER_TRANSCRIPT.md, VERIFY_TRANSCRIPT.md

experiments/results/
  m0/                  source-model evaluation summaries
  is_fresh/            analysis outputs — the JSONs the paper's numbers cite
    closure/code/      the closure experiment: measure, sweep, analyze, verify
    closure/json/      its analysis + verification reports (VERIFY_FINAL.json)
    closure/           DESIGN.md, RESULTS.md, manifests, review notes
    e3_vectors/        E3 replica manifests, provenance, verification
    e2_gn/             GroupNorm-lane gates and progress logs

figures/scripts/       figure generators
paper/is2/tools/       packaging, reconciliation and gate tooling
paper/is2/provenance/  interpreter and dependency records
paper/is2/paper/BUILD_ENVIRONMENT.md   the reference build environment record
```

## Environment

**Python 3.10.9 is the tested interpreter. Other versions are untested** — and
this is a pin, not a preference: `scipy==1.15.3` requires ≥ 3.10, and
`numpy==1.23.5` publishes no wheel for 3.12. See `BUILD_INTERPRETER.md` for the
full policy.

```bash
python -m venv .venv                 # on Python 3.10.9
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install -r requirements-analysis.txt
```

`requirements-analysis.txt` is the file to install. It covers every script in
`experiments/ttt/is_fresh` and `figures/scripts` **except** the two that need a
GPU (`f15_e2_entropy_gn.py`, which trains and samples, and `f_scope_bench.py`,
a wall-clock benchmark that recomputes no manuscript number). PyTorch is *not*
needed for the re-analyses — `core/utils.py` imports torch lazily — but it is
needed by `f6_relu_multiseed.py` and by the original runners under
`experiments/ttt/{e2_cifar,e4_gpt2}`. Those runners' environment is recorded
separately in `requirements-experiment.txt`.

## Reproducing the headline numbers

`COMMANDS.md` is authoritative and lists every command in dependency order.
Two caveats for this repository specifically:

1. Its "Building the two documents" section does not apply here — the
   manuscript sources and PDFs are not included.
2. Steps that re-derive analysis JSONs from raw per-instance records need the
   DOI deposit (see [`DATA.md`](DATA.md)). Steps that *check* a printed number
   do not: every number is bound to an analysis JSON that ships here.

The closed-form and simulation results run on CPU from a clean checkout:

```bash
# solvable-model measurements (CPU); run f10 before f3
python experiments/ttt/is_fresh/f1_boundary_onestep.py
python experiments/ttt/is_fresh/f2_boundary_stopped.py
python experiments/ttt/is_fresh/f10_oracle_grid.py
python experiments/ttt/is_fresh/f3_optimal_stopping.py
python experiments/ttt/is_fresh/f18_integer_boundary_check.py
```

Each writes a `*_summary.json` next to the others in
`experiments/results/is_fresh/`; compare against the committed copy.

The closure identity result — **358,709 measurements, zero violations** — is
recorded in `experiments/results/is_fresh/closure/json/VERIFY_FINAL.json`
(`route3_n_tested`, `route3_violations_recomputed`). To recompute it from the
records, fetch `closure_records.zip` per `DATA.md`, unpack it to
`experiments/results/is_fresh/closure/records/`, and run
`experiments/results/is_fresh/closure/code/verify_closure.py`.

Claim-to-file tracing goes through `AUDIT_MAP.json`; file integrity goes
through `MANIFEST.json` and the per-directory `MANIFEST_*.sha256` files.

## Paths and the run environment

Scripts that originally hard-coded the run host's directories now take them
from the environment or from a relative default:

- Python runners default to a relative `workdir/` (override with the usual
  `--data-root`, `--ckpt-dir`, `--out-dir` flags).
- `experiments/ttt/e4_gpt2/vec_rerun/*.sh` require `TTT_ROOT` to be set to the
  project root on the run host.

Because those files were rewritten, their `sha256` in `MANIFEST.json` — which
was computed over the archive originals — will not match the copies here. The
affected files are the runners under `experiments/ttt/e2_cifar/`,
`experiments/ttt/e4_gpt2/` and `experiments/ttt/e4_gpt2/vec_rerun/`. Every
other file matches its manifest entry.

## Data

Large record sets, model checkpoints and their hashes: [`DATA.md`](DATA.md).

## License

**No license file is included yet.** Without one, default copyright applies and
no reuse is permitted. If this repository is meant to serve as a reproducibility
artifact, add a license before pointing readers at it.
