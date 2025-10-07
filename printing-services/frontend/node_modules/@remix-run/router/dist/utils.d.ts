import type { Location, Path, To } from "./history";
/**
 * Map of routeId -> data returned from a loader/action/error
 */
export interface RouteData {
    [routeId: string]: any;
}
export declare enum ResultType {
    data = "data",
    deferred = "deferred",
    redirect = "redirect",
    error = "error"
}
/**
 * Successful result from a loader or action
 */
export interface SuccessResult {
    type: ResultType.data;
    data: unknown;
    statusCode?: number;
    headers?: Headers;
}
/**
 * Successful defer() result from a loader or action
 */
export interface DeferredResult {
    type: ResultType.deferred;
    deferredData: DeferredData;
    statusCode?: number;
    headers?: Headers;
}
/**
 * Redirect result from a loader or action
 */
export interface RedirectResult {
    type: ResultType.redirect;
    response: Response;
}
/**
 * Unsuccessful result from a loader or action
 */
export interface ErrorResult {
    type: ResultType.error;
    error: unknown;
    statusCode?: number;
    headers?: Headers;
}
/**
 * Result from a loader or action - potentially successful or unsuccessful
 */
export type DataResult = SuccessResult | DeferredResult | RedirectResult | ErrorResult;
type LowerCaseFormMethod = "get" | "post" | "put" | "patch" | "delete";
type UpperCaseFormMethod = Uppercase<LowerCaseFormMethod>;
/**
 * Users can specify either lowercase or uppercase form methods on `<Form>`,
 * useSubmit(), `<fetcher.Form>`, etc.
 */
export type HTMLFormMethod = LowerCaseFormMethod | UpperCaseFormMethod;
/**
 * Active navigation/fetcher form methods are exposed in lowercase on the
 * RouterState
 */
export type FormMethod = LowerCaseFormMethod;
export type MutationFormMethod = Exclude<FormMethod, "get">;
/**
 * In v7, active navigation/fetcher form methods are exposed in uppercase on the
 * RouterState.  This is to align with the normalization done via fetch().
 */
export type V7_FormMethod = UpperCaseFormMethod;
export type V7_MutationFormMethod = Exclude<V7_FormMethod, "GET">;
export type FormEncType = "application/x-www-form-urlencoded" | "multipart/form-data" | "application/json" | "text/plain";
type JsonObject = {
    [Key in string]: JsonValue;
} & {
    [Key in string]?: JsonValue | undefined;
};
type JsonArray = JsonValue[] | readonly JsonValue[];
type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonObject | JsonArray;
/**
 * @private
 * Internal interface to pass around for action submissions, not intended for
 * external consumption
 */
export type Submission = {
    formMethod: FormMethod | V7_FormMethod;
    formAction: string;
    formEncType: FormEncType;
    formData: FormData;
    json: undefined;
    text: undefined;
} | {
    formMethod: FormMethod | V7_FormMethod;
    formAction: string;
    formEncType: FormEncType;
    formData: undefined;
    json: JsonValue;
    text: undefined;
} | {
    formMethod: FormMethod | V7_FormMethod;
    formAction: string;
    formEncType: FormEncType;
    formData: undefined;
    json: undefined;
    text: string;
};
/**
 * @private
 * Arguments passed to route loader/action functions.  Same for now but we keep
 * this as a private implementation detail in case they diverge in the future.
 */
interface DataFunctionArgs<Context> {
    request: Request;
    params: Params;
    context?: Context;
}
/**
 * Arguments passed to loader functions
 */
export interface LoaderFunctionArgs<Context = any> extends DataFunctionArgs<Context> {
}
/**
 * Arguments passed to action functions
 */
export interface ActionFunctionArgs<Context = any> extends DataFunctionArgs<Context> {
}
/**
 * Loaders and actions can return anything except `undefined` (`null` is a
 * valid return value if there is no data to return).  Responses are preferred
 * and will ease any future migration to Remix
 */
