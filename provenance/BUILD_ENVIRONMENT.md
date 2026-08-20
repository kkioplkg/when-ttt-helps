# BUILD_ENVIRONMENT — the reference build for the two-document submission

**What "pinned" means here, and what it does not.** This file is a detailed
*version record* of one reference environment: the TeX distribution, the
package versions, the engine, the fonts and the exact build sequence are all
written down, so that a divergence can be diagnosed rather than guessed at. It
is **not** an executable frozen TeX environment: the archive does not ship a
container or a TeX installation, and running the documented sequence on a
different TeX tree is therefore not guaranteed to reproduce the shipped
pagination. Exact cross-machine page counts are not promised, and no claim in
either document depends on one — see the layer-comparison recipe in §5. What
*is* guaranteed by the shipped gates is the content: zero LaTeX errors, zero
undefined references, and a text layer that matches.

The failure mode this file exists to prevent: a source bundle that does not
pin its TeX distribution, package versions, font environment and build
container cannot reproduce its own page count, and nobody can then tell
harmless layout drift apart from a real difference in content. That is not
hypothetical for this manuscript. Rebuilding an earlier source tree and its
compiled bibliography under a standard pdflatex workflow on another machine
produced a document two pages longer than the shipped PDF, with no substantive
text difference — the divergence was layout, float placement, font metrics and
LaTeX environment. Without a pin there is nothing to check the shipped output
against.

**A measured instance of exactly that drift, for calibration.** An earlier
state of this source tree paginated the article to **29 pages** under the
reference environment recorded in §3 (MiKTeX, versions in §2.1), and an
independent rebuild of that same tree under a current TeX Live paginated it
to **30**, with no substantive difference in content and with the
supplement identical in length under both. One page in twenty-nine is the
size of drift this class of difference produces here, and it is what §2.1's
layout-affecting block is for: pin `cas-sc`, `geometry`, `stfloats`,
`longtable`, the tabular stack and `stix` first, because those are what move
a float across a page break. Two consequences follow, and both are load
bearing. First, **the page counts in §3 are properties of the reference
build, not of the source**: they are read off the build products rather than
typed, and a different TeX tree may legitimately produce different ones.
Second, the reader who wants certainty about *content* rather than
pagination should not chase the page count at all — run the §5 layer
comparison, which compares the extracted text layer and is insensitive to
where pages break. Every gate this submission ships is a gate of that kind;
none of them asserts a page total, and no claim, number, table or figure in
either document depends on one.

This file is that pin. It is referenced from `COMMANDS.md` in the
reproducibility archive.

**The submission is two documents, and this file covers both.**

| document | source | role |
|---|---|---|
| `paper/main.pdf` | `paper/is2/paper/` | the article, Elsevier `cas-sc`, single column |
| `supplement/supplement.pdf` | `paper/is2/supplement/` | the Supplementary Material, plain `article` |

The supplement is deliberately **not** built with `cas-sc`. It carries no
Elsevier **journal front matter** — no `cas-sc` metadata block, no
`\maketitle`, no abstract, no keywords, no `Page N of M` footer — and loading
the journal class would require duplicating the article's author metadata into
a second document that is not the article of record. It *does* carry a plain
centred title and placeholder author and affiliation lines, set by hand, so the
claim is precisely the narrow one — no Elsevier front matter — and not the
wider and false "no title block, no author or affiliation fields". It shares `math_commands.tex`, `references.bib` and
two generated table fragments with the article rather
than duplicating them, so a figure or macro cannot diverge between the two.

**Where those shared files are, and why `supplement/` alone still builds when
it is uploaded by itself.** In this tree they live in `paper/`, and the single
place that path appears is `\SharedRoot` in `supplement.tex`, which defaults to
`../paper/`. `supplement.tex` first tries `\InputIfFileExists{shared_root}`: if
a `shared_root.tex` sits beside it, that file's `\def\SharedRoot{./}` wins and
every shared reference resolves locally instead. `make_review_zip.py` writes
exactly that one-line file into `supplement/` inside the review package, beside
byte-for-byte copies of the four shared files, and asserts at package time that
each copy equals the article's original. So the shipped `supplement/` directory
is an independently buildable source package, the shared macros keep exactly
one hand-maintained home, and `--standalone-build-check` compiles the packaged
`supplement/` with no sibling directory reachable — a shared dependency added
without being declared fails there rather than at an editor's upload.

The supplement cannot resolve the article's labels. Every article object it
names is reached through a `\Main…` macro defined in `supplement.tex`, which is
one edit site per object if the article is ever renumbered again.

---

## 1. Exact build command

### 1.1 The article

Five `pdflatex` passes and one `bibtex`, in this order, from
`paper/is2/paper/`:

```
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex   main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

`paper/is2/tools/build.sh` is that sequence, and is the implementation of
record for it.

**Why five passes and not three.** `cas-common.sty` writes the "Page N of M"
footer total to the `.aux` from an `\AtEndDocument` hook whose `\clearpage` is
commented out, so the total it records is taken before the last pages ship and
is systematically one short — a 66-page build printed `Page 66 of 65`, and the
value was *stable*, not unconverged, so extra passes alone never fixed it.
`main.tex` therefore loads `lastpage` and redefines `\lastpage` to
`\pageref{LastPage}` at `\AtBeginDocument`. That reference needs its own extra
pass to settle. Passes 4 and 5 are byte-identical; pass 5 exists only to
*prove* convergence. If your run stops at pass 3, the footer total will be
wrong — that is a build error, not a source error.

### 1.2 The supplement

Four `pdflatex` passes and one `bibtex`, from `paper/is2/supplement/`:

```
pdflatex -interaction=nonstopmode supplement.tex
bibtex   supplement
pdflatex -interaction=nonstopmode supplement.tex
pdflatex -interaction=nonstopmode supplement.tex
pdflatex -interaction=nonstopmode supplement.tex
```

`paper/is2/tools/build_supp.sh` is that sequence. The supplement has no
`lastpage` footer to converge, so it needs one pass fewer than the article; the
three post-`bibtex` passes settle its table of contents, its internal `\ref`s
and its bibliography.

**Build the article first.** `supplement.tex`'s `\Main…` macros are filled from
the article's final numbering; if the article is rebuilt with a changed
numbering and the supplement is not, the supplement points at the previous
numbers and nothing in either `.log` says so. The reconciliation of §6 is what
catches that, because it scans both documents.

### 1.3 The compiled bibliographies

`main.bbl` and `supplement.bbl` ship in **both** distributed packages — the
review ZIP and `release_archive.zip` — so a reader without the `.bib` toolchain
can skip `bibtex` and run `pdflatex` alone from either one. The article's
bibliography style is `cas-model2-names`, supplied by the Elsevier CAS bundle.

> **Why the `.bbl` files are asserted into both packages, not merely claimed.**
> The weaker sentence "`main.bbl` ships in the archive" is true of the review
> package and **false of `release_archive.zip`** unless the file is asserted
> in: `.bbl` is not in the packaging script's paper-file extension whitelist,
> so without that assertion a reader who extracts the reproducibility archive
> and runs `pdflatex` gets `No file main.bbl` and 96 undefined-citation
> warnings, and the documented BibTeX-free path does not exist there. The fix
> ships the file rather than narrowing the claim: `collect()` in
> `paper/is2/tools/make_release_zip.py` adds each document's `.pdf`, `.log` and
> `.bbl` under an assertion that fails the build if any is missing, so the
> archive cannot be packaged without them. Because the files are present in
> both packages, the **cross-package byte-identity comparison of §6.2 covers
> them automatically** and the two copies cannot diverge.

## 2. Reference environment (the one that produced the shipped PDF)

| component | value |
|---|---|
| engine | `pdfTeX 3.141592653-2.6-1.40.25` |
| distribution | **MiKTeX 24.1** (`MiKTeX-pdfTeX 4.18`) |
| format | `pdflatex 2026.6.28` (preloaded) |
| LaTeX kernel | `LaTeX2e <2023-11-01> patch level 1` |
| L3 layer | `L3 programming layer <2024-01-04>` |
| bibtex | `MiKTeX-BibTeX 4.1 (MiKTeX 24.1)` |
| TEXMF root | `D:\MiKTeX\tex\latex` (+ user tree under `%APPDATA%\MiKTeX`) |
| OS | Windows 10 Pro 10.0.19045 (x86-64) |
| Python (figures, tables, analysis) | 3.10.9 — the interpreter of `BUILD_INTERPRETER.md`, the only version the analysis lock is tested on |

Get the first two on any machine with `pdflatex --version`, and resolve any
individual package with `kpsewhich <name>.sty`.

### 2.1 Document class and package versions

Read off the reference build's `main.log` (`Package: <name> <date> <version>`
lines). A rebuild that loads different versions of the *layout-affecting*
packages — the first block below — is the expected cause of a page-count
difference.

**Layout-affecting (pin these first if the page count differs):**

| package | version as loaded |
|---|---|
| `cas-sc` (document class) | 2024/05/04, 2.4 — Elsevier CAS single-column |
| `article` (base class it builds on) | 2023/05/17 v1.4n |
| `geometry` | 2020/01/02 v5.9 |
| `stfloats` | 2025/06/18 v3.4 |
| `longtable` | 2023-11-01 v4.19 |
| `array` | 2023/10/16 v2.5g |
| `colortbl` | 2026/05/01 v1.0l |
| `booktabs` | 2020/01/12 v1.61803398 |
| `makecell` | 2009/08/03 V0.1e |
| `multirow` | 2024/11/12 v2.9 |
| `dcolumn` | 2023/07/08 v1.06 |
| `footmisc` | 2025/05/09 v7.0b |
| `wrapfig` | 2003/01/31 v3.6 |
| `lastpage` / `lastpage2e` / `lastpageclassic` | 2025/08/14 v2.1h |
| `stix` (text and math fonts) | 2018/04/17 v1.1.3-latex |

**Math, citations, graphics, hyperlinks:**

| package | version as loaded |
|---|---|
| `amsmath` | 2023/05/13 v2.17o |
| `amssymb` / `amsfonts` | 2013/01/14 v3.01 |
| `amsthm` | 2020/05/29 v2.20.6 |
| `mathtools` | 2024/10/04 v1.31 |
| `natbib` | 2010/09/13 8.31b |
| `graphicx` | 2021/09/16 v1.2d |
| `graphics` | 2022/03/10 v1.4e |
| `pdftex.def` | 2022/09/22 v1.2b |
| `xcolor` | 2023/11/15 v3.01 |
| `color` | 2022/01/06 v1.3d |
| `hyperref` | 2023-11-26 v7.01g |
| `nameref` | 2023-11-26 v2.56 |
| `url` | 2013/09/16 ver 3.4 |
| `fontenc` | 2021/04/29 v2.0v |
| `xstring` | 2023/08/22 v1.86 |
| `etoolbox` | 2020/10/05 v2.5k |
| `verbatim` | 2023-11-06 v1.5v |
| `moreverb` | 2008/06/03 v2.3a |

The manuscript loads **68 distinct packages and document classes**, and that
list is recoverable from `main.log` in this directory:

```
grep -oE '^(Package|Document Class): [A-Za-z0-9@._-]+' main.log \
  | sed 's/.*: //' | sort -u          # 68 distinct names
