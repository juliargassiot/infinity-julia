Peter's rules, which bind every session, are in @DEV.md.

## The game

Julia's vision: a heavily quest-based, high-fantasy magic game in the Infinity Nikki style, with more spookiness. The world is a limited open world: areas are explored freely, but quests unlock them gradually, in a rough order. The races are werewolves, vampires, mermaids, witches and fae. The player chooses a race and customizes looks such as hair and skin color. The game starts in Crossroads Village, at the center of the map. The mood changes with the area and situation, and later battles bring genuinely scary enemies. A familiar, a pet companion, follows the player; she chooses its form (fox-like, cat-like and so on) and its colors. Fashion is a major sub-game: each race holds a fashion show or social event, the game's version of farming-sim festivals, where the right outfit and good conversations win the player a title like "It Girl" (name to be decided).

## Tools

On the laptop; neither Godot nor Blender is on PATH.

- Godot 4.7.2: `%LOCALAPPDATA%\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_*\Godot_v4.7.2-stable_win64_console.exe`
- Blender 5.3: `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`
- Export templates, Linux and Windows x86_64 only: `%APPDATA%\Godot\export_templates\4.7.2.stable`
- Python: run scripts with `py -3` (3.12). The Microsoft Store `python` cannot see the export templates, so exports started from it fail.
- The laptop GPU is an Intel Iris Xe (D3D12, Forward+). Heavy effects run slowly here; the Steam Deck is the performance target.

## Build and run

- Check visual work by rendering it and looking at the PNG: `py -3 tools/run/quiet.py --path game --fixed-fps 60 -s ../tools/run/screenshot.gd -- res://main.tscn build/shots/main.png`.
- Never open Godot windows on Julia's screen for tests: run Godot through `tools/run/quiet.py` (hidden desktop). Scripted play and frame times: `tools/run/drive.gd`; see `tools/run/README.md`.
- Every push to `main` publishes a Steam Deck build that Julia's Deck fetches by itself (`tools/deck`). The push fails if the export fails; a GitHub workflow then test-installs the build on Linux. Check that run after pushing game changes: `gh run list --workflow deck.yml`.

## Where things are

- `game/` is the Godot project, `art/` holds Blender sources, `tools/` holds scripts.
- The map is in `game/world/`: each area is its own scene, streamed in around the camera; quests open area gates with `World.open_gate(id)`.
- `.claude/skills/backlog-fan` runs several backlog items in parallel when Julia says "backlog fan".

## Repository

- `tools/check_docs.py` enforces the four documentation rules in `DEV.md`. It runs as the git pre-commit hook (`tools/hooks`) and as Claude hooks (`.claude/settings.json`). After cloning: `git config core.hooksPath tools/hooks`.
- The checker pins a hash of each immutable section of `DEV.md`; update a hash only when the person named in that section asked for the change.
- Folders named `third_party` hold downloads with their licenses; every other directory is first-party. The repository is public, so they may only hold files whose licenses allow redistribution.
- Claude's automatic memory is off; this file is the memory.
