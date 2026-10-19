#version 330
uniform float time;
uniform vec2 resolution;
out vec4 fragColor;

mat2 rotate(float a) { float c=cos(a), s=sin(a); return mat2(c,-s,s,c); }
float smin(float a, float b, float k) {
    float h=clamp(0.5+0.5*(b-a)/k,0.0,1.0);
    return mix(b,a,h)-k*h*(1.0-h);
}
float roundedBox(vec3 p, vec3 b, float r) {
    vec3 q=abs(p)-b;
    return length(max(q,0.0))+min(max(q.x,max(q.y,q.z)),0.0)-r;
}
float torus(vec3 p) { return length(vec2(length(p.xz)-1.06,p.y))-0.40; }
vec3 localPoint(vec3 p) {
    p.xz=rotate(0.28*time-0.4)*p.xz;
    p.xy=rotate(0.24*sin(time*0.37))*p.xy;
    return p;
}
float field(vec3 p) {
    p=localPoint(p);
    float sphere=length(p)-1.22;
    float orbit=1.70*(1.0-smoothstep(0.7,3.2,time));
    float blobs=length(p)-1.00;
    for(int i=0;i<3;i++) {
        float a=float(i)*2.0944+time*0.35;
        vec3 center=vec3(cos(a)*orbit,0.38*sin(a+time*0.5),sin(a)*orbit);
        blobs=smin(blobs,length(p-center)-0.55,0.52);
    }
    float box=roundedBox(p,vec3(0.86),0.24);
    float ring=torus(p);
    float drilled=roundedBox(p,vec3(0.94),0.22);
    float holes=min(length(p.xy),min(length(p.yz),length(p.xz)))-0.57;
    // Rounded subtraction creates smooth lips at all three intersecting tunnels.
    drilled=-smin(-drilled,holes,0.14);
    float d=mix(blobs,sphere,smoothstep(2.6,3.5,time));
    d=mix(d,box,smoothstep(3.6,5.7,time));
    d=mix(d,ring,smoothstep(6.1,8.2,time));
    d=mix(d,drilled,smoothstep(9.0,11.7,time));
    // A restrained breathing/twist finish preserves the sculptural silhouette.
    float wave=0.025*sin(7.0*p.x+time)*sin(7.0*p.y-time)*sin(7.0*p.z);
    return d+wave*smoothstep(12.0,14.0,time);
}
vec3 normalAt(vec3 p) {
    vec2 e=vec2(0.0012,0);
    return normalize(vec3(field(p+e.xyy)-field(p-e.xyy),
        field(p+e.yxy)-field(p-e.yxy),field(p+e.yyx)-field(p-e.yyx)));
}
float ambientOcclusion(vec3 p, vec3 n) {
    float occ=0.0, weight=1.0;
    for(int i=1;i<=4;i++) {
        float h=0.075*float(i);
        occ+=(h-field(p+n*h))*weight;
        weight*=0.55;
    }
    return clamp(1.0-2.3*occ,0.22,1.0);
}
float shadow(vec3 p, vec3 l) {
    float shade=1.0, travel=0.035;
    for(int i=0;i<28;i++) {
        float h=field(p+l*travel);
        shade=min(shade,12.0*max(h,0.0)/travel);
        travel+=clamp(h,0.025,0.24);
        if(h<0.0008 || travel>4.0) break;
    }
    return clamp(shade,0.12,1.0);
}
vec3 light(vec3 n, vec3 v, vec3 l, vec3 color, vec3 base, float rough) {
    float nl=max(dot(n,l),0.0);
    vec3 h=normalize(l+v);
    float nh=max(dot(n,h),0.0), vh=max(dot(v,h),0.0);
    float a=rough*rough, a2=a*a;
    float denom=nh*nh*(a2-1.0)+1.0;
    float distribution=a2/(3.14159*denom*denom+0.0001);
    float k=(rough+1.0)*(rough+1.0)/8.0;
    float nv=max(dot(n,v),0.001);
    float geometry=(nl/(nl*(1.0-k)+k))*(nv/(nv*(1.0-k)+k));
    vec3 fresnel=mix(vec3(0.12),base,0.72);
    fresnel+= (1.0-fresnel)*pow(1.0-vh,5.0);
    vec3 spec=distribution*geometry*fresnel/max(4.0*nl*nv,0.001);
    return (base*0.23/3.14159+spec)*color*nl;
}
void main() {
    vec2 uv=(2.0*gl_FragCoord.xy-resolution)/resolution.y;
    vec3 eye=vec3(0.0,1.35,6.7);
    vec3 forward=normalize(-eye);
    vec3 right=normalize(cross(forward,vec3(0,1,0)));
    vec3 up=cross(right,forward);
    vec3 ray=normalize(forward*2.0+uv.x*right+uv.y*up);
    // Analytic bounding sphere keeps the background exactly black and skips empty rays.
    float b=dot(eye,ray), c=dot(eye,eye)-7.84;
    float discriminant=b*b-c;
    if(discriminant<0.0) { fragColor=vec4(0,0,0,1); return; }
    float distance=max(0.0,-b-sqrt(discriminant));
    float end=-b+sqrt(discriminant);
    bool hit=false;
    for(int i=0;i<160;i++) {
        float d=field(eye+ray*distance);
        if(d<0.0009) {hit=true;break;}
        distance+=max(d*0.65,0.0005);
        if(distance>end) break;
    }
    if(!hit) {fragColor=vec4(0,0,0,1);return;}
    vec3 p=eye+ray*distance, n=normalAt(p), v=-ray;
    vec3 q=localPoint(p);
    float tint=0.5+0.5*sin(q.y*1.5+q.x*0.65+time*0.22);
    vec3 base=mix(vec3(0.13,0.40,0.52),vec3(0.72,0.37,0.13),tint);
    vec3 key=normalize(vec3(-3,5,4));
    float ao=ambientOcclusion(p,n);
    vec3 color=base*0.065*ao;
    color+=light(n,v,key,vec3(7.0,5.9,4.7),base,0.29)*shadow(p+n*0.007,key);
    color+=light(n,v,normalize(vec3(4,1,2)),vec3(0.7,2.9,4.8),base,0.34)*ao;
    color+=light(n,v,normalize(vec3(-1,2,-4)),vec3(3.6,1.3,5.4),base,0.25)*ao;
    float rim=pow(1.0-max(dot(n,v),0.0),3.0);
    color+=vec3(0.08,0.28,0.36)*rim*ao;
    color=color/(1.0+color);
    color=pow(color,vec3(1.0/2.2));
    fragColor=vec4(color,1.0);
}
