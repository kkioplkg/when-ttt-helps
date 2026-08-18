# Dependency-provenance evidence

This file supplies the evidence for two questions the rest of the archive can
otherwise only *assert*: how the recorded experiment environment came to
hold a combination `pip` refuses to create, and whether the documented
`opencv-python` substitution really makes that set resolve.

Everything below was produced on the build machine described in
`BUILD_INTERPRETER.md` (Python 3.10.9, Anaconda, win-64).


## 1. How the conflicting combination got onto the machine

It is **not** *conda*, through its own solver, that installed the conflicting
pair: that is not what the installed state shows.  The two distributions were
installed by **different installers into different site directories**:

| distribution | version | installer | site directory |
|---|---|---|---|
| `numpy` | 1.23.5 | `conda` | the Anaconda prefix, `<prefix>/Lib/site-packages` |
| `opencv-python` | 4.12.0.88 | `pip` | the **per-user** site, `%APPDATA%/Python/Python310/site-packages` |

Evidence, in the installed metadata:

```
<prefix>/Lib/site-packages/numpy-1.23.5.dist-info/INSTALLER          -> conda
<prefix>/conda-meta/numpy-1.23.5-py310h60c9a35_0.json
    "channel": "https://repo.anaconda.com/pkgs/main/win-64"
    "url":     ".../win-64/numpy-1.23.5-py310h60c9a35_0.conda"

%APPDATA%/Python/Python310/site-packages/opencv_python-4.12.0.88.dist-info/INSTALLER
    -> pip
    METADATA: Requires-Dist: numpy<2.3.0,>=2; python_version >= "3.9"
```

and in the conda transaction log, `<prefix>/conda-meta/history`:

```
==> 2025-05-08 13:57:59 <==
# cmd: <prefix>\Scripts\conda-script.py install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia
# conda version: 23.3.1
...
+defaults/win-64::numpy-1.23.5-py310h60c9a35_0
+defaults/win-64::numpy-base-1.23.5-py310h04254f7_0
```

`opencv-python` appears nowhere in `conda-meta/`.  The accurate statement is
therefore the narrower, **location-only** one: **`numpy` 1.23.5 was installed
by conda into the environment prefix; `opencv-python` 4.12.0.88 was installed
by pip into the per-user site directory, which pip treats as a separate
installation target.**
The import system then resolves `numpy` from the prefix and `cv2` from the user
site, so both are importable in one interpreter even though no single `pip`
resolution would have produced that pair.  That is a property of the two-site
layout, not of conda's solver, and nothing in this archive claims otherwise.

**No chronology is claimed.**  The evidence above does not establish that pip
installed OpenCV *later*: `INSTALLER` files and the `conda-meta/history`
transaction record *which installer* wrote *which target*, not *when* the pip
write happened relative to the conda one; pip leaves no dated transaction log
for an already-installed distribution, and a `.dist-info` directory
modification time is a filesystem artefact, not installer metadata.  The word
"later" has therefore been withdrawn everywhere in favour of the
installer-and-location statement.  Any narrative of *how* the mixed
environment arose --- for instance that a working conda environment was
subsequently extended by a user-site `pip install opencv-python` --- is an
**interpretation**, offered as such and not as a finding, and would require
installation-order evidence this archive does not contain.

The consequence for a reader is unchanged: `requirements-experiment.txt` is a
*record* of what ran, not a lock `pip` can reconstruct.


## 2. Resolver transcripts

Produced in a **clean virtual environment** created from the build
interpreter, with no site packages inherited:

```
$ python -m venv <CLEAN-VENV>
$ <CLEAN-VENV>/Scripts/python -V
Python 3.10.9 | packaged by Anaconda, Inc. | (main, Mar  1 2023, 18:18:15) [MSC v.1916 64 bit (AMD64)]
$ <CLEAN-VENV>/Scripts/python -m pip --version
pip 22.3.1
```

