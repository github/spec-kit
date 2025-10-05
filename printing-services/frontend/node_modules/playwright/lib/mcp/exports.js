"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __reExport = (target, mod, secondTarget) => (__copyProps(target, mod, "default"), secondTarget && __copyProps(secondTarget, mod, "default"));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var exports_exports = {};
module.exports = __toCommonJS(exports_exports);
__reExport(exports_exports, require("./inProcessTransport.js"), module.exports);
__reExport(exports_exports, require("./proxyBackend.js"), module.exports);
__reExport(exports_exports, require("./server.js"), module.exports);
__reExport(exports_exports, require("./tool.js"), module.exports);
__reExport(exports_exports, require("./transport.js"), module.exports);
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ...require("./inProcessTransport.js"),
  ...require("./proxyBackend.js"),
  ...require("./server.js"),
  ...require("./tool.js"),
  ...require("./transport.js")
});
