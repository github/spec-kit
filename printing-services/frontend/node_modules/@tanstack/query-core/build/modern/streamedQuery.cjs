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

// src/streamedQuery.ts
var streamedQuery_exports = {};
__export(streamedQuery_exports, {
  streamedQuery: () => streamedQuery
});
module.exports = __toCommonJS(streamedQuery_exports);
var import_utils = require("./utils.cjs");
function streamedQuery({
  streamFn,
  refetchMode = "reset",
  reducer = (items, chunk) => (0, import_utils.addToEnd)(items, chunk),
  initialValue = []
}) {
  return async (context) => {
    const query = context.client.getQueryCache().find({ queryKey: context.queryKey, exact: true });
    const isRefetch = !!query && query.state.data !== void 0;
    if (isRefetch && refetchMode === "reset") {
      query.setState({
        status: "pending",
        data: void 0,
        error: null,
        fetchStatus: "fetching"
      });
    }
    let result = initialValue;
    const stream = await streamFn(context);
    for await (const chunk of stream) {
      if (context.signal.aborted) {
        break;
      }
      if (!isRefetch || refetchMode !== "replace") {
        context.client.setQueryData(
          context.queryKey,
          (prev) => reducer(prev === void 0 ? initialValue : prev, chunk)
        );
      }
      result = reducer(result, chunk);
    }
    if (isRefetch && refetchMode === "replace" && !context.signal.aborted) {
      context.client.setQueryData(context.queryKey, result);
    }
    return context.client.getQueryData(context.queryKey);
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  streamedQuery
});
//# sourceMappingURL=streamedQuery.cjs.map