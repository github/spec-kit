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
var bidiDeserializer_exports = {};
__export(bidiDeserializer_exports, {
  BidiDeserializer: () => BidiDeserializer
});
module.exports = __toCommonJS(bidiDeserializer_exports);
/**
 * @license
 * Copyright 2024 Google Inc.
 * Modifications copyright (c) Microsoft Corporation.
 * SPDX-License-Identifier: Apache-2.0
 */
class BidiDeserializer {
  static deserialize(result) {
    if (!result)
      return void 0;
    switch (result.type) {
      case "array":
        return result.value?.map((value) => {
          return BidiDeserializer.deserialize(value);
        });
      case "set":
        return result.value?.reduce((acc, value) => {
          return acc.add(BidiDeserializer.deserialize(value));
        }, /* @__PURE__ */ new Set());
      case "object":
        return result.value?.reduce((acc, tuple) => {
          const { key, value } = BidiDeserializer._deserializeTuple(tuple);
          acc[key] = value;
          return acc;
        }, {});
      case "map":
        return result.value?.reduce((acc, tuple) => {
          const { key, value } = BidiDeserializer._deserializeTuple(tuple);
          return acc.set(key, value);
        }, /* @__PURE__ */ new Map());
      case "promise":
        return {};
      case "regexp":
        return new RegExp(result.value.pattern, result.value.flags);
      case "date":
        return new Date(result.value);
      case "undefined":
        return void 0;
      case "null":
        return null;
      case "number":
        return BidiDeserializer._deserializeNumber(result.value);
      case "bigint":
        return BigInt(result.value);
      case "boolean":
        return Boolean(result.value);
      case "string":
        return result.value;
    }
    throw new Error(`Deserialization of type ${result.type} not supported.`);
  }
  static _deserializeNumber(value) {
    switch (value) {
      case "-0":
        return -0;
      case "NaN":
        return NaN;
      case "Infinity":
        return Infinity;
      case "-Infinity":
        return -Infinity;
      default:
        return value;
    }
  }
  static _deserializeTuple([serializedKey, serializedValue]) {
    const key = typeof serializedKey === "string" ? serializedKey : BidiDeserializer.deserialize(serializedKey);
    const value = BidiDeserializer.deserialize(serializedValue);
    return { key, value };
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  BidiDeserializer
});
