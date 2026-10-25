// Render every studio shot to raw/<name>.png (transparent). usage: node shoot.cjs [name ...]
const path = require("path"), fs = require("fs");
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  const p = await b.newPage({ viewport: { width: 1300, height: 1300 } });
  p.on("pageerror", e => console.error("pageerror:", e.message)); p.on("console", m => m.type() === "error" && console.error(m.text()));
  await p.goto("file://" + path.resolve(__dirname, "studio.html")); await p.waitForFunction(() => window.ready);
  const names = process.argv.slice(2).length ? process.argv.slice(2) : await p.evaluate(() => window.SHOT_NAMES);
  fs.mkdirSync(path.join(__dirname, "raw"), { recursive: true });
  for (const n of names) { const d = await p.evaluate(n => window.shoot(n), n); fs.writeFileSync(path.join(__dirname, "raw", n + ".png"), Buffer.from(d.split(",")[1], "base64")); process.stdout.write(n + " "); }
  await b.close(); console.log();
})();