```

Read the count carefully: 68 is the number of *distinct* `Package:` /
`Document Class:` names. The broader recipe

```
grep -cE '^(Package|Document Class|File|Class): ' main.log     # 106
```

returns 106, because it also matches `File:` and `Class:` events and counts a
package once per load event rather than once per package; and the narrow
recipe without `sort -u` returns 69, one `Document Class:` line plus 68
`Package:` lines with one package announced twice. All three numbers are true
of different things. Printing the 68 beside the 106-line command would invite
the reader to run it and find a number that does not match the prose, so each
count here is printed with the command that returns it.

Both `.log` files **ship** — at `paper/main.log` and
`supplement/supplement.log` in the review ZIP, and at
`paper/is2/paper/main.log` and `paper/is2/supplement/supplement.log` in
`release_archive.zip`, in each case the log of the very build whose PDF sits
beside it. This section and §6 both supply `grep` commands against them, and a
`grep` recipe aimed at a file neither package contains is no recipe at all, so
both are shipped and `make_release_zip.py` raises rather than packaging
without them. Only those two: the `r*p*.log` build transcripts in the same
working directory are scratch and are not packaged.

### 2.2 One machine-specific shim, and why it is in the source

`main.tex` carries, immediately after `\documentclass`:

```latex
\makeatletter
\@ifundefined{insert@pcolumn}{\let\insert@pcolumn\insert@column}{}
\@ifundefined{do@row@strut}{\let\do@row@strut\relax}{}
\makeatother
```

This is a `colortbl`/`array` version-mismatch guard: on this MiKTeX install
`colortbl 2026/05/01 v1.0l` expects `array` internals that the loaded `array
2023/10/16 v2.5g` does not define, and without the shim **every `p{...}` column
in the document fails**. Both `\@ifundefined` tests make it a no-op on an
install whose two packages agree, so it is safe to leave in place on any
environment. If your rebuild errors inside a `tabular` with an undefined
`\insert@pcolumn`, this is why, and the shim is the fix.

## 3. Expected output of the reference build

One column per document. Every row is interpolated from that document's
own build products by `paper/is2/tools/build_env_section3.py`; nothing in
the block is transcribed, and `--check` fails the release build if the
block and the products disagree.

<!-- BEGIN GENERATED SECTION 3 -- build_env_section3.py -->

<!-- Every row below is INTERPOLATED from the build products by
     paper/is2/tools/build_env_section3.py.  Do not edit by hand:
     `python build_env_section3.py --check` fails the release
     build if this block and the products disagree.  A typed
     checksum or size row here ships one build stale the first
     time either document is rebuilt without it. -->

| property | `paper/main.pdf` (article) | `supplement/supplement.pdf` |
|---|---|---|
| pages | **40** | **59** |
| `.pdf` size | 1,455,332 bytes | 1,061,627 bytes |
| `.pdf` SHA-256 | `a51dce5b6b431d06a21f4b433ca3534da4b16140fb0b6c3e71fe7b9f57742cf1` | `e3b5cf0370a203e57bdc6016ec087adcd15edcd84a9413ad7a0eef1e52e24553` |
| `.tex` SHA-256 | `970c22d576796a56442dbb31fa00928c0cb3d941d4c3dee6d312a4858a6d9352` | `4d651ad8c908ce404c171056a280e210fd9726f251f31582c59c6501d8f1e6a6` |
| `.bbl` SHA-256 | `8637a5ee0f1e699cc11e02e68033b256e40955675e1188da7c98f615d9b016e2` | `e7d1f1f28f9177d96d46e0b7e36a8cbdb325e445f449dec268a811eb924dbecb` |
| LaTeX errors | 0 | 0 |
| undefined references / citations | 0 | 0 |
| multiply-defined labels | 0 | 0 |
| `.log` size / SHA-256 | 40,619 bytes / `c7d9894eaac56856518c06ebdfde2f40e076feef9ce4738f381b4e54833d1539` | 28,127 bytes / `7966a2d21f865ab3e562e323eaaecda02f66c10bdbfb34779a718dc36774edc7` |
| final-page footer | `Page 40 of 40` (verify this; see section 1) | none (the supplement carries no journal front matter) |

The values above are **generated at package time from the two documents' own `.pdf`, `.log`, `.tex` and `.bbl` files**, not transcribed; the error, undefined-reference and multiply-defined censuses are computed by the same tests section 6 runs, so this table and that gate cannot disagree.

The PDFs are **not** bit-reproducible across runs: `pdftex` stamps
`CreationDate`/`ModDate` and an `/ID`, so the SHA-256 values above
identify *these* builds, not the class of correct builds. Set
`SOURCE_DATE_EPOCH` and `\pdfsuppressptexinfo` if you need a byte-stable
comparison. What *is* stable across runs on this environment is the page
count, the float placement and the cross-reference numbering, which is what
a reader's check needs.

<!-- END GENERATED SECTION 3 -->

### 3.1 Page-count drift on a rebuild — known and expected

An independent rebuild of a `cas-sc` source tree on another machine has
produced a document two pages longer than ours, with no substantive text
difference and no undefined references on either side. That is float and
environment drift, and it is the ordinary consequence of rebuilding a
float-dense `cas-sc` document under a different TeX tree. Concretely, the page
total is sensitive to:

* the `cas-sc` class version (2.4 here) and the `stix` font metrics — different
  metrics change line counts and therefore where each `[t]` float lands;
* `stfloats` (float placement across the page bottom) and `footmisc` (footnote
  layout on the title page);
* `longtable` and `colortbl`/`array`, which govern the wide tables — a
  one-line difference there moves a page break;
* whether the fifth `pdflatex` pass was run at all (see §1.1): stopping early
  leaves `\pageref{LastPage}` unresolved and can change the last page.

**No number, claim, figure or table changes with the page count.** To confirm a
rebuild is substantively identical rather than merely similar, compare the text
layer, not the page total:

```
pdftotext -layout main.pdf - | tr -s ' \n' ' \n' > rebuilt.txt
# diff rebuilt.txt against the same extraction from the shipped main.pdf
```

The page totals are in the generated table of §3 and are not repeated here; a
number repeated beside a generated one is a number that will eventually
disagree with it.

**The article's page budget is a hard constraint, not an observation.** The
target is a regular Information Sciences article: nominally 40 pages including
references and a slim appendix, with 41 as the accepted ceiling. The
supplement has no page budget. A rebuild that lands one page over on a
different TeX tree is drift and is not a defect of the source; a source edit
that lands over is, and the remedy is the edit, not the ceiling.

> **Why the cross-reference gate reads the rendered PDF.** A build of a
> document can ship carrying one cosmetic defect: an unresolved cross-reference
> in a table caption, rendering as `(Section ef{sec:exp-e2})` instead of
> `(Section 6.2)`, from a stray carriage return in place of the backslash of
> `\ref` introduced by a scripted edit to the caption sentence; `pdflatex`
> reports no error at all because `ef{sec:exp-e2}` is valid text, and the page
> count, footer and error/undefined counts are identical to a clean build.
> Nothing but a scan of the rendered text layer separates the two, which is why
> the gate reads the PDF rather than the log (see §6).

## 4. Build warnings: disposition

Both documents report **0 errors, 0 undefined references, 0 undefined
citations, 0 multiply-defined labels** (the generated table of §3 is the
authority on those four counts; they are read out of the two `.log` files by
the same tests §6 runs).

A *sized* overfull box has to be either resolved or visually approved before
shipping: an undispositioned one means a page may be clipped with nobody
having looked. Badness-only `\hbox`/`\vbox` warnings, which carry no dimension,
carry no risk of clipping and are not tracked individually.

<!-- BEGIN GENERATED SECTION 4 -- build_env_section3.py -->

<!-- The box census and the placeholder-status sentences below
     are INTERPOLATED by paper/is2/tools/build_env_section3.py:
     the boxes from the two .log files, the affiliation-field
     status from the two .tex sources.  Do not edit by hand.
     Typed, they shipped stale in both directions at once -- a
     count that a rebuild had moved, and a `commented out and
     restorable' description of fields the source had active. -->

