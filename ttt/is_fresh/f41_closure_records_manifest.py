#!/usr/bin/env python
"""Build the theory-closure side archive, and manifest it inside the release.

WHY THERE IS A SIDE ARCHIVE AT ALL
----------------------------------
The theory-closure suite writes 71 raw per-episode record files, 128 MB, as
`.jsonl.gz`.  They cannot go into `release_archive.zip`:

  * the release is already 61.8 MB and is attached to correspondence beside a
    ~2 MB review package, against an 80 MB combined budget.  128 MB of records
    would take the attached pair to roughly 192 MB;
  * the records are gzip already, so a container that recompresses them saves
    nothing -- unlike a float64 array, there is no precision trade to make;
  * `make_release_zip.py` drops `.gz` by construction (`SKIP_EXT`), so they
    would silently not ship even if nobody thought about it.

So the split is by content, exactly as it was for the E3 replica vectors: the
release keeps every ANALYSIS json, every verification report, the analysis and
measurement code and the design and results documents -- everything a reader
needs to check every number printed in either document -- and the raw
per-episode records move to a side archive held beside the DOI deposit.

WHAT THIS BUYS AND WHAT IT DOES NOT
-----------------------------------
The manifest written by this script ships INSIDE the release, so a reader who
obtains the side archive can verify it file by file rather than trusting one
whole-archive digest.  It proves neither possession nor correctness of an
archive a reader has not obtained.  Nothing printed in either document is
recomputed from the side archive: every printed number is bound (in
`paper/is2/tools/r9_reconcile.py`) to an analysis json that ships in the
release.  The one place the records are needed is re-deriving those analysis
jsons from scratch -- which is the point of shipping them at all.

Each member is hashed twice, and the second hash is the load-bearing one:

  * `sha256` -- the `.jsonl.gz` file exactly as the run wrote it.  This is what
    `MANIFEST_staged.sha256` in the results directory also records, so the two
    agree and a reader can cross-check them.
  * `sha256_uncompressed` -- the sha256 of the DECOMPRESSED bytes, plus the
    record count.  A side archive that was re-gzipped at a different
    compression level has different member bytes and identical decompressed
    bytes, so this is the hash that survives a rebuild.  The E3 manifest takes
    the same view for the same reason, one level down (array bytes rather than
    `.npy` containers).

USAGE
-----
With the pinned interpreter recorded in
paper/is2/provenance/BUILD_INTERPRETER.md:

    <python> f41_closure_records_manifest.py --build
    <python> f41_closure_records_manifest.py            # write the manifest
    <python> f41_closure_records_manifest.py --check    # re-derive, compare

Exit codes: 0 ok, 1 mismatch, 2 the side archive is not present.
"""

import argparse
import gzip
import hashlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path

_here = Path(__file__).resolve()
# <root>/ttt/is_fresh/f41_... -> repository root
REPO = _here.parents[2]
RECORDS = REPO / "results" / "is_fresh" / "closure" / "records"
OUT_DEFAULT = (REPO / "results" / "is_fresh" / "closure"
               / "CLOSURE_RECORDS_MANIFEST.json")
ZIP_DEFAULT = REPO / "paper" / "is2" / "closure_records.zip"

# One fixed timestamp, so two builds of the same records are byte-identical.
# It is the date the suite's results were staged into the tree, not "now":
# a build stamp that moves makes an archive that cannot be reproduced.
STAMP = (2026, 8, 18, 0, 0, 0)

README = """\
# Theory-closure suite: raw per-episode records

The 71 `.jsonl.gz` files here are the raw per-episode records of the
theory-closure experiments, exactly as the runs wrote them: no measurement in
this archive has been transformed, rounded or re-serialized.

**This archive is not needed to check any number printed in the paper.**  Every
printed number is bound to an analysis json, and every analysis json ships in
`release_archive.zip` under
`experiments/results/is_fresh/closure/json/`.  What this archive is for is
re-deriving those analysis jsons from scratch, which the release's own
`closure/code/` scripts do:

    python code/analyze_p1.py
    python code/analyze_p2.py
    python code/analyze_boundary.py
    python code/analyze_extras.py
    python code/analyze_kappa_restricted.py
    python code/verify_closure.py

Extract this archive so that `records/` sits beside `json/` and `code/` inside
`experiments/results/is_fresh/closure/`, and those commands find their inputs.

## Verifying what you have

`release_archive.zip` carries
`experiments/results/is_fresh/closure/CLOSURE_RECORDS_MANIFEST.json`, which
lists every member of this archive with its size, the sha256 of the file as
stored, the sha256 of its DECOMPRESSED bytes, and its record count.  The
second hash is the one to prefer: it is invariant to the gzip level, so it
still matches if this archive is rebuilt.

The same per-file digests also appear in
`experiments/results/is_fresh/closure/MANIFEST_staged.sha256`, which ships in
the release and can be checked with `sha256sum -c` once the records are in
place.
"""


