// src/index.ts
export * from "@tanstack/query-core";
export * from "./types.js";
import { useQueries } from "./useQueries.js";
import { useQuery } from "./useQuery.js";
import { useSuspenseQuery } from "./useSuspenseQuery.js";
import { useSuspenseInfiniteQuery } from "./useSuspenseInfiniteQuery.js";
import { useSuspenseQueries } from "./useSuspenseQueries.js";
import { usePrefetchQuery } from "./usePrefetchQuery.js";
import { usePrefetchInfiniteQuery } from "./usePrefetchInfiniteQuery.js";
import { queryOptions } from "./queryOptions.js";
import { infiniteQueryOptions } from "./infiniteQueryOptions.js";
import {
  QueryClientContext,
  QueryClientProvider,
  useQueryClient
} from "./QueryClientProvider.js";
import { HydrationBoundary } from "./HydrationBoundary.js";
import {
  QueryErrorResetBoundary,
  useQueryErrorResetBoundary
} from "./QueryErrorResetBoundary.js";
import { useIsFetching } from "./useIsFetching.js";
import { useIsMutating, useMutationState } from "./useMutationState.js";
import { useMutation } from "./useMutation.js";
import { mutationOptions } from "./mutationOptions.js";
import { useInfiniteQuery } from "./useInfiniteQuery.js";
import { useIsRestoring, IsRestoringProvider } from "./IsRestoringProvider.js";
export {
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
  useSuspenseQuery
};
//# sourceMappingURL=index.js.map