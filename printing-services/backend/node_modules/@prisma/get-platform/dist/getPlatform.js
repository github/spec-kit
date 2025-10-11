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
var getPlatform_exports = {};
__export(getPlatform_exports, {
  computeLibSSLSpecificPaths: () => import_chunk_YDM7ULQH.computeLibSSLSpecificPaths,
  getArchFromUname: () => import_chunk_YDM7ULQH.getArchFromUname,
  getBinaryTargetForCurrentPlatform: () => import_chunk_YDM7ULQH.getBinaryTargetForCurrentPlatform,
  getBinaryTargetForCurrentPlatformInternal: () => import_chunk_YDM7ULQH.getBinaryTargetForCurrentPlatformInternal,
  getPlatformInfo: () => import_chunk_YDM7ULQH.getPlatformInfo,
  getPlatformInfoMemoized: () => import_chunk_YDM7ULQH.getPlatformInfoMemoized,
  getSSLVersion: () => import_chunk_YDM7ULQH.getSSLVersion,
  getos: () => import_chunk_YDM7ULQH.getos,
  parseDistro: () => import_chunk_YDM7ULQH.parseDistro,
  parseLibSSLVersion: () => import_chunk_YDM7ULQH.parseLibSSLVersion,
  parseOpenSSLVersion: () => import_chunk_YDM7ULQH.parseOpenSSLVersion,
  resolveDistro: () => import_chunk_YDM7ULQH.resolveDistro
});
module.exports = __toCommonJS(getPlatform_exports);
var import_chunk_YDM7ULQH = require("./chunk-YDM7ULQH.js");
var import_chunk_FWMN4WME = require("./chunk-FWMN4WME.js");
var import_chunk_YVXCXD3A = require("./chunk-YVXCXD3A.js");
var import_chunk_2ESYSVXG = require("./chunk-2ESYSVXG.js");
