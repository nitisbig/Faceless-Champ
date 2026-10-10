# Verification — 2026-10-10

Implemented with core 0.1.2, kit 0.1.0rc3, Playwright 1.63.0, and Chromium headless shell 153.0.8010.12.

- The authored composition is exactly 30 seconds.
- Seven storyboard samples were prepared and visually inspected at source seconds 2, 7, 11, 16, 21, 25, and 28.
- Only source seconds 6–10 were exported: H.264, 960×540, 15 FPS, 60 frames, 4.000 seconds, silent.
- The excerpt was completely decoded with FFmpeg without errors and an encoded frame was inspected.
- The original HTML was preserved; the example uses its existing local simulated reply logic.
- Browser tests verify timed input, local assets, delayed JS responses, CSS transitions and repeating CSS animations. Repeated and ranged captures match sampled full-capture pixels.
- Core suite: 323 passed; kit suite: 128 passed. The opt-in Chromium integration test also passed separately.
- Core tests cover backward seeking, source offsets, final-frame holds, selector crops, transforms, masks, missing ranges/dependencies, and missing/truncated cache files.
- Kit tests cover fresh component ownership and bounded portrait/landscape layouts.
- Both distributions were built as wheels and source archives. A clean installed environment composed the storyboard and exported the excerpt with no Playwright installed. After installing web extras, a one-second synthetic capture and kit playback passed.
- Guide checks passed for 28 chapters, 36 Python snippets, 21 examples, and four starters. Browser examples use synthetic prepared assets in the guide verifier.

Outputs: `output/storyboard/storyboard.png` and `output/preview.mp4` (generated files, ignored by Git).

**No complete 30-second video was rendered.** Full export, 4K performance, and other browser/font environments remain unverified. Run `render.py --mode render` when ready.
