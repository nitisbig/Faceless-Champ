"""Verify installed OS UI packages and optionally render the full starter.

Run from outside the source tree with both wheels installed:
python /path/to/examples/os_ui/verify.py --output /path/to/output/os-ui --render
"""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import facelesschamp_kit
from facelesschamp_kit import Project
from facelesschamp_kit.blocks import FinderWindow, SettingsWindow
from facelesschamp_kit.context import BuildContext
from facelesschamp_kit.scaffold import init_project
from PIL import Image, ImageDraw

import faceless_champ
from faceless_champ import Canvas, PillowRenderer, Scene
from faceless_champ.os_ui import OSClip, OSScript


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--chunk", type=int, help="Render one five-second range, numbered from zero")
    parser.add_argument("--finish", action="store_true", help="Join and verify all rendered ranges")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fc-os-starter-") as temporary:
        project_root = Path(temporary) / "tutorial"
        init_project(project_root, template="os-ui")
        compiled = Project(project_root).build("main")
        scene = compiled.composition
        renderer = PillowRenderer(1)
        renderer.validate(scene)
        if args.chunk is not None:
            start = args.chunk * 5
            if args.chunk < 0 or start >= scene.duration:
                parser.error("Chunk index is outside the tutorial")
            scene.render(
                output / f"chunk-{args.chunk:03}.mp4",
                width=1920,
                height=1080,
                fps=30,
                antialias=1,
                preset="fast",
                overwrite=True,
                start_time=start,
                end_time=min(scene.duration, start + 5),
            )
            print(f"Completed chunk {args.chunk}", flush=True)
            return
        samples = [1.9, 3.5, 4.9, 8.5, 17.9, 24.9, 26.7, 31.9]
        for i, at in enumerate(samples):
            renderer.frame(scene, at, (1920, 1080)).save(output / f"still-{i:02}.png")
        # Both direct and source-offset playback agree at intermediate action times.
        clip = scene.entries[0].component
        assert isinstance(clip, OSClip)
        expected = clip.frame_image(8.5, 0.25).tobytes()
        clip.frame_image(30, 0.25)
        assert clip.frame_image(8.5, 0.25).tobytes() == expected
        for block in (FinderWindow(), SettingsWindow(script=OSScript().set_value("appearance:theme", "dark"))):
            name = block.mode
            ctx = BuildContext(output, canvas=Canvas(1080, 1920, "#172438"))
            built = block.compose(ctx, ctx.bounds)
            portrait = Scene(ctx.canvas).add(built.root).wait(2)
            renderer.frame(portrait, 1.5, (1080, 1920)).save(output / f"portrait-{name}.png")
            rgba = built.root.frame_image(1.5)
            assert rgba.getpixel((0, 0))[3] == 0
            rgba.save(output / f"transparent-{name}.png")
        report = {
            "core_version": faceless_champ.__version__,
            "kit_version": facelesschamp_kit.__version__,
            "core_path": faceless_champ.__file__,
            "kit_path": facelesschamp_kit.__file__,
            "duration": scene.duration,
            "still_times": samples,
            "random_access_passed": True,
            "transparent_and_portrait_passed": True,
            "full_export_verified": False,
        }
        if args.render or args.finish:
            video = output / "macos-tutorial-1080p.mp4"

            def progress(done, total):
                if done % 150 == 0 or done == total:
                    print(f"Render {done}/{total}", flush=True)

            if args.finish:
                import math

                chunks = [output / f"chunk-{i:03}.mp4" for i in range(math.ceil(scene.duration / 5))]
                if not all(chunk.is_file() for chunk in chunks):
                    raise ValueError("Render every chunk before --finish")
                manifest = output / "concat.txt"
                manifest.write_text("".join(f"file '{chunk.name}'\n" for chunk in chunks))
                subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-f",
                        "concat",
                        "-safe",
                        "0",
                        "-i",
                        str(manifest),
                        "-c",
                        "copy",
                        "-movflags",
                        "+faststart",
                        "-y",
                        str(video),
                    ],
                    check=True,
                )
            else:
                scene.render(
                    video,
                    width=1920,
                    height=1080,
                    fps=30,
                    antialias=1,
                    preset="fast",
                    overwrite=True,
                    progress=progress,
                )
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
            metadata = json.loads(
                subprocess.check_output(
                    ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]
                )
            )
            stream = next(s for s in metadata["streams"] if s["codec_type"] == "video")
            assert (stream["width"], stream["height"], stream["r_frame_rate"]) == (1920, 1080, "30/1")
            assert int(stream["nb_frames"]) == round(scene.duration * 30)
            assert abs(float(metadata["format"]["duration"]) - scene.duration) < 1 / 30
            for i, at in enumerate(samples):
                subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-ss",
                        str(at),
                        "-i",
                        str(video),
                        "-frames:v",
                        "1",
                        "-y",
                        str(output / f"encoded-{i:02}.png"),
                    ],
                    check=True,
                )
            # Check joined boundaries against the original timeline, allowing H.264 loss.
            import math

            from PIL import ImageChops, ImageStat

            boundary_psnr = {}
            for at in range(5, int(scene.duration), 5):
                frame_path = output / f"boundary-{at:02}.png"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-ss",
                        str(at),
                        "-i",
                        str(video),
                        "-frames:v",
                        "1",
                        "-y",
                        str(frame_path),
                    ],
                    check=True,
                )
                expected = renderer.frame(scene, at, (1920, 1080)).convert("RGB")
                with Image.open(frame_path) as encoded:
                    error = ImageStat.Stat(ImageChops.difference(expected, encoded.convert("RGB")))
                    mse = sum(error.sum2) / (1920 * 1080 * 3)
                    psnr = 100 if mse == 0 else 10 * math.log10(255 * 255 / mse)
                    if psnr < 30:
                        raise ValueError(f"Source-clock mismatch at {at}s: {psnr:.2f}dB")
                    boundary_psnr[str(at)] = round(psnr, 2)
            sheet = Image.new("RGB", (1280, 4 * 384), "#111827")
            draw = ImageDraw.Draw(sheet)
            for i, at in enumerate(samples):
                with Image.open(output / f"encoded-{i:02}.png") as img:
                    sheet.paste(img.resize((640, 360)), ((i % 2) * 640, (i // 2) * 384))
                draw.text(((i % 2) * 640 + 8, (i // 2) * 384 + 364), f"{at:.1f}s", fill="white")
            sheet.save(output / "contact-sheet.png")
            report.update(
                boundary_psnr_db=boundary_psnr,
                joined_ranges=args.finish,
                full_export_verified=True,
                frames=int(stream["nb_frames"]),
                size=[1920, 1080],
                fps=30,
                complete_decode_passed=True,
                video=str(video),
            )
        (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
