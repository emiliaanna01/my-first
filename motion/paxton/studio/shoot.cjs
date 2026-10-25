// Render every period shot: raw/<name>.png (lit greyscale) and raw/<name>_id.png (material ids).
// usage: node shoot.cjs [name ...]
const path = require("path"), fs = require("fs");
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  const p = await b.newPage({ viewport: { width: 1300, height: 2200 } });
  p.on("pageerror", e => console.error("pageerror:", e.message));
  await p.goto("file://" + path.resolve(__dirname, "studio.html")); await p.waitForFunction(() => window.ready);
  const names = process.argv.slice(2).length ? process.argv.slice(2) : await p.evaluate(() => window.SHOT_NAMES);
  fs.mkdirSync(path.join(__dirname, "raw"), { recursive: true });
  for (const n of names) for (const pass of ["shade", "id"]) {
    const d = await p.evaluate(([n, pass]) => window.shoot(n, pass), [n, pass]);
    fs.writeFileSync(path.join(__dirname, "raw", n + (pass === "id" ? "_id" : "") + ".png"), Buffer.from(d.split(",")[1], "base64"));
  }
  await b.close(); console.log(names.join(" "));
})();
