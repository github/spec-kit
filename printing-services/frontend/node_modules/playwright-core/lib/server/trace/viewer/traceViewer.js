"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var traceViewer_exports = {};
__export(traceViewer_exports, {
  installRootRedirect: () => installRootRedirect,
  openTraceInBrowser: () => openTraceInBrowser,
  openTraceViewerApp: () => openTraceViewerApp,
  runTraceInBrowser: () => runTraceInBrowser,
  runTraceViewerApp: () => runTraceViewerApp,
  startTraceViewerServer: () => startTraceViewerServer
});
module.exports = __toCommonJS(traceViewer_exports);
var import_fs = __toESM(require("fs"));
var import_path = __toESM(require("path"));
var import_utils = require("../../../utils");
var import_utils2 = require("../../../utils");
var import_httpServer = require("../../utils/httpServer");
var import_utilsBundle = require("../../../utilsBundle");
var import_launchApp = require("../../launchApp");
var import_launchApp2 = require("../../launchApp");
var import_playwright = require("../../playwright");
var import_progress = require("../../progress");
function validateTraceUrls(traceUrls) {
  for (const traceUrl of traceUrls) {
    let traceFile = traceUrl;
    if (traceUrl.endsWith(".json"))
      traceFile = traceUrl.substring(0, traceUrl.length - ".json".length);
    if (!traceUrl.startsWith("http://") && !traceUrl.startsWith("https://") && !import_fs.default.existsSync(traceFile) && !import_fs.default.existsSync(traceFile + ".trace"))
      throw new Error(`Trace file ${traceUrl} does not exist!`);
  }
}
async function startTraceViewerServer(options) {
  const server = new import_httpServer.HttpServer();
  server.routePrefix("/trace", (request, response) => {
    const url = new URL("http://localhost" + request.url);
    const relativePath = url.pathname.slice("/trace".length);
    if (process.env.PW_HMR) {
      response.appendHeader("Access-Control-Allow-Origin", "http://localhost:44223");
    }
    if (relativePath.endsWith("/stall.js"))
      return true;
    if (relativePath.startsWith("/file")) {
      try {
        const filePath = url.searchParams.get("path");
        if (import_fs.default.existsSync(filePath))
          return server.serveFile(request, response, url.searchParams.get("path"));
        if (filePath.endsWith(".json")) {
          const traceName = filePath.substring(0, filePath.length - ".json".length);
          response.statusCode = 200;
          response.setHeader("Content-Type", "application/json");
          response.end(JSON.stringify(traceDescriptor(traceName)));
          return true;
        }
      } catch (e) {
      }
      response.statusCode = 404;
      response.end();
      return true;
    }
    const absolutePath = import_path.default.join(__dirname, "..", "..", "..", "vite", "traceViewer", ...relativePath.split("/"));
    return server.serveFile(request, response, absolutePath);
  });
  const transport = options?.transport || (options?.isServer ? new StdinServer() : void 0);
  if (transport)
    server.createWebSocket(transport);
  const { host, port } = options || {};
  await server.start({ preferredPort: port, host });
  return server;
}
async function installRootRedirect(server, traceUrls, options) {
  const params = new URLSearchParams();
  if (import_path.default.sep !== import_path.default.posix.sep)
    params.set("pathSeparator", import_path.default.sep);
  for (const traceUrl of traceUrls)
    params.append("trace", traceUrl);
  if (server.wsGuid())
    params.append("ws", server.wsGuid());
  if (options?.isServer)
    params.append("isServer", "");
  if ((0, import_utils2.isUnderTest)())
    params.append("isUnderTest", "true");
  for (const arg of options.args || [])
    params.append("arg", arg);
  if (options.grep)
    params.append("grep", options.grep);
  if (options.grepInvert)
    params.append("grepInvert", options.grepInvert);
  for (const project of options.project || [])
    params.append("project", project);
  for (const reporter of options.reporter || [])
    params.append("reporter", reporter);
  let baseUrl = ".";
  if (process.env.PW_HMR) {
    baseUrl = "http://localhost:44223";
    params.set("server", server.urlPrefix("precise"));
  }
  const urlPath = `${baseUrl}/trace/${options.webApp || "index.html"}?${params.toString()}`;
  server.routePath("/", (_, response) => {
    response.statusCode = 302;
    response.setHeader("Location", urlPath);
    response.end();
    return true;
  });
}
async function runTraceViewerApp(traceUrls, browserName, options, exitOnClose) {
  validateTraceUrls(traceUrls);
  const server = await startTraceViewerServer(options);
  await installRootRedirect(server, traceUrls, options);
  const page = await openTraceViewerApp(server.urlPrefix("precise"), browserName, options);
  if (exitOnClose)
    page.on("close", () => (0, import_utils.gracefullyProcessExitDoNotHang)(0));
  return page;
}
async function runTraceInBrowser(traceUrls, options) {
  validateTraceUrls(traceUrls);
  const server = await startTraceViewerServer(options);
  await installRootRedirect(server, traceUrls, options);
  await openTraceInBrowser(server.urlPrefix("human-readable"));
}
async function openTraceViewerApp(url, browserName, options) {
  const traceViewerPlaywright = (0, import_playwright.createPlaywright)({ sdkLanguage: "javascript", isInternalPlaywright: true });
  const traceViewerBrowser = (0, import_utils2.isUnderTest)() ? "chromium" : browserName;
  const { context, page } = await (0, import_launchApp2.launchApp)(traceViewerPlaywright[traceViewerBrowser], {
    sdkLanguage: traceViewerPlaywright.options.sdkLanguage,
    windowSize: { width: 1280, height: 800 },
    persistentContextOptions: {
      ...options?.persistentContextOptions,
      cdpPort: (0, import_utils2.isUnderTest)() ? 0 : void 0,
      headless: !!options?.headless,
      colorScheme: (0, import_utils2.isUnderTest)() ? "light" : void 0
    }
  });
  const controller = new import_progress.ProgressController();
  await controller.run(async (progress) => {
    await context._browser._defaultContext._loadDefaultContextAsIs(progress);
    if (process.env.PWTEST_PRINT_WS_ENDPOINT) {
      process.stderr.write("DevTools listening on: " + context._browser.options.wsEndpoint + "\n");
    }
    if (!(0, import_utils2.isUnderTest)())
      await (0, import_launchApp.syncLocalStorageWithSettings)(page, "traceviewer");
    if ((0, import_utils2.isUnderTest)())
      page.on("close", () => context.close({ reason: "Trace viewer closed" }).catch(() => {
      }));
    await page.mainFrame().goto(progress, url);
  });
  return page;
}
async function openTraceInBrowser(url) {
  console.log("\nListening on " + url);
  if (!(0, import_utils2.isUnderTest)())
    await (0, import_utilsBundle.open)(url.replace("0.0.0.0", "localhost")).catch(() => {
    });
}
class StdinServer {
  constructor() {
    process.stdin.on("data", (data) => {
      const url = data.toString().trim();
      if (url === this._traceUrl)
        return;
      if (url.endsWith(".json"))
        this._pollLoadTrace(url);
      else
        this._loadTrace(url);
    });
    process.stdin.on("close", () => (0, import_utils.gracefullyProcessExitDoNotHang)(0));
  }
  onconnect() {
  }
  async dispatch(method, params) {
    if (method === "initialize") {
      if (this._traceUrl)
        this._loadTrace(this._traceUrl);
    }
  }
  onclose() {
  }
  _loadTrace(traceUrl) {
    this._traceUrl = traceUrl;
    clearTimeout(this._pollTimer);
    this.sendEvent?.("loadTraceRequested", { traceUrl });
  }
  _pollLoadTrace(url) {
    this._loadTrace(url);
    this._pollTimer = setTimeout(() => {
      this._pollLoadTrace(url);
    }, 500);
  }
}
function traceDescriptor(traceName) {
  const result = {
    entries: []
  };
  const traceDir = import_path.default.dirname(traceName);
  const traceFile = import_path.default.basename(traceName);
  for (const name of import_fs.default.readdirSync(traceDir)) {
    if (name.startsWith(traceFile))
      result.entries.push({ name, path: import_path.default.join(traceDir, name) });
  }
  const resourcesDir = import_path.default.join(traceDir, "resources");
  if (import_fs.default.existsSync(resourcesDir)) {
    for (const name of import_fs.default.readdirSync(resourcesDir))
      result.entries.push({ name: "resources/" + name, path: import_path.default.join(resourcesDir, name) });
  }
  return result;
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  installRootRedirect,
  openTraceInBrowser,
  openTraceViewerApp,
  runTraceInBrowser,
  runTraceViewerApp,
  startTraceViewerServer
});
