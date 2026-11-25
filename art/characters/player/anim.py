"""Hand-keyed animations, written as functions of time and baked at 30 keys a second.

Each animation becomes an action on its own NLA track of the rig and of the head's shape keys;
the export turns every track name into one animation. Hair bones are left to the game's spring
simulation.
"""
import bpy
import numpy as np
from mathutils import Vector

from figure import Figure, mirrored, turn
from parts import other_side
from rig import BODY_BONES

FPS = 30
EYES = ("LeftEye", "RightEye")
CURL = ("Proximal", "Intermediate", "Distal")
FINGER_NAMES = ("Index", "Middle", "Ring", "Little")


def wave(t, period, shift=0.0):
    return np.sin(2.0 * np.pi * (t / period + shift))


def bump(t, at, length):
    """Rises smoothly from 0 to 1 and back, centred on a moment."""
    x = np.clip(1.0 - abs(t - at) / (length / 2.0), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def both(turns, name, rotation):
    """Gives a left bone a turn and its right twin the mirrored turn."""
    turns[name] = rotation
    turns[other_side(name)] = mirrored(rotation)


def hands(turns, curl, spread=0.0):
    """Curls the fingers of both hands: curl is degrees per joint, a little more toward the
    little finger."""
    for i, finger in enumerate(FINGER_NAMES):
        for joint in CURL:
            both(turns, f"Left{finger}{joint}", turn(y=curl * (0.8 + 0.13 * i), x=spread * (i - 1.5)))
    both(turns, "LeftThumbProximal", turn(x=-curl * 0.5, y=curl * 0.3))
    both(turns, "LeftThumbDistal", turn(x=-curl * 0.6))


def idle(figure):
    """Standing at ease: breathing, a slow sway of the weight, small looks around and blinks."""
    ankles = {side: figure.heads[f"{side}Foot"].copy() for side in ("Left", "Right")}

    def pose(t):
        breath = wave(t, 4.0)
        sway = wave(t, 8.0)
        drift = wave(t, 8.0, 0.2)
        turns = {
            "Hips": turn(y=1.4 * sway, z=0.8 * drift),
            "Spine": turn(x=-0.8 - 0.5 * breath, y=-1.0 * sway, z=-0.4 * drift),
            "Chest": turn(x=-0.7 * breath, y=-0.9 * sway, z=-0.4 * drift),
            "UpperChest": turn(x=-0.6 * breath),
            "Neck": turn(x=1.0 + 0.8 * breath, y=0.3 * sway),
            "Head": turn(x=1.0 * breath + 1.2 * wave(t, 8.0, 0.35), y=1.2 * wave(t, 8.0, 0.6),
                         z=3.0 * wave(t, 8.0, 0.1)),
        }
        both(turns, "LeftShoulder", turn(y=-1.3 * breath - 1.0))
        turns["LeftUpperArm"] = turn(y=20.0 + 1.0 * breath + 0.8 * sway, x=-3.0 + 1.0 * drift)
        turns["RightUpperArm"] = mirrored(turn(y=20.0 + 1.0 * breath - 0.8 * sway,
                                               x=-3.0 - 1.0 * drift))
        turns["LeftLowerArm"] = turn(x=-12.0 - 1.5 * wave(t, 8.0, 0.3), y=8.0)
        turns["RightLowerArm"] = mirrored(turn(x=-12.0 - 1.5 * wave(t, 8.0, 0.8), y=8.0))
        hands(turns, 9.0 + 1.5 * wave(t, 8.0, 0.4))

        hips = Vector((0.012 * sway, 0.003 * drift, -0.008 + 0.0015 * wave(t, 4.0, 0.25)))
        for side, ankle in ankles.items():
            figure.leg(side, turns, hips, ankle, knee_out=6.0)

        look = bump(t, 3.2, 1.8) - bump(t, 6.6, 1.4)
        for eye in EYES:
            turns[eye] = turn(z=3.5 * look, x=-1.0 * bump(t, 6.6, 1.4))
        blink = max(bump(t, 1.5, 0.24), bump(t, 4.9, 0.24), bump(t, 5.25, 0.22))
        faces = {"eyeBlinkLeft": blink, "eyeBlinkRight": blink,
                 "mouthSmileLeft": 0.18 + 0.06 * breath, "mouthSmileRight": 0.18 + 0.06 * breath}
        return turns, hips, faces

    return 8.0, pose


STEP_CYCLE = 0.66


def steps(figure, speed, on_ground, lift, drop, bounce, lean, swing, elbow):
    """Two steps on the spot at a ground speed in m/s, the left foot landing at the start.
    Walk and run share STEP_CYCLE, so the game can blend them by speed. on_ground is the part
    of the cycle each foot spends on the ground."""
    ankles = {side: figure.heads[f"{side}Foot"].copy() for side in ("Left", "Right")}
    reach = speed * STEP_CYCLE * on_ground / 2.0

    def foot(phase):
        """Where a foot is, from its landing: offset forward, height, toes' pitch downward."""
        phase %= 1.0
        if phase < on_ground:
            along = phase / on_ground
            return reach * (1.0 - 2.0 * along), 0.0, 22.0 * bump(along, 1.0, 0.5) - 12.0 * bump(along, 0.0, 0.4)
        along = (phase - on_ground) / (1.0 - on_ground)
        eased = along * along * (3.0 - 2.0 * along)
        return (reach * (2.0 * eased - 1.0), lift * np.sin(np.pi * along) ** 0.8,
                40.0 * (1.0 - along) ** 2 - 12.0 * along)

    def pose(t):
        cycle = t / STEP_CYCLE
        stride = np.cos(2.0 * np.pi * cycle)
        turns = {
            "Hips": turn(x=lean * 0.4, z=-5.0 * stride, y=2.0 * np.sin(2.0 * np.pi * cycle)),
            "Spine": turn(x=lean * 0.3, z=4.0 * stride),
            "Chest": turn(x=lean * 0.3, z=5.0 * stride),
            "Neck": turn(x=-lean * 0.4, z=-2.0 * stride),
            "Head": turn(x=-lean * 0.5, z=-2.0 * stride),
        }
        turns["LeftUpperArm"] = turn(y=30.0, x=swing * stride)
        turns["RightUpperArm"] = mirrored(turn(y=30.0, x=-swing * stride))
        turns["LeftLowerArm"] = turn(x=-elbow + 0.3 * swing * stride, y=6.0)
        turns["RightLowerArm"] = mirrored(turn(x=-elbow - 0.3 * swing * stride, y=6.0))
        hands(turns, 22.0)
        hips = Vector((0.0, -0.02 * lean / 10.0,
                       -drop - bounce * np.cos(4.0 * np.pi * (cycle - 0.08))))
        for side, shift in (("Left", 0.0), ("Right", 0.5)):
            forward, height, pitch = foot(cycle + shift)
            ankle = ankles[side] + Vector((0.0, -forward, height + 0.0007 * max(pitch, 0.0)))
            figure.leg(side, turns, hips, ankle, toe_pitch=pitch, knee_out=3.0)
        return turns, hips, {"mouthSmileLeft": 0.15, "mouthSmileRight": 0.15}

    return STEP_CYCLE, pose


def walk(figure):
    """A light, quick walk at the game's walking speed."""
    return steps(figure, 3.0, on_ground=0.42, lift=0.1, drop=0.035, bounce=0.014, lean=5.0,
                 swing=24.0, elbow=28.0)


def run(figure):
    return steps(figure, 6.5, on_ground=0.27, lift=0.26, drop=0.06, bounce=0.03, lean=14.0,
                 swing=42.0, elbow=75.0)


def airborne(spine, arms_out, arms_forward, elbow, thighs, knees, toes, flutter):
    """A held pose in the air that breathes a little. thighs, knees: degrees for the left and
    the right leg."""
    def make(figure):
        def pose(t):
            sway = wave(t, 1.0)
            turns = {
                "Hips": turn(x=spine * 0.5), "Spine": turn(x=spine * 0.25),
                "Chest": turn(x=spine * 0.25), "Neck": turn(x=-spine * 0.4),
                "Head": turn(x=-spine * 0.5),
            }
            both(turns, "LeftUpperArm", turn(y=-arms_out + flutter * sway, x=-arms_forward))
            both(turns, "LeftLowerArm", turn(x=-elbow, y=4.0 + flutter * sway))
            hands(turns, 12.0, spread=3.0)
            for side, thigh, knee, way in (("Left", thighs[0], knees[0], 1.0),
                                           ("Right", thighs[1], knees[1], -1.0)):
                turns[f"{side}UpperLeg"] = turn(x=-thigh + flutter * sway * way, y=3.0 * way)
                turns[f"{side}LowerLeg"] = turn(x=knee - flutter * sway * way)
                turns[f"{side}Foot"] = turn(x=toes)
            return turns, Vector(), {"mouthSmileLeft": 0.2, "mouthSmileRight": 0.2}

        return 1.0, pose

    return make


ANIMATIONS = {
    "idle": idle, "walk": walk, "run": run,
    "rise": airborne(spine=-4.0, arms_out=-8.0, arms_forward=10.0, elbow=30.0,
                     thighs=(38.0, 6.0), knees=(62.0, 24.0), toes=30.0, flutter=1.0),
    "fall": airborne(spine=5.0, arms_out=28.0, arms_forward=-6.0, elbow=22.0,
                     thighs=(16.0, 30.0), knees=(28.0, 46.0), toes=22.0, flutter=2.5),
    "glide": airborne(spine=16.0, arms_out=38.0, arms_forward=-8.0, elbow=10.0,
                      thighs=(-12.0, -4.0), knees=(14.0, 30.0), toes=40.0, flutter=1.5),
}


def bake(armature, head):
    """Creates every animation as an NLA track on the rig and on the head's shape keys."""
    figure = Figure(armature)
    shape_keys = head.data.shape_keys
    bones = [armature.pose.bones[name] for name in (*BODY_BONES, *EYES)]
    for name, make in ANIMATIONS.items():
        seconds, pose = make(figure)
        action = bpy.data.actions.new(name)
        for target in (armature, shape_keys):
            if target.animation_data is None:
                target.animation_data_create()
            target.animation_data.action = action
        previous = {}
        for frame in range(round(seconds * FPS) + 1):
            turns, hips, faces = pose(frame / FPS)
            figure.apply(turns, hips)
            for bone in bones:
                rotation = bone.rotation_quaternion
                if bone.name in previous and previous[bone.name].dot(rotation) < 0.0:
                    bone.rotation_quaternion = -rotation
                previous[bone.name] = bone.rotation_quaternion.copy()
                bone.keyframe_insert("rotation_quaternion", frame=frame)
            armature.pose.bones["Hips"].keyframe_insert("location", frame=frame)
            for block in shape_keys.key_blocks[1:]:
                block.value = faces.get(block.name, 0.0)
                block.keyframe_insert("value", frame=frame)
        for target in (armature, shape_keys):
            track = target.animation_data.nla_tracks.new()
            track.name = name
            track.strips.new(name, 0, action)
            track.mute = True
            target.animation_data.action = None
    figure.apply({})
    for block in shape_keys.key_blocks:
        block.value = 0.0
