"""GPU point-cloud renderer (moderngl) for particle, smoke and light films.

Each layer's points are uploaded once. Per frame:

1. Depth prepass: occluder layers (and their water reflections) splat enlarged points into a
   depth buffer, pushed back slightly so their own points still pass the test.
2. Sharp pass (full res) and smoke pass (quarter res): every layer draws additively into float
   targets, depth-tested against the prepass, so trees and mountains truly hide what is behind.
3. Post: quarter-res downsample, separable gaussian blurs (smoke volume and bloom), god rays from
   a light through the sky mask, light glows occlusion-tested against depth, filmic tonemap and
   dither. The result is read back as uint8 RGB.

The shaders animate per-kind motion (water glitter, mist drift, rising smoke, fireflies, star
twinkle) and the mirror pass (reflections in a y = 0 water plane), so frames are pure functions
of time and render in any order.
"""

from __future__ import annotations

import moderngl
import numpy as np

POINT_VS = """
#version 330
in vec3 in_pos;
in vec3 in_base;
in float in_moon;
in float in_size;

uniform vec3 cam_pos, cam_right, cam_up, cam_fwd;
uniform float focal;
uniform vec2 res;
uniform float t;
uniform int kind;
uniform float mirror;
uniform float fog;
uniform float gain;
uniform float moon_k;
uniform vec3 moon_col, moon_dir;
uniform float depth_pass;
uniform float occ_size;
uniform vec3 lamp0, lamp1, lamp_col;

out vec3 v_col;
out float v_round;

float hash(float n) { return fract(sin(n) * 43758.5453123); }

float log_depth(float z) { return clamp(log(max(z, 0.1) / 0.1) / log(40000.0), 0.0, 1.0) * 2.0 - 1.0; }

void cull() { gl_Position = vec4(3.0, 3.0, 3.0, 1.0); gl_PointSize = 1.0; v_col = vec3(0.0); v_round = 0.0; }

void main() {
    vec3 p = in_pos;
    float id = float(gl_VertexID);
    float h1 = hash(id * 0.1234 + 1.7), h2 = hash(id * 0.3171 + 7.3), h3 = hash(id * 0.7193 + 3.1);
    vec3 col = in_base + moon_col * (in_moon * moon_k);

    if (kind == 2) {            // drifting mist and cloud
        p.x += t * 0.45 + sin(t * 0.21 + p.z * 0.05 + h1 * 6.28) * 0.5;
        p.y += sin(t * 0.17 + p.x * 0.04) * 0.25;
    } else if (kind == 3) {     // rising chimney smoke, looped
        float life = fract(t * 0.07 + h1);
        p += vec3(life * 7.0 + sin(life * 5.0 + h2 * 6.28) * life * 2.0, life * 16.0, cos(life * 4.0 + h3 * 6.28) * life * 2.0);
        col *= (1.0 - life) * smoothstep(0.0, 0.08, life) * 3.0;
    } else if (kind == 4) {     // fireflies: wander and blink
        p += vec3(sin(t * 0.5 + h1 * 6.28), 0.6 * sin(t * 0.37 + h2 * 6.28), cos(t * 0.43 + h3 * 6.28)) * 0.9;
        col *= pow(0.5 + 0.5 * sin(t * (1.2 + h2 * 2.0) + h1 * 6.28), 4.0);
    } else if (kind == 5) {     // stars twinkle
        col *= 0.7 + 0.3 * sin(t * (1.5 + h1 * 4.0) + h2 * 6.28);
    }

    if (mirror > 0.5) {
        if (p.y < 0.0) { cull(); return; }
        float rip = sin(p.z * 0.9 + t * 1.4) * 0.5 + sin(p.z * 2.3 - t * 2.1 + p.x * 0.3) * 0.25;
        p.x += rip * (0.04 + p.y * 0.01);
        p.y = -p.y * (1.0 + 0.004 * sin(p.x * 0.7 + t));
        col *= 0.3;
    }

    vec3 d = p - cam_pos;
    float z = dot(d, cam_fwd);
    if (z < 0.12) { cull(); return; }
    float sx = focal * dot(d, cam_right) / z;
    float sy = focal * dot(d, cam_up) / z;
    float zd = depth_pass > 0.5 ? z * 1.025 + 0.4 : z;
    gl_Position = vec4(sx / (res.x * 0.5), sy / (res.y * 0.5), log_depth(zd), 1.0);

    float fade = pow(clamp((z - 0.12) / 1.2, 0.0, 1.0), 2.0) * exp(-z / fog);
    vec3 view = normalize(d);
    if (kind == 1) {            // water: glitter from wave normals toward the moon and lanterns
        vec3 n = normalize(vec3(
            0.11 * (sin(p.x * 1.7 + t * 1.1 + h1 * 6.28) + sin(p.z * 0.9 - t * 0.8) + 0.6 * sin(p.z * 3.1 + t * 2.3 + h2 * 6.28)),
            1.0,
            0.11 * (cos(p.z * 1.3 + t * 1.3 + h2 * 6.28) + sin(p.x * 0.6 + p.z * 0.4 + t * 0.6) + 0.6 * cos(p.x * 2.7 - t * 1.9))));
        vec3 r = reflect(view, n);
        float spec = pow(max(dot(r, moon_dir), 0.0), 90.0) * 22.0 * moon_k;
        float lamp = 0.0;
        vec3 l0 = lamp0 - p, l1 = lamp1 - p;
        lamp += pow(max(dot(r, normalize(l0)), 0.0), 60.0) * 4.0 / (1.0 + dot(l0, l0) * 0.02);
        lamp += pow(max(dot(r, normalize(l1)), 0.0), 60.0) * 4.0 / (1.0 + dot(l1, l1) * 0.02);
        // far water packs many points into each pixel at grazing angles: thin the glitter with distance
        spec *= 1.0 / (1.0 + z * z / 1600.0);
        col += moon_col * spec + lamp_col * lamp;
    } else if (kind == 2) {     // forward scattering: mist glows when looking toward the moon
        col *= 1.0 + 1.5 * pow(max(dot(view, moon_dir), 0.0), 30.0) * moon_k;
    }
    v_col = col * fade * gain;

    float size = in_size > 0.0 ? in_size * focal / z : 0.0;
    if (depth_pass > 0.5) size = clamp(occ_size * focal / z, 1.0, 48.0);
    gl_PointSize = max(size, 1.0);
    v_round = (size > 2.0 && depth_pass < 0.5) ? 1.0 : 0.0;
}
"""

