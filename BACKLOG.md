# Backlog

## 17. Player character look, second pass

### Task description
The base in `game/characters/player/` works (rig, sockets, color parameters, animations) but needs to reach Infinity Nikki quality: a more dimensional face with stronger lips and natural eyes, fuller and softer hair with clean stylized highlights, a clearer thin-hourglass figure between Nikki and Bayonetta, relaxed hands, warmer skin that also works for dark tones, and smoother walk and run cycles. Then swap her into `game/player/player.tscn` in place of the capsule, so she appears on the Deck.

### Open questions
- Julia's feedback on the first renders.

### Status
Not started. First renders were sent to Julia for review.

## 6. Character creator

### Task description
At the start of the game, the player picks a magical race (werewolf, vampire, mermaid, witch or fae) and customizes hair color, skin color and eye color, with the character shown live, turning on a pedestal. Saved with the game. Each race gets a placeholder trait (ears, fangs, fins, hat, wings) until item 7.

### Open questions
- Besides colors, what can be customized: hairstyle, face shape, makeup, height?
- Besides movement, does race change abilities?

### Status
Not started. The character is in `game/characters/player/`, with color parameters and sockets. Save into the `Save` autoload (`game/save/`) with its own section.

## 7. Race designs

### Task description
Design each race's look on the base character, in the Infinity Nikki style with a touch of spookiness: werewolf ears, tail and claws; vampire fangs, pale glow and red eyes; mermaid scales and a tail form in water; witch markings and a hat; fae wings and pointed ears. Start with design sheets rendered in Blender for Julia to choose from, then build the chosen designs.

### Open questions
- Can werewolves fully transform, and do mermaids get legs on land?

### Status
Not started. The character is in `game/characters/player/`, with color parameters and sockets. Probably splits into one item per race after the design sheets.

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
Not started. Needs item 8.

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
Not started. Movement is in `game/player/`; quests grant the familiar with a `familiar` grant on `Quests.granted` (`game/quests/`).

## 14. Wardrobe and outfits

### Task description
Fashion is central: many outfits over time, in slots for underclothes, bottoms, tops, dresses and one-pieces, socks, shoes, necklace, bracelets on each wrist, arm cuffs on each bicep, a multi-ring set on each hand, earrings, facial jewelry, head accessories and hairstyles, plus body features (fairy, feathered or bat wings, halos, horns) on their own sockets. Pieces skin to the character's skeleton, move with cloth physics and hide covered body parts. Build the slot system, a wardrobe screen, the sparkly outfit-change effect, and style tags (elegant, gothic, cute, wild, ethereal) that events judge. Make three starter outfits in different styles.

### Open questions
- How are new pieces earned: bought, crafted at the tailor, quest rewards, or all three?

### Status
Not started. The character is in `game/characters/player/`, with color parameters and sockets. Quest rewards arrive as `item` grants on `Quests.granted` (`game/quests/`); the wardrobe should take them.

## 15. First race social event

### Task description
Build the event system and the first event, a witch marsh gathering, as the game's version of a farming-sim festival. The player is invited through a quest, arrives at a decorated venue with a dress code, mingles with NPCs in conversations where good answers win favor, and is judged on how well her outfit fits the event's style tags. A strong showing earns standing toward a title like "It Girl". Each later race gets its own event built on the same system.

### Open questions
- The title's name is decided later; "It Girl" is a placeholder.
- Do events happen on a calendar, like festivals, or when the story reaches them?
- Can the player fail an event and try again?

### Status
Not started. Needs item 14. Quests can invite with an `invite` grant (`game/quests/`).

## 16. Title screen and storybook font

### Task description
A title screen for the Deck: New game, Continue (from the save in `game/save/`), and Settings (volume, readout, camera sensitivity). Bundle an open-licence storybook serif font in a `third_party` folder and use it across the game's screens, because SteamOS lacks the laptop's Palatino and Georgia fallbacks. The title screen should be pretty: a slow camera drift over Crossroads Village at golden hour, with the game's name.

### Open questions
- What is the game called?

### Status
Not started. The screens' theme is in `game/ui/`.
