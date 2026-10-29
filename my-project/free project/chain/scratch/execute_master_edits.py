#!/usr/bin/env python3
"""
execute_master_edits.py
Performs precision audio muting, phrase trimming, and chapter transition pauses
on the 4K master video without re-rendering the whole animation.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/kingnit/Desktop/Faceless Champ/my-project/chain")
OUTPUT_DIR = ROOT / "output"
SCRATCH_DIR = ROOT / "scratch"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], desc: str):
    print(f"\n---> {desc}...")
    t0 = time.time()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"FAILED: {desc}\nSTDERR:\n{res.stderr}")
        sys.exit(1)
    print(f"DONE in {time.time() - t0:.1f}s")


def main():
    print("==========================================================")
    print("Starting 4K Master Video Precision Edits & Assembly")
    print("==========================================================")

    # -------------------------------------------------------------------------
    # 1. Edit Scene 02: Mute "dirabunde" at 36.10s - 37.45s
    # -------------------------------------------------------------------------
    s2_in = OUTPUT_DIR / "scene_02_4k.mp4"
    s2_out = SCRATCH_DIR / "scene_02_edited.mp4"
    mute_filter = "volume=enable='between(t,36.10,37.45)':volume=0"
    run([
        "ffmpeg", "-y", "-i", str(s2_in),
        "-c:v", "copy",
        "-af", mute_filter,
        "-c:a", "aac", "-b:a", "384k",
        str(s2_out)
    ], "Step 1: Muting 'dirabunde' in Scene 02")

    # -------------------------------------------------------------------------
    # 2. Edit Scene 03: Trim off 'Label that rate on screen, times two' (keep 0.0 -> 19.25s)
    # -------------------------------------------------------------------------
    s3_in = OUTPUT_DIR / "scene_03_4k.mp4"
    s3_out = SCRATCH_DIR / "scene_03_edited.mp4"
    run([
        "ffmpeg", "-y", "-ss", "0.0", "-to", "19.25", "-i", str(s3_in),
        "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "384k",
        str(s3_out)
    ], "Step 2: Trimming Scene 03 to 19.25s (cutting 'times two' narration)")

    # -------------------------------------------------------------------------
    # 3. Edit Scene 04: Cut out 'Label that rate, times three' (7.80s -> 9.85s)
    # -------------------------------------------------------------------------
    s4_in = OUTPUT_DIR / "scene_04_4k.mp4"
    s4_p1 = SCRATCH_DIR / "scene_04_p1.mp4"
    s4_p2 = SCRATCH_DIR / "scene_04_p2.mp4"
    s4_out = SCRATCH_DIR / "scene_04_edited.mp4"

    run([
        "ffmpeg", "-y", "-ss", "0.0", "-to", "7.80", "-i", str(s4_in),
        "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "384k",
        str(s4_p1)
    ], "Step 3a: Scene 04 Part 1 (0.0s -> 7.80s)")

    run([
        "ffmpeg", "-y", "-ss", "9.85", "-to", "42.80", "-i", str(s4_in),
        "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "384k",
        str(s4_p2)
    ], "Step 3b: Scene 04 Part 2 (9.85s -> 42.80s)")

    s4_concat_txt = SCRATCH_DIR / "scene_04_concat.txt"
    s4_concat_txt.write_text(f"file '{s4_p1.name}'\nfile '{s4_p2.name}'\n")

    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(s4_concat_txt),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "384k",
        str(s4_out)
    ], "Step 3c: Joining Scene 04 Parts without 'times three' narration")

    # -------------------------------------------------------------------------
    # 4. Generate 0.5s Freeze-Frame Transition Pauses for Scenes 01 to 11
    # -------------------------------------------------------------------------
    print("\n---> Step 4: Generating 0.5s Freeze-Frame Transition Pauses...")
    # First update last frame for Scene 03 from the newly trimmed clip
    run([
        "ffmpeg", "-y", "-sseof", "-0.04", "-i", str(s3_out),
        "-vframes", "1", str(SCRATCH_DIR / "last_frame_03.png")
    ], "Updating Scene 03 final frame")

    for i in range(1, 12):
        frame_png = SCRATCH_DIR / f"last_frame_{i:02d}.png"
        pause_mp4 = SCRATCH_DIR / f"pause_{i:02d}.mp4"
        run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-t", "0.5", "-i", str(frame_png),
            "-f", "lavfi", "-t", "0.5", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k",
            str(pause_mp4)
        ], f"Generating pause_{i:02d}.mp4")

    # -------------------------------------------------------------------------
    # 5. Assemble Full Concat List
    # -------------------------------------------------------------------------
    print("\n---> Step 5: Preparing Master Concat List...")
    final_clips = [
        OUTPUT_DIR / "scene_01_4k.mp4",
        SCRATCH_DIR / "pause_01.mp4",
        s2_out,
        SCRATCH_DIR / "pause_02.mp4",
        s3_out,
        SCRATCH_DIR / "pause_03.mp4",
        s4_out,
        SCRATCH_DIR / "pause_04.mp4",
        OUTPUT_DIR / "scene_05_4k.mp4",
        SCRATCH_DIR / "pause_05.mp4",
        OUTPUT_DIR / "scene_06_4k.mp4",
        SCRATCH_DIR / "pause_06.mp4",
        OUTPUT_DIR / "scene_07_4k.mp4",
        SCRATCH_DIR / "pause_07.mp4",
        OUTPUT_DIR / "scene_08_4k.mp4",
        SCRATCH_DIR / "pause_08.mp4",
        OUTPUT_DIR / "scene_09_4k.mp4",
        SCRATCH_DIR / "pause_09.mp4",
        OUTPUT_DIR / "scene_10_4k.mp4",
        SCRATCH_DIR / "pause_10.mp4",
        OUTPUT_DIR / "scene_11_4k.mp4",
        SCRATCH_DIR / "pause_11.mp4",
        OUTPUT_DIR / "scene_12_4k.mp4",
    ]

    master_list_txt = SCRATCH_DIR / "master_edit_concat.txt"
    with open(master_list_txt, "w") as f:
        for clip in final_clips:
            f.write(f"file '{clip.resolve()}'\n")

    # -------------------------------------------------------------------------
    # 6. Final Concat into output/chain_rule_master_4k_youtube.mp4
    # -------------------------------------------------------------------------
    final_master = OUTPUT_DIR / "chain_rule_master_4k_youtube.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(master_list_txt),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "384k",
        "-movflags", "+faststart",
        str(final_master)
    ], "Step 6: Final Concatenation to chain_rule_master_4k_youtube.mp4")

    print("\n==========================================================")
    print(f"Master 4K Video Successfully Edited and Exported:")
    print(f" -> {final_master}")
    print("==========================================================")


if __name__ == "__main__":
    main()
