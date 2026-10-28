"""Video renderer for chain-rule project.

Supports low-res previews, keyframe test exports, and full scene rendering.
Usage examples:
    # Keyframe test (renders key PNG frames for visual verification)
    python render.py --test

    # Short low-res preview video (640x360 @ 15fps, default 8 seconds)
    python render.py --preview

    # Single frame snapshot at source second 16.5
    python render.py --frame 16.5

    # Custom time range excerpt
    python render.py --range 12 21 --quality low
"""

from __future__ import annotations

import argparse
import sys
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
from scenes import build_scene_01, SCENE_01_DURATION

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

    parser.add_argument("--scene", type=int, default=1, choices=[1], help="Scene number to render (default: 1)")
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
    print(f"Building Scene {args.scene:02d} (Target Export: {width}x{height} @ {fps} fps, backend={args.backend})...")
    scene = build_scene_01(audio_path=audio_path)

    # 1. Action: --test (Extract key stills for fast inspection)
    if args.test:
        frames_dir = output_dir / f"scene_{args.scene:02d}_test_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        timestamps = [
            (3.0, "network_reveal"),
            (16.5, "tunable_weight_dial"),
            (23.0, "input_digit_7"),
            (27.0, "forward_activation_wave"),
            (32.0, "output_prediction_guess"),
            (37.5, "red_loss_flare"),
        ]
        print(f"Exporting {len(timestamps)} test frames to {frames_dir}...")
        with create_renderer(args.backend, antialias=1) as renderer:
            for t, label in timestamps:
                out_path = frames_dir / f"frame_{t:04.1f}s_{label}.png"
                img = renderer.frame(scene, t, (width, height))
                img.save(out_path)
                print(f"  ✓ [{t:04.1f}s] {out_path.name} ({img.size[0]}x{img.size[1]})")
        print(f"Test completed. Inspect frames at:\n  {frames_dir}")
        return

    # 2. Action: --frame (Single timestamp still)
    if args.frame is not None:
        t = args.frame
        if not 0.0 <= t <= scene.duration:
            sys.exit(f"Error: frame timestamp {t}s is outside scene duration [0.0, {scene.duration}s]")
        out_path = args.output or output_dir / f"scene_{args.scene:02d}_frame_{t:04.1f}s.png"
        with create_renderer(args.backend, antialias=1) as renderer:
            save_frame(
                scene,
                t,
                out_path,
                size=(width, height),
                renderer=renderer,
                overwrite=args.overwrite,
            )
        print(f"Saved frame: {out_path}")
        return

    # 3. Action: --preview or video export
    # Preview defaults to a fast low-res 8-second excerpt unless specified otherwise
    if args.preview and not args.range:
        preview_dur = args.duration or 8.0
        start_t = 0.0
        end_t = min(preview_dur, scene.duration)
        default_name = f"preview_scene_{args.scene:02d}_{int(preview_dur)}s.mp4"
    elif args.range:
        start_t, end_t = args.range[0], args.range[1]
        default_name = f"scene_{args.scene:02d}_range_{start_t:g}_{end_t:g}.mp4"
    else:
        start_t, end_t = 0.0, scene.duration
        default_name = f"scene_{args.scene:02d}.mp4"

    out_video = args.output or output_dir / default_name

    if out_video.exists() and not args.overwrite:
        sys.exit(f"Error: Output file exists: {out_video}. Pass --overwrite to replace it.")

    settings = ExportSettings(
        width=width,
        height=height,
        fps=fps,
        backend=args.backend,
        antialias=1,
        preset="fast" if args.preview else "medium",
    )

    print(f"Rendering video to: {out_video}")
    print(f"  Time range: {start_t:.2f}s to {end_t:.2f}s ({end_t - start_t:.2f}s)")
    print(f"  Resolution: {width}x{height} @ {fps} fps")

    with create_renderer(args.backend, antialias=1) as renderer:
        with ExportProgress() as progress:
            render(
                scene,
                out_video,
                settings=settings,
                renderer=renderer,
                start_time=start_t,
                end_time=end_t,
                overwrite=args.overwrite,
                progress=progress,
            )

    print(f"✓ Video rendered successfully: {out_video}")


if __name__ == "__main__":
    main()
