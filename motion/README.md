# Soft Studio launch film

A 16-second, 4:5 launch film for the X feed. It uses the actual public dataset and the landing page’s neutral colors, regular sans-serif typography, white rounded controls, and soft ingredient artwork.

The deliverable is `site/launch/soft-studio-launch-x.mp4`. Watch it at <https://soft-studio-ingredients.vercel.app/launch>. The video plays only after the viewer chooses Play; sound is enabled and all essential information is also visible on screen.

## Edit and render

Install Python 3.12 and the packages in `motion/requirements.txt`, then run:

```powershell
python -m pip install -r motion/requirements.txt
python motion/render.py --stills  # contact sheet + full-size poster
python motion/render.py --draft   # 30 fps, half-resolution review export
python motion/render.py           # 1080 × 1350, 60 fps, final export
```

The renderer currently uses Windows Segoe UI from `C:/Windows/Fonts`. Outputs and inspection files go into the ignored `motion/output` folder. Copy the final MP4 and poster to `site/launch`, then run the normal site build.

## Timing

| Time        | Picture                                                                             | Sound                                           |
| ----------- | ----------------------------------------------------------------------------------- | ----------------------------------------------- |
| 0–2.7 s     | Three floating ingredients settle beneath the introductory title.                   | Warm plucks, soft taps, a restrained chord bed. |
| 2.7–6.4 s   | Three cards flip through 16 ingredient combinations, accelerating.                  | Frame-synchronized clicks over a light beat.    |
| 6.4–10.1 s  | The cards become the center of a continuous camera pullback.                        | An airy swell opens into the reveal.            |
| 10.1–12.2 s | All 520 unique ingredients are visible in a 26 × 20 grid.                           | A short four-note resolution.                   |
| 12.2–16 s   | A rounded end card: “All 520. All free.” Site URL and CC BY 4.0 credit requirement. | Final chord with a clean tail.                  |

`soundtrack.py` synthesizes the original stereo score and effects from oscillators and noise. There are no third-party music recordings or audio samples. The mix is mastered near −16 LUFS without clipping.

The final export uses H.264 High, 4:2:0, AAC-LC stereo at 48 kHz, and a front-loaded MP4 index for quick playback. These codecs follow [X’s published video specifications](https://help.x.com/en/business-and-advertising/creative-ad-specifications); the 16-second file is within [standard account duration and size limits](https://help.x.com/en/using-x/x-videos).

The artwork remains licensed under CC BY 4.0. The movie does not alter any of the 520 source images or the dataset release.
