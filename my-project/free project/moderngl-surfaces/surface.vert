#version 330
in vec2 in_uv;
uniform float time;
uniform mat4 mvp;
out vec2 uv;
out vec3 normal;
out vec3 world;

vec3 surface(vec2 q) {
    const float PI = 3.14159265359;
    vec2 p = (q * 2.0 - 1.0) * PI;
    float r = length(p);
    float wave = 0.38 * sin(2.4 * r - time * 1.6) * exp(-0.09 * r * r);
    wave += 0.13 * sin(p.x * 2.0 + time) * cos(p.y * 1.8 - time * 0.7);
    float saddle = 0.17 * (p.x * p.x - p.y * p.y);
    float saddleMix = smoothstep(3.0, 6.0, time);
    vec3 sheet = vec3(p.x * 0.88, mix(wave, saddle + wave * 0.45, saddleMix), p.y * 0.88);
    float a = q.x * 2.0 * PI;
    float b = q.y * 2.0 * PI;
    float minorR = 0.72 + 0.10 * sin(3.0 * a - time * 1.5) + 0.07 * cos(3.0 * b + time);
    float majorR = 1.83 + 0.10 * sin(2.0 * a + time * 0.6);
    vec3 torus = vec3((majorR + minorR * cos(b)) * cos(a), minorR * sin(b),
                      (majorR + minorR * cos(b)) * sin(a));
    return mix(sheet, torus, smoothstep(7.0, 11.0, time));
}

void main() {
    uv = in_uv;
    world = surface(uv);
    float e = 0.00015;
    vec3 du = surface(uv + vec2(e, 0.0)) - surface(uv - vec2(e, 0.0));
    vec3 dv = surface(uv + vec2(0.0, e)) - surface(uv - vec2(0.0, e));
    normal = normalize(cross(du, dv));
    gl_Position = mvp * vec4(world, 1.0);
}
