#!/usr/bin/env python
"""Build the seed-matched suite's side archive, and manifest it in the release.

WHY THERE IS A SIDE ARCHIVE AT ALL
----------------------------------
The seed-matched re-measurement writes twelve raw per-episode record files,
55.4 MB of plain `.json`: six crossed measurement matrices (every episode's
`delta_feat` and labelled frozen loss measured through each of the three fresh
source networks) and six exposed adaptation runs.  They do not go into
`release_archive.zip`, and the reason is size and nothing else:

  * the release is already ~63 MB and is attached to correspondence beside a
    ~3 MB review package, against an 80 MB combined budget.  These records
    compress to ~9.7 MB, which is small in absolute terms and still enough to
    take the attached pair past that budget;
  * unlike the closure suite's `.jsonl.gz`, these files are plain JSON, so
    `make_release_zip.py` would ship them by construction -- the recursive
    walk under `experiments/results/is_fresh` admits `.json`.  The exclusion
    is therefore DECLARED, in `RESULT_EXCLUDE_PREFIXES` and in
    `DROPPED_PAYLOAD`, rather than inherited from an extension rule.

The split is by size, not by relevance, and it is the same split the theory-
closure suite made: the release keeps every ANALYSIS json, the frozen episode
manifest, the six source-model evaluation records, the measurement and
analysis code, and the design, review and results documents -- everything a
reader needs to check every number printed in either document -- and the raw
per-episode records move to a side archive published as a versioned release
asset of the public code repository.

WHAT THIS BUYS AND WHAT IT DOES NOT
-----------------------------------
The manifest written by this script ships INSIDE the release, so a reader who
obtains the side archive can verify it member by member rather than trusting
one whole-archive digest.  It proves neither possession nor correctness of an
archive a reader has not obtained.  Nothing printed in either document is
recomputed from the side archive: every printed number is bound (in
`paper/is2/tools/r9_reconcile.py`) to an analysis json that ships in the
release.  The one place the records are needed is re-deriving those analysis
jsons from scratch -- which is the point of shipping them at all.

Each member is hashed once, and the reason it is once rather than twice is
worth stating, because the sibling manifests hash twice.  `f41` records a
second digest over the DECOMPRESSED bytes because its members are `.jsonl.gz`
and a rebuild at a different gzip level changes the stored bytes while leaving
the content identical.  These members carry no compression of their own: the
bytes in the archive are the bytes the run wrote, so `sha256` already is the
content digest, and it is the same digest `MANIFEST_staged.sha256` records in
the results directory.  A second hash here would be the first one again.

USAGE
-----
With the pinned interpreter recorded in
paper/is2/provenance/BUILD_INTERPRETER.md:

    <python> f42_seedmatch_records_manifest.py --build
    <python> f42_seedmatch_records_manifest.py            # write the manifest
    <python> f42_seedmatch_records_manifest.py --check    # re-derive, compare

Exit codes: 0 ok, 1 mismatch, 2 the side archive is not present.
"""

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

_here = Path(__file__).resolve()
# experiments/ttt/is_fresh/f42_... -> repository root
REPO = _here.parents[3]
RECORDS = REPO / "experiments" / "results" / "is_fresh" / "seedmatch" / "records"
OUT_DEFAULT = (REPO / "experiments" / "results" / "is_fresh" / "seedmatch"
               / "SEEDMATCH_RECORDS_MANIFEST.json")
ZIP_DEFAULT = REPO / "paper" / "is2" / "seedmatch_records.zip"

# One fixed timestamp, so two builds of the same records are byte-identical.
# It is the date the suite's results were staged into the tree, not "now": a
# build stamp that moves makes an archive that cannot be reproduced.
STAMP = (2026, 8, 20, 0, 0, 0)

README = """\
# Seed-matched delta_feat re-measurement: raw per-episode records

The twelve `.json` files here are the raw per-episode records of the
seed-matched re-measurement, exactly as the runs wrote them, with one textual
transform applied and recorded: the compute host's repository prefix was
stripped from the `meta.argv` path fields, so no path in this archive resolves
to somebody's account.  No measurement has been transformed, rounded or
re-serialized.

* `records/crossed_*.json` -- the crossed measurement matrix.  For each
  (dataset, measurement network) pair, every episode in the frozen manifest
  measured through that network: its `delta_feat` and the labelled frozen loss
  of that same network.  Three networks x two datasets = six files.
* `records/cifar*_ttt_*_main_s[12].json` -- the six exposed Stage B adaptation
  runs (source seeds 1 and 2), in the same schema as the published
  `experiments/results/e2/` records.

**This archive is not needed to check any number printed in the paper.**  Every
printed number is bound to an analysis json, and every analysis json ships in
`release_archive.zip` under
`experiments/results/is_fresh/seedmatch/json/`.  What this archive is for is
re-deriving those analysis jsons from scratch, which the release's own
`seedmatch/code/` scripts do:

    python code/sm_analysis.py
    python code/sm_transport.py
    python code/sm_noise_scale.py
    python code/sm_downstream.py

Extract this archive so that `records/` sits beside `json/` and `code/` inside
`experiments/results/is_fresh/seedmatch/`, and those commands find their
inputs.

## Verifying what you have

`release_archive.zip` carries
`experiments/results/is_fresh/seedmatch/SEEDMATCH_RECORDS_MANIFEST.json`, which
lists every member of this archive with its size, its sha256, and the number of
per-episode records it holds.  The same per-file digests also appear in
`experiments/results/is_fresh/seedmatch/MANIFEST_staged.sha256`, which ships in
the release and can be checked with `sha256sum -c` once the records are in
place.
"""


