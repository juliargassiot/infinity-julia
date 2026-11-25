---
name: backlog-fan
description: Fan up to three independent backlog items out to subagents in their own worktrees, and merge each into main as it finishes. Use when Julia says "backlog fan".
---

## Pick

Choose up to three independent items: none needs another's result or edits the same files or shared modules. First settle in the main chat, in plain language, every open question that needs Julia's input. Questions that need investigation go to the agent, which reports what it found.

## Model and effort

- Most difficult (sculpting, rigging, animation, shaders, lighting, judgement across many files): Fable, high (Opus, max, once Fable usage runs out).
- Moderate: Opus, high.
- Simple and mechanical: Sonnet, medium.

## Brief

Run each in the background in its own worktree, told to:

- Merge `origin/main` first, then read CLAUDE.md and DEV.md and its item in BACKLOG.md.
- Copy the gitignored files it needs from the main checkout; never write outside its worktree.
- Avoid other agents' files and any tools you name as off-limits.
- Leave the code in the shape it should have. No special cases, duplicated logic or reaching into another module's internals for speed. If the right change would collide with parallel work, report it as a follow-up instead of working around it.
- Leave BACKLOG.md alone, commit on its branch, push it, and not merge.
- Report its branch, commit, results, screenshot paths, open-question answers and anything unverified.

## Merge

As each agent finishes, check its diff and screenshots. In your own worktree, merge its branch onto `origin/main`, clear its item, run `tools/check_docs.py`, and push to main as a fast-forward. Each push publishes a Steam Deck build: push one merge at a time. Never merge inside another session's checkout. Relay new rules on main to agents still running.
