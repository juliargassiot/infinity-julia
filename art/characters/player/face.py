"""The parts of the face that are not skin: eyes, lashes and brows.

Each function builds the left side (+X); the build mirrors it. Sizes are in metres on the finished
head. Lashes and brows are vertex-colored for the face_details material: RGB is the color and A is
how much of it the hair color tints.
"""
import numpy as np
from mathutils.bvhtree import BVHTree

from cage import FACE_SETS, smoothstep
from parts import Binding, Part, grid

EYE_MARGIN = 0.006
EYE_TUCK = 0.0025
EYE_UV_RADIUS = 0.03
EYE_INSET = 0.0006
LASH_COLOR = (0.07, 0.05, 0.055, 0.4)
BROW_COLOR = (0.5, 0.46, 0.46, 1.0)
TEETH_COLOR = (0.93, 0.92, 0.88, 0.0)
TONGUE_COLOR = (0.8, 0.36, 0.38, 0.0)


def eye(head, center, radius, opening, scale):
    """A cap of the eyeball looking along -Y, a little wider than the opening between the
    lids and shaded as if nearly flat. UVs map the view from the front: EYE_UV_RADIUS from the
    pupil is the edge of the UV square."""
    rings, segments = 12, 32
    reach = np.arcsin((opening + EYE_MARGIN * scale) / radius)
    polar = np.repeat(np.linspace(0.0, reach, rings + 1)[1:], segments)
    around = np.tile(np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False), rings)
    polar, around = np.append(polar, 0.0), np.append(around, 0.0)
    direction = np.stack([np.sin(polar) * np.cos(around), -np.cos(polar),
                          np.sin(polar) * np.sin(around)], axis=1)
    uv = 0.5 + 0.5 * radius * direction[:, [0, 2]] / (EYE_UV_RADIUS * scale)
    pole = rings * segments
    polygons = [polygon[::-1] for polygon in grid(rings, segments, closed=True)]
    polygons += [[pole, i, (i + 1) % segments] for i in range(segments)]
    shading = direction * 0.35 + (0.0, -0.65, 0.0)
    points = tucked(head, center + radius * direction, EYE_TUCK * scale)
    return Part("eye", points, polygons, [uv[polygon] for polygon in polygons],
                np.ones((len(direction), 4)), shading / np.linalg.norm(shading, axis=1)[:, None],
                groups={"LeftEye": np.ones(len(polar))})


def tucked(head, points, depth):
    """Pulls the points that would show through the face back under the skin."""
    tree = BVHTree.FromPolygons(head.points.tolist(), head.polygons)
    face_skin = ~np.isin(head.face_sets, FACE_SETS["eyelid"] + FACE_SETS["socket"])
    points = points.copy()
    for i, point in enumerate(points):
        nearest, normal, polygon, _ = tree.find_nearest(point.tolist())
        nearest, normal = np.array(nearest), np.array(normal)
        if face_skin[polygon] and (point - nearest) @ normal > -depth:
            points[i] = nearest - normal * depth
    return points


def eyes(head, center, radius, opening, scale):
    """Both eyes. The right one keeps the left one's UVs unmirrored, so the catchlights sit on
    the same side of both."""
    left = eye(head, center, radius, opening, scale)
    right = left.mirrored()
    right.uvs = [uv * (-1.0, 1.0) + (1.0, 0.0) for uv in right.uvs]
    return [left, right]


def lid_edges(head, ring, beside):
    """The left eye's border between two face sets as two rows of vertices, each from the
    inner corner to the outer corner: along the upper lid and along the lower lid."""
    def verts(name):
        faces = np.flatnonzero(np.isin(head.face_sets, FACE_SETS[name]))
        return set(v for face in faces for v in head.polygons[face])

    shared = {v for v in verts(ring) & verts(beside) if head.points[v][0] > 0.0}
    neighbors = {v: set() for v in shared}
    for polygon in head.polygons:
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            if a in shared and b in shared:
                neighbors[a].add(b)
                neighbors[b].add(a)
    start = min(shared, key=lambda v: head.points[v][0])
    loop, previous = [start], None
    while True:
        following = next(v for v in neighbors[loop[-1]] if v != previous)
        if following == start:
            break
        previous = loop[-1]
        loop.append(following)
    outer = int(np.argmax(head.points[loop][:, 0]))
    one, other = loop[:outer + 1], [loop[0]] + loop[:outer - 1:-1]
    if head.points[one][:, 2].mean() < head.points[other][:, 2].mean():
        one, other = other, one
    return one, other


