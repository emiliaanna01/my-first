# Motion MCP connectors

| Connector | Status | Why |
|---|---|---|
| Figma | **Installed** (`figma@claude-plugins-official`, project scope) | Bundles the remote Figma MCP and Figma's skills. Sign in once: `/mcp` → `figma` → Authenticate. |
| Playwright, Context7, 21st.dev Magic, Parallel search | Installed earlier (`.mcp.json`) | Page capture, current docs, UI/video blocks, research. |
| HeyGen, Higgsfield, ElevenLabs | **Run the commands below yourself** | Hosted servers with OAuth sign-in. Registering third-party endpoints was blocked by the auto-mode safety check, so you decide. |
| After Effects (AE Motion), Blender | **Desktop only** | They control an app running on your computer (After Effects / Blender), which a cloud container doesn't have. |
| Manim MCP (abhiemj) | **Not enabled** | Its `cleanup_manim_temp_dir` tool deletes any path the model passes, and it renders with `-p`, which needs a desktop player. Claude runs Manim directly through the `manim-*` skills instead. Source is in `motion/vendor/manim-mcp-server`. |

## Hosted connectors (OAuth, no API key stored in the repo)

Run in a terminal in this repo, then sign in with `/mcp` inside Claude Code. Drop `--scope project` to keep a
connector to yourself instead of committing it to `.mcp.json`.

```bash
claude mcp add --scope project --transport http heygen     https://mcp.heygen.com/mcp/v1/    # avatar videos, translation (credits)
claude mcp add --scope project --transport http higgsfield https://mcp.higgsfield.ai/mcp     # Seedance / Vibe Motion AI video (credits)
claude mcp add --scope project --transport http elevenlabs https://api.elevenlabs.io/v1/mcp  # voiceover, SFX, music (free tier: 10k credits/month)
```

On claude.ai or the Claude app, add the same URLs under Settings → Connectors → Add custom connector.

## Desktop connectors (your own computer)

**After Effects: AE Motion** (77 tools: comps, layers, keyframes, expressions, 3D camera, render). Needs AE 2022+ and Node 22.18+.
```bash
git clone https://github.com/dha-aa/ae-motion && cd ae-motion
bash scripts/install.sh            # macOS   (Windows: ./scripts/install.ps1)
claude mcp add ae-motion -- node "$(pwd)/dist/index.js"
```
Then open After Effects → Window → Extensions → AE Motion. The `run-ae-motion` skill is already in `.claude/skills/`.

**Blender: blender-mcp** (scene, materials, animation, render). Needs Blender 3.0+ and `uv`.
```bash
claude mcp add blender -- uvx blender-mcp
```
In Blender: Edit → Preferences → Add-ons → Install `addon.py` from https://github.com/ahujasid/blender-mcp,
enable "Interface: Blender MCP", then in the 3D view sidebar (N) → BlenderMCP → Connect.
Alternatives: `6xvl/blender-mcp` (~270 tools) or `MakerSully/blender-mcp` (read-only).
