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
var proxyBackend_exports = {};
__export(proxyBackend_exports, {
  ProxyBackend: () => ProxyBackend
});
module.exports = __toCommonJS(proxyBackend_exports);
var import_utilsBundle = require("playwright-core/lib/utilsBundle");
var mcpBundle = __toESM(require("./bundle"));
const errorsDebug = (0, import_utilsBundle.debug)("pw:mcp:errors");
class ProxyBackend {
  constructor(name, version, mcpProviders) {
    this._roots = [];
    this.name = name;
    this.version = version;
    this._mcpProviders = mcpProviders;
    this._contextSwitchTool = this._defineContextSwitchTool();
  }
  async initialize(clientVersion, roots) {
    this._roots = roots;
    await this._setCurrentClient(this._mcpProviders[0]);
  }
  async listTools() {
    const response = await this._currentClient.listTools();
    if (this._mcpProviders.length === 1)
      return response.tools;
    return [
      ...response.tools,
      this._contextSwitchTool
    ];
  }
  async callTool(name, args) {
    if (name === this._contextSwitchTool.name)
      return this._callContextSwitchTool(args);
    return await this._currentClient.callTool({
      name,
      arguments: args
    });
  }
  serverClosed() {
    void this._currentClient?.close().catch(errorsDebug);
  }
  async _callContextSwitchTool(params) {
    try {
      const factory = this._mcpProviders.find((factory2) => factory2.name === params.name);
      if (!factory)
        throw new Error("Unknown connection method: " + params.name);
      await this._setCurrentClient(factory);
      return {
        content: [{ type: "text", text: "### Result\nSuccessfully changed connection method.\n" }]
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `### Result
Error: ${error}
` }],
        isError: true
      };
    }
  }
  _defineContextSwitchTool() {
    return {
      name: "browser_connect",
      description: [
        "Connect to a browser using one of the available methods:",
        ...this._mcpProviders.map((factory) => `- "${factory.name}": ${factory.description}`)
      ].join("\n"),
      inputSchema: mcpBundle.zodToJsonSchema(mcpBundle.z.object({
        name: mcpBundle.z.enum(this._mcpProviders.map((factory) => factory.name)).default(this._mcpProviders[0].name).describe("The method to use to connect to the browser")
      }), { strictUnions: true }),
      annotations: {
        title: "Connect to a browser context",
        readOnlyHint: true,
        openWorldHint: false
      }
    };
  }
  async _setCurrentClient(factory) {
    await this._currentClient?.close();
    this._currentClient = void 0;
    const client = new mcpBundle.Client({ name: this.name, version: this.version });
    client.registerCapabilities({
      roots: {
        listRoots: true
      }
    });
    client.setRequestHandler(mcpBundle.ListRootsRequestSchema, () => ({ roots: this._roots }));
    client.setRequestHandler(mcpBundle.PingRequestSchema, () => ({}));
    const transport = await factory.connect();
    await client.connect(transport);
    this._currentClient = client;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ProxyBackend
});
