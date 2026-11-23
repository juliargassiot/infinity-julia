#!/usr/bin/env python3
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

NAME = "Infinity Julia"
SLUG = "infinity-julia"
GAME_BINARY = f"{SLUG}.x86_64"
BASE_URL = os.environ.get(
    "INFINITY_JULIA_URL",
    f"https://github.com/juliargassiot/{SLUG}/releases/download/deck")

DATA_HOME = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
HOME = DATA_HOME / SLUG
VERSIONS = HOME / "versions"
CURRENT = HOME / "current"
LAUNCHER = HOME / "play"
DESKTOP_ENTRY = DATA_HOME / "applications" / f"{SLUG}.desktop"
UNITS = CONFIG_HOME / "systemd/user"
UPDATE_UNIT = f"{SLUG}-update"

MANIFEST_TIMEOUT = 5
DOWNLOAD_TIMEOUT = 30
CHUNK = 1 << 20


class Busy(Exception):
    pass


class Console:
    percent = None

    def progress(self, fraction, text):
        percent = int(fraction * 100)
        if percent != self.percent:
            self.percent = percent
            print(f"\r{text} {percent:3}%", end="", flush=True)

    def close(self):
        if self.percent is not None:
            print()


class Dialog:
    def __init__(self):
        self.process = None
        self.fallback = Console()

    def progress(self, fraction, text):
        if self.process is None:
            self.process = self.open()
        if not self.process:
            return self.fallback.progress(fraction, text)
        try:
            self.process.stdin.write(f"# {text}\n{min(int(fraction * 100), 99)}\n")
            self.process.stdin.flush()
        except OSError:
            self.process = False

    def open(self):
        try:
            return subprocess.Popen(
                ["zenity", "--progress", f"--title={NAME}", "--no-cancel",
                 "--auto-close", "--width=480"],
                stdin=subprocess.PIPE, text=True)
        except OSError:
            return False

    def close(self):
        if self.process:
            try:
                self.process.stdin.write("100\n")
                self.process.stdin.close()
                self.process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                self.process.kill()


def lock():
    HOME.mkdir(parents=True, exist_ok=True)
    handle = open(HOME / "lock", "w")
    try:
        import fcntl
    except ImportError:
        return handle
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise Busy("another update is running") from None
    return handle


def fetch(asset, timeout, start=0):
    request = urllib.request.Request(f"{BASE_URL}/{asset}")
    if start:
        request.add_header("Range", f"bytes={start}-")
    return urllib.request.urlopen(request, timeout=timeout)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while chunk := file.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def current_version():
    try:
        version = CURRENT.read_text().strip()
    except OSError:
        return None
    return version if (VERSIONS / version / "manifest.json").is_file() else None


def installed_files(version):
    if not version:
        return {}
    manifest = json.loads((VERSIONS / version / "manifest.json").read_text())
    return {f["sha256"]: VERSIONS / version / f["name"] for f in manifest["files"]}


def download(entry, target, report):
    part = target.with_name(target.name + ".part")
    have = part.stat().st_size if part.exists() else 0
    if have > entry["size"]:
        part.unlink()
        have = 0
    if have < entry["size"]:
        with fetch(entry["asset"], DOWNLOAD_TIMEOUT, have) as response:
            resumed = have and response.status == 206
            if not resumed:
                have = 0
            with open(part, "ab" if resumed else "wb") as file:
                while chunk := response.read(CHUNK):
                    file.write(chunk)
                    have += len(chunk)
                    report(len(chunk))
    if sha256(part) != entry["sha256"]:
        part.unlink()
        raise OSError(f"{entry['name']} arrived damaged; it will be fetched again")
    part.replace(target)


