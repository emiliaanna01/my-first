#!/usr/bin/env bash
# Installs the video-editing toolchain (CPU only). Idempotent: safe to re-run.
set -euo pipefail
VENV=~/.venvs/video
MODELS=~/.cache/video-models
mkdir -p "$MODELS" ~/.fonts

[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$(dirname "$0")/requirements.txt"

get() { [ -s "$MODELS/$1" ] || curl -sSfL -o "$MODELS/$1" "$2"; }
# Background matting (RobustVideoMatting, ONNX)
get rvm_mobilenetv3_fp32.onnx https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
# MediaPipe: person/hair/clothes segmentation, hand tracking, face detection (auto-zoom, VFX anchoring)
MP=https://storage.googleapis.com/mediapipe-models
get selfie_multiclass.tflite $MP/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite
get hand_landmarker.task $MP/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
get face_detector.tflite $MP/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite

# Speech-to-text with word timestamps (GitHub-hosted; Hugging Face is not reachable here)
ASR=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
if [ ! -d "$MODELS/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8" ]; then   # English, best accuracy
  curl -sSfL "$ASR/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2" | tar xj -C "$MODELS"
fi
if [ ! -d "$MODELS/sherpa-onnx-whisper-small" ]; then                     # multilingual fallback
  curl -sSfL "$ASR/sherpa-onnx-whisper-small.tar.bz2" | tar xj -C "$MODELS"
  rm -f "$MODELS"/sherpa-onnx-whisper-small/small-{encoder,decoder}.onnx  # keep int8 only
fi

# Fonts: captions (Poppins) and retro serif titles (DM Serif Display)
for f in poppins/Poppins-ExtraBold.ttf poppins/Poppins-Bold.ttf dmserifdisplay/DMSerifDisplay-Regular.ttf dmserifdisplay/DMSerifDisplay-Italic.ttf; do
  [ -s ~/.fonts/"${f#*/}" ] || curl -sSfL -o ~/.fonts/"${f#*/}" "https://raw.githubusercontent.com/google/fonts/main/ofl/$f"
done
fc-cache -f >/dev/null 2>&1 || true

# IT Reelsmaker plugin extras: YuNet face model, rembg person model (where doctor.py looks), Remotion project
get face_detection_yunet_2023mar.onnx https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
if [ ! -s ~/.u2net/u2net_human_seg.onnx ]; then
  "$VENV/bin/rembg" d u2net_human_seg >/dev/null 2>&1 || true
  mkdir -p ~/.u2net && ln -sf ~/.rembg/models/u2net_human_seg/u2net_human_seg.onnx ~/.u2net/u2net_human_seg.onnx
fi
# Remotion can't download its browser here (remotion.media) and forces Chrome off the proxy;
# wrap the preinstalled headless shell so it renders and still reaches Google Fonts via the proxy.
mkdir -p ~/.local/bin
cat > ~/.local/bin/remotion-chrome <<'WRAP'
#!/bin/bash
args=()
for a in "$@"; do
  case "$a" in --no-proxy-server|--proxy-server=*|--proxy-bypass-list=*) ;; *) args+=("$a") ;; esac
done
[ -n "${HTTPS_PROXY:-}" ] && args+=("--proxy-server=$HTTPS_PROXY")
exec /opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell "${args[@]}"
WRAP
chmod +x ~/.local/bin/remotion-chrome
(cd "$(dirname "$0")/reels" && [ -d node_modules ] || npm install --no-fund --no-audit --silent)
echo "Video toolchain ready: source $VENV/bin/activate"