type DataFunctionValue = Response | NonNullable<unknown> | null;
type DataFunctionReturnValue = Promise<DataFunctionValue> | DataFunctionValue;
/**
 * Route loader function signature
 */
export type LoaderFunction<Context = any> = {
    (args: LoaderFunctionArgs<Context>, handlerCtx?: unknown): DataFunctionReturnValue;
} & {
    hydrate?: boolean;
};
/**
 * Route action function signature
 */
export interface ActionFunction<Context = any> {
    (args: ActionFunctionArgs<Context>, handlerCtx?: unknown): DataFunctionReturnValue;
}
/**
 * Arguments passed to shouldRevalidate function
 */
export interface ShouldRevalidateFunctionArgs {
    currentUrl: URL;
    currentParams: AgnosticDataRouteMatch["params"];
    nextUrl: URL;
    nextParams: AgnosticDataRouteMatch["params"];
    formMethod?: Submission["formMethod"];
    formAction?: Submission["formAction"];
    formEncType?: Submission["formEncType"];
    text?: Submission["text"];
    formData?: Submission["formData"];
    json?: Submission["json"];
    actionStatus?: number;
    actionResult?: any;
    defaultShouldRevalidate: boolean;
}
/**
 * Route shouldRevalidate function signature.  This runs after any submission
 * (navigation or fetcher), so we flatten the navigation/fetcher submission
 * onto the arguments.  It shouldn't matter whether it came from a navigation
 * or a fetcher, what really matters is the URLs and the formData since loaders
 * have to re-run based on the data models that were potentially mutated.
 */
export interface ShouldRevalidateFunction {
    (args: ShouldRevalidateFunctionArgs): boolean;
}
/**
 * Function provided by the framework-aware layers to set `hasErrorBoundary`
 * from the framework-aware `errorElement` prop
 *
 * @deprecated Use `mapRouteProperties` instead
 */
export interface DetectErrorBoundaryFunction {
    (route: AgnosticRouteObject): boolean;
}
export interface DataStrategyMatch extends AgnosticRouteMatch<string, AgnosticDataRouteObject> {
    shouldLoad: boolean;
    resolve: (handlerOverride?: (handler: (ctx?: unknown) => DataFunctionReturnValue) => DataFunctionReturnValue) => Promise<DataStrategyResult>;
}
export interface DataStrategyFunctionArgs<Context = any> extends DataFunctionArgs<Context> {
    matches: DataStrategyMatch[];
    fetcherKey: string | null;
}
/**
 * Result from a loader or action called via dataStrategy
 */
export interface DataStrategyResult {
    type: "data" | "error";
    result: unknown;
}
export interface DataStrategyFunction {
    (args: DataStrategyFunctionArgs): Promise<Record<string, DataStrategyResult>>;
}
export type AgnosticPatchRoutesOnNavigationFunctionArgs<O extends AgnosticRouteObject = AgnosticRouteObject, M extends AgnosticRouteMatch = AgnosticRouteMatch> = {
    signal: AbortSignal;
    path: string;
    matches: M[];
    fetcherKey: string | undefined;
    patch: (routeId: string | null, children: O[]) => void;
};
export type AgnosticPatchRoutesOnNavigationFunction<O extends AgnosticRouteObject = AgnosticRouteObject, M extends AgnosticRouteMatch = AgnosticRouteMatch> = (opts: AgnosticPatchRoutesOnNavigationFunctionArgs<O, M>) => void | Promise<void>;
/**
 * Function provided by the framework-aware layers to set any framework-specific
 * properties from framework-agnostic properties
 */
export interface MapRoutePropertiesFunction {
    (route: AgnosticRouteObject): {
        hasErrorBoundary: boolean;
    } & Record<string, any>;
}
/**
 * Keys we cannot change from within a lazy() function. We spread all other keys
 * onto the route. Either they're meaningful to the router, or they'll get
 * ignored.
 */
