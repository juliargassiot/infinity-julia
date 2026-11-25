"""Turns the sculpted cage into the two skin meshes: a subdivided Head that carries the
expressions, and the Body. Both share the vertices and normals along the base of the neck.

Vertex colors mask what the skin shader tints: R lips, G blush, B thin skin that light shines
through, A 1 on open skin and 0 inside the mouth and eye sockets.
"""
import bpy
import numpy as np

from cage import FINGERS, FOOT, HAND, HEAD, MIRROR, MOUTH, ball, smoothstep
from parts import Part
from rig import limited
from subdivide import Subdivision

# The parts of her surface the game can hide under clothing, by number. Faces nothing hides are
# Always; WingOpening is for the patch of a garment's back that opens around wings.
LIMB_REGIONS = ("Shoulder", "Bicep", "Elbow", "Forearm", "Wrist", "Hand",
                "Thigh", "Knee", "Calf", "Ankle", "Foot")
REGIONS = ["Always", "Chest", "Waist", "Hips", "WingOpening",
           *(side + name for side in ("Left", "Right") for name in LIMB_REGIONS)]
# face set: the joints it runs between, its region before and after halfway
HALVES = {"upper_arm": ("LeftUpperArm", "LeftLowerArm", "Bicep", "Elbow"),
          "forearm": ("LeftLowerArm", "LeftHand", "Forearm", "Wrist"),
          "thigh": ("LeftUpperLeg", "LeftLowerLeg", "Thigh", "Knee"),
          "shin": ("LeftLowerLeg", "LeftFoot", "Calf", "Ankle")}
UPPER_LIP = 0.0075
LOWER_LIP = 0.0095
# UV tiles of the base mesh, packed into one square for the body: tile -> (scale, u, v).
BODY_ATLAS = {1: (2 / 3, 0.0, 1 / 3), 2: (1 / 3, 2 / 3, 2 / 3), 4: (1 / 3, 2 / 3, 1 / 3)}


def paint(cage, joints, head_scale):
    co = cage.co[:cage.count]

    def member(*names, blur=0):
        return cage.in_sets(*names, blur=blur)[:cage.count]

    def both(point, radius):
        point = np.asarray(point)
        return ball(co, point, radius) + ball(co, point * MIRROR, radius)

    outer = cage.in_sets("skull", "jaw") > 0
    slit = cage.border(["skull", "jaw"], ["upper_mouth", "lower_mouth"])
    reach = cage.geodesic(slit, outer)[:cage.count]
    corner = np.abs(co[slit, 0]).max()
    across = np.sqrt(np.clip(1.0 - (co[:, 0] / corner) ** 2, 0.0, 1.0))
    upper = co[:, 2] > co[slit, 2].mean()
    bow = 1.0 - 0.22 * np.exp(-(co[:, 0] / (0.1 * corner)) ** 2)
    thickness = np.where(upper, UPPER_LIP * bow, LOWER_LIP) * head_scale * (0.12 + 0.88 * across)
    lips = smoothstep((1.0 - reach / thickness) / 0.45)

    eye = joints["LeftEye"]
    cheek = eye + np.array([0.012, -0.03, -0.047]) * head_scale
    blush = 0.9 * both(cheek, 0.034 * head_scale)
    blush += 0.35 * member("nose", blur=2) * ball(co, eye * (0, 1, 1) + (0, -0.07, -0.04), 0.03)
    blush += 0.6 * both(joints["LeftLowerLeg"] + (0.0, -0.05, 0.0), 0.06)
    blush += 0.6 * both(joints["LeftLowerArm"] + (0.0, 0.035, 0.0), 0.045)
    blush += 0.45 * both(joints["LeftUpperArm"] + (0.02, 0.0, 0.03), 0.06)
    blush += 0.5 * member(*(f"{finger}_3" for finger in FINGERS), blur=1)
    blush += 0.4 * member("toes", "heel", blur=1) * smoothstep((0.03 - co[:, 2]) / 0.03)

    thin = np.full(len(co), 0.12)
    thin = np.maximum(thin, member("ear", blur=1))
    thin = np.maximum(thin, 0.55 * member("nose", blur=1))
    thin = np.maximum(thin, 0.5 * member(*HAND, blur=1))
    thin = np.maximum(thin, 0.4 * member(*FOOT, blur=1))

    open_skin = 1.0 - member(*MOUTH, "socket")
    return np.stack([lips, np.clip(blush, 0.0, 1.0), thin, open_skin], axis=1)