**A fresh build of this tree emits 1 sized overfull box in the article and 0 in the supplement.**

| document | box | size | located at |
|---|---|---|---|
| article | `Overfull \hbox` | 117.08 pt | detected at line 172 |

1 of these is the **front-matter** box `cas-sc` emits at `\maketitle` (main.tex line 172, read from the source) out of the author block. Its size is invariant to shortening any single field and it is produced by the class's front-matter assembly rather than by a paragraph of ours; this build carries the real author metadata, so it is that build, and the box did not move: it is the same 117.08 pt under the authors' names, ORCIDs, e-mails, CRediT lists and affiliation as it was under the placeholders, which is the invariance the paragraph above predicts. The title page of both documents was rendered and inspected on this build and carries no overflow, clipping or collision, and its ink clears every physical page edge, so the box is dispositioned as producing no visible overflow rather than tolerated undispositioned.

**Placeholder status, read from the source rather than described.** `paper/main.tex` carries **no** placeholder field on a live line: the author names, ORCIDs, e-mail addresses, CRediT role lists and the affiliation are the submission values. The affiliation fields set on live lines are `city`, `country`, `organization`. Fields present only inside comments: `organization`.

The supplement's own front matter carries no placeholder field on a live line either; its centred title block prints the article's title, authors and affiliation.

<!-- END GENERATED SECTION 4 -->

Boxes that were **resolved at their source** rather than tolerated, and
that must stay resolved: a 47.75 pt box in the proof of the $K$-class
calibration bound, where an integrability chain set inline had no interior
break point (the chain is now a display: same symbols, same order, same
argument); a 6.64 pt box in the source-training protocol, from a line whose
only break candidates were `Ko-modakis` and `ResNet-` (a breakable slash in
`entropy\slash pseudo-label` and three discretionary hyphens supply earlier
break points); and the boxes introduced by the release-archive path names
that the supplement now points at, each of which carries `\allowbreak` at
its separators for the same reason.

## 5. Regenerating the figures and tables the build consumes

The two documents consume PDFs and `.tex` fragments under `paper/figures/`.
They are not rebuilt by `pdflatex`; regenerate them from the reproducibility
archive before building if you want an end-to-end reproduction. `COMMANDS.md`
in the archive carries the exact list and order.

**There are two artefact classes here, and only one of them has a generator.**
Nine artefacts under `figures/` are *measurement* artefacts: a script reads a
record file and writes the PDF or `.tex` fragment, and the guarantee a reader
is given is that re-running the script reproduces the shipped bytes. Three are
not. Main Figures 1--3 are **author-drawn mechanism figures** -- schematics of
the protocol, the hard-pair construction and the entropy identity -- whose
source of record is vector artwork, not a script and not a record file. They
plot nothing measured, so there is no generator to name, no `--check` to run,
and no record to bind them to; what stands in place of a generator is the
conversion documented immediately below the table. They are listed in their
own block so that the empty generator column reads as a property of the class
rather than as a missing entry, and `make_release_zip.check_no_output_collisions`
asserts that no live generator claims any of their three basenames -- a
generator that did would replace author artwork with a plot on the next bulk
re-run of the figure directory.

One artefact still ships without being typeset by either document: it mirrors
a released record rather than carrying evidence for a claim, so it lives in
the reproducibility release and is `--check`ed exactly as before.

**Do not read the middle column as a fact about this file.** It is a fact
about the two document trees, and the authoritative form of it is one grep
against the sources this package ships:

```
grep -rn 'figures/' paper/sections/*.tex supplement/*.tex
```

An artefact is typeset exactly when that output contains an
`\includegraphics` or `\input` of it, in the tree of the document that
typesets it. The other hits are not consumption: two are the supplement's
`\graphicspath`/`\input@path` search-path lines, which name no artefact, and
the rest are source comments and a `\texttt` path inside prose. Every row
below whose artefact has a consuming hit is typeset; every row whose artefact
has none is **not typeset**. A row here once read "release only" of a fragment
the supplement `\input`s, which is why the executable form is given first.

**Not typeset is not the same as not shipped, and this column says only the
first.** The one untypeset artefact below ships in *both* packages, and
`make_release_zip.py` asserts its presence: `S4_e1_gates.tex`, so that the
release's `tab_s4_e1_gates.py --check` has a target. `F8_domains.pdf` carries
presence assertions of its own for a separate reason recorded below, and they
are unaffected by its being typeset. "Release only" is the wrong phrase for
that column and is not used in it: as a statement about typesetting it would be
true of one row, and as a statement about shipping it would be false of every
row.

Measurement artefacts, each with a generator of record:

| artefact | consumed by | generator |
|---|---|---|
| `F1_curves.pdf` | article, Fig. 4 | `experiments/ttt/is_fresh/fig_f1_curves.py` |
| `F2_phase.pdf` | article, Fig. 5 | `experiments/ttt/is_fresh/fig_f2_phase.py` |
| `F4_e2_phase.pdf` | article, Fig. 6 | `experiments/ttt/is_fresh/fig_f4_e2.py` |
| `F6_calib.pdf` | article, Fig. 7 | `figures/scripts/fig_F6.py` |
| `F8_domains.pdf` | article, Fig. 8; also pointed at by supplement §S9.4 | `experiments/ttt/is_fresh/fig_f8_domains.py` |
| `F5_batch.pdf` | **supplement**, S9.2 (E2 batch mechanics) | `figures/scripts/fig_F5.py` |
| `S7_e4_proxy.tex` | **supplement**, S9.3 (E3 per-domain proxy table) | `paper/is2/tools/tab_s7_e4_proxy.py` |
| `S5_e2_batch.tex` | **supplement**, S9.2 (E2 batch mechanics) | `paper/is2/tools/tab_s5_e2_batch.py` |
| `S4_e1_gates.tex` | not typeset; ships in both (E1 gate table) | `paper/is2/tools/tab_s4_e1_gates.py` |