export type ImmutableRouteKey = "lazy" | "caseSensitive" | "path" | "id" | "index" | "children";
export declare const immutableRouteKeys: Set<ImmutableRouteKey>;
type RequireOne<T, Key = keyof T> = Exclude<{
    [K in keyof T]: K extends Key ? Omit<T, K> & Required<Pick<T, K>> : never;
}[keyof T], undefined>;
/**
 * lazy() function to load a route definition, which can add non-matching
 * related properties to a route
 */
export interface LazyRouteFunction<R extends AgnosticRouteObject> {
    (): Promise<RequireOne<Omit<R, ImmutableRouteKey>>>;
}
/**
 * Base RouteObject with common props shared by all types of routes
 */
type AgnosticBaseRouteObject = {
    caseSensitive?: boolean;
    path?: string;
    id?: string;
    loader?: LoaderFunction | boolean;
    action?: ActionFunction | boolean;
    hasErrorBoundary?: boolean;
    shouldRevalidate?: ShouldRevalidateFunction;
    handle?: any;
    lazy?: LazyRouteFunction<AgnosticBaseRouteObject>;
};
/**
 * Index routes must not have children
 */
export type AgnosticIndexRouteObject = AgnosticBaseRouteObject & {
    children?: undefined;
    index: true;
};
/**
 * Non-index routes may have children, but cannot have index
 */
export type AgnosticNonIndexRouteObject = AgnosticBaseRouteObject & {
    children?: AgnosticRouteObject[];
    index?: false;
};
/**
 * A route object represents a logical route, with (optionally) its child
 * routes organized in a tree-like structure.
 */
export type AgnosticRouteObject = AgnosticIndexRouteObject | AgnosticNonIndexRouteObject;
export type AgnosticDataIndexRouteObject = AgnosticIndexRouteObject & {
    id: string;
};
export type AgnosticDataNonIndexRouteObject = AgnosticNonIndexRouteObject & {
    children?: AgnosticDataRouteObject[];
    id: string;
};
/**
 * A data route object, which is just a RouteObject with a required unique ID
 */
export type AgnosticDataRouteObject = AgnosticDataIndexRouteObject | AgnosticDataNonIndexRouteObject;
export type RouteManifest = Record<string, AgnosticDataRouteObject | undefined>;
type _PathParam<Path extends string> = Path extends `${infer L}/${infer R}` ? _PathParam<L> | _PathParam<R> : Path extends `:${infer Param}` ? Param extends `${infer Optional}?` ? Optional : Param : never;
/**
 * Examples:
 * "/a/b/*" -> "*"
 * ":a" -> "a"
 * "/a/:b" -> "b"
 * "/a/blahblahblah:b" -> "b"
 * "/:a/:b" -> "a" | "b"
 * "/:a/b/:c/*" -> "a" | "c" | "*"
 */
export type PathParam<Path extends string> = Path extends "*" | "/*" ? "*" : Path extends `${infer Rest}/*` ? "*" | _PathParam<Rest> : _PathParam<Path>;
export type ParamParseKey<Segment extends string> = [
    PathParam<Segment>
] extends [never] ? string : PathParam<Segment>;
/**
 * The parameters that were parsed from the URL path.
 */
export type Params<Key extends string = string> = {
    readonly [key in Key]: string | undefined;
};
/**
 * A RouteMatch contains info about how a route matched a URL.
 */
export interface AgnosticRouteMatch<ParamKey extends string = string, RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject> {
    /**
     * The names and values of dynamic parameters in the URL.
     */
    params: Params<ParamKey>;
    /**
     * The portion of the URL pathname that was matched.
     */
    pathname: string;
    /**
     * The portion of the URL pathname that was matched before child routes.
     */
    pathnameBase: string;
    /**
     * The route object that was used to match.
     */
    route: RouteObjectType;
}
export interface AgnosticDataRouteMatch extends AgnosticRouteMatch<string, AgnosticDataRouteObject> {
}
export declare function convertRoutesToDataRoutes(routes: AgnosticRouteObject[], mapRouteProperties: MapRoutePropertiesFunction, parentPath?: string[], manifest?: RouteManifest): AgnosticDataRouteObject[];
/**
 * Matches the given routes to a location and returns the match data.
 *
 * @see https://reactrouter.com/v6/utils/match-routes
 */
