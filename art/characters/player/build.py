"""Builds the player character from the base mesh: player.blend here and, in the game, her
model, her hairstyle and her placeholder outfit as separate files.

    blender -b --python art/characters/player/build.py
"""
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import anim
import body
import cage as cages
import expressions
import face
import hair
import landmarks
import outfit
import rig
import skin
from mathutils.bvhtree import BVHTree

from parts import to_object

ART = HERE.parent.parent
BLEND = HERE / "player.blend"
GAME = ART.parent / "game/characters/player"
# Preview colors; the game replaces these materials with its own of the same names.
MATERIALS = {
    "skin": (0.95, 0.76, 0.7), "eye": (0.9, 0.9, 0.95),
    "face_details": (0.2, 0.12, 0.12), "hair": (0.85, 0.55, 0.6), "outfit": (0.95, 0.93, 0.9),
}


def both_sides(part):
    return [part, part.mirrored()]


def export(name, objects, animations=False):
    """Writes objects as game/characters/player/<name>.glb."""
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj in objects)
    bpy.ops.export_scene.gltf(
        filepath=str(GAME / f"{name}.glb"), export_format="GLB", use_selection=True,
        export_yup=True, export_apply=False, export_materials="EXPORT",
        export_vertex_color="ACTIVE", export_all_vertex_colors=False,
        export_active_vertex_color_when_no_material=True, export_tangents=False,
        export_morph=True, export_morph_normal=True, export_morph_tangent=False,
        export_skins=True, export_animations=animations, export_animation_mode="NLA_TRACKS",
        export_cameras=False, export_lights=False, export_extras=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, color in MATERIALS.items():
        bpy.data.materials.new(name).diffuse_color = (*color, 1.0)
    cage = cages.load(ART)
    body.sculpt(cage)
    joints = landmarks.joints(cage)
    scale = body.HEAD_SCALE
    eye = joints["LeftEye"]

    shapes, face_rig = expressions.shapes(cage, eye, scale)
    skinned = skin.Skin(cage, skin.paint(cage, joints, scale), shapes,
                        skin.face_softness(cage, eye), skin.regions(cage, joints))
    head, torso = skinned.head, skinned.body
    surface = BVHTree.FromPolygons(skinned.points.tolist(),
                                   [polygon.tolist() for polygon in skinned.polygons])
    locks, hair_joints = hair.build(head, eye, scale, surface)

    sockets = landmarks.sockets(cage, joints, face_rig.on_face(*expressions.BROW_OUTER))
    armature = rig.body(joints, sockets)
    hair_rig = rig.hair(joints, hair_joints)
    weights = rig.heat_weights(armature, cage.co[:cage.count], cage.loop_verts.reshape(-1, 4),
                               rig.BODY_BONES)
    skinned.bind(weights, cage.in_sets(*cages.HEAD, blur=4)[:cage.count])
    bpy.data.meshes.remove(cage.mesh)

    objects = {
        "Face": [head, *both_sides(face.lashes(head, eye)), *both_sides(face.brow(head, eye, scale)),
                 face.mouth(face_rig, scale)],
        "Body": [torso],
        "Outfit": [outfit.romper(torso, sockets["Wings"][1])],
        "Eyes": face.eyes(head, eye, body.EYE_RADIUS * scale - face.EYE_INSET,
                          body.EYE_OPENING * scale, scale),
        "Hair": locks,
    }
    objects = {name: to_object(name, parts) for name, parts in objects.items()}
    for name, obj in objects.items():
        rig.attach(hair_rig if name == "Hair" else armature, obj)
    objects["Body"]["regions"] = ",".join(skin.REGIONS)
    anim.bake(armature, objects["Face"])
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
    export("player", [armature, objects["Face"], objects["Body"], objects["Eyes"]], animations=True)
    export("hair_flowing", [hair_rig, objects["Hair"]])
    export("outfit_romper", [armature, objects["Outfit"]])


main()
