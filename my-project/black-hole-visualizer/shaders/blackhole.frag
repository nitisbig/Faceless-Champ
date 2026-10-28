#version 330 core
// Schwarzschild null-geodesic tracer. Units G = c = M = 1 (horizon at r = 2).
// Each pixel integrates  x'' = -3 h^2 x / r^5  (exact Binet orbit u'' + u = 3u^2)
// with velocity-Verlet, collecting thin-disk emission at every equatorial crossing.

in vec2 v_uv;
out vec4 frag;

uniform vec2 resolution;
uniform vec3 cam_pos;
uniform mat3 cam_basis;      // columns: right, up, forward
uniform float tan_half_fov;
uniform vec2 lens_shift;     // off-axis projection in NDC units
uniform float sim_time;      // disk clock, units of M
uniform float exposure;
uniform float disk_in;
uniform float disk_out;
uniform float t4_peak;       // r^-3 (1 - sqrt(r_isco/r)) at its maximum
uniform float t_peak_kelvin;
uniform vec2 lut_range;      // log(T_min), log(T_max)
uniform int samples;         // supersampling grid per axis
uniform sampler2D blackbody;

const int MAX_STEPS = 320;
const int MAX_CROSSINGS = 4;
const float R_HORIZON = 2.0;
const float R_ESCAPE = 90.0;

// ---------------------------------------------------------------- noise
float hash13(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.zyx + 31.32);
    return fract((p.x + p.y) * p.z);
}

vec3 hash33(vec3 p) {
    p = fract(p * vec3(0.1031, 0.1030, 0.0973));
    p += dot(p, p.yxz + 33.33);
    return fract((p.xxy + p.yxx) * p.zyx);
}

float vnoise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(hash13(i), hash13(i + vec3(1, 0, 0)), u.x),
                   mix(hash13(i + vec3(0, 1, 0)), hash13(i + vec3(1, 1, 0)), u.x), u.y),
               mix(mix(hash13(i + vec3(0, 0, 1)), hash13(i + vec3(1, 0, 1)), u.x),
                   mix(hash13(i + vec3(0, 1, 1)), hash13(i + vec3(1, 1, 1)), u.x), u.y), u.z);
}

float fbm(vec3 p) {
    float sum = 0.0, amp = 0.5;
    for (int i = 0; i < 5; ++i) {
        sum += amp * vnoise(p);
        p = p * 2.03 + vec3(1.7, 9.2, 3.1);
        amp *= 0.5;
    }
    return sum;
}

// ---------------------------------------------------------------- physics
vec3 blackbody_rgb(float kelvin) {
    float s = clamp((log(kelvin) - lut_range.x) / (lut_range.y - lut_range.x), 0.0, 1.0);
    return texture(blackbody, vec2(s, 0.5)).rgb;
}

// Emission and opacity of the disk where the ray crosses z = 0.
vec4 disk_sample(vec3 p, float lam_z) {
    float r = length(p.xy);
    if (r < disk_in * 0.92 || r > disk_out) return vec4(0.0);

    float omega = pow(r, -1.5);                                  // Keplerian Ω
    float g = sqrt(max(1.0 - 3.0 / r, 1e-4)) / (1.0 - omega * lam_z);
    float t4 = max(pow(r, -3.0) * (1.0 - sqrt(disk_in / max(r, disk_in))), 0.0) / t4_peak;
    float t_rel = pow(t4, 0.25);

    // Differentially rotating turbulence: sheared along φ, banded in log r.
    float phi = atan(p.y, p.x) - omega * sim_time;
    vec2 ring = vec2(cos(phi), sin(phi));
    float lr = log(r);
    float bands = fbm(vec3(ring * 1.4, lr * 11.0));
    float fine = fbm(vec3(ring * 7.0, lr * 38.0 + 4.0));
    float density = smoothstep(0.3, 0.72, bands) * (0.35 + 1.1 * fine * fine * 1.6);
    density *= smoothstep(disk_in * 0.92, disk_in * 1.08, r) * (1.0 - smoothstep(disk_out * 0.55, disk_out, r));

    float kelvin = max(g * t_rel * t_peak_kelvin, 800.0);
    float flux = pow(g, 4.0) * t4;                                // bolometric I ∝ g^4 T^4
    vec3 emission = blackbody_rgb(kelvin) * flux * (0.35 + 1.6 * density);
    float alpha = clamp(0.25 + 0.85 * density, 0.0, 0.97);
    return vec4(emission, alpha);
}

