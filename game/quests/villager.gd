class_name Villager
extends Speaker
## A placeholder villager until real characters come: a robed figure in a pointed hat, in her own
## colors. She faces along +Z.

@export var robe := Color(0.55, 0.42, 0.7)
@export var hat := Color(0.3, 0.22, 0.4)
@export var skin := Color(0.96, 0.82, 0.74)


func _ready() -> void:
	super()
	_paint($Robe, robe)
	_paint($Hat, hat)
	_paint($Hat/Brim, hat)
	_paint($Head, skin)


static func _paint(mesh: MeshInstance3D, color: Color) -> void:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.8
	mesh.material_override = material
