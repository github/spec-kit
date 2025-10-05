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

// src/usePrefetchInfiniteQuery.tsx
var usePrefetchInfiniteQuery_exports = {};
__export(usePrefetchInfiniteQuery_exports, {
  usePrefetchInfiniteQuery: () => usePrefetchInfiniteQuery
});
module.exports = __toCommonJS(usePrefetchInfiniteQuery_exports);
var import_QueryClientProvider = require("./QueryClientProvider.cjs");
function usePrefetchInfiniteQuery(options, queryClient) {
  const client = (0, import_QueryClientProvider.useQueryClient)(queryClient);
  if (!client.getQueryState(options.queryKey)) {
    client.prefetchInfiniteQuery(options);
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  usePrefetchInfiniteQuery
});
//# sourceMappingURL=usePrefetchInfiniteQuery.cjs.map