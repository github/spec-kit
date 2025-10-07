"use strict";
"use client";
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

// src/HydrationBoundary.tsx
var HydrationBoundary_exports = {};
__export(HydrationBoundary_exports, {
  HydrationBoundary: () => HydrationBoundary
});
module.exports = __toCommonJS(HydrationBoundary_exports);
var React = __toESM(require("react"), 1);
var import_query_core = require("@tanstack/query-core");
var import_QueryClientProvider = require("./QueryClientProvider.cjs");
var HydrationBoundary = ({
  children,
  options = {},
  state,
  queryClient
}) => {
  const client = (0, import_QueryClientProvider.useQueryClient)(queryClient);
  const optionsRef = React.useRef(options);
  optionsRef.current = options;
  const hydrationQueue = React.useMemo(() => {
    if (state) {
      if (typeof state !== "object") {
        return;
      }
      const queryCache = client.getQueryCache();
      const queries = state.queries || [];
      const newQueries = [];
      const existingQueries = [];
      for (const dehydratedQuery of queries) {
        const existingQuery = queryCache.get(dehydratedQuery.queryHash);
        if (!existingQuery) {
          newQueries.push(dehydratedQuery);
        } else {
          const hydrationIsNewer = dehydratedQuery.state.dataUpdatedAt > existingQuery.state.dataUpdatedAt || dehydratedQuery.promise && existingQuery.state.status !== "pending" && existingQuery.state.fetchStatus !== "fetching" && dehydratedQuery.dehydratedAt !== void 0 && dehydratedQuery.dehydratedAt > existingQuery.state.dataUpdatedAt;
          if (hydrationIsNewer) {
            existingQueries.push(dehydratedQuery);
          }
        }
      }
      if (newQueries.length > 0) {
        (0, import_query_core.hydrate)(client, { queries: newQueries }, optionsRef.current);
      }
      if (existingQueries.length > 0) {
        return existingQueries;
      }
    }
    return void 0;
  }, [client, state]);
  React.useEffect(() => {
    if (hydrationQueue) {
      (0, import_query_core.hydrate)(client, { queries: hydrationQueue }, optionsRef.current);
    }
  }, [client, hydrationQueue]);
  return children;
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  HydrationBoundary
});
//# sourceMappingURL=HydrationBoundary.cjs.map