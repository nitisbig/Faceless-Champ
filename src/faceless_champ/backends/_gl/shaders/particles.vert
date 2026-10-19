#version 330
in vec3 instance;
uniform vec2 target_size;
uniform mat3 transform;
uniform vec2 origin;
uniform float radius;
out vec2 point_uv;
out float alpha;
void main() {
    point_uv=vec2(gl_VertexID&1,(gl_VertexID>>1)&1)*2.0-1.0;
    vec2 local=instance.xy-origin+point_uv*(radius+1.0);
    vec3 p=transform*vec3(local,1.0);
    gl_Position=vec4(p.xy/target_size*2.0-1.0,0.0,1.0);
    alpha=instance.z;
}
