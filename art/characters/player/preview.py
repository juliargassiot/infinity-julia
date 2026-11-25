"""Renders quick clay previews of the open .blend, for judging shapes without the game.

    blender -b art/characters/player/player.blend --python art/characters/player/preview.py -- <out folder> [<animation>@<frame>] [-<object to hide>] [+<expression>] [view ...]
"""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

# name: (height of the view centre as a fraction of the eye height, direction, view height)
VIEWS = {
    "front": (0.54, (0, -1, 0), 1.8),
    "side": (0.54, (1, 0, 0), 1.8),
    "back": (0.54, (0, 1, 0), 1.8),
    "face": (0.985, (0, -1, 0), 0.3),
    "face_34": (0.985, (0.6, -0.8, 0), 0.3),
    "face_side": (0.985, (1, 0, 0), 0.3),
    "bust": (0.9, (0.35, -0.94, 0.1), 0.75),
    "eye": (1.0, (0.25, -1, 0), 0.1),
    "mouth": (0.955, (0.3, -1, -0.1), 0.1),
    "hips": (0.6, (0.3, -1, 0.1), 0.7),
    "hips_side": (0.6, (1, -0.2, 0), 0.7),
}


def eye_height():
    eyes = bpy.data.objects.get("Eyes")
    if eyes:
        return sum(corner[2] for corner in eyes.bound_box) / 8.0 + eyes.location.z
    head = bpy.data.objects["Face"]
    return max(v.co.z for v in head.data.vertices) - 0.12


def show(animation, frame):
    """Poses the character as an animation has her at a frame."""
    for holder in (bpy.data.objects["Rig"], bpy.data.objects["Face"].data.shape_keys):
        for track in holder.animation_data.nla_tracks:
            track.mute = track.name != animation
    bpy.context.scene.frame_set(int(frame))


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    out = Path(args[0]).resolve()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "MATCAP"
    shading.studio_light = "clay_studio.exr"
    shading.color_type = "MATERIAL"
    scene.display.render_aa = "8"
    camera = bpy.data.objects.new("PreviewCamera", bpy.data.cameras.new("PreviewCamera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    views = [arg for arg in args[1:] if arg in VIEWS]
    for arg in args[1:]:
        if "@" in arg:
            show(*arg.split("@"))
        elif arg.startswith("-"):
            bpy.data.objects[arg[1:]].hide_render = True
        elif arg.startswith("+"):
            bpy.data.objects["Face"].data.shape_keys.key_blocks[arg[1:]].value = 1.0
    eyes = eye_height()
    for name in views or VIEWS:
        height, direction, size = VIEWS[name]
        direction = Vector(direction).normalized()
        centre = Vector((0.045 if name == "eye" else 0.0, 0.0, eyes * height))
        camera.data.ortho_scale = size
        camera.location = centre + direction * 5.0
        camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = (900, 1200) if size > 1 else (1000, 1000)
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)


main()
