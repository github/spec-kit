import * as React from "react";
import type { AgnosticIndexRouteObject, AgnosticNonIndexRouteObject, AgnosticRouteMatch, History, LazyRouteFunction, Location, Action as NavigationType, RelativeRoutingType, Router, StaticHandlerContext, To, TrackedPromise } from "@remix-run/router";
export interface IndexRouteObject {
    caseSensitive?: AgnosticIndexRouteObject["caseSensitive"];
    path?: AgnosticIndexRouteObject["path"];
    id?: AgnosticIndexRouteObject["id"];
    loader?: AgnosticIndexRouteObject["loader"];
    action?: AgnosticIndexRouteObject["action"];
    hasErrorBoundary?: AgnosticIndexRouteObject["hasErrorBoundary"];
    shouldRevalidate?: AgnosticIndexRouteObject["shouldRevalidate"];
    handle?: AgnosticIndexRouteObject["handle"];
    index: true;
    children?: undefined;
    element?: React.ReactNode | null;
    hydrateFallbackElement?: React.ReactNode | null;
    errorElement?: React.ReactNode | null;
    Component?: React.ComponentType | null;
    HydrateFallback?: React.ComponentType | null;
    ErrorBoundary?: React.ComponentType | null;
    lazy?: LazyRouteFunction<RouteObject>;
}
export interface NonIndexRouteObject {
    caseSensitive?: AgnosticNonIndexRouteObject["caseSensitive"];
    path?: AgnosticNonIndexRouteObject["path"];
    id?: AgnosticNonIndexRouteObject["id"];
    loader?: AgnosticNonIndexRouteObject["loader"];
    action?: AgnosticNonIndexRouteObject["action"];
    hasErrorBoundary?: AgnosticNonIndexRouteObject["hasErrorBoundary"];
    shouldRevalidate?: AgnosticNonIndexRouteObject["shouldRevalidate"];
    handle?: AgnosticNonIndexRouteObject["handle"];
    index?: false;
    children?: RouteObject[];
    element?: React.ReactNode | null;
    hydrateFallbackElement?: React.ReactNode | null;
    errorElement?: React.ReactNode | null;
    Component?: React.ComponentType | null;
    HydrateFallback?: React.ComponentType | null;
    ErrorBoundary?: React.ComponentType | null;
    lazy?: LazyRouteFunction<RouteObject>;
}
export type RouteObject = IndexRouteObject | NonIndexRouteObject;
export type DataRouteObject = RouteObject & {
    children?: DataRouteObject[];
    id: string;
};
export interface RouteMatch<ParamKey extends string = string, RouteObjectType extends RouteObject = RouteObject> extends AgnosticRouteMatch<ParamKey, RouteObjectType> {
}
export interface DataRouteMatch extends RouteMatch<string, DataRouteObject> {
}
export interface DataRouterContextObject extends Omit<NavigationContextObject, "future"> {
    router: Router;
    staticContext?: StaticHandlerContext;
}
export declare const DataRouterContext: React.Context<DataRouterContextObject | null>;
export declare const DataRouterStateContext: React.Context<import("@remix-run/router").RouterState | null>;
export declare const AwaitContext: React.Context<TrackedPromise | null>;
export interface NavigateOptions {
    replace?: boolean;
    state?: any;
    preventScrollReset?: boolean;
    relative?: RelativeRoutingType;
    flushSync?: boolean;
    viewTransition?: boolean;
}
/**
 * A Navigator is a "location changer"; it's how you get to different locations.
 *
 * Every history instance conforms to the Navigator interface, but the
 * distinction is useful primarily when it comes to the low-level `<Router>` API
 * where both the location and a navigator must be provided separately in order
 * to avoid "tearing" that may occur in a suspense-enabled app if the action
 * and/or location were to be read directly from the history instance.
 */
export interface Navigator {
    createHref: History["createHref"];
    encodeLocation?: History["encodeLocation"];
    go: History["go"];
    push(to: To, state?: any, opts?: NavigateOptions): void;
    replace(to: To, state?: any, opts?: NavigateOptions): void;
}
interface NavigationContextObject {
    basename: string;
    navigator: Navigator;
    static: boolean;
    future: {
        v7_relativeSplatPath: boolean;
    };
}
export declare const NavigationContext: React.Context<NavigationContextObject>;
interface LocationContextObject {
    location: Location;
    navigationType: NavigationType;
}
export declare const LocationContext: React.Context<LocationContextObject>;
export interface RouteContextObject {
    outlet: React.ReactElement | null;
    matches: RouteMatch[];
    isDataRoute: boolean;
}
export declare const RouteContext: React.Context<RouteContextObject>;
export declare const RouteErrorContext: React.Context<any>;
export {};
