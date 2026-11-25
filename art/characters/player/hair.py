"""The hairstyle: long, softly waved hair with bangs and face-framing side locks.

Every lock starts at the crown, runs over a shell around the skull to the hairline, and hangs
from there. Angles: azimuth 0 is the front (-Y), 90 her left (+X), 180 the back; polar 0 is
straight up. Vertex colors for the hair material: R a random value per lock, G 0 at the root to
1 at the tip, B the layer (0 underneath, 1 on top). Chains of bones carry the hanging parts.
"""
from dataclasses import dataclass

import numpy as np
from mathutils.bvhtree import BVHTree

from cage import smoothstep
from parts import Part, grid

CROWN = (180.0, 13.0)
SKULL_STEPS = 6
HANG_STEPS = 13
SECTION = np.array([(-1.0, 0.0), (-0.5, 0.85), (0.5, 0.85), (1.0, 0.0), (0.5, -0.3), (-0.5, -0.3)])
SECTION_U = np.array([0.0, 0.3, 0.7, 1.0, 0.7, 0.3])
CLEARANCE = 0.004


@dataclass
class Shell:
    """An ellipsoid a little larger than the skull, that the hair lies on."""
    center: np.ndarray
    radii: np.ndarray

    def direction(self, azimuth, polar):
        a, p = np.radians(azimuth), np.radians(polar)
        return np.array([np.sin(p) * np.sin(a), -np.sin(p) * np.cos(a), np.cos(p)])

    def point(self, direction, lift=0.0):
        return self.center + self.radii * direction * (1.0 + lift)

    def normal(self, point):
        normal = (point - self.center) / self.radii ** 2
        return normal / np.linalg.norm(normal)


@dataclass
class Lock:
    azimuth: float
    hairline: float
    end: np.ndarray
    end_direction: np.ndarray
    width: float
    thickness: float
    chain: str
    layer: float = 1.0
    lift: float = 0.0
    waves: float = 0.0
    wave_size: float = 0.0
    momentum: float = 0.05


def slerp(a, b, t):
    angle = np.arccos(np.clip(a @ b, -1.0, 1.0))
    return (np.sin((1.0 - t) * angle) * a + np.sin(t * angle) * b) / np.sin(angle)


def guide(shell, lock, random):
    """The lock's centre line, the outward direction at each point, and how far along the
    hanging part each point is: 0 on the skull, rising to 1 at the tip."""
    crown = shell.direction(*CROWN)
    hairline = shell.direction(lock.azimuth, lock.hairline)
    on_skull = [shell.point(slerp(crown, hairline, t), lock.lift * t)
                for t in np.linspace(0.0, 1.0, SKULL_STEPS)]
    leave = on_skull[-1]
    tangent = leave - on_skull[-2]
    tangent /= np.linalg.norm(tangent)
    reach = np.linalg.norm(lock.end - leave)
    handles = [leave, leave + tangent * lock.momentum,
               lock.end - lock.end_direction * reach * 0.35, lock.end]
    t = np.linspace(0.0, 1.0, HANG_STEPS + 1)[1:, None]
    hanging = ((1 - t) ** 3 * handles[0] + 3 * (1 - t) ** 2 * t * handles[1]
               + 3 * (1 - t) * t ** 2 * handles[2] + t ** 3 * handles[3])
    points = np.vstack([on_skull, hanging])
    hang = np.concatenate([np.zeros(SKULL_STEPS), t[:, 0]])

    outward = np.array([shell.normal(point) for point in points])
    flat = points - (0.0, shell.center[1] + 0.01, 0.0)
    flat[:, 2] = 0.0
    flat /= np.linalg.norm(flat, axis=1, keepdims=True)
    blend = smoothstep(hang / 0.35)[:, None]
    outward = outward * (1.0 - blend) + flat * blend
    outward /= np.linalg.norm(outward, axis=1, keepdims=True)

    along = np.gradient(points, axis=0)
    side = np.cross(along, outward)
    side /= np.linalg.norm(side, axis=1, keepdims=True)
    phase = random.uniform(0.0, 2.0 * np.pi)
    wave = np.sin(2.0 * np.pi * lock.waves * hang + phase) - np.sin(phase)
    points = points + side * (wave * lock.wave_size * hang)[:, None]
    return points, outward, hang


