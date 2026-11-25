# ui

The screen over the world, styled as a storybook by `theme.tres` (the project's theme): parchment panels, plum name plates, gold accents, a serif from the system.

`hud.tscn` belongs inside the World (`../main.tscn` has it). It shows the followed quest at the top left, notes at the top when quests change, a prompt for the nearest thing within reach, and:

- `objective_marker.gd`: gold gems over what the followed quest's step is about, with the distance; off screen, at the edge, pointing the way.
- `dialogue_box.gd`: conversations, line by line; choices are buttons.
- `journal.gd`: the quest journal, an open book. Picking a quest follows it.
- `button_hint.gd`: a button's label as printed on the Steam Deck while a controller is in use, or the key otherwise.

The game pauses while a conversation or the journal is open, and resumes once their buttons are let go, so closing one never makes her jump.

| | Steam Deck | Keyboard |
|---|---|---|
| talk, read, pick up | X | E |
| journal | View | J |
| next line, choose | A | Enter, Space |
| close | B | Esc |
| move in menus | D-pad, left stick | arrow keys |
