# save

`save.gd` is the `Save` autoload: the game's one save file, `user://save.json`. Each system keeps a section of it, a dictionary of plain data under its own name: `quests` for quest progress, `world` for the open gates and where the player stands. The character creator adds its own section the same way.

- A system reads its section with `Save.section(name)` when the game loads; autoloads listen to `Save.loaded`, scene nodes read it when they enter the tree.
- On `Save.saving` each system writes its section; `Save.write()` then writes the file. Any system calls `write()` when something worth keeping happened. Quests save at every change, and closing the window saves too.
- `Save.use(file)` plays from another file, or a new game when it does not exist; to load during play, call it and reload the main scene. An empty file name is a game that is never saved: scripted test runs use it unless they pass `save=` (see `tools/run/README.md`).
