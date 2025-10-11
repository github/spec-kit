"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });
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
var __reExport = (target, mod, secondTarget) => (__copyProps(target, mod, "default"), secondTarget && __copyProps(secondTarget, mod, "default"));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/index.ts
var index_exports = {};
__export(index_exports, {
  getRecursionDetectionPlugin: () => getRecursionDetectionPlugin
});
module.exports = __toCommonJS(index_exports);

// src/configuration.ts
var recursionDetectionMiddlewareOptions = {
  step: "build",
  tags: ["RECURSION_DETECTION"],
  name: "recursionDetectionMiddleware",
  override: true,
  priority: "low"
};

// src/getRecursionDetectionPlugin.ts
var import_recursionDetectionMiddleware = require("././recursionDetectionMiddleware");
var getRecursionDetectionPlugin = /* @__PURE__ */ __name((options) => ({
  applyToStack: /* @__PURE__ */ __name((clientStack) => {
    clientStack.add((0, import_recursionDetectionMiddleware.recursionDetectionMiddleware)(), recursionDetectionMiddlewareOptions);
  }, "applyToStack")
}), "getRecursionDetectionPlugin");

// src/index.ts
__reExport(index_exports, require("././recursionDetectionMiddleware"), module.exports);
// Annotate the CommonJS export names for ESM import in node:

0 && (module.exports = {
  getRecursionDetectionPlugin,
  recursionDetectionMiddleware
});

