#!/usr/bin/env node
// Full-page screenshots at desktop (1440) and phone (390) width, light or dark.
// Usage: node web-design/bin/shoot.cjs <url-or-file> [out-prefix] [--dark]
//   node web-design/bin/shoot.cjs web-design/starter/index.html out/starter
//   node web-design/bin/shoot.cjs https://example.com web-design/references/demo/example
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");

function loadPlaywright() {
  try { return require("playwright"); } catch {}
  const globalRoot = execSync("npm root -g").toString().trim();
  return require(path.join(globalRoot, "playwright"));
}

(async () => {
  const args = process.argv.slice(2);
  const dark = args.includes("--dark");
  const [target, prefix = "out/shot"] = args.filter((a) => !a.startsWith("--"));
  if (!target) { console.error("usage: shoot.cjs <url-or-file> [out-prefix] [--dark]"); process.exit(1); }

  const url = /^https?:|^file:/.test(target) ? target : "file://" + path.resolve(target);
  fs.mkdirSync(path.dirname(path.resolve(prefix)), { recursive: true });

  const { chromium } = loadPlaywright();
  const launch = { headless: true };
  if (fs.existsSync("/opt/pw-browsers/chromium")) launch.executablePath = "/opt/pw-browsers/chromium";
  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  // Local servers and files must not go through the outbound proxy (it only tunnels HTTPS).
  const local = /^(file:|https?:\/\/(localhost|127\.0\.0\.1|\[::1\])[:/])/.test(url);
  if (proxy && !local) launch.proxy = { server: proxy };
  const browser = await chromium.launch(launch);

  const sizes = { desktop: { width: 1440, height: 900 }, mobile: { width: 390, height: 844 } };
  for (const [name, viewport] of Object.entries(sizes)) {
    const page = await browser.newPage({
      viewport, colorScheme: dark ? "dark" : "light",
      deviceScaleFactor: name === "mobile" ? 2 : 1,
    });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(url, { waitUntil: "networkidle", timeout: 45000 }).catch((e) => errors.push(e.message));
    // Scroll through so scroll-triggered content reveals, then let animations settle.
    await page.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo({ top: y, behavior: "instant" }); await new Promise((r) => setTimeout(r, 120)); }
      window.scrollTo({ top: 0, behavior: "instant" });
    });
    await page.waitForTimeout(2500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    const file = `${prefix}-${name}${dark ? "-dark" : ""}.png`;
    await page.screenshot({ path: file, fullPage: true });
    console.log(`${file}${overflow ? "  WARNING: horizontal overflow" : ""}${errors.length ? "  errors: " + errors.join(" | ") : ""}`);
    await page.close();
  }
  await browser.close();
})();