def regions(cage, joints):
    """The number in REGIONS of each face of the cage."""
    centers = cage.co[cage.loop_verts.reshape(-1, 4)].mean(axis=1)
    right = centers[:, 0] < 0.0
    centers = centers * np.where(right, -1.0, 1.0)[:, None] * (1.0, 0.0, 0.0) + centers * (0.0, 1.0, 1.0)
    result = np.zeros(len(centers), dtype=int)

    def put(chosen, name):
        if name in LIMB_REGIONS:
            result[chosen] = REGIONS.index("Left" + name) + len(LIMB_REGIONS) * right[chosen]
        else:
            result[chosen] = REGIONS.index(name)

    torso = cage.faces_in("torso")
    put(torso & (centers[:, 2] > joints["Chest"][2]), "Chest")
    put(torso & (centers[:, 2] <= joints["Chest"][2]), "Waist")
    put(cage.faces_in("pelvis"), "Hips")
    put(cage.faces_in("shoulder"), "Shoulder")
    put(cage.faces_in(*HAND), "Hand")
    put(cage.faces_in(*FOOT), "Foot")
    for name, (start, end, before, after) in HALVES.items():
        limb = joints[end] - joints[start]
        far = (centers - joints[start]) @ limb > 0.5 * limb @ limb
        put(cage.faces_in(name) & ~far, before)
        put(cage.faces_in(name) & far, after)
    return result


def face_softness(cage, eye):
    """Most on the front of the face, fading out toward the ears and the neck."""
    face = cage.in_sets("skull", "nose", "jaw", "orbit", "eyelid", blur=2)
    front = smoothstep((eye[1] + 0.07 - cage.co[:, 1]) / 0.06)
    low = smoothstep((cage.co[:, 2] - (eye[2] - 0.12)) / 0.03)
    return 0.7 * face * front * low


def corner_uvs(cage, fine):
    uvs = np.empty(len(cage.mesh.loops) * 2)
    cage.mesh.uv_layers[0].data.foreach_get("uv", uvs)
    uvs = uvs.reshape(-1, 4, 2)
    tiles = np.floor(uvs[:, :, 0].mean(axis=1)).astype(int)
    uvs[:, :, 0] -= tiles[:, None]
    for tile, (scale, u, v) in BODY_ATLAS.items():
        packed = (tiles == tile) & ~fine
        uvs[packed] = uvs[packed] * scale + (u, v)
    return uvs


def smooth_normals(points, polygons):
    mesh = bpy.data.meshes.new("normals")
    mesh.from_pydata(points, [], [list(map(int, polygon)) for polygon in polygons])
    normals = np.empty(len(points) * 3)
    mesh.vertices.foreach_get("normal", normals)
    bpy.data.meshes.remove(mesh)
    return normals.reshape(-1, 3)


class Skin:
    """The head and body parts, and the whole surface they were cut from."""

    def __init__(self, cage, colors, shapes, softness, regions):
        """shapes: name -> per-vertex offsets of the cage. regions: per cage face, its number
        in REGIONS; the body keeps them. softness: per cage vertex, how far
        the shading normals lean toward those of a smoothed-out copy of the surface, which
        gives the face its soft, even light."""
        faces = cage.loop_verts.reshape(-1, 4)
        fine = cage.faces_in(*HEAD, "neck")
        self.subdivision = Subdivision(faces, fine)
        self.points = self.subdivision.points(cage.co[:cage.count])
        polygons, uvs, sources = self.subdivision.polygons(corner_uvs(cage, fine))
        self.polygons = [np.array(polygon) for polygon in polygons]
        normals = smooth_normals(self.points, self.polygons)
        sharp = cage.co.copy()
        cage.relax((softness > 0.0).astype(float), iterations=30)
        smoothed = smooth_normals(self.subdivision.points(cage.co[:cage.count]), self.polygons)
        cage.co = sharp
        lean = self.subdivision.points(softness[:cage.count])[:, None]
        normals = normals * (1.0 - lean) + smoothed * lean
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        colors = self.subdivision.points(colors)
        shapes = {name: self.subdivision.points(delta) for name, delta in shapes.items()}

        def part(chosen, shapes, regions=None):
            picked = np.flatnonzero(chosen[sources])
            used = np.unique(np.concatenate([self.polygons[i] for i in picked]))
            index = np.full(len(self.points), -1)
            index[used] = np.arange(len(used))
            return used, Part(
                "skin", self.points[used], [index[self.polygons[i]].tolist() for i in picked],
                [uvs[i] for i in picked], colors[used], normals[used],
                {name: delta[used] for name, delta in shapes.items()},
                cage.face_sets[sources[picked]],
                regions=None if regions is None else regions[sources[picked]])

        self.head_verts, self.head = part(fine, shapes)
        self.body_verts, self.body = part(~fine, {}, regions)

    def bind(self, weights, head_hold):
        """Gives both parts their bone weights. weights: bone -> weight per cage vertex;
        head_hold: per cage vertex, how firmly the Head bone alone holds it."""
        weights = {name: weight * (1.0 - head_hold) for name, weight in weights.items()}
        weights["Head"] = weights.get("Head", 0.0) + head_hold
        weights = limited({name: self.subdivision.points(w) for name, w in weights.items()})
        self.head.groups = {name: weight[self.head_verts] for name, weight in weights.items()}
        self.body.groups = {name: weight[self.body_verts] for name, weight in weights.items()}
