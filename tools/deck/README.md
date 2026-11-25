# deck

Delivers the game to the Steam Deck. The laptop builds; the Deck pulls from GitHub, so it also updates away from home.

- `publish.py` exports the `Steam Deck` preset and uploads it to the rolling GitHub release `deck`: content-hashed files first, `manifest.json` last, so the Deck never sees a half-published build. `../hooks/pre-push` runs it on every push to `main`; it skips when `game/` and `deck.py` are unchanged since the published commit. `--force` republishes. Its `manifest.json` carries the build's `version` (the commit) and `date`; the game's readout (`F3`) shows them from the copy beside its binary, or `build dev` without one.
- `deck.py` runs on the Deck and uses only the Python standard library. `install` sets everything up, `update` downloads the files that changed into `~/.local/share/infinity-julia/versions/<commit>`, and `play` updates and then starts the game. It ships inside every build, so it updates itself; after an update the new copy's `setup` rewrites the launcher, the menu entry and the systemd user timer that looks for a build every 15 minutes.

Bootstrap, typed once in Konsole in Desktop Mode:

    curl https://juliargassiot.github.io/infinity-julia/deck|sh

That page is a two-line stub on the orphan `gh-pages` branch; it pipes the release's `deck.py` into `python3`. Install also adds the game to Steam with `steamos-add-to-steam`.

`.github/workflows/deck.yml` repeats that install on a Linux runner after every publish and starts the game headless.

To test without GitHub, serve `build/deck/upload` with `python -m http.server` and point `INFINITY_JULIA_URL` at it.
