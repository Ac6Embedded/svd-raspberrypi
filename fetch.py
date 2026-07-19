#!/usr/bin/env python3
"""Fetch Raspberry Pi SVD files from raspberrypi/pico-sdk (master).

Stdlib only. Re-runnable. Incremental: every run starts with a cheap
metadata check (one GitHub API request for the current master commit sha,
no artifact downloads). If the sha matches manifest.json and all tracked
files are present, the script prints 'up to date' and exits 0 without
touching anything. Otherwise it downloads the SVD files and LICENSE.TXT
into <repo>/.work, validates the SVDs with xml.etree, places them under
<Family>/ and rewrites manifest.json. A missing or unreadable
manifest.json (or missing svd files) triggers a full rebuild.
Run from anywhere: paths are derived from this file.
"""

import datetime
import json
import os
import shutil
import stat
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / ".work"
SVD_BASE = ROOT
LICENSES_DIR = ROOT / "LICENSES"
MANIFEST = ROOT / "manifest.json"

# Entries that live at the repo root and must never be deleted as if they
# were a family directory. Everything else at the top level that is a dir
# is treated as generated family output.
PROTECTED = {
    ".git",
    ".github",
    ".gitignore",
    ".work",
    "LICENSES",
    "README.md",
    "manifest.json",
    "fetch.py",
}

RAW_BASE = "https://raw.githubusercontent.com/raspberrypi/pico-sdk/master"
API_COMMIT = "https://api.github.com/repos/raspberrypi/pico-sdk/commits/master"

TARGETS = [
    # (raw path in repo, family, device)
    ("src/rp2040/hardware_regs/RP2040.svd", "RP2040", "RP2040"),
    ("src/rp2350/hardware_regs/RP2350.svd", "RP2350", "RP2350"),
]
LICENSE_PATH = "LICENSE.TXT"
LICENSE_DEST = "pico-sdk-LICENSE.TXT"

UA = {"User-Agent": "Mozilla/5.0"}


def _force_remove(func, path, _exc):
    """rmtree onerror handler: clear read-only bit and retry (Windows)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clean_family_dirs():
    """Delete generated family directories only, never protected entries.

    The SVD output base is now the repo root, so a blind rmtree of the base
    would wipe the whole repo (including .git). This removes only the
    top-level directories that are not in PROTECTED.
    """
    for child in ROOT.iterdir():
        if child.is_dir() and child.name not in PROTECTED:
            shutil.rmtree(child, onerror=_force_remove)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch_artifact(url: str) -> bytes:
    """Download an artifact (SVD or license). Logged so runs are auditable."""
    print(f"DOWNLOAD {url}")
    return fetch(url)


def load_manifest():
    if not MANIFEST.is_file():
        return None
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def recorded_sha(manifest) -> str:
    if not isinstance(manifest, dict):
        return ""
    for src in manifest.get("sources", []):
        if src.get("name") == "pico-sdk":
            return src.get("version", "")
    return ""


def tree_complete(manifest) -> bool:
    """All files listed in the manifest (and the license copy) exist locally."""
    if not isinstance(manifest, dict):
        return False
    entries = manifest.get("files", [])
    if len(entries) != len(TARGETS):
        return False
    for entry in entries:
        if not (ROOT / entry.get("path", "")).is_file():
            return False
    return (LICENSES_DIR / LICENSE_DEST).is_file()


def main() -> int:
    # Cheap metadata check: one API request, no artifact downloads.
    print(f"check {API_COMMIT} (metadata only)")
    commit = json.loads(fetch(API_COMMIT).decode("utf-8"))
    sha = commit["sha"]
    print(f"pico-sdk master commit: {sha}")

    manifest = load_manifest()
    old_sha = recorded_sha(manifest)
    if old_sha == sha and tree_complete(manifest):
        print("up to date")
        return 0

    if old_sha and old_sha != sha:
        print(f"pico-sdk changed: {old_sha} -> {sha}")
    elif not old_sha:
        print("no usable manifest.json, full rebuild")
    else:
        print("local files missing, rebuilding")

    WORK.mkdir(parents=True, exist_ok=True)
    clean_family_dirs()
    LICENSES_DIR.mkdir(parents=True, exist_ok=True)

    # License file.
    lic = fetch_artifact(f"{RAW_BASE}/{LICENSE_PATH}")
    (LICENSES_DIR / LICENSE_DEST).write_bytes(lic)
    print(f"{LICENSE_PATH}: {len(lic)} bytes")

    files_meta = []
    total_bytes = 0
    for rel, family, device in TARGETS:
        url = f"{RAW_BASE}/{rel}"
        data = fetch_artifact(url)
        tmp = WORK / f"{device}.svd"
        tmp.write_bytes(data)

        # Validate: well-formed XML, root element must be 'device'.
        root = ET.parse(tmp).getroot()
        tag = root.tag.split("}")[-1]
        if tag != "device":
            print(f"FAIL {rel}: root element is '{tag}', expected 'device'")
            return 1

        dest = SVD_BASE / family / f"{device}.svd"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tmp, dest)
        total_bytes += len(data)
        print(f"OK {rel} -> {dest.relative_to(ROOT)} ({len(data)} bytes)")
        files_meta.append({
            "path": f"{family}/{device}.svd",
            "device": device,
            "family": family,
            "source": "pico-sdk",
            "provenance": "pristine",
        })

    manifest = {
        "vendor": "Raspberry Pi",
        "generated": datetime.date.today().isoformat(),
        "sources": [
            {
                "name": "pico-sdk",
                "url": "https://github.com/raspberrypi/pico-sdk",
                "version": sha,
                "license": "BSD-3-Clause",
                "files": [rel for rel, _, _ in TARGETS] + [LICENSE_PATH],
            }
        ],
        "files": files_meta,
        "stats": {
            "total_files": len(files_meta),
            "total_bytes": total_bytes,
        },
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"manifest.json written: {len(files_meta)} files, {total_bytes} bytes")

    shutil.rmtree(WORK, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
