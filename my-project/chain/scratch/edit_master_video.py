import subprocess
import wave
import numpy as np
from pathlib import Path
import time

ROOT = Path("/home/kingnit/Desktop/Faceless Champ/my-project/chain")
OUTPUT_DIR = ROOT / "output"
TMP_DIR = Path("/tmp/video_edit")
TMP_DIR.mkdir(parents=True, exist_ok=True)

# 1. Exact scene definitions
scenes = [OUTPUT_DIR / f"scene_{i:02d}_4k.mp4" for i in range(1, 13)]
durations = []
boundaries = []
t = 0.0

for s in scenes:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=duration,nb_frames",
        "-of", "default=noprint_wrappers=1:nokey=1", str(s)
    ]).decode().split()
    dur = float(out[0])
    frames = int(out[1])
    durations.append((dur, frames))
    if len(durations) < 12:
        t += dur
        boundaries.append(t)

print(f"Loaded 12 scene clips. Total frames: {sum(f for _, f in durations)}")
print(f"Boundaries (11 transitions): {boundaries}")

# 2. Extract final frame of scenes 1..11 and create 0.8s (24 frames) spacers
spacer_files = []
for i in range(1, 12):
    scene_file = scenes[i - 1]
    last_frame_img = TMP_DIR / f"last_frame_{i:02d}.png"
    spacer_clip = TMP_DIR / f"spacer_{i:02d}.mp4"
    spacer_files.append(spacer_clip)
    
    # Extract last frame
    subprocess.run([
        "ffmpeg", "-y", "-sseof", "-0.05", "-i", str(scene_file),
        "-vframes", "1", str(last_frame_img)
    ], check=True, stderr=subprocess.DEVNULL)
    
    # Encode 24-frame still clip matching exact H.264 profile, timescale, and audio rate
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(last_frame_img),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", "0.8", "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1",
        "-pix_fmt", "yuv420p", "-video_track_timescale", "15360",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        str(spacer_clip)
    ], check=True, stderr=subprocess.DEVNULL)
    print(f"Generated 0.8s spacer for Scene {i:02d}")

# 3. Concatenate video stream
concat_list = TMP_DIR / "concat_with_spacers.txt"
with open(concat_list, "w") as f:
    for i in range(1, 13):
        f.write(f"file '{scenes[i - 1]}'\n")
        if i < 12:
            f.write(f"file '{spacer_files[i - 1]}'\n")

print("Concatenating 12 scenes + 11 spacers with stream copy...")
video_with_gaps = TMP_DIR / "video_with_gaps.mp4"
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
    "-c", "copy", str(video_with_gaps)
], check=True, stderr=subprocess.DEVNULL)
print("Video stream concatenation complete!")

# 4. Process Audio: Mutes + 0.8s Gaps at Boundaries
# Convert audio.mp3 to uncompressed 48kHz stereo WAV
raw_wav = TMP_DIR / "raw_audio_48k.wav"
subprocess.run([
    "ffmpeg", "-y", "-i", str(ROOT / "audio.mp3"),
    "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(raw_wav)
], check=True, stderr=subprocess.DEVNULL)

with wave.open(str(raw_wav), "rb") as wf:
    framerate = wf.getframerate()
    nchannels = wf.getnchannels()
    nframes = wf.getnframes()
    pcm_data = np.frombuffer(wf.readframes(nframes), dtype=np.int16).copy().reshape(-1, nchannels)

audio_len_s = len(pcm_data) / framerate
print(f"Loaded master audio: {len(pcm_data)} samples ({audio_len_s:.3f}s)")

# Apply 3 mutes with 25ms cosine fade out/in
def apply_mute(data, sr, t_start, t_end, fade_ms=25):
    fade_len = int(sr * (fade_ms / 1000.0))
    i_start = int(sr * t_start)
    i_end = int(sr * t_end)
    
    # Fade out
    fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_len)))
    for ch in range(data.shape[1]):
        data[i_start : i_start + fade_len, ch] = (data[i_start : i_start + fade_len, ch] * fade_out).astype(np.int16)
        # Zero out middle
        data[i_start + fade_len : i_end - fade_len, ch] = 0
        # Fade in
        fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_len)))
        data[i_end - fade_len : i_end, ch] = (data[i_end - fade_len : i_end, ch] * fade_in).astype(np.int16)

print("Applying 3 requested mutes...")
apply_mute(pcm_data, framerate, 62.10, 63.50)  # Mute 1: "dirabunde" / "The year album day"
apply_mute(pcm_data, framerate, 86.40, 89.15)  # Mute 2: "Label that rate on screen, times two"
apply_mute(pcm_data, framerate, 97.10, 99.05)  # Mute 3: "Label that rate, times three"
print("Mutes applied.")

# Now slice audio into 12 chapter chunks and insert 0.8s silence (38,400 samples)
silence_08s = np.zeros((int(framerate * 0.8), nchannels), dtype=np.int16)

boundary_samples = [int(round(b * framerate)) for b in boundaries]
audio_chunks = []
prev_idx = 0
for b_idx in boundary_samples:
    audio_chunks.append(pcm_data[prev_idx:b_idx])
    audio_chunks.append(silence_08s)
    prev_idx = b_idx
audio_chunks.append(pcm_data[prev_idx:])

final_audio_pcm = np.concatenate(audio_chunks, axis=0)
print(f"Final audio assembled: {len(final_audio_pcm)} samples ({len(final_audio_pcm)/framerate:.3f}s)")

# Save final audio to WAV
audio_with_gaps_wav = TMP_DIR / "audio_with_gaps.wav"
with wave.open(str(audio_with_gaps_wav), "wb") as wf:
    wf.setnchannels(nchannels)
    wf.setsampwidth(2)
    wf.setframerate(framerate)
    wf.writeframes(final_audio_pcm.tobytes())

# 5. Final Mux: Video with Gaps + Master Audio with Gaps
final_output = OUTPUT_DIR / "chain_rule_master_4k_youtube.mp4"
print(f"Muxing into final master: {final_output}...")
subprocess.run([
    "ffmpeg", "-y",
    "-i", str(video_with_gaps),
    "-i", str(audio_with_gaps_wav),
    "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "384k", "-ar", "48000",
    "-movflags", "+faststart",
    str(final_output)
], check=True, stderr=subprocess.DEVNULL)

print("Final master video generated successfully!")
