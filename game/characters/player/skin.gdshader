shader_type spatial;
render_mode sss_mode_skin;

#include "regions.gdshaderinc"
// Vertex color masks: R lips, G blush, B thin skin that light shines through, A 1 on open skin
// and 0 inside the mouth and eye sockets.

instance uniform vec3 skin_color : source_color, instance_index(0) = vec3(0.97, 0.8, 0.72);

uniform vec3 lip_tint : source_color = vec3(0.86, 0.33, 0.4);
uniform float lip_strength : hint_range(0.0, 1.0) = 0.9;
uniform vec3 blush_tint : source_color = vec3(1.0, 0.5, 0.5);
uniform float blush_strength : hint_range(0.0, 1.0) = 0.42;
uniform vec3 inside_color : source_color = vec3(0.3, 0.07, 0.09);
uniform vec3 blood_tint : source_color = vec3(1.0, 0.36, 0.26);
uniform float roughness : hint_range(0.0, 1.0) = 0.52;
uniform float lip_roughness : hint_range(0.0, 1.0) = 0.28;
uniform float scatter : hint_range(0.0, 1.0) = 0.3;
uniform float translucency : hint_range(0.0, 1.0) = 0.5;
uniform float rim : hint_range(0.0, 1.0) = 0.15;
uniform float wrap : hint_range(0.0, 1.0) = 0.3;
// How fast each color fades into shadow: red lingers, so shadow edges turn warm.
uniform vec3 shadow_falloff = vec3(0.72, 1.25, 1.45);
uniform float warmth : hint_range(0.0, 0.3) = 0.06;

varying float thin;

void vertex() {
	VERTEX = unless_hidden(VERTEX, UV2);
}

void fragment() {
	vec3 base = mix(skin_color, skin_color * blush_tint, COLOR.g * blush_strength);
	base = mix(base, mix(base * lip_tint, lip_tint, 0.4), COLOR.r * lip_strength);
	ALBEDO = mix(inside_color, base, COLOR.a);
	ROUGHNESS = mix(roughness, lip_roughness, COLOR.r);
	SPECULAR = 0.25;
	SSS_STRENGTH = scatter * COLOR.a;
	EMISSION = base * blood_tint * warmth * COLOR.a;
	RIM = rim * COLOR.a;
	RIM_TINT = 0.7;
	thin = COLOR.b * translucency;
}

void light() {
	float around = mix(wrap, 1.0, thin);
	float lit = clamp((dot(NORMAL, LIGHT) + around) / (1.0 + around), 0.0, 1.0) * ATTENUATION;
	DIFFUSE_LIGHT += pow(vec3(lit), shadow_falloff) * LIGHT_COLOR / PI;
	float gloss = exp2(9.0 * (1.0 - ROUGHNESS) + 1.0);
	float shine = pow(max(dot(NORMAL, normalize(LIGHT + VIEW)), 0.0), gloss) * (gloss + 8.0) / 25.0;
	SPECULAR_LIGHT += shine * SPECULAR_AMOUNT * 0.2 * lit * LIGHT_COLOR / PI;
}
