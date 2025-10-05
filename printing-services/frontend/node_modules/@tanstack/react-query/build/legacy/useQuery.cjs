"use strict";
"use client";
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

// src/useQuery.ts
var useQuery_exports = {};
__export(useQuery_exports, {
  useQuery: () => useQuery
});
module.exports = __toCommonJS(useQuery_exports);
var import_query_core = require("@tanstack/query-core");
var import_useBaseQuery = require("./useBaseQuery.cjs");
function useQuery(options, queryClient) {
  return (0, import_useBaseQuery.useBaseQuery)(options, import_query_core.QueryObserver, queryClient);
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useQuery
});
//# sourceMappingURL=useQuery.cjs.map