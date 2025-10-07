/**
 * NOTE: If you refactor this to split up the modules into separate files,
 * you'll need to update the rollup config for react-router-dom-v5-compat.
 */
import * as React from "react";
import type { FutureConfig, Location, NavigateOptions, RelativeRoutingType, RouteObject, RouterProviderProps, To, DataStrategyFunction, PatchRoutesOnNavigationFunction } from "react-router";
import type { Fetcher, FormEncType, FormMethod, FutureConfig as RouterFutureConfig, GetScrollRestorationKeyFunction, History, HTMLFormMethod, HydrationState, Router as RemixRouter, V7_FormMethod, BlockerFunction } from "@remix-run/router";
import { UNSAFE_ErrorResponseImpl as ErrorResponseImpl } from "@remix-run/router";
import type { SubmitOptions, ParamKeyValuePair, URLSearchParamsInit, SubmitTarget, FetcherSubmitOptions } from "./dom";
import { createSearchParams } from "./dom";
export type { FormEncType, FormMethod, GetScrollRestorationKeyFunction, ParamKeyValuePair, SubmitOptions, URLSearchParamsInit, V7_FormMethod, };
export { createSearchParams, ErrorResponseImpl as UNSAFE_ErrorResponseImpl };
export type { ActionFunction, ActionFunctionArgs, AwaitProps, Blocker, BlockerFunction, DataRouteMatch, DataRouteObject, DataStrategyFunction, DataStrategyFunctionArgs, DataStrategyMatch, DataStrategyResult, ErrorResponse, Fetcher, FutureConfig, Hash, IndexRouteObject, IndexRouteProps, JsonFunction, LazyRouteFunction, LayoutRouteProps, LoaderFunction, LoaderFunctionArgs, Location, MemoryRouterProps, NavigateFunction, NavigateOptions, NavigateProps, Navigation, Navigator, NonIndexRouteObject, OutletProps, Params, ParamParseKey, PatchRoutesOnNavigationFunction, PatchRoutesOnNavigationFunctionArgs, Path, PathMatch, Pathname, PathParam, PathPattern, PathRouteProps, RedirectFunction, RelativeRoutingType, RouteMatch, RouteObject, RouteProps, RouterProps, RouterProviderProps, RoutesProps, Search, ShouldRevalidateFunction, ShouldRevalidateFunctionArgs, To, UIMatch, } from "react-router";
export { AbortedDeferredError, Await, MemoryRouter, Navigate, NavigationType, Outlet, Route, Router, Routes, createMemoryRouter, createPath, createRoutesFromChildren, createRoutesFromElements, defer, isRouteErrorResponse, generatePath, json, matchPath, matchRoutes, parsePath, redirect, redirectDocument, replace, renderMatches, resolvePath, useActionData, useAsyncError, useAsyncValue, useBlocker, useHref, useInRouterContext, useLoaderData, useLocation, useMatch, useMatches, useNavigate, useNavigation, useNavigationType, useOutlet, useOutletContext, useParams, useResolvedPath, useRevalidator, useRouteError, useRouteLoaderData, useRoutes, } from "react-router";
/** @internal */
export { UNSAFE_DataRouterContext, UNSAFE_DataRouterStateContext, UNSAFE_NavigationContext, UNSAFE_LocationContext, UNSAFE_RouteContext, UNSAFE_useRouteId, } from "react-router";
declare global {
    var __staticRouterHydrationData: HydrationState | undefined;
    var __reactRouterVersion: string;
    interface Document {
        startViewTransition(cb: () => Promise<void> | void): ViewTransition;
    }
}
interface DOMRouterOpts {
    basename?: string;
    future?: Partial<Omit<RouterFutureConfig, "v7_prependBasename">>;
    hydrationData?: HydrationState;
    dataStrategy?: DataStrategyFunction;
    patchRoutesOnNavigation?: PatchRoutesOnNavigationFunction;
    window?: Window;
}
export declare function createBrowserRouter(routes: RouteObject[], opts?: DOMRouterOpts): RemixRouter;
export declare function createHashRouter(routes: RouteObject[], opts?: DOMRouterOpts): RemixRouter;
type ViewTransitionContextObject = {
    isTransitioning: false;
} | {
    isTransitioning: true;
    flushSync: boolean;
    currentLocation: Location;
    nextLocation: Location;
};
declare const ViewTransitionContext: React.Context<ViewTransitionContextObject>;
export { ViewTransitionContext as UNSAFE_ViewTransitionContext };
type FetchersContextObject = Map<string, any>;
declare const FetchersContext: React.Context<FetchersContextObject>;
export { FetchersContext as UNSAFE_FetchersContext };
interface ViewTransition {
    finished: Promise<void>;
    ready: Promise<void>;
    updateCallbackDone: Promise<void>;
    skipTransition(): void;
}
/**
 * Given a Remix Router instance, render the appropriate UI
 */
