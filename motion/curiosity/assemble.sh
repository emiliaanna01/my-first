#!/bin/sh
# Fix, upscale, speed up 1.3x (each 6 s clip -> 4.615 s = 2 bars at 104 BPM) and join the 10 scene clips, then mux the soundtrack.
# S09/S10: drop the 1-frame flash at the start. S08: crop its white card border (it grows as the card zooms).
set -e
cd "$(dirname "$0")"; mkdir -p clips
for i in 01 02 03 04 05 06 07 08 09 10; do
  pre=""; ss=""
  [ $i = 08 ] && pre="crop=656:1166:32:57,"
  { [ $i = 09 ] || [ $i = 10 ]; } && ss="-ss 0.0417"
  ffmpeg -loglevel error -y $ss -i video/S$i.mp4 -an -vf "${pre}scale=1080:1920:flags=lanczos,unsharp=5:5:0.5,setpts=PTS/1.3,fps=30,tpad=stop_mode=clone:stop_duration=0.2,trim=duration=4.6154,setpts=PTS-STARTPTS,format=yuv420p" -c:v libx264 -crf 14 -preset medium clips/S$i.mp4
done
printf "file 'clips/S%s.mp4'\n" 01 02 03 04 05 06 07 08 09 10 > list.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i list.txt -c copy video_cut.mp4
ffmpeg -loglevel error -y -i video_cut.mp4 -i soundtrack.m4a -map 0:v -map 1:a -vf tpad=stop_mode=clone:stop_duration=1.8 -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart ../../exports/phone-addiction-reel.mp4
