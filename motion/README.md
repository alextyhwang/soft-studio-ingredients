# Soft Studio launch film

A nine-second edit for X. One ingredient at a time, accelerating hard cuts, a continuous pullback to all 520 images, and one final message. The pale gray background and regular black type match the landing page.

The deliverable is `site/launch/soft-studio-launch-x.mp4`. Watch it at <https://soft-studio-ingredients.vercel.app/launch>. Playback starts only after the viewer chooses Play, with sound enabled.

## Edit and render

Use Python 3.12 and the packages in `motion/requirements.txt`:

```powershell
python -m pip install -r motion/requirements.txt
python motion/render.py --stills
python motion/render.py --draft
python motion/render.py
```

The renderer uses Windows Segoe UI. It reads the original PNGs in `.release/originals` for the large ingredient shots when available, and the released WebPs for the grid. It crops transparent padding at draw time to keep the match cuts visually consistent. Source artwork files are unchanged.

Outputs go into the ignored `motion/output` directory. Copy the final MP4 and poster to `site/launch`, then run the site build.

## Edit points

| Time       | Picture                                                                                         | Sound                                                    |
| ---------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 0–3.4 s    | 23 ingredient shots at 167–150 ms per cut, with the last three inside the moving camera.        | Short, dry taps exactly on the cuts.                     |
| 3.08–6.2 s | Continuous pullback, with fruit swaps continuing across six nearby cells and gradually slowing. | A brushed sweep and increasingly sparse, quieter clicks. |
| 6.2–7.1 s  | All 520 unique ingredients, fully visible.                                                      | Soft low impact, then a pause.                           |
| 7.1–9 s    | Hard cut to “520 ingredients. Free.” with a small wordmark and license credit note.             | Closing tap and short decay.                             |

There is no text during the ingredient sequence. The frame contains only the artwork and background until the final card. No badges, controls, labels, or decorative panels.

The camera begins before the last cuts finish. Its initial image matches the close-up, and neighboring grid cells begin outside the frame. The logarithmic zoom uses [easeInOutSine](https://easings.net/#easeInOutSine) to accelerate and settle gently. Nearby grid images use the original PNGs throughout the move, avoiding a resolution change during the handoff.

During the pullback, eight staggered waves of cuts spread from the center into neighboring cells. The gaps grow from 167 ms to 617 ms, and the number of active cells tapers. All swaps stop at 5.98 seconds. Exchanges preserve the complete set of 520 unique ingredients; the settled grid is held still before the end card.

`soundtrack.py` synthesizes the sound effects. The soundtrack has no music bed, voiceover, or third-party recordings. The cut list is shared by the renderer and soundtrack so edits land on exact 60 fps frame boundaries.

The MP4 uses H.264 High, YUV 4:2:0, 1080 × 1350 at 60 fps, AAC-LC stereo at 48 kHz, and fast-start metadata. The artwork remains CC BY 4.0.