POINT_FS = """
#version 330
in vec3 v_col;
in float v_round;
out vec4 frag;
void main() {
    float a = 1.0;
    if (v_round > 0.5) {
        vec2 c = gl_PointCoord * 2.0 - 1.0;
        float r2 = dot(c, c);
        if (r2 > 1.0) discard;
        a = exp(-r2 * 2.5);
    }
    frag = vec4(v_col * a, 1.0);
}
"""

QUAD_VS = """
#version 330
in vec2 in_xy;
out vec2 uv;
void main() { uv = in_xy * 0.5 + 0.5; gl_Position = vec4(in_xy, 0.0, 1.0); }
"""

DOWN_FS = """
#version 330
uniform sampler2D src;
uniform int factor;
in vec2 uv;
out vec4 frag;
void main() {
    ivec2 base = ivec2(gl_FragCoord.xy) * factor;
    vec3 acc = vec3(0.0);
    for (int y = 0; y < factor; y++) for (int x = 0; x < factor; x++) acc += texelFetch(src, base + ivec2(x, y), 0).rgb;
    frag = vec4(acc / float(factor * factor), 1.0);
}
"""

BLUR_FS = """
#version 330
uniform sampler2D src;
uniform vec2 step_uv;
uniform float sigma;
in vec2 uv;
out vec4 frag;
void main() {
    int r = int(ceil(sigma * 2.5));
    vec3 acc = vec3(0.0);
    float wsum = 0.0;
    for (int i = -r; i <= r; i++) {
        float w = exp(-0.5 * float(i * i) / (sigma * sigma));
        acc += w * texture(src, uv + step_uv * float(i)).rgb;
        wsum += w;
    }
    frag = vec4(acc / wsum, 1.0);
}
"""

