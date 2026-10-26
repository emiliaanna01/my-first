#!/bin/bash
# Voice + ducked music -> mix_voice.wav (-14 LUFS). Also writes stems for checking.
set -e
F="[1:a]aformat=sample_rates=48000:channel_layouts=mono,highpass=f=90,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.2:g=2.5,acompressor=threshold=0.12:ratio=3:attack=5:release=120:makeup=1.5,volume=3dB,aformat=channel_layouts=stereo,asplit=3[vo][sc][vs];
[0:a]volume=-6dB,volume=enable='between(t,4.3,8.9)':volume=-4dB[mus];[mus][sc]sidechaincompress=threshold=0.03:ratio=3:attack=20:release=450:makeup=1,asplit=2[duck][ms];
[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]"
ffmpeg -v error -y -i ../composition/public/soundtrack.wav -i vo/voice.wav -filter_complex "$F" \
  -map "[out]" -ar 48000 mix_voice.wav -map "[ms]" stem_music.wav -map "[vs]" stem_voice.wav
