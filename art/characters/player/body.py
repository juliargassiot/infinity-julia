"""Sculpts the base mesh into the player's body: slender, long-legged, with a doll-like face.

Coordinates are those of the unmodified base mesh; the proportion changes run last.
"""
import numpy as np

from cage import FOOT, HEAD, smoothstep

EYE = np.array([0.0473, -0.0804, 1.4633])
EYE_SCALE = 1.07
EYE_SHIFT = np.array([0.0015, 0.0385 * (EYE_SCALE - 1.0), -0.003])
# The eyeball is a cap of a larger sphere than the socket was made for: a flatter, anime eye
# that still turns without leaving its lids.
EYE_FLATTEN = 1.4
EYE_OPENING = 0.025 * EYE_SCALE
SOCKET_RADIUS = 0.0385 * EYE_SCALE
EYE_RADIUS = SOCKET_RADIUS * EYE_FLATTEN
EYE_SETBACK = (np.sqrt(EYE_RADIUS ** 2 - EYE_OPENING ** 2)
               - np.sqrt(SOCKET_RADIUS ** 2 - EYE_OPENING ** 2))
CROTCH = 0.80
LEG_STRETCH = 1.14
NECK_STRETCH = 0.012
HEAD_SCALE = 0.90
HEAD_PIVOT = np.array([0.0, -0.03, 1.36])


def sculpt_face(cage):
    head = cage.in_sets(*HEAD, blur=2)
    face = cage.in_sets("skull", "nose", "jaw", "upper_mouth", "lower_mouth", "orbit", "eyelid",
                        "socket", blur=1)
    co = cage.co

    # A small nose: narrow, short, barely there from the front.
    nose = (0.0, -0.13, 1.418)
    cage.scale(nose, (0.05, 0.06, 0.045), (0.3, 0.42, 0.62), mask=face)
    cage.grab((0.0, -0.144, 1.412), 0.026, (0.0, 0.002, 0.005), mask=face)
    cage.smooth((0.0, -0.138, 1.408), 0.034, iterations=14, mask=face)

    # A short lower face with a small mouth and soft, thin lips that sit back from the nose.
    lower = smoothstep((1.425 - co[:, 2]) / 0.06) * face
    co[:, 2] += lower * (1.425 - co[:, 2]) * 0.12
    mouth = (0.0, -0.125, 1.392)
    cage.scale(mouth, (0.07, 0.07, 0.045), (0.56, 0.7, 0.62), mask=face)
    cage.grab((0.0, -0.14, 1.392), 0.04, (0.0, 0.006, 0.002), mask=face)

    # The lower face tapers to a small chin.
    taper = smoothstep((1.45 - co[:, 2]) / 0.11) * face
    front = smoothstep((0.0 - co[:, 1]) / 0.08)
    co[:, 0] *= 1.0 - 0.19 * taper * (0.4 + 0.6 * front)
    cage.scale((0.0, -0.12, 1.35), (0.06, 0.07, 0.04), (0.76, 0.95, 0.9), mask=face)

    # Softer cheeks and a flatter profile between the eyes.
    cage.inflate((0.058, -0.112, 1.412), 0.045, 0.002, mask=face)
    cage.grab((0.0, -0.14, 1.462), 0.03, (0.0, 0.004, 0.0), mask=face)

    # Large eyes, set a little low and wide: taller, slightly raised at the outer corner, the
    # lids still hugging the eyeball.
    eye_area = cage.in_sets("eyelid", "socket", blur=3)
    lids = cage.in_sets("eyelid", "socket")
    eyes = np.where(co[:, :1] >= 0.0, EYE, EYE * (-1.0, 1.0, 1.0))
    distance = np.linalg.norm(co - eyes, axis=1) * EYE_SCALE
    co += eye_area[:, None] * (co - eyes) * (EYE_SCALE - 1.0)
    cage.scale(EYE, (0.07, 0.09, 0.07), (1.0, 1.0, 1.1), mask=eye_area)
    cage.grab(EYE + (0.03, -0.03, 0.0), 0.024, (0.002, 0.0, 0.0045), mask=eye_area)
    cage.grab(EYE + (-0.026, -0.03, -0.002), 0.02, (0.0, 0.0, -0.003), mask=eye_area)
    offset = cage.co - eyes
    fitted = eyes + offset * (distance / np.maximum(np.linalg.norm(offset, axis=1), 1e-9))[:, None]
    cage.co += lids[:, None] * (fitted - cage.co)
    eyes = eyes + (0.0, EYE_SETBACK, 0.0)
    offset = cage.co - eyes
    reach = np.maximum(np.linalg.norm(offset, axis=1), 1e-9)
    fitted = eyes + offset * ((EYE_RADIUS + distance - SOCKET_RADIUS) / reach)[:, None]
    cage.co += (lids * cage.in_sets("eyelid", blur=1))[:, None] * (fitted - cage.co)
    cage.co[cage.marks["eye"]] = EYE + (0.0, EYE_SETBACK, 0.0)
    cage.co += eye_area[:, None] * EYE_SHIFT * np.where(cage.co[:, :1] >= 0.0, 1.0, (-1.0, 1.0, 1.0))
    # Lids that lie flat in the face, without a rim around the eye.
    around = cage.in_sets("eyelid", "orbit", blur=1)
    around[cage.border(["eyelid"], ["socket"])] = 0.0
    cage.relax(around * (1.0 - cage.in_sets("socket")), iterations=14)

    # Small ears, held close to the head.
    ear = cage.in_sets("ear", blur=1)
    root = (0.1, -0.012, 1.445)
    cage.scale(root, (0.09, 0.09, 0.09), (0.55, 0.78, 0.74), mask=ear)
    return head