`--dry-run` resolves and reports without installing.  The transcripts are
reproduced verbatim except that the temporary environment path is replaced by
`<CLEAN-VENV>` and the requirement-file names are restored to their archive
names.

Summary:

| set | expected | observed |
|---|---|---|
| `requirements-experiment.txt` as recorded | `ResolutionImpossible` | `ResolutionImpossible`, exit 1, with `opencv-python 4.12.0.88 depends on numpy<2.3.0 and >=2` named as a cause |
| same, with `opencv-python==4.9.0.80` | resolves | resolves, exit 0, `Would install ... numpy-1.23.5 opencv-python-4.9.0.80 ...` |
| `requirements-analysis.txt` | resolves | resolves, exit 0 |

```
### 1. requirements-experiment.txt AS RECORDED (opencv-python==4.12.0.88)
$ python -m pip install --dry-run -r requirements-experiment.txt
INFO: pip is looking at multiple versions of torchvision to determine which version is compatible with other requirements. This could take a while.
INFO: pip is looking at multiple versions of torch to determine which version is compatible with other requirements. This could take a while.
INFO: pip is looking at multiple versions of matplotlib to determine which version is compatible with other requirements. This could take a while.
INFO: pip is looking at multiple versions of scipy to determine which version is compatible with other requirements. This could take a while.
INFO: pip is looking at multiple versions of <Python from Requires-Python> to determine which version is compatible with other requirements. This could take a while.
INFO: pip is looking at multiple versions of numpy to determine which version is compatible with other requirements. This could take a while.
ERROR: Cannot install -r requirements-experiment.txt (line 48), -r requirements-experiment.txt (line 49), -r requirements-experiment.txt (line 53), -r requirements-experiment.txt (line 54), -r requirements-experiment.txt (line 59), -r requirements-experiment.txt (line 60) and numpy==1.23.5 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested numpy==1.23.5
    scipy 1.15.3 depends on numpy<2.5 and >=1.23.5
    matplotlib 3.7.0 depends on numpy>=1.20
    torchvision 0.18.0 depends on numpy
    transformers 4.24.0 depends on numpy>=1.17
    scikit-image 0.19.3 depends on numpy>=1.17.0
    opencv-python 4.12.0.88 depends on numpy<2.3.0 and >=2; python_version >= "3.9"

To fix this you could try to:
1. loosen the range of package versions you've specified
2. remove package versions to allow pip attempt to solve the dependency conflict

ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts

[notice] A new release of pip available: 22.3.1 -> 26.2
[notice] To update, run: <CLEAN-VENV>\Scripts\python.exe -m pip install --upgrade pip
EXIT=1

### 2. SAME SET WITH THE DOCUMENTED SUBSTITUTION (opencv-python==4.9.0.80)
$ python -m pip install --dry-run -r requirements-experiment.txt   # opencv-python pin substituted
Collecting idna<4,>=2.5
  Downloading idna-3.18-py3-none-any.whl (65 kB)
     ---------------------------------------- 65.5/65.5 kB ? eta 0:00:00
Collecting tbb==2021.*
  Downloading tbb-2021.13.1-py3-none-win_amd64.whl (286 kB)
     ------------------------------------- 286.9/286.9 kB 18.4 MB/s eta 0:00:00
Collecting intel-openmp==2021.*
  Downloading intel_openmp-2021.4.0-py2.py3-none-win_amd64.whl (3.5 MB)
     ---------------------------------------- 3.5/3.5 MB 22.5 MB/s eta 0:00:00
Collecting six>=1.5
  Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
Collecting MarkupSafe>=2.0
  Downloading markupsafe-3.0.3-cp310-cp310-win_amd64.whl (15 kB)
Collecting mpmath<1.4,>=1.1.0
  Downloading mpmath-1.3.0-py3-none-any.whl (536 kB)
     ------------------------------------- 536.2/536.2 kB 32.9 MB/s eta 0:00:00
Would install ImageIO-2.37.4 Jinja2-3.1.6 MarkupSafe-3.0.3 Pillow-9.4.0 PyWavelets-1.8.0 PyYAML-6.0.3 certifi-2026.7.22 charset-normalizer-2.1.1 colorama-0.4.6 contourpy-1.3.2 cycler-0.12.1 filelock-3.9.0 fonttools-4.63.0 fsspec-2022.11.0 huggingface-hub-0.10.1 idna-3.18 intel-openmp-2021.4.0 kiwisolver-1.5.0 matplotlib-3.7.0 mkl-2021.4.0 mpmath-1.3.0 networkx-3.4.2 numpy-1.23.5 opencv-python-4.9.0.80 packaging-26.3 pandas-1.5.3 pyparsing-3.3.2 python-dateutil-2.9.0.post0 pytz-2026.3.post1 regex-2026.7.19 requests-2.28.1 safetensors-0.7.0 scikit-image-0.19.3 scipy-1.15.3 six-1.17.0 sympy-1.14.0 tbb-2021.13.1 tifffile-2025.5.10 tokenizers-0.11.4 torch-2.3.0 torchvision-0.18.0 tqdm-4.64.1 transformers-4.24.0 typing_extensions-4.16.0 urllib3-1.26.20

[notice] A new release of pip available: 22.3.1 -> 26.2
[notice] To update, run: <CLEAN-VENV>\Scripts\python.exe -m pip install --upgrade pip
EXIT=0

### 3. requirements-analysis.txt (the installable lock)
$ python -m pip install --dry-run -r requirements-analysis.txt
Collecting mpmath<1.4,>=1.1.0
  Using cached mpmath-1.3.0-py3-none-any.whl (536 kB)
Would install Jinja2-3.1.6 MarkupSafe-3.0.3 contourpy-1.3.2 cycler-0.12.1 filelock-3.32.2 fonttools-4.63.0 fsspec-2026.7.0 intel-openmp-2021.4.0 kiwisolver-1.5.0 matplotlib-3.7.0 mkl-2021.4.0 mpmath-1.3.0 networkx-3.4.2 numpy-1.23.5 packaging-26.3 pillow-12.3.0 pyparsing-3.3.2 python-dateutil-2.9.0.post0 scipy-1.15.3 six-1.17.0 sympy-1.14.0 tbb-2021.13.1 torch-2.3.0 typing_extensions-4.16.0

[notice] A new release of pip available: 22.3.1 -> 26.2
[notice] To update, run: <CLEAN-VENV>\Scripts\python.exe -m pip install --upgrade pip
EXIT=0
```

