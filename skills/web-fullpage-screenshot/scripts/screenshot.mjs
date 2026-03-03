import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

function parseArgs(argv) {
  const args = {
    url: null,
    out: null,
    chrome: null,
    fullPage: false,
    viewport: "1366x768",
    deviceScaleFactor: 1,
    waitUntil: "networkidle2",
    timeoutMs: 60_000,
    scroll: false,
    scrollStep: 800,
    scrollDelayMs: 250,
    maxScrolls: 80,
    cookies: null,
    userAgent: null,
    headers: null,
    background: true,
    port: null,
    idleTimeMs: 800,
  };

  const it = argv[Symbol.iterator]();
  for (let token of it) {
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    switch (key) {
      case "url":
        args.url = it.next().value ?? null;
        break;
      case "out":
        args.out = it.next().value ?? null;
        break;
      case "chrome":
        args.chrome = it.next().value ?? null;
        break;
      case "port":
        args.port = Number(it.next().value ?? args.port);
        break;
      case "viewport":
        args.viewport = it.next().value ?? args.viewport;
        break;
      case "deviceScaleFactor":
        args.deviceScaleFactor = Number(it.next().value ?? args.deviceScaleFactor);
        break;
      case "waitUntil":
        args.waitUntil = it.next().value ?? args.waitUntil;
        break;
      case "timeoutMs":
        args.timeoutMs = Number(it.next().value ?? args.timeoutMs);
        break;
      case "idleTimeMs":
        args.idleTimeMs = Number(it.next().value ?? args.idleTimeMs);
        break;
      case "fullPage":
        args.fullPage = true;
        break;
      case "scroll":
        args.scroll = true;
        break;
      case "scrollStep":
        args.scrollStep = Number(it.next().value ?? args.scrollStep);
        break;
      case "scrollDelayMs":
        args.scrollDelayMs = Number(it.next().value ?? args.scrollDelayMs);
        break;
      case "maxScrolls":
        args.maxScrolls = Number(it.next().value ?? args.maxScrolls);
        break;
      case "cookies":
        args.cookies = it.next().value ?? null;
        break;
      case "userAgent":
        args.userAgent = it.next().value ?? null;
        break;
      case "headers":
        args.headers = it.next().value ?? null;
        break;
      case "transparent":
        args.background = false;
        break;
      case "help":
        printHelpAndExit(0);
        break;
      default:
        console.error(`Unknown flag: --${key}`);
        printHelpAndExit(2);
    }
  }

  return args;
}

function printHelpAndExit(code) {
  console.log(
    [
      "Usage:",
      "  node screenshot.mjs --url <URL> --out <PATH> [options]",
      "",
      "Options:",
      "  --fullPage                  Capture full page (default: viewport only)",
      "  --scroll                    Auto-scroll to trigger lazy-load",
      "  --cookies <cookies.json>     JSON array of cookies (Puppeteer format)",
      "  --chrome <path>             Chrome/Chromium executable path",
      "  --port 9222                 Remote debugging port (auto if omitted)",
      "  --viewport 1366x768         Viewport size",
      "  --deviceScaleFactor 1       Device scale factor",
      "  --waitUntil networkidle2    load|domcontentloaded|networkidle0|networkidle2",
      "  --timeoutMs 60000           Navigation timeout in ms",
      "  --idleTimeMs 800            Network idle window (networkidle*)",
      "  --headers <headers.json>    Extra HTTP headers (JSON object)",
      "  --userAgent <ua>            Override User-Agent",
      "  --transparent               Omit background (png only)",
      "  --help                      Show help",
    ].join("\n"),
  );
  process.exit(code);
}

function parseViewport(viewport) {
  const m = /^(\d+)x(\d+)$/.exec(viewport);
  if (!m) throw new Error(`Invalid --viewport '${viewport}', expected WIDTHxHEIGHT`);
  return { width: Number(m[1]), height: Number(m[2]) };
}

