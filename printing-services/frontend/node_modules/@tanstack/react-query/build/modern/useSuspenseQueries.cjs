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

// src/useSuspenseQueries.ts
var useSuspenseQueries_exports = {};
__export(useSuspenseQueries_exports, {
  useSuspenseQueries: () => useSuspenseQueries
});
module.exports = __toCommonJS(useSuspenseQueries_exports);
var import_query_core = require("@tanstack/query-core");
var import_useQueries = require("./useQueries.cjs");
var import_suspense = require("./suspense.cjs");
function useSuspenseQueries(options, queryClient) {
  return (0, import_useQueries.useQueries)(
    {
      ...options,
      queries: options.queries.map((query) => {
        if (process.env.NODE_ENV !== "production") {
          if (query.queryFn === import_query_core.skipToken) {
            console.error("skipToken is not allowed for useSuspenseQueries");
          }
        }
        return {
          ...query,
          suspense: true,
          throwOnError: import_suspense.defaultThrowOnError,
          enabled: true,
          placeholderData: void 0
        };
      })
    },
    queryClient
  );
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useSuspenseQueries
});
//# sourceMappingURL=useSuspenseQueries.cjs.map