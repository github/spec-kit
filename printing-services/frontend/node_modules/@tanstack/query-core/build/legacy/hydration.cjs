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

// src/hydration.ts
var hydration_exports = {};
__export(hydration_exports, {
  defaultShouldDehydrateMutation: () => defaultShouldDehydrateMutation,
  defaultShouldDehydrateQuery: () => defaultShouldDehydrateQuery,
  dehydrate: () => dehydrate,
  hydrate: () => hydrate
});
module.exports = __toCommonJS(hydration_exports);
var import_thenable = require("./thenable.cjs");
function defaultTransformerFn(data) {
  return data;
}
function dehydrateMutation(mutation) {
  return {
    mutationKey: mutation.options.mutationKey,
    state: mutation.state,
    ...mutation.options.scope && { scope: mutation.options.scope },
    ...mutation.meta && { meta: mutation.meta }
  };
}
function dehydrateQuery(query, serializeData, shouldRedactErrors) {
  var _a;
  return {
    dehydratedAt: Date.now(),
    state: {
      ...query.state,
      ...query.state.data !== void 0 && {
        data: serializeData(query.state.data)
      }
    },
    queryKey: query.queryKey,
    queryHash: query.queryHash,
    ...query.state.status === "pending" && {
      promise: (_a = query.promise) == null ? void 0 : _a.then(serializeData).catch((error) => {
        if (!shouldRedactErrors(error)) {
          return Promise.reject(error);
        }
        if (process.env.NODE_ENV !== "production") {
          console.error(
            `A query that was dehydrated as pending ended up rejecting. [${query.queryHash}]: ${error}; The error will be redacted in production builds`
          );
        }
        return Promise.reject(new Error("redacted"));
      })
    },
    ...query.meta && { meta: query.meta }
  };
}
function defaultShouldDehydrateMutation(mutation) {
  return mutation.state.isPaused;
}
function defaultShouldDehydrateQuery(query) {
  return query.state.status === "success";
}
function defaultShouldRedactErrors(_) {
  return true;
}
function dehydrate(client, options = {}) {
  var _a, _b, _c, _d;
  const filterMutation = options.shouldDehydrateMutation ?? ((_a = client.getDefaultOptions().dehydrate) == null ? void 0 : _a.shouldDehydrateMutation) ?? defaultShouldDehydrateMutation;
  const mutations = client.getMutationCache().getAll().flatMap(
    (mutation) => filterMutation(mutation) ? [dehydrateMutation(mutation)] : []
  );
  const filterQuery = options.shouldDehydrateQuery ?? ((_b = client.getDefaultOptions().dehydrate) == null ? void 0 : _b.shouldDehydrateQuery) ?? defaultShouldDehydrateQuery;
  const shouldRedactErrors = options.shouldRedactErrors ?? ((_c = client.getDefaultOptions().dehydrate) == null ? void 0 : _c.shouldRedactErrors) ?? defaultShouldRedactErrors;
  const serializeData = options.serializeData ?? ((_d = client.getDefaultOptions().dehydrate) == null ? void 0 : _d.serializeData) ?? defaultTransformerFn;
  const queries = client.getQueryCache().getAll().flatMap(
    (query) => filterQuery(query) ? [dehydrateQuery(query, serializeData, shouldRedactErrors)] : []
  );
  return { mutations, queries };
}
function hydrate(client, dehydratedState, options) {
  var _a, _b;
  if (typeof dehydratedState !== "object" || dehydratedState === null) {
    return;
  }
  const mutationCache = client.getMutationCache();
  const queryCache = client.getQueryCache();
  const deserializeData = ((_a = options == null ? void 0 : options.defaultOptions) == null ? void 0 : _a.deserializeData) ?? ((_b = client.getDefaultOptions().hydrate) == null ? void 0 : _b.deserializeData) ?? defaultTransformerFn;
  const mutations = dehydratedState.mutations || [];
  const queries = dehydratedState.queries || [];
  mutations.forEach(({ state, ...mutationOptions }) => {
    var _a2, _b2;
    mutationCache.build(
      client,
      {
        ...(_a2 = client.getDefaultOptions().hydrate) == null ? void 0 : _a2.mutations,
        ...(_b2 = options == null ? void 0 : options.defaultOptions) == null ? void 0 : _b2.mutations,
        ...mutationOptions
      },
      state
    );
  });
  queries.forEach(
    ({ queryKey, state, queryHash, meta, promise, dehydratedAt }) => {
      var _a2, _b2;
      const syncData = promise ? (0, import_thenable.tryResolveSync)(promise) : void 0;
      const rawData = state.data === void 0 ? syncData == null ? void 0 : syncData.data : state.data;
      const data = rawData === void 0 ? rawData : deserializeData(rawData);
      let query = queryCache.get(queryHash);
      const existingQueryIsPending = (query == null ? void 0 : query.state.status) === "pending";
      const existingQueryIsFetching = (query == null ? void 0 : query.state.fetchStatus) === "fetching";
      if (query) {
        const hasNewerSyncData = syncData && // We only need this undefined check to handle older dehydration
        // payloads that might not have dehydratedAt
        dehydratedAt !== void 0 && dehydratedAt > query.state.dataUpdatedAt;
        if (state.dataUpdatedAt > query.state.dataUpdatedAt || hasNewerSyncData) {
          const { fetchStatus: _ignored, ...serializedState } = state;
          query.setState({
            ...serializedState,
            data
          });
        }
      } else {
        query = queryCache.build(
          client,
          {
            ...(_a2 = client.getDefaultOptions().hydrate) == null ? void 0 : _a2.queries,
            ...(_b2 = options == null ? void 0 : options.defaultOptions) == null ? void 0 : _b2.queries,
            queryKey,
            queryHash,
            meta
          },
          // Reset fetch status to idle to avoid
          // query being stuck in fetching state upon hydration
          {
            ...state,
            data,
            fetchStatus: "idle",
            status: data !== void 0 ? "success" : state.status
          }
        );
      }
      if (promise && !existingQueryIsPending && !existingQueryIsFetching && // Only hydrate if dehydration is newer than any existing data,
      // this is always true for new queries
      (dehydratedAt === void 0 || dehydratedAt > query.state.dataUpdatedAt)) {
        void query.fetch(void 0, {
          // RSC transformed promises are not thenable
          initialPromise: Promise.resolve(promise).then(deserializeData)
        });
      }
    }
  );
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  defaultShouldDehydrateMutation,
  defaultShouldDehydrateQuery,
  dehydrate,
  hydrate
});
//# sourceMappingURL=hydration.cjs.map