export declare function matchRoutes<RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject>(routes: RouteObjectType[], locationArg: Partial<Location> | string, basename?: string): AgnosticRouteMatch<string, RouteObjectType>[] | null;
export declare function matchRoutesImpl<RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject>(routes: RouteObjectType[], locationArg: Partial<Location> | string, basename: string, allowPartial: boolean): AgnosticRouteMatch<string, RouteObjectType>[] | null;
export interface UIMatch<Data = unknown, Handle = unknown> {
    id: string;
    pathname: string;
    params: AgnosticRouteMatch["params"];
    data: Data;
    handle: Handle;
}
export declare function convertRouteMatchToUiMatch(match: AgnosticDataRouteMatch, loaderData: RouteData): UIMatch;
/**
 * Returns a path with params interpolated.
 *
 * @see https://reactrouter.com/v6/utils/generate-path
 */
export declare function generatePath<Path extends string>(originalPath: Path, params?: {
    [key in PathParam<Path>]: string | null;
}): string;
/**
 * A PathPattern is used to match on some portion of a URL pathname.
 */
export interface PathPattern<Path extends string = string> {
    /**
     * A string to match against a URL pathname. May contain `:id`-style segments
     * to indicate placeholders for dynamic parameters. May also end with `/*` to
     * indicate matching the rest of the URL pathname.
     */
    path: Path;
    /**
     * Should be `true` if the static portions of the `path` should be matched in
     * the same case.
     */
    caseSensitive?: boolean;
    /**
     * Should be `true` if this pattern should match the entire URL pathname.
     */
    end?: boolean;
}
/**
 * A PathMatch contains info about how a PathPattern matched on a URL pathname.
 */
export interface PathMatch<ParamKey extends string = string> {
    /**
     * The names and values of dynamic parameters in the URL.
     */
    params: Params<ParamKey>;
    /**
     * The portion of the URL pathname that was matched.
     */
    pathname: string;
    /**
     * The portion of the URL pathname that was matched before child routes.
     */
    pathnameBase: string;
    /**
     * The pattern that was used to match.
     */
    pattern: PathPattern;
}
/**
 * Performs pattern matching on a URL pathname and returns information about
 * the match.
 *
 * @see https://reactrouter.com/v6/utils/match-path
 */
export declare function matchPath<ParamKey extends ParamParseKey<Path>, Path extends string>(pattern: PathPattern<Path> | Path, pathname: string): PathMatch<ParamKey> | null;
export declare function decodePath(value: string): string;
/**
 * @private
 */
export declare function stripBasename(pathname: string, basename: string): string | null;
/**
 * Returns a resolved path object relative to the given pathname.
 *
 * @see https://reactrouter.com/v6/utils/resolve-path
 */
export declare function resolvePath(to: To, fromPathname?: string): Path;
/**
 * @private
 *
 * When processing relative navigation we want to ignore ancestor routes that
 * do not contribute to the path, such that index/pathless layout routes don't
 * interfere.
 *
 * For example, when moving a route element into an index route and/or a
 * pathless layout route, relative link behavior contained within should stay
 * the same.  Both of the following examples should link back to the root:
 *
 *   <Route path="/">
 *     <Route path="accounts" element={<Link to=".."}>
 *   </Route>
 *
 *   <Route path="/">
 *     <Route path="accounts">
 *       <Route element={<AccountsLayout />}>       // <-- Does not contribute
 *         <Route index element={<Link to=".."} />  // <-- Does not contribute
 *       </Route
 *     </Route>
 *   </Route>
 */
export declare function getPathContributingMatches<T extends AgnosticRouteMatch = AgnosticRouteMatch>(matches: T[]): T[];
export declare function getResolveToMatches<T extends AgnosticRouteMatch = AgnosticRouteMatch>(matches: T[], v7_relativeSplatPath: boolean): string[];
/**
 * @private
 */
