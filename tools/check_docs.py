#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
HOOKS_PATH = "tools/hooks"

GLOBAL_DOCS = {"CLAUDE.md", "DEV.md", "BACKLOG.md"}
DOC_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".org",
                ".rtf", ".doc", ".docx", ".odt", ".pdf"}
DOC_NAMES_WITHOUT_SUFFIX = {"readme", "notes", "todo", "changelog"}
NOT_DOCS = {"requirements.txt", "cmakelists.txt", "robots.txt"}
LICENSE_PREFIXES = ("license", "licence", "copying")

DIRECTORY_DOC_WORDS = 300
NOTES_WORDS = 600
BACKLOG_SECTION_WORDS = 100
BACKLOG_SECTIONS = ["Task description", "Open questions", "Status"]

NOTES_POINTER = "@DEV.md"
IMMUTABLE_BLOCKS = {
    "immutable without Peter’s (Julia’s husband developer) blessing":
        "9bd538b7cf520d0de090c39b854d77a30eda7b0ba2eff05a0a73b773860d7b6d",
}


def words(text):
    return len(text.split())


def git(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    return result.stdout.decode("utf-8", "replace")


def read(path):
    return (ROOT / path).read_text(encoding="utf-8").replace("\r\n", "\n")


def is_document(path):
    name = path.name.lower()
    if name in NOT_DOCS or name.startswith(LICENSE_PREFIXES):
        return False
    return path.suffix.lower() in DOC_SUFFIXES or name in DOC_NAMES_WITHOUT_SUFFIX


def first_party_documents():
    listed = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    paths = (PurePosixPath(p) for p in listed.split("\0") if p)
    return [p for p in paths
            if "third_party" not in p.parts[:-1]
            and is_document(p)
            and (ROOT / p).is_file()]


def check_documents():
    by_directory = defaultdict(list)
    for path in first_party_documents():
        by_directory[path.parent].append(path)

    for directory, docs in sorted(by_directory.items()):
        if directory == PurePosixPath("."):
            for doc in docs:
                if doc.name not in GLOBAL_DOCS:
                    yield (f"{doc}: the only global documents are CLAUDE.md, DEV.md "
                           f"and BACKLOG.md. Delete it or fold it into one of them.")
            continue
        if len(docs) > 1:
            names = ", ".join(sorted(d.name for d in docs))
            yield f"{directory}/: has {len(docs)} documents ({names}); one is allowed."
        for doc in docs:
            try:
                count = words(read(doc))
            except UnicodeDecodeError:
                yield f"{doc}: documents must be plain UTF-8 text."
                continue
            if count > DIRECTORY_DOC_WORDS:
                yield f"{doc}: {count} words; the limit is {DIRECTORY_DOC_WORDS}."


def tagged_blocks(text):
    blocks, stray, name, body = {}, [], None, []
    for number, line in enumerate(text.split("\n"), 1):
        if name is None:
            opening = re.fullmatch(r"<([^/].*)>", line)
            if opening:
                name, body = opening.group(1), []
            elif line.strip():
                stray.append(number)
        elif line == f"</{name}>":
            blocks[name] = "\n".join(body).strip()
            name = None
        else:
            body.append(line)
    return blocks, stray, name


def check_dev_md():
    blocks, stray, unclosed = tagged_blocks(read("DEV.md"))
    if unclosed:
        yield f"DEV.md: the <{unclosed}> block is never closed."
    if stray:
        yield (f"DEV.md: line {stray[0]} is outside the immutable blocks; "
               f"Claude's text belongs in CLAUDE.md.")
    if list(blocks) != list(IMMUTABLE_BLOCKS):
        yield ("DEV.md: must hold exactly these blocks in order: "
               + ", ".join(f"<{b}>" for b in IMMUTABLE_BLOCKS))
        return
    for name, expected in IMMUTABLE_BLOCKS.items():
        actual = hashlib.sha256(blocks[name].encode("utf-8")).hexdigest()
        if actual != expected:
            yield (f"DEV.md: the <{name}> block was changed. Restore it, or if "
                   f"the person it names asked for the change, set its hash in "
                   f"tools/check_docs.py to {actual}")


def check_claude_md():
    pointer, _, notes = read("CLAUDE.md").partition("\n")
    if NOTES_POINTER not in pointer:
        yield f"CLAUDE.md: the first line must point to {NOTES_POINTER}."
    count = words(notes)
    if count > NOTES_WORDS:
        yield f"CLAUDE.md: Claude's notes are {count} words; the limit is {NOTES_WORDS}."


def check_backlog():
    lines = [line for line in read("BACKLOG.md").split("\n") if line.strip()]
    if not lines or lines[0] != "# Backlog":
        yield "BACKLOG.md: must start with the line '# Backlog'."
        return

    items, sections = [], None
    for line in lines[1:]:
        if line.startswith("## "):
            sections = []
            items.append((line[3:].strip(), sections))
        elif line.startswith("### ") and sections is not None:
            sections.append([line[4:].strip(), 0])
        elif line.startswith("#"):
            yield f"BACKLOG.md: unexpected heading '{line.strip()}'."
        elif not sections:
            yield (f"BACKLOG.md: text outside an item section: '{line.strip()[:50]}'. "
                   f"Items hold only: {', '.join(BACKLOG_SECTIONS)}.")
        else:
            sections[-1][1] += words(line)

    for title, sections in items:
        if [name for name, _ in sections] != BACKLOG_SECTIONS:
            yield (f"BACKLOG.md: item '{title}' must have exactly these sections "
                   f"in order: {', '.join(BACKLOG_SECTIONS)}.")
        for name, count in sections:
            if count > BACKLOG_SECTION_WORDS:
                yield (f"BACKLOG.md: '{name}' of item '{title}' is {count} words; "
                       f"the limit is {BACKLOG_SECTION_WORDS}.")


def check_git_hook():
    configured = git("config", "--get", "core.hooksPath").strip().replace("\\", "/")
    if not configured.rstrip("/").endswith(HOOKS_PATH):
        yield (f"The pre-commit hook is not installed. "
               f"Run: git config core.hooksPath {HOOKS_PATH}")


def hook_event():
    try:
        return json.loads(sys.stdin.buffer.read() or b"{}")
    except ValueError:
        return {}


def main():
    sys.stderr.reconfigure(encoding="utf-8")
    event = hook_event() if "--hook" in sys.argv else {}

    errors = []
    for check in (check_documents, check_dev_md, check_claude_md, check_backlog,
                  check_git_hook):
        try:
            errors.extend(check())
        except OSError as error:
            errors.append(f"{check.__name__}: {error}")
    if not errors:
        return 0

    print("Documentation rules in DEV.md are violated. Fix these before "
          "continuing:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    return 0 if event.get("stop_hook_active") else 2


if __name__ == "__main__":
    sys.exit(main())
