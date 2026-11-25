"""The sculpting cage: the low-resolution body whose vertices every sculpt step moves.

All operations are mirrored across x = 0, so the character stays symmetric. The character
faces -Y; her left side is +X.
"""
import bpy
import numpy as np

MIRROR = np.array([-1.0, 1.0, 1.0])

BASE_BLEND = "third_party/blender_human_base_meshes/stylized_female_body.blend"
BASE_OBJECT = "GEO-body_female_stylized"
FACE_SETS = {
    "neck": (6,), "skull": (44,), "nose": (45,), "jaw": (46,), "upper_mouth": (47,),
    "lower_mouth": (48,), "throat": (49,), "orbit": (27,), "eyelid": (28,), "socket": (37,),
    "ear": (29,), "thigh": (256,), "shin": (257,), "pelvis": (258,), "torso": (259,),
    "shoulder": (260,), "forearm": (262,), "upper_arm": (263,), "palm": (273,),
    "thumb_1": (359,), "thumb_2": (285,), "thumb_3": (284,),
    "index_1": (278,), "index_2": (283,), "index_3": (282,),
    "middle_1": (277,), "middle_2": (279,), "middle_3": (272,),
    "ring_1": (280,), "ring_2": (274,), "ring_3": (275,),
    "little_1": (281,), "little_2": (286,), "little_3": (276,),
    "ankle": (288,), "heel": (316,), "ball": (317,), "toes": (318, 319, 320, 321, 322),
}
FINGERS = ("thumb", "index", "middle", "ring", "little")
HAND = ("palm",) + tuple(f"{finger}_{i}" for finger in FINGERS for i in (1, 2, 3))
FOOT = ("ankle", "heel", "ball", "toes")
MOUTH = ("upper_mouth", "lower_mouth", "throat")
HEAD = ("skull", "nose", "jaw", "orbit", "eyelid", "socket", "ear") + MOUTH


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class Cage:
    def __init__(self, mesh):
        self.mesh = mesh
        count = len(mesh.vertices)
        self.co = np.empty(count * 3)
        mesh.vertices.foreach_get("co", self.co)
        self.co = self.co.reshape(-1, 3)
        self.edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
        mesh.edges.foreach_get("vertices", self.edges)
        self.edges = self.edges.reshape(-1, 2)
        self.valence = np.bincount(self.edges.ravel(), minlength=count).astype(float)
        self.face_sets = np.empty(len(mesh.polygons), dtype=np.int32)
        mesh.attributes[".sculpt_face_set"].data.foreach_get("value", self.face_sets)
        self.loop_verts = np.empty(len(mesh.loops), dtype=np.int64)
        mesh.loops.foreach_get("vertex_index", self.loop_verts)
        self.loop_faces = np.repeat(np.arange(len(mesh.polygons)),
                                    [p.loop_total for p in mesh.polygons])
        self.count = count
        self.marks = {}
        self.mark_sets = []

    def mark(self, name, point, face_set):
        """Tracks a point that is not a vertex through the sculpt, as part of a face set."""
        self.marks[name] = len(self.co)
        self.mark_sets.append(face_set)
        self.co = np.vstack([self.co, point])
        self.edges = np.vstack([self.edges, [self.marks[name]] * 2])
        self.valence = np.append(self.valence, 2.0)

    def marked(self, name):
        return self.co[self.marks[name]].copy()

    def write(self):
        self.mesh.vertices.foreach_set("co", self.co[:self.count].ravel())
        self.mesh.update()

    def normals(self):
        self.write()
        normals = np.zeros(len(self.co) * 3)
        self.mesh.vertices.foreach_get("normal", normals[:self.count * 3])
        return normals.reshape(-1, 3)

    def neighbor_mean(self, values):
        total = np.zeros_like(values)
        np.add.at(total, self.edges[:, 0], values[self.edges[:, 1]])
        np.add.at(total, self.edges[:, 1], values[self.edges[:, 0]])
        valence = self.valence if values.ndim == 1 else self.valence[:, None]
        return total / valence

    def blur(self, weights, iterations):
        for _ in range(iterations):
            weights = 0.5 * weights + 0.5 * self.neighbor_mean(weights)
        return weights

    def faces_in(self, *names):
        ids = [i for name in names for i in FACE_SETS[name]]
        return np.isin(self.face_sets, ids)

    def in_sets(self, *names, blur=0):
        """1 on the vertices of the named face sets, 0 elsewhere, blurred across the border."""
        weights = np.zeros(len(self.co))
        weights[self.loop_verts[self.faces_in(*names)[self.loop_faces]]] = 1.0
        weights[self.count:] = np.isin(self.mark_sets, names)
        return self.blur(weights, blur)

    def border(self, some, others):
        """The vertices shared by the face sets named in some and those named in others."""
        return np.flatnonzero((self.in_sets(*some) > 0) & (self.in_sets(*others) > 0))

    def geodesic(self, sources, within):
        """Distance along edges from the source vertices, crossing only vertices in within."""
        import heapq
        neighbors = [[] for _ in range(len(self.co))]
        lengths = np.linalg.norm(self.co[self.edges[:, 0]] - self.co[self.edges[:, 1]], axis=1)
        for (a, b), length in zip(self.edges, lengths):
            if within[a] and within[b]:
                neighbors[a].append((b, length))
                neighbors[b].append((a, length))
        distance = np.full(len(self.co), np.inf)
        distance[sources] = 0.0
        queue = [(0.0, int(v)) for v in sources]
        while queue:
            d, v = heapq.heappop(queue)
            if d > distance[v]:
                continue
            for other, length in neighbors[v]:
                if d + length < distance[other]:
                    distance[other] = d + length
                    heapq.heappush(queue, (d + length, other))
        return distance

    def near(self, center, radius):
        """Smooth falloff around a point and its mirror image: 1 at the point, 0 at the radius."""
        radius = np.asarray(radius, dtype=float)
        center = np.asarray(center, dtype=float)

        def one(point):
            distance = np.linalg.norm((self.co - point) / radius, axis=1)
            return smoothstep(1.0 - distance)

        if abs(center[0]) < 1e-6:
            return one(center), None
        return one(center), one(center * MIRROR)

    def _each_side(self, center, radius, mask):
        center = np.asarray(center, dtype=float)
        here, there = self.near(center, radius)
        if mask is not None:
            here = here * mask
            there = None if there is None else there * mask
        yield center, here, np.ones(3)
        if there is not None:
            yield center * MIRROR, there, MIRROR

    def grab(self, center, radius, offset, mask=None):
        offset = np.asarray(offset, dtype=float)
        moved = np.zeros_like(self.co)
        for _, weight, sign in self._each_side(center, radius, mask):
            moved += weight[:, None] * offset * sign
        self.co += moved

    def scale(self, center, radius, factors, mask=None):
        factors = np.broadcast_to(np.asarray(factors, dtype=float), (3,))
        moved = np.zeros_like(self.co)
        for point, weight, _ in self._each_side(center, radius, mask):
            moved += weight[:, None] * (self.co - point) * (factors - 1.0)
        self.co += moved

    def inflate(self, center, radius, amount, mask=None):
        normals = self.normals()
        moved = np.zeros_like(self.co)
        for _, weight, _ in self._each_side(center, radius, mask):
            moved += weight[:, None] * normals * amount
        self.co += moved

    def smooth(self, center, radius, iterations=4, strength=0.5, mask=None):
        weight = sum(w for _, w, _ in self._each_side(center, radius, mask))
        self.relax(np.clip(weight, 0.0, 1.0), iterations, strength)

    def relax(self, weight, iterations=4, strength=0.5):
        weight = (weight * strength)[:, None]
        for _ in range(iterations):
            self.co += weight * (self.neighbor_mean(self.co) - self.co)


def load(art):
    """Appends the base mesh from art/third_party and returns its Cage."""
    with bpy.data.libraries.load(str(art / BASE_BLEND)) as (source, target):
        target.objects = [BASE_OBJECT]
    return Cage(target.objects[0].data)


def ball(points, center, radius):
    """Smooth falloff around a point: 1 at the point, 0 at the radius."""
    return smoothstep(1.0 - np.linalg.norm((points - center) / radius, axis=1))
