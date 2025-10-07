'use strict';

Object.defineProperty(exports, '__esModule', { value: true });

var React = require('react');
var router = require('@remix-run/router');
var reactRouter = require('react-router');
var reactRouterDom = require('react-router-dom');

function _interopNamespace(e) {
    if (e && e.__esModule) return e;
    var n = Object.create(null);
    if (e) {
        Object.keys(e).forEach(function (k) {
            if (k !== 'default') {
                var d = Object.getOwnPropertyDescriptor(e, k);
                Object.defineProperty(n, k, d.get ? d : {
                    enumerable: true,
                    get: function () { return e[k]; }
                });
            }
        });
    }
    n["default"] = e;
    return Object.freeze(n);
}

var React__namespace = /*#__PURE__*/_interopNamespace(React);

/**
 * A `<Router>` that may not navigate to any other location. This is useful
 * on the server where there is no stateful UI.
 */
function StaticRouter({
  basename,
  children,
  location: locationProp = "/",
  future
}) {
  if (typeof locationProp === "string") {
    locationProp = reactRouterDom.parsePath(locationProp);
  }
  let action = router.Action.Pop;
  let location = {
    pathname: locationProp.pathname || "/",
    search: locationProp.search || "",
    hash: locationProp.hash || "",
    state: locationProp.state != null ? locationProp.state : null,
    key: locationProp.key || "default"
  };
  let staticNavigator = getStatelessNavigator();
  return /*#__PURE__*/React__namespace.createElement(reactRouterDom.Router, {
    basename: basename,
    children: children,
    location: location,
    navigationType: action,
    navigator: staticNavigator,
    future: future,
    static: true
  });
}
/**
 * A Data Router that may not navigate to any other location. This is useful
 * on the server where there is no stateful UI.
 */
