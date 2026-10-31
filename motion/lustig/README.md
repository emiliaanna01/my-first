# Jimmy Hoffa reel (28 clips, ~63 s, 9:16)
```sh
python3 vo.py <kokoro_model_dir> <vo_dir>        # voice A: British female storyteller; clip lengths follow the lines
python3 fix_s13.py                               # repaints the S13 tag 2:30 -> 2:15 PM (AP timeline)
python3 assemble.py <vo_dir> clips/video_cut.mp4 # cuts each 6 s clip to its line (animation window, up to 2x)
python3 audio.py <vo_dir> mix.wav                # noir score + paper sound design + mix (needs earshot)
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.2:LRA=11 -c:a aac -b:a 192k soundtrack.m4a
ffmpeg -i clips/video_cut.mp4 -i soundtrack.m4a -map 0:v -map 1:a -c:v libx264 -crf 21 -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart ../../exports/hoffa-reel.mp4
```
`thumbnail_fixed.jpg` / `exports/hoffa-cover.jpg`: "NEVER FOUUND" corrected to "NEVER FOUND".
