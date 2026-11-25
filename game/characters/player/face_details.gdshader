shader_type spatial;
render_mode cull_disabled;
// Lashes and brows. Vertex color: RGB is the color, A how much of it the hair color tints.

instance uniform vec3 hair_color : source_color, instance_index(1) = vec3(0.93, 0.62, 0.7);

void fragment() {
	ALBEDO = mix(COLOR.rgb, COLOR.rgb * hair_color * 1.6, COLOR.a);
	ROUGHNESS = 0.7;
	SPECULAR = 0.2;
}