def sculpt_body(cage):
    legs = cage.in_sets("thigh", "shin", "pelvis", blur=3)
    trunk = cage.in_sets("pelvis", "torso", "thigh", blur=3)

    cage.scale((0.085, -0.02, 0.66), (0.16, 0.25, 0.3), (0.84, 0.86, 1.0), mask=legs)
    cage.scale((0.07, -0.01, 0.3), (0.12, 0.2, 0.22), (0.9, 0.9, 1.0), mask=legs)
    cage.scale((0.0, -0.02, 0.9), (0.4, 0.4, 0.16), (0.99, 0.97, 1.0), mask=trunk)
    cage.scale((0.0, -0.02, 1.06), (0.4, 0.4, 0.1), (0.82, 0.88, 1.0), mask=trunk)

    chest = cage.in_sets("torso", blur=2)
    cage.inflate((0.058, -0.105, 1.165), 0.05, 0.009, mask=chest)
    cage.smooth((0.058, -0.1, 1.13), 0.05, iterations=8, mask=chest)


def proportion(cage, head):
    co = cage.co
    leg = cage.in_sets("thigh", "shin", *FOOT)
    below = np.where(leg > 0.5, np.minimum(co[:, 2], CROTCH), CROTCH)
    co[:, 2] += (LEG_STRETCH - 1.0) * below
    neck = co[cage.in_sets("neck") > 0.5, 2]
    above = np.clip((co[:, 2] - neck.min()) / (neck.max() - neck.min()), 0.0, 1.0)
    co[:, 2] += NECK_STRETCH * above * (cage.in_sets("neck", *HEAD) > 0.5)
    pivot = HEAD_PIVOT + (0.0, 0.0, (LEG_STRETCH - 1.0) * CROTCH + NECK_STRETCH)
    co += head[:, None] * (co - pivot) * (HEAD_SCALE - 1.0)


def sculpt(cage):
    cage.mark("eye", EYE, "socket")
    head = sculpt_face(cage)
    sculpt_body(cage)
    proportion(cage, head)
    cage.write()
