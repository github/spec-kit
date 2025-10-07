"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
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
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var tool_exports = {};
__export(tool_exports, {
  toMcpTool: () => toMcpTool
});
module.exports = __toCommonJS(tool_exports);
var import_bundle = require("./bundle");
function toMcpTool(tool) {
  return {
    name: tool.name,
    description: tool.description,
    inputSchema: (0, import_bundle.zodToJsonSchema)(tool.inputSchema, { strictUnions: true }),
    annotations: {
      title: tool.title,
      readOnlyHint: tool.type === "readOnly",
      destructiveHint: tool.type === "destructive",
      openWorldHint: true
    }
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  toMcpTool
});
