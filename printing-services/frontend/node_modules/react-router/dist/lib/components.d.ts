import type { InitialEntry, LazyRouteFunction, Location, RelativeRoutingType, Router as RemixRouter, To, TrackedPromise } from "@remix-run/router";
import { Action as NavigationType } from "@remix-run/router";
import * as React from "react";
import type { IndexRouteObject, Navigator, NonIndexRouteObject, RouteMatch, RouteObject } from "./context";
export interface FutureConfig {
    v7_relativeSplatPath: boolean;
    v7_startTransition: boolean;
}
export interface RouterProviderProps {
    fallbackElement?: React.ReactNode;
    router: RemixRouter;
    future?: Partial<Pick<FutureConfig, "v7_startTransition">>;
}
/**
 * Given a Remix Router instance, render the appropriate UI
 */
export declare function RouterProvider({ fallbackElement, router, future, }: RouterProviderProps): React.ReactElement;
export interface MemoryRouterProps {
    basename?: string;
    children?: React.ReactNode;
    initialEntries?: InitialEntry[];
    initialIndex?: number;
    future?: Partial<FutureConfig>;
}
/**
 * A `<Router>` that stores all entries in memory.
 *
 * @see https://reactrouter.com/v6/router-components/memory-router
 */
export declare function MemoryRouter({ basename, children, initialEntries, initialIndex, future, }: MemoryRouterProps): React.ReactElement;
export interface NavigateProps {
    to: To;
    replace?: boolean;
    state?: any;
    relative?: RelativeRoutingType;
}
/**
 * Changes the current location.
 *
 * Note: This API is mostly useful in React.Component subclasses that are not
 * able to use hooks. In functional components, we recommend you use the
 * `useNavigate` hook instead.
 *
 * @see https://reactrouter.com/v6/components/navigate
 */
export declare function Navigate({ to, replace, state, relative, }: NavigateProps): null;
export interface OutletProps {
    context?: unknown;
}
/**
 * Renders the child route's element, if there is one.
 *
 * @see https://reactrouter.com/v6/components/outlet
 */
export declare function Outlet(props: OutletProps): React.ReactElement | null;
export interface PathRouteProps {
    caseSensitive?: NonIndexRouteObject["caseSensitive"];
    path?: NonIndexRouteObject["path"];
    id?: NonIndexRouteObject["id"];
    lazy?: LazyRouteFunction<NonIndexRouteObject>;
    loader?: NonIndexRouteObject["loader"];
    action?: NonIndexRouteObject["action"];
    hasErrorBoundary?: NonIndexRouteObject["hasErrorBoundary"];
    shouldRevalidate?: NonIndexRouteObject["shouldRevalidate"];
    handle?: NonIndexRouteObject["handle"];
    index?: false;
    children?: React.ReactNode;
    element?: React.ReactNode | null;
    hydrateFallbackElement?: React.ReactNode | null;
    errorElement?: React.ReactNode | null;
    Component?: React.ComponentType | null;
    HydrateFallback?: React.ComponentType | null;
    ErrorBoundary?: React.ComponentType | null;
}
export interface LayoutRouteProps extends PathRouteProps {
}
export interface IndexRouteProps {
    caseSensitive?: IndexRouteObject["caseSensitive"];
    path?: IndexRouteObject["path"];
    id?: IndexRouteObject["id"];
    lazy?: LazyRouteFunction<IndexRouteObject>;
    loader?: IndexRouteObject["loader"];
    action?: IndexRouteObject["action"];
    hasErrorBoundary?: IndexRouteObject["hasErrorBoundary"];
    shouldRevalidate?: IndexRouteObject["shouldRevalidate"];
    handle?: IndexRouteObject["handle"];
    index: true;
    children?: undefined;
    element?: React.ReactNode | null;
    hydrateFallbackElement?: React.ReactNode | null;
    errorElement?: React.ReactNode | null;
    Component?: React.ComponentType | null;
    HydrateFallback?: React.ComponentType | null;
    ErrorBoundary?: React.ComponentType | null;
}
export type RouteProps = PathRouteProps | LayoutRouteProps | IndexRouteProps;
/**
 * Declares an element that should be rendered at a certain URL path.
 *
 * @see https://reactrouter.com/v6/components/route
 */
export declare function Route(_props: RouteProps): React.ReactElement | null;
export interface RouterProps {
    basename?: string;
    children?: React.ReactNode;
    location: Partial<Location> | string;
    navigationType?: NavigationType;
    navigator: Navigator;
    static?: boolean;
    future?: Partial<Pick<FutureConfig, "v7_relativeSplatPath">>;
}
/**
 * Provides location context for the rest of the app.
 *
 * Note: You usually won't render a `<Router>` directly. Instead, you'll render a
 * router that is more specific to your environment such as a `<BrowserRouter>`
 * in web browsers or a `<StaticRouter>` for server rendering.
 *
 * @see https://reactrouter.com/v6/router-components/router
 */
export declare function Router({ basename: basenameProp, children, location: locationProp, navigationType, navigator, static: staticProp, future, }: RouterProps): React.ReactElement | null;
export interface RoutesProps {
    children?: React.ReactNode;
    location?: Partial<Location> | string;
}
/**
 * A container for a nested tree of `<Route>` elements that renders the branch
 * that best matches the current location.
 *
 * @see https://reactrouter.com/v6/components/routes
 */
export declare function Routes({ children, location, }: RoutesProps): React.ReactElement | null;
export interface AwaitResolveRenderFunction {
    (data: Awaited<any>): React.ReactNode;
}
export interface AwaitProps {
    children: React.ReactNode | AwaitResolveRenderFunction;
    errorElement?: React.ReactNode;
    resolve: TrackedPromise | any;
}
/**
 * Component to use for rendering lazily loaded data from returning defer()
 * in a loader function
 */
export declare function Await({ children, errorElement, resolve }: AwaitProps): React.JSX.Element;
/**
 * Creates a route config from a React "children" object, which is usually
 * either a `<Route>` element or an array of them. Used internally by
 * `<Routes>` to create a route config from its children.
 *
 * @see https://reactrouter.com/v6/utils/create-routes-from-children
 */
export declare function createRoutesFromChildren(children: React.ReactNode, parentPath?: number[]): RouteObject[];
/**
 * Renders the result of `matchRoutes()` into a React element.
 */
export declare function renderMatches(matches: RouteMatch[] | null): React.ReactElement | null;