RAYS_FS = """
#version 330
uniform sampler2D soft;
uniform sampler2D depth;
uniform vec2 light_uv;
uniform vec3 light_col;
uniform float light_r;      // glow radius in uv-y units
uniform float aspect;
uniform float strength;
in vec2 uv;
out vec4 frag;
vec3 source(vec2 q) {
    float sky = step(0.9999, texture(depth, q).r);
    vec2 d = (q - light_uv) * vec2(aspect, 1.0);
    float g = exp(-dot(d, d) / (2.0 * light_r * light_r));
    return (texture(soft, q).rgb * 0.5 + light_col * g) * sky;
}
void main() {
    vec3 acc = vec3(0.0);
    float wsum = 0.0;
    const int N = 40;
    for (int k = 0; k < N; k++) {
        float s = 1.0 - 0.7 * float(k) / float(N);
        float w = pow(0.95, float(k));
        acc += source(light_uv + (uv - light_uv) * s) * w;
        wsum += w;
    }
    frag = vec4(acc / wsum * strength, 1.0);
}
"""

COMP_FS = """
#version 330
uniform sampler2D sharp;
uniform sampler2D soft;
uniform sampler2D soft_wide;
uniform sampler2D bloom_a;
uniform sampler2D bloom_b;
uniform sampler2D rays;
uniform sampler2D depth;
uniform vec4 lights[8];       // xy = uv, z = radius (uv-y), w = power
uniform vec4 light_depth[8];  // x = depth of the light for occlusion
uniform vec3 light_cols[8];
uniform int n_lights;
uniform float aspect;
uniform float k_soft, k_bloom, k_rays, exposure, flash;
uniform vec3 bg;
uniform float seed;
in vec2 uv;
out vec4 frag;
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233)) + seed) * 43758.5453); }
void main() {
    vec3 c = texture(sharp, uv).rgb;
    c += (texture(soft, uv).rgb + 0.6 * texture(soft_wide, uv).rgb) * k_soft;
    c += (texture(bloom_a, uv).rgb * 0.8 + texture(bloom_b, uv).rgb * 0.6) * k_bloom;
    c += texture(rays, uv).rgb * k_rays;
    for (int i = 0; i < n_lights; i++) {
        vec2 lu = lights[i].xy;
        float vis = 0.0;
        for (int k = 0; k < 5; k++) {
            vec2 o = vec2(float(k % 3) - 1.0, float(k / 3) - 0.5) * 0.002;
            vis += step(light_depth[i].x - 0.0005, texture(depth, lu + o).r);
        }
        vis /= 5.0;
        vec2 d = (uv - lu) * vec2(aspect, 1.0);
        float r = lights[i].z;
        float g = exp(-dot(d, d) / (2.0 * r * r)) + 0.08 * exp(-dot(d, d) / (2.0 * 25.0 * r * r));
        c += light_cols[i] * g * lights[i].w * vis;
    }
    c = 1.0 - exp(-c * exposure);
    c = bg + (1.0 - bg) * clamp(c + flash, 0.0, 1.0);
    c += (hash(gl_FragCoord.xy) - 0.5) / 255.0;
    frag = vec4(c, 1.0);
}
"""


