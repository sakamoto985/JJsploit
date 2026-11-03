# The Russian Civil War — HNN Special Report (video)

A ~6-minute animated "TV news special" built from the Filipe & Miguel script
(studio anchor + field correspondent), rendered entirely from code.

**Final video:** `russian_civil_war_special_report.mp4` (1920×1080, 25 fps, AAC stereo)

## What's in it
- **Intro + 6 part title cards** (How it began · Reds vs. Whites · On the ground · The tide turns · Victory & a new state · The final word)
- **Illustrated studio** with an animated anchor (Filipe) whose mouth moves with his voice, plus a video wall
- **Field reports** from Miguel in four painted locations (snowy town, burning village, Red Army camp, quiet street) with snow/ash, smoke, fire, marching soldiers, camera shake
- **Split-screen "two-box" live link**, including a "connecting…" satellite moment
- **Animated maps** (real country outlines, conic projection): Red heartland, railways with moving trains, foreign intervention arrows, fronts, divided White armies, the Red advance
- **Explainer graphics**: 1917, Bolsheviks/Lenin/Provisional Government, Reds vs. Whites, divided Whites, human cost, White defeats 1919–20, War Communism, USSR 1922, legacy timeline
- **Broadcast package**: logo bug, LIVE pill, speaker chip, headline bar, scrolling history ticker, burned-in captions
- **Sound**: two synthesized voices (Piper TTS), an original synthesized news theme, stingers, and field ambience (wind, distant gunfire, artillery, a church bell), ducked under the dialogue

## Rebuild
Requirements: Python 3 with Pillow + NumPy, ffmpeg, the Piper binary + voices
(`en-us-ryan-high`, `en-gb-alan-low`, from github.com/rhasspy/piper releases) and
the country outlines from github.com/johan/world.geo.json.

```bash
src/build_all.sh <piper_dir> <build_dir> <world.geo.json_dir> out.mp4 4
```

| File | Role |
|---|---|
| `src/script_data.py` | Script split into chunks, each tagged with the visual to show |
| `src/build_voice.py` | TTS per sentence, timing, lip-sync envelopes |
| `src/figures.py`, `src/scenes.py` | Characters, studio and field locations |
| `src/maps.py`, `src/gfx.py` | Animated maps and explainer graphics |
| `src/render.py` | Shot list, transitions, overlays, captions, frame output |
| `src/audio.py` | Music, stingers, ambience and final mix |