function fileExists(p) {
  try {
    fs.accessSync(p, fs.constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function findChromeExecutable(explicitPath) {
  if (explicitPath) return explicitPath;

  const candidates = [
    // macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    // Linux (common)
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ];

  for (const candidate of candidates) {
    if (fileExists(candidate)) return candidate;
  }

  return null;
}

function ensureParentDir(outPath) {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
}

function readJsonFile(p) {
  const raw = fs.readFileSync(p, "utf8");
  return JSON.parse(raw);
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function fetchJson(url, timeoutMs) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

function withTimeout(promise, timeoutMs, label) {
  let t;
  const timeout = new Promise((_, reject) => {
    t = setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms: ${label}`)), timeoutMs);
  });
  return Promise.race([promise.finally(() => clearTimeout(t)), timeout]);
}

class CdpClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
  }

  on(method, fn) {
    const arr = this.listeners.get(method) ?? [];
    arr.push(fn);
    this.listeners.set(method, arr);
  }

  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    await new Promise((resolve, reject) => {
      this.ws.addEventListener("open", resolve, { once: true });
      this.ws.addEventListener("error", reject, { once: true });
    });

    this.ws.addEventListener("message", (evt) => {
      const msg = JSON.parse(String(evt.data));
      if (typeof msg.id === "number") {
        const pending = this.pending.get(msg.id);
        if (!pending) return;
        this.pending.delete(msg.id);
        if (msg.error) pending.reject(new Error(`${msg.error.message ?? "CDP error"} (${msg.error.code ?? "?"})`));
        else pending.resolve(msg.result);
        return;
      }

      if (msg.method) {
        const arr = this.listeners.get(msg.method) ?? [];
        for (const fn of arr) fn(msg.params);
      }
    });
  }

  async close() {
    if (!this.ws) return;
    this.ws.close();
    this.ws = null;
  }

  send(method, params = {}) {
    if (!this.ws) throw new Error("CDP websocket is not connected");
    const id = this.nextId++;
    const payload = { id, method, params };
    this.ws.send(JSON.stringify(payload));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
}

function pickPort(explicitPort) {
  if (explicitPort && Number.isFinite(explicitPort)) return explicitPort;
  const base = 9222;
  const spread = 200;
  return base + Math.floor(Math.random() * spread);
}

async function waitForDebugPort(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  const url = `http://127.0.0.1:${port}/json/version`;
  while (Date.now() < deadline) {
    try {
      await fetchJson(url, 2_000);
      return;
    } catch {
      await sleep(100);
    }
  }
  throw new Error(`Chrome remote debugging not ready on port ${port}`);
}

async function createTarget(port, url, timeoutMs) {
  const createUrl = `http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`;
  return await withTimeout(fetchJson(createUrl, timeoutMs), timeoutMs, "createTarget");
}

function normalizeCookies(cookies, url) {
  if (!Array.isArray(cookies)) throw new Error("--cookies must be a JSON array");
  const origin = new URL(url).origin;
  return cookies.map((c) => (c && typeof c === "object" && !c.url ? { ...c, url: origin } : c));
}

async function autoScrollCdp(cdp, { step, delayMs, maxScrolls }) {
  const expression = `(async () => {
    const el = document.scrollingElement || document.documentElement;
    for (let i = 0; i < ${maxScrolls}; i++) {
      const before = el.scrollTop;
      el.scrollBy(0, ${step});
      await new Promise(r => setTimeout(r, ${delayMs}));
      const after = el.scrollTop;
      const max = el.scrollHeight - el.clientHeight;
      if (after === before || after >= max - 2) break;
    }
    return true;
  })()`;
  await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
}

async function waitUntilEvent(cdp, eventName, timeoutMs) {
  return await withTimeout(
    new Promise((resolve) => cdp.on(eventName, () => resolve())),
    timeoutMs,
    `wait ${eventName}`,
  );
}

async function waitForNetworkIdle(cdp, { maxInflight, idleTimeMs, timeoutMs }) {
  let inflight = 0;
  let idleTimer = null;
  let resolved = false;

  const done = new Promise((resolve, reject) => {
    const startIdleTimer = () => {
      if (idleTimer) return;
      idleTimer = setTimeout(() => {
        resolved = true;
        resolve();
      }, idleTimeMs);
    };
    const stopIdleTimer = () => {
      if (!idleTimer) return;
      clearTimeout(idleTimer);
      idleTimer = null;
    };

    cdp.on("Network.requestWillBeSent", () => {
      inflight += 1;
      if (inflight > maxInflight) stopIdleTimer();
    });
    const onDone = () => {
      inflight = Math.max(0, inflight - 1);
      if (inflight <= maxInflight) startIdleTimer();
    };
    cdp.on("Network.loadingFinished", onDone);
    cdp.on("Network.loadingFailed", onDone);

    startIdleTimer();

    setTimeout(() => {
      if (resolved) return;
      reject(new Error(`Timeout after ${timeoutMs}ms: waitForNetworkIdle(maxInflight=${maxInflight})`));
    }, timeoutMs);
  });

  await done;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.url || !args.out) printHelpAndExit(2);

  const url = new URL(args.url).toString();
  const outPath = path.resolve(args.out);
  ensureParentDir(outPath);

  const executablePath = findChromeExecutable(args.chrome);
  if (!executablePath) {
    console.error(
      [
        "Could not find a Chrome/Chromium executable.",
        "Install Google Chrome (recommended) or pass an explicit path:",
        "  node screenshot.mjs --chrome \"/path/to/chrome\" --url ... --out ...",
      ].join("\n"),
    );
    process.exit(2);
  }

  const viewport = parseViewport(args.viewport);

  const port = pickPort(args.port);
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "web-fullpage-screenshot-"));

  const chromeArgs = [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    "--headless=new",
    "--hide-scrollbars",
    "--mute-audio",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank",
  ];

  const chrome = spawn(executablePath, chromeArgs, { stdio: ["ignore", "pipe", "pipe"] });
  let chromeExited = false;
  let chromeExitCode = null;
  let chromeSignal = null;
  let chromeStderr = "";
  let chromeStdout = "";

  chrome.stdout?.on("data", (chunk) => {
    if (chromeStdout.length > 8192) return;
    chromeStdout += String(chunk);
  });
  chrome.stderr?.on("data", (chunk) => {
    if (chromeStderr.length > 8192) return;
    chromeStderr += String(chunk);
  });
  chrome.on("exit", (code, signal) => {
    chromeExited = true;
    chromeExitCode = code;
    chromeSignal = signal;
  });

  const cleanup = async () => {
    try {
      chrome.kill("SIGTERM");
    } catch {}
    await sleep(150);
    try {
      if (!chrome.killed) chrome.kill("SIGKILL");
    } catch {}
    try {
      fs.rmSync(userDataDir, { recursive: true, force: true });
    } catch {}
  };

  try {
    const portWaitMs = Math.min(10_000, args.timeoutMs);
    const portWait = (async () => {
      while (true) {
        if (chromeExited) {
          const detail = [
            "Chrome process exited before remote debugging became ready.",
            `Exit: code=${chromeExitCode} signal=${chromeSignal}`,
            chromeStderr.trim() ? `stderr:\n${chromeStderr.trim()}` : null,
            chromeStdout.trim() ? `stdout:\n${chromeStdout.trim()}` : null,
            "",
            "If you see 'Operation not permitted' errors, your environment may block binding localhost ports.",
            "In Codex, rerun the command outside the sandbox (require_escalated).",
          ]
            .filter(Boolean)
            .join("\n");
          throw new Error(detail);
        }
        try {
          await waitForDebugPort(port, 400);
          return;
        } catch {
          // keep polling
        }
        await sleep(100);
      }
    })();
    await withTimeout(portWait, portWaitMs, "waitForDebugPort");

    const target = await createTarget(port, url, Math.min(10_000, args.timeoutMs));
    if (!target?.webSocketDebuggerUrl) throw new Error("Failed to get webSocketDebuggerUrl from Chrome");

    const cdp = new CdpClient(target.webSocketDebuggerUrl);
    await cdp.connect();

    try {
      await cdp.send("Page.enable");
      await cdp.send("Runtime.enable");
      await cdp.send("Network.enable");

      await cdp.send("Emulation.setDeviceMetricsOverride", {
        width: viewport.width,
        height: viewport.height,
        deviceScaleFactor: args.deviceScaleFactor,
        mobile: false,
      });

      if (!args.background) {
        await cdp.send("Emulation.setDefaultBackgroundColorOverride", { color: { r: 0, g: 0, b: 0, a: 0 } });
      }

      if (args.userAgent) {
        await cdp.send("Network.setUserAgentOverride", { userAgent: args.userAgent });
      }

      if (args.headers) {
        const headers = readJsonFile(args.headers);
        await cdp.send("Network.setExtraHTTPHeaders", { headers });
      }

      if (args.cookies) {
        const cookies = normalizeCookies(readJsonFile(args.cookies), url);
        await cdp.send("Network.setCookies", { cookies });
      }

      await cdp.send("Page.navigate", { url });

      if (args.waitUntil === "domcontentloaded") {
        await waitUntilEvent(cdp, "Page.domContentEventFired", args.timeoutMs);
      } else if (args.waitUntil === "load") {
        await waitUntilEvent(cdp, "Page.loadEventFired", args.timeoutMs);
      } else if (args.waitUntil === "networkidle0") {
        await waitForNetworkIdle(cdp, {
          maxInflight: 0,
          idleTimeMs: args.idleTimeMs,
          timeoutMs: args.timeoutMs,
        });
      } else if (args.waitUntil === "networkidle2") {
        await waitForNetworkIdle(cdp, {
          maxInflight: 2,
          idleTimeMs: args.idleTimeMs,
          timeoutMs: args.timeoutMs,
        });
      } else {
        throw new Error(`Invalid --waitUntil '${args.waitUntil}'`);
      }

      if (args.scroll) {
        await autoScrollCdp(cdp, { step: args.scrollStep, delayMs: args.scrollDelayMs, maxScrolls: args.maxScrolls });
        await sleep(250);
      }

      let screenshotResult;
      if (args.fullPage) {
        try {
          screenshotResult = await cdp.send("Page.captureScreenshot", {
            format: "png",
            fromSurface: true,
            captureBeyondViewport: true,
          });
        } catch {
          const metrics = await cdp.send("Page.getLayoutMetrics");
          const cs = metrics?.contentSize;
          if (!cs?.width || !cs?.height) throw new Error("Failed to get contentSize for fullPage screenshot");
          screenshotResult = await cdp.send("Page.captureScreenshot", {
            format: "png",
            fromSurface: true,
            clip: { x: 0, y: 0, width: cs.width, height: cs.height, scale: 1 },
          });
        }
      } else {
        screenshotResult = await cdp.send("Page.captureScreenshot", { format: "png", fromSurface: true });
      }

      if (!screenshotResult?.data) throw new Error("Empty screenshot data");
      fs.writeFileSync(outPath, Buffer.from(screenshotResult.data, "base64"));
      console.log(`Saved: ${outPath}`);
    } finally {
      await cdp.close();
    }
  } finally {
    await cleanup();
  }
}

try {
  await main();
} catch (err) {
  const message = err && typeof err === "object" && "stack" in err ? err.stack : String(err);
  console.error(message);
  process.exit(1);
}
