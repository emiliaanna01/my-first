#!/bin/bash
# Rebuilds everything that lives outside the repo when a cloud container starts fresh:
# the project plugins declared in .claude/settings.json, then the motion toolkit (motion/setup.sh).
# Skills need nothing: they are committed in .claude/skills. Idempotent and non-interactive.
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "$CLAUDE_PROJECT_DIR"

# Plugins: add each declared marketplace, install each enabled plugin that is missing
installed="$(claude plugin list 2>/dev/null || true)"
known="$(claude plugin marketplace list 2>/dev/null || true)"
python3 - .claude/settings.json <<'PY' | while IFS=$'\t' read -r kind a b; do
import json, sys
s = json.load(open(sys.argv[1]))
for name, m in s.get("extraKnownMarketplaces", {}).items():
    src = m["source"]
    print("market", name, src.get("repo") or src.get("path"), sep="\t")
for p, on in s.get("enabledPlugins", {}).items():
    if on: print("plugin", p, "-", sep="\t")
PY
  if [ "$kind" = market ]; then
    grep -q "> $a\$" <<<"$known" || claude plugin marketplace add "$b" --scope project >/dev/null 2>&1 \
      || echo "session-start: could not add marketplace $a" >&2
  else
    grep -q "> $a\$" <<<"$installed" || claude plugin install "$a" --scope project -y >/dev/null 2>&1 \
      || echo "session-start: could not install plugin $a" >&2
  fi
done

# Frameworks, Manim, Kokoro voice and reference repos
./motion/setup.sh

# Kokoro TTS on PATH for `hyperframes tts`
[ -n "${CLAUDE_ENV_FILE:-}" ] && echo 'export PATH="$HOME/.venvs/tts/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
exit 0
