#!/usr/bin/env python
"""Derive the per-member manifest of the UNATTACHED E3 replica side archive.

WHY THIS EXISTS
---------------
`paper/is2/e3_vectors_replicas.zip` carries the K = 3 per-replica prediction
trajectories from which the released `pi_bar` and `s` arrays were formed.  It
is ~62 MB and is NOT attached to review correspondence -- the attached pair
would exceed the correspondence size limit -- so the submission manifest
states its size, entry count and SHA-256 and nothing else.

Those three assertions are unverifiable to a reader who does not have the
archive, and only weakly verifiable to a reader who does: a whole-archive
digest tells you nothing until you have reproduced the byte-for-byte ZIP,
which depends on compression settings and entry order rather than on content.

This script writes the manifest that fixes both problems, and it is written
INTO THE ATTACHED RELEASE:

  * for every member of the side archive, its name, its UNCOMPRESSED size and
    the SHA-256 of its uncompressed bytes -- so possession is verifiable
    member by member, with no dependence on how the ZIP was compressed;
  * for every `.npz` member, the name, shape, dtype and SHA-256 of the raw
    C-order bytes of every array inside it -- so possession is verifiable
    array by array, which is the level the provenance claim is actually made
    at ("pi_bar is the replica mean, s is the replica dispersion").

A reader who obtains the side archive can therefore check that they have the
same object this submission used, without trusting a single opaque digest and
without needing the archive to have been rebuilt identically.

The availability statement is deliberately plain and is printed into the
output: the side archive is an AUTHOR-SIDE DEPOSIT held alongside the DOI
release, not a file this correspondence attaches.

Usage:
    python f40_e3_replicas_manifest.py \
        [--zip paper/is2/e3_vectors_replicas.zip] \
        [--out experiments/results/is_fresh/e3_vectors/REPLICAS_MANIFEST.json]
    python f40_e3_replicas_manifest.py --check   # re-derive and compare
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DEFAULT_ZIP = os.path.join(REPO, "paper", "is2", "e3_vectors_replicas.zip")
DEFAULT_OUT = os.path.join(REPO, "experiments", "results", "is_fresh",
                           "e3_vectors", "REPLICAS_MANIFEST.json")

AVAILABILITY = (
    "e3_vectors_replicas.zip is an author-side deposit held alongside the "
    "DOI release. It is NOT attached to review correspondence: at ~62 MB it "
    "would put the attached pair over the correspondence size limit. This "
    "file is the manifest of its contents and ships INSIDE the attached "
    "release, so a reader who obtains the side archive can verify it member "
    "by member and array by array without trusting a single whole-archive "
    "digest."
)

PURPOSE = (
    "The side archive is required to REGENERATE the released summary arrays "
    "from the replicas (pi_bar as the replica mean, s as the replica "
    "dispersion). It is NOT required to rerun the selector, which "
    "f39_e3_vector_selfcheck.py does from the released arrays alone, and it "
    "is not required to reproduce any number printed in either document."
)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def npz_arrays(raw: bytes):
    """(name, shape, dtype, sha256 of C-order raw bytes) for each array.

    The digest is taken over the ARRAY's own bytes, not over the .npy
    container and not over the enclosing ZIP member, so it is invariant to
    the compression and the container framing and depends only on the
    numbers.  That is the level at which the provenance claim is made.
    """
    import numpy as np
    out = []
    with np.load(io.BytesIO(raw), allow_pickle=False) as d:
        for name in d.files:
            a = np.ascontiguousarray(d[name])
            out.append({
                "array": name,
                "shape": list(a.shape),
                "dtype": str(a.dtype),
                "sha256_raw_c_order": sha_bytes(a.tobytes(order="C")),
                "nbytes": int(a.nbytes),
            })
    return out


def derive(zip_path: str) -> dict:
    st = os.stat(zip_path)
    with open(zip_path, "rb") as f:
        whole = f.read()
    members = []
    with zipfile.ZipFile(io.BytesIO(whole)) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            raw = z.read(info.filename)
            row = {
                "name": info.filename,
                "bytes": int(info.file_size),
                "sha256": sha_bytes(raw),
            }
            assert len(raw) == info.file_size, info.filename
            if info.filename.lower().endswith(".npz"):
                row["arrays"] = npz_arrays(raw)
            members.append(row)
    return {
        "archive": os.path.basename(zip_path),
        "availability": AVAILABILITY,
        "purpose": PURPOSE,
        "archive_bytes": int(st.st_size),
        "archive_sha256": sha_bytes(whole),
        "n_entries": len(members),
        "n_npz_members": sum(1 for m in members if "arrays" in m),
        "total_uncompressed_bytes": sum(m["bytes"] for m in members),
        "n_arrays": sum(len(m.get("arrays", [])) for m in members),
        "members": members,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=DEFAULT_ZIP)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare with the file on disk")
    a = ap.parse_args()
    if not os.path.exists(a.zip):
        print(f"[f40] side archive not present at {a.zip}", file=sys.stderr)
        return 2
    rep = derive(a.zip)
    if a.check:
        with open(a.out, encoding="utf-8") as f:
            have = json.load(f)
        if have != rep:
            print("[f40] REPLICAS_MANIFEST.json does not match the side "
                  "archive it describes", file=sys.stderr)
            return 1
        print(f"[f40] REPLICAS_MANIFEST.json matches: {rep['n_entries']} "
              f"members, {rep['n_arrays']} arrays")
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
        f.write("\n")
    print(f"[f40] {rep['n_entries']} members, {rep['n_npz_members']} npz, "
          f"{rep['n_arrays']} arrays, "
          f"{rep['total_uncompressed_bytes']:,} uncompressed bytes")
    print(f"[f40] archive sha256 {rep['archive_sha256']}")
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
