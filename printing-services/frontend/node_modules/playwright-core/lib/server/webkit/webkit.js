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
var webkit_exports = {};
__export(webkit_exports, {
  WebKit: () => WebKit
});
module.exports = __toCommonJS(webkit_exports);
var import_path = __toESM(require("path"));
var import_wkConnection = require("./wkConnection");
var import_ascii = require("../utils/ascii");
var import_browserType = require("../browserType");
var import_wkBrowser = require("../webkit/wkBrowser");
class WebKit extends import_browserType.BrowserType {
  constructor(parent) {
    super(parent, "webkit");
  }
  connectToTransport(transport, options) {
    return import_wkBrowser.WKBrowser.connect(this.attribution.playwright, transport, options);
  }
  amendEnvironment(env, userDataDir, isPersistent) {
    return {
      ...env,
      CURL_COOKIE_JAR_PATH: process.platform === "win32" && isPersistent ? import_path.default.join(userDataDir, "cookiejar.db") : void 0
    };
  }
  doRewriteStartupLog(error) {
    if (!error.logs)
      return error;
    if (error.logs.includes("Failed to open display") || error.logs.includes("cannot open display"))
      error.logs = "\n" + (0, import_ascii.wrapInASCIIBox)(import_browserType.kNoXServerRunningError, 1);
    return error;
  }
  attemptToGracefullyCloseBrowser(transport) {
    transport.send({ method: "Playwright.close", params: {}, id: import_wkConnection.kBrowserCloseMessageId });
  }
  defaultArgs(options, isPersistent, userDataDir) {
    const { args = [], headless } = options;
    const userDataDirArg = args.find((arg) => arg.startsWith("--user-data-dir"));
    if (userDataDirArg)
      throw this._createUserDataDirArgMisuseError("--user-data-dir");
    if (args.find((arg) => !arg.startsWith("-")))
      throw new Error("Arguments can not specify page to be opened");
    const webkitArguments = ["--inspector-pipe"];
    if (process.platform === "win32")
      webkitArguments.push("--disable-accelerated-compositing");
    if (headless)
      webkitArguments.push("--headless");
    if (isPersistent)
      webkitArguments.push(`--user-data-dir=${userDataDir}`);
    else
      webkitArguments.push(`--no-startup-window`);
    const proxy = options.proxyOverride || options.proxy;
    if (proxy) {
      if (process.platform === "darwin") {
        webkitArguments.push(`--proxy=${proxy.server}`);
        if (proxy.bypass)
          webkitArguments.push(`--proxy-bypass-list=${proxy.bypass}`);
      } else if (process.platform === "linux") {
        webkitArguments.push(`--proxy=${proxy.server}`);
        if (proxy.bypass)
          webkitArguments.push(...proxy.bypass.split(",").map((t) => `--ignore-host=${t}`));
      } else if (process.platform === "win32") {
        webkitArguments.push(`--curl-proxy=${proxy.server.replace(/^socks5:\/\//, "socks5h://")}`);
        if (proxy.bypass)
          webkitArguments.push(`--curl-noproxy=${proxy.bypass}`);
      }
    }
    webkitArguments.push(...args);
    if (isPersistent)
      webkitArguments.push("about:blank");
    return webkitArguments;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  WebKit
});