**Two rows above were corrected rather than carried forward.** `F8_domains.pdf`
and `F5_batch.pdf` were both listed as "not typeset". The grep printed above is
the authority on that column and it contradicts both: `experiments.tex` carries
an `\includegraphics` of `F8_domains.pdf` inside a captioned figure environment,
and `s8_full_results.tex` carries one of `F5_batch.pdf`. The rows are now what
the grep says. Nothing about *shipping* changes -- both files shipped before
and ship now, and the presence assertions on `F8_domains.pdf` described below
are untouched; what was wrong was only the claim that no document typesets
them.

Author-drawn mechanism figures. **No generator, by construction** -- see the
paragraph above the table:

| artefact | consumed by | source of record |
|---|---|---|
| `fig_mech_1_phase_law.pdf` | article, Fig. 1 (§3.2, the phase law) | `paper/mechanism_figures/1.svg` |
| `fig_mech_2_information_boundary.pdf` | article, Fig. 2 (§4, the hard pair) | `paper/mechanism_figures/2.svg` |
| `fig_mech_3_entropy_alignment.pdf` | article, Fig. 3 (§5, the entropy identity) | `paper/mechanism_figures/3.svg` |

**The conversion, which is what these three have instead of a generator.** The
`.svg` sources are vector throughout -- no embedded raster, no metadata -- and
`pdflatex` cannot include SVG, so each is converted once to PDF. The route on
the build machine was **cairosvg 2.9.0 under the pinned interpreter** of
`provenance/BUILD_INTERPRETER.md` (CPython 3.10.9, Anaconda); Inkscape and
`rsvg-convert` are not installed there, and `cairosvg` was already present, so
nothing was installed for the conversion and the pinned environment is
unchanged.
The output is genuine vector: embedded TrueType/CFF subsets, **zero raster
XObjects** in all three (`pdfimages -list` returns no rows), and the text layer
extracts. Each page box is the drawing's own ink bounding box plus a small
uniform pad, so no `pdfcrop` pass -- and so no ghostscript dependency -- is
involved.

**The conversion is in the tree, not only in this prose.**
`paper/is2/tools/svg_to_pdf_mechfigs.py` performs it, and

```
python paper/is2/tools/svg_to_pdf_mechfigs.py --check
```

re-converts into a temporary directory and compares against the three shipped
PDFs. On the build machine all three come back **byte-identical**. That check
is deliberately not part of `gates.sh`: byte identity across *machines* is not
promised and is not claimed anywhere, because the output embeds subsets of
system fonts and a different Cambria or Calibri build yields different bytes
for the same drawing. What it is for is the same machine, where a silent drift
between the artwork and the shipped PDF is exactly what it catches.

Two properties of the sources needed handling and are recorded rather than
left to be rediscovered:

