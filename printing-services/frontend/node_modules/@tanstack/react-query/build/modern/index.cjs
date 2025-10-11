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
var __reExport = (target, mod, secondTarget) => (__copyProps(target, mod, "default"), secondTarget && __copyProps(secondTarget, mod, "default"));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/index.ts
var index_exports = {};
__export(index_exports, {
  HydrationBoundary: () => import_HydrationBoundary.HydrationBoundary,
  IsRestoringProvider: () => import_IsRestoringProvider.IsRestoringProvider,
  QueryClientContext: () => import_QueryClientProvider.QueryClientContext,
  QueryClientProvider: () => import_QueryClientProvider.QueryClientProvider,
  QueryErrorResetBoundary: () => import_QueryErrorResetBoundary.QueryErrorResetBoundary,
  infiniteQueryOptions: () => import_infiniteQueryOptions.infiniteQueryOptions,
  mutationOptions: () => import_mutationOptions.mutationOptions,
  queryOptions: () => import_queryOptions.queryOptions,
  useInfiniteQuery: () => import_useInfiniteQuery.useInfiniteQuery,
  useIsFetching: () => import_useIsFetching.useIsFetching,
  useIsMutating: () => import_useMutationState.useIsMutating,
  useIsRestoring: () => import_IsRestoringProvider.useIsRestoring,
  useMutation: () => import_useMutation.useMutation,
  useMutationState: () => import_useMutationState.useMutationState,
  usePrefetchInfiniteQuery: () => import_usePrefetchInfiniteQuery.usePrefetchInfiniteQuery,
  usePrefetchQuery: () => import_usePrefetchQuery.usePrefetchQuery,
  useQueries: () => import_useQueries.useQueries,
  useQuery: () => import_useQuery.useQuery,
  useQueryClient: () => import_QueryClientProvider.useQueryClient,
  useQueryErrorResetBoundary: () => import_QueryErrorResetBoundary.useQueryErrorResetBoundary,
  useSuspenseInfiniteQuery: () => import_useSuspenseInfiniteQuery.useSuspenseInfiniteQuery,
  useSuspenseQueries: () => import_useSuspenseQueries.useSuspenseQueries,
  useSuspenseQuery: () => import_useSuspenseQuery.useSuspenseQuery
});
module.exports = __toCommonJS(index_exports);
__reExport(index_exports, require("@tanstack/query-core"), module.exports);
__reExport(index_exports, require("./types.cjs"), module.exports);
var import_useQueries = require("./useQueries.cjs");
var import_useQuery = require("./useQuery.cjs");
var import_useSuspenseQuery = require("./useSuspenseQuery.cjs");
var import_useSuspenseInfiniteQuery = require("./useSuspenseInfiniteQuery.cjs");
var import_useSuspenseQueries = require("./useSuspenseQueries.cjs");
var import_usePrefetchQuery = require("./usePrefetchQuery.cjs");
var import_usePrefetchInfiniteQuery = require("./usePrefetchInfiniteQuery.cjs");
var import_queryOptions = require("./queryOptions.cjs");
var import_infiniteQueryOptions = require("./infiniteQueryOptions.cjs");
var import_QueryClientProvider = require("./QueryClientProvider.cjs");
var import_HydrationBoundary = require("./HydrationBoundary.cjs");
var import_QueryErrorResetBoundary = require("./QueryErrorResetBoundary.cjs");
var import_useIsFetching = require("./useIsFetching.cjs");
var import_useMutationState = require("./useMutationState.cjs");
var import_useMutation = require("./useMutation.cjs");
var import_mutationOptions = require("./mutationOptions.cjs");
var import_useInfiniteQuery = require("./useInfiniteQuery.cjs");
var import_IsRestoringProvider = require("./IsRestoringProvider.cjs");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  HydrationBoundary,
  IsRestoringProvider,
  QueryClientContext,
  QueryClientProvider,
  QueryErrorResetBoundary,
  infiniteQueryOptions,
  mutationOptions,
  queryOptions,
  useInfiniteQuery,
  useIsFetching,
  useIsMutating,
  useIsRestoring,
  useMutation,
  useMutationState,
  usePrefetchInfiniteQuery,
  usePrefetchQuery,
  useQueries,
  useQuery,
  useQueryClient,
  useQueryErrorResetBoundary,
  useSuspenseInfiniteQuery,
  useSuspenseQueries,
  useSuspenseQuery,
  ...require("@tanstack/query-core"),
  ...require("./types.cjs")
});
//# sourceMappingURL=index.cjs.map