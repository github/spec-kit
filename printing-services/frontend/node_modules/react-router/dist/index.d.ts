import type { ActionFunction, ActionFunctionArgs, AgnosticPatchRoutesOnNavigationFunction, AgnosticPatchRoutesOnNavigationFunctionArgs, Blocker, BlockerFunction, DataStrategyFunction, DataStrategyFunctionArgs, DataStrategyMatch, DataStrategyResult, ErrorResponse, Fetcher, HydrationState, InitialEntry, JsonFunction, LazyRouteFunction, LoaderFunction, LoaderFunctionArgs, Location, Navigation, ParamParseKey, Params, Path, PathMatch, PathParam, PathPattern, RedirectFunction, RelativeRoutingType, Router as RemixRouter, FutureConfig as RouterFutureConfig, ShouldRevalidateFunction, ShouldRevalidateFunctionArgs, To, UIMatch } from "@remix-run/router";
import { AbortedDeferredError, Action as NavigationType, createPath, defer, generatePath, isRouteErrorResponse, json, matchPath, matchRoutes, parsePath, redirect, redirectDocument, replace, resolvePath } from "@remix-run/router";
import type { AwaitProps, FutureConfig, IndexRouteProps, LayoutRouteProps, MemoryRouterProps, NavigateProps, OutletProps, PathRouteProps, RouteProps, RouterProps, RouterProviderProps, RoutesProps } from "./lib/components";
import { Await, MemoryRouter, Navigate, Outlet, Route, Router, RouterProvider, Routes, createRoutesFromChildren, renderMatches } from "./lib/components";
import type { DataRouteMatch, DataRouteObject, IndexRouteObject, NavigateOptions, Navigator, NonIndexRouteObject, RouteMatch, RouteObject } from "./lib/context";
import { DataRouterContext, DataRouterStateContext, LocationContext, NavigationContext, RouteContext } from "./lib/context";
import type { NavigateFunction } from "./lib/hooks";
import { useActionData, useAsyncError, useAsyncValue, useBlocker, useHref, useInRouterContext, useLoaderData, useLocation, useMatch, useMatches, useNavigate, useNavigation, useNavigationType, useOutlet, useOutletContext, useParams, useResolvedPath, useRevalidator, useRouteError, useRouteId, useRouteLoaderData, useRoutes, useRoutesImpl } from "./lib/hooks";
import { logV6DeprecationWarnings } from "./lib/deprecations";
type Hash = string;
type Pathname = string;
type Search = string;
export type { ActionFunction, ActionFunctionArgs, AwaitProps, DataRouteMatch, DataRouteObject, DataStrategyFunction, DataStrategyFunctionArgs, DataStrategyMatch, DataStrategyResult, ErrorResponse, Fetcher, FutureConfig, Hash, IndexRouteObject, IndexRouteProps, JsonFunction, LayoutRouteProps, LazyRouteFunction, LoaderFunction, LoaderFunctionArgs, Location, MemoryRouterProps, NavigateFunction, NavigateOptions, NavigateProps, Navigation, Navigator, NonIndexRouteObject, OutletProps, ParamParseKey, Params, Path, PathMatch, PathParam, PathPattern, PathRouteProps, Pathname, RedirectFunction, RelativeRoutingType, RouteMatch, RouteObject, RouteProps, RouterProps, RouterProviderProps, RoutesProps, Search, ShouldRevalidateFunction, ShouldRevalidateFunctionArgs, To, UIMatch, Blocker, BlockerFunction, };
export { AbortedDeferredError, Await, MemoryRouter, Navigate, NavigationType, Outlet, Route, Router, RouterProvider, Routes, createPath, createRoutesFromChildren, createRoutesFromChildren as createRoutesFromElements, defer, generatePath, isRouteErrorResponse, json, matchPath, matchRoutes, parsePath, redirect, redirectDocument, replace, renderMatches, resolvePath, useBlocker, useActionData, useAsyncError, useAsyncValue, useHref, useInRouterContext, useLoaderData, useLocation, useMatch, useMatches, useNavigate, useNavigation, useNavigationType, useOutlet, useOutletContext, useParams, useResolvedPath, useRevalidator, useRouteError, useRouteLoaderData, useRoutes, };
export type PatchRoutesOnNavigationFunctionArgs = AgnosticPatchRoutesOnNavigationFunctionArgs<RouteObject, RouteMatch>;
export type PatchRoutesOnNavigationFunction = AgnosticPatchRoutesOnNavigationFunction<RouteObject, RouteMatch>;
declare function mapRouteProperties(route: RouteObject): Partial<RouteObject> & {
    hasErrorBoundary: boolean;
};
export declare function createMemoryRouter(routes: RouteObject[], opts?: {
    basename?: string;
    future?: Partial<Omit<RouterFutureConfig, "v7_prependBasename">>;
    hydrationData?: HydrationState;
    initialEntries?: InitialEntry[];
    initialIndex?: number;
    dataStrategy?: DataStrategyFunction;
    patchRoutesOnNavigation?: PatchRoutesOnNavigationFunction;
}): RemixRouter;
/** @internal */
export { DataRouterContext as UNSAFE_DataRouterContext, DataRouterStateContext as UNSAFE_DataRouterStateContext, LocationContext as UNSAFE_LocationContext, NavigationContext as UNSAFE_NavigationContext, RouteContext as UNSAFE_RouteContext, mapRouteProperties as UNSAFE_mapRouteProperties, useRouteId as UNSAFE_useRouteId, useRoutesImpl as UNSAFE_useRoutesImpl, logV6DeprecationWarnings as UNSAFE_logV6DeprecationWarnings, };
