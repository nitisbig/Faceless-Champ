#version 330
in vec2 uv;
in vec3 normal;
in vec3 world;
uniform float time;
uniform vec3 eye;
out vec4 frag;

void main() {
    // Derivative-filtered parameter lines stay fine as the camera rotates.
    vec2 grid = uv * vec2(64.0, 48.0);
    vec2 distanceToLine = abs(fract(grid - 0.5) - 0.5) / max(fwidth(grid), vec2(0.0001));
    float d = min(distanceToLine.x, distanceToLine.y);
    float line = 1.0 - smoothstep(0.25, 1.05, d);
    float halo = exp(-d * d * 0.16) * 0.12;
    vec3 n = normalize(normal);
    vec3 view = normalize(eye - world);
    float facing = abs(dot(n, view));
    float rim = pow(1.0 - facing, 2.5);
    float light = 0.25 + 0.75 * abs(dot(n, normalize(vec3(-0.5, 1.0, 0.7))));
    float phase = uv.x * 0.7 + uv.y * 0.3 + world.y * 0.16 - time * 0.035;
    vec3 color = 0.5 + 0.5 * cos(6.2831853 * (phase + vec3(0.02, 0.35, 0.65)));
    color = mix(vec3(0.04, 0.65, 1.0), color, 0.85);
    // A moving latitude carries a brighter pulse across the mesh.
    float scan = exp(-pow((uv.y - fract(time * 0.11)) / 0.028, 2.0));
    vec3 fill = color * (0.045 + light * 0.12 + rim * 0.12);
    vec3 mesh = mix(color, vec3(0.70, 0.96, 1.0), 0.25 + scan * 0.4);
    vec3 radiance = fill + mesh * (line * (0.55 + scan * 0.4) + halo);
    radiance += color * rim * 0.16;
    float envelope = smoothstep(0.0, 0.9, time) * (1.0 - smoothstep(13.7, 15.0, time));
    frag = vec4(radiance * envelope, 1.0);
}
