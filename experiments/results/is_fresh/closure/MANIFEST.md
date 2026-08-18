# Manifest and transfer integrity

Two hash lists, because the staged copies are not byte-identical to what the
compute host produced — and the difference is deliberate, so it is recorded
rather than papered over.

| file | what it hashes |
|---|---|
| `MANIFEST_source.sha256` | the 150 files **as produced on the compute host**, hashed there before transfer |
| `MANIFEST_staged.sha256` | the same 150 files **as they now sit in this directory** |

**Transfer integrity.** All 150 files were verified against
`MANIFEST_source.sha256` immediately after transfer: **150 / 150 matched, 0
mismatches, 0 missing.** The transfer itself was lossless.

**Post-transfer transform.** 29 of the 79 analysis JSONs were then
path-sanitized: `run_meta` recorded absolute paths from the compute host in its
`argv` block, and a shippable artifact must not carry a host account name or a
path that resolves nowhere in an extracted archive. Those 29 files therefore
hash differently in the staged manifest, by design.

* **byte-identical to source: 121 / 150**
* **path-sanitized: 29 / 150** (analysis JSONs only)
* **raw per-episode records altered: 0** — all 71 `.jsonl.gz` files are
  byte-identical to what the runs wrote. No measurement was touched.

The sanitization is idempotent and textual (strip the repository prefix, replace
the interpreter path with `<env-python>`); `common.run_meta` was patched during
the run so later jobs record repository-relative paths natively, which is why
50 of the 79 JSONs needed no transform.

**Files added after the original transfer** (4, so the staged manifest lists 154
where the source manifest lists 150): `json/P2_SOURCE_GATE.json` — the
source-model comparability audit written by this suite — and the three
`json/cifar10_resnet26ttt_s2026092*_train.json` training records it is derived
from, pulled from the checkpoint directory. These have no entry in
`MANIFEST_source.sha256` because they were not part of the results directory at
transfer time.

To re-verify the staged tree:

```
sha256sum -c MANIFEST_staged.sha256
```

---

## Added at manuscript integration

Five things about this directory as it now stands. **No measurement was
touched: all 71 raw record files and all 83 transferred analysis JSONs are
byte-identical to what the runs wrote and to what arrived.**

**1. The two hash lists were rewritten from CRLF to LF line endings.** As
transferred neither could be consumed by `sha256sum -c` at all --- it read the
trailing carriage return as part of each filename and reported every file as
missing --- so the command this document tells you to run failed on every
line. Nothing else about them changed at that step, and every digest verified
unchanged through it.

**2. `MANIFEST_staged.sha256` was then regenerated over the whole directory.**
As transferred it covered `records/` and `json/` only --- 154 entries --- so
the code and the documents beside them were unhashed. It now covers every file
in this directory except the two hash lists themselves: **183 entries, all
verifying.** `MANIFEST_source.sha256` is untouched and remains the record of
the 150 files as the compute host produced them, under that host's flat
filenames; it is a transfer record, not a check that runs against this layout.

**3. Three prose passages were reworded**, in `DESIGN.md`, `RESULTS.md` and
`code/verify_closure.py`. All three named this suite's own design-audit
history in wording that the manuscript package's cold-read gate forbids
anywhere in a distributed archive. The substance is unchanged in each case:
the audits
happened, `DESIGN.md`'s changelog still states every change each one forced,
and `RESULTS.md` still records that an initial implementation of the route-4
harness used an absolute tolerance and what that cost. No number, no finding
and no caveat was altered --- in particular the withdrawn source-model caveat
of section 12 stays withdrawn, on the same evidence.

**4. The two design-audit transcripts do not ship.** `REVIEW_R1.md` and
`REVIEW_R2.md` are process records rather than measurement records, and a
package read cold does not carry another review's transcript. They remain here
and are hashed above; the release packager excludes them by name and states
the reason in its own `INDEX.md`.

**5. Two files were added.** `json/KAPPA_RESTRICTED.json`, written by the new
`code/analyze_kappa_restricted.py` from the records: the suite reports the
Jacobian condition number under the *literal* Loewner reading of Assumption
5.4, while the manuscript states that assumption in the restricted form its
own proof consumes, so the matching condition number had to be computed. Both
readings are in that file, so the gap between them stays visible.
`CLOSURE_RECORDS_MANIFEST.json` is the per-member manifest of the side archive
described next.

**6. `RESULTS.md` §9 was reworded once more**, and this one was a correctness
fix rather than a wording one. Having reported the literal reading, it closed
with "which is why the literal Loewner constant is used throughout" — written
before the manuscript restated Assumption 5.4 on the restricted form, and false
of the submitted manuscript afterwards. §9 now states the split it actually is:
this suite reports the literal constant, the manuscript cites the restricted
one, `json/KAPPA_RESTRICTED.json` carries both per episode, and neither is used
throughout. No measurement changed; the restricted medians (2.15 / 2.36) and
the pooled separation (smallest restricted `κ_J` 1.079 against largest
`κ_crit` 1.035) are read out of that same file. `MANIFEST_staged.sha256`'s
entries for `RESULTS.md` and for this file were recomputed accordingly; every
other digest in it is unchanged, and no `records/` digest is touched by any of
this.

## The raw records are in a side archive

At 127 MB the 71 record files cannot go into the manuscript's reproducibility
release, which is attached beside a review package against an 80 MB combined
budget; and they are gzip already, so there is no precision trade available to
shrink them. They are packed into `closure_records.zip`, built and manifested
by `experiments/ttt/is_fresh/f41_closure_records_manifest.py`.

`CLOSURE_RECORDS_MANIFEST.json` ships inside the release and records, for each
member, its size, the sha256 of the stored `.jsonl.gz`, the sha256 of its
**decompressed** bytes, and its record count. The stored-file digests are the
same digests `MANIFEST_staged.sha256` lists, so the two cross-check; the
decompressed digest is the one that survives a rebuild of the archive at a
different gzip level.

Running `sha256sum -c MANIFEST_staged.sha256` from a release extraction
therefore reports the 71 `records/` lines and the 2 `REVIEW_R*.md` lines as
missing and the other 110 as `OK`. Put the side archive's `records/` back
beside `json/` and only the two transcripts are absent. Everything needed to
check a number printed in the manuscript ships in the release: the analysis
JSONs, the independent verifier's own report, and all of the code.
