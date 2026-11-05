# Stick-figure money reel ("pay yourself first", 8 scenes, ~28 s, 9:16)
```sh
python3 vo.py <kokoro_model_dir> <vo_dir>                 # voice C: friendly relaxed male
python3 ../anderson/words.py <vo_dir> vo.json             # word onsets for the captions
python3 assemble.py clips/video_cap.mp4                   # cut to the lines, zoom wide shots, burn one-word captions
python3 audio.py <vo_dir> mix.wav                         # playful score + cartoon SFX + mix (needs earshot)
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.2:LRA=11 -c:a aac -b:a 192k soundtrack.m4a
ffmpeg -i clips/video_cap.mp4 -i soundtrack.m4a -map 0:v -map 1:a -c:v libx264 -crf 21 -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart ../../exports/money-reel.mp4
```