def keep_clear(points, outward, hang, tree, margin):
    """Pushes the hanging part of a centre line out of the body."""
    for _ in range(3):
        for i in np.flatnonzero(hang > 0.0):
            nearest, normal, _, distance = tree.find_nearest(points[i].tolist())
            away = points[i] - np.array(nearest)
            inside = away @ np.array(normal) < 0.0
            if inside or distance < margin:
                direction = np.array(normal) if inside or distance < 1e-6 else away / distance
                points[i] = np.array(nearest) + direction * margin
        smoothed = points.copy()
        smoothed[1:-1] = 0.25 * points[:-2] + 0.5 * points[1:-1] + 0.25 * points[2:]
        points = np.where((hang > 0.0)[:, None], smoothed, points)
    return points


def lock_part(shell, lock, tree, random, chains):
    points, outward, hang = guide(shell, lock, random)
    points = keep_clear(points, outward, hang, tree, lock.thickness * 0.35 + CLEARANCE)
    count = len(points)
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    along_all = np.concatenate([[0.0], np.cumsum(lengths)]) / lengths.sum()

    along = np.gradient(points, axis=0)
    along /= np.linalg.norm(along, axis=1, keepdims=True)
    side = np.cross(along, outward)
    side /= np.linalg.norm(side, axis=1, keepdims=True)
    out = np.cross(side, along)

    skull = np.linspace(0.0, 1.0, SKULL_STEPS)
    grow = np.concatenate([0.3 + 0.7 * skull, np.ones(count - SKULL_STEPS)])
    taper = (1.0 - hang ** 2.4) ** 0.75
    width = np.maximum(lock.width * 0.5 * grow * taper, 0.0004)
    thickness = lock.thickness * np.concatenate(
        [0.35 + 0.65 * skull, np.ones(count - SKULL_STEPS)]) * np.maximum(taper, 0.08)

    rings = (points[:, None, :] + side[:, None, :] * (width[:, None] * SECTION[:, 0])[:, :, None]
             + out[:, None, :] * (thickness[:, None] * SECTION[:, 1])[:, :, None])
    sections = len(SECTION)
    polygons = grid(count, sections, closed=True)
    uv = np.stack([np.tile(SECTION_U, count), np.repeat(along_all, sections)], axis=1)
    colors = np.stack([np.full(count * sections, random.uniform()), np.repeat(along_all, sections),
                       np.full(count * sections, lock.layer), np.ones(count * sections)], axis=1)
    shading = np.repeat(outward, sections, axis=0)
    part = Part("hair", rings.reshape(-1, 3), polygons, [uv[polygon] for polygon in polygons],
                colors, shading, groups=chain_weights(chains[lock.chain], np.repeat(hang, sections)))
    return part, points, hang


def chain_weights(chain, hang):
    """Weights along a chain of bones for points at the given distances down the hanging part;
    the head holds what lies on the skull."""
    names = ["Head"] + chain
    position = np.clip(hang * len(chain) + 0.5, 0.0, len(chain))
    return {name: np.clip(1.0 - np.abs(position - i), 0.0, 1.0) for i, name in enumerate(names)}


def cap(head, shell, hairline):
    """The scalp under the hair: the skin above the hairline, lifted a little."""
    offset = head.points - shell.center
    polar = np.degrees(np.arccos(offset[:, 2] / np.linalg.norm(offset, axis=1)))
    azimuth = np.degrees(np.arctan2(offset[:, 0], -offset[:, 1]))
    covered = polar < hairline(azimuth)
    polygons = [polygon for polygon in head.polygons if all(covered[polygon])]
    used = np.unique(np.concatenate(polygons))
    index = np.full(len(head.points), -1)
    index[used] = np.arange(len(used))
    uv = np.stack([azimuth / 360.0 + 0.5, polar / 180.0], axis=1)[used]
    polygons = [index[polygon].tolist() for polygon in polygons]
    colors = np.tile((0.5, 0.0, 0.0, 1.0), (len(used), 1))
    return Part("hair", head.points[used] + head.normals[used] * 0.003, polygons,
                [uv[polygon] for polygon in polygons], colors, head.normals[used],
                groups={"Head": np.ones(len(used))})


def hairline(azimuth):
    """How far down the shell the scalp reaches: the forehead in front, the nape behind."""
    toward_back = 0.5 - 0.5 * np.cos(np.radians(azimuth))
    return 58.0 + 58.0 * smoothstep(toward_back / 0.9)


