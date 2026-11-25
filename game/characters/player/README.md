# player character

The player's visible body. The `.glb` files come from `art/characters/player/build.py`.

`player_character.tscn` is a `PlayerBody`: she faces +Z, feet at the origin, 1.71 m tall. `locomotion.gd` blends `idle`, `walk`, `run`, `rise`, `fall` and `glide` from `show_motion`.

**Look.** `skin_color`, `hair_color` and `eye_color` reach every mesh as instance shader parameters. The `Face` mesh has ARKit-named blend shapes (`eyeBlinkLeft`, `jawOpen`, `mouthSmileRight`, ...); `LeftEye` and `RightEye` bones turn the eyes.

**Pieces.** Everything she wears is a scene modelled in place on her rest pose, put on with `wear(slot, piece, bone, covers)` and removed with `take_off(slot)`:

- Without a bone, the piece's meshes are skinned to her skeleton: clothing, shoes, a ring set on the finger bones.
- With a bone, the piece rides on it: rigid jewelry on a socket, or a piece with its own skeleton such as a hairstyle (on `Head`; `hair_springs.gd` swings its `Hair..._n` chains), wings or a tail.
- `covers` names regions to hide on her body and on other pieces, so nothing pokes through: `Chest`, `Waist`, `Hips`, and per side `Shoulder`, `Bicep`, `Elbow`, `Forearm`, `Wrist`, `Hand`, `Thigh`, `Knee`, `Calf`, `Ankle`, `Foot` (`LeftCalf`). Wings cover `WingOpening`, the patch a garment's back opens with. Garment shaders include `regions.gdshaderinc`.

**Sockets** are bones named `<Name>Socket`: `Necklace`, `Wings`, `Tail`, `Halo`, `Hat`, `Septum`, and left and right `Bracelet`, `ArmCuff`, `Earring`, `Nostril`, `Brow`, `Horn`, `AnimalEar`, `HairClip` (`LeftHornSocket`).

**Preview.** `preview.tscn` is a stage with the cameras `ThreeQuarter`, `Front`, `Side`, `Back`, `Bust` and `Closeup`:

    py -3 tools/run/quiet.py --path game --fixed-fps 60 --resolution 1280x800 -s ../tools/run/screenshot.gd -- res://characters/player/preview.tscn build/shots/run.png 90 view=Side speed=6.5 hair=4060c0

Other options: `vertical=<m/s>`, `air=glide` (or `air=jump`), `skin=`, `eyes=`.
