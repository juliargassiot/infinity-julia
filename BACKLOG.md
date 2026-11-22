# Backlog

## 1. Prepare the project and install larger dependencies

### Task description
Install Godot and Blender on this laptop, create the Godot project skeleton and first-party directory layout, and download the larger free dependencies the game needs. Add .gitignore and LFS patterns matching the layout.

### Open questions
- Which Godot version and renderer? Forward+ looks best but must hold a playable frame rate on the Steam Deck.
- Which dependencies count as "larger" beyond Godot and Blender (export templates, scan libraries, HDRIs, mocap sets)?
- The laptop has about 71 GB free. Is that enough, or should assets go on another drive?

### Status
Not started.

## 2. Write the deterministic controls

### Task description
Write scripts that enforce the four documentation rules in CLAUDE.md: only CLAUDE.md and BACKLOG.md as global docs, Claude's notes at most 600 words, backlog items limited to the three sections at 100 words each, and one document of at most 300 words per first-party directory. Wire them in so violations block the work.

### Open questions
- Enforce through a git pre-commit hook, a Claude Code hook, or both?
- Should the controls also protect the immutable sections of CLAUDE.md from edits?
- How are first-party directories told apart from downloaded ones?

### Status
Not started.

## 3. Playable on the Steam Deck with automatic updates

### Task description
Make the game playable on Julia's Steam Deck, which is on the home network. This laptop stays the development machine. The Deck should receive the latest version automatically with as little involvement from Julia as possible, and bootstrapping the Deck to play and receive updates should need as little typing on the Deck's keyboard as possible.

### Open questions
- Push builds from the laptop over the network, or have the Deck pull them from GitHub?
- What is the least-typing bootstrap: a single short command, or a file fetched in the Deck's browser?
- Should the game appear in Gaming Mode as a non-Steam game?

### Status
Not started. Depends on item 1.
