#version 330
in vec2 uv;
in float elevation;
uniform float time;
out vec4 frag;
void main() {
    vec2 g = uv*50.0;
    vec2 dist = abs(fract(g-0.5)-0.5)/max(fwidth(g),vec2(0.0001));
    float d = min(dist.x,dist.y);
    float line = 1.0-smoothstep(0.2,1.05,d);
    vec3 color = mix(vec3(0.025,0.55,0.9), vec3(1.0,0.15,0.48),smoothstep(-0.1,0.65,elevation));
    float reveal = smoothstep(5.1,7.7,time) * (1.0-smoothstep(13.5,15.0,time));
    float edge = smoothstep(0.0,0.035,min(min(uv.x,uv.y),min(1.0-uv.x,1.0-uv.y)));
    frag = vec4(color*(0.045+line*0.85+0.08*exp(-d*d*0.2))*reveal*edge,1.0);
}
