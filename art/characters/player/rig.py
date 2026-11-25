"""The skeletons and skin weights.

Body bones carry the names of Godot's humanoid profile, so motion made for that profile maps
onto her without a table. Bones named <Name>Socket deform nothing: they mark where pieces
attach. A hairstyle has a skeleton of its own, so the game can swap it: its Head bone stands
where the body's does and the chains hang off it.
"""
import bpy
import numpy as np
from mathutils import Vector

from cage import FINGERS
from parts import MIRROR, other_side

MAX_INFLUENCES = 4
SOCKET_LENGTH = 0.03
FORWARD = Vector((0.0, -1.0, 0.0))
UP = Vector((0.0, 0.0, 1.0))

# bone: (parent, joint at its tail)
SPINE = {
    "Hips": (None, "Spine"), "Spine": ("Hips", "Chest"), "Chest": ("Spine", "UpperChest"),
    "UpperChest": ("Chest", "Neck"), "Neck": ("UpperChest", "Head"), "Head": ("Neck", "HeadTop"),
}
LEFT = {
    "LeftShoulder": ("UpperChest", "LeftUpperArm"), "LeftUpperArm": ("LeftShoulder", "LeftLowerArm"),
    "LeftLowerArm": ("LeftUpperArm", "LeftHand"), "LeftHand": ("LeftLowerArm", "LeftMiddleProximal"),
    "LeftUpperLeg": ("Hips", "LeftLowerLeg"), "LeftLowerLeg": ("LeftUpperLeg", "LeftFoot"),
    "LeftFoot": ("LeftLowerLeg", "LeftToes"), "LeftToes": ("LeftFoot", "LeftToesTip"),
}
for finger in FINGERS:
    segments = ("Metacarpal", "Proximal", "Distal", "Tip") if finger == "thumb" else \
        ("Proximal", "Intermediate", "Distal", "Tip")
    names = [f"Left{finger.capitalize()}{segment}" for segment in segments]
    for parent, name, tail in zip(["LeftHand"] + names, names, names[1:]):
        LEFT[name] = (parent, tail)


BODY_BONES = [*SPINE, *LEFT, *(other_side(name) for name in LEFT)]


def both_sides(left, twin):
    """Adds the right twins of the entries named Left...: twin gives a value's right twin."""
    result = dict(left)
    for name, values in left.items():
        if name.startswith("Left"):
            result[other_side(name)] = tuple(twin(value) for value in values)
    return result


def armature(name, bones):
    """Creates an armature. bones: name -> (parent, head, tail, the axis its roll aligns to)."""
    rig = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    edit = rig.data.edit_bones
    for bone_name, (parent, head, tail, roll) in bones.items():
        bone = edit.new(bone_name)
        bone.head, bone.tail = Vector(head), Vector(tail)
        bone.parent = edit.get(parent) if parent else None
        bone.use_connect = bool(parent) and (bone.parent.tail - bone.head).length < 1e-5
        bone.align_roll(roll)
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def body(joints, sockets):
    """The body's armature. sockets: name -> (parent bone, point, direction)."""
    joints = dict(joints)
    joints.update({other_side(name): point * MIRROR for name, point in joints.items()
                   if name.startswith("Left")})
    bones = {}
    for name, (parent, tail) in {**SPINE, **both_sides(LEFT, other_side)}.items():
        bones[name] = (parent, joints[name], joints[tail],
                       UP if "Foot" in name or "Toes" in name else FORWARD)
    for side in ("Left", "Right"):
        eye = joints[f"{side}Eye"]
        bones[f"{side}Eye"] = ("Head", eye, eye + (0.0, -0.03, 0.0), UP)
    mirror = lambda value: other_side(value) if isinstance(value, str) else value * MIRROR
    for name, (parent, point, direction) in both_sides(sockets, mirror).items():
        reach = direction / np.linalg.norm(direction) * SOCKET_LENGTH
        bones[f"{name}Socket"] = (parent, point, point + reach,
                                  UP if abs(reach[2]) < 0.7 * SOCKET_LENGTH else FORWARD)
    rig = armature("Rig", bones)
    for bone in rig.data.bones:
        bone.use_deform = not bone.name.endswith("Socket")
    return rig


def hair(joints, chains):
    """A hairstyle's armature. chains: chain name -> joints from root to tip."""
    bones = {"Head": (None, joints["Head"], joints["HeadTop"], FORWARD)}
    for chain, points in chains.items():
        parent = "Head"
        for i, (head, tail) in enumerate(zip(points, points[1:])):
            bones[f"{chain}_{i + 1}"] = (parent, head, tail, FORWARD)
            parent = f"{chain}_{i + 1}"
    return armature("HairRig", bones)


def heat_weights(rig, points, polygons, bones):
    """Blender's automatic weights of a surface for the named bones: name -> per-vertex weight."""
    mesh = bpy.data.meshes.new("Weights")
    mesh.from_pydata(points, [], [list(map(int, polygon)) for polygon in polygons])
    surface = bpy.data.objects.new("Weights", mesh)
    bpy.context.scene.collection.objects.link(surface)
    deforming = {bone.name: bone.use_deform for bone in rig.data.bones}
    for bone in rig.data.bones:
        bone.use_deform = bone.name in bones
    bpy.context.view_layer.update()
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj in (surface, rig))
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for bone in rig.data.bones:
        bone.use_deform = deforming[bone.name]

    weights = {group.name: np.zeros(len(points)) for group in surface.vertex_groups}
    names = [group.name for group in surface.vertex_groups]
    for vertex in mesh.vertices:
        for element in vertex.groups:
            weights[names[element.group]][vertex.index] = element.weight
    bpy.data.objects.remove(surface)
    bpy.data.meshes.remove(mesh)
    return weights


def limited(weights):
    """Keeps each vertex's strongest influences and makes them sum to one."""
    names = list(weights)
    table = np.stack([weights[name] for name in names], axis=1)
    weakest = np.argsort(table, axis=1)[:, :-MAX_INFLUENCES]
    np.put_along_axis(table, weakest, 0.0, axis=1)
    table /= table.sum(axis=1, keepdims=True)
    return {name: table[:, i] for i, name in enumerate(names) if table[:, i].any()}


def attach(rig, obj):
    obj.parent = rig
    obj.modifiers.new("Rig", "ARMATURE").object = rig
