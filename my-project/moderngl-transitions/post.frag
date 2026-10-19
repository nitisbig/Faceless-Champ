#version 330
in vec2 uv;
uniform sampler2D source;
uniform float time;
uniform vec2 resolution;
out vec4 frag;
float hash(float n) { return fract(sin(n*127.1)*43758.5453); }
vec3 sampleBlack(vec2 q) {
    if(any(lessThan(q,vec2(0.0))) || any(greaterThan(q,vec2(1.0)))) return vec3(0.0);
    return texture(source,q).rgb;
}
void main() {
    float envelope = smoothstep(2.8,4.4,time)*(1.0-smoothstep(6.2,7.6,time));
    float beat = exp(-pow((time-4.1)/0.12,2.0)) + exp(-pow((time-5.7)/0.15,2.0));
    vec2 center = uv-0.5;
    float radius = length(center);
    vec2 q = uv + center*sin(radius*34.0-time*7.0)*envelope*0.018;
    float band = floor(uv.y*50.0);
    float jump = (hash(band+floor(time*18.0))-0.5)*step(0.77,hash(band+9.0));
    q.x += jump*beat*0.13;
    vec2 split = vec2((0.004*envelope+0.014*beat),0.001*envelope);
    // Radial multi-tap blur, each channel displaced independently.
    vec3 rgb = vec3(0.0);
    for(int i=0;i<7;i++) {
        vec2 tap = q + center*(float(i)-3.0)*0.007*envelope;
        rgb += vec3(sampleBlack(tap+split).r,sampleBlack(tap).g,sampleBlack(tap-split).b)/7.0;
    }
    // Restrict fine scanline modulation to the transition itself.
    rgb *= 1.0-0.12*beat*(0.5+0.5*sin(uv.y*resolution.y*3.14159));
    frag = vec4(rgb,1.0);
}
