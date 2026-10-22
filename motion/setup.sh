#!/usr/bin/env bash
# Installs the motion-design frameworks and reference repos. Idempotent: safe to re-run.
# Skills and plugins live in .claude/ and load on their own; this script only adds what they call.
#   FULL=1 ./motion/setup.sh   also clones the large example repos (Math-To-Manim, ~470 MB)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV=~/.venvs/manim

# Node frameworks: HyperFrames CLI, Remotion, Motion Canvas, Revideo, GSAP, Lottie, Three.js, skills CLI
(cd "$HERE" && npm install --no-audit --no-fund --loglevel=error)

# Manim Community Edition (used by the manim-* skills, math-to-manim and the manim-skill plugin)
# manimpango builds against Pango; LaTeX (MathTex) is optional and not installed here
if ! dpkg -s libpango1.0-dev >/dev/null 2>&1 && command -v apt-get >/dev/null; then
  apt-get install -y -qq libpango1.0-dev pkg-config >/dev/null || { apt-get update -qq && apt-get install -y -qq libpango1.0-dev pkg-config >/dev/null; }
fi
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q manim mcp

# Reference repos: prompts, toolkits, templates and the desktop MCP servers (see motion/MCP.md)
mkdir -p "$HERE/vendor"
clone() { [ -d "$HERE/vendor/${1#*/}" ] || git clone -q --depth 1 "https://github.com/$1" "$HERE/vendor/${1#*/}"; }
clone wilwaldon/Claude-Code-Video-Toolkit      # curated list of video skills and MCP servers
clone tonbistudio/hyperframes-prompts          # HyperFrames prompts from 5 test builds
clone digitalsamba/claude-code-video-toolkit   # project template: /video, /record-demo, /brand
clone frankxai/awesome-motion-design-agent-skills
clone NVIDIA/SkillSpector                      # scan a skill pack before installing it
clone dha-aa/ae-motion                         # After Effects MCP (desktop, needs AE)
clone ahujasid/blender-mcp                     # Blender MCP (desktop, needs Blender)
clone abhiemj/manim-mcp-server                 # Manim MCP (reference only, see motion/MCP.md)
clone motion-canvas/motion-canvas
clone redotvideo/revideo
if [ "${FULL:-0}" = 1 ]; then
  clone HarleyCoops/Math-To-Manim              # 55+ Manim examples
fi

echo "motion toolkit ready:"
echo "  hyperframes $(cd "$HERE" && npx --no-install hyperframes --version 2>/dev/null | tail -1)"
echo "  remotion    $(node -p "require('$HERE/node_modules/remotion/package.json').version")"
echo "  manim       $("$VENV/bin/manim" --version 2>/dev/null | head -1)"
