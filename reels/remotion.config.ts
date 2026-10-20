// Options: https://remotion.dev/docs/config (each one is also a CLI flag).
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// Cloud sessions cannot reach remotion.media: use the preinstalled headless shell via a proxy wrapper (setup.sh).
import { existsSync } from "node:fs";
const LOCAL_SHELL = "/root/.local/bin/remotion-chrome";
if (existsSync(LOCAL_SHELL)) Config.setBrowserExecutable(LOCAL_SHELL);
