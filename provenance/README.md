# Dependency-provenance records, shipped verbatim

This directory holds four records of **the interpreter that produced the
numbers in this submission**, not of the interpreter that happens to run the
packager:

| file | what it records |
|---|---|
| `BUILD_INTERPRETER.md` | interpreter version, platform, machine, CUDA availability |
| `requirements-analysis.txt` | the resolvable lock for recomputing the numbers the two documents print |
| `requirements-experiment.txt` | the ORIGINAL GPU experiment environment, as recorded |
| `pip-freeze-full.txt` | the complete `pip freeze --all` of the build environment |

They are a **verbatim, byte-identical copy** of the four root entries of the
frozen `paper/is/release_archive.zip`, which is where that interpreter's own
packaging run wrote them.  Nothing here is edited, reformatted or
regenerated.  `paper/is2/tools/make_release_zip.py` reads them from this
directory and ships them, unchanged, as the four root entries of
`paper/is2/release_archive.zip`.

## Why they are copied and not regenerated

Rendering these four files from whatever interpreter runs the packager turns
them into a record of the packaging session instead of a record of the
experiments: the pins become whatever is installed on the packaging machine,
the resolution claims in `experiments/ttt/is_fresh/RESOLVER_TRANSCRIPT.md`
stop being claims about the shipped file, and `pip-freeze-full.txt` loses the
conda-prefix and per-user-site paths that *are* the provenance evidence
`BUILD_ENVIRONMENT.md` section 6.4 reasons about.  The archive's own
absolute-path gate detected exactly that failure once: on a clean non-conda
interpreter the regenerated freeze came back path-free, so a declared
exception went stale and the build failed rather than shipping a record of
the wrong machine.

The four entries are provenance **of the experiments**, not of the package.
Copying them forward is what keeps them true; regenerating them is what would
falsify them.

## One line of `requirements-analysis.txt` is superseded, and is kept anyway

Line 51 of `requirements-analysis.txt` reads

> `# torch is a HARD dependency of the CPU-only re-analyses too:`
> `is_fresh/common.py imports run_e1, which imports core.utils, which does`
> `` `import torch` `` `at module scope.  See COMMANDS.md.`

That was true of the code when the record was written. It is **false of the
code shipped with this submission**: `core/utils.py` imports torch lazily,
inside the functions that touch a tensor, so `common.py` no longer drags it
in. Blocking `torch` and every `torch.*` submodule with a `sys.meta_path`
finder and then importing `is_fresh/common.py` succeeds, and `torch` is
absent from `sys.modules` afterwards.

The line is **not corrected**, for the reason the section above gives: these
four files are a record of the environment that produced the numbers, not a
description of the current tree, and every build in the source repository
asserts them byte-identical to their originals. Editing one to agree with
today's code is precisely the falsification this directory exists to
prevent. So the record keeps its sentence and `COMMANDS.md` supersedes it,
quoting it and giving the complete, measured list of the three shipped
scripts that do import torch — `is_fresh/f6_relu_multiseed.py`,
`is_fresh/f_scope_bench.py` and `is_fresh/f15_e2_entropy_gn.py`. The build
asserts that the superseded sentence is still present in the shipped record,
so the quotation cannot go stale unnoticed.

The pin `torch==2.3.0` itself is **not** stale: `f6_relu_multiseed.py` is
part of the documented analysis suite and does need torch. Only the stated
reason is.

## Why they are here rather than read out of the frozen archive

They used to be read directly out of `paper/is/release_archive.zip` at
packaging time.  That made the packager unrunnable from a clean extraction of
the release: the frozen parent archive is not shipped inside the release, so
the default command failed with a missing-file assertion and the released
archive could not rebuild itself with its own documented packaging utility.

Shipping the four records here is the transparent, non-recursive form of the
same dependency: the objects are present as plain files that a reader can
open, and no archive contains another archive.

## Re-verifying them against the frozen tree

Inside the source repository, where the frozen archive is present, the
packager does this automatically on every build and fails loudly on any
difference.  To repeat it by hand:

```
python - <<'PY'
import hashlib, zipfile
NAMES = ("BUILD_INTERPRETER.md", "requirements-analysis.txt",
         "requirements-experiment.txt", "pip-freeze-full.txt")
with zipfile.ZipFile("paper/is/release_archive.zip") as z:
    for n in NAMES:
        a = z.read(n)
        b = open("paper/is2/provenance/" + n, "rb").read()
        print(("OK  " if a == b else "DIFF"), n,
              hashlib.sha256(b).hexdigest())
PY
```

Inside an extracted release the frozen archive is absent by design.  The
copies here are then authenticated the same way every other shipped file is:
by `MANIFEST.json`, which records the size and SHA-256 of each of them, and
by the SHA-256 of the whole ZIP published in the review manifest.

## Note on the four root entries

The same four files also appear at the **root** of the release archive, which
is where the documentation, the installation instructions and the
absolute-path gate's exception list refer to them.  The root copies and the
copies in this directory are written from the same bytes in the same
packaging run, so they are byte-identical by construction.  `pip-freeze-full.txt`
is a declared absolute-path exception in both locations, for the reason stated
above and in `BUILD_ENVIRONMENT.md` section 6.4.
