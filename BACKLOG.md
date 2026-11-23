# Backlog

## 1. Confirm the Steam Deck install on the real Deck

### Task description
Julia runs the install line once on her Steam Deck. Confirm the game appears and runs in Gaming Mode, then fix whatever the real Deck shows that the Linux check could not cover: the Steam library entry, the update progress window, the background update timer and fullscreen.

### Open questions
- Does the game show up under Non-Steam in Gaming Mode after the install?

### Status
Built and published; every push to `main` publishes a build the Deck fetches by itself. Install, update and game start pass on a GitHub Linux runner. Not yet run on the Deck. The line, typed in Konsole in Desktop Mode: `curl https://juliargassiot.github.io/infinity-julia/deck|sh`
