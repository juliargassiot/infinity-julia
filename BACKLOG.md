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

## 3. Player character base

### Task description
Sculpt, retopologize and rig an original anime-styled player body in Blender: doll-like face, clean topology, face rig for expressions, and one flowing hairstyle with bones for hair motion. Give her soft, slightly translucent PBR skin and stylized hair highlights in Godot, with skin and hair color exposed as parameters for the character creator. Import into Godot with an idle animation and check close-up screenshots. Placeholder outfit only.

### Open questions
- Is the player always a young woman, like Nikki, or can players choose a body type?

### Status
Not started. Independent of items 4 and 5.

## 4. Movement and camera

### Task description
A third-person controller with a placeholder capsule: walk, run, jump and a floaty glide, plus an orbiting camera that avoids walls. Steam Deck controls first (sticks, buttons, gyro optional), keyboard and mouse second. Movement should feel light and graceful. Test on a simple ground with slopes, steps and ledges, and record frame times with the scripted-play harness once item 2 lands.

### Open questions
- Should the glide need an outfit or ability, or be available from the start?

### Status
Not started. Swaps the capsule for the item 3 character once both are done.

## 5. Crossroads Village blockout

### Task description
Gray-box Crossroads Village at the center of the map: a crossroads with roads toward the lands of each race (werewolf forest, vampire estate, mermaid coast, witch marsh, fae glade), each closed by a natural gate (a broken bridge, a thorn wall, fog) that a quest will later open. Lay out the village (square, shops, houses, landmarks) at walking scale, add golden-hour lighting, fog and sky, and plan area loading so the map can grow while holding 60 fps on the Deck. Screenshots from ground level.

### Open questions
- What must the village have: a tailor, a magic shop, an inn, a notice board?
- Which race's lands lie in which direction, and in what order do they open?

### Status
Not started.

## 6. Character creator

### Task description
At the start of the game, the player picks a magical race (werewolf, vampire, mermaid, witch or fae) and customizes hair color, skin color and eye color, with the character shown live, turning on a pedestal. Saved with the game. Each race gets a placeholder trait (ears, fangs, fins, hat, wings) until item 7.

### Open questions
- Besides colors, what can be customized: hairstyle, face shape, makeup, height?
- Does race change abilities, or only looks and story?

### Status
Not started. Needs item 3.

## 7. Race designs

### Task description
Design each race's look on the base character, in the Infinity Nikki style with a touch of spookiness: werewolf ears, tail and claws; vampire fangs, pale glow and red eyes; mermaid scales and a tail form in water; witch markings and familiar; fae wings and pointed ears. Start with design sheets rendered in Blender for Julia to choose from, then build the chosen designs.

### Open questions
- Can werewolves fully transform, and do mermaids get legs on land?

### Status
Not started. Needs item 3. Probably splits into one item per race after the design sheets.

## 8. Area moods

### Task description
Make the mood follow the place and the situation: each area has a mood (light color, fog, sky, color grading, particles, music) that blends smoothly as the player crosses borders, and events such as nightfall or danger can push it darker. Bright storybook in Crossroads Village; eerie, moonlit and misty toward the vampire estate and the werewolf forest. Build the system with two or three example moods.

### Open questions
- Is there a day and night cycle, and do monsters come out at night?

### Status
Not started. Works best after item 5.

## 9. First battle and a scary enemy

### Task description
A first combat prototype: the player fights with magic suited to their race, against one original enemy that looks genuinely frightening but still fits the high-fantasy style, such as a hollow-eyed corrupted creature from the woods. Includes the enemy's model, rig and animations, a simple attack and dodge, health, and the area mood darkening during the fight.

### Open questions
- Should fights be fast action, like a brawler, or slower and spell-based?
- How scary is too scary: unsettling, or real horror?

### Status
Not started. Needs items 3, 4 and 8.

## 10. Quests and area unlocking

### Task description
The game is heavily quest-based, and quests unlock the map gradually. Build the quest system: quests written as data files (steps, objectives, rewards, what they unlock), talking to villagers with dialogue choices, a quest journal, objective markers, and saving progress. Completing a quest can open an area gate from item 5. Prove it with a short first quest in Crossroads Village that opens the road to the first area.

### Open questions
- What is the main story, and who sends the player out from the village?
- Are there side quests from the start?

### Status
Not started. Works best after items 4 and 5.
