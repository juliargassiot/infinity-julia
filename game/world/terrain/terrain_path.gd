@tool
class_name TerrainPath
extends Path3D
## A road or a stream bed pressed into the terrain: within width the ground takes the path's height,
## and it blends back over falloff. A road follows the ground under it, smoothed along its length; a
## stream keeps the heights of its points. Paved paths are drawn as roads.

@export var width := 5.0
@export var falloff := 6.0
@export var follows_ground := true
@export var paved := true
