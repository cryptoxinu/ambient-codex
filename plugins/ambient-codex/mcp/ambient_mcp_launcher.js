#!/usr/bin/env node
"use strict";

const { spawn, spawnSync } = require("child_process");
const path = require("path");

const MIN_PYTHON = "3.8";
const pluginRoot = path.resolve(__dirname, "..");
const serverPath = path.join(__dirname, "ambient_mcp.py");

function pythonCandidates() {
  const common = [
    { command: "python3", args: [] },
    { command: "python", args: [] },
  ];
  if (process.platform === "win32") {
    return [
      { command: "py", args: ["-3"] },
      ...common,
    ];
  }
  return common;
}

function candidateLabel(candidate) {
  return [candidate.command, ...candidate.args].join(" ");
}

function isUsablePython(candidate) {
  const probe = [
    ...candidate.args,
    "-c",
    "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)",
  ];
  const result = spawnSync(candidate.command, probe, {
    cwd: pluginRoot,
    stdio: "ignore",
    timeout: 5000,
    windowsHide: true,
  });
  return result.status === 0;
}

function selectPython() {
  return pythonCandidates().find(isUsablePython);
}

function exitForSignal(signal) {
  if (signal === "SIGINT") {
    return 130;
  }
  if (signal === "SIGTERM") {
    return 143;
  }
  return 1;
}

const selected = selectPython();
if (!selected) {
  const tried = pythonCandidates().map(candidateLabel).join(", ");
  console.error(
    `ambient MCP fatal error: Python ${MIN_PYTHON}+ not found; tried: ${tried}`
  );
  process.exit(127);
}

const child = spawn(
  selected.command,
  [...selected.args, "-u", serverPath, ...process.argv.slice(2)],
  {
    cwd: pluginRoot,
    env: process.env,
    stdio: "inherit",
    windowsHide: true,
  }
);

let childClosed = false;

function forwardSignal(signal) {
  if (!childClosed && !child.killed) {
    child.kill(signal);
  }
}

process.on("SIGINT", () => forwardSignal("SIGINT"));
process.on("SIGTERM", () => forwardSignal("SIGTERM"));

child.on("error", (error) => {
  console.error(`ambient MCP fatal error: unable to launch Python: ${error.message}`);
  process.exit(127);
});

child.on("close", (code, signal) => {
  childClosed = true;
  if (typeof code === "number") {
    process.exit(code);
  }
  process.exit(exitForSignal(signal));
});
