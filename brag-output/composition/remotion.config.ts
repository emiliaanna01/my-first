import { Config } from "@remotion/cli/config";
import { existsSync } from "node:fs";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);
// Cloud sessions cannot download Remotion's browser; use the preinstalled headless shell.
const SHELL = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-linux/headless_shell";
const SHELL2 = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
if (existsSync(SHELL)) Config.setBrowserExecutable(SHELL);
else if (existsSync(SHELL2)) Config.setBrowserExecutable(SHELL2);