class PointRenderer:
    """Uploads layers once; ``frame(...)`` renders one image and returns uint8 (h, w, 3)."""

    def __init__(self, layers: dict, width: int, height: int):
        self.w, self.h = width, height
        self.lw, self.lh = max(2, width // 4), max(2, height // 4)
        self.ctx = ctx = moderngl.create_standalone_context(require=330)
        self.prog = ctx.program(vertex_shader=POINT_VS, fragment_shader=POINT_FS)
        self.layers = []
        for name, L in layers.items():
            data = np.concatenate(
                [L["p"], L["base"], L["moon"][:, None], L["size"][:, None]], axis=1
            ).astype("f4")
            vbo = ctx.buffer(data.tobytes())
            vao = ctx.vertex_array(self.prog, [(vbo, "3f 3f 1f 1f", "in_pos", "in_base", "in_moon", "in_size")])
            self.layers.append((name, L, vao, len(data)))

        def target(w, h, depth=True):
            tex = ctx.texture((w, h), 4, dtype="f4")
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            tex.repeat_x = tex.repeat_y = False
            dep = ctx.depth_texture((w, h)) if depth else None
            if dep is not None:
                dep.repeat_x = dep.repeat_y = False
                dep.compare_func = ""  # sample raw depth (sky mask, light occlusion)
            return tex, dep, ctx.framebuffer([tex], dep)

        self.sharp, self.depth, self.fbo_sharp = target(width, height)
        self.smoke, self.depth_low, self.fbo_smoke = target(self.lw, self.lh)
        self.lows = {k: target(self.lw, self.lh, depth=False) for k in ("down", "tmp", "soft", "soft_wide", "bloom_a", "bloom_b", "rays")}
        self.out = ctx.texture((width, height), 4, dtype="f1")
        self.fbo_out = ctx.framebuffer([self.out])

        quad = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], "f4").tobytes())
        self.passes = {}
        for key, fs in (("down", DOWN_FS), ("blur", BLUR_FS), ("rays", RAYS_FS), ("comp", COMP_FS)):
            prog = ctx.program(vertex_shader=QUAD_VS, fragment_shader=fs)
            self.passes[key] = (prog, ctx.vertex_array(prog, [(quad, "2f", "in_xy")]))

    # ------------------------------------------------------------------ helpers
    def _set(self, prog, **values):
        for k, v in values.items():
            if k in prog:
                prog[k].value = tuple(float(x) for x in v) if isinstance(v, (tuple, list, np.ndarray)) else v

    def _quad(self, key, fbo, **uniforms):
        prog, vao = self.passes[key]
        textures = {k: v for k, v in uniforms.items() if isinstance(v, moderngl.Texture)}
        for i, (name, tex) in enumerate(textures.items()):
            tex.use(location=i)
            if name in prog:
                prog[name].value = i
        self._set(prog, **{k: v for k, v in uniforms.items() if k not in textures})
        fbo.use()
        vao.render(moderngl.TRIANGLE_STRIP)

    def _blur(self, src, dst, sigma):
        tmp_tex, _, tmp_fbo = self.lows["tmp"]
        self._quad("blur", tmp_fbo, src=src, step_uv=(1.0 / self.lw, 0.0), sigma=sigma)
        self._quad("blur", dst[2], src=tmp_tex, step_uv=(0.0, 1.0 / self.lh), sigma=sigma)

    def _points(self, fbo, size, cam, focal, uni, pass_kind):
        """pass_kind: 'depth', 'sharp' or 'smoke'."""
        ctx, prog = self.ctx, self.prog
        w, h = size
        pos, right, up, fwd = cam
        self._set(prog, cam_pos=pos, cam_right=right, cam_up=up, cam_fwd=fwd, focal=focal * w, res=(w, h), **uni)
        kres = (1280.0 / self.w) ** 2
        for name, L, vao, n in self.layers:
            if pass_kind == "depth":
                occ = float(L.get("occ", 0.0))
                if occ <= 0:
                    continue
                weight = 0.0
            else:
                weight = float(L.get(pass_kind, 0.0)) * float(L.get("gain", 1.0)) * kres
                if weight <= 0:
                    continue
                occ = 0.0
            self._set(prog, kind=int(L.get("kind", 0)), fog=float(L.get("fog", 1e9)), gain=weight,
                      depth_pass=1.0 if pass_kind == "depth" else 0.0, occ_size=occ)
            mirrors = (0.0, 1.0) if L.get("reflect") else (0.0,)
            for m in mirrors:
                prog["mirror"].value = m
                vao.render(moderngl.POINTS, vertices=n)

    def _scene_pass(self, fbo, size, cam, focal, uni, kind):
        ctx = self.ctx
        fbo.use()
        fbo.depth_mask = True  # clear() respects the mask; the previous frame left it off
        fbo.color_mask = (True, True, True, True)
        fbo.clear(0.0, 0.0, 0.0, 0.0, depth=1.0)
        ctx.enable(moderngl.DEPTH_TEST | moderngl.PROGRAM_POINT_SIZE)
        ctx.depth_func = "<"
        fbo.depth_mask = True
        fbo.color_mask = (False, False, False, False)
        ctx.disable(moderngl.BLEND)
        self._points(fbo, size, cam, focal, uni, "depth")
        fbo.color_mask = (True, True, True, True)
        fbo.depth_mask = False
        ctx.depth_func = "<="
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.ONE, moderngl.ONE)
        self._points(fbo, size, cam, focal, uni, kind)
        ctx.disable(moderngl.DEPTH_TEST | moderngl.BLEND)

    # ------------------------------------------------------------------ frame
    def frame(self, cam, focal, t, uni, lights, rays_light, *, k_soft, k_bloom, k_rays, exposure, flash, bg):
        """cam = (pos, right, up, fwd); lights = [(world_pos, colour, radius_m, power)];
        rays_light = (world_pos, colour, glow radius in uv-y, strength) or None."""
        uni = dict(uni, t=t)
        self._scene_pass(self.fbo_sharp, (self.w, self.h), cam, focal, uni, "sharp")
        self._scene_pass(self.fbo_smoke, (self.lw, self.lh), cam, focal, uni, "smoke")

        down = self.lows["down"]
        self._quad("down", down[2], src=self.sharp, factor=self.w // self.lw)
        self._blur(self.smoke, self.lows["soft"], 1.3 * self.lw / 320)
        self._blur(self.lows["soft"][0], self.lows["soft_wide"], 4.0 * self.lw / 320)

        self._blur(down[0], self.lows["bloom_a"], 2.0 * self.lw / 320)
        self._blur(down[0], self.lows["bloom_b"], 10.0 * self.lw / 320)

        pos, right, up, fwd = cam
        aspect = self.w / self.h

        def to_uv(p):
            d = np.asarray(p, float) - pos
            z = float(d @ fwd)
            if z <= 0.2:
                return None
            f = focal * self.w
            return (0.5 + f * float(d @ right) / z / self.w, 0.5 + f * float(d @ up) / z / self.h, z)

        rays_tex = self.lows["rays"]
        rays_tex[2].clear(0, 0, 0, 0)
        if rays_light is not None:
            lp, lcol, lr, strength = rays_light
            q = to_uv(lp)
            if q is not None:
                self._quad("rays", rays_tex[2], soft=self.lows["soft"][0], depth=self.depth, light_uv=q[:2],
                           light_col=lcol, light_r=lr, aspect=aspect, strength=strength)

        packed, pdepth, pcols = [], [], []
        for lp, lcol, radius_m, power in lights[:8]:
            q = to_uv(lp)
            if q is None or not (-0.3 < q[0] < 1.3 and -0.3 < q[1] < 1.3):
                continue
            r_uv = min(0.25, max(0.0015, radius_m * focal * self.w / q[2] / self.h))
            dl = np.clip(np.log(max(q[2], 0.1) / 0.1) / np.log(40000.0), 0, 1)
            packed.append((q[0], q[1], r_uv, power))
            pdepth.append((dl, 0, 0, 0))
            pcols.append(tuple(lcol))
        n = len(packed)
        packed += [(0, 0, 0.01, 0)] * (8 - n)
        pdepth += [(1, 0, 0, 0)] * (8 - n)
        pcols += [(0, 0, 0)] * (8 - n)
        prog = self.passes["comp"][0]
        prog["lights"].write(np.array(packed, "f4").tobytes())
        prog["light_depth"].write(np.array(pdepth, "f4").tobytes())
        prog["light_cols"].write(np.array(pcols, "f4").tobytes())
        self._quad("comp", self.fbo_out, sharp=self.sharp, soft=self.lows["soft"][0], soft_wide=self.lows["soft_wide"][0], bloom_a=self.lows["bloom_a"][0],
                   bloom_b=self.lows["bloom_b"][0], rays=rays_tex[0], depth=self.depth, n_lights=n, aspect=aspect,
                   k_soft=k_soft, k_bloom=k_bloom, k_rays=k_rays, exposure=exposure, flash=flash, bg=bg,
                   seed=float(t * 37.0 % 100.0))
        img = np.frombuffer(self.fbo_out.read(components=3, dtype="f1"), np.uint8).reshape(self.h, self.w, 3)
        return img[::-1]
