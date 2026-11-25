# Backlog

## 3. Player character base

### Task description
Sculpt, retopologize and rig an original anime-styled player body in Blender: doll-like face, clean topology, face rig for expressions, and one flowing hairstyle with bones for hair motion. Give her soft, slightly translucent PBR skin and stylized hair highlights in Godot, with skin and hair color exposed as parameters for the character creator. Import into Godot with an idle animation and check close-up screenshots. Placeholder outfit only.

### Open questions
- None. Settled: the player is always a young woman, as in Infinity Nikki.

### Status
Not started. Independent of items 4 and 5.

## 4. Movement and camera

### Task description
A third-person controller with a placeholder capsule: walk, run and jump, plus an orbiting camera that avoids walls. Steam Deck controls first (sticks, buttons, gyro optional), keyboard and mouse second. Movement should feel light and graceful. Test on a simple ground with slopes, steps and ledges, and record frame times with `tools/run/drive.gd`. Air movement depends on race: build it as swappable abilities, with a floaty glide as the first.

### Open questions
- None. Settled: air movement depends on race (fae fly, mermaids swim fast, others to be designed in item 7).

### Status
Not started. Swaps the capsule for the item 3 character once both are done.

## 5. Crossroads Village blockout

### Task description
Gray-box Crossroads Village at the center of the map: a crossroads with roads toward the lands of each race (werewolf forest, vampire estate, mermaid coast, witch marsh, fae glade), each closed by a natural gate (a broken bridge, a thorn wall, fog) that a quest will later open. Lay out the village (square, tailor's outfit shop, magic shop, inn, quest notice board, houses, landmarks) at walking scale, add golden-hour lighting, fog and sky, and plan area loading so the map can grow while holding 60 fps on the Deck. Screenshots from ground level.

### Open questions
- In what order do the lands after the witch marsh open? Julia chose the witch marsh first, nearest the village.

### Status
Not started.

## 6. Character creator

### Task description
At the start of the game, the player picks a magical race (werewolf, vampire, mermaid, witch or fae) and customizes hair color, skin color and eye color, with the character shown live, turning on a pedestal. Saved with the game. Each race gets a placeholder trait (ears, fangs, fins, hat, wings) until item 7.

### Open questions
- Besides colors, what can be customized: hairstyle, face shape, makeup, height?
- Besides movement, does race change abilities?

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
