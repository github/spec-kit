// src/hydration.ts
import { tryResolveSync } from "./thenable.js";
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
      promise: query.promise?.then(serializeData).catch((error) => {
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
  const filterMutation = options.shouldDehydrateMutation ?? client.getDefaultOptions().dehydrate?.shouldDehydrateMutation ?? defaultShouldDehydrateMutation;
  const mutations = client.getMutationCache().getAll().flatMap(
    (mutation) => filterMutation(mutation) ? [dehydrateMutation(mutation)] : []
  );
  const filterQuery = options.shouldDehydrateQuery ?? client.getDefaultOptions().dehydrate?.shouldDehydrateQuery ?? defaultShouldDehydrateQuery;
  const shouldRedactErrors = options.shouldRedactErrors ?? client.getDefaultOptions().dehydrate?.shouldRedactErrors ?? defaultShouldRedactErrors;
  const serializeData = options.serializeData ?? client.getDefaultOptions().dehydrate?.serializeData ?? defaultTransformerFn;
  const queries = client.getQueryCache().getAll().flatMap(
    (query) => filterQuery(query) ? [dehydrateQuery(query, serializeData, shouldRedactErrors)] : []
  );
  return { mutations, queries };
}
function hydrate(client, dehydratedState, options) {
  if (typeof dehydratedState !== "object" || dehydratedState === null) {
    return;
  }
  const mutationCache = client.getMutationCache();
  const queryCache = client.getQueryCache();
  const deserializeData = options?.defaultOptions?.deserializeData ?? client.getDefaultOptions().hydrate?.deserializeData ?? defaultTransformerFn;
  const mutations = dehydratedState.mutations || [];
  const queries = dehydratedState.queries || [];
  mutations.forEach(({ state, ...mutationOptions }) => {
    mutationCache.build(
      client,
      {
        ...client.getDefaultOptions().hydrate?.mutations,
        ...options?.defaultOptions?.mutations,
        ...mutationOptions
      },
      state
    );
  });
  queries.forEach(
    ({ queryKey, state, queryHash, meta, promise, dehydratedAt }) => {
      const syncData = promise ? tryResolveSync(promise) : void 0;
      const rawData = state.data === void 0 ? syncData?.data : state.data;
      const data = rawData === void 0 ? rawData : deserializeData(rawData);
      let query = queryCache.get(queryHash);
      const existingQueryIsPending = query?.state.status === "pending";
      const existingQueryIsFetching = query?.state.fetchStatus === "fetching";
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
            ...client.getDefaultOptions().hydrate?.queries,
            ...options?.defaultOptions?.queries,
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
export {
  defaultShouldDehydrateMutation,
  defaultShouldDehydrateQuery,
  dehydrate,
  hydrate
};
//# sourceMappingURL=hydration.js.map