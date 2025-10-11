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
var transport_exports = {};
__export(transport_exports, {
  start: () => start
});
module.exports = __toCommonJS(transport_exports);
var import_assert = __toESM(require("assert"));
var import_http = __toESM(require("http"));
var import_crypto = __toESM(require("crypto"));
var import_utilsBundle = require("playwright-core/lib/utilsBundle");
var mcpBundle = __toESM(require("./bundle"));
var mcpServer = __toESM(require("./server"));
async function start(serverBackendFactory, options) {
  if (options.port !== void 0) {
    const httpServer = await startHttpServer(options);
    startHttpTransport(httpServer, serverBackendFactory);
  } else {
    await startStdioTransport(serverBackendFactory);
  }
}
async function startStdioTransport(serverBackendFactory) {
  await mcpServer.connect(serverBackendFactory, new mcpBundle.StdioServerTransport(), false);
}
const testDebug = (0, import_utilsBundle.debug)("pw:mcp:test");
async function handleSSE(serverBackendFactory, req, res, url, sessions) {
  if (req.method === "POST") {
    const sessionId = url.searchParams.get("sessionId");
    if (!sessionId) {
      res.statusCode = 400;
      return res.end("Missing sessionId");
    }
    const transport = sessions.get(sessionId);
    if (!transport) {
      res.statusCode = 404;
      return res.end("Session not found");
    }
    return await transport.handlePostMessage(req, res);
  } else if (req.method === "GET") {
    const transport = new mcpBundle.SSEServerTransport("/sse", res);
    sessions.set(transport.sessionId, transport);
    testDebug(`create SSE session: ${transport.sessionId}`);
    await mcpServer.connect(serverBackendFactory, transport, false);
    res.on("close", () => {
      testDebug(`delete SSE session: ${transport.sessionId}`);
      sessions.delete(transport.sessionId);
    });
    return;
  }
  res.statusCode = 405;
  res.end("Method not allowed");
}
async function handleStreamable(serverBackendFactory, req, res, sessions) {
  const sessionId = req.headers["mcp-session-id"];
  if (sessionId) {
    const transport = sessions.get(sessionId);
    if (!transport) {
      res.statusCode = 404;
      res.end("Session not found");
      return;
    }
    return await transport.handleRequest(req, res);
  }
  if (req.method === "POST") {
    const transport = new mcpBundle.StreamableHTTPServerTransport({
      sessionIdGenerator: () => import_crypto.default.randomUUID(),
      onsessioninitialized: async (sessionId2) => {
        testDebug(`create http session: ${transport.sessionId}`);
        await mcpServer.connect(serverBackendFactory, transport, true);
        sessions.set(sessionId2, transport);
      }
    });
    transport.onclose = () => {
      if (!transport.sessionId)
        return;
      sessions.delete(transport.sessionId);
      testDebug(`delete http session: ${transport.sessionId}`);
    };
    await transport.handleRequest(req, res);
    return;
  }
  res.statusCode = 400;
  res.end("Invalid request");
}
function startHttpTransport(httpServer, serverBackendFactory) {
  const sseSessions = /* @__PURE__ */ new Map();
  const streamableSessions = /* @__PURE__ */ new Map();
  httpServer.on("request", async (req, res) => {
    const url2 = new URL(`http://localhost${req.url}`);
    if (url2.pathname.startsWith("/sse"))
      await handleSSE(serverBackendFactory, req, res, url2, sseSessions);
    else
      await handleStreamable(serverBackendFactory, req, res, streamableSessions);
  });
  const url = httpAddressToString(httpServer.address());
  const message = [
    `Listening on ${url}`,
    "Put this in your client config:",
    JSON.stringify({
      "mcpServers": {
        "playwright": {
          "url": `${url}/mcp`
        }
      }
    }, void 0, 2),
    "For legacy SSE transport support, you can use the /sse endpoint instead."
  ].join("\n");
  console.error(message);
}
async function startHttpServer(config) {
  const { host, port } = config;
  const httpServer = import_http.default.createServer();
  await new Promise((resolve, reject) => {
    httpServer.on("error", reject);
    httpServer.listen(port, host, () => {
      resolve();
      httpServer.removeListener("error", reject);
    });
  });
  return httpServer;
}
function httpAddressToString(address) {
  (0, import_assert.default)(address, "Could not bind server socket");
  if (typeof address === "string")
    return address;
  const resolvedPort = address.port;
  let resolvedHost = address.family === "IPv4" ? address.address : `[${address.address}]`;
  if (resolvedHost === "0.0.0.0" || resolvedHost === "[::]")
    resolvedHost = "localhost";
  return `http://${resolvedHost}:${resolvedPort}`;
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  start
});