def _record_count(path):
    """How many per-episode records the file holds.

    Two schemas, and the count means the same thing in both: one entry per
    (episode) observation.  A crossed matrix carries them flat and states its
    own count, which is asserted rather than trusted; an adaptation record
    nests them one level under its cells.
    """
    d = json.loads(path.read_text(encoding="utf-8"))
    if "records" in d:
        n = len(d["records"])
        assert d.get("n_records") == n, (
            f"{path.name}: the file states n_records={d.get('n_records')} and "
            f"carries {n}")
        return n
    return sum(len(cell["episodes"]) for cell in d["results"])


def _digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return os.path.getsize(path), h.hexdigest()


def build(zip_path):
    """Write the side archive deterministically from the records directory."""
    assert RECORDS.is_dir(), f"records directory not found: {RECORDS}"
    names = sorted(p.name for p in RECORDS.glob("*.json"))
    assert names, f"no .json records under {RECORDS}"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        info = zipfile.ZipInfo("README.md", date_time=STAMP)
        info.external_attr = 0o600 << 16
        z.writestr(info, README)
        for n in names:
            info = zipfile.ZipInfo(f"records/{n}", date_time=STAMP)
            info.external_attr = 0o600 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (RECORDS / n).read_bytes())
    size = zip_path.stat().st_size
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"[seedmatch-records] wrote {zip_path.name}: {len(names) + 1} "
          f"entries, {size} bytes, SHA-256 {sha}")
    return zip_path


def manifest(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        names = [e.filename for e in z.infolist()]
    members = []
    total_bytes = 0
    total_records = 0
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
        nbytes, sha = _digest(src)
        with zipfile.ZipFile(zip_path) as z:
            stored = z.getinfo(name).file_size
        assert stored == nbytes, (
            f"{name}: the archived member is {stored} bytes and the record on "
            f"disk is {nbytes}; the archive is stale")
        members.append({
            "name": name,
            "bytes": nbytes,
            "sha256": sha,
            "records": _record_count(src),
        })
        total_bytes += nbytes
        total_records += members[-1]["records"]

    zsize = zip_path.stat().st_size
    zsha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return {
        "archive": zip_path.name,
        "availability": (
            "seedmatch_records.zip is published as a versioned release asset "
            "of the public code repository and downloads without an account "
            "from https://github.com/kkioplkg/when-ttt-helps/releases . There "
            "is no DOI and no archival-preservation claim. It is NOT attached "
            "to review correspondence: the release archive and the review "
            "package already sit near the 80 MB combined budget. This file is "
            "the manifest of its contents and ships INSIDE the attached "
            "release, so a reader who obtains the side archive can verify it "
            "member by member without trusting a single whole-archive digest. "
            "Possession of the side archive is neither proved nor implied by "
            "having this manifest."),
        "purpose": (
            "The side archive is required to RE-DERIVE the released analysis "
            "jsons from scratch. It is NOT required to check any number "
            "printed in either document: every printed number is bound to an "
            "analysis json that ships in the release, under "
            "experiments/results/is_fresh/seedmatch/json/."),
        "hash_note": (
            "sha256 is of the .json file as the run wrote it, after the "
            "recorded path transform, and agrees with MANIFEST_staged.sha256 "
            "in the results directory. There is no second digest over "
            "decompressed bytes because these members carry no compression of "
            "their own: unlike the closure suite's .jsonl.gz, the bytes in "
            "the archive are the bytes on disk."),
        "archive_bytes": zsize,
        "archive_sha256": zsha,
        "n_entries": len(members),
        "n_record_files": len(members) - 1,
        "total_record_bytes": total_bytes,
        "total_records": total_records,
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
        print(f"[seedmatch-records] side archive not present: {zip_path}")
        print("[seedmatch-records] nothing to check against; this is what a "
              "clean extraction of the release looks like.")
        return 2

    rep = manifest(zip_path)

    if a.check:
        if not out.exists():
            print(f"[seedmatch-records] MISSING manifest: {out}")
            return 1
        old = json.loads(out.read_text(encoding="utf-8"))
        if old == rep:
            print(f"[seedmatch-records] --check OK: {rep['n_record_files']} "
                  f"record files, {rep['total_records']} records, "
                  f"{rep['archive_bytes']} bytes, manifest matches")
            return 0
        diff = [k for k in set(old) | set(rep) if old.get(k) != rep.get(k)]
        print(f"[seedmatch-records] --check MISMATCH on {sorted(diff)}")
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, indent=1)
        fh.write("\n")
    print(f"[seedmatch-records] wrote {out}: {rep['n_record_files']} record "
          f"files, {rep['total_records']} records, "
          f"{rep['total_record_bytes']} bytes of records, archive "
          f"{rep['archive_bytes']} bytes SHA-256 {rep['archive_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
