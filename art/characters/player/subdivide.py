"""Catmull-Clark subdivision of part of a closed all-quad mesh.

The chosen faces are subdivided once; the others keep their size but follow the smoothed surface,
and those bordering a subdivided face gain its edge points, so the surface stays watertight.
Subdivision is linear, so the same Subdivision maps shape keys and masks onto the new vertices.
"""
import numpy as np


class Subdivision:
    def __init__(self, faces, fine):
        """faces: (m, 4) vertex indices. fine: (m,) bool, the faces to subdivide."""
        self.faces = faces
        self.fine = fine
        self.vert_count = int(faces.max()) + 1
        corners = np.stack([faces, np.roll(faces, -1, axis=1)], axis=2).reshape(-1, 2)
        self.edges, corner_edge = np.unique(np.sort(corners, axis=1), axis=0, return_inverse=True)
        self.face_edges = corner_edge.reshape(-1, 4)
        self.edge_faces = np.argsort(self.face_edges.ravel(), kind="stable").reshape(-1, 2) // 4
        self.valence = np.bincount(self.edges.ravel(), minlength=self.vert_count).astype(float)

        fine_edges = np.zeros(len(self.edges), dtype=bool)
        fine_edges[self.face_edges[fine]] = True
        self.edge_slot = np.full(len(self.edges), -1)
        self.edge_slot[fine_edges] = self.vert_count + np.arange(fine_edges.sum())
        self.face_slot = np.full(len(faces), -1)
        self.face_slot[fine] = self.vert_count + fine_edges.sum() + np.arange(fine.sum())
        self.fine_edges = fine_edges

    def points(self, values):
        """Maps per-vertex values of the cage onto the vertices of the result."""
        values = np.asarray(values, dtype=float)
        flat = values.reshape(len(values), -1)
        face_points = flat[self.faces].mean(axis=1)
        ends = flat[self.edges].sum(axis=1)
        edge_points = (ends + face_points[self.edge_faces].sum(axis=1)) / 4.0

        around_faces = np.zeros_like(flat)
        np.add.at(around_faces, self.faces.ravel(), np.repeat(face_points, 4, axis=0))
        around_edges = np.zeros_like(flat)
        np.add.at(around_edges, self.edges[:, 0], ends / 2.0)
        np.add.at(around_edges, self.edges[:, 1], ends / 2.0)
        n = self.valence[:, None]
        vert_points = (around_faces / n + 2.0 * around_edges / n + (n - 3.0) * flat) / n

        result = np.vstack([vert_points, edge_points[self.fine_edges], face_points[self.fine]])
        return result.reshape(-1, *values.shape[1:])

    def polygons(self, corner_uvs):
        """The result's polygons as lists of vertex indices, with per-corner UVs and each
        polygon's source face. corner_uvs: (m, 4, 2)."""
        polygons, uvs, sources = [], [], []
        for face in range(len(self.faces)):
            verts = self.faces[face]
            edges = self.edge_slot[self.face_edges[face]]
            uv = corner_uvs[face]
            mid = (uv + np.roll(uv, -1, axis=0)) / 2.0
            if self.fine[face]:
                center = uv.mean(axis=0)
                for i in range(4):
                    polygons.append([verts[i], edges[i], self.face_slot[face], edges[i - 1]])
                    uvs.append([uv[i], mid[i], center, mid[i - 1]])
                    sources.append(face)
                continue
            polygon, polygon_uv = [], []
            for i in range(4):
                polygon.append(verts[i])
                polygon_uv.append(uv[i])
                if edges[i] >= 0:
                    polygon.append(edges[i])
                    polygon_uv.append(mid[i])
            polygons.append(polygon)
            uvs.append(polygon_uv)
            sources.append(face)
        return polygons, uvs, np.array(sources)
