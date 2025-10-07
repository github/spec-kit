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

// src/useMutationState.ts
var useMutationState_exports = {};
__export(useMutationState_exports, {
  useIsMutating: () => useIsMutating,
  useMutationState: () => useMutationState
});
module.exports = __toCommonJS(useMutationState_exports);
var React = __toESM(require("react"), 1);
var import_query_core = require("@tanstack/query-core");
var import_QueryClientProvider = require("./QueryClientProvider.cjs");
function useIsMutating(filters, queryClient) {
  const client = (0, import_QueryClientProvider.useQueryClient)(queryClient);
  return useMutationState(
    { filters: { ...filters, status: "pending" } },
    client
  ).length;
}
function getResult(mutationCache, options) {
  return mutationCache.findAll(options.filters).map(
    (mutation) => options.select ? options.select(mutation) : mutation.state
  );
}
function useMutationState(options = {}, queryClient) {
  const mutationCache = (0, import_QueryClientProvider.useQueryClient)(queryClient).getMutationCache();
  const optionsRef = React.useRef(options);
  const result = React.useRef(null);
  if (!result.current) {
    result.current = getResult(mutationCache, options);
  }
  React.useEffect(() => {
    optionsRef.current = options;
  });
  return React.useSyncExternalStore(
    React.useCallback(
      (onStoreChange) => mutationCache.subscribe(() => {
        const nextResult = (0, import_query_core.replaceEqualDeep)(
          result.current,
          getResult(mutationCache, optionsRef.current)
        );
        if (result.current !== nextResult) {
          result.current = nextResult;
          import_query_core.notifyManager.schedule(onStoreChange);
        }
      }),
      [mutationCache]
    ),
    () => result.current,
    () => result.current
  );
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useIsMutating,
  useMutationState
});
//# sourceMappingURL=useMutationState.cjs.map