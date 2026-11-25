"""Posing math for the rig, in armature space (X her left, -Y forward, Z up).

A pose gives each bone a turn relative to its parent, written in the armature's axes as if the
whole body were in its rest pose. That makes poses readable: turning an upper arm about Y lowers
it whatever its bone's own axes are.
"""
import numpy as np
from mathutils import Quaternion, Vector

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def turn(x=0.0, y=0.0, z=0.0):
    """A turn by angles in degrees about the armature's Z, then X, then Y axes."""
    return (Quaternion(Y, np.radians(y)) @ Quaternion(X, np.radians(x))
            @ Quaternion(Z, np.radians(z)))


def mirrored(rotation):
    return Quaternion((rotation.w, rotation.x, -rotation.y, -rotation.z))


class Figure:
    def __init__(self, armature):
        self.armature = armature
        bones = armature.data.bones
        self.parents = {bone.name: bone.parent.name if bone.parent else None for bone in bones}
        self.heads = {bone.name: bone.head_local.copy() for bone in bones}
        self.tails = {bone.name: bone.tail_local.copy() for bone in bones}
        self.rest = {bone.name: bone.matrix_local.to_quaternion() for bone in bones}
        self.order = [bone.name for bone in bones]

    def solve(self, turns, hips=Vector()):
        """World turns and joint positions of every bone, for turns relative to the parents and
        an offset of the hips."""
        world, at = {}, {}
        for name in self.order:
            parent = self.parents[name]
            own = turns.get(name, Quaternion())
            if parent is None:
                world[name], at[name] = own, self.heads[name] + hips
            else:
                world[name] = world[parent] @ own
                at[name] = at[parent] + world[parent] @ (self.heads[name] - self.heads[parent])
        return world, at

    def leg(self, side, turns, hips, ankle, toe_pitch=0.0, knee_out=0.0):
        """Adds to turns what the leg needs for its ankle to reach a point, the knee pointing
        forward and outward by knee_out degrees, the foot pitched down by toe_pitch degrees."""
        upper, lower, foot = (f"{side}UpperLeg", f"{side}LowerLeg", f"{side}Foot")
        world, at = self.solve(turns, hips)
        hips_turn = world["Hips"]
        thigh = (self.heads[lower] - self.heads[upper]).length
        shin = (self.heads[foot] - self.heads[lower]).length
        reach = ankle - at[upper]
        distance = min(reach.length, (thigh + shin) * 0.999)
        direction = reach.normalized()
        outward = 1.0 if side == "Left" else -1.0
        forward = Quaternion(Z, np.radians(knee_out * outward)) @ Vector((0.0, -1.0, 0.0))
        bend_axis = direction.cross(forward).normalized()
        hip_angle = np.arccos((thigh ** 2 + distance ** 2 - shin ** 2) / (2 * thigh * distance))
        knee_angle = np.pi - np.arccos((thigh ** 2 + shin ** 2 - distance ** 2) / (2 * thigh * shin))
        thigh_direction = Quaternion(bend_axis, hip_angle) @ direction
        shin_direction = Quaternion(bend_axis, -knee_angle) @ thigh_direction

        def aim(rest_from, rest_to, direction, hinge):
            rest_direction = (rest_to - rest_from).normalized()
            swing = rest_direction.rotation_difference(direction)
            rest_hinge = rest_direction.cross(Vector((0.0, -1.0, 0.0))).normalized()
            twist = (swing @ rest_hinge).rotation_difference(hinge)
            return twist @ swing

        thigh_world = aim(self.heads[upper], self.heads[lower], thigh_direction, bend_axis)
        shin_world = aim(self.heads[lower], self.heads[foot], shin_direction, bend_axis)
        foot_world = Quaternion(Z, np.radians(knee_out * outward * 0.6)) @ Quaternion(X, np.radians(toe_pitch))
        turns[upper] = hips_turn.inverted() @ thigh_world
        turns[lower] = thigh_world.inverted() @ shin_world
        turns[foot] = shin_world.inverted() @ foot_world

    def apply(self, turns, hips=Vector()):
        """Poses the armature."""
        for name, bone in self.armature.pose.bones.items():
            rest = self.rest[name]
            bone.rotation_mode = "QUATERNION"
            bone.rotation_quaternion = rest.inverted() @ turns.get(name, Quaternion()) @ rest
        hips_bone = self.armature.pose.bones["Hips"]
        hips_bone.location = self.rest["Hips"].inverted() @ hips
