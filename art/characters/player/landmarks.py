"""Joint positions and attachment points, read from the sculpted cage.

Everything is for the left side (+X) or the midline; the rig mirrors it.
"""
import numpy as np

from cage import FINGERS

UP, DOWN, BACK, FRONT = (np.array(axis, dtype=float) for axis in (
    (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)))


def joints(cage):
    co = cage.co[:cage.count]

    def left(verts):
        return verts[co[verts, 0] > 1e-5]

    def center(some, others, side=True):
        verts = cage.border(some, others)
        return co[left(verts) if side else verts].mean(axis=0)

    def midline(point):
        return point * (0.0, 1.0, 1.0)

    def tip(name, toward):
        verts = left(np.flatnonzero(cage.in_sets(name)[:cage.count] > 0))
        return co[verts[np.argmax(co[verts] @ toward)]]

    found = {}
    hip_crease = center(["pelvis"], ["thigh"])
    waist = midline(center(["pelvis"], ["torso"], side=False))
    neck_base = midline(center(["neck"], ["torso"], side=False))
    head_base = midline(center(["neck"], ["skull", "jaw"], side=False))
    back = co[np.flatnonzero(cage.in_sets("pelvis", "torso")[:cage.count] > 0), 1].max()

    def spine(t, depth):
        point = waist + (neck_base - waist) * t
        point[1] += (back - point[1]) * depth
        return point

    found["Hips"] = midline(hip_crease + (0.0, 0.0, 0.07)) + (0.0, 0.02, 0.0)
    found["Spine"] = spine(-0.05, 0.45)
    found["Chest"] = spine(0.3, 0.5)
    found["UpperChest"] = spine(0.62, 0.5)
    found["Neck"] = neck_base + (0.0, 0.012, 0.01)
    found["Head"] = head_base + (0.0, 0.012, -0.005)
    found["HeadTop"] = np.array([0.0, found["Head"][1], co[:, 2].max()])

    shoulder = center(["shoulder"], ["upper_arm"])
    found["LeftShoulder"] = neck_base + (shoulder - neck_base) * (0.25, 1.0, 0.0) + (0, 0, -0.035)
    found["LeftUpperArm"] = shoulder + (-0.008, 0.0, 0.004)
    found["LeftLowerArm"] = center(["upper_arm"], ["forearm"])
    found["LeftHand"] = center(["forearm"], ["palm"])
    for finger in FINGERS:
        chain = ["palm"] + [f"{finger}_{i}" for i in (1, 2, 3)]
        points = [center([a], [b]) for a, b in zip(chain, chain[1:])]
        points.append(tip(chain[-1], points[-1] - points[-2]))
        if finger == "thumb":
            names = ("Metacarpal", "Proximal", "Distal", "Tip")
            points[0] = points[0] + (found["LeftHand"] - points[0]) * 0.55
        else:
            names = ("Proximal", "Intermediate", "Distal", "Tip")
        for name, point in zip(names, points):
            found[f"Left{finger.capitalize()}{name}"] = point

    found["LeftUpperLeg"] = hip_crease + (0.004, 0.0, 0.035)
    found["LeftLowerLeg"] = center(["thigh"], ["shin"]) + (0.0, 0.006, 0.0)
    found["LeftFoot"] = center(["shin"], ["ankle"]) + (0.0, 0.008, -0.01)
    found["LeftToes"] = center(["heel"], ["ball"]) * (1.0, 1.0, 0.0) + (0.0, -0.015, 0.012)
    found["LeftToesTip"] = tip("toes", FRONT) * (0.0, 1.0, 0.0) + found["LeftToes"] * (1.0, 0.0, 1.0)
    found["LeftEye"] = cage.marked("eye")
    return found


def sockets(cage, joints, brow):
    """Where jewelry, accessories and body features attach: name -> (the bone that carries it,
    its point, the direction it points along). On limbs that is along the limb; on the head and
    trunk it is out of the skin, except where a piece hangs or floats."""
    co = cage.co[:cage.count]
    normals = cage.normals()[:cage.count]
    near_middle = np.abs(co[:, 0]) < 1e-4

    def spot(names, toward, where=True):
        """The point of the named face sets that lies farthest in a direction, and the skin's
        normal there."""
        verts = np.flatnonzero((cage.in_sets(*names)[:cage.count] > 0) & (co[:, 0] > -1e-5) & where)
        vert = verts[np.argmax(co[verts] @ np.asarray(toward, dtype=float))]
        return co[vert], normals[vert]

    def at_height(z):
        return near_middle & (np.abs(co[:, 2] - z) < 0.03)

    def along(start, end, t):
        return joints[start] + (joints[end] - joints[start]) * t, joints[end] - joints[start]

    top = joints["HeadTop"]
    found = {
        "Necklace": ("UpperChest", spot(("neck", "torso"), FRONT, at_height(joints["Neck"][2]))[0], FRONT),
        "Wings": ("UpperChest", spot(("torso",), BACK, at_height(joints["UpperChest"][2] + 0.03))[0], BACK),
        "Tail": ("Hips", spot(("pelvis", "torso"), BACK, at_height(joints["Hips"][2] - 0.03))[0],
                 BACK + DOWN * 0.4),
        "Halo": ("Head", top + UP * 0.12, UP),
        "Hat": ("Head", top, UP),
        "Septum": ("Head", spot(("nose",), DOWN, near_middle)[0], DOWN),
        "LeftBrow": ("Head", brow, FRONT),
        "LeftEarring": ("Head", spot(("ear",), DOWN)[0], DOWN),
        "LeftBracelet": ("LeftLowerArm", *along("LeftLowerArm", "LeftHand", 0.9)),
        "LeftArmCuff": ("LeftUpperArm", *along("LeftUpperArm", "LeftLowerArm", 0.45)),
    }
    for name, sets, toward in (("LeftNostril", ("nose",), (1.0, 0.0, -0.2)),
                               ("LeftHorn", ("skull",), (0.4, -0.45, 0.8)),
                               ("LeftAnimalEar", ("skull",), (0.55, 0.15, 0.82)),
                               ("LeftHairClip", ("skull",), (0.8, -0.35, 0.45))):
        found[name] = ("Head", *spot(sets, toward))
    return found