## 3. What is still not evidenced

The transcripts above are resolutions, not installations, and they were run
long after the original GPU experiments.  They establish that the recorded set
does not resolve, that the named substitution does, and that the analysis lock
does -- nothing about the order in which the original environment was actually
assembled beyond what the installer metadata and the conda transaction log of
section 1 record.  No claim in this archive depends on more than that.

**No superlative about `opencv-python` 4.9.0.80 is evidenced here.**
Section 2 tests exactly two pins: 4.12.0.88,
which does not resolve against the pinned `numpy==1.23.5`, and 4.9.0.80, which
does.  Every release between them, and every release before 4.9.0.80, is
untested.  Describing 4.9.0.80 as
*"the last release whose metadata accepts numpy 1.x"* would be a claim about
the whole release history of the distribution, supported by nothing in this
file; `requirements-experiment.txt` says *"a tested
release whose metadata is compatible with the pinned numpy 1.23.5"* instead.
Establishing the superlative would require a release-by-release metadata
sweep, which is not performed.  Nothing depends on it: OpenCV is used only by
`experiments/ttt/e3_imagenet/generate_imagenet_c.py` for corruption
generation, the released analyses consume archived records, and any pin that
resolves serves the documented purpose.

The resolved version set in section 2 is not pinned: `pip` chose current
releases for the unpinned transitive dependencies on the day the transcript was
taken, so re-running it later will report different versions for those.  What
is being evidenced is the resolution outcome (possible / impossible) and the
named cause, not the exact closure.
