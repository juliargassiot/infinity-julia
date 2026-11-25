"""Mesh parts as plain arrays, joined into Blender objects at the end of the build.

A Part carries everything a surface of the exported model needs. Its regions, one number per
polygon, go into a second UV layer: the game hides the regions that clothing covers. Parts that ride on the skin
(lashes, brows) get their expression shapes from a Binding to the skin's triangles.
"""
from dataclasses import dataclass, field

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

MIRROR = np.array([-1.0, 1.0, 1.0])


@dataclass
class Part:
    material: str
    points: np.ndarray
    polygons: list
    uvs: list
    colors: np.ndarray
    normals: np.ndarray = None
    shapes: dict = field(default_factory=dict)
    face_sets: np.ndarray = None
    groups: dict = None
    regions: np.ndarray = None

    def mirrored(self):
        """The same part on the other side of the body, with the sides of its groups' and
        shapes' names swapped."""
        flip = lambda array: None if array is None else array * MIRROR
        return Part(self.material, flip(self.points), [polygon[::-1] for polygon in self.polygons],
                    [uv[::-1] for uv in self.uvs], self.colors, flip(self.normals),
                    {other_side(name): flip(delta) for name, delta in self.shapes.items()}, self.face_sets,
                    self.groups and {other_side(name): w for name, w in self.groups.items()},
                    self.regions)

    def triangles(self):
        return np.array([[polygon[0], polygon[i], polygon[i + 1]]
                         for polygon in self.polygons for i in range(1, len(polygon) - 1)])


def other_side(name):
    for one, other in (("Left", "Right"), ("Right", "Left")):
        if one in name:
            return name.replace(one, other)
    return name


def grid(rows, columns, closed=False):
    """Quads of a rows x columns vertex grid, numbered row by row; closed joins the last column
    to the first."""
    quads = []
    for row in range(rows - 1):
        for column in range(columns if closed else columns - 1):
            a = row * columns + column
            b = row * columns + (column + 1) % columns
            quads.append([a, b, b + columns, a + columns])
    return quads


class Binding:
    """Ties points to the nearest triangles of a surface, so they follow when it deforms."""

    def __init__(self, surface, triangles, points):
        self.triangles = triangles
        tree = BVHTree.FromPolygons(surface.tolist(), triangles.tolist())
        nearest = [tree.find_nearest(point.tolist()) for point in points]
        self.picked = triangles[[found[2] for found in nearest]]
        on_surface = np.array([found[0] for found in nearest])
        a, b, c = (surface[self.picked[:, i]] for i in range(3))
        normal = np.cross(b - a, c - a)
        area = (normal * normal).sum(axis=1)
        self.weights = np.stack([
            (np.cross(c - b, on_surface - b) * normal).sum(axis=1) / area,
            (np.cross(a - c, on_surface - c) * normal).sum(axis=1) / area,
            (np.cross(b - a, on_surface - a) * normal).sum(axis=1) / area], axis=1)
        origin, frame = self._frames(surface)
        self.local = np.einsum("nij,nj->ni", frame.transpose(0, 2, 1), points - origin)

    def _frames(self, surface):
        a, b, c = (surface[self.picked[:, i]] for i in range(3))
        origin = (np.stack([a, b, c], axis=1) * self.weights[:, :, None]).sum(axis=1)
        along = b - a
        along /= np.linalg.norm(along, axis=1, keepdims=True)
        normal = np.cross(along, c - a)
        normal /= np.linalg.norm(normal, axis=1, keepdims=True)
        return origin, np.stack([along, np.cross(normal, along), normal], axis=2)

    def follow(self, surface):
        origin, frame = self._frames(surface)
        return origin + np.einsum("nij,nj->ni", frame, self.local)

    def shapes(self, surface, shapes):
        rest = self.follow(surface)
        return {name: self.follow(surface + delta) - rest for name, delta in shapes.items()}


def to_object(name, parts):
    """Joins parts into one mesh object with a material slot per material."""
    materials = list(dict.fromkeys(part.material for part in parts))
    offsets = np.cumsum([0] + [len(part.points) for part in parts])
    points = np.vstack([part.points for part in parts])
    polygons = [[int(v) + offset for v in polygon]
                for part, offset in zip(parts, offsets) for polygon in part.polygons]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], polygons)
    mesh.uv_layers.new(name="UVMap").data.foreach_set(
        "uv", np.concatenate([uv for part in parts for uv in part.uvs]).ravel())
    if any(part.regions is not None for part in parts):
        regions = np.concatenate([
            np.repeat(part.regions if part.regions is not None else np.zeros(len(part.polygons)),
                      [len(polygon) for polygon in part.polygons]) for part in parts])
        mesh.uv_layers.new(name="Regions").data.foreach_set(
            "uv", np.stack([regions, np.zeros(len(regions))], axis=1).ravel())
    mesh.polygons.foreach_set("use_smooth", np.ones(len(polygons), dtype=bool))
    mesh.polygons.foreach_set("material_index", np.concatenate(
        [np.full(len(part.polygons), materials.index(part.material)) for part in parts]))
    mesh.attributes.new("Color", "FLOAT_COLOR", "POINT").data.foreach_set(
        "color", np.vstack([part.colors for part in parts]).ravel())
    for material in materials:
        mesh.materials.append(bpy.data.materials.get(material) or bpy.data.materials.new(material))
    if any(part.face_sets is not None for part in parts):
        mesh.attributes.new("face_set", "INT", "FACE").data.foreach_set("value", np.concatenate(
            [part.face_sets if part.face_sets is not None else np.zeros(len(part.polygons), int)
             for part in parts]))
    if any(part.normals is not None for part in parts):
        normals = np.empty(len(points) * 3)
        mesh.vertices.foreach_get("normal", normals)
        normals = normals.reshape(-1, 3)
        for part, offset in zip(parts, offsets):
            if part.normals is not None:
                normals[offset:offset + len(part.points)] = part.normals
        mesh.normals_split_custom_set_from_vertices(normals)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for part, offset in zip(parts, offsets):
        for group, weights in (part.groups or {}).items():
            vertex_group = obj.vertex_groups.get(group) or obj.vertex_groups.new(name=group)
            for vertex in np.flatnonzero(weights > 1e-4):
                vertex_group.add([int(vertex + offset)], float(weights[vertex]), "REPLACE")
    names = list(dict.fromkeys(key for part in parts for key in part.shapes))
    if names:
        obj.shape_key_add(name="Basis")
    for key in names:
        moved = np.vstack([part.points + part.shapes.get(key, 0.0) for part in parts])
        obj.shape_key_add(name=key).data.foreach_set("co", moved.ravel())
    return obj
