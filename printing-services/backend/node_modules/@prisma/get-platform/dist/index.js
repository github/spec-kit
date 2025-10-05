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
var dist_exports = {};
__export(dist_exports, {
  assertNodeAPISupported: () => import_chunk_O5EOXX3N.assertNodeAPISupported,
  binaryTargets: () => import_chunk_7MLUNQIZ.binaryTargets,
  getBinaryTargetForCurrentPlatform: () => import_chunk_YDM7ULQH.getBinaryTargetForCurrentPlatform,
  getNodeAPIName: () => import_chunk_2U36ISZO.getNodeAPIName,
  getPlatformInfo: () => import_chunk_YDM7ULQH.getPlatformInfo,
  getos: () => import_chunk_YDM7ULQH.getos,
  jestConsoleContext: () => import_chunk_M5NKJZ76.jestConsoleContext,
  jestContext: () => import_chunk_M5NKJZ76.jestContext,
  jestProcessContext: () => import_chunk_M5NKJZ76.jestProcessContext,
  link: () => import_chunk_D7S5FGQN.link
});
module.exports = __toCommonJS(dist_exports);
var import_chunk_6HZWON4S = require("./chunk-6HZWON4S.js");
var import_chunk_M5NKJZ76 = require("./chunk-M5NKJZ76.js");
var import_chunk_O5EOXX3N = require("./chunk-O5EOXX3N.js");
var import_chunk_2U36ISZO = require("./chunk-2U36ISZO.js");
var import_chunk_YDM7ULQH = require("./chunk-YDM7ULQH.js");
var import_chunk_D7S5FGQN = require("./chunk-D7S5FGQN.js");
var import_chunk_FWMN4WME = require("./chunk-FWMN4WME.js");
var import_chunk_YVXCXD3A = require("./chunk-YVXCXD3A.js");
var import_chunk_7MLUNQIZ = require("./chunk-7MLUNQIZ.js");
var import_chunk_2ESYSVXG = require("./chunk-2ESYSVXG.js");
(0, import_chunk_7MLUNQIZ.init_binaryTargets)();
