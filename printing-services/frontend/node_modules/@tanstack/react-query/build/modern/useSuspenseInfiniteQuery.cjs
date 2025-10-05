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

// src/useSuspenseInfiniteQuery.ts
var useSuspenseInfiniteQuery_exports = {};
__export(useSuspenseInfiniteQuery_exports, {
  useSuspenseInfiniteQuery: () => useSuspenseInfiniteQuery
});
module.exports = __toCommonJS(useSuspenseInfiniteQuery_exports);
var import_query_core = require("@tanstack/query-core");
var import_useBaseQuery = require("./useBaseQuery.cjs");
var import_suspense = require("./suspense.cjs");
function useSuspenseInfiniteQuery(options, queryClient) {
  if (process.env.NODE_ENV !== "production") {
    if (options.queryFn === import_query_core.skipToken) {
      console.error("skipToken is not allowed for useSuspenseInfiniteQuery");
    }
  }
  return (0, import_useBaseQuery.useBaseQuery)(
    {
      ...options,
      enabled: true,
      suspense: true,
      throwOnError: import_suspense.defaultThrowOnError
    },
    import_query_core.InfiniteQueryObserver,
    queryClient
  );
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useSuspenseInfiniteQuery
});
//# sourceMappingURL=useSuspenseInfiniteQuery.cjs.map