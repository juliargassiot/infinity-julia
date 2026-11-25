@tool
class_name TerrainShape
extends Marker3D
## Pulls the terrain to this marker's height within radius; nearby markers blend into each other.
## Roughness adds rolling hills of about that many meters.

@export var radius := 60.0
@export var roughness := 0.0