def _digests(path):
    """(bytes, sha256 of the file, sha256 of the decompressed bytes, lines)."""
    raw = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            raw.update(chunk)
    plain = hashlib.sha256()
    lines = 0
    with gzip.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            plain.update(chunk)
            lines += chunk.count(b"\n")
    return (os.path.getsize(path), raw.hexdigest(), plain.hexdigest(), lines)


def build(zip_path):
    """Write the side archive deterministically from the records directory."""
    assert RECORDS.is_dir(), f"records directory not found: {RECORDS}"
    names = sorted(p.name for p in RECORDS.glob("*.jsonl.gz"))
    assert names, f"no .jsonl.gz records under {RECORDS}"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        info = zipfile.ZipInfo("README.md", date_time=STAMP)
        info.external_attr = 0o600 << 16
        z.writestr(info, README)
        for n in names:
            info = zipfile.ZipInfo(f"records/{n}", date_time=STAMP)
            info.external_attr = 0o600 << 16
            # The members are gzip already; storing them uncompressed avoids a
            # pointless second pass and keeps the archive size honest.
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, (RECORDS / n).read_bytes())
    size = zip_path.stat().st_size
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"[closure-records] wrote {zip_path.name}: {len(names) + 1} entries, "
          f"{size} bytes, SHA-256 {sha}")
    return zip_path


def manifest(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        entries = z.infolist()
        names = [e.filename for e in entries]
    members = []
    total_unc = 0
    total_lines = 0
    for name in sorted(names):
        if name == "README.md":
            with zipfile.ZipFile(zip_path) as z:
                blob = z.read(name)
            members.append({"name": name, "bytes": len(blob),
                            "sha256": hashlib.sha256(blob).hexdigest()})
            continue
        src = RECORDS / os.path.basename(name)
        assert src.exists(), (
            f"the side archive lists {name} but the records directory has no "
            f"{src.name}; manifest and archive would disagree")
        nbytes, sha, sha_plain, lines = _digests(src)
        with zipfile.ZipFile(zip_path) as z:
            stored = z.getinfo(name).file_size
        assert stored == nbytes, (
            f"{name}: the archived member is {stored} bytes and the record on "
            f"disk is {nbytes}; the archive is stale")
        members.append({
            "name": name,
            "bytes": nbytes,
            "sha256": sha,
            "sha256_uncompressed": sha_plain,
            "records": lines,
        })
        total_unc += nbytes
        total_lines += lines

    zsize = zip_path.stat().st_size
    zsha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return {
        "archive": zip_path.name,
        "availability": (
            "closure_records.zip is an author-side deposit held alongside the "
            "DOI release. It is NOT attached to review correspondence: at "
            "~128 MB it would put the attached pair far over the "
            "correspondence size limit. This file is the manifest of its "
            "contents and ships INSIDE the attached release, so a reader who "
            "obtains the side archive can verify it member by member without "
            "trusting a single whole-archive digest. Possession of the side "
            "archive is neither proved nor implied by having this manifest."),
        "purpose": (
            "The side archive is required to RE-DERIVE the released analysis "
            "jsons from scratch. It is NOT required to check any number "
            "printed in either document: every printed number is bound to an "
            "analysis json that ships in the release, and the independent "
            "verifier's own report (json/VERIFY_FINAL.json) ships there too."),
        "hash_note": (
            "sha256 is of the .jsonl.gz file as stored and agrees with "
            "MANIFEST_staged.sha256 in the results directory; "
            "sha256_uncompressed is of the decompressed bytes and is the "
            "digest that survives a rebuild at a different gzip level."),
        "archive_bytes": zsize,
        "archive_sha256": zsha,
        "n_entries": len(members),
        "n_record_files": len(members) - 1,
        "total_record_bytes": total_unc,
        "total_records": total_lines,
        "members": members,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=str(ZIP_DEFAULT))
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--build", action="store_true",
                    help="rebuild the side archive from the records directory")
    ap.add_argument("--check", action="store_true",
                    help="re-derive the manifest and compare, writing nothing")
    a = ap.parse_args(argv)

    zip_path = Path(a.zip)
    out = Path(a.out)

    if a.build:
        build(zip_path)

    if not zip_path.exists():
        print(f"[closure-records] side archive not present: {zip_path}")
        print("[closure-records] nothing to check against; this is what a "
              "clean extraction of the release looks like.")
        return 2

    rep = manifest(zip_path)

    if a.check:
        if not out.exists():
            print(f"[closure-records] MISSING manifest: {out}")
            return 1
        old = json.loads(out.read_text(encoding="utf-8"))
        if old == rep:
            print(f"[closure-records] --check OK: {rep['n_record_files']} "
                  f"record files, {rep['total_records']} records, "
                  f"{rep['archive_bytes']} bytes, manifest matches")
            return 0
        diff = [k for k in set(old) | set(rep) if old.get(k) != rep.get(k)]
        print(f"[closure-records] --check MISMATCH on {sorted(diff)}")
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, indent=1)
        fh.write("\n")
    print(f"[closure-records] wrote {out}: {rep['n_record_files']} record "
          f"files, {rep['total_records']} records, "
          f"{rep['total_record_bytes']} bytes of records, archive "
          f"{rep['archive_bytes']} bytes SHA-256 {rep['archive_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
