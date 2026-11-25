# player character source

The player is built by script from a CC0 base mesh, so every change is a code change and the result is reproducible:

    blender -b --python art/characters/player/build.py

It writes `player.blend` here and `player.glb`, `hair_flowing.glb` and `outfit_romper.glb` into `game/characters/player`. Look at the result without the game:

    blender -b art/characters/player/player.blend --python art/characters/player/preview.py -- <out folder> [walk@10] [-Hair] [+jawOpen] [front side face ...]

The steps, in build order:

- `cage.py` loads the base mesh as a cage with sculpting operations; its face sets name the body's areas.
- `body.py` sculpts her face and figure and sets her proportions.
- `landmarks.py` reads joints and attachment points (sockets) off the cage.
- `expressions.py` sculpts the face shapes, named after ARKit's blend shapes.
- `skin.py` subdivides the head (`subdivide.py`), paints the skin shader's masks into vertex colors, softens the face's normals and numbers the regions clothing can hide.
- `face.py` adds eyes, lashes, brows, teeth and tongue; `hair.py` the hairstyle with its bone chains; `outfit.py` the placeholder romper.
- `rig.py` makes the body's skeleton (Godot humanoid bone names, plus `...Socket` bones) and the hairstyle's own, and weights the skin.
- `anim.py` keys the animations as functions of time, with `figure.py` for posing and leg IK.
- `parts.py` holds the mesh data all of these pass around.

New clothing, hairstyles, jewelry, wings and tails are modelled in place on `player.blend`'s rest pose. Skin clothing to `Rig`; give a hairstyle or wings a skeleton of their own. Number a garment's faces in a second UV layer like the body's when other pieces should hide them.
