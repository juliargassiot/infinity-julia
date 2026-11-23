# Backlog

## 1. Write the deterministic controls

### Task description
Write scripts that enforce the four documentation rules in CLAUDE.md: only CLAUDE.md and BACKLOG.md as global docs, Claude's notes at most 600 words, backlog items limited to the three sections at 100 words each, and one document of at most 300 words per first-party directory. Wire them in so violations block the work.

### Open questions
- Enforce through a git pre-commit hook, a Claude Code hook, or both?
- Should the controls also protect the immutable sections of CLAUDE.md from edits?

### Status
Not started. First-party means every directory not named `third_party`.

## 2. Playable on the Steam Deck with automatic updates

### Task description
Make the game playable on Julia's Steam Deck, which is on the home network. This laptop stays the development machine. The Deck should receive the latest version automatically with as little involvement from Julia as possible, and bootstrapping the Deck to play and receive updates should need as little typing on the Deck's keyboard as possible.

### Open questions
- Push builds from the laptop over the network, or have the Deck pull them from GitHub?
- What is the least-typing bootstrap: a single short command, or a file fetched in the Deck's browser?
- Should the game appear in Gaming Mode as a non-Steam game?

### Status
Not started. The Godot project and Linux export templates are in place. Peter allows making the repository public if that helps.
