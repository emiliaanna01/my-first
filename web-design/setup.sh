#!/usr/bin/env bash
# Installs / updates the web-design skills into .claude/skills from their upstream repos.
# Idempotent: safe to re-run. --extras also installs the uipro and Impeccable CLIs globally.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEST="$ROOT/.claude/skills"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$DEST"

clone() { git clone -q --depth 1 "https://github.com/$1" "$TMP/$2"; }
put() { rm -rf "$DEST/$(basename "$1")"; cp -rL "$1" "$DEST/"; }

clone anthropics/skills anthropic
for s in frontend-design web-artifacts-builder theme-factory canvas-design brand-guidelines webapp-testing; do
  put "$TMP/anthropic/skills/$s"
done

clone nextlevelbuilder/ui-ux-pro-max-skill uipro
for s in ui-ux-pro-max design-system ui-styling; do put "$TMP/uipro/.claude/skills/$s"; done
rm -rf "$DEST/ui-ux-pro-max/scripts/tests"

clone pbakaus/impeccable impeccable
put "$TMP/impeccable/.claude/skills/impeccable"

git clone -q --depth 1 --filter=blob:none --sparse https://github.com/shadcn-ui/ui "$TMP/shadcn"
git -C "$TMP/shadcn" sparse-checkout set skills
put "$TMP/shadcn/skills/shadcn"

clone greensock/gsap-skills gsap
for s in "$TMP"/gsap/skills/*/; do put "${s%/}"; done

clone addyosmani/web-quality-skills webq
for s in "$TMP"/webq/skills/*/; do put "${s%/}"; done

# Impeccable fetches its detector binary on first run; keep its anonymous usage data off.
"$DEST/impeccable/scripts/impeccable" telemetry off >/dev/null 2>&1 || true

if [ "${1:-}" = "--extras" ]; then
  npm install -g uipro-cli impeccable
fi

echo "Skills ready in $DEST:"
ls "$DEST" | tr '\n' ' '; echo
