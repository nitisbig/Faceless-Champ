#version 330
in vec2 grid;
in vec3 world;
uniform vec3 color;
uniform float opacity;
uniform float time;
uniform float reveal;
uniform float scan_y;
uniform int wire_mode;
out vec4 frag;
void main() {
    if (world.y > reveal) discard;
    vec2 d = abs(fract(grid - 0.5) - 0.5) / max(fwidth(grid), vec2(0.0001));
    float edge = 1.0 - smoothstep(0.25, 1.15, min(d.x, d.y));
    float ink = wire_mode == 0 ? 1.0 : 0.025 + 0.975 * edge;
    float scan = exp(-pow((world.y - scan_y) / 0.12, 2.0));
    float reveal_edge = exp(-pow((world.y - reveal) / 0.065, 2.0));
    float depth = 0.7 + 0.3 * clamp((world.z + 2.0) / 4.0, 0.0, 1.0);
    float modulation = 0.97 + 0.03 * sin(world.y * 100.0 + time * 2.0);
    vec3 light = color + vec3(0.16, 0.22, 0.17) * scan;
    frag = vec4(light, opacity * ink * depth * modulation * (1.0 + scan + reveal_edge));
}
