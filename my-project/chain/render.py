"""Video renderer for the chain project.

Supports low-res previews, keyframe test exports, single frame snapshots, and full scene rendering.

Usage examples:
    # Keyframe test (renders key PNG frames for fast visual verification)
    python render.py --test

    # Short low-res preview video (640x360 @ 15fps, default 8 seconds)
    python render.py --preview

    # Single frame snapshot at source second 14.5
    python render.py --frame 14.5

    # Custom time range excerpt (e.g., from 10s to 22s)
    python render.py --range 10.0 22.0 --quality medium

    # Full Scene 01 render at 1080p high quality
    python render.py --quality high
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from faceless_champ import (
    ExportProgress,
    ExportSettings,
    create_renderer,
    render,
    save_frame,
)
from scenes import (
    SCENE_01_DURATION,
    SCENE_02_DURATION,
    SCENE_03_DURATION,
    SCENE_04_DURATION,
    SCENE_05_DURATION,
    SCENE_06_DURATION,
    SCENE_07_DURATION,
    SCENE_08_DURATION,
    SCENE_09_DURATION,
    SCENE_10_DURATION,
    SCENE_11_DURATION,
    SCENE_12_DURATION,
    build_scene_01,
    build_scene_02,
    build_scene_03,
    build_scene_04,
    build_scene_05,
    build_scene_06,
    build_scene_07,
    build_scene_08,
    build_scene_09,
    build_scene_10,
    build_scene_11,
    build_scene_12,
)

DEFAULT_AUDIO = ROOT / "audio.mp3"

QUALITIES = {
    "low": (640, 360),
    "preview": (960, 540),
    "medium": (960, 540),
    "high": (1920, 1080),
    "1080p": (1920, 1080),
    "4k": (3840, 2160),
    "2160p": (3840, 2160),
    "uhd": (3840, 2160),
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--test", action="store_true", help="Render test still frames across key story timestamps")
    mode.add_argument("--preview", action="store_true", help="Render a low-res preview video (640x360 @ 15fps)")
    mode.add_argument("--frame", type=float, metavar="SECONDS", help="Render a single frame at the given timestamp")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"), help="Render a custom time range")

    parser.add_argument("--scene", type=int, default=1, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], help="Scene number to render (default: 1)")
    parser.add_argument("--all", action="store_true", help="Render or test all 12 scenes sequentially")
    parser.add_argument(
        "--quality",
        choices=["low", "preview", "medium", "high", "1080p", "4k", "2160p", "uhd"],
        default=None,
        help="Resolution preset (default: low for preview/test, high otherwise, 4k for 3840x2160)",
    )
    parser.add_argument("--fps", type=int, default=None, help="Frame rate (default: 15 for low/preview, 30 for high)")
    parser.add_argument(
        "--backend",
        choices=["skia", "moderngl", "pillow"],
        default="skia",
        help="Rendering backend (default: skia)",
    )
    parser.add_argument("--duration", type=float, default=None, help="Preview duration in seconds (default: 8.0s)")
    parser.add_argument("--no-audio", action="store_true", help="Do not mix audio track")
    parser.add_argument("--output", type=Path, help="Custom output path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")

    return parser.parse_args()


def main():
    args = parse_args()

    # Determine quality and fps defaults
    if args.preview or args.test:
        quality_key = args.quality or "low"
        default_fps = 15
    else:
        quality_key = args.quality or "high"
        default_fps = 30

    width, height = QUALITIES[quality_key]
    fps = args.fps or default_fps

    output_dir = ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = None if args.no_audio else DEFAULT_AUDIO
    scene_registry = {
        1: (build_scene_01, [
            (3.0, "01_network_reveal"),
            (7.5, "02_ambient_learning_flow"),
            (12.5, "03_focal_weight_dial"),
            (16.0, "04_dial_needle_wiggle"),
            (19.2, "05_forward_attribution_pulse"),
            (21.0, "06_crimson_loss_beacon"),
            (24.0, "07_grand_chain_rule_title"),
        ]),
        2: (build_scene_02, [
            (3.5, "01_lamp_shadow_velocity_arrow"),
            (8.5, "02_compounding_bank_rate_graph"),
            (14.0, "03_roadmap_stage_1_gears"),
            (20.0, "04_roadmap_stage_2_first_principles"),
            (26.5, "05_roadmap_stage_3_crucible_sin_x2"),
            (33.0, "06_roadmap_stage_4_neural_backprop"),
            (39.0, "07_you_will_see_it_climax"),
        ]),
        3: (build_scene_03, [
            (3.0, "01_three_gears_materialize"),
            (7.5, "02_gear_a_gear_b_meshed"),
            (10.5, "03_gear_b_gear_c_meshed"),
            (14.5, "04_kinematics_sweep_rotation"),
            (17.5, "05_revolutions_completed_1_and_2"),
            (20.5, "06_floating_rate_formula_times_two"),
            (24.5, "07_pulse_forward_rate_propagation"),
            (29.0, "08_scene_03_final_three_gear_tableau"),
        ]),
        4: (build_scene_04, [
            (5.5, "01_gear_b_drives_gear_c_x3_rate"),
            (10.0, "02_rate_bc_formula_and_3_turns"),
            (14.0, "03_cascading_question_dc_da"),
            (20.5, "04_synchronous_full_chain_spin"),
            (23.5, "05_six_full_turns_arithmetic_2x3_6"),
            (28.5, "06_numbers_merged_into_6_rates_multiply"),
            (32.0, "07_definition_header_and_caliper_divider"),
            (34.8, "08_chain_rule_laser_wipe_and_linking_arc"),
            (36.2, "09_chain_rule_formula_complete_mint_bloom"),
            (39.5, "10_holographic_transmission_cascade_x6"),
        ]),
        5: (build_scene_05, [
            (4.0, "01_processors_materialized_and_pipe"),
            (9.8, "02_capsule_x_entering_machine_g"),
            (13.5, "03_capsule_u_in_glass_conduit_pipe"),
            (17.5, "04_capsule_y_emerging_from_machine_f"),
            (21.0, "05_composite_formula_y_fgx_revealed"),
            (26.0, "06_nudge_question_arc_dy_dx"),
        ]),
        6: (build_scene_06, [
            (2.2, "01_three_stacked_number_lines_materialized"),
            (4.8, "02_input_nudge_dx_vector_and_caliper"),
            (10.0, "03_first_stretch_du_and_beam"),
            (15.0, "04_second_stretch_dy_all_three_displacements"),
            (18.5, "05_kinetic_micro_gears_g_and_f"),
            (21.5, "06_machine_g_rate_gauge_du_over_dx"),
            (24.5, "07_machine_f_rate_gauge_dy_over_du"),
            (30.0, "08_climax_formula_complete_with_bloom_and_streak"),
        ]),
        7: (build_scene_07, [
            (3.5, "01_lhs_derivative_revealed"),
            (7.5, "02_limit_definition_and_brackets"),
            (10.5, "03_limit_dx_shrinks_to_zero"),
            (15.0, "04_fractional_split_opening"),
            (19.0, "05_stepping_stone_du_inserted"),
            (24.0, "06_diagonal_cancellation_beam"),
            (27.5, "07_cancellation_strikes_and_equivalence"),
            (31.5, "08_stepping_stone_bridge_and_photon_jump"),
        ]),
        8: (build_scene_08, [
            (4.5, "01_machine_g_rate_gauge_and_fraction"),
            (9.0, "02_machine_f_rate_gauge_and_fraction"),
            (13.5, "03_distributed_limit_expression"),
            (17.5, "04_calipers_dx_and_du_contracting"),
            (21.5, "05_quantum_sparkle_settling_into_derivatives"),
            (25.0, "06_morph_left_fraction_dy_du"),
            (27.5, "07_morph_right_fraction_du_dx"),
            (34.0, "08_grand_leibniz_master_equation"),
            (44.0, "09_plain_words_underbraces_and_eval_arc"),
            (52.0, "10_honest_footnote_caratheodory"),
            (58.5, "11_final_product_law_energy_cascade"),
        ]),
        9: (build_scene_09, [
            (3.0, "01_target_formula_y_sin_x2"),
            (6.5, "02_dual_graphs_parabola_and_sine"),
            (10.0, "03_operating_points_and_conduit_bridge"),
            (14.5, "04_tangent_slopes_du_dx_and_dy_du"),
            (18.0, "05_chain_rule_multiplication_structure"),
            (22.5, "06_analytic_derivative_2x_cos_x2_crystallized"),
            (25.5, "07_hook_question_is_formula_telling_truth"),
            (27.0, "08_scene_09_final_tableau"),
        ]),
        10: (build_scene_10, [
            (4.0, "01_analytic_inner_rate_2"),
            (10.0, "02_analytic_outer_rate_cos1"),
            (15.5, "03_analytic_product_1_0806_gauge"),
            (21.0, "04_brute_force_nudge_dx_001"),
            (27.0, "05_brute_force_du_002001_twice_nudge"),
            (34.0, "06_brute_force_dy_001080"),
            (40.0, "07_empirical_quotient_1_080"),
            (45.5, "08_emerald_agreement_stamp_converged"),
            (51.0, "09_common_trap_missing_gear_alert"),
            (54.0, "10_scene_10_final_tableau"),
        ]),
        11: (build_scene_11, [
            (3.0, "01_neural_lattice_3_layers"),
            (7.0, "02_synaptic_filaments_and_layer_flow"),
            (11.0, "03_weight_dial_isolation_w"),
            (15.0, "04_neuron_affine_and_sigmoid_activation"),
            (19.0, "05_forward_activation_pulse_to_output"),
            (23.0, "06_prediction_vs_target_loss_beacon"),
            (26.5, "07_crimson_loss_shockwaves"),
            (29.0, "08_chain_rule_gradient_4_factors"),
            (31.5, "09_calipers_on_local_derivatives"),
            (33.0, "10_scene_11_final_tableau"),
        ]),
        12: (build_scene_12, [
            (3.5, "01_reverse_gears_turning"),
            (8.5, "02_weight_dial_turning_by_delta_w"),
            (14.0, "03_massive_multi_layer_matrix_zoom_out"),
            (19.0, "04_billions_scale_reverse_gradient_wave"),
            (25.5, "05_do_not_see_symbols_see_gears_formula"),
            (31.0, "06_transmission_gears_and_nudge_entry"),
            (36.5, "07_multiplicative_stretches_cascade_dx_du_dy"),
            (43.0, "08_three_pillars_shadow_bank_neural"),
            (49.0, "09_master_product_sovereign_theorem"),
            (54.0, "10_scene_12_grand_finale_tableau"),
        ]),
    }

    scenes_to_process = list(range(1, 13)) if args.all else [args.scene]

    for s_idx in scenes_to_process:
        if s_idx not in scene_registry:
            sys.exit(f"Unsupported scene number: {s_idx}")
        builder, timestamps = scene_registry[s_idx]
        print(f"\n[{s_idx:02d}/12] Building Scene {s_idx:02d} (Target Export: {width}x{height} @ {fps} fps, backend={args.backend})...")
        scene = builder(audio_path=audio_path)

        # 1. Action: --test (Extract key stills for fast inspection)
        if args.test:
            suffix = "_4k_test_frames" if quality_key in ("4k", "2160p", "uhd") else "_test_frames"
            frames_dir = output_dir / f"scene_{s_idx:02d}{suffix}"
            frames_dir.mkdir(parents=True, exist_ok=True)
            print(f"Exporting {len(timestamps)} test frames to {frames_dir}...")
            with create_renderer(args.backend, antialias=1) as renderer:
                for t, label in timestamps:
                    out_path = frames_dir / f"frame_{t:04.1f}s_{label}.png"
                    img = renderer.frame(scene, t, (width, height))
                    img.save(out_path)
                    print(f"  ✓ [{t:04.1f}s] {out_path.name} ({img.size[0]}x{img.size[1]})")
            print(f"Test completed for Scene {s_idx:02d}. Stills at: {frames_dir}")
            continue

        # 2. Action: --frame (Single timestamp still)
        if args.frame is not None:
            t = args.frame
            if not 0.0 <= t <= scene.duration:
                sys.exit(f"Error: frame timestamp {t}s is outside scene duration [0.0, {scene.duration}s]")
            suffix = "_4k" if quality_key in ("4k", "2160p", "uhd") else ""
            out_path = args.output or output_dir / f"scene_{s_idx:02d}_frame_{t:04.1f}s{suffix}.png"
            with create_renderer(args.backend, antialias=1) as renderer:
                save_frame(
                    scene,
                    t,
                    out_path,
                    size=(width, height),
                    renderer=renderer,
                    overwrite=args.overwrite or True,
                )
            print(f"Saved frame: {out_path}")
            continue

        # 3. Action: --preview or video export
        if args.preview and not args.range:
            preview_dur = args.duration or 8.0
            start_t = 0.0
            end_t = min(preview_dur, scene.duration)
            default_name = f"preview_scene_{s_idx:02d}_{int(preview_dur)}s.mp4"
        elif args.range:
            start_t, end_t = args.range[0], args.range[1]
            default_name = f"scene_{s_idx:02d}_range_{start_t:g}_{end_t:g}.mp4"
        else:
            start_t, end_t = 0.0, scene.duration
            if quality_key in ("4k", "2160p", "uhd"):
                default_name = f"scene_{s_idx:02d}_4k.mp4"
            else:
                default_name = f"scene_{s_idx:02d}.mp4"

        out_path = args.output if (args.output and len(scenes_to_process) == 1) else (output_dir / default_name)
        print(f"Rendering time range [{start_t:.2f}s -> {end_t:.2f}s] ({end_t - start_t:.2f}s duration) to {out_path}...")

        settings = ExportSettings(
            width=width,
            height=height,
            fps=fps,
            backend=args.backend,
            antialias=1,
        )

        start_wall_time = time.time()
        last_update_time = 0.0

        def progress(completed: int, total: int):
            nonlocal last_update_time
            if total <= 0:
                return
            now = time.time()
            if completed < total and (now - last_update_time < 0.06):
                return
            last_update_time = now

            elapsed = now - start_wall_time
            fps_rate = completed / elapsed if elapsed > 0.001 else 0.0
            pct = completed / total

            if completed > 0 and pct < 1.0:
                remaining_s = (elapsed / completed) * (total - completed)
                eta_str = f"{int(remaining_s // 60):02d}:{int(remaining_s % 60):02d}"
            else:
                eta_str = "--:--"

            elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
            bar_len = 30
            filled = int(round(bar_len * pct))
            bar = "█" * filled + "░" * (bar_len - filled)

            line = (
                f"\r  [{bar}] {pct*100:5.1f}% | {completed:>{len(str(total))}}/{total} frames "
                f"| {fps_rate:4.1f} fps | Elapsed: {elapsed_str} | ETA: {eta_str}"
            )
            sys.stdout.write(line)
            sys.stdout.flush()

            if completed >= total:
                sys.stdout.write("\n")
                sys.stdout.flush()

        with create_renderer(args.backend, antialias=1) as renderer:
            render(
                scene,
                out_path,
                start_time=start_t,
                end_time=end_t,
                settings=settings,
                renderer=renderer,
                progress=progress,
                overwrite=args.overwrite or True,
            )

        print(f"Render complete: {out_path}")


if __name__ == "__main__":
    main()
