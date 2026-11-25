shader_type spatial;
// Plain cloth in the colors painted on its vertices.

#include "regions.gdshaderinc"

uniform float roughness : hint_range(0.0, 1.0) = 0.5;
uniform float rim : hint_range(0.0, 1.0) = 0.35;

void vertex() {
	VERTEX = unless_hidden(VERTEX, UV2);
}

void fragment() {
	ALBEDO = COLOR.rgb;
	ROUGHNESS = roughness;
	RIM = rim;
	RIM_TINT = 0.6;
}
