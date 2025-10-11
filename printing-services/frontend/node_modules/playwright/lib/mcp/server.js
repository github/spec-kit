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
var server_exports = {};
__export(server_exports, {
  connect: () => connect,
  createServer: () => createServer
});
module.exports = __toCommonJS(server_exports);
var import_utilsBundle = require("playwright-core/lib/utilsBundle");
var mcpBundle = __toESM(require("./bundle"));
const serverDebug = (0, import_utilsBundle.debug)("pw:mcp:server");
const errorsDebug = (0, import_utilsBundle.debug)("pw:mcp:errors");
async function connect(serverBackendFactory, transport, runHeartbeat) {
  const backend = serverBackendFactory();
  const server = createServer(backend, runHeartbeat);
  await server.connect(transport);
}
function createServer(backend, runHeartbeat) {
  let initializedCallback = () => {
  };
  const initializedPromise = new Promise((resolve) => initializedCallback = resolve);
  const server = new mcpBundle.Server({ name: backend.name, version: backend.version }, {
    capabilities: {
      tools: {}
    }
  });
  server.setRequestHandler(mcpBundle.ListToolsRequestSchema, async () => {
    serverDebug("listTools");
    await initializedPromise;
    const tools = await backend.listTools();
    return { tools };
  });
  let heartbeatRunning = false;
  server.setRequestHandler(mcpBundle.CallToolRequestSchema, async (request) => {
    serverDebug("callTool", request);
    await initializedPromise;
    if (runHeartbeat && !heartbeatRunning) {
      heartbeatRunning = true;
      startHeartbeat(server);
    }
    try {
      return await backend.callTool(request.params.name, request.params.arguments || {});
    } catch (error) {
      return {
        content: [{ type: "text", text: "### Result\n" + String(error) }],
        isError: true
      };
    }
  });
  addServerListener(server, "initialized", async () => {
    try {
      const capabilities = server.getClientCapabilities();
      let clientRoots = [];
      if (capabilities?.roots) {
        const { roots } = await server.listRoots(void 0, { timeout: 2e3 }).catch(() => ({ roots: [] }));
        clientRoots = roots;
      }
      const clientVersion = server.getClientVersion() ?? { name: "unknown", version: "unknown" };
      await backend.initialize?.(clientVersion, clientRoots);
      initializedCallback();
    } catch (e) {
      errorsDebug(e);
    }
  });
  addServerListener(server, "close", () => backend.serverClosed?.());
  return server;
}
const startHeartbeat = (server) => {
  const beat = () => {
    Promise.race([
      server.ping(),
      new Promise((_, reject) => setTimeout(() => reject(new Error("ping timeout")), 5e3))
    ]).then(() => {
      setTimeout(beat, 3e3);
    }).catch(() => {
      void server.close();
    });
  };
  beat();
};
function addServerListener(server, event, listener) {
  const oldListener = server[`on${event}`];
  server[`on${event}`] = () => {
    oldListener?.();
    listener();
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  connect,
  createServer
});
