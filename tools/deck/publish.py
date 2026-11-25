#!/usr/bin/env python3
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build/deck"
UPLOAD = BUILD / "upload"
TAG = "deck"
PRESET = "Steam Deck"
BINARY = "infinity-julia.x86_64"
PACK = "infinity-julia.pck"
CLIENT = "deck.py"
SOURCES = ["game", f"tools/deck/{CLIENT}"]
SMOKE_TEST = ".github/workflows/deck.yml"
MAX_ASSET_BYTES = 2 * 1024 ** 3
GODOT_GLOB = (r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_*"
              r"\Godot_v*_win64_console.exe")


def run(*command, check=True):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode:
        sys.exit(f"{' '.join(map(str, command))}\n{result.stdout}{result.stderr}")
    return result


def godot():
    found = os.environ.get("GODOT") or next(
        iter(sorted(glob.glob(os.path.expandvars(GODOT_GLOB)))), None)
    if not found:
        sys.exit("Godot was not found; set GODOT to its console executable.")
    return found


def published_version():
    result = run("gh", "release", "download", TAG, "--pattern", "manifest.json",
                 "--output", "-", check=False)
    return json.loads(result.stdout)["version"] if result.returncode == 0 else None


def unchanged_since(version):
    if not version or run("git", "cat-file", "-e", f"{version}^{{commit}}",
                          check=False).returncode:
        return False
    return run("git", "diff", "--quiet", version, "HEAD", "--", *SOURCES,
               check=False).returncode == 0


def export():
    shutil.rmtree(BUILD, ignore_errors=True)
    UPLOAD.mkdir(parents=True)
    result = run(godot(), "--headless", "--path", "game", "--export-release", PRESET,
                 BUILD / BINARY, check=False)
    if result.returncode or not all((BUILD / name).is_file() for name in (BINARY, PACK)):
        sys.exit(f"The Steam Deck export failed.\n{result.stdout}{result.stderr}")
    shutil.copyfile(ROOT / "tools/deck" / CLIENT, BUILD / CLIENT)


def head_stamp():
    version, date = run("git", "show", "-s", "--abbrev=12", "--format=%h%n%cd",
                        "--date=format:%Y-%m-%d %H:%M", "HEAD").stdout.splitlines()
    return {"version": version, "date": date}


def manifest(stamp):
    files = []
    for name, mode in ((BINARY, "755"), (PACK, "644"), (CLIENT, "755")):
        data = (BUILD / name).read_bytes()
        if len(data) >= MAX_ASSET_BYTES:
            sys.exit(f"{name} is over GitHub's 2 GiB limit; split the pack.")
        digest = hashlib.sha256(data).hexdigest()
        asset = f"{digest[:16]}-{name}"
        shutil.copyfile(BUILD / name, UPLOAD / asset)
        files.append({"name": name, "asset": asset, "sha256": digest,
                      "size": len(data), "mode": mode})
    return {**stamp, "files": files}


def upload(build):
    if run("gh", "release", "view", TAG, check=False).returncode:
        run("gh", "release", "create", TAG, "--title", "Steam Deck build", "--notes",
            "Rolling build. The Steam Deck updates itself from these files.")
    listed = run("gh", "release", "view", TAG, "--json", "assets",
                 "--jq", ".assets[].name").stdout.split()
    wanted = {entry["asset"] for entry in build["files"]}
    fresh = sorted(wanted - set(listed))
    if fresh:
        run("gh", "release", "upload", TAG, *(UPLOAD / name for name in fresh))
    (UPLOAD / "manifest.json").write_text(json.dumps(build, indent=1), newline="\n")
    shutil.copyfile(BUILD / CLIENT, UPLOAD / CLIENT)
    run("gh", "release", "upload", TAG, "--clobber", UPLOAD / CLIENT,
        UPLOAD / "manifest.json")
    for stale in set(listed) - wanted - {CLIENT, "manifest.json"}:
        run("gh", "release", "delete-asset", TAG, stale, "--yes")


def main():
    force = "--force" in sys.argv
    if run("git", "status", "--porcelain", "--", *SOURCES).stdout.strip():
        sys.exit("Commit the changes under game/ and tools/deck/ before publishing.")
    stamp = head_stamp()
    if not force and unchanged_since(published_version()):
        print("Steam Deck build: already up to date.")
        return
    print(f"Steam Deck build: exporting {stamp['version']}...", flush=True)
    export()
    print("Steam Deck build: uploading...", flush=True)
    upload(manifest(stamp))
    if (ROOT / SMOKE_TEST).is_file():
        run("gh", "workflow", "run", Path(SMOKE_TEST).name, check=False)
    print(f"Steam Deck build: {stamp['version']} is published.")


if __name__ == "__main__":
    main()
