"""The face rig: expression shapes sculpted on the cage, named after ARKit's blend shapes so
face capture and other tools map onto them. Shapes are built for the left side and mirrored.
"""
import numpy as np
from mathutils import Matrix, Vector, kdtree

from cage import MIRROR, ball, smoothstep

JAW_ANGLE = np.radians(10.0)
# Sideways from the left eye and up from it, in head-scale units.
BROW_INNER, BROW_MIDDLE, BROW_OUTER = (-0.02, 0.036), (0.004, 0.036), (0.028, 0.036)
UPPER_LID_FOLLOW = (1.0, 0.94, 0.78, 0.55, 0.32, 0.15, 0.05)
LOWER_LID_FOLLOW = (1.0, 0.7, 0.36, 0.12)
INSIDE_FOLLOW = (1.0, 0.85, 0.5, 0.15)


def follow(table, hops):
    table = np.append(table, 0.0)
    return table[np.minimum(hops, len(table) - 1)]


class Face:
    def __init__(self, cage, eye, scale):
        self.cage = cage
        self.co = cage.co[:cage.count].copy()
        self.eye = eye
        self.scale = scale
        self.left = self.co[:, 0] > 1e-5
        self.skin = cage.in_sets("skull", "jaw", "nose", "orbit", "eyelid")[:cage.count] > 0
        tree = kdtree.KDTree(cage.count)
        for index, point in enumerate(self.co):
            tree.insert(point, index)
        tree.balance()
        self.pair = np.array([tree.find(point * MIRROR)[1] for point in self.co])
        slit = cage.border(["skull", "jaw"], ["upper_mouth", "lower_mouth"])
        self.corner = self.co[slit[np.argmax(self.co[slit, 0])]]
        self.mouth = self.co[slit].mean(axis=0) * (0.0, 1.0, 1.0)
        self._lids()

    def mirror(self, delta):
        return delta[self.pair] * MIRROR

    def on_face(self, x, height):
        """The point of the face's front at a sideways position and a height above the eyes,
        both in head-scale units from the left eye."""
        x, z = self.eye[0] + x * self.scale, self.eye[2] + height * self.scale
        front = self.skin & (self.co[:, 1] < self.eye[1] + 0.03)
        candidates = np.flatnonzero(front)
        offsets = self.co[candidates][:, [0, 2]] - (x, z)
        return self.co[candidates[np.argmin((offsets ** 2).sum(axis=1))]]

    def pull(self, center, radius, offset):
        """A one-sided grab on the face."""
        weight = ball(self.co, np.asarray(center), radius * self.scale)
        return weight[:, None] * np.asarray(offset) * self.scale

    def _hops(self, sources, allowed):
        """Edge counts from the sources through allowed vertices, and each vertex's source."""
        hops = np.full(self.cage.count, 99)
        root = np.full(self.cage.count, -1)
        hops[sources], root[sources] = 0, sources
        neighbors = [[] for _ in range(self.cage.count)]
        for a, b in self.cage.edges:
            if a < self.cage.count and b < self.cage.count and a != b:
                neighbors[a].append(b)
                neighbors[b].append(a)
        frontier = list(sources)
        while frontier:
            following = []
            for v in frontier:
                for other in neighbors[v]:
                    if allowed[other] and hops[other] == 99:
                        hops[other], root[other] = hops[v] + 1, root[v]
                        following.append(other)
            frontier = following
        return hops, root

    def _lids(self):
        cage, co = self.cage, self.co
        margin = cage.border(["eyelid"], ["socket"])
        margin = margin[co[margin, 0] > 0.0]
        inner, outer = margin[np.argmin(co[margin, 0])], margin[np.argmax(co[margin, 0])]
        span = co[outer] - co[inner]
        across = (co[margin, 0] - co[inner, 0]) / span[0]
        chord = co[inner, 2] + across * span[2]
        upper = co[margin, 2] > chord + 1e-6
        lower = ~upper

        def line(which):
            order = np.argsort(across[which])
            return across[which][order], co[margin[which]][order]

        upper_at, upper_points = line(upper | (margin == inner) | (margin == outer))
        lower_at, lower_points = line(lower)

        def along(at, points, where):
            return np.stack([np.interp(where, at, points[:, axis]) for axis in range(3)], axis=1)

        self.margin = margin
        self.margin_upper = upper
        self.upper_line = along(upper_at, upper_points, across)
        self.lower_line = along(lower_at, lower_points, across)
        outside = cage.in_sets("eyelid", "orbit", "skull", "nose")[:cage.count] > 0
        inside = cage.in_sets("socket")[:cage.count] > 0
        self.out_hops, self.out_root = self._hops(margin, outside & self.left)
        self.in_hops, self.in_root = self._hops(margin, inside & self.left)

    def lids(self, upper_close, lower_close):
        """Moves the left eye's lids toward each other: 1 brings a lid's edge to the other
        lid's resting edge; negative values open the eye wider."""
        index = {v: i for i, v in enumerate(self.margin)}
        gap = self.lower_line - self.upper_line
        move = np.where(self.margin_upper[:, None], gap * upper_close, -gap * lower_close)
        corner = smoothstep(np.minimum(self._across(), 1.0 - self._across()) / 0.12)
        move = move * corner[:, None] + (0.0, -0.0003 * abs(upper_close), 0.0)
        delta = np.zeros_like(self.co)
        for hops, root, tables in ((self.out_hops, self.out_root, (UPPER_LID_FOLLOW, LOWER_LID_FOLLOW)),
                                   (self.in_hops, self.in_root, (INSIDE_FOLLOW, INSIDE_FOLLOW))):
            reached = np.flatnonzero(root >= 0)
            rows = np.array([index[r] for r in root[reached]])
            is_upper = self.margin_upper[rows]
            weight = np.where(is_upper, follow(tables[0], hops[reached]),
                              follow(tables[1], hops[reached]))
            delta[reached] = move[rows] * weight[:, None]
        radius = np.linalg.norm(self.co - self.eye, axis=1)
        moved = self.co + delta - self.eye
        fitted = self.eye + moved * (radius / np.linalg.norm(moved, axis=1))[:, None]
        near = np.linalg.norm(delta, axis=1) > 0.0
        return np.where(near[:, None], fitted - self.co, 0.0)

    def _across(self):
        x = self.co[self.margin, 0]
        return (x - x.min()) / (x.max() - x.min())

    def jaw_weight(self):
        """How much of the jaw's swing each vertex takes. Between the corners of the mouth the
        lower lip takes all of it and the upper lip none, so the lips part; beside the mouth
        the share grows with depth below the lips over a band that widens toward the cheeks.
        Nothing moves behind the hinge or on the neck."""
        cage, co, s = self.cage, self.co, self.scale
        count = cage.count
        head = cage.in_sets("skull", "jaw", "nose", "upper_mouth", "lower_mouth", "throat",
                            blur=4)[:count]
        lower = (cage.in_sets("jaw", "lower_mouth")[:count]
                 * (1.0 - 0.5 * cage.in_sets("skull", "upper_mouth")[:count]))
        aside = np.abs(co[:, 0])
        lips = 1.0 - smoothstep((aside / self.corner[0] - 0.6) / 0.8)
        lips *= 1.0 - cage.in_sets("throat")[:count]
        below = (self.mouth[2] + 0.0025 * s + 0.3 * aside - co[:, 2]) / (0.009 * s + 0.6 * aside)
        hinge = self.jaw_hinge()
        forward = (hinge[1] - co[:, 1]) / (hinge[1] - self.mouth[1])
        share = lips * lower + (1.0 - lips) * smoothstep(below)
        return head * share * smoothstep(forward / 0.7)

    def jaw_hinge(self):
        return self.eye * (0.0, 1.0, 1.0) + np.array([0.0, 0.07, -0.028]) * self.scale

    def jaw(self, points, weight, amount=1.0):
        """Offsets that swing points about the jaw's hinge by amount of the full opening."""
        swing = np.array(Matrix.Rotation(JAW_ANGLE * amount, 3, "X"))
        hinge = self.jaw_hinge()
        return weight[:, None] * ((points - hinge) @ swing.T + hinge - points)


