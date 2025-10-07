import * as React from "react";
import type { Router as RemixRouter, StaticHandlerContext, CreateStaticHandlerOptions as RouterCreateStaticHandlerOptions, FutureConfig as RouterFutureConfig } from "@remix-run/router";
import type { FutureConfig, Location, RouteObject } from "react-router-dom";
export interface StaticRouterProps {
    basename?: string;
    children?: React.ReactNode;
    location: Partial<Location> | string;
    future?: Partial<FutureConfig>;
}
/**
 * A `<Router>` that may not navigate to any other location. This is useful
 * on the server where there is no stateful UI.
 */
export declare function StaticRouter({ basename, children, location: locationProp, future, }: StaticRouterProps): React.JSX.Element;
export { StaticHandlerContext };
export interface StaticRouterProviderProps {
    context: StaticHandlerContext;
    router: RemixRouter;
    hydrate?: boolean;
    nonce?: string;
}
/**
 * A Data Router that may not navigate to any other location. This is useful
 * on the server where there is no stateful UI.
 */
export declare function StaticRouterProvider({ context, router, hydrate, nonce, }: StaticRouterProviderProps): React.JSX.Element;
type CreateStaticHandlerOptions = Omit<RouterCreateStaticHandlerOptions, "detectErrorBoundary" | "mapRouteProperties">;
export declare function createStaticHandler(routes: RouteObject[], opts?: CreateStaticHandlerOptions): import("@remix-run/router").StaticHandler;
export declare function createStaticRouter(routes: RouteObject[], context: StaticHandlerContext, opts?: {
    future?: Partial<Pick<RouterFutureConfig, "v7_partialHydration" | "v7_relativeSplatPath">>;
}): RemixRouter;
