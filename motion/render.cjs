// Render the reel HTML to MP4 (or stills) with headless Chromium + ffmpeg.
//   node motion/render.cjs exports/control-reel.html exports/control-reel.mp4 [samples]
//   node motion/render.cjs exports/control-reel.html --stills out_dir 0.4,1.6,3.0 [samples]
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const { chromium } = require("playwright");

(async () => {
  const [html, out, ...rest] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 2100 } });
  page.on("pageerror", e => console.error("pageerror:", e.message));
  await page.addInitScript(() => { window.__EXPORT__ = true; });
  await page.goto("file://" + path.resolve(html));
  await page.evaluate(() => window.REEL.ready);
  const grab = (f, s) => page.evaluate(([f, s]) => { window.REEL.renderFrame(f, s); return window.REEL.canvas.toDataURL("image/png"); }, [f, s]);
  const png = d => Buffer.from(d.slice(d.indexOf(",") + 1), "base64");

  if (out === "--stills") {
    const [dir, times, samples = "1"] = rest;
    fs.mkdirSync(dir, { recursive: true });
    for (const t of times.split(",").map(Number)) {
      const f = Math.round(t * 30);
      fs.writeFileSync(path.join(dir, `f${String(f).padStart(3, "0")}.png`), png(await grab(f, +samples)));
    }
    await browser.close();
    return;
  }

  const samples = +(rest[0] || 6);
  const { FRAMES, FPS } = await page.evaluate(() => ({ FRAMES: window.REEL.FRAMES, FPS: window.REEL.FPS }));
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error",
    "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "png", "-i", "-",
    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
    "-shortest", "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-profile:v", "high", "-pix_fmt", "yuv420p",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
  const t0 = Date.now();
  for (let f = 0; f < FRAMES; f++) {
    const buf = png(await grab(f, samples));
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (f % 60 === 0) console.log(`frame ${f}/${FRAMES}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await browser.close();
  console.log(`done ${out} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
})();
