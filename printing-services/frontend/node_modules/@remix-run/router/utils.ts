import type { Location, Path, To } from "./history";
import { invariant, parsePath, warning } from "./history";

/**
 * Map of routeId -> data returned from a loader/action/error
 */
export interface RouteData {
  [routeId: string]: any;
}

export enum ResultType {
  data = "data",
  deferred = "deferred",
  redirect = "redirect",
  error = "error",
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
  // We keep the raw Response for redirects so we can return it verbatim
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
export type DataResult =
  | SuccessResult
  | DeferredResult
  | RedirectResult
  | ErrorResult;

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

export type FormEncType =
  | "application/x-www-form-urlencoded"
  | "multipart/form-data"
  | "application/json"
  | "text/plain";

// Thanks https://github.com/sindresorhus/type-fest!
type JsonObject = { [Key in string]: JsonValue } & {
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
export type Submission =
  | {
      formMethod: FormMethod | V7_FormMethod;
      formAction: string;
      formEncType: FormEncType;
      formData: FormData;
      json: undefined;
      text: undefined;
    }
  | {
      formMethod: FormMethod | V7_FormMethod;
      formAction: string;
      formEncType: FormEncType;
      formData: undefined;
      json: JsonValue;
      text: undefined;
    }
  | {
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

// TODO: (v7) Change the defaults from any to unknown in and remove Remix wrappers:
//   ActionFunction, ActionFunctionArgs, LoaderFunction, LoaderFunctionArgs
//   Also, make them a type alias instead of an interface

/**
 * Arguments passed to loader functions
 */
export interface LoaderFunctionArgs<Context = any>
  extends DataFunctionArgs<Context> {}

/**
 * Arguments passed to action functions
 */
export interface ActionFunctionArgs<Context = any>
  extends DataFunctionArgs<Context> {}

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
  (
    args: LoaderFunctionArgs<Context>,
    handlerCtx?: unknown
  ): DataFunctionReturnValue;
} & { hydrate?: boolean };

/**
 * Route action function signature
 */
export interface ActionFunction<Context = any> {
  (
    args: ActionFunctionArgs<Context>,
    handlerCtx?: unknown
  ): DataFunctionReturnValue;
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

export interface DataStrategyMatch
  extends AgnosticRouteMatch<string, AgnosticDataRouteObject> {
  shouldLoad: boolean;
  resolve: (
    handlerOverride?: (
      handler: (ctx?: unknown) => DataFunctionReturnValue
    ) => DataFunctionReturnValue
  ) => Promise<DataStrategyResult>;
}

export interface DataStrategyFunctionArgs<Context = any>
  extends DataFunctionArgs<Context> {
  matches: DataStrategyMatch[];
  fetcherKey: string | null;
}

/**
 * Result from a loader or action called via dataStrategy
 */
export interface DataStrategyResult {
  type: "data" | "error";
  result: unknown; // data, Error, Response, DeferredData, DataWithResponseInit
}

export interface DataStrategyFunction {
  (args: DataStrategyFunctionArgs): Promise<Record<string, DataStrategyResult>>;
}

export type AgnosticPatchRoutesOnNavigationFunctionArgs<
  O extends AgnosticRouteObject = AgnosticRouteObject,
  M extends AgnosticRouteMatch = AgnosticRouteMatch
> = {
  signal: AbortSignal;
  path: string;
  matches: M[];
  fetcherKey: string | undefined;
  patch: (routeId: string | null, children: O[]) => void;
};

export type AgnosticPatchRoutesOnNavigationFunction<
  O extends AgnosticRouteObject = AgnosticRouteObject,
  M extends AgnosticRouteMatch = AgnosticRouteMatch
> = (
  opts: AgnosticPatchRoutesOnNavigationFunctionArgs<O, M>
) => void | Promise<void>;

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
export type ImmutableRouteKey =
  | "lazy"
  | "caseSensitive"
  | "path"
  | "id"
  | "index"
  | "children";

export const immutableRouteKeys = new Set<ImmutableRouteKey>([
  "lazy",
  "caseSensitive",
  "path",
  "id",
  "index",
  "children",
]);

type RequireOne<T, Key = keyof T> = Exclude<
  {
    [K in keyof T]: K extends Key ? Omit<T, K> & Required<Pick<T, K>> : never;
  }[keyof T],
  undefined
>;

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
export type AgnosticRouteObject =
  | AgnosticIndexRouteObject
  | AgnosticNonIndexRouteObject;

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
export type AgnosticDataRouteObject =
  | AgnosticDataIndexRouteObject
  | AgnosticDataNonIndexRouteObject;

export type RouteManifest = Record<string, AgnosticDataRouteObject | undefined>;

// Recursive helper for finding path parameters in the absence of wildcards
type _PathParam<Path extends string> =
  // split path into individual path segments
  Path extends `${infer L}/${infer R}`
    ? _PathParam<L> | _PathParam<R>
    : // find params after `:`
    Path extends `:${infer Param}`
    ? Param extends `${infer Optional}?`
      ? Optional
      : Param
    : // otherwise, there aren't any params present
      never;

/**
 * Examples:
 * "/a/b/*" -> "*"
 * ":a" -> "a"
 * "/a/:b" -> "b"
 * "/a/blahblahblah:b" -> "b"
 * "/:a/:b" -> "a" | "b"
 * "/:a/b/:c/*" -> "a" | "c" | "*"
 */
export type PathParam<Path extends string> =
  // check if path is just a wildcard
  Path extends "*" | "/*"
    ? "*"
    : // look for wildcard at the end of the path
    Path extends `${infer Rest}/*`
    ? "*" | _PathParam<Rest>
    : // look for params in the absence of wildcards
      _PathParam<Path>;

// Attempt to parse the given string segment. If it fails, then just return the
// plain string type as a default fallback. Otherwise, return the union of the
// parsed string literals that were referenced as dynamic segments in the route.
export type ParamParseKey<Segment extends string> =
  // if you could not find path params, fallback to `string`
  [PathParam<Segment>] extends [never] ? string : PathParam<Segment>;

/**
 * The parameters that were parsed from the URL path.
 */
export type Params<Key extends string = string> = {
  readonly [key in Key]: string | undefined;
};

/**
 * A RouteMatch contains info about how a route matched a URL.
 */
export interface AgnosticRouteMatch<
  ParamKey extends string = string,
  RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject
> {
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

export interface AgnosticDataRouteMatch
  extends AgnosticRouteMatch<string, AgnosticDataRouteObject> {}

function isIndexRoute(
  route: AgnosticRouteObject
): route is AgnosticIndexRouteObject {
  return route.index === true;
}

// Walk the route tree generating unique IDs where necessary, so we are working
// solely with AgnosticDataRouteObject's within the Router
export function convertRoutesToDataRoutes(
  routes: AgnosticRouteObject[],
  mapRouteProperties: MapRoutePropertiesFunction,
  parentPath: string[] = [],
  manifest: RouteManifest = {}
): AgnosticDataRouteObject[] {
  return routes.map((route, index) => {
    let treePath = [...parentPath, String(index)];
    let id = typeof route.id === "string" ? route.id : treePath.join("-");
    invariant(
      route.index !== true || !route.children,
      `Cannot specify children on an index route`
    );
    invariant(
      !manifest[id],
      `Found a route id collision on id "${id}".  Route ` +
        "id's must be globally unique within Data Router usages"
    );

    if (isIndexRoute(route)) {
      let indexRoute: AgnosticDataIndexRouteObject = {
        ...route,
        ...mapRouteProperties(route),
        id,
      };
      manifest[id] = indexRoute;
      return indexRoute;
    } else {
      let pathOrLayoutRoute: AgnosticDataNonIndexRouteObject = {
        ...route,
        ...mapRouteProperties(route),
        id,
        children: undefined,
      };
      manifest[id] = pathOrLayoutRoute;

      if (route.children) {
        pathOrLayoutRoute.children = convertRoutesToDataRoutes(
          route.children,
          mapRouteProperties,
          treePath,
          manifest
        );
      }

      return pathOrLayoutRoute;
    }
  });
}

/**
 * Matches the given routes to a location and returns the match data.
 *
 * @see https://reactrouter.com/v6/utils/match-routes
 */
export function matchRoutes<
  RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject
>(
  routes: RouteObjectType[],
  locationArg: Partial<Location> | string,
  basename = "/"
): AgnosticRouteMatch<string, RouteObjectType>[] | null {
  return matchRoutesImpl(routes, locationArg, basename, false);
}

export function matchRoutesImpl<
  RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject
>(
  routes: RouteObjectType[],
  locationArg: Partial<Location> | string,
  basename: string,
  allowPartial: boolean
): AgnosticRouteMatch<string, RouteObjectType>[] | null {
  let location =
    typeof locationArg === "string" ? parsePath(locationArg) : locationArg;

  let pathname = stripBasename(location.pathname || "/", basename);

  if (pathname == null) {
    return null;
  }

  let branches = flattenRoutes(routes);
  rankRouteBranches(branches);

  let matches = null;
  for (let i = 0; matches == null && i < branches.length; ++i) {
    // Incoming pathnames are generally encoded from either window.location
    // or from router.navigate, but we want to match against the unencoded
    // paths in the route definitions.  Memory router locations won't be
    // encoded here but there also shouldn't be anything to decode so this
    // should be a safe operation.  This avoids needing matchRoutes to be
    // history-aware.
    let decoded = decodePath(pathname);
    matches = matchRouteBranch<string, RouteObjectType>(
      branches[i],
      decoded,
      allowPartial
    );
  }

  return matches;
}

export interface UIMatch<Data = unknown, Handle = unknown> {
  id: string;
  pathname: string;
  params: AgnosticRouteMatch["params"];
  data: Data;
  handle: Handle;
}

export function convertRouteMatchToUiMatch(
  match: AgnosticDataRouteMatch,
  loaderData: RouteData
): UIMatch {
  let { route, pathname, params } = match;
  return {
    id: route.id,
    pathname,
    params,
    data: loaderData[route.id],
    handle: route.handle,
  };
}

interface RouteMeta<
  RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject
> {
  relativePath: string;
  caseSensitive: boolean;
  childrenIndex: number;
  route: RouteObjectType;
}

interface RouteBranch<
  RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject
> {
  path: string;
  score: number;
  routesMeta: RouteMeta<RouteObjectType>[];
}

function flattenRoutes<
  RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject
>(
  routes: RouteObjectType[],
  branches: RouteBranch<RouteObjectType>[] = [],
  parentsMeta: RouteMeta<RouteObjectType>[] = [],
  parentPath = ""
): RouteBranch<RouteObjectType>[] {
  let flattenRoute = (
    route: RouteObjectType,
    index: number,
    relativePath?: string
  ) => {
    let meta: RouteMeta<RouteObjectType> = {
      relativePath:
        relativePath === undefined ? route.path || "" : relativePath,
      caseSensitive: route.caseSensitive === true,
      childrenIndex: index,
      route,
    };

    if (meta.relativePath.startsWith("/")) {
      invariant(
        meta.relativePath.startsWith(parentPath),
        `Absolute route path "${meta.relativePath}" nested under path ` +
          `"${parentPath}" is not valid. An absolute child route path ` +
          `must start with the combined path of all its parent routes.`
      );

      meta.relativePath = meta.relativePath.slice(parentPath.length);
    }

    let path = joinPaths([parentPath, meta.relativePath]);
    let routesMeta = parentsMeta.concat(meta);

    // Add the children before adding this route to the array, so we traverse the
    // route tree depth-first and child routes appear before their parents in
    // the "flattened" version.
    if (route.children && route.children.length > 0) {
      invariant(
        // Our types know better, but runtime JS may not!
        // @ts-expect-error
        route.index !== true,
        `Index routes must not have child routes. Please remove ` +
          `all child routes from route path "${path}".`
      );
      flattenRoutes(route.children, branches, routesMeta, path);
    }

    // Routes without a path shouldn't ever match by themselves unless they are
    // index routes, so don't add them to the list of possible branches.
    if (route.path == null && !route.index) {
      return;
    }

    branches.push({
      path,
      score: computeScore(path, route.index),
      routesMeta,
    });
  };
  routes.forEach((route, index) => {
    // coarse-grain check for optional params
    if (route.path === "" || !route.path?.includes("?")) {
      flattenRoute(route, index);
    } else {
      for (let exploded of explodeOptionalSegments(route.path)) {
        flattenRoute(route, index, exploded);
      }
    }
  });

  return branches;
}

/**
 * Computes all combinations of optional path segments for a given path,
 * excluding combinations that are ambiguous and of lower priority.
 *
 * For example, `/one/:two?/three/:four?/:five?` explodes to:
 * - `/one/three`
 * - `/one/:two/three`
 * - `/one/three/:four`
 * - `/one/three/:five`
 * - `/one/:two/three/:four`
 * - `/one/:two/three/:five`
 * - `/one/three/:four/:five`
 * - `/one/:two/three/:four/:five`
 */
function explodeOptionalSegments(path: string): string[] {
  let segments = path.split("/");
  if (segments.length === 0) return [];

  let [first, ...rest] = segments;

  // Optional path segments are denoted by a trailing `?`
  let isOptional = first.endsWith("?");
  // Compute the corresponding required segment: `foo?` -> `foo`
  let required = first.replace(/\?$/, "");

  if (rest.length === 0) {
    // Intepret empty string as omitting an optional segment
    // `["one", "", "three"]` corresponds to omitting `:two` from `/one/:two?/three` -> `/one/three`
    return isOptional ? [required, ""] : [required];
  }

  let restExploded = explodeOptionalSegments(rest.join("/"));

  let result: string[] = [];

  // All child paths with the prefix.  Do this for all children before the
  // optional version for all children, so we get consistent ordering where the
  // parent optional aspect is preferred as required.  Otherwise, we can get
  // child sections interspersed where deeper optional segments are higher than
  // parent optional segments, where for example, /:two would explode _earlier_
  // then /:one.  By always including the parent as required _for all children_
  // first, we avoid this issue
  result.push(
    ...restExploded.map((subpath) =>
      subpath === "" ? required : [required, subpath].join("/")
    )
  );

  // Then, if this is an optional value, add all child versions without
  if (isOptional) {
    result.push(...restExploded);
  }

  // for absolute paths, ensure `/` instead of empty segment
  return result.map((exploded) =>
    path.startsWith("/") && exploded === "" ? "/" : exploded
  );
}

function rankRouteBranches(branches: RouteBranch[]): void {
  branches.sort((a, b) =>
    a.score !== b.score
      ? b.score - a.score // Higher score first
      : compareIndexes(
          a.routesMeta.map((meta) => meta.childrenIndex),
          b.routesMeta.map((meta) => meta.childrenIndex)
        )
  );
}

const paramRe = /^:[\w-]+$/;
const dynamicSegmentValue = 3;
const indexRouteValue = 2;
const emptySegmentValue = 1;
const staticSegmentValue = 10;
const splatPenalty = -2;
const isSplat = (s: string) => s === "*";

function computeScore(path: string, index: boolean | undefined): number {
  let segments = path.split("/");
  let initialScore = segments.length;
  if (segments.some(isSplat)) {
    initialScore += splatPenalty;
  }

  if (index) {
    initialScore += indexRouteValue;
  }

  return segments
    .filter((s) => !isSplat(s))
    .reduce(
      (score, segment) =>
        score +
        (paramRe.test(segment)
          ? dynamicSegmentValue
          : segment === ""
          ? emptySegmentValue
          : staticSegmentValue),
      initialScore
    );
}

function compareIndexes(a: number[], b: number[]): number {
  let siblings =
    a.length === b.length && a.slice(0, -1).every((n, i) => n === b[i]);

  return siblings
    ? // If two routes are siblings, we should try to match the earlier sibling
      // first. This allows people to have fine-grained control over the matching
      // behavior by simply putting routes with identical paths in the order they
      // want them tried.
      a[a.length - 1] - b[b.length - 1]
    : // Otherwise, it doesn't really make sense to rank non-siblings by index,
      // so they sort equally.
      0;
}

function matchRouteBranch<
  ParamKey extends string = string,
  RouteObjectType extends AgnosticRouteObject = AgnosticRouteObject
>(
  branch: RouteBranch<RouteObjectType>,
  pathname: string,
  allowPartial = false
): AgnosticRouteMatch<ParamKey, RouteObjectType>[] | null {
  let { routesMeta } = branch;

  let matchedParams = {};
  let matchedPathname = "/";
  let matches: AgnosticRouteMatch<ParamKey, RouteObjectType>[] = [];
  for (let i = 0; i < routesMeta.length; ++i) {
    let meta = routesMeta[i];
    let end = i === routesMeta.length - 1;
    let remainingPathname =
      matchedPathname === "/"
        ? pathname
        : pathname.slice(matchedPathname.length) || "/";
    let match = matchPath(
      { path: meta.relativePath, caseSensitive: meta.caseSensitive, end },
      remainingPathname
    );

    let route = meta.route;

    if (
      !match &&
      end &&
      allowPartial &&
      !routesMeta[routesMeta.length - 1].route.index
    ) {
      match = matchPath(
        {
          path: meta.relativePath,
          caseSensitive: meta.caseSensitive,
          end: false,
        },
        remainingPathname
      );
    }

    if (!match) {
      return null;
    }

    Object.assign(matchedParams, match.params);

    matches.push({
      // TODO: Can this as be avoided?
      params: matchedParams as Params<ParamKey>,
      pathname: joinPaths([matchedPathname, match.pathname]),
      pathnameBase: normalizePathname(
        joinPaths([matchedPathname, match.pathnameBase])
      ),
      route,
    });

    if (match.pathnameBase !== "/") {
      matchedPathname = joinPaths([matchedPathname, match.pathnameBase]);
    }
  }

  return matches;
}

/**
 * Returns a path with params interpolated.
 *
 * @see https://reactrouter.com/v6/utils/generate-path
 */
export function generatePath<Path extends string>(
  originalPath: Path,
  params: {
    [key in PathParam<Path>]: string | null;
  } = {} as any
): string {
  let path: string = originalPath;
  if (path.endsWith("*") && path !== "*" && !path.endsWith("/*")) {
    warning(
      false,
      `Route path "${path}" will be treated as if it were ` +
        `"${path.replace(/\*$/, "/*")}" because the \`*\` character must ` +
        `always follow a \`/\` in the pattern. To get rid of this warning, ` +
        `please change the route path to "${path.replace(/\*$/, "/*")}".`
    );
    path = path.replace(/\*$/, "/*") as Path;
  }

  // ensure `/` is added at the beginning if the path is absolute
  const prefix = path.startsWith("/") ? "/" : "";

  const stringify = (p: any) =>
    p == null ? "" : typeof p === "string" ? p : String(p);

  const segments = path
    .split(/\/+/)
    .map((segment, index, array) => {
      const isLastSegment = index === array.length - 1;

      // only apply the splat if it's the last segment
      if (isLastSegment && segment === "*") {
        const star = "*" as PathParam<Path>;
        // Apply the splat
        return stringify(params[star]);
      }

      const keyMatch = segment.match(/^:([\w-]+)(\??)$/);
      if (keyMatch) {
        const [, key, optional] = keyMatch;
        let param = params[key as PathParam<Path>];
        invariant(optional === "?" || param != null, `Missing ":${key}" param`);
        return stringify(param);
      }

      // Remove any optional markers from optional static segments
      return segment.replace(/\?$/g, "");
    })
    // Remove empty segments
    .filter((segment) => !!segment);

  return prefix + segments.join("/");
}

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

type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

/**
 * Performs pattern matching on a URL pathname and returns information about
 * the match.
 *
 * @see https://reactrouter.com/v6/utils/match-path
 */
export function matchPath<
  ParamKey extends ParamParseKey<Path>,
  Path extends string
>(
  pattern: PathPattern<Path> | Path,
  pathname: string
): PathMatch<ParamKey> | null {
  if (typeof pattern === "string") {
    pattern = { path: pattern, caseSensitive: false, end: true };
  }

  let [matcher, compiledParams] = compilePath(
    pattern.path,
    pattern.caseSensitive,
    pattern.end
  );

  let match = pathname.match(matcher);
  if (!match) return null;

  let matchedPathname = match[0];
  let pathnameBase = matchedPathname.replace(/(.)\/+$/, "$1");
  let captureGroups = match.slice(1);
  let params: Params = compiledParams.reduce<Mutable<Params>>(
    (memo, { paramName, isOptional }, index) => {
      // We need to compute the pathnameBase here using the raw splat value
      // instead of using params["*"] later because it will be decoded then
      if (paramName === "*") {
        let splatValue = captureGroups[index] || "";
        pathnameBase = matchedPathname
          .slice(0, matchedPathname.length - splatValue.length)
          .replace(/(.)\/+$/, "$1");
      }

      const value = captureGroups[index];
      if (isOptional && !value) {
        memo[paramName] = undefined;
      } else {
        memo[paramName] = (value || "").replace(/%2F/g, "/");
      }
      return memo;
    },
    {}
  );

  return {
    params,
    pathname: matchedPathname,
    pathnameBase,
    pattern,
  };
}

type CompiledPathParam = { paramName: string; isOptional?: boolean };

function compilePath(
  path: string,
  caseSensitive = false,
  end = true
): [RegExp, CompiledPathParam[]] {
  warning(
    path === "*" || !path.endsWith("*") || path.endsWith("/*"),
    `Route path "${path}" will be treated as if it were ` +
      `"${path.replace(/\*$/, "/*")}" because the \`*\` character must ` +
      `always follow a \`/\` in the pattern. To get rid of this warning, ` +
      `please change the route path to "${path.replace(/\*$/, "/*")}".`
  );

  let params: CompiledPathParam[] = [];
  let regexpSource =
    "^" +
    path
      .replace(/\/*\*?$/, "") // Ignore trailing / and /*, we'll handle it below
      .replace(/^\/*/, "/") // Make sure it has a leading /
      .replace(/[\\.*+^${}|()[\]]/g, "\\$&") // Escape special regex chars
      .replace(
        /\/:([\w-]+)(\?)?/g,
        (_: string, paramName: string, isOptional) => {
          params.push({ paramName, isOptional: isOptional != null });
          return isOptional ? "/?([^\\/]+)?" : "/([^\\/]+)";
        }
      );

  if (path.endsWith("*")) {
    params.push({ paramName: "*" });
    regexpSource +=
      path === "*" || path === "/*"
        ? "(.*)$" // Already matched the initial /, just match the rest
        : "(?:\\/(.+)|\\/*)$"; // Don't include the / in params["*"]
  } else if (end) {
    // When matching to the end, ignore trailing slashes
    regexpSource += "\\/*$";
  } else if (path !== "" && path !== "/") {
    // If our path is non-empty and contains anything beyond an initial slash,
    // then we have _some_ form of path in our regex, so we should expect to
    // match only if we find the end of this path segment.  Look for an optional
    // non-captured trailing slash (to match a portion of the URL) or the end
    // of the path (if we've matched to the end).  We used to do this with a
    // word boundary but that gives false positives on routes like
    // /user-preferences since `-` counts as a word boundary.
    regexpSource += "(?:(?=\\/|$))";
  } else {
    // Nothing to match for "" or "/"
  }

  let matcher = new RegExp(regexpSource, caseSensitive ? undefined : "i");

  return [matcher, params];
}

export function decodePath(value: string) {
  try {
    return value
      .split("/")
      .map((v) => decodeURIComponent(v).replace(/\//g, "%2F"))
      .join("/");
  } catch (error) {
    warning(
      false,
      `The URL path "${value}" could not be decoded because it is is a ` +
        `malformed URL segment. This is probably due to a bad percent ` +
        `encoding (${error}).`
    );

    return value;
  }
}

/**
 * @private
 */
export function stripBasename(
  pathname: string,
  basename: string
): string | null {
  if (basename === "/") return pathname;

  if (!pathname.toLowerCase().startsWith(basename.toLowerCase())) {
    return null;
  }

  // We want to leave trailing slash behavior in the user's control, so if they
  // specify a basename with a trailing slash, we should support it
  let startIndex = basename.endsWith("/")
    ? basename.length - 1
    : basename.length;
  let nextChar = pathname.charAt(startIndex);
  if (nextChar && nextChar !== "/") {
    // pathname does not start with basename/
    return null;
  }

  return pathname.slice(startIndex) || "/";
}

/**
 * Returns a resolved path object relative to the given pathname.
 *
 * @see https://reactrouter.com/v6/utils/resolve-path
 */
export function resolvePath(to: To, fromPathname = "/"): Path {
  let {
    pathname: toPathname,
    search = "",
    hash = "",
  } = typeof to === "string" ? parsePath(to) : to;

  let pathname = toPathname
    ? toPathname.startsWith("/")
      ? toPathname
      : resolvePathname(toPathname, fromPathname)
    : fromPathname;

  return {
    pathname,
    search: normalizeSearch(search),
    hash: normalizeHash(hash),
  };
}

function resolvePathname(relativePath: string, fromPathname: string): string {
  let segments = fromPathname.replace(/\/+$/, "").split("/");
  let relativeSegments = relativePath.split("/");

  relativeSegments.forEach((segment) => {
    if (segment === "..") {
      // Keep the root "" segment so the pathname starts at /
      if (segments.length > 1) segments.pop();
    } else if (segment !== ".") {
      segments.push(segment);
    }
  });

  return segments.length > 1 ? segments.join("/") : "/";
}

function getInvalidPathError(
  char: string,
  field: string,
  dest: string,
  path: Partial<Path>
) {
  return (
    `Cannot include a '${char}' character in a manually specified ` +
    `\`to.${field}\` field [${JSON.stringify(
      path
    )}].  Please separate it out to the ` +
    `\`to.${dest}\` field. Alternatively you may provide the full path as ` +
    `a string in <Link to="..."> and the router will parse it for you.`
  );
}

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
export function getPathContributingMatches<
  T extends AgnosticRouteMatch = AgnosticRouteMatch
>(matches: T[]) {
  return matches.filter(
    (match, index) =>
      index === 0 || (match.route.path && match.route.path.length > 0)
  );
}

// Return the array of pathnames for the current route matches - used to
// generate the routePathnames input for resolveTo()
export function getResolveToMatches<
  T extends AgnosticRouteMatch = AgnosticRouteMatch
>(matches: T[], v7_relativeSplatPath: boolean) {
  let pathMatches = getPathContributingMatches(matches);

  // When v7_relativeSplatPath is enabled, use the full pathname for the leaf
  // match so we include splat values for "." links.  See:
  // https://github.com/remix-run/react-router/issues/11052#issuecomment-1836589329
  if (v7_relativeSplatPath) {
    return pathMatches.map((match, idx) =>
      idx === pathMatches.length - 1 ? match.pathname : match.pathnameBase
    );
  }

  return pathMatches.map((match) => match.pathnameBase);
}

/**
 * @private
 */
export function resolveTo(
  toArg: To,
  routePathnames: string[],
  locationPathname: string,
  isPathRelative = false
): Path {
  let to: Partial<Path>;
  if (typeof toArg === "string") {
    to = parsePath(toArg);
  } else {
    to = { ...toArg };

    invariant(
      !to.pathname || !to.pathname.includes("?"),
      getInvalidPathError("?", "pathname", "search", to)
    );
    invariant(
      !to.pathname || !to.pathname.includes("#"),
      getInvalidPathError("#", "pathname", "hash", to)
    );
    invariant(
      !to.search || !to.search.includes("#"),
      getInvalidPathError("#", "search", "hash", to)
    );
  }

  let isEmptyPath = toArg === "" || to.pathname === "";
  let toPathname = isEmptyPath ? "/" : to.pathname;

  let from: string;

  // Routing is relative to the current pathname if explicitly requested.
  //
  // If a pathname is explicitly provided in `to`, it should be relative to the
  // route context. This is explained in `Note on `<Link to>` values` in our
  // migration guide from v5 as a means of disambiguation between `to` values
  // that begin with `/` and those that do not. However, this is problematic for
  // `to` values that do not provide a pathname. `to` can simply be a search or
  // hash string, in which case we should assume that the navigation is relative
  // to the current location's pathname and *not* the route pathname.
  if (toPathname == null) {
    from = locationPathname;
  } else {
    let routePathnameIndex = routePathnames.length - 1;

    // With relative="route" (the default), each leading .. segment means
    // "go up one route" instead of "go up one URL segment".  This is a key
    // difference from how <a href> works and a major reason we call this a
    // "to" value instead of a "href".
    if (!isPathRelative && toPathname.startsWith("..")) {
      let toSegments = toPathname.split("/");

      while (toSegments[0] === "..") {
        toSegments.shift();
        routePathnameIndex -= 1;
      }

      to.pathname = toSegments.join("/");
    }

    from = routePathnameIndex >= 0 ? routePathnames[routePathnameIndex] : "/";
  }

  let path = resolvePath(to, from);

  // Ensure the pathname has a trailing slash if the original "to" had one
  let hasExplicitTrailingSlash =
    toPathname && toPathname !== "/" && toPathname.endsWith("/");
  // Or if this was a link to the current path which has a trailing slash
  let hasCurrentTrailingSlash =
    (isEmptyPath || toPathname === ".") && locationPathname.endsWith("/");
  if (
    !path.pathname.endsWith("/") &&
    (hasExplicitTrailingSlash || hasCurrentTrailingSlash)
  ) {
    path.pathname += "/";
  }

  return path;
}

/**
 * @private
 */
export function getToPathname(to: To): string | undefined {
  // Empty strings should be treated the same as / paths
  return to === "" || (to as Path).pathname === ""
    ? "/"
    : typeof to === "string"
    ? parsePath(to).pathname
    : to.pathname;
}

/**
 * @private
 */
export const joinPaths = (paths: string[]): string =>
  paths.join("/").replace(/\/\/+/g, "/");

/**
 * @private
 */
export const normalizePathname = (pathname: string): string =>
  pathname.replace(/\/+$/, "").replace(/^\/*/, "/");

/**
 * @private
 */
export const normalizeSearch = (search: string): string =>
  !search || search === "?"
    ? ""
    : search.startsWith("?")
    ? search
    : "?" + search;

/**
 * @private
 */
export const normalizeHash = (hash: string): string =>
  !hash || hash === "#" ? "" : hash.startsWith("#") ? hash : "#" + hash;

export type JsonFunction = <Data>(
  data: Data,
  init?: number | ResponseInit
) => Response;

/**
 * This is a shortcut for creating `application/json` responses. Converts `data`
 * to JSON and sets the `Content-Type` header.
 *
 * @deprecated The `json` method is deprecated in favor of returning raw objects.
 * This method will be removed in v7.
 */
export const json: JsonFunction = (data, init = {}) => {
  let responseInit = typeof init === "number" ? { status: init } : init;

  let headers = new Headers(responseInit.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json; charset=utf-8");
  }

  return new Response(JSON.stringify(data), {
    ...responseInit,
    headers,
  });
};

export class DataWithResponseInit<D> {
  type: string = "DataWithResponseInit";
  data: D;
  init: ResponseInit | null;

  constructor(data: D, init?: ResponseInit) {
    this.data = data;
    this.init = init || null;
  }
}

/**
 * Create "responses" that contain `status`/`headers` without forcing
 * serialization into an actual `Response` - used by Remix single fetch
 */
export function data<D>(data: D, init?: number | ResponseInit) {
  return new DataWithResponseInit(
    data,
    typeof init === "number" ? { status: init } : init
  );
}

export interface TrackedPromise extends Promise<any> {
  _tracked?: boolean;
  _data?: any;
  _error?: any;
}

export class AbortedDeferredError extends Error {}

export class DeferredData {
  private pendingKeysSet: Set<string> = new Set<string>();
  private controller: AbortController;
  private abortPromise: Promise<void>;
  private unlistenAbortSignal: () => void;
  private subscribers: Set<(aborted: boolean, settledKey?: string) => void> =
    new Set();
  data: Record<string, unknown>;
  init?: ResponseInit;
  deferredKeys: string[] = [];

  constructor(data: Record<string, unknown>, responseInit?: ResponseInit) {
    invariant(
      data && typeof data === "object" && !Array.isArray(data),
      "defer() only accepts plain objects"
    );

    // Set up an AbortController + Promise we can race against to exit early
    // cancellation
    let reject: (e: AbortedDeferredError) => void;
    this.abortPromise = new Promise((_, r) => (reject = r));
    this.controller = new AbortController();
    let onAbort = () =>
      reject(new AbortedDeferredError("Deferred data aborted"));
    this.unlistenAbortSignal = () =>
      this.controller.signal.removeEventListener("abort", onAbort);
    this.controller.signal.addEventListener("abort", onAbort);

    this.data = Object.entries(data).reduce(
      (acc, [key, value]) =>
        Object.assign(acc, {
          [key]: this.trackPromise(key, value),
        }),
      {}
    );

    if (this.done) {
      // All incoming values were resolved
      this.unlistenAbortSignal();
    }

    this.init = responseInit;
  }

  private trackPromise(
    key: string,
    value: Promise<unknown> | unknown
  ): TrackedPromise | unknown {
    if (!(value instanceof Promise)) {
      return value;
    }

    this.deferredKeys.push(key);
    this.pendingKeysSet.add(key);

    // We store a little wrapper promise that will be extended with
    // _data/_error props upon resolve/reject
    let promise: TrackedPromise = Promise.race([value, this.abortPromise]).then(
      (data) => this.onSettle(promise, key, undefined, data as unknown),
      (error) => this.onSettle(promise, key, error as unknown)
    );

    // Register rejection listeners to avoid uncaught promise rejections on
    // errors or aborted deferred values
    promise.catch(() => {});

    Object.defineProperty(promise, "_tracked", { get: () => true });
    return promise;
  }

  private onSettle(
    promise: TrackedPromise,
    key: string,
    error: unknown,
    data?: unknown
  ): unknown {
    if (
      this.controller.signal.aborted &&
      error instanceof AbortedDeferredError
    ) {
      this.unlistenAbortSignal();
      Object.defineProperty(promise, "_error", { get: () => error });
      return Promise.reject(error);
    }

    this.pendingKeysSet.delete(key);

    if (this.done) {
      // Nothing left to abort!
      this.unlistenAbortSignal();
    }

    // If the promise was resolved/rejected with undefined, we'll throw an error as you
    // should always resolve with a value or null
    if (error === undefined && data === undefined) {
      let undefinedError = new Error(
        `Deferred data for key "${key}" resolved/rejected with \`undefined\`, ` +
          `you must resolve/reject with a value or \`null\`.`
      );
      Object.defineProperty(promise, "_error", { get: () => undefinedError });
      this.emit(false, key);
      return Promise.reject(undefinedError);
    }

    if (data === undefined) {
      Object.defineProperty(promise, "_error", { get: () => error });
      this.emit(false, key);
      return Promise.reject(error);
    }

    Object.defineProperty(promise, "_data", { get: () => data });
    this.emit(false, key);
    return data;
  }

  private emit(aborted: boolean, settledKey?: string) {
    this.subscribers.forEach((subscriber) => subscriber(aborted, settledKey));
  }

  subscribe(fn: (aborted: boolean, settledKey?: string) => void) {
    this.subscribers.add(fn);
    return () => this.subscribers.delete(fn);
  }

  cancel() {
    this.controller.abort();
    this.pendingKeysSet.forEach((v, k) => this.pendingKeysSet.delete(k));
    this.emit(true);
  }

  async resolveData(signal: AbortSignal) {
    let aborted = false;
    if (!this.done) {
      let onAbort = () => this.cancel();
      signal.addEventListener("abort", onAbort);
      aborted = await new Promise((resolve) => {
        this.subscribe((aborted) => {
          signal.removeEventListener("abort", onAbort);
          if (aborted || this.done) {
            resolve(aborted);
          }
        });
      });
    }
    return aborted;
  }

  get done() {
    return this.pendingKeysSet.size === 0;
  }

  get unwrappedData() {
    invariant(
      this.data !== null && this.done,
      "Can only unwrap data on initialized and settled deferreds"
    );

    return Object.entries(this.data).reduce(
      (acc, [key, value]) =>
        Object.assign(acc, {
          [key]: unwrapTrackedPromise(value),
        }),
      {}
    );
  }

  get pendingKeys() {
    return Array.from(this.pendingKeysSet);
  }
}

function isTrackedPromise(value: any): value is TrackedPromise {
  return (
    value instanceof Promise && (value as TrackedPromise)._tracked === true
  );
}

function unwrapTrackedPromise(value: any) {
  if (!isTrackedPromise(value)) {
    return value;
  }

  if (value._error) {
    throw value._error;
  }
  return value._data;
}

export type DeferFunction = (
  data: Record<string, unknown>,
  init?: number | ResponseInit
) => DeferredData;

/**
 * @deprecated The `defer` method is deprecated in favor of returning raw
 * objects. This method will be removed in v7.
 */
export const defer: DeferFunction = (data, init = {}) => {
  let responseInit = typeof init === "number" ? { status: init } : init;

  return new DeferredData(data, responseInit);
};

export type RedirectFunction = (
  url: string,
  init?: number | ResponseInit
) => Response;

/**
 * A redirect response. Sets the status code and the `Location` header.
 * Defaults to "302 Found".
 */
export const redirect: RedirectFunction = (url, init = 302) => {
  let responseInit = init;
  if (typeof responseInit === "number") {
    responseInit = { status: responseInit };
  } else if (typeof responseInit.status === "undefined") {
    responseInit.status = 302;
  }

  let headers = new Headers(responseInit.headers);
  headers.set("Location", url);

  return new Response(null, {
    ...responseInit,
    headers,
  });
};

/**
 * A redirect response that will force a document reload to the new location.
 * Sets the status code and the `Location` header.
 * Defaults to "302 Found".
 */
export const redirectDocument: RedirectFunction = (url, init) => {
  let response = redirect(url, init);
  response.headers.set("X-Remix-Reload-Document", "true");
  return response;
};

/**
 * A redirect response that will perform a `history.replaceState` instead of a
 * `history.pushState` for client-side navigation redirects.
 * Sets the status code and the `Location` header.
 * Defaults to "302 Found".
 */
export const replace: RedirectFunction = (url, init) => {
  let response = redirect(url, init);
  response.headers.set("X-Remix-Replace", "true");
  return response;
};

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
export class ErrorResponseImpl implements ErrorResponse {
  status: number;
  statusText: string;
  data: any;
  private error?: Error;
  private internal: boolean;

  constructor(
    status: number,
    statusText: string | undefined,
    data: any,
    internal = false
  ) {
    this.status = status;
    this.statusText = statusText || "";
    this.internal = internal;
    if (data instanceof Error) {
      this.data = data.toString();
      this.error = data;
    } else {
      this.data = data;
    }
  }
}

/**
 * Check if the given error is an ErrorResponse generated from a 4xx/5xx
 * Response thrown from an action/loader
 */
export function isRouteErrorResponse(error: any): error is ErrorResponse {
  return (
    error != null &&
    typeof error.status === "number" &&
    typeof error.statusText === "string" &&
    typeof error.internal === "boolean" &&
    "data" in error
  );
}
