import * as React from 'react';
import { QueryClient } from '@tanstack/query-core';

declare const QueryClientContext: React.Context<QueryClient | undefined>;
declare const useQueryClient: (queryClient?: QueryClient) => QueryClient;
type QueryClientProviderProps = {
    client: QueryClient;
    children?: React.ReactNode;
};
declare const QueryClientProvider: ({ client, children, }: QueryClientProviderProps) => React.JSX.Element;

export { QueryClientContext, QueryClientProvider, type QueryClientProviderProps, useQueryClient };