def on_skin(tree, points, lift):
    """The points moved onto the skin and lifted off it along its normal."""
    found = [tree.find_nearest(point.tolist()) for point in points]
    return np.array([np.array(f[0]) + np.array(f[1]) * l for f, l in zip(found, lift)])


def swung(center, at, delta, points):
    """Where points end up when they are carried along as `at` moves by delta around center."""
    before, after = at - center, at + delta - center
    axis = np.cross(before, after)
    scale = np.linalg.norm(before, axis=1) * np.linalg.norm(after, axis=1)
    sine = np.linalg.norm(axis, axis=1)
    axis = axis / np.maximum(sine, 1e-12)[:, None]
    sine, cosine = (sine / scale)[:, None], ((before * after).sum(axis=1) / scale)[:, None]
    arm = points - at
    along = (axis * arm).sum(axis=1, keepdims=True)
    return (at + delta + arm * cosine + np.cross(axis, arm) * sine
            + axis * along * (1.0 - cosine))


def lash_band(head, tree, eye, margin, rim, up, thickness):
    """A ridge over a lid's rim, from its row of vertices at the eye across to the row at the
    skin: thickness(t) times as wide as the rim, t running from the inner corner to the outer.
    It swings around the eye with the lid's edge, so it keeps its shape when the eye closes."""
    at, to = head.points[margin], head.points[rim]
    lengths = np.linalg.norm(np.diff(at, axis=0), axis=1)
    t = np.concatenate([[0.0], np.cumsum(lengths)]) / lengths.sum()
    reach = thickness(t)
    across = np.concatenate([np.full(len(t), -0.12), reach * 0.5, reach])
    lift = np.repeat([0.0002, 0.0009, 0.0003], len(t))
    at, to = np.tile(at, (3, 1)), np.tile(to, (3, 1))
    points = on_skin(tree, at + (to - at) * across[:, None], lift)
    shapes = {name: swung(eye, at, np.tile(delta[margin], (3, 1)), points) - points
              for name, delta in head.shapes.items()}
    polygons = grid(3, len(t))
    if up < 0:
        polygons = [polygon[::-1] for polygon in polygons]
    return points, polygons, shapes


def lashes(head, eye):
    """A thick upper lash line and a fine lower one around the left eye."""
    tree = BVHTree.FromPolygons(head.points.tolist(), head.polygons)
    upper_margin, lower_margin = lid_edges(head, "eyelid", "socket")
    upper_rim, lower_rim = lid_edges(head, "eyelid", "orbit")

    def upper_thickness(t):
        full = 0.6 + 1.3 * smoothstep(t / 0.35) * (0.5 + 0.5 * t)
        return full * (1.0 - 0.6 * smoothstep((t - 0.9) / 0.1))

    def lower_thickness(t):
        return 0.2 + 0.5 * smoothstep((t - 0.1) / 0.6)

    start = len(lower_margin) // 3
    upper = lash_band(head, tree, eye, upper_margin, upper_rim, 1.0, upper_thickness)
    lower = lash_band(head, tree, eye, lower_margin[start:-1], lower_rim[start:-1], -1.0,
                      lower_thickness)
    points = np.vstack([upper[0], lower[0]])
    polygons = upper[1] + [[v + len(upper[0]) for v in polygon] for polygon in lower[1]]
    shapes = {name: np.vstack([upper[2][name], lower[2][name]]) for name in head.shapes}
    return detail(points, polygons, LASH_COLOR, shapes)


