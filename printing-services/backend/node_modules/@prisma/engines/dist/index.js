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

// src/index.ts
var src_exports = {};
__export(src_exports, {
  DEFAULT_CLI_QUERY_ENGINE_BINARY_TYPE: () => DEFAULT_CLI_QUERY_ENGINE_BINARY_TYPE,
  enginesVersion: () => import_engines_version2.enginesVersion,
  ensureBinariesExist: () => ensureBinariesExist,
  getCliQueryEngineBinaryType: () => getCliQueryEngineBinaryType,
  getEnginesPath: () => getEnginesPath
});
module.exports = __toCommonJS(src_exports);
var import_debug = __toESM(require("@prisma/debug"));
var import_engines_version = require("@prisma/engines-version");
var import_fetch_engine = require("@prisma/fetch-engine");
var import_path = __toESM(require("path"));
var import_engines_version2 = require("@prisma/engines-version");
var debug = (0, import_debug.default)("prisma:engines");
function getEnginesPath() {
  return import_path.default.join(__dirname, "../");
}
var DEFAULT_CLI_QUERY_ENGINE_BINARY_TYPE = import_fetch_engine.BinaryType.QueryEngineLibrary;
function getCliQueryEngineBinaryType() {
  const envCliQueryEngineType = process.env.PRISMA_CLI_QUERY_ENGINE_TYPE;
  if (envCliQueryEngineType) {
    if (envCliQueryEngineType === "binary") {
      return import_fetch_engine.BinaryType.QueryEngineBinary;
    }
    if (envCliQueryEngineType === "library") {
      return import_fetch_engine.BinaryType.QueryEngineLibrary;
    }
  }
  return DEFAULT_CLI_QUERY_ENGINE_BINARY_TYPE;
}
async function ensureBinariesExist() {
  const binaryDir = import_path.default.join(__dirname, "../");
  let binaryTargets;
  if (process.env.PRISMA_CLI_BINARY_TARGETS) {
    binaryTargets = process.env.PRISMA_CLI_BINARY_TARGETS.split(",");
  }
  const cliQueryEngineBinaryType = getCliQueryEngineBinaryType();
  const binaries = {
    [cliQueryEngineBinaryType]: binaryDir,
    [import_fetch_engine.BinaryType.SchemaEngineBinary]: binaryDir
  };
  debug(`binaries to download ${Object.keys(binaries).join(", ")}`);
  await (0, import_fetch_engine.download)({
    binaries,
    showProgress: true,
    version: import_engines_version.enginesVersion,
    failSilent: false,
    binaryTargets
  });
}
import_path.default.join(__dirname, "../query-engine-darwin");
import_path.default.join(__dirname, "../query-engine-darwin-arm64");
import_path.default.join(__dirname, "../query-engine-debian-openssl-1.0.x");
import_path.default.join(__dirname, "../query-engine-debian-openssl-1.1.x");
import_path.default.join(__dirname, "../query-engine-debian-openssl-3.0.x");
import_path.default.join(__dirname, "../query-engine-linux-static-x64");
import_path.default.join(__dirname, "../query-engine-linux-static-arm64");
import_path.default.join(__dirname, "../query-engine-rhel-openssl-1.0.x");
import_path.default.join(__dirname, "../query-engine-rhel-openssl-1.1.x");
import_path.default.join(__dirname, "../query-engine-rhel-openssl-3.0.x");
import_path.default.join(__dirname, "../libquery_engine-darwin.dylib.node");
import_path.default.join(__dirname, "../libquery_engine-darwin-arm64.dylib.node");
import_path.default.join(__dirname, "../libquery_engine-debian-openssl-1.0.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-debian-openssl-1.1.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-debian-openssl-3.0.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-linux-arm64-openssl-1.0.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-linux-arm64-openssl-1.1.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-linux-arm64-openssl-3.0.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-linux-musl.so.node");
import_path.default.join(__dirname, "../libquery_engine-linux-musl-openssl-3.0.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-rhel-openssl-1.0.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-rhel-openssl-1.1.x.so.node");
import_path.default.join(__dirname, "../libquery_engine-rhel-openssl-3.0.x.so.node");
import_path.default.join(__dirname, "../query_engine-windows.dll.node");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  DEFAULT_CLI_QUERY_ENGINE_BINARY_TYPE,
  enginesVersion,
  ensureBinariesExist,
  getCliQueryEngineBinaryType,
  getEnginesPath
});