def shapes(cage, eye, scale):
    """name -> per-vertex offsets of the cage. Also returns the Face, for parts that are not skin."""
    face = Face(cage, eye, scale)
    corner, mouth = face.corner, face.mouth
    cheek = face.on_face(0.012, -0.045)
    brow_inner, brow_mid, brow_outer = (face.on_face(*at) for at in (BROW_INNER, BROW_MIDDLE, BROW_OUTER))
    s = scale

    left = {
        "eyeBlink": face.lids(0.86, 0.14),
        "eyeWide": face.lids(-0.16, -0.06),
        "eyeSquint": face.lids(0.14, 0.42) + face.pull(cheek, 0.03, (0.0, -0.001, 0.003)),
        "browDown": face.pull(brow_mid, 0.03, (-0.0015, 0.0, -0.0045))
        + face.pull(brow_inner, 0.02, (-0.002, 0.0, -0.003)),
        "browOuterUp": face.pull(brow_outer, 0.026, (0.0, 0.0, 0.006)),
        "mouthSmile": face.pull(corner, 0.024, (0.0065, 0.004, 0.0065))
        + face.pull(cheek, 0.032, (0.001, -0.0015, 0.004)),
        "mouthFrown": face.pull(corner, 0.022, (0.002, 0.002, -0.0055)),
    }
    result = {}
    for name, delta in left.items():
        result[f"{name}Left"] = delta
        result[f"{name}Right"] = face.mirror(delta)
    inner_up = face.pull(brow_inner, 0.022, (0.001, 0.0, 0.0065))
    result["browInnerUp"] = inner_up + face.mirror(inner_up)
    around = ball(face.co, mouth + (0.0, -0.005, 0.0), 0.034 * s)
    result["mouthPucker"] = around[:, None] * np.stack(
        [-0.45 * face.co[:, 0], np.full(cage.count, -0.004 * s), np.zeros(cage.count)], axis=1)
    result["jawOpen"] = face.jaw(face.co, face.jaw_weight())
    return result, face
