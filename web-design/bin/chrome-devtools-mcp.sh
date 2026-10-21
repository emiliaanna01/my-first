#!/usr/bin/env bash
# Chrome DevTools MCP (Lighthouse, performance traces, console, network). Usage statistics off.
args=(--headless --isolated --no-usage-statistics)
[ -x /opt/pw-browsers/chromium ] && args+=(--executablePath /opt/pw-browsers/chromium)
exec npx -y chrome-devtools-mcp@latest "${args[@]}" "$@"
