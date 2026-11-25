# Backlog

## 1. Build stamp and frame-rate readout on the Deck

### Task description
Show the build version and the frame rate in a corner of the screen, toggled with a button, so Julia can tell which build the Deck is running and whether it holds 60 fps. Use the first push of this change to confirm that the Deck updates itself: Julia starts the game and sees the new stamp.

### Open questions
- Which Deck button toggles the readout?
- Does the update progress window appear in Gaming Mode?

### Status
Not started. The install is confirmed on Julia's Deck; an automatic update has not been observed there yet.

## 2. Hidden test runs and scripted play

### Task description
Borrow two tools from Peter's `eccco3/clockwork-knight`. First, `dev/quiet.py`: run Godot on a hidden Windows desktop so test windows never appear on Julia's screen, also when several agents work at once. Second, a scripted-play harness like his `dev/drive`: play a list of inputs at a fixed 60 fps, take screenshots and record frame times. Make `tools/screenshot.gd` use both.

### Open questions
- Does the hidden desktop render correctly on the Iris Xe with D3D12?

### Status
Not started. Peter's versions assume a `toolchain/` folder; here Godot is found through the path in `CLAUDE.md`.
