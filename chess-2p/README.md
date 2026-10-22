# Pass & Play Chess

Two-player chess on one Android phone, fully offline, styled after chess.com.

## Features
- **Complete rules**: castling (incl. "not through check"), en passant, promotion picker,
  check, checkmate, stalemate. Verified with perft on the six standard test positions.
- **Automatic draws as on chess.com**: threefold repetition, 50-move rule,
  insufficient material (K v K, K+minor v K, K+minor v K+minor, same-colour bishops),
  plus draw by agreement and resignation.
- **Chess clocks**: Bullet, Blitz, Rapid presets, custom minutes + increment, or no clock.
  Time is measured from a monotonic timestamp, so it cannot drift. The clock starts after
  White's first move; the increment is added after each timed move; tenths of a second show
  below 20 s; flag-fall vs insufficient material is a draw (K+N+N still wins, as on chess.com);
  a move made after the flag fell is rejected.
- Clocks pause automatically when the app is left, and the game is saved and resumed.
- Move list with figurines, review (back/next), takeback, auto-flip / fixed / tabletop board,
  5 board themes, legal-move dots, captured pieces and material count, PGN export with `%clk`.
- **Ayman**: player 1 is Ayman with his photo; at the start of each game Ayman greets you
  on screen and out loud (Android text-to-speech). Photos and names can be changed in
  Settings → Players (pick any picture from the gallery).

## Layout
| Path | What |
|---|---|
| `www/` | The game (HTML/CSS/JS, no dependencies). Also runs in a browser as an installable PWA. |
| `www/js/chess.js` | Rules engine |
| `android/` | WebView wrapper: manifest, `MainActivity.java`, icons, debug signing key |
| `build-apk.sh` | Builds `dist/PassAndPlayChess.apk` without Gradle |
| `test/engine.test.js` | Engine tests (`node test/engine.test.js`, `--deep` for big perft) |

## Build
```bash
sudo apt-get install aapt apksigner zipalign dalvik-exchange android-sdk-platform-23
./build-apk.sh          # -> dist/PassAndPlayChess.apk
```
The GitHub workflow `chess-apk.yml` runs the tests and builds the APK as a downloadable artifact.

The player photo `www/img/ayman.jpg` is kept out of git (this repo is public). Put it there before
building to bundle it; without it Ayman shows a letter avatar until a photo is picked in the app.
`android/debug.keystore` (password `android`) is a throwaway signing key, so that updated
APKs install over older ones and keep saved games.

## Install on the phone
Copy the APK to the phone, open it, and allow "Install unknown apps" for the app you opened it
with (Files, Chrome, ...) when Android asks.

Pieces: cburnett set by Colin M.L. Burnett (GPLv2+/BSD/CC BY-SA 3.0).