vec3 sky(vec3 d, float px) {
    vec3 col = vec3(0.0);
    // Two hashed star layers on the celestial sphere; width tracks pixel size.
    for (int layer = 0; layer < 2; ++layer) {
        float scale = layer == 0 ? 90.0 : 240.0;
        vec3 p = d * scale;
        vec3 cell = floor(p);
        vec3 h = hash33(cell);
        float present = step(layer == 0 ? 0.93 : 0.82, hash13(cell + 17.0));
        vec3 star = cell + 0.25 + 0.5 * h;
        float dist = length(p - star);
        float width = max(px * scale * 0.9, 0.035);
        float mag = layer == 0 ? 1.4 : 0.4;
        float temp = mix(3200.0, 14000.0, pow(hash13(cell + 3.0), 1.6));
        col += present * mag * exp(-dist * dist / (width * width)) * blackbody_rgb(temp) * (0.3 + h.x);
    }
    // Faint dust band and nebulosity.
    float band = exp(-pow(dot(d, normalize(vec3(0.25, 0.9, 0.35))) * 3.2, 2.0));
    float neb = fbm(d * 3.5 + 11.0);
    col += band * (0.012 + 0.03 * neb * neb) * vec3(0.55, 0.62, 1.0);
    col += 0.010 * pow(fbm(d * 2.0 - 5.0), 3.0) * vec3(0.9, 0.5, 1.0);
    return col;
}

vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

// Filmic curve on luminance keeps blackbody hue; ACES is mixed in so hot cores still roll to white.
vec3 tonemap(vec3 x) {
    float lum = dot(x, vec3(0.2126, 0.7152, 0.0722));
    float mapped = lum * (1.0 + lum / 9.0) / (1.0 + lum);
    vec3 hue = x * (mapped / max(lum, 1e-5));
    vec3 film = mix(hue, aces(x), clamp(lum * 0.35, 0.0, 0.6));
    return clamp(film, 0.0, 1.0);
}

vec3 trace(vec2 ndc, float px) {
    vec3 dir = normalize(cam_basis * vec3((ndc + lens_shift) * vec2(resolution.x / resolution.y, 1.0) * tan_half_fov, 1.0));
    vec3 x = cam_pos;
    vec3 v = dir;
    vec3 L = cross(x, v);
    float h2 = dot(L, L);
    float lam_z = -L.z;                                           // photon momentum is -v

    vec3 col = vec3(0.0);
    float trans = 1.0;
    int crossings = 0;
    bool captured = false;

    for (int i = 0; i < MAX_STEPS; ++i) {
        float r = length(x);
        if (r < R_HORIZON * 1.002) { captured = true; break; }
        if (r > R_ESCAPE && dot(x, v) > 0.0) break;

        float dl = clamp(0.065 * (r - 1.5), 0.02, 3.5);
        vec3 a = -3.0 * h2 * x / pow(r, 5.0);
        vec3 vh = v + 0.5 * dl * a;
        vec3 xn = x + dl * vh;
        float rn = length(xn);
        v = vh + 0.5 * dl * (-3.0 * h2 * xn / pow(rn, 5.0));

        if (x.z * xn.z < 0.0 && crossings < MAX_CROSSINGS) {
            vec3 p = mix(x, xn, x.z / (x.z - xn.z));
            vec4 s = disk_sample(p, lam_z);
            col += trans * s.a * s.rgb;
            trans *= 1.0 - s.a;
            crossings++;
            if (trans < 0.01) break;
        }
        x = xn;
    }
    if (!captured && trans > 0.01) col += trans * sky(normalize(v), px);
    return col;
}

void main() {
    vec2 frag_px = v_uv * resolution;
    float px = 2.0 * tan_half_fov / resolution.y;                 // angular size of a pixel
    vec3 col = vec3(0.0);
    for (int sy = 0; sy < samples; ++sy) {
        for (int sx = 0; sx < samples; ++sx) {
            vec2 offset = (vec2(sx, sy) + 0.5) / float(samples) - 0.5;
            vec2 ndc = ((frag_px + offset) / resolution) * 2.0 - 1.0;
            col += trace(ndc, px);
        }
    }
    col /= float(samples * samples);
    col = tonemap(col * exposure);
    col = pow(col, vec3(1.0 / 2.2));
    col += (hash13(vec3(frag_px, sim_time)) - 0.5) / 255.0;       // dither against banding
    frag = vec4(col, 1.0);
}
