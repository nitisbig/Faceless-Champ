# Cloud render on Kaggle (4K, 30 fps)

Kernel: https://www.kaggle.com/code/nitesh1230/convolution-explained-4k-render
Input dataset: nitesh1230/convolution-explained-4k-input (private)

The render runs on Kaggle's CPU machine (no GPU quota used), 4 parallel workers,
in 51 chunks of 300 frames (10 s). You can turn your PC off — it runs in the cloud.

## Where the results appear (the kernel's Output tab)

| Path | What |
| --- | --- |
| `final/convolution_explained_4k.mp4` | the full video with narration (only when 100% done) |
| `chapters/chN_<name>_4k.mp4` | each chapter with its narration, as soon as that chapter is finished |
| `chunks/` | finished 10 s video-only pieces (used for resuming) |
| `status.json` | progress: chunks done, chapters done, missing chunks, errors, ETA |

## Commands (run from the project folder, with the venv active)

```bash
python kaggle/kaggle_resume.py status     # running / complete / error
python kaggle/kaggle_resume.py download   # download Output into kaggle/output/ and print progress
python kaggle/kaggle_resume.py resume     # continue an interrupted run (renders only missing chunks)
kaggle kernels logs -f nitesh1230/convolution-explained-4k-render   # live log while running
```

## If it stops early

* The runner stops starting new chunks after 11 h 15 min, so the run ends cleanly before
  Kaggle's 12 h limit and everything finished so far is saved to Output.
* Every chunk is verified (exact frame count and 3840x2160) before it counts as done;
  a chunk cut off mid-render is discarded, never kept as finished.
* `resume` downloads the Output, publishes the finished chunks as the private dataset
  `nitesh1230/convolution-explained-4k-progress`, attaches it to the kernel and pushes a new
  version. The new run adopts those chunks and renders only what is missing, then assembles
  the chapters and the final video.

## Changing the video later

Edit the scenes, then rebuild and re-upload the bundle:

```bash
FC_MANIM_4K=1 python -c "import sys; sys.path.insert(0,'.'); from scenes import ch1_sliding as m; print(m.manim_clip().directory)"
python kaggle/build_bundle.py --manim-dir <folder printed above>
kaggle datasets version -p kaggle/dataset -m "update"
kaggle kernels push -p kaggle/kernel
```

(Old chunks are only valid for unchanged scenes; do not attach the progress dataset after editing visuals.)