export declare function resolveTo(toArg: To, routePathnames: string[], locationPathname: string, isPathRelative?: boolean): Path;
/**
 * @private
 */
export declare function getToPathname(to: To): string | undefined;
/**
 * @private
 */
export declare const joinPaths: (paths: string[]) => string;
/**
 * @private
 */
export declare const normalizePathname: (pathname: string) => string;
/**
 * @private
 */
export declare const normalizeSearch: (search: string) => string;
/**
 * @private
 */
export declare const normalizeHash: (hash: string) => string;
export type JsonFunction = <Data>(data: Data, init?: number | ResponseInit) => Response;
/**
 * This is a shortcut for creating `application/json` responses. Converts `data`
 * to JSON and sets the `Content-Type` header.
 *
 * @deprecated The `json` method is deprecated in favor of returning raw objects.
 * This method will be removed in v7.
 */
export declare const json: JsonFunction;
export declare class DataWithResponseInit<D> {
    type: string;
    data: D;
    init: ResponseInit | null;
    constructor(data: D, init?: ResponseInit);
}
/**
 * Create "responses" that contain `status`/`headers` without forcing
 * serialization into an actual `Response` - used by Remix single fetch
 */
export declare function data<D>(data: D, init?: number | ResponseInit): DataWithResponseInit<D>;
export interface TrackedPromise extends Promise<any> {
    _tracked?: boolean;
    _data?: any;
    _error?: any;
}
export declare class AbortedDeferredError extends Error {
}
export declare class DeferredData {
    private pendingKeysSet;
    private controller;
    private abortPromise;
    private unlistenAbortSignal;
    private subscribers;
    data: Record<string, unknown>;
    init?: ResponseInit;
    deferredKeys: string[];
    constructor(data: Record<string, unknown>, responseInit?: ResponseInit);
    private trackPromise;
    private onSettle;
    private emit;
    subscribe(fn: (aborted: boolean, settledKey?: string) => void): () => boolean;
    cancel(): void;
    resolveData(signal: AbortSignal): Promise<boolean>;
    get done(): boolean;
    get unwrappedData(): {};
    get pendingKeys(): string[];
}
export type DeferFunction = (data: Record<string, unknown>, init?: number | ResponseInit) => DeferredData;
/**
 * @deprecated The `defer` method is deprecated in favor of returning raw
 * objects. This method will be removed in v7.
 */
export declare const defer: DeferFunction;
export type RedirectFunction = (url: string, init?: number | ResponseInit) => Response;
/**
 * A redirect response. Sets the status code and the `Location` header.
 * Defaults to "302 Found".
 */
export declare const redirect: RedirectFunction;
/**
 * A redirect response that will force a document reload to the new location.
 * Sets the status code and the `Location` header.
 * Defaults to "302 Found".
 */
export declare const redirectDocument: RedirectFunction;
/**
 * A redirect response that will perform a `history.replaceState` instead of a
 * `history.pushState` for client-side navigation redirects.
 * Sets the status code and the `Location` header.
 * Defaults to "302 Found".
 */
export declare const replace: RedirectFunction;
export type ErrorResponse = {
    status: number;
    statusText: string;
    data: any;
};
/**
 * @private
 * Utility class we use to hold auto-unwrapped 4xx/5xx Response bodies
 *
 * We don't export the class for public use since it's an implementation
 * detail, but we export the interface above so folks can build their own
 * abstractions around instances via isRouteErrorResponse()
 */
export declare class ErrorResponseImpl implements ErrorResponse {
    status: number;
    statusText: string;
    data: any;
    private error?;
    private internal;
    constructor(status: number, statusText: string | undefined, data: any, internal?: boolean);
}
/**
 * Check if the given error is an ErrorResponse generated from a 4xx/5xx
 * Response thrown from an action/loader
 */
export declare function isRouteErrorResponse(error: any): error is ErrorResponse;
export {};
