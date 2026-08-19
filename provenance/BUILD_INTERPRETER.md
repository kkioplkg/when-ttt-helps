# Build interpreter and machine

Metadata for the interpreter that built this archive.  **This file is not a
requirements file**; the installable pins are in `requirements-analysis.txt`,
the original GPU experiment environment is recorded in
`requirements-experiment.txt`, and the complete freeze of the build
environment is in `pip-freeze-full.txt`.

| field | value |
|---|---|
| Python | `3.10.9 \| packaged by Anaconda, Inc. \| (main, Mar  1 2023, 18:18:15) [MSC v.1916 64 bit (AMD64)]` |
| `sys.platform` | `win32` |
| platform | `Windows-10-10.0.19045-SP0` |
| machine | `AMD64` |
| processor | `Intel64 Family 6 Model 85 Stepping 4, GenuineIntel` |
| PyTorch | `2.3.0` |
| CUDA available at build time | `False` |
| CUDA runtime linked into PyTorch | `None` |

## Python version policy

**Python 3.10.9 is tested.  Other versions are untested.**

The archive was built and all shipped analyses were run on Python
3.10.9; that is the interpreter the pins in
`requirements-analysis.txt` were taken from, and it is the only one on which
that lock has been resolved and the analyses exercised.

Two weaker statements of this policy are not supportable and are not made
anywhere in this archive.  "Python 3.11+" contradicts the recorded
build interpreter above.  "3.9 through 3.12, given the same third-party
versions" is false on the pins
themselves: `scipy==1.15.3` declares `Requires-Python >= 3.10`, so 3.9 is
excluded outright, and `numpy==1.23.5` publishes no wheel for 3.12.  It is
true that the analysis code uses no syntax or standard-library feature newer
than Python 3.9 (no `match` statements, no `tomllib`, no PEP 604 `X | Y`
annotations evaluated at runtime, no `itertools.batched`), but source-level
compatibility is not interpreter compatibility once the pins are fixed.
Supporting a range would require a resolvable lock demonstrated on each
interpreter in it, and we have not built one.

## The LaTeX side

The TeX toolchain is pinned separately in
`paper/is/paper/BUILD_ENVIRONMENT.md`, which ships in this archive.
