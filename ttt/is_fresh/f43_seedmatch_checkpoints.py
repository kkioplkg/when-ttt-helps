#!/usr/bin/env python
"""Build the seed-matched suite's checkpoint asset, and manifest it here.

WHY THIS ASSET EXISTS AT ALL
----------------------------
The published CIFAR grid's three per-seed source checkpoints were not
retained.  That is why its seed-resolved `delta_feat` cannot be recomputed
from the release, why the cross-model measurement disclosed in supplement
S8.3 could not be settled inside the published grid, and why "the per-seed
source checkpoints were not retained" is a sentence this paper has had to
write.  The seed-matched re-measurement retrained that family, and its six
networks WERE retained.  Publishing them is the part of that answer a reader
can act on: the six networks every number under
`experiments/results/is_fresh/seedmatch/json/` was measured through can be
loaded and re-measured rather than re-trained.

The archive also carries the two reconstruction-head records the masking
objective needs, because six encoders do not imply six heads and a reader who
had the encoders alone could not re-run `ttt_mask`.

WHAT IT DOES NOT DO
-------------------
It does not recover the lost published checkpoints, and nothing here is a
substitute for them.  These are fresh realizations of the nominal recipe
under a different execution stack; the counterfactual on the published
networks stays unidentified.  Nor is any number in either document recomputed
from this asset: every printed number is bound to an analysis json that ships
inside `release_archive.zip`.  What this asset buys is re-measurement without
re-training.

Weights are `.pt` files, which `make_release_zip.py` drops by construction
(`SKIP_EXT`), so they could not ship inside the release archive even if the
size were acceptable.  They are published as a versioned release asset
instead, on the same terms as the two record side archives.

USAGE
-----
With the pinned interpreter recorded in
paper/is2/provenance/BUILD_INTERPRETER.md:

    <python> f43_seedmatch_checkpoints.py --build
    <python> f43_seedmatch_checkpoints.py            # write the manifest
    <python> f43_seedmatch_checkpoints.py --check    # re-derive, compare

Exit codes: 0 ok, 1 mismatch, 2 the asset is not present.
"""

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

_here = Path(__file__).resolve()
# experiments/ttt/is_fresh/f43_... -> repository root
REPO = _here.parents[3]
CKPT = REPO / "experiments" / "ckpt" / "seedmatch"
OUT_DEFAULT = (REPO / "experiments" / "results" / "is_fresh" / "seedmatch"
               / "SEEDMATCH_CHECKPOINTS_MANIFEST.json")
ZIP_DEFAULT = REPO / "paper" / "is2" / "checkpoints_seedmatch.zip"

# One fixed timestamp, so two builds of the same weights are byte-identical.
STAMP = (2026, 8, 20, 0, 0, 0)

README = """\
# Seed-matched delta_feat re-measurement: the six retained source networks

These are the ResNet-26+GroupNorm source networks the seed-matched
re-measurement trained, and through which every number under
`experiments/results/is_fresh/seedmatch/json/` was measured.

    checkpoints/cifar10_resnet26ttt_s{0,1,2}.pt
    checkpoints/cifar100_resnet26ttt_s{0,1,2}.pt
    checkpoints/cifar10_resnet26ttt_s{1,2}_recon.json

Each `.pt` holds `{"model": state_dict, "args": vars(args)}`, written by
`experiments/ttt/e2_cifar/train_source.py` under the published recipe.  The
two `_recon.json` records are the reconstruction heads the masking objective
adapts against; six encoders do not imply six heads, and the exposed masking
lane runs on CIFAR-10 seeds 1 and 2 only.

## What these are, and what they are not

The published CIFAR grid's own three per-seed source checkpoints were **not**
retained, which is why the paper says its seed-resolved measurement cannot be
recomputed.  These six do not recover those: they are fresh realizations of
the same nominal recipe under a different execution stack, and the
counterfactual on the published networks remains unidentified.  What they do
is let a reader re-measure instead of re-train.

Comparability was gated before any endpoint was read: every network sits
inside the published across-seed accuracy range with a tolerance of 0.010.
The per-network accuracies are in
`experiments/results/is_fresh/seedmatch/json/cifar*_resnet26ttt_s*.json`,
which ship inside `release_archive.zip`, and are tabulated in that
directory's `RESULTS.md`.  Those records also carry `"gate_pass": false`,
which is the training script's own aspirational absolute threshold; no
published model meets it either, and the published records under
`experiments/results/m0/` carry the identical flags.

## Verifying what you have

`release_archive.zip` carries
`experiments/results/is_fresh/seedmatch/SEEDMATCH_CHECKPOINTS_MANIFEST.json`,
which lists every member of this archive with its size and sha256.  The same
digests appear in that directory's `MANIFEST.md`.

## Reproducing a measurement from them

Place `checkpoints/` at `experiments/ckpt/seedmatch/` in an extracted
`release_archive.zip`, obtain `seedmatch_records.zip` if you also want the raw
per-episode records, and the suite's own code under
`experiments/results/is_fresh/seedmatch/code/` re-runs the measurement
(`sm_crossed.py`) and the analysis (`sm_analysis.py`, `sm_transport.py`,
`sm_noise_scale.py`, `sm_downstream.py`).  CIFAR-10/100 and the -C corruption
sets are not redistributed here and are fetched from their own hosts.
"""


