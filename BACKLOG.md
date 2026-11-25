# Backlog

## 3. Player character base

### Task description
Sculpt, retopologize and rig an original anime-styled player body in Blender: doll-like face, clean topology, face rig for expressions, and one flowing hairstyle with bones for hair motion. Give her soft, slightly translucent PBR skin and stylized hair highlights in Godot, with skin and hair color exposed as parameters for the character creator. Import into Godot with an idle animation and check close-up screenshots. Placeholder outfit only.

### Open questions
- None. Settled: the player is always a young woman, as in Infinity Nikki.

### Status
In progress on a branch.

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
Design each race's look on the base character, in the Infinity Nikki style with a touch of spookiness: werewolf ears, tail and claws; vampire fangs, pale glow and red eyes; mermaid scales and a tail form in water; witch markings and a hat; fae wings and pointed ears. Start with design sheets rendered in Blender for Julia to choose from, then build the chosen designs.

### Open questions
- Can werewolves fully transform, and do mermaids get legs on land?

### Status
Not started. Needs item 3. Probably splits into one item per race after the design sheets.

## 8. Area moods

### Task description
Make the mood follow the place and the situation: each area has a mood (light color, fog, sky, color grading, particles, music) that blends smoothly as the player crosses borders, and events such as nightfall or danger can push it darker. Bright storybook in Crossroads Village; eerie, moonlit and misty toward the vampire estate and the werewolf forest. Include per-area ground tints (the terrain now colors by height only, so the marsh reads sandy). Build the system with two or three example moods.

### Open questions
- None. Settled: there is a day and night cycle, nights are darker and spookier, and some monsters come out only after dark (they arrive with item 9).

### Status
Not started. The village and the area streaming are in `game/world/`.

## 9. First battle and a scary enemy

### Task description
A first combat prototype: the player fights with magic suited to their race, against one original enemy that looks genuinely frightening but still fits the high-fantasy style, such as a hollow-eyed corrupted creature from the woods. Includes the enemy's model, rig and animations, a simple attack and dodge, health, and the area mood darkening during the fight.

### Open questions
- Should fights be fast action, like a brawler, or slower and spell-based?
- How scary is too scary: unsettling, or real horror?

### Status
Not started. Needs items 3 and 8.

## 10. Quests and area unlocking

### Task description
The game is heavily quest-based, and quests unlock the map gradually. Build the quest system: quests written as data files (steps, objectives, rewards, what they unlock), talking to villagers with dialogue choices, a quest journal, objective markers, and saving progress. Completing a quest can open an area gate from item 5. Prove it with a short first quest in Crossroads Village that opens the road to the first area.

### Open questions
- None. Settled: the main story is decided later, so the first main quest is a placeholder. Side quests are on the notice board from the start; include one example.

### Status
In progress on a branch. The village and area gates are in `game/world/`; quests open gates with `World.open_gate(id)`, and gate state still needs saving.

## 12. Seal the map borders

### Task description
Gates close the roads to locked lands, but a player can still glide over the stream ravine elsewhere, climb the gentler hills around a gate, or walk off the map edge. Shape the terrain and scenery around each gate and along the map border (cliffs, thick woods, deep water) so locked lands stay out of reach and the edge never shows, without invisible walls where possible. Verify with drive.gd runs that try to get around each gate.

### Open questions
- None.

### Status
In progress on a branch. The map is in `game/world/`; terrain shapes and paths bake into one heightmap.

## 13. Familiar companion

### Task description
A familiar, a magical pet, follows the player around the world: it trots after her, waits, plays idle animations and reacts to her (happy when she returns, curious about objects). The player picks one of several forms, each with its own animal vibe (fox-like, cat-like and others) but all clearly magical, and customizes its colors. Build the follow behavior and the first two forms with models, rigs and animations, plus the choice and coloring screen. Cute but able to look a little eerie at night.

### Open questions
- None. Settled: six forms (fox, cat, owl, bunny, dragonling, moth); this item builds fox and cat, the rest follow. It fights alongside her in battles (item 9), and she meets it in an early quest in Crossroads Village (item 10).

### Status
Not started. Movement is done in `game/player/`.

## 14. Wardrobe and outfits

### Task description
The heart of the fashion sub-game: outfits made of swappable pieces (hair accessory, top, bottom or dress, shoes, accessories) that fit the player character and move with cloth physics, a wardrobe screen to dress her, and the sparkly transformation effect when switching outfits. Each piece carries style tags (elegant, gothic, cute, wild, ethereal and so on) that events can judge. Make three complete starter outfits in clearly different styles. The tailor's shop in the village will later sell and craft pieces.

### Open questions
- How are new pieces earned: bought, crafted at the tailor, quest rewards, or all three?

### Status
Not started. Needs item 3.

## 15. First race social event

### Task description
Build the event system and the first event, a witch marsh gathering, as the game's version of a farming-sim festival. The player is invited through a quest, arrives at a decorated venue with a dress code, mingles with NPCs in conversations where good answers win favor, and is judged on how well her outfit fits the event's style tags. A strong showing earns standing toward a title like "It Girl". Each later race gets its own event built on the same system.

### Open questions
- The title's name is decided later; "It Girl" is a placeholder.
- Do events happen on a calendar, like festivals, or when the story reaches them?
- Can the player fail an event and try again?

### Status
Not started. Needs items 10 and 14.