def brow(head, center, scale):
    tree = BVHTree.FromPolygons(head.points.tolist(), head.polygons)
    s = np.linspace(0.0, 1.0, 14)
    x = center[0] + scale * (-0.022 + 0.052 * s)
    z = center[2] + scale * (0.0345 + 0.0045 * np.sin(np.pi * s ** 0.8) - 0.005 * s ** 2)
    width = scale * 0.0034 * (1.0 - 0.72 * s ** 1.4) * (0.55 + 0.45 * smoothstep(s / 0.12))
    rows = []
    for across, lift in ((-0.5, 0.0002), (0.0, 0.0008), (0.5, 0.0002)):
        row = []
        for xi, zi, wi in zip(x, z, width):
            hit, normal, _, _ = tree.ray_cast((xi, center[1] - 1.0, zi + across * wi), (0, 1, 0))
            row.append(np.array(hit) + np.array(normal) * lift)
        rows.append(row)
    points = np.array(rows).reshape(-1, 3)
    binding = Binding(head.points, head.triangles(), points)
    return detail(points, grid(3, len(s)), BROW_COLOR, binding.shapes(head.points, head.shapes))


def detail(points, polygons, color, shapes):
    """A face_details part of one color that moves with the head."""
    return Part("face_details", points, polygons, [np.zeros((len(p), 2)) for p in polygons],
                np.tile(color, (len(points), 1)), None, shapes,
                groups={"Head": np.ones(len(points))})


def arch(width, depth, top, bottom, thickness):
    """A row of teeth as one smooth band around the front of the mouth, its front centre at
    the origin: points and polygons."""
    steps = 13
    angle = np.linspace(-1.5, 1.5, steps)
    section = [(0.0, top), (0.0, bottom), (thickness, bottom), (thickness, top)]
    rows = [np.stack([(width - inset) * np.sin(angle), depth - (depth - inset) * np.cos(angle),
                      np.full(steps, height)], axis=1) for inset, height in section]
    return np.vstack(rows), grid(len(section), steps) + [
        [3 * steps + i, 3 * steps + i + 1, i + 1, i] for i in range(steps - 1)]


def mouth(rig, scale):
    """Teeth and tongue, hidden behind the lips until the jaw opens."""
    s = scale
    front = rig.mouth + np.array([0.0, 0.0035, 0.0]) * s
    upper, upper_polygons = arch(0.017 * s, 0.022 * s, 0.008 * s, -0.0012 * s, 0.003 * s)
    lower, lower_polygons = arch(0.016 * s, 0.021 * s, -0.009 * s, -0.0016 * s, 0.003 * s)
    lower_polygons = [polygon[::-1] for polygon in lower_polygons]
    rings, segments = 6, 10
    polar = np.repeat(np.linspace(0.0, np.pi, rings + 2)[1:-1], segments)
    around = np.tile(np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False), rings)
    ball = np.stack([np.sin(polar) * np.cos(around), np.cos(polar), np.sin(polar) * np.sin(around)], 1)
    ball = np.vstack([ball, [(0.0, 1.0, 0.0), (0.0, -1.0, 0.0)]])
    tongue = ball * np.array([0.011, 0.017, 0.0035]) * s + np.array([0.0, 0.021, -0.006]) * s
    top, tip = rings * segments, rings * segments + 1
    tongue_polygons = [polygon[::-1] for polygon in grid(rings, segments, closed=True)]
    tongue_polygons += [[top, (i + 1) % segments, i] for i in range(segments)]
    tongue_polygons += [[tip, top - segments + i, top - segments + (i + 1) % segments]
                        for i in range(segments)]

    points = np.vstack([upper, lower, tongue]) + front
    offsets = np.cumsum([0, len(upper), len(lower)])
    polygons = [[v + offset for v in polygon] for offset, part in zip(
        offsets, (upper_polygons, lower_polygons, tongue_polygons)) for polygon in part]
    colors = np.vstack([np.tile(TEETH_COLOR, (len(upper) + len(lower), 1)),
                        np.tile(TONGUE_COLOR, (len(tongue), 1))])
    moves = np.concatenate([np.zeros(len(upper)), np.ones(len(lower) + len(tongue))])
    return Part("face_details", points, polygons, [np.zeros((len(p), 2)) for p in polygons],
                colors, None, {"jawOpen": rig.jaw(points, moves)},
                groups={"Head": np.ones(len(points))})
