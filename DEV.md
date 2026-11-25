<immutable without Peter’s (Julia’s husband developer) blessing>
In this project you develop a game. The graphics and animation are extremely high quality and extremely detailed. Generic surface scans, environment lighting, anatomy references, motion capture, or base meshes as a starting point for body topology and rigging may be downloaded; all designs and most meshes are original. The animations are extremely fluid and realistic and the meshes have excellent topology and rigging. Animations can also be hand-keyed — be ambitious. The primary tools are Godot and Blender, but you can download anything that is free.

The user, Julia, is not a developer. Please build proactively build tooling when appropriate that makes it easier for her to test on the Steam Deck. Please optimize graphics for 60 fps on the steam deck.  She also doesn’t help with ballooning stale, duplicate, or obsolete documentation, the primary failure mode of vibecoding, the way a developer would. Accordingly, the following rules must be enforced deterministically:

1. The only global documentation is the CLAUDE.md, the DEV.md and the BACKLOG.md.
2. Claude’s notes in the CLAUDE.md do not exceed 600 words.
3. The backlog only contains a queue of top-level backlog items with the following sections, none of which may exceed a hundred words: task description, open questions, status.
4. There is only one directory-scoped document per first-party directory, and it does not exceed 300 words.

The following is not enforced deterministically, but scripts and application files prefer code over comments.

All tasks that would take more than a minute are processed into backlog items, each sized for one session. After completing a backlog item:

1. Clear the backlog item.
2. Commit and push to the remote without asking.
3. If appropriate, choose between /compact and /clear to recommend to Julia.

Never ask Julia whether to commit, merge or push: commit, merge and push whenever work is done. Only regressions are not merged.

Claude can use CLAUDE.md as memory.

Claude is the owner of the architecture of the codebase. You can proactively solve tech debt yourself. If a big refactor is needed, you can add it to the backlog.
</immutable without Peter’s (Julia’s husband developer) blessing>
<immutable without Julia’s permission>
The art style of this game is similar to Infinity Nikki — stylized anime-fantasy characters rendered with physically based lighting, in a bright storybook world.

1. Characters: soft, doll-like anime faces and proportions, but lit with PBR so they sit naturally in a realistic-lit world. Skin should look soft and slightly translucent; hair should have clean, stylized highlights.
2. Clothing: fabrics that read as real materials up close (satin sheen, velvet, lace, sheer layers, embroidery, sequins, metal trims).
3. Cloth and hair motion: skirts, sleeves, ribbons, and hair that flow and trail during running, jumping, and gliding, stay stable, and don't clip through the body.
4. World: a painterly, European-fairytale open world with saturated but harmonious color.
5. Lighting and atmosphere: warm golden-hour light, soft bloom, volumetric fog and god rays, floating sparkle particles, and pretty water reflections.
6. Animation feel: light, graceful, floaty character movement, expressive idle animations and small interactions, short sparkly "transformation" effects when switching outfits, and cinematic cutscenes with expressive faces.
7. Photo-mode-level quality, to the extent possible with these engines and resources. The game should hold up in close-up screenshots.

</immutable without Julia’s permission>