def _digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return os.path.getsize(path), h.hexdigest()


def _members():
    names = sorted(p.name for p in CKPT.iterdir()
                   if p.suffix in (".pt", ".json"))
    assert names, f"no checkpoints under {CKPT}"
    return names


def build(zip_path):
    assert CKPT.is_dir(), f"checkpoint directory not found: {CKPT}"
    names = _members()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        info = zipfile.ZipInfo("README.md", date_time=STAMP)
        info.external_attr = 0o600 << 16
        z.writestr(info, README)
        for n in names:
            info = zipfile.ZipInfo(f"checkpoints/{n}", date_time=STAMP)
            info.external_attr = 0o600 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (CKPT / n).read_bytes())
    size = zip_path.stat().st_size
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"[seedmatch-ckpt] wrote {zip_path.name}: {len(names) + 1} entries, "
          f"{size} bytes, SHA-256 {sha}")
    return zip_path


def manifest(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        names = [e.filename for e in z.infolist()]
    members = []
    total = 0
    n_nets = 0
    for name in sorted(names):
        if name == "README.md":
            with zipfile.ZipFile(zip_path) as z:
                blob = z.read(name)
            members.append({"name": name, "bytes": len(blob),
                            "sha256": hashlib.sha256(blob).hexdigest()})
            continue
        src = CKPT / os.path.basename(name)
        assert src.exists(), (
            f"the asset lists {name} but the checkpoint directory has no "
            f"{src.name}; manifest and archive would disagree")
        nbytes, sha = _digest(src)
        with zipfile.ZipFile(zip_path) as z:
            stored = z.getinfo(name).file_size
        assert stored == nbytes, (
            f"{name}: the archived member is {stored} bytes and the file on "
            f"disk is {nbytes}; the asset is stale")
        members.append({"name": name, "bytes": nbytes, "sha256": sha})
        total += nbytes
        if name.endswith(".pt"):
            n_nets += 1

    zsize = zip_path.stat().st_size
    zsha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return {
        "archive": zip_path.name,
        "availability": (
            "checkpoints_seedmatch.zip is published as a versioned release "
            "asset of the public code repository and downloads without an "
            "account from "
            "https://github.com/kkioplkg/when-ttt-helps/releases . There is "
            "no DOI and no archival-preservation claim. This file is the "
            "manifest of its contents and ships INSIDE release_archive.zip, "
            "so a reader who obtains the asset can verify it member by "
            "member. Possession of the asset is neither proved nor implied "
            "by having this manifest."),
        "purpose": (
            "These are the six source networks the seed-matched suite trained "
            "and measured through, retained so that a reader can RE-MEASURE "
            "rather than re-train. They do NOT recover the published grid's "
            "own three per-seed source checkpoints, which were not retained; "
            "they are fresh realizations of the same nominal recipe under a "
            "different execution stack. No number printed in either document "
            "is recomputed from this asset."),
        "why_not_in_the_release_archive": (
            "make_release_zip.py drops .pt by construction (SKIP_EXT), so "
            "model weights cannot ship inside release_archive.zip; and at "
            "~16 MB they would consume the correspondence attachment budget "
            "the release archive already nearly fills."),
        "archive_bytes": zsize,
        "archive_sha256": zsha,
        "n_entries": len(members),
        "n_networks": n_nets,
        "total_member_bytes": total,
        "members": members,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=str(ZIP_DEFAULT))
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--build", action="store_true",
                    help="rebuild the asset from the checkpoint directory")
    ap.add_argument("--check", action="store_true",
                    help="re-derive the manifest and compare, writing nothing")
    a = ap.parse_args(argv)

    zip_path = Path(a.zip)
    out = Path(a.out)

    if a.build:
        build(zip_path)

    if not zip_path.exists():
        print(f"[seedmatch-ckpt] asset not present: {zip_path}")
        print("[seedmatch-ckpt] nothing to check against; this is what a "
              "clean extraction of the release looks like.")
        return 2

    rep = manifest(zip_path)

    if a.check:
        if not out.exists():
            print(f"[seedmatch-ckpt] MISSING manifest: {out}")
            return 1
        old = json.loads(out.read_text(encoding="utf-8"))
        if old == rep:
            print(f"[seedmatch-ckpt] --check OK: {rep['n_networks']} networks, "
                  f"{rep['archive_bytes']} bytes, manifest matches")
            return 0
        diff = [k for k in set(old) | set(rep) if old.get(k) != rep.get(k)]
        print(f"[seedmatch-ckpt] --check MISMATCH on {sorted(diff)}")
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, indent=1)
        fh.write("\n")
    print(f"[seedmatch-ckpt] wrote {out}: {rep['n_networks']} networks, "
          f"{rep['total_member_bytes']} bytes of weights, archive "
          f"{rep['archive_bytes']} bytes SHA-256 {rep['archive_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
