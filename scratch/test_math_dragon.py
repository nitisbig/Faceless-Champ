import os
os.environ["MPLCONFIGDIR"] = "/tmp/mpl"
import numpy as np
import pyvista as pv
from matplotlib.colors import LinearSegmentedColormap

DRAGON_CMAP = LinearSegmentedColormap.from_list(
    "obsidian_math",
    ["#06080e", "#0f1624", "#1c110e", "#551500", "#9c2d00", "#ff6a00", "#ffbb22", "#ffffff"]
)

FIRE_CMAP = LinearSegmentedColormap.from_list(
    "fire_math",
    ["#150100", "#4a0600", "#9c1400", "#ff4000", "#ff9400", "#ffea55", "#ffffff"]
)

def build_mathematical_dragon(t: float, jaw_open: float = 0.0, heat_intensity: float = 0.0):
    meshes = []
    
    # Flight kinematics
    omega = 4.2
    flap = 0.65 * np.sin(omega * t)
    pitch = 0.22 * np.cos(omega * t)
    elbow_flex = 0.35 * (1.0 - np.sin(omega * t - 0.5))
    
    # 1. Articulated Spine & Vertebrae (20 segments)
    n_seg = 20
    s_vals = np.linspace(0, 1, n_seg)
    lat_wave = 0.08 * (s_vals**1.2) * np.sin(omega * t * 0.7 - s_vals * 4.5)
    vert_wave = 0.035 * (s_vals**1.0) * np.cos(omega * t * 0.7 - s_vals * 4.5)
    
    body_points = []
    for i, s in enumerate(s_vals):
        x = s * 1.5 - 0.5
        y = lat_wave[i]
        z = vert_wave[i]
        body_points.append(np.array([x, y, z]))
        
        # Radius profile
        if s < 0.20:
            r = 0.045 + 0.045 * (s / 0.20)
        elif s < 0.45:
            r = 0.090 - 0.025 * ((s - 0.20) / 0.25)
        else:
            r = 0.065 * (1.0 - (s - 0.45) / 0.55)**1.15 + 0.008
            
        vert = pv.ParametricEllipsoid(r * 0.95, r * 0.85, r * 1.1)
        vert = vert.translate([x, y, z], inplace=False)
        # Heat field along spine
        h_local = heat_intensity * np.exp(-((s - 0.15) / 0.18)**2)
        vert["heat"] = np.full(vert.n_points, h_local)
        meshes.append(vert)
        
        # Dorsal spines
        if 2 <= i <= 17:
            h = r * 1.5
            cone = pv.Cone(center=[x, y, z + r + h*0.35], direction=[0.15, 0, 1], height=h, radius=r*0.25)
            cone["heat"] = np.full(cone.n_points, h_local * 0.6)
            meshes.append(cone)

    # 2. Head & Articulated Jaws at s=0
    head_pos = body_points[0]
    cranium = pv.Cone(center=[head_pos[0] - 0.09, head_pos[1], head_pos[2] + 0.02], direction=[-1, 0, 0], height=0.19, radius=0.062)
    cranium["heat"] = np.full(cranium.n_points, heat_intensity * 0.85)
    meshes.append(cranium)
    
    # Lower Jaw (hinges down when roaring!)
    jaw_angle = jaw_open * 0.48
    jaw_center = [head_pos[0] - 0.08, head_pos[1], head_pos[2] - 0.025 - 0.045 * jaw_open]
    jaw = pv.Cone(center=jaw_center, direction=[-1, 0, -np.sin(jaw_angle)], height=0.16, radius=0.048)
    jaw["heat"] = np.full(jaw.n_points, heat_intensity * 0.95)
    meshes.append(jaw)
    
    mouth_pos = np.array([head_pos[0] - 0.17, head_pos[1], head_pos[2] - 0.015 - 0.03 * jaw_open])
    
    # Spiral Horns
    for side in (-1, 1):
        horn = pv.Cone(center=[head_pos[0] + 0.02, head_pos[1] + side * 0.04, head_pos[2] + 0.07], direction=[0.6, side * 0.4, 0.8], height=0.15, radius=0.022)
        horn["heat"] = np.full(horn.n_points, 0.1)
        meshes.append(horn)

    # Glowing eyes
    for side in (-1, 1):
        eye = pv.Sphere(radius=0.013, center=[head_pos[0] - 0.045, head_pos[1] + side * 0.038, head_pos[2] + 0.038])
        eye["heat"] = np.full(eye.n_points, 1.0)
        meshes.append(eye)

    # 3. Articulated Wings (attached at thorax s ~ 0.3)
    thorax_idx = 6
    shoulder_base = body_points[thorax_idx]
    
    for side in (-1, 1):
        sh_pos = np.array([shoulder_base[0] - 0.02, shoulder_base[1] + side * 0.075, shoulder_base[2] + 0.04])
        arm_len = 0.30
        el_pos = sh_pos + np.array([
            0.05 + 0.04 * np.sin(pitch),
            side * arm_len * np.cos(flap),
            arm_len * np.sin(flap)
        ])
        fore_len = 0.42
        fore_flap = flap + 0.28 * elbow_flex
        wr_pos = el_pos + np.array([
            -0.08,
            side * fore_len * np.cos(fore_flap),
            fore_len * np.sin(fore_flap)
        ])
        
        b1 = pv.Cylinder(center=(sh_pos + el_pos)/2, direction=el_pos - sh_pos, radius=0.017, height=np.linalg.norm(el_pos - sh_pos))
        b2 = pv.Cylinder(center=(el_pos + wr_pos)/2, direction=wr_pos - el_pos, radius=0.013, height=np.linalg.norm(wr_pos - el_pos))
        b1["heat"] = np.full(b1.n_points, 0.15)
        b2["heat"] = np.full(b2.n_points, 0.10)
        meshes.extend([b1, b2])
        
        finger_tips = []
        for f_idx in range(4):
            f_angle = -0.45 + f_idx * 0.28
            f_len = 0.46 - f_idx * 0.07
            tip = wr_pos + np.array([
                -0.12 - 0.09 * f_idx,
                side * f_len * np.cos(fore_flap + side * f_angle * 0.4),
                f_len * np.sin(fore_flap + side * f_angle * 0.4) - 0.05 * f_idx
            ])
            finger_tips.append(tip)
            f_bone = pv.Cylinder(center=(wr_pos + tip)/2, direction=tip - wr_pos, radius=0.007, height=np.linalg.norm(tip - wr_pos))
            f_bone["heat"] = np.full(f_bone.n_points, 0.08)
            meshes.append(f_bone)
            
        # Wing Membrane
        camber = -0.07 * np.cos(omega * t)
        u_grid = np.linspace(0, 1, 10)
        v_grid = np.linspace(0, 1, 10)
        U, V = np.meshgrid(u_grid, v_grid, indexing='ij')
        
        mem_x = (1 - V) * ((1 - U)*sh_pos[0] + U*finger_tips[0][0]) + V * ((1 - U)*body_points[thorax_idx+4][0] + U*finger_tips[3][0])
        mem_y = (1 - V) * ((1 - U)*sh_pos[1] + U*finger_tips[0][1]) + V * ((1 - U)*body_points[thorax_idx+4][1] + U*finger_tips[3][1])
        mem_z = (1 - V) * ((1 - U)*sh_pos[2] + U*finger_tips[0][2]) + V * ((1 - U)*body_points[thorax_idx+4][2] + U*finger_tips[3][2]) + camber * np.sin(np.pi * U) * np.sin(np.pi * V)
        
        xyz = np.column_stack([mem_x.ravel(), mem_y.ravel(), mem_z.ravel()])
        grid = pv.StructuredGrid(*(xyz[:, i].reshape(mem_x.shape) for i in range(3)))
        mem_mesh = grid.extract_surface(algorithm='dataset_surface')
        # Wing membrane subtle translucent heat glow
        mem_mesh["heat"] = np.full(mem_mesh.n_points, 0.05 + 0.15 * heat_intensity)
        meshes.append(mem_mesh)

    # 4. Tail Rudder Flukes
    tail_tip = body_points[-1]
    for side in (-1, 1):
        fluke = pv.Cone(center=[tail_tip[0] + 0.06, tail_tip[1] + side * 0.045, tail_tip[2]], direction=[-0.8, side * 0.6, 0], height=0.12, radius=0.035)
        fluke["heat"] = np.full(fluke.n_points, 0.05)
        meshes.append(fluke)

    # Combine all parts
    dragon = meshes[0].copy()
    for m in meshes[1:]:
        dragon = dragon.merge(m)
        
    return dragon, mouth_pos

if __name__ == "__main__":
    p = pv.Plotter(off_screen=True, window_size=(1280, 720))
    p.set_background("#020306")
    
    dragon, mouth = build_mathematical_dragon(t=1.2, jaw_open=0.9, heat_intensity=1.0)
    p.add_mesh(dragon, scalars="heat", cmap=DRAGON_CMAP, clim=(0, 1), smooth_shading=True, specular=0.85, specular_power=26, metallic=0.75, show_scalar_bar=False)
    
    # Add mouth light
    mouth_light = pv.Light(position=mouth + [-0.02, 0, 0], color="#ff7711", intensity=3.2)
    p.add_light(mouth_light)
    rim_light = pv.Light(position=(0.3, 0.5, -0.4), color="#224263", intensity=1.2)
    p.add_light(rim_light)
    
    p.camera.position = (-0.95, 0.35, 0.55)
    p.camera.focal_point = (-0.15, 0.0, 0.0)
    p.camera.view_angle = 48
    p.camera.up = (0, 0, 1)
    
    p.screenshot("my-project/dragon-fire-3d/output/test_math_flying_dragon.png")
    p.close()
    print("Test mathematical flying dragon screenshot saved!")
