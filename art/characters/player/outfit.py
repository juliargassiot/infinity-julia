"""The placeholder outfit: a sleeveless romper cut from the body's own faces and lifted off the
skin. Its vertices keep the weights of the skin under them, so it follows every pose exactly.

Vertex colors are the fabric's colors, for a material that uses them as albedo.
"""
import numpy as np

from cage import FACE_SETS
from parts import Part
from skin import REGIONS

LIFT = 0.004
LEG_ROWS = 3
WING_OPENING = 0.075
FABRIC = (0.93, 0.9, 0.86, 1.0)
TRIM = (0.86, 0.47, 0.58, 1.0)


def romper(body, wings):
    """Covers the torso and the first LEG_ROWS rows of faces down each thigh. Its faces keep the
    regions of the skin under them, so more clothing can hide them in turn; those around the
    point where wings attach are the opening for wings."""
    points, normals = body.points, body.normals
    trunk = np.isin(body.face_sets, FACE_SETS["torso"] + FACE_SETS["pelvis"])
    thigh = np.isin(body.face_sets, FACE_SETS["thigh"])
    reached = np.zeros(len(points), dtype=bool)
    reached[np.concatenate([body.polygons[i] for i in np.flatnonzero(trunk)])] = True
    covered = set(np.flatnonzero(trunk))
    for _ in range(LEG_ROWS):
        row = [i for i in np.flatnonzero(thigh) if i not in covered and reached[body.polygons[i]].any()]
        covered.update(row)
        reached[np.concatenate([body.polygons[i] for i in row])] = True
    covered = sorted(covered)
    used = np.unique(np.concatenate([body.polygons[i] for i in covered]))
    index = np.full(len(points), -1)
    index[used] = np.arange(len(used))
    polygons = [[int(index[v]) for v in body.polygons[i]] for i in covered]
    uvs = [body.uvs[i] for i in covered]
    centers = np.array([points[body.polygons[i]].mean(axis=0) for i in covered])
    regions = np.where(np.linalg.norm(centers - wings, axis=1) < WING_OPENING,
                       REGIONS.index("WingOpening"), body.regions[covered])

    sides = {}
    for polygon in polygons:
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            sides[(a, b)] = sides.get((a, b), 0) + 1
    edge = [(a, b) for (a, b) in sides if (b, a) not in sides]
    on_edge = np.unique(edge)
    under = np.full(len(used), -1)
    under[on_edge] = len(used) + np.arange(len(on_edge))
    for a, b in edge:
        polygons.append([int(b), int(a), int(under[a]), int(under[b])])
        uvs.append(np.zeros((4, 2)))
    regions = np.concatenate([regions, np.zeros(len(edge), dtype=int)])

    shell = points[used] + normals[used] * LIFT
    tucked = points[used][on_edge] - normals[used][on_edge] * 0.001
    colors = np.tile(FABRIC, (len(used), 1))
    colors[on_edge] = TRIM
    groups = {name: np.concatenate([weight[used], weight[used][on_edge]])
              for name, weight in body.groups.items()}
    return Part("outfit", np.vstack([shell, tucked]), polygons, uvs,
                np.vstack([colors, np.tile(TRIM, (len(on_edge), 1))]),
                np.vstack([normals[used], normals[used][on_edge]]), groups=groups,
                regions=regions)