export declare function RouterProvider({ fallbackElement, router, future, }: RouterProviderProps): React.ReactElement;
export interface BrowserRouterProps {
    basename?: string;
    children?: React.ReactNode;
    future?: Partial<FutureConfig>;
    window?: Window;
}
/**
 * A `<Router>` for use in web browsers. Provides the cleanest URLs.
 */
export declare function BrowserRouter({ basename, children, future, window, }: BrowserRouterProps): React.JSX.Element;
export interface HashRouterProps {
    basename?: string;
    children?: React.ReactNode;
    future?: Partial<FutureConfig>;
    window?: Window;
}
/**
 * A `<Router>` for use in web browsers. Stores the location in the hash
 * portion of the URL so it is not sent to the server.
 */
export declare function HashRouter({ basename, children, future, window, }: HashRouterProps): React.JSX.Element;
export interface HistoryRouterProps {
    basename?: string;
    children?: React.ReactNode;
    future?: FutureConfig;
    history: History;
}
/**
 * A `<Router>` that accepts a pre-instantiated history object. It's important
 * to note that using your own history object is highly discouraged and may add
 * two versions of the history library to your bundles unless you use the same
 * version of the history library that React Router uses internally.
 */
declare function HistoryRouter({ basename, children, future, history, }: HistoryRouterProps): React.JSX.Element;
declare namespace HistoryRouter {
    var displayName: string;
}
export { HistoryRouter as unstable_HistoryRouter };
export interface LinkProps extends Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, "href"> {
    reloadDocument?: boolean;
    replace?: boolean;
    state?: any;
    preventScrollReset?: boolean;
    relative?: RelativeRoutingType;
    to: To;
    viewTransition?: boolean;
}
/**
 * The public API for rendering a history-aware `<a>`.
 */
export declare const Link: React.ForwardRefExoticComponent<LinkProps & React.RefAttributes<HTMLAnchorElement>>;
export type NavLinkRenderProps = {
    isActive: boolean;
    isPending: boolean;
    isTransitioning: boolean;
};
export interface NavLinkProps extends Omit<LinkProps, "className" | "style" | "children"> {
    children?: React.ReactNode | ((props: NavLinkRenderProps) => React.ReactNode);
    caseSensitive?: boolean;
    className?: string | ((props: NavLinkRenderProps) => string | undefined);
    end?: boolean;
    style?: React.CSSProperties | ((props: NavLinkRenderProps) => React.CSSProperties | undefined);
}
/**
 * A `<Link>` wrapper that knows if it's "active" or not.
 */
export declare const NavLink: React.ForwardRefExoticComponent<NavLinkProps & React.RefAttributes<HTMLAnchorElement>>;
/**
 * Form props shared by navigations and fetchers
 */
interface SharedFormProps extends React.FormHTMLAttributes<HTMLFormElement> {
    /**
     * The HTTP verb to use when the form is submit. Supports "get", "post",
     * "put", "delete", "patch".
     */
    method?: HTMLFormMethod;
    /**
     * `<form encType>` - enhancing beyond the normal string type and limiting
     * to the built-in browser supported values
     */
    encType?: "application/x-www-form-urlencoded" | "multipart/form-data" | "text/plain";
    /**
     * Normal `<form action>` but supports React Router's relative paths.
     */
    action?: string;
    /**
     * Determines whether the form action is relative to the route hierarchy or
     * the pathname.  Use this if you want to opt out of navigating the route
     * hierarchy and want to instead route based on /-delimited URL segments
     */
    relative?: RelativeRoutingType;
    /**
     * Prevent the scroll position from resetting to the top of the viewport on
     * completion of the navigation when using the <ScrollRestoration> component
     */
    preventScrollReset?: boolean;
    /**
     * A function to call when the form is submitted. If you call
     * `event.preventDefault()` then this form will not do anything.
     */
    onSubmit?: React.FormEventHandler<HTMLFormElement>;
}
/**
 * Form props available to fetchers
 */
export interface FetcherFormProps extends SharedFormProps {
}
/**
 * Form props available to navigations
 */
export interface FormProps extends SharedFormProps {
    /**
     * Indicate a specific fetcherKey to use when using navigate=false
     */
    fetcherKey?: string;
    /**
     * navigate=false will use a fetcher instead of a navigation
     */
    navigate?: boolean;
    /**
     * Forces a full document navigation instead of a fetch.
     */
    reloadDocument?: boolean;
    /**
     * Replaces the current entry in the browser history stack when the form
     * navigates. Use this if you don't want the user to be able to click "back"
     * to the page with the form on it.
     */
    replace?: boolean;
    /**
     * State object to add to the history stack entry for this navigation
     */
    state?: any;
    /**
     * Enable view transitions on this Form navigation
     */
    viewTransition?: boolean;
}
/**
 * A `@remix-run/router`-aware `<form>`. It behaves like a normal form except
 * that the interaction with the server is with `fetch` instead of new document
 * requests, allowing components to add nicer UX to the page as the form is
 * submitted and returns with data.
 */
