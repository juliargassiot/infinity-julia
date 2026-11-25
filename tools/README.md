# tools

Scripts that support development; nothing here ships in the game.

- `check_docs.py` enforces the documentation rules in `../DEV.md` and exits with 2 when one is broken. `hooks/pre-commit` runs it before every commit and for the Claude hooks in `../.claude/settings.json`.
- `hooks/pre-push` publishes the Steam Deck build; see `deck/`.
- `run/` runs the game for tests on a hidden desktop: scripted play, screenshots and frame times.
