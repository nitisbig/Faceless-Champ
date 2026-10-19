#version 330
in vec2 origin;
in vec3 seed;
uniform float time;
uniform float height;
uniform mat4 mvp;
out float alpha;
out vec3 color;
void main() {
    float p = smoothstep(3.0 + seed.z * 0.65, 7.1, time);
    vec2 q = (seed.xy * 2.0 - 1.0) * 3.14159265;
    float h = 0.65 * sin(2.0*q.x-time*1.8) * cos(2.0*q.y-time*1.1);
    vec4 target = mvp * vec4(q.x, h, q.y, 1.0);
    vec2 projected = target.xy / target.w;
    float burst = sin(p * 3.14159265);
    vec2 curl = vec2(sin(seed.z*24.0 + time*1.3), cos(seed.x*19.0-time)) * 0.32;
    vec2 pos = mix(origin, projected, p) + burst * curl;
    gl_Position = vec4(pos, 0.0, 1.0);
    gl_PointSize = (1.8 + burst * (1.0+seed.z*2.0)) * height/1080.0;
    alpha = smoothstep(0.2, 1.3, time) * (1.0-smoothstep(6.4, 8.0, time));
    color = mix(vec3(0.66,0.91,1.0), mix(vec3(0.07,0.72,1.0),vec3(1.0,0.16,0.54),seed.z),burst);
}
