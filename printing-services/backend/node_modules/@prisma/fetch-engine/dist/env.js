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
var env_exports = {};
__export(env_exports, {
  allEngineEnvVarsSet: () => import_chunk_PXQVM7NP.allEngineEnvVarsSet,
  deprecatedEnvVarMap: () => import_chunk_PXQVM7NP.deprecatedEnvVarMap,
  engineEnvVarMap: () => import_chunk_PXQVM7NP.engineEnvVarMap,
  getBinaryEnvVarPath: () => import_chunk_PXQVM7NP.getBinaryEnvVarPath
});
module.exports = __toCommonJS(env_exports);
var import_chunk_PXQVM7NP = require("./chunk-PXQVM7NP.js");
var import_chunk_X37PZICB = require("./chunk-X37PZICB.js");
var import_chunk_AH6QHEOA = require("./chunk-AH6QHEOA.js");
