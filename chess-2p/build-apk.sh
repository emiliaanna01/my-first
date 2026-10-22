#!/usr/bin/env bash
# Builds dist/PassAndPlayChess.apk from www/ (the game) and android/ (the wrapper)
# with the plain Android build tools, no Gradle needed. On Ubuntu 24.04:
#   sudo apt-get install aapt apksigner zipalign dalvik-exchange android-sdk-platform-23 openjdk-17-jdk-headless
set -euo pipefail
cd "$(dirname "$0")"

ANDROID_JAR=${ANDROID_JAR:-/usr/lib/android-sdk/platforms/android-23/android.jar}
DX=${DX:-/usr/lib/android-sdk/build-tools/debian/dx}
OUT=build
APK=dist/PassAndPlayChess.apk

rm -rf "$OUT"
mkdir -p "$OUT/gen" "$OUT/classes" "$OUT/assets" dist
cp -r www "$OUT/assets/www"
rm -f "$OUT/assets/www/sw.js"   # browser-only
if [ ! -f www/img/ayman.jpg ]; then
  echo "note: www/img/ayman.jpg not found; Ayman will show a letter avatar until a photo is picked in the app"
fi

echo "== resources"
aapt package -f -m -0 arsc -0 jpg -0 png \
  -M android/AndroidManifest.xml -S android/res -A "$OUT/assets" \
  -I "$ANDROID_JAR" -J "$OUT/gen" -F "$OUT/unsigned.apk"

echo "== java"
javac -nowarn -Xlint:-options -source 8 -target 8 -encoding UTF-8 \
  -bootclasspath "$ANDROID_JAR" -d "$OUT/classes" \
  "$OUT"/gen/com/chess2p/app/R.java android/src/com/chess2p/app/*.java

echo "== dex"
"$DX" --dex --min-sdk-version=21 --output="$OUT/classes.dex" "$OUT/classes"
(cd "$OUT" && aapt add -f unsigned.apk classes.dex >/dev/null)

echo "== align + sign"
zipalign -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
apksigner sign --ks android/debug.keystore --ks-pass pass:android --key-pass pass:android \
  --ks-key-alias androiddebugkey --out "$APK" "$OUT/aligned.apk"
apksigner verify --print-certs "$APK" | head -1
ls -l "$APK"