export declare const Form: React.ForwardRefExoticComponent<FormProps & React.RefAttributes<HTMLFormElement>>;
export interface ScrollRestorationProps {
    getKey?: GetScrollRestorationKeyFunction;
    storageKey?: string;
}
/**
 * This component will emulate the browser's scroll restoration on location
 * changes.
 */
export declare function ScrollRestoration({ getKey, storageKey, }: ScrollRestorationProps): null;
export declare namespace ScrollRestoration {
    var displayName: string;
}
/**
 * Handles the click behavior for router `<Link>` components. This is useful if
 * you need to create custom `<Link>` components with the same click behavior we
 * use in our exported `<Link>`.
 */
export declare function useLinkClickHandler<E extends Element = HTMLAnchorElement>(to: To, { target, replace: replaceProp, state, preventScrollReset, relative, viewTransition, }?: {
    target?: React.HTMLAttributeAnchorTarget;
    replace?: boolean;
    state?: any;
    preventScrollReset?: boolean;
    relative?: RelativeRoutingType;
    viewTransition?: boolean;
}): (event: React.MouseEvent<E, MouseEvent>) => void;
/**
 * A convenient wrapper for reading and writing search parameters via the
 * URLSearchParams interface.
 */
export declare function useSearchParams(defaultInit?: URLSearchParamsInit): [URLSearchParams, SetURLSearchParams];
export type SetURLSearchParams = (nextInit?: URLSearchParamsInit | ((prev: URLSearchParams) => URLSearchParamsInit), navigateOpts?: NavigateOptions) => void;
/**
 * Submits a HTML `<form>` to the server without reloading the page.
 */
export interface SubmitFunction {
    (
    /**
     * Specifies the `<form>` to be submitted to the server, a specific
     * `<button>` or `<input type="submit">` to use to submit the form, or some
     * arbitrary data to submit.
     *
     * Note: When using a `<button>` its `name` and `value` will also be
     * included in the form data that is submitted.
     */
    target: SubmitTarget, 
    /**
     * Options that override the `<form>`'s own attributes. Required when
     * submitting arbitrary data without a backing `<form>`.
     */
    options?: SubmitOptions): void;
}
/**
 * Submits a fetcher `<form>` to the server without reloading the page.
 */
export interface FetcherSubmitFunction {
    (target: SubmitTarget, options?: FetcherSubmitOptions): void;
}
/**
 * Returns a function that may be used to programmatically submit a form (or
 * some arbitrary data) to the server.
 */
export declare function useSubmit(): SubmitFunction;
export declare function useFormAction(action?: string, { relative }?: {
    relative?: RelativeRoutingType;
}): string;
export type FetcherWithComponents<TData> = Fetcher<TData> & {
    Form: React.ForwardRefExoticComponent<FetcherFormProps & React.RefAttributes<HTMLFormElement>>;
    submit: FetcherSubmitFunction;
    load: (href: string, opts?: {
        flushSync?: boolean;
    }) => void;
};
/**
 * Interacts with route loaders and actions without causing a navigation. Great
 * for any interaction that stays on the same page.
 */
export declare function useFetcher<TData = any>({ key, }?: {
    key?: string;
}): FetcherWithComponents<TData>;
/**
 * Provides all fetchers currently on the page. Useful for layouts and parent
 * routes that need to provide pending/optimistic UI regarding the fetch.
 */
export declare function useFetchers(): (Fetcher & {
    key: string;
})[];
/**
 * When rendered inside a RouterProvider, will restore scroll positions on navigations
 */
declare function useScrollRestoration({ getKey, storageKey, }?: {
    getKey?: GetScrollRestorationKeyFunction;
    storageKey?: string;
}): void;
export { useScrollRestoration as UNSAFE_useScrollRestoration };
/**
 * Setup a callback to be fired on the window's `beforeunload` event. This is
 * useful for saving some data to `window.localStorage` just before the page
 * refreshes.
 *
 * Note: The `callback` argument should be a function created with
 * `React.useCallback()`.
 */
export declare function useBeforeUnload(callback: (event: BeforeUnloadEvent) => any, options?: {
    capture?: boolean;
}): void;
/**
 * Wrapper around useBlocker to show a window.confirm prompt to users instead
 * of building a custom UI with useBlocker.
 *
 * Warning: This has *a lot of rough edges* and behaves very differently (and
 * very incorrectly in some cases) across browsers if user click addition
 * back/forward navigations while the confirm is open.  Use at your own risk.
 */
declare function usePrompt({ when, message, }: {
    when: boolean | BlockerFunction;
    message: string;
}): void;
export { usePrompt as unstable_usePrompt };
/**
 * Return a boolean indicating if there is an active view transition to the
 * given href.  You can use this value to render CSS classes or viewTransitionName
 * styles onto your elements
 *
 * @param href The destination href
 * @param [opts.relative] Relative routing type ("route" | "path")
 */
declare function useViewTransitionState(to: To, opts?: {
    relative?: RelativeRoutingType;
}): boolean;
export { useViewTransitionState as useViewTransitionState };