def style(shell, eye, scale, tree, random):
    """The locks of the hairstyle and the bone chains that carry them: name -> bone count."""
    def front(x, z):
        return tree.find_nearest((x, -0.6, z))[0][1]

    def back(x, z):
        return tree.find_nearest((x, 0.6, z))[0][1]

    def leave(azimuth, polar):
        return shell.point(shell.direction(azimuth, polar))

    def unit(vector):
        return np.array(vector) / np.linalg.norm(vector)

    locks = []
    chains = {"HairFrontLeft": 2, "HairFront": 2, "HairFrontRight": 2, "HairSideLeft": 3,
              "HairSideRight": 3, **{f"HairBack{i}": 5 for i in range(1, 6)}}

    for azimuth in np.linspace(-60.0, 60.0, 9):
        x = leave(azimuth, 56.0)[0] * 0.93 + random.uniform(-0.004, 0.004)
        drop = np.interp(abs(x) / scale, [0.0, 0.02, 0.05, 0.07, 0.085],
                         [0.004, 0.012, 0.027, 0.008, -0.03])
        z = eye[2] + scale * drop + random.uniform(-0.003, 0.003)
        end = np.array([x, front(x, z) - 0.012, z])
        chain = ("HairFront" if abs(azimuth) < 20.0
                 else "HairFrontLeft" if azimuth > 0.0 else "HairFrontRight")
        locks.append(Lock(azimuth, 56.0, end, unit((np.sign(x) * 0.25, 0.3, -1.0)),
                          scale * 0.044, scale * 0.011, chain, lift=0.08, momentum=0.035))

    for sign, name in ((1.0, "HairSideLeft"), (-1.0, "HairSideRight")):
        for azimuth, z, x in ((66.0, 1.25, 0.078), (84.0, 1.33, 0.092)):
            z = eye[2] - scale * (1.525 - z) / 0.9
            end = np.array([sign * x, front(sign * x, z) - 0.016, z])
            locks.append(Lock(sign * azimuth, 80.0, end, unit((-sign * 0.25, 0.1, -1.0)),
                              scale * 0.046, scale * 0.012, name, lift=0.06, waves=1.0,
                              wave_size=0.006))

    for layer, count, width, lift, longer in ((0.0, 8, 0.09, 0.02, -0.04), (1.0, 15, 0.062, 0.09, 0.0)):
        for azimuth in np.linspace(102.0, 258.0, count):
            azimuth += random.uniform(-3.0, 3.0)
            polar = 108.0 + random.uniform(-5.0, 5.0)
            x = leave(azimuth, polar)[0] * 1.1
            z = 1.0 - longer + 0.06 * abs(np.sin(np.radians(azimuth))) + random.uniform(-0.03, 0.03)
            end = np.array([x, back(x, z) + 0.018 + 0.016 * layer, z])
            chain = f"HairBack{int(np.clip(round((azimuth - 110.0) / 35.0), 0, 4)) + 1}"
            locks.append(Lock(azimuth, polar, end, unit((np.sign(x) * 0.1, -0.1, -1.0)),
                              scale * width, scale * 0.014, chain, layer, lift, waves=1.4,
                              wave_size=0.011 * layer + 0.004, momentum=0.06))
    return locks, chains


def build(head, eye, scale, tree):
    """Returns the hair parts and, for the rig, each chain's joints from root to tip. The
    chain's bones are named <chain>_1, <chain>_2 and so on."""
    random = np.random.default_rng(7)
    shell = Shell(np.array([0.0, eye[1] + 0.052 * scale, eye[2] + 0.044 * scale]),
                  scale * np.array([0.113, 0.136, 0.12]))
    locks, chains = style(shell, eye, scale, tree, random)
    bones = {name: [f"{name}_{i + 1}" for i in range(count)] for name, count in chains.items()}
    parts = [cap(head, shell, hairline)]
    lines = {name: [] for name in chains}
    for lock in locks:
        part, points, hang = lock_part(shell, lock, tree, random, bones)
        parts.append(part)
        stops = np.linspace(0.0, 1.0, chains[lock.chain] + 1)
        start = SKULL_STEPS - 1
        lines[lock.chain].append(np.stack(
            [np.interp(stops, hang[start:], points[start:, axis]) for axis in range(3)], axis=1))
    return parts, {name: np.mean(members, axis=0) for name, members in lines.items()}