function StaticRouterProvider({
  context,
  router: router$1,
  hydrate = true,
  nonce
}) {
  !(router$1 && context) ? process.env.NODE_ENV !== "production" ? router.UNSAFE_invariant(false, "You must provide `router` and `context` to <StaticRouterProvider>") : router.UNSAFE_invariant(false) : void 0;
  let dataRouterContext = {
    router: router$1,
    navigator: getStatelessNavigator(),
    static: true,
    staticContext: context,
    basename: context.basename || "/"
  };
  let fetchersContext = new Map();
  let hydrateScript = "";
  if (hydrate !== false) {
    let data = {
      loaderData: context.loaderData,
      actionData: context.actionData,
      errors: serializeErrors(context.errors)
    };
    // Use JSON.parse here instead of embedding a raw JS object here to speed
    // up parsing on the client.  Dual-stringify is needed to ensure all quotes
    // are properly escaped in the resulting string.  See:
    //   https://v8.dev/blog/cost-of-javascript-2019#json
    let json = htmlEscape(JSON.stringify(JSON.stringify(data)));
    hydrateScript = `window.__staticRouterHydrationData = JSON.parse(${json});`;
  }
  let {
    state
  } = dataRouterContext.router;
  return /*#__PURE__*/React__namespace.createElement(React__namespace.Fragment, null, /*#__PURE__*/React__namespace.createElement(reactRouterDom.UNSAFE_DataRouterContext.Provider, {
    value: dataRouterContext
  }, /*#__PURE__*/React__namespace.createElement(reactRouterDom.UNSAFE_DataRouterStateContext.Provider, {
    value: state
  }, /*#__PURE__*/React__namespace.createElement(reactRouterDom.UNSAFE_FetchersContext.Provider, {
    value: fetchersContext
  }, /*#__PURE__*/React__namespace.createElement(reactRouterDom.UNSAFE_ViewTransitionContext.Provider, {
    value: {
      isTransitioning: false
    }
  }, /*#__PURE__*/React__namespace.createElement(reactRouterDom.Router, {
    basename: dataRouterContext.basename,
    location: state.location,
    navigationType: state.historyAction,
    navigator: dataRouterContext.navigator,
    static: dataRouterContext.static,
    future: {
      v7_relativeSplatPath: router$1.future.v7_relativeSplatPath
    }
  }, /*#__PURE__*/React__namespace.createElement(DataRoutes, {
    routes: router$1.routes,
    future: router$1.future,
    state: state
  })))))), hydrateScript ? /*#__PURE__*/React__namespace.createElement("script", {
    suppressHydrationWarning: true,
    nonce: nonce,
    dangerouslySetInnerHTML: {
      __html: hydrateScript
    }
  }) : null);
}
function DataRoutes({
  routes,
  future,
  state
}) {
  return reactRouter.UNSAFE_useRoutesImpl(routes, undefined, state, future);
}
function serializeErrors(errors) {
  if (!errors) return null;
  let entries = Object.entries(errors);
  let serialized = {};
  for (let [key, val] of entries) {
    // Hey you!  If you change this, please change the corresponding logic in
    // deserializeErrors in react-router-dom/index.tsx :)
    if (router.isRouteErrorResponse(val)) {
      serialized[key] = {
        ...val,
        __type: "RouteErrorResponse"
      };
    } else if (val instanceof Error) {
      // Do not serialize stack traces from SSR for security reasons
      serialized[key] = {
        message: val.message,
        __type: "Error",
        // If this is a subclass (i.e., ReferenceError), send up the type so we
        // can re-create the same type during hydration.
        ...(val.name !== "Error" ? {
          __subType: val.name
        } : {})
      };
    } else {
      serialized[key] = val;
    }
  }
  return serialized;
}
function getStatelessNavigator() {
  return {
    createHref,
    encodeLocation,
    push(to) {
      throw new Error(`You cannot use navigator.push() on the server because it is a stateless ` + `environment. This error was probably triggered when you did a ` + `\`navigate(${JSON.stringify(to)})\` somewhere in your app.`);
    },
    replace(to) {
      throw new Error(`You cannot use navigator.replace() on the server because it is a stateless ` + `environment. This error was probably triggered when you did a ` + `\`navigate(${JSON.stringify(to)}, { replace: true })\` somewhere ` + `in your app.`);
    },
    go(delta) {
      throw new Error(`You cannot use navigator.go() on the server because it is a stateless ` + `environment. This error was probably triggered when you did a ` + `\`navigate(${delta})\` somewhere in your app.`);
    },
    back() {
      throw new Error(`You cannot use navigator.back() on the server because it is a stateless ` + `environment.`);
    },
    forward() {
      throw new Error(`You cannot use navigator.forward() on the server because it is a stateless ` + `environment.`);
    }
  };
}
function createStaticHandler(routes, opts) {
  return router.createStaticHandler(routes, {
    ...opts,
    mapRouteProperties: reactRouter.UNSAFE_mapRouteProperties
  });
}
function createStaticRouter(routes, context, opts = {}) {
  let manifest = {};
  let dataRoutes = router.UNSAFE_convertRoutesToDataRoutes(routes, reactRouter.UNSAFE_mapRouteProperties, undefined, manifest);
  // Because our context matches may be from a framework-agnostic set of
  // routes passed to createStaticHandler(), we update them here with our
  // newly created/enhanced data routes
  let matches = context.matches.map(match => {
    let route = manifest[match.route.id] || match.route;
    return {
      ...match,
      route
    };
  });
  let msg = method => `You cannot use router.${method}() on the server because it is a stateless environment`;
  return {
    get basename() {
      return context.basename;
    },
    get future() {
      return {
        v7_fetcherPersist: false,
        v7_normalizeFormMethod: false,
        v7_partialHydration: opts.future?.v7_partialHydration === true,
        v7_prependBasename: false,
        v7_relativeSplatPath: opts.future?.v7_relativeSplatPath === true,
        v7_skipActionErrorRevalidation: false
      };
    },
    get state() {
      return {
        historyAction: router.Action.Pop,
        location: context.location,
        matches,
        loaderData: context.loaderData,
        actionData: context.actionData,
        errors: context.errors,
        initialized: true,
        navigation: router.IDLE_NAVIGATION,
        restoreScrollPosition: null,
        preventScrollReset: false,
        revalidation: "idle",
        fetchers: new Map(),
        blockers: new Map()
      };
    },
    get routes() {
      return dataRoutes;
    },
    get window() {
      return undefined;
    },
    initialize() {
      throw msg("initialize");
    },
    subscribe() {
      throw msg("subscribe");
    },
    enableScrollRestoration() {
      throw msg("enableScrollRestoration");
    },
    navigate() {
      throw msg("navigate");
    },
    fetch() {
      throw msg("fetch");
    },
    revalidate() {
      throw msg("revalidate");
    },
    createHref,
    encodeLocation,
    getFetcher() {
      return router.IDLE_FETCHER;
    },
    deleteFetcher() {
      throw msg("deleteFetcher");
    },
    dispose() {
      throw msg("dispose");
    },
    getBlocker() {
      return router.IDLE_BLOCKER;
    },
    deleteBlocker() {
      throw msg("deleteBlocker");
    },
    patchRoutes() {
      throw msg("patchRoutes");
    },
    _internalFetchControllers: new Map(),
    _internalActiveDeferreds: new Map(),
    _internalSetRoutes() {
      throw msg("_internalSetRoutes");
    }
  };
}
function createHref(to) {
  return typeof to === "string" ? to : reactRouterDom.createPath(to);
}
function encodeLocation(to) {
  let href = typeof to === "string" ? to : reactRouterDom.createPath(to);
  // Treating this as a full URL will strip any trailing spaces so we need to
  // pre-encode them since they might be part of a matching splat param from
  // an ancestor route
  href = href.replace(/ $/, "%20");
  let encoded = ABSOLUTE_URL_REGEX.test(href) ? new URL(href) : new URL(href, "http://localhost");
  return {
    pathname: encoded.pathname,
    search: encoded.search,
    hash: encoded.hash
  };
}
const ABSOLUTE_URL_REGEX = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i;
// This utility is based on https://github.com/zertosh/htmlescape
// License: https://github.com/zertosh/htmlescape/blob/0527ca7156a524d256101bb310a9f970f63078ad/LICENSE
const ESCAPE_LOOKUP = {
  "&": "\\u0026",
  ">": "\\u003e",
  "<": "\\u003c",
  "\u2028": "\\u2028",
  "\u2029": "\\u2029"
};
const ESCAPE_REGEX = /[&><\u2028\u2029]/g;
function htmlEscape(str) {
  return str.replace(ESCAPE_REGEX, match => ESCAPE_LOOKUP[match]);
}

exports.StaticRouter = StaticRouter;
exports.StaticRouterProvider = StaticRouterProvider;
exports.createStaticHandler = createStaticHandler;
exports.createStaticRouter = createStaticRouter;
