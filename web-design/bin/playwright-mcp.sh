#!/usr/bin/env bash
# Playwright MCP. Uses the preinstalled Chromium in Claude cloud sessions; elsewhere Playwright picks its own browser.
args=(--headless --isolated)
[ -x /opt/pw-browsers/chromium ] && args+=(--executable-path /opt/pw-browsers/chromium)
exec npx -y @playwright/mcp@latest "${args[@]}" "$@"