def reuse(source, target):
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def update(ui):
    held = lock()
    try:
        with fetch("manifest.json", MANIFEST_TIMEOUT) as response:
            manifest = json.load(response)
        version = manifest["version"]
        previous = current_version()
        if version == previous:
            return False

        have = installed_files(previous)
        staging = VERSIONS / f"{version}.partial"
        staging.mkdir(parents=True, exist_ok=True)
        pending = [f for f in manifest["files"]
                   if f["sha256"] not in have and not (staging / f["name"]).exists()]
        total = sum(f["size"] for f in pending) or 1
        done = 0

        def report(count):
            nonlocal done
            done += count
            ui.progress(min(done / total, 1), f"Updating {NAME}")

        for entry in manifest["files"]:
            target = staging / entry["name"]
            if entry in pending:
                download(entry, target, report)
            elif not target.exists():
                reuse(have[entry["sha256"]], target)
            target.chmod(int(entry["mode"], 8))
        (staging / "manifest.json").write_text(json.dumps(manifest))

        final = VERSIONS / version
        shutil.rmtree(final, ignore_errors=True)
        staging.replace(final)
        pointer = HOME / "current.new"
        pointer.write_text(version)
        pointer.replace(CURRENT)

        for old in VERSIONS.iterdir():
            if old.name not in (version, previous):
                shutil.rmtree(old, ignore_errors=True)
        subprocess.run([sys.executable, str(final / "deck.py"), "setup"], check=False)
        return True
    finally:
        held.close()
        ui.close()


def write(path, text, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, newline="\n")
    path.chmod(mode)


def setup():
    home = shlex.quote(str(HOME))
    write(LAUNCHER, f"""#!/bin/sh
home={home}
[ $# -eq 0 ] && set -- play
exec python3 "$home/versions/$(cat "$home/current")/deck.py" "$@"
""", 0o755)
    write(DESKTOP_ENTRY, f"""[Desktop Entry]
Type=Application
Name={NAME}
Exec="{LAUNCHER}"
Terminal=false
Categories=Game;
""")
    write(UNITS / f"{UPDATE_UNIT}.service", f"""[Unit]
Description=Fetch the latest {NAME}

[Service]
Type=oneshot
ExecStart="{LAUNCHER}" update
""")
    write(UNITS / f"{UPDATE_UNIT}.timer", f"""[Unit]
Description=Look for a new {NAME} every quarter of an hour

[Timer]
OnStartupSec=1min
OnCalendar=*:0/15
Persistent=true
RandomizedDelaySec=1min

[Install]
WantedBy=timers.target
""")
    for arguments in (["daemon-reload"], ["enable", "--now", f"{UPDATE_UNIT}.timer"]):
        try:
            subprocess.run(["systemctl", "--user", *arguments], check=False,
                           capture_output=True)
        except OSError:
            break


def in_steam_library():
    for root in (DATA_HOME / "Steam", Path.home() / ".steam/steam"):
        for shortcuts in root.glob("userdata/*/config/shortcuts.vdf"):
            if str(LAUNCHER).encode() in shortcuts.read_bytes():
                return True
    return False


def add_to_steam():
    if in_steam_library():
        return True
    if not shutil.which("steamos-add-to-steam"):
        return False
    return subprocess.run(["steamos-add-to-steam", str(DESKTOP_ENTRY)],
                          check=False).returncode == 0


def install():
    update(Console())
    setup()
    print(f"\n{NAME} is installed and will keep itself up to date.")
    if add_to_steam():
        print("Return to Gaming Mode: it is in your Library under Non-Steam.")
    else:
        print(f"Start it from the application menu, or add {LAUNCHER} to Steam "
              f"with Games > Add a Non-Steam Game.")


def play(arguments):
    try:
        update(Dialog())
    except Exception as error:
        print(f"Not updated: {error}", file=sys.stderr)
    version = current_version()
    if not version:
        message = f"{NAME} could not be downloaded. Check the internet connection."
        subprocess.run(["zenity", "--error", f"--title={NAME}", f"--text={message}"],
                       check=False)
        sys.exit(message)
    directory = VERSIONS / version
    os.chdir(directory)
    binary = str(directory / GAME_BINARY)
    os.execv(binary, [binary, *arguments])


def main():
    command, *arguments = sys.argv[1:] or ["install"]
    try:
        if command == "install":
            install()
        elif command == "setup":
            setup()
        elif command == "update":
            print("Updated." if update(Console()) else "Already up to date.")
        elif command == "play":
            play(arguments)
        else:
            sys.exit("usage: deck.py [install|update|play|setup]")
    except Busy as busy:
        print(f"Skipped: {busy}.")
    except OSError as error:
        sys.exit(f"{NAME} could not be updated: {error}")


if __name__ == "__main__":
    main()
