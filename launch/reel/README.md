# Round House launch film (Launchreel-style)

67.5 s, 1920×1080, built in HyperFrames from the site's own DOM. Structure follows Launchreel's films
(whatships.com/videos/launchreel, launchreel.so): hook → overflowing inbox → reveal on the music drop → the click →
floating features → stat band → orbit finale → end card.

| File | What it is |
|---|---|
| `film/renders/roundhouse-launch-film.mp4` | The film (−13.8 LUFS, −1 dBTP) |
| `film/build/vo.txt` | The script, one line per voice cue |
| `film/build/build.py` | Generates every scene and the audio mix (voice timings, ducking, effects) |
| `audition/roundhouse-voice-and-music-audition.mp4` | The voice and music audition reel used to choose |

**Voice:** Kokoro `af_heart` at 0.95× (free, on device), chosen from 6 voices.
**Music:** "Fresh Fit" by HoliznaCC0 (CC0, via SoundSafari/CC0-1.0-Music), chosen from 5 tracks. It starts at 3.0 s so its
drop (track 12.0 s) lands on the reveal at 15.0 s, and it is ducked to 35% under every voice line with a volume envelope.
**Effects:** Mixkit (via video-shotcraft), placed on visible actions, peaks one frame after the picture.

The inquiry/follow-up/file cards in the opening are illustrative; the 43.3 hours figure is the site calculator's own planning
estimate (20 h/week × 50% × 4.33 weeks), stated on screen.