* **One glyph does not survive cairo's toy text API.** `U+1D4AC MATHEMATICAL
  SCRIPT CAPITAL Q` -- the instance class $\mathcal{Q}$, in figure 2 only --
  is astral-plane, and the cairo build here maps it to `.notdef`; the BMP
  script letters in the same figures (`U+2112`, `U+2115`) are unaffected.
  Before conversion, and **in a temporary copy only**, that one `<text>` run is
  replaced by the same glyph's outline taken from the font the element already
  names (Cambria Math), emitted as an SVG `<path>` at the same baseline origin.
  Same font, same glyph: the substitution changes the encoding of the mark and
  not the mark. Headless Chrome renders the glyph correctly and was the
  alternative route, but it emits a **Type 3** font in figure 3, which is worse
  for an Elsevier submission than this substitution is.
* **The delivered SVGs are never written to.** They are the authors' source of
  record and stay where they are, under `paper/mechanism_figures/`. The release
  archive carries all three (`MECHFIG_SOURCES` in `make_release_zip.py`
  asserts, for each, that the source is present *and* that the PDF it converts
  to is in the payload). The delivery note beside them, `README.md`, is
  deliberately **not** shipped: it documents an earlier raster pipeline that
  the vector files supersede, and it is written in the review-process
  vocabulary the leak gate exists to keep out of what a reader receives.

**One number is drawn inside a figure and cannot be reached by `\ref`.**
Figure 3, panel c prints the literal string `under Assumption 5.4`. It is
correct in this build, and the caption carries the same pointer as a `\ref` so
the two can be compared on the page -- Assumption 5.4 is typeset a few lines
below the figure. It is the only hardcoded statement number in any of the
three, and if the shared statement counter of §5 ever moves, `3.svg` has to be
re-exported.

`tools/r9_reconcile.py` scans any `.tex` fragment under `figures/` that no
document `\input`s -- as of this build, `S4_e1_gates.tex` alone -- as the
`archive` location class, so every number it carries is still bound to its
record and a deletion would surface as an orphan, not as silence. The set is
**derived** from the two documents' own `\input`s and not typed, so a fragment
that comes back into a document stops counting as archive on the next run.
The three author-drawn figures are outside all of this: they are PDFs, they
print no number the reconciler could bind, and their captions quote only
quantities the theorems they cite state.

Three of them carry corrections or constraints that a stale copy would
silently undo:

* `F2_phase.pdf` — its legend must read "Thm. 9", the article's number for the
  executable one-step criterion.
* `S4_e1_gates.tex` — the E1 gate table is the **five**-part table, not the
  six-part table of the frozen `paper/is/` tree:
  the stopping-rule diagnostic row is gone and the remaining parts are
  relettered. `paper/is2/tools/tab_s4_e1_gates.py` is its generator, and
  `--check` is a **byte** comparison against the shipped `.tex`, not a
  digit-by-digit one — a relettering that left the numbers alone would pass the
  weaker test. `experiments/ttt/is_fresh/tab_t4_e1_gates.py` generates the
  six-part table and is not the generator of anything in this submission.
* `S7_e4_proxy.tex` — the per-domain proxy table is supplement **Table S7**,
  and it is **not** the frozen `paper/is/` tree's `T6_e4_proxy.tex`: it prints
  the manuscript's relative-noise symbol `\sigma^2_{rel}` rather than the
  solvable model's `\sigma^2`, carries this submission's label, and is set in
  **two blocks at the supplement's own type size** instead of seven columns
  scaled to the text width. Its generator of record is
  `paper/is2/tools/tab_s7_e4_proxy.py` and its `--check` is a **byte**
  comparison. `experiments/ttt/is_fresh/tab_t6_e4_proxy.py` generates the
  frozen tree's copy, compares numeric tokens only, and is not the generator
  of anything in this submission.

**The figure generators write into the frozen tree by default.**
`fig_f1_curves.py`, `fig_f2_phase.py` and `fig_f4_e2.py` carry an `OUT_DEFAULT`
that points into `paper/is/paper/figures/`, because that is where they wrote
when they were run. Running one without an explicit output path therefore
updates the frozen tree and leaves this one untouched. Pass the `is2` path, or
copy the result afterwards.

**One figure carries a presence assertion of its own.** The E3 per-domain
scatter `F8_domains.pdf` is in the submission archive as
`paper/figures/F8_domains.pdf`
and in the release as `paper/is2/paper/figures/F8_domains.pdf`. A package that
withheld it would be withholding a scientifically relevant figure without
grounds: the submission names and fully specifies the selection rule behind
its $y$-axis (supplement §S6.3) and the axis label is neutral, so no
disclosure reason applies. The article typesets it as Figure 8 and supplement
§S9.4 additionally points at it, and it
adds no quantity to the record, every number it plots being in article Table 2
and supplement Tables S2 and S3. `make_release_zip.py` asserts its
**presence** twice, once over the collected payload and once over the finished
archive's member list (`D6_REQUIRED`), so the pointer cannot silently stop
resolving. **No sentence anywhere in this document, in `COMMANDS.md` or in
either package may describe this file as absent, excluded or not shipped**;
each such sentence would be false of the packages built by the current
scripts, and the two presence assertions are what makes the prohibition
checkable rather than a promise.

## 6. Verifying a rebuild

**`paper/is2/tools/gates.sh` is the implementation of this section.** The
recipe below is what it runs, printed so that a reader can run it by hand or
audit the script against it; the script is the authority, and any divergence
between the two is a defect in this document rather than in the script. It
takes no arguments, resolves every path from its own location, prints one
`ok`/`FAIL` line per check, and exits non-zero if any check fails. It needs
`pdftotext` and `pdfinfo` on the path.

```
bash paper/is2/tools/gates.sh          # ends "ALL GATES GREEN"
python paper/is2/tools/r9_reconcile.py # the number reconciliation, below
```

The six gates it runs, over **both** documents:

1. **build gate** — 0 LaTeX errors, 0 undefined references or citations, and
   no `There were undefined` line, in each `.log`;
2. **rendered cross-reference artefact gate** — no `ef{`/`qref{`/`ite{`/`abel{`
   and no `??` in either document's text layer (§6.1);
3. **process-vocabulary gate** — the hard phrase set of §6.3, over the rendered
   text of both PDFs;
4. **stray-CR sweep** — no carriage return outside a CRLF pair in any `.tex`,
   `.bib`, `.md` or `.txt` source of either document;
5. **duplicate-line gate** — no two consecutive identical non-blank source
   lines, which in a manuscript are always an editing accident. Fenced code
   blocks in `.md` files are exempt, because a build recipe legitimately
   repeats one command line four times and repetition there is content; that
   exemption is declared in `source_hygiene.py` and nowhere else;
6. **tab gate** — no literal TAB in any `.tex` source.

Gates 4–6 are `paper/is2/tools/source_hygiene.py`, which `gates.sh` invokes.

### 6.0 The same checks by hand, from an extracted archive

**Working directory: the archive root** — the directory that contains
`MANIFEST.json` after extracting `release_archive.zip`, which is also the
repository root and has the same layout. **Every** command below is written
relative to that one directory and the block runs top to bottom without any
`cd`; a block whose commands silently assume different working directories
cannot be run as printed from anywhere. The scripts locate their own inputs
from `__file__`, so invoking them by path is enough.

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f MANIFEST.json)")"   # = archive root = repo root

# `grep -c` exits 1 when the count is 0 -- which is the PASSING case for every
# count in this block -- so under `set -e` a bare `grep -c` aborts the script
# on success.  Take every count through this helper, which prints the count
# and always exits 0; the assertion is the printed number, not the status.
count() { grep -c "$@" || true; }
countE() { grep -cE "$@" || true; }
countP() { LC_ALL=C.UTF-8 grep -ciP "$@" || true; }

# 0. all six manuscript gates at once, over both documents
bash paper/is2/tools/gates.sh                     # ends "ALL GATES GREEN"

# 1. numbers: every curated headline claim against the JSON of record,
#    scanned across BOTH documents, with the orphan check
python paper/is2/tools/r9_reconcile.py   # prints its own claim count;
#                                        # expect 0 mismatches, 0 orphans

# 2. generated tables: shipped .tex vs a fresh generation
python paper/is2/tools/tab_s4_e1_gates.py --check          # supplement S4
python paper/is2/tools/tab_s5_e2_batch.py --check          # supplement S5
python paper/is2/tools/tab_s7_e4_proxy.py --check          # supplement S7

# 3. generated blocks of THIS file vs both documents' build products
python paper/is2/tools/build_env_section3.py --check

# 4. build: 0 errors, 0 undefined, converged, footer correct
count  '^!' paper/is2/paper/main.log                              # expect 0
countE 'undefined (references|citations)' paper/is2/paper/main.log      # 0
count  'There were undefined' paper/is2/paper/main.log            # expect 0
count  '^!' paper/is2/supplement/supplement.log                   # expect 0
countE 'undefined (references|citations)' \
       paper/is2/supplement/supplement.log                        # expect 0
pdftotext -layout paper/is2/paper/main.pdf - \
  | grep -o 'Page [0-9]* of [0-9]*' | tail -1        # `Page N of N`, N = §3

# 5. rendered-PDF gates on each document: cross-reference artefacts (6.1)
#    and the process-vocabulary sweep (6.3)
for pdf in paper/is2/paper/main.pdf paper/is2/supplement/supplement.pdf; do
  pdftotext -layout "$pdf" - > rendered.txt
  countE '(^|[^A-Za-z])(ef|qref|ite|abel)\{' rendered.txt        # expect 0
  count  '??' rendered.txt                                       # expect 0
  countP 'referee|reviewer|earlier form of this|(?<![A-Za-z])rounds?\b(?!ed|ing)|external review|this round|last round|this revision|previous version|earlier versions?|earlier revisions?|earlier draft|prior version|we previously' rendered.txt
done                                                             # expect 0
rm -f rendered.txt

# 6. archive hygiene: the parser-based absolute-path gate (6.4), read-only
python paper/is2/tools/make_release_zip.py --check-paths .
#                                          # ends "absolute-path gate VERIFIED"
```

`readlink -f` is GNU coreutils; on a shell without it, `cd` to the extracted
archive root by hand. Step 6 writes nothing: `--check-paths` runs the gate
alone against the tree you are standing in. Running `make_release_zip.py` with
no arguments instead rebuilds the archive and runs the whole verification
suite, of which this gate is one item.

> **What that suite verifies in full, and what it verifies only at reduced
> parameters.** Its integrity half is full: every payload re-hashes from a
> clean extraction, every declared identity holds, every path and
> documentation gate passes, and three shipped artefacts — supplement Tables
> S3 and S4 and the generated blocks of this file — regenerate at published
> parameters and are compared, S4 byte for byte. Its numerical half is
> **reduced**: five recomputations run at cut-down draws and single bootstrap
> streams, two of them under `--no-audit` because a reduced result must not be
> compared with the archived record. **A passing run is therefore not a
> regeneration of the published numerical endpoints.** Those come from the
> *default* invocations in `COMMANDS.md`, with no reduction flags, under which
> each script's own audit compares its output against the archived record.
> `experiments/ttt/is_fresh/VERIFY_TRANSCRIPT.md` in the archive carries a
> complete verification run on the pinned Python 3.10.9 with its exit code.
> That transcript's currency is **derived, not asserted**: `verify()` parses
> the transcript out of the extracted archive and binds its declared payload
> count, ZIP-entry count and path-exception count to what the archive it is
> shipping in actually contains, so a transcript describing a different
> package fails the build that would ship it. It records the immediately
> preceding build, which differs from the shipped one in that one file alone —
> a ZIP cannot contain a transcript of a run against itself — which is why the
> gate binds counts rather than digests.

Match the *undefined-reference* warnings specifically, not the bare word.
A plain `grep -c 'undefined' main.log` returns a nonzero count on a correct
build and always has: those lines are

```
LaTeX Font Warning: Font shape `T1/stix/m/scit' undefined
(Font)              using `T1/stix/m/sc' instead on input line NNN.
```

— the STIX text family has no small-caps italic, so LaTeX substitutes upright
small caps. That is a font substitution, not a broken reference, it is
expected, and it is unrelated to `\ref`/`\cite` resolution. The bare-word form
with an expected count of 0 is therefore a command that fails on a correct
build; since both `.log` files ship, a reader can run what is printed here, so
what is printed here has to be true of the files they have.

### 6.1 The rendered-PDF cross-reference gate

`grep`ping `main.log` is **not sufficient**. A stray carriage return
substituted for the backslash of `\ref` leaves `ef{sec:exp-e2}` in the source;
that is ordinary text, so `pdflatex` exits 0, reports no undefined reference,
and ships a caption reading `(Section ef{sec:exp-e2})`. Only the *rendered*
page shows the defect. A gate therefore extracts the text layer of the built
PDF and fails on the artefacts that class of error leaves:

```
pdftotext -layout main.pdf - > rendered.txt
grep -nE '(^|[^A-Za-z])(ef|qref|ite|abel)\{' rendered.txt   # expect no match
grep -n '??' rendered.txt                                   # expect no match
```

It runs on **both** documents, not only the article: the supplement resolves
the article's objects through `\Main…` macros, so a macro that lost its
backslash renders as ordinary text there in exactly the same way.

The same gate re-checks the final-page footer against the true page count from
`pdfinfo`, and sweeps every `.tex`, `.bib`, `.md` and `.txt` source of both
documents for a CR that is not part of a CRLF pair — the mechanism that produces that class of
defect in the first place. That sweep is not redundant: it once found a
further instance in this file, where the sentence in §3 describing the defect
had itself lost the backslash of `\ref` to a carriage return. It is fixed.

### 6.2 Package build order and the cross-package identity check

`release_archive.zip` embeds a copy of the manuscript sources, and the review
ZIP ships the same files. An archive built *before* a last documentation edit
leaves its copy of a shared file one generation behind the copy in the review
package. Two rules prevent that:

1. **no package is built until every documentation and manuscript edit is
   final**, and the archive is rebuilt whenever any file it contains changes;
2. after both packages exist, `paper/is2/make_review_zip.py` compares **every
   file the two packages hold in common under a declared path mapping** and
   asserts that each pair is byte-identical; a mismatch aborts packaging rather
   than shipping two versions of one paper.

**The mapping, now that the submission is two documents.** The review package
roots the article at `paper/` and the supplement at `supplement/`; the archive
roots them at `paper/is2/paper/` and `paper/is2/supplement/`. The mapping is
therefore review-package `paper/X` ↔ archive `paper/is2/paper/X`, review-package
`supplement/X` ↔ archive `paper/is2/supplement/X`, plus the one out-of-tree
pair `FRESH_RESULTS.md` ↔ `experiments/results/is_fresh/FRESH_RESULTS.md`. It
is a **mapping, not a literal intersection of ZIP path strings**: the two
packages root the manuscript differently, so almost nothing occupies the same
path in both. The count reported for this check is the size of the mapping,
and what is verified of each pair is identical content.

**What that second rule is, precisely.** It is an assertion made **at packaging
time by an author-side build tool** — a check, not a gate.
`make_review_zip.py` lives at `paper/is2/` and is in **neither** package, so it
is not something a reader can invoke from an attachment, and nothing in this
document should be read as claiming otherwise. What a reader *can* do is
re-perform it directly: extract both ZIPs and compare the SHA-256 of every
member of the review package against the member at the mapped path in the
archive. That requires no code beyond a checksum utility, which is why no
comparator is shipped for it. The similarly named check *inside*
`make_release_zip.py`, which does ship and does run in the release
verification, is a different and narrower thing: it compares the two original
generator outputs in the release staging tree against their
`paper/is2/paper/figures/` copies. It does not compare the two packages.

**Determinism.** Both packagers stamp every ZIP entry with a single timestamp
taken from the article's `main.pdf`, rather than with each source file's own
mtime. Without that, two builds from an identical tree produced byte-different
ZIPs whenever a member had merely been rewritten with identical content —
which the generated manifest is, every run. With it the review ZIP is a pure
function of the tree, so "the same tree produces the same archive" is a claim
about content rather than about filesystem metadata, and it is checked by
building twice and comparing the two SHA-256 values.

### 6.3 The review-process leak gate

Editing a manuscript against a report of comments leaves the vocabulary of
that correspondence within reach of the manuscript. The failure mode is
concrete: an appendix sharpness paragraph that describes its own arithmetic
as written for the reader of such a report, or a closing paragraph that opens
"An earlier form of this counterexample". Neither touches a number or a claim,
and no other gate catches either, because both are perfectly
well-formed prose. A gate therefore greps the **rendered text of the built
PDF**, not the sources, for the vocabulary of the review process:

The gate is a Python scan of the extracted text, and the pattern list below is
the one it actually applies — reproduced verbatim, because an abbreviation
such as `round [0-9]` lacks a left token
boundary and therefore also matches inside ordinary prose such as
“around 0.025”: it could not pass as written. Every `round` pattern needs a token boundary on the **left**,
which POSIX ERE cannot express; the gate uses a lookbehind, so the shell
equivalent needs `grep -P`, not `grep -E`:

```
pdftotext -layout paper/is2/paper/main.pdf - > rendered.txt
pdftotext -layout paper/is2/supplement/supplement.pdf - >> rendered.txt

# the HARD set: any hit fails the build.  There is no second, tolerated tier:
# every phrase below, including `previous version`, `earlier version`,
# `earlier versions`, `earlier draft`, `prior version` and `we previously`,
# fails it.
LC_ALL=C.UTF-8 grep -niP 'referee|reviewer|earlier form of this|(?<![A-Za-z])rounds?\b(?!ed|ing)|external review|this round|last round|this revision|previous version|earlier versions?|earlier revisions?|earlier draft|prior version|we previously' rendered.txt

# the ADVISORY set is now EMPTY: there is no phrase the gate tolerates.
```

GNU `grep -P` refuses to run under a non-UTF-8 multibyte locale
(`-P supports only unibyte and UTF-8 locales`); the `LC_ALL=C.UTF-8` prefix
above avoids that. On the reference build the hard set returns **0** hits.
For contrast, the
abbreviated `round [0-9]` form returns **1** hit, on
`... inside [0.0225, 0.0299] around 0.025 ...`, which is precisely the false
positive the token boundary removes.

**Why there is no advisory set.** An *advisory* set with a nonzero expected
count is wrong twice over. First, the expectation is a guess about how many
such passages the rendered PDF contains, and it is routinely low: a
confidence-budget note in the Proposition 52 proof and a sentence such as
"This is the step the previous version got wrong" are two passages where one
was expected. Second, passages of that kind are editorial
commentary rather than mathematical exposition, so tolerating them at all is
the mistake. A tolerated phrase is an uncounted phrase: an expected count
above zero hides every further instance behind it. Prose of that kind is
therefore written to state the mathematical point without referring to any
draft — the even split of the confidence budget is *forced*, and the maximum
$\kappa^\sharp$ is *unavoidable* — as are the drift bound and clause (c1) of
`appendix/proofs_upper_lower.tex`, which invite the same phrasing.
**Expected advisory count: 0. Expected hard count: 0.**

**Why `earlier revisions?` is in the hard set.** `earlier version` does not
match `earlier revision`, and an Appendix C paragraph
describing what an E4 interval construction replaces opens naturally with
exactly that phrase — visible to the reader on rendered page 73 while the gate
returns 0. Such paragraphs are written as timeless prose instead (what the
estimator is, what the alternative endpoint rule would give, and that both
sets of records ship), and `earlier revisions?` is in the hard set above so
that the phrase cannot enter unnoticed. The pattern is printed twice in this document, in §6
and in §6.3; the two printings are identical strings and must stay so.

`(?<![A-Za-z])rounds?\b(?!ed|ing)` is the load-bearing piece. The lookbehind
drops `around`, `background` and `surround`; the `s?` catches the plural; and
the `(?!ed|ing)` lookahead drops `rounded` and `rounding`, which occur
throughout the rounding-convention discussion in Section 7.3 and Appendix C.
The three-word phrases (`this round`, `last round`, `this revision`) are
redundant against that pattern but are kept so a failure names the construction
that produced it.

Expected: **no match** on the hard set. The gate runs on the PDF text layer
and not on the source tree, so `%` comments in the `.tex` sources and the code
blocks in this file — which necessarily quote the pattern itself, and would
otherwise match it — are out of scope by construction. Only what a reader of
the two PDFs sees is tested, and **both** are tested: the supplement is a
distributed document and is inside the claim.

### 6.4 The absolute-path gate

**The claim this gate certifies**, stated before the checker so the two can be
compared:

> Of the entries of `release_archive.zip` that the gate reads — **every JSON
> member, parsed to its string leaves, and every other text member, scanned
> line by line** — none carries a build-machine or run-machine **absolute**
> path *of the syntaxes the gate matches*, except for the files enumerated in
> `ABS_PATH_EXCEPTIONS`: this document, the two verbatim `pdflatex`
> transcripts, the `pip freeze --all` provenance record in both the copies it
> ships as, and the closure suite's own path sanitizer, whose docstring has to
> name the shape of path it strips. The gate prints that list, with a per-file
> reason and count, on every run, and the census below is generated from the
> same run.

Nothing weaker and nothing wider — and the two qualifications in that sentence
are load-bearing rather than decorative, so they are spelled out here:

* **binary members are out of scope.** The gate classifies
  `.pdf .png .jpg .pt .zip .ttf .otf .pyc .npz .npy` members as binary,
  *reports* their count instead of skipping them silently, and does not read
  inside them. The generated census below prints that count. A path embedded
  in a figure PDF or a `.npz` would therefore not be found by this gate; what
  rules it out is that every one of those members is produced by a shipped
  generator from shipped inputs, not that the gate looked;
* **the POSIX recognizer matches a fixed list of machine roots**, not every
  string that begins with `/`: `root`, `home`, `mnt`, `media`, `opt`, `usr`,
  `var`, `tmp`, `Users`, `autodl-tmp`, `content`, `workspace`. An absolute
  path under an unlisted root — `/data`, `/scratch`, `/project`, `/private` —
  would not match. The Windows branch has no such restriction: it matches any
  drive letter and any UNC host/share. The roots listed are the ones the run
  and build hosts actually used, which is why the census is empty outside the
  exceptions; the sentence above claims what was tested, not more.

In particular the claim is **not** "zero absolute paths anywhere", a statement
the records below falsify; it is **not** restricted to result
JSONs, a narrower scope than this section claims; and it is **not**
restricted to the manifested payload, which is narrower again and leaves the
generated root entries outside a claim that names them. A mismatch of
that kind is closed by widening the checker to the claim, never by narrowing
the claim to the checker. No count in this section is hand-typed: the census below is
generated from the gate's own run, and the gate prints the exception table
itself on every run.

The stronger-sounding claim — that a repository sweep finds *zero* absolute
paths in the result JSONs — is false of the records as produced, which is why
it is not made. A parsed scan found **441 absolute-path string fields in
214 of the 447 result JSONs as produced**, all under the run machine's
`/root/autodl-tmp/…` prefix, plus Windows paths in 24 of the 26 current
analysis logs and MiKTeX/user-profile paths in `main.log`. Those counts are
statements about the **unsanitized record corpus as produced**, not about this
archive's payload, which is smaller: they are the size of the problem that was
fixed, and they do not move when the payload does. The census of *this* build
is the generated block at the end of this section, and it is the only number
here that describes the shipped archive. The claim failed
because the checker did not match the claim's scope: the sweep was a
Windows-syntax regular expression over a subset of files, while the claim
quantified over all files and all path syntaxes. **The general lesson, applied
to every gate in this document: a verification pattern must cover the full
scope of the claim it certifies, and a parser beats a regex wherever the data
has structure.**

What was done, and how it was proved safe:

* **214 result JSONs, 441 fields.** The single machine prefix
  `/root/autodl-tmp` was replaced by the placeholder `<RUN_ROOT>` at the byte
  level, so every other byte of every record is untouched. The rewrite was
  then *proved* correct with a parser rather than trusted: for each file the
  before and after trees were parsed, their leaf sets asserted equal, every
  changed leaf asserted to lie at one of the six path pointers
  (`/meta/argv/{out_dir,data_root,ckpt_dir,data_dir,ref_file}` and
  `/clean_val_dir`), each change asserted to be exactly that prefix
  substitution and reversible, and the set of untouched leaves — every number
  in the archive included — asserted identical. **No numeric value changed;**
  `r9_reconcile.py` reports the same claim count with 0 mismatches over the
  sanitized records as over the raw ones.
* **24 analysis logs, 164 paths.** All were `[is_fresh] wrote …` lines and two
  f15 checkpoint lines carrying the build machine's repository prefix. The
  prefix was stripped so the paths read repository-relative, and the two
  emitters — `common.save()` and `f15_e2_entropy_gn.py` — now print through a
  `rel()` helper, so **regeneration is idempotent** and cannot reintroduce
  them. The figure generators and both gate-table generators were given the
  same helper for their `saved …` / `wrote …` lines.
* **12 shipped experiment files, 61 occurrences.** The remote-host GPU runners
  under `experiments/ttt/{e2_cifar,e4_gpt2}`, the E4 job list `jobs_e4.txt`,
  the E4 smoke transcript `SMOKE.md` and the three `e4_gpt2/vec_rerun/`
  drivers were declared exceptions for eleven rounds, on the ground that they
  shipped **unmodified** as the record of what was executed. That ground had
  quietly stopped holding. The result records whose `meta/argv` those defaults
  were said to reproduce have carried `<RUN_ROOT>` since the first bullet
  above, so the shipped scripts were the last place the run host's literal
  prefix survived, and the archive was asserting a byte correspondence with
  the records that no longer existed. The prefix is now substituted here too,
  by the same prefix-only rule and nothing else: `/root/autodl-tmp` → the
  relative `workdir/` (38 occurrences), `/root/miniconda3/bin/{python,pip}` →
  the bare interpreter names (19), and the three `.sh` drivers'
  `R=/mnt/data/Programming/research_ws/TTT` → a **required** `${TTT_ROOT}`
  that aborts with a stated message when unset (4, one of them the
  `os.environ["TTT_ROOT"]` inside `finalize_e3.sh`'s heredoc). Every flag,
  every ordering, every path *suffix* and every seed is byte-identical to what
  ran; only the machine-identifying prefix is gone, and it is recoverable from
  this bullet. The files remain runnable — the seven Python files pass
  `py_compile`, the three shell scripts pass `bash -n`, and each exits 1 with
  its message when `TTT_ROOT` is unset. **No JSON was touched by this pass, so
  no number in the archive could move**; the reconciliation below is over the
  same records as before.
**The declared exceptions, and why each is retained rather than sanitized.**
The gate prints this table itself on every run, and its count of them is in
the generated census below; the per-file counts here are from the shipped
build.

| files | why not sanitized |
|---|---|
| `paper/is2/paper/main.log` | the unedited stdout of `pdflatex`. The "0 errors, 0 undefined references, N output pages" rows of §3 are statements about *that* file, and are read out of it by the generator; editing it would make them claims about a file no engine produced. Ships verbatim, retaining `C:\Users\…` and `D:\MiKTeX\…`. Its retained-path count is printed by the gate, not typed here. |
| `paper/is2/supplement/supplement.log` | the same, for the second document of the pair. §3 carries a supplement column and reads it out of this file. |
| `paper/is2/paper/BUILD_ENVIRONMENT.md` | this file, whose *purpose* is to record the reference build machine. §2 must name the TEXMF root for the build to be reproducible at all, and §6.4 — this section — discloses every other exception **and quotes the prefixes it removed**, which is why this file's own retained count rose when the twelve runners' fell to zero: naming a prefix is how a sanitization is disclosed rather than hidden. Its retained-path count is printed by the gate, not typed here. |
| `experiments/results/is_fresh/closure/code/common.py` | the closure suite's own path **sanitizer**, whose docstring has to be able to name the shape of path it strips in order to say what it does. The suite's records and analysis JSONs are clean precisely because this function ran on them; the only absolute path in the whole closure directory is the one inside the sentence explaining their absence. |
| `pip-freeze-full.txt` | the verbatim `pip freeze --all` transcript of the build interpreter. The conda-prefix and user-site locations in it *are* the provenance record — they are what distinguishes the mixed installation `RESOLVER_TRANSCRIPT.md` section 3 reasons about from a clean one — so rewriting them would destroy the evidence. Nothing installs from this file: the installable pins are `requirements-analysis.txt` and `requirements-experiment.txt`, and both are clean. |
| `paper/is2/provenance/pip-freeze-full.txt` | the payload copy of the root entry above, byte-identical to it by construction. Same reason, same paths, same evidentiary role — stated once and not paraphrased, because two differently worded reasons for one object are a difference a reader has to adjudicate. |

**Two ways an entry leaves this map, and both have now happened.** The
ImageNet-C runner and its job files were nine entries here. They are gone
because the *file* is gone from the payload: this submission does not report
that experiment, so neither its code nor its records ship, and `INDEX.md`
lists that omission with its reason. The twelve experiment-runner, job-list,
smoke-transcript and `vec_rerun` entries are gone for the other reason: the
*files are now clean*, per the third bullet above. The gate asserts both
directions — every file named here must still ship **and** must still contain
at least one absolute path — so neither a removed file nor a cleaned one can
leave a dead exemption behind. This is not a courtesy: an exemption for a
clean file turns the gate red on the next build, which is the gate working
rather than failing.

**No retained path is ever resolved.** Five of the six files are records —
two `pdflatex` transcripts, this document and the `pip freeze --all` output in
its two copies — and nothing in the archive opens them as paths. The sixth,
`closure/code/common.py`, *is* imported by the closure suite, but its retained
path sits inside a **docstring** describing the shape of path the function
strips; the function never constructs it. So a reader never meets a path that
resolves nowhere, and the retained paths are inert in the strong sense: no
code path in the archive reads any of them. **Every retained path is in an
enumerated file; within the scope stated above the count elsewhere is zero.**
The number of exception files and the number of paths they retain are in the
generated census below, printed by the gate that measured them.

The exception list is itself gated. The checker asserts that every declared
exception still ships *and* still contains at least one absolute path, so a
file that has since been cleaned cannot linger on the list as a silent
blanket amnesty — the exemption stays exactly as wide as the facts.

**Why the archive's own `INDEX.md` paragraph is generated rather than
written.** A hand-written copy of a gate's result rots even while the prose it
was copied from stays correct. The `INDEX.md` written into
`release_archive.zip` — and the template that generates it, and the gate's own
header comment in `make_release_zip.py` — must not say the claim holds "with
**exactly one** declared exception, `paper/is2/paper/main.log`". A sentence of
that shape is true when the map holds one entry and rots silently as the map
grows to nineteen, at which point the archive's headline claim contradicts the
gate the same archive ships. The remedy removes the possibility rather than
the sentence: the
sweep is now a reusable census (`abs_path_census`), `check_no_absolute_paths`
is a thin asserting wrapper around it, and `index_md` **calls the same census
and interpolates its counts into the `INDEX.md` paragraph at build time**. No
exception count and no path count is typed into `make_release_zip.py`
anywhere. The generated paragraph also names the gate, not itself, as the
authority, prints the coverage figures of that build's run, and tabulates
every declared exception with its own occurrence count. `index_md` asserts
the census is clean before it will write the paragraph at all, so a build
that would ship a false hygiene claim fails instead.

**There is a second file of that basename, and it is not this gate.**
`experiments/ttt/is_fresh/make_release_zip.py` is the packager of the frozen
`paper/is/` submission. It ships because `experiments/ttt/is_fresh` ships
whole, as the analysis suite as it was run; its path-exception map is written
for that package's layout, so run against the package this submission ships
it reports failures that are artefacts of the layout mismatch and not of the
tree. It is quarantined at its command line — it prints the two commands
below and exits non-zero — and this document names it nowhere else. Every
instruction here, in section 5 and in `COMMANDS.md`, names
`paper/is2/tools/make_release_zip.py`.

The gate itself (`check_no_absolute_paths` in
`paper/is2/tools/make_release_zip.py` — the same script as the command given
in section 5 above, and the only checker this document ever names — run as
item 5 of `verify()` on the extracted tree, and standalone via
`python paper/is2/tools/make_release_zip.py --check-paths .`):

* iterates **every entry the archive ships** — the files listed in
  `MANIFEST.json` *and* the generated root entries beside it — not a
  sample, not one directory. A checker that iterates `MANIFEST.json`
  alone while this section claims the wider property is a scope mismatch, and
  the way to close it is to widen the checker, not to narrow this sentence;
* **parses** each JSON member and tests every *string leaf* of the resulting
  tree, identified by JSON pointer, so a path is caught wherever it sits in
  the structure and regardless of key name, nesting, indentation or line
  breaking;
* scans every non-JSON text member line by line;
* counts binary members (`.pdf .png .jpg .pt .zip .ttf .otf .pyc .npz .npy`)
  as explicitly out of scope and *reports* that count rather than silently
  skipping them;
* matches **both** path syntaxes: twelve POSIX machine roots (`root`, `home`,
  `mnt`, `media`, `opt`, `usr`, `var`, `tmp`, `Users`, `autodl-tmp`,
  `content`, `workspace`, each anchored to a leading slash) and Windows
  drive-letter and UNC host/share paths. Repository-relative paths are not
  absolute and are the intended form;
* carries a lookbehind on the drive-letter branch. Without it the tails of
  `https:`, `arXiv:\allowbreak` and `gate_pass:\ false` all match as drive
  letters, and the gate drowns in false positives from LaTeX and URLs; a real
  Windows path is never preceded by an alphanumeric character. Thirteen unit
  cases pin the boundary in both directions;
* excludes the portable `#!` … `usr/bin/env` shebang by construction — it
  names no machine and resolves everywhere POSIX (the count is in the
  generated census below);
* **does not exempt its own source.** Every pattern fragment in
  `make_release_zip.py` that would otherwise match is assembled from parts at
  import time and the surrounding prose describes the syntaxes in words, so
  the checker is scanned by the same rule as everything else. An exempted
  checker is the hole that makes a hygiene claim unverifiable;
* prints its own coverage — how many JSON members, how many string leaves, how
  many text members, how many binaries, how many shebangs, and the full
  exception table with per-file counts and reasons — so the reader can check
  the gate's scope against the claim rather than taking a number on trust.

<!-- BEGIN GENERATED 6.4 CENSUS -- build_env_section3.py -->

<!-- Every number in the paragraph below is INTERPOLATED from the
     same `abs_path_census` the gate itself calls, by
     paper/is2/tools/build_env_section3.py.  Do not edit by
     hand.  These were typed once and shipped stale
     (447/247,260/135 against a gate reporting 449/247,285/140) -->

On the shipped build it reports: **0 absolute paths outside the declared
exceptions, over 399 JSON members (140,031 string leaves parsed) and 246 text
members; 27 binary members out of scope, 49 portable shebangs excluded; 6
declared exceptions holding 760 matching contexts, which contain 775 absolute-path occurrences.**

A context is one line of a text member, or one parsed JSON string leaf, and it
can hold more than one path, so the two counts differ and each is reported under
its own noun. The load-bearing number is neither of them: it is the **zero**
outside the declared exceptions, and a context count and an occurrence count are
zero together.

Its scope is **all 672 entries** of the archive: the 662 manifested payload
files plus the 10 generated root entries. 399 + 246 + 27 = 672, so every entry falls in
exactly one of the three categories and none is skipped.

> **Why the checker walks every entry.**
> It once iterated `MANIFEST.json` — the
> 662 payload files — while the claim above, and the gate's own header
> comment, quantified over every file the ZIP ships. The 10
> generated root entries were therefore outside the census, and one
> of them, `pip-freeze-full.txt`, holds 268 path-like strings. Three
> artefacts then disagreed about the scope.
> The repair is the wider checker, not the narrower sentence: the
> gate walks every entry, and `pip-freeze-full.txt` joins
> `ABS_PATH_EXCEPTIONS` with its reason recorded like every other —
> a verbatim `pip freeze --all` transcript in which the installation
> locations *are* the provenance evidence, and from which nothing is
> installed (the installable pins are `requirements-analysis.txt`
> and `requirements-experiment.txt`, both clean). The census numbers
> above are larger than a manifest-limited census would report for
> that reason and no other: the delta is SCOPE, not amnesty — no
> exception was widened to produce it, and no file was sanitized to
> produce it either. Sanitization moves these numbers the other way,
> and the one pass that did so — the twelve experiment runners, job
> list, smoke transcript and `vec_rerun` drivers — is recorded in the
> hand-written part of this section, together with the twelve
> exception entries it retired.

<!-- END GENERATED 6.4 CENSUS -->

The `CURRENT VALUES` section at the top of
`experiments/results/is_fresh/FRESH_RESULTS.md` is the authoritative source for
the curated headline and repeated numerical claims that `r9_reconcile.py`
binds to a record of record, together with the construction claims of its
`PASS 1b` check. **Both counts are stated in that section and printed by the
script on every run; they are deliberately not restated here**, because a
count typed beside a gate is a second, unchecked copy of the gate's output,
and a second copy of a number is a number that will eventually disagree with
the first.

> **What this gate does not cover.** It would be wrong to describe the section
> as holding "the authoritative current values for **every number in the
> manuscript**". It does not, and `FRESH_RESULTS.md` and `r9_reconcile.py`
> both say so explicitly: the table is a **curated headline-value and rounding
> audit**, and a claim that was never added to it is not detected by it.
> Quantities that are printed in either document and are **not** bound
> include the E2 leave-one-corruption-out fold intervals and some E2
> conditional calibration proportions. Report the gate as "N curated claims
> checked, 0 mismatches", with N read from the run, and never as "every number
> in the submission is machine-bound". The curated set is widened whenever an
> unbound quantity is caught by other means: 42 rows cover every E4
> interval endpoint, design effect and intraclass correlation, an unbound
> quantity being precisely what an all-green value pass cannot see, and
> further rows cover the quantities beside them.
>
> **The reconciliation scans both documents, and it fails on an orphan.** A
> claim whose printed token appears in *neither* document is a binding whose
> text was deleted, and without that check it would keep passing forever while
> its number stopped being a claim about anything. The run reports where each
> claim binds — in the article, in the supplement, or in both — and a claim
> that binds nowhere fails the run. That check is what a restructuring needs
> and a single-document reconciliation cannot express.
