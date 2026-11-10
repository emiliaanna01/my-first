# D.B. Cooper stick-figure reel (15 scenes, ~76 s, 9:16)
```sh
python3 vo.py <kokoro_model_dir> <vo_dir>                 # voice B: British male narrator
python3 ../anderson/words.py <vo_dir> vo.json             # word onsets for the captions
python3 assemble.py clips/video_cap.mp4                   # fit scenes to the narration, cream/gold one-word captions, numbers as figures
python3 audio.py <vo_dir> mix.wav                         # dark mystery score + rain/thunder/jet SFX + mix (needs earshot)
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.2:LRA=11 -c:a aac -b:a 192k soundtrack.m4a
ffmpeg -i clips/video_cap.mp4 -i soundtrack.m4a -map 0:v -map 1:a -c:v libx264 -crf 21 -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart ../../exports/cooper-reel.mp4
```
