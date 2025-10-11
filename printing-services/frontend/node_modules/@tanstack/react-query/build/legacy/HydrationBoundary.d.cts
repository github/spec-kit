import * as React from 'react';
import { DehydratedState, OmitKeyof, HydrateOptions, QueryClient } from '@tanstack/query-core';

interface HydrationBoundaryProps {
    state: DehydratedState | null | undefined;
    options?: OmitKeyof<HydrateOptions, 'defaultOptions'> & {
        defaultOptions?: OmitKeyof<Exclude<HydrateOptions['defaultOptions'], undefined>, 'mutations'>;
    };
    children?: React.ReactNode;
    queryClient?: QueryClient;
}
declare const HydrationBoundary: ({ children, options, state, queryClient, }: HydrationBoundaryProps) => React.ReactElement;

export { HydrationBoundary, type HydrationBoundaryProps };
