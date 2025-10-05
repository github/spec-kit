/**
 * React Router DOM v6.30.1
 *
 * Copyright (c) Remix Software Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE.md file in the root directory of this source tree.
 *
 * @license MIT
 */
(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports, require('react'), require('react-dom'), require('react-router'), require('@remix-run/router')) :
  typeof define === 'function' && define.amd ? define(['exports', 'react', 'react-dom', 'react-router', '@remix-run/router'], factory) :
  (global = typeof globalThis !== 'undefined' ? globalThis : global || self, factory(global.ReactRouterDOM = {}, global.React, global.ReactDOM, global.ReactRouter, global.RemixRouter));
})(this, (function (exports, React, ReactDOM, reactRouter, router) { 'use strict';

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
  var ReactDOM__namespace = /*#__PURE__*/_interopNamespace(ReactDOM);

  function _extends() {
    _extends = Object.assign ? Object.assign.bind() : function (target) {
      for (var i = 1; i < arguments.length; i++) {
        var source = arguments[i];
        for (var key in source) {
          if (Object.prototype.hasOwnProperty.call(source, key)) {
            target[key] = source[key];
          }
        }
      }
      return target;
    };
    return _extends.apply(this, arguments);
  }
  function _objectWithoutPropertiesLoose(source, excluded) {
    if (source == null) return {};
    var target = {};
    var sourceKeys = Object.keys(source);
    var key, i;
    for (i = 0; i < sourceKeys.length; i++) {
      key = sourceKeys[i];
      if (excluded.indexOf(key) >= 0) continue;
      target[key] = source[key];
    }
    return target;
  }

  const defaultMethod = "get";
  const defaultEncType = "application/x-www-form-urlencoded";
  function isHtmlElement(object) {
    return object != null && typeof object.tagName === "string";
  }
  function isButtonElement(object) {
    return isHtmlElement(object) && object.tagName.toLowerCase() === "button";
  }
  function isFormElement(object) {
    return isHtmlElement(object) && object.tagName.toLowerCase() === "form";
  }
  function isInputElement(object) {
    return isHtmlElement(object) && object.tagName.toLowerCase() === "input";
  }
  function isModifiedEvent(event) {
    return !!(event.metaKey || event.altKey || event.ctrlKey || event.shiftKey);
  }
  function shouldProcessLinkClick(event, target) {
    return event.button === 0 && (
    // Ignore everything but left clicks
    !target || target === "_self") &&
    // Let browser handle "target=_blank" etc.
    !isModifiedEvent(event) // Ignore clicks with modifier keys
    ;
  }

  /**
   * Creates a URLSearchParams object using the given initializer.
   *
   * This is identical to `new URLSearchParams(init)` except it also
   * supports arrays as values in the object form of the initializer
   * instead of just strings. This is convenient when you need multiple
   * values for a given key, but don't want to use an array initializer.
   *
   * For example, instead of:
   *
   *   let searchParams = new URLSearchParams([
   *     ['sort', 'name'],
   *     ['sort', 'price']
   *   ]);
   *
   * you can do:
   *
   *   let searchParams = createSearchParams({
   *     sort: ['name', 'price']
   *   });
   */
  function createSearchParams(init) {
    if (init === void 0) {
      init = "";
    }
    return new URLSearchParams(typeof init === "string" || Array.isArray(init) || init instanceof URLSearchParams ? init : Object.keys(init).reduce((memo, key) => {
      let value = init[key];
      return memo.concat(Array.isArray(value) ? value.map(v => [key, v]) : [[key, value]]);
    }, []));
  }
  function getSearchParamsForLocation(locationSearch, defaultSearchParams) {
    let searchParams = createSearchParams(locationSearch);
    if (defaultSearchParams) {
      // Use `defaultSearchParams.forEach(...)` here instead of iterating of
      // `defaultSearchParams.keys()` to work-around a bug in Firefox related to
      // web extensions. Relevant Bugzilla tickets:
      // https://bugzilla.mozilla.org/show_bug.cgi?id=1414602
      // https://bugzilla.mozilla.org/show_bug.cgi?id=1023984
      defaultSearchParams.forEach((_, key) => {
        if (!searchParams.has(key)) {
          defaultSearchParams.getAll(key).forEach(value => {
            searchParams.append(key, value);
          });
        }
      });
    }
    return searchParams;
  }

  // Thanks https://github.com/sindresorhus/type-fest!

  // One-time check for submitter support
  let _formDataSupportsSubmitter = null;
  function isFormDataSubmitterSupported() {
    if (_formDataSupportsSubmitter === null) {
      try {
        new FormData(document.createElement("form"),
        // @ts-expect-error if FormData supports the submitter parameter, this will throw
        0);
        _formDataSupportsSubmitter = false;
      } catch (e) {
        _formDataSupportsSubmitter = true;
      }
    }
    return _formDataSupportsSubmitter;
  }

  /**
   * Submit options shared by both navigations and fetchers
   */

  /**
   * Submit options available to fetchers
   */

  /**
   * Submit options available to navigations
   */

  const supportedFormEncTypes = new Set(["application/x-www-form-urlencoded", "multipart/form-data", "text/plain"]);
  function getFormEncType(encType) {
    if (encType != null && !supportedFormEncTypes.has(encType)) {
      router.UNSAFE_warning(false, "\"" + encType + "\" is not a valid `encType` for `<Form>`/`<fetcher.Form>` " + ("and will default to \"" + defaultEncType + "\"")) ;
      return null;
    }
    return encType;
  }
  function getFormSubmissionInfo(target, basename) {
    let method;
    let action;
    let encType;
    let formData;
    let body;
    if (isFormElement(target)) {
      // When grabbing the action from the element, it will have had the basename
      // prefixed to ensure non-JS scenarios work, so strip it since we'll
      // re-prefix in the router
      let attr = target.getAttribute("action");
      action = attr ? router.stripBasename(attr, basename) : null;
      method = target.getAttribute("method") || defaultMethod;
      encType = getFormEncType(target.getAttribute("enctype")) || defaultEncType;
      formData = new FormData(target);
    } else if (isButtonElement(target) || isInputElement(target) && (target.type === "submit" || target.type === "image")) {
      let form = target.form;
      if (form == null) {
        throw new Error("Cannot submit a <button> or <input type=\"submit\"> without a <form>");
      }

      // <button>/<input type="submit"> may override attributes of <form>

      // When grabbing the action from the element, it will have had the basename
      // prefixed to ensure non-JS scenarios work, so strip it since we'll
      // re-prefix in the router
      let attr = target.getAttribute("formaction") || form.getAttribute("action");
      action = attr ? router.stripBasename(attr, basename) : null;
      method = target.getAttribute("formmethod") || form.getAttribute("method") || defaultMethod;
      encType = getFormEncType(target.getAttribute("formenctype")) || getFormEncType(form.getAttribute("enctype")) || defaultEncType;

      // Build a FormData object populated from a form and submitter
      formData = new FormData(form, target);

      // If this browser doesn't support the `FormData(el, submitter)` format,
      // then tack on the submitter value at the end.  This is a lightweight
      // solution that is not 100% spec compliant.  For complete support in older
      // browsers, consider using the `formdata-submitter-polyfill` package
      if (!isFormDataSubmitterSupported()) {
        let {
          name,
          type,
          value
        } = target;
        if (type === "image") {
          let prefix = name ? name + "." : "";
          formData.append(prefix + "x", "0");
          formData.append(prefix + "y", "0");
        } else if (name) {
          formData.append(name, value);
        }
      }
    } else if (isHtmlElement(target)) {
      throw new Error("Cannot submit element that is not <form>, <button>, or " + "<input type=\"submit|image\">");
    } else {
      method = defaultMethod;
      action = null;
      encType = defaultEncType;
      body = target;
    }

    // Send body for <Form encType="text/plain" so we encode it into text
    if (formData && encType === "text/plain") {
      body = formData;
      formData = undefined;
    }
    return {
      action,
      method: method.toLowerCase(),
      encType,
      formData,
      body
    };
  }

  const _excluded = ["onClick", "relative", "reloadDocument", "replace", "state", "target", "to", "preventScrollReset", "viewTransition"],
    _excluded2 = ["aria-current", "caseSensitive", "className", "end", "style", "to", "viewTransition", "children"],
    _excluded3 = ["fetcherKey", "navigate", "reloadDocument", "replace", "state", "method", "action", "onSubmit", "relative", "preventScrollReset", "viewTransition"];
  //#endregion
  // HEY YOU! DON'T TOUCH THIS VARIABLE!
  //
  // It is replaced with the proper version at build time via a babel plugin in
  // the rollup config.
  //
  // Export a global property onto the window for React Router detection by the
  // Core Web Vitals Technology Report.  This way they can configure the `wappalyzer`
  // to detect and properly classify live websites as being built with React Router:
  // https://github.com/HTTPArchive/wappalyzer/blob/main/src/technologies/r.json
  const REACT_ROUTER_VERSION = "6";
  try {
    window.__reactRouterVersion = REACT_ROUTER_VERSION;
  } catch (e) {
    // no-op
  }

  ////////////////////////////////////////////////////////////////////////////////
  //#region Routers
  ////////////////////////////////////////////////////////////////////////////////
  function createBrowserRouter(routes, opts) {
    return router.createRouter({
      basename: opts == null ? void 0 : opts.basename,
      future: _extends({}, opts == null ? void 0 : opts.future, {
        v7_prependBasename: true
      }),
      history: router.createBrowserHistory({
        window: opts == null ? void 0 : opts.window
      }),
      hydrationData: (opts == null ? void 0 : opts.hydrationData) || parseHydrationData(),
      routes,
      mapRouteProperties: reactRouter.UNSAFE_mapRouteProperties,
      dataStrategy: opts == null ? void 0 : opts.dataStrategy,
      patchRoutesOnNavigation: opts == null ? void 0 : opts.patchRoutesOnNavigation,
      window: opts == null ? void 0 : opts.window
    }).initialize();
  }
  function createHashRouter(routes, opts) {
    return router.createRouter({
      basename: opts == null ? void 0 : opts.basename,
      future: _extends({}, opts == null ? void 0 : opts.future, {
        v7_prependBasename: true
      }),
      history: router.createHashHistory({
        window: opts == null ? void 0 : opts.window
      }),
      hydrationData: (opts == null ? void 0 : opts.hydrationData) || parseHydrationData(),
      routes,
      mapRouteProperties: reactRouter.UNSAFE_mapRouteProperties,
      dataStrategy: opts == null ? void 0 : opts.dataStrategy,
      patchRoutesOnNavigation: opts == null ? void 0 : opts.patchRoutesOnNavigation,
      window: opts == null ? void 0 : opts.window
    }).initialize();
  }
  function parseHydrationData() {
    var _window;
    let state = (_window = window) == null ? void 0 : _window.__staticRouterHydrationData;
    if (state && state.errors) {
      state = _extends({}, state, {
        errors: deserializeErrors(state.errors)
      });
    }
    return state;
  }
  function deserializeErrors(errors) {
    if (!errors) return null;
    let entries = Object.entries(errors);
    let serialized = {};
    for (let [key, val] of entries) {
      // Hey you!  If you change this, please change the corresponding logic in
      // serializeErrors in react-router-dom/server.tsx :)
      if (val && val.__type === "RouteErrorResponse") {
        serialized[key] = new router.UNSAFE_ErrorResponseImpl(val.status, val.statusText, val.data, val.internal === true);
      } else if (val && val.__type === "Error") {
        // Attempt to reconstruct the right type of Error (i.e., ReferenceError)
        if (val.__subType) {
          let ErrorConstructor = window[val.__subType];
          if (typeof ErrorConstructor === "function") {
            try {
              // @ts-expect-error
              let error = new ErrorConstructor(val.message);
              // Wipe away the client-side stack trace.  Nothing to fill it in with
              // because we don't serialize SSR stack traces for security reasons
              error.stack = "";
              serialized[key] = error;
            } catch (e) {
              // no-op - fall through and create a normal Error
            }
          }
        }
        if (serialized[key] == null) {
          let error = new Error(val.message);
          // Wipe away the client-side stack trace.  Nothing to fill it in with
          // because we don't serialize SSR stack traces for security reasons
          error.stack = "";
          serialized[key] = error;
        }
      } else {
        serialized[key] = val;
      }
    }
    return serialized;
  }

  //#endregion

  ////////////////////////////////////////////////////////////////////////////////
  //#region Contexts
  ////////////////////////////////////////////////////////////////////////////////
  const ViewTransitionContext = /*#__PURE__*/React__namespace.createContext({
    isTransitioning: false
  });
  {
    ViewTransitionContext.displayName = "ViewTransition";
  }

  // TODO: (v7) Change the useFetcher data from `any` to `unknown`

  const FetchersContext = /*#__PURE__*/React__namespace.createContext(new Map());
  {
    FetchersContext.displayName = "Fetchers";
  }

  //#endregion

  ////////////////////////////////////////////////////////////////////////////////
  //#region Components
  ////////////////////////////////////////////////////////////////////////////////

  /**
    Webpack + React 17 fails to compile on any of the following because webpack
    complains that `startTransition` doesn't exist in `React`:
    * import { startTransition } from "react"
    * import * as React from from "react";
      "startTransition" in React ? React.startTransition(() => setState()) : setState()
    * import * as React from from "react";
      "startTransition" in React ? React["startTransition"](() => setState()) : setState()

    Moving it to a constant such as the following solves the Webpack/React 17 issue:
    * import * as React from from "react";
      const START_TRANSITION = "startTransition";
      START_TRANSITION in React ? React[START_TRANSITION](() => setState()) : setState()

    However, that introduces webpack/terser minification issues in production builds
    in React 18 where minification/obfuscation ends up removing the call of
    React.startTransition entirely from the first half of the ternary.  Grabbing
    this exported reference once up front resolves that issue.

    See https://github.com/remix-run/react-router/issues/10579
  */
  const START_TRANSITION = "startTransition";
  const startTransitionImpl = React__namespace[START_TRANSITION];
  const FLUSH_SYNC = "flushSync";
  const flushSyncImpl = ReactDOM__namespace[FLUSH_SYNC];
  const USE_ID = "useId";
  const useIdImpl = React__namespace[USE_ID];
  function startTransitionSafe(cb) {
    if (startTransitionImpl) {
      startTransitionImpl(cb);
    } else {
      cb();
    }
  }
  function flushSyncSafe(cb) {
    if (flushSyncImpl) {
      flushSyncImpl(cb);
    } else {
      cb();
    }
  }
  class Deferred {
    // @ts-expect-error - no initializer

    // @ts-expect-error - no initializer

    constructor() {
      this.status = "pending";
      this.promise = new Promise((resolve, reject) => {
        this.resolve = value => {
          if (this.status === "pending") {
            this.status = "resolved";
            resolve(value);
          }
        };
        this.reject = reason => {
          if (this.status === "pending") {
            this.status = "rejected";
            reject(reason);
          }
        };
      });
    }
  }

  /**
   * Given a Remix Router instance, render the appropriate UI
   */
  function RouterProvider(_ref) {
    let {
      fallbackElement,
      router: router$1,
      future
    } = _ref;
    let [state, setStateImpl] = React__namespace.useState(router$1.state);
    let [pendingState, setPendingState] = React__namespace.useState();
    let [vtContext, setVtContext] = React__namespace.useState({
      isTransitioning: false
    });
    let [renderDfd, setRenderDfd] = React__namespace.useState();
    let [transition, setTransition] = React__namespace.useState();
    let [interruption, setInterruption] = React__namespace.useState();
    let fetcherData = React__namespace.useRef(new Map());
    let {
      v7_startTransition
    } = future || {};
    let optInStartTransition = React__namespace.useCallback(cb => {
      if (v7_startTransition) {
        startTransitionSafe(cb);
      } else {
        cb();
      }
    }, [v7_startTransition]);
    let setState = React__namespace.useCallback((newState, _ref2) => {
      let {
        deletedFetchers,
        flushSync: flushSync,
        viewTransitionOpts: viewTransitionOpts
      } = _ref2;
      newState.fetchers.forEach((fetcher, key) => {
        if (fetcher.data !== undefined) {
          fetcherData.current.set(key, fetcher.data);
        }
      });
      deletedFetchers.forEach(key => fetcherData.current.delete(key));
      let isViewTransitionUnavailable = router$1.window == null || router$1.window.document == null || typeof router$1.window.document.startViewTransition !== "function";

      // If this isn't a view transition or it's not available in this browser,
      // just update and be done with it
      if (!viewTransitionOpts || isViewTransitionUnavailable) {
        if (flushSync) {
          flushSyncSafe(() => setStateImpl(newState));
        } else {
          optInStartTransition(() => setStateImpl(newState));
        }
        return;
      }

      // flushSync + startViewTransition
      if (flushSync) {
        // Flush through the context to mark DOM elements as transition=ing
        flushSyncSafe(() => {
          // Cancel any pending transitions
          if (transition) {
            renderDfd && renderDfd.resolve();
            transition.skipTransition();
          }
          setVtContext({
            isTransitioning: true,
            flushSync: true,
            currentLocation: viewTransitionOpts.currentLocation,
            nextLocation: viewTransitionOpts.nextLocation
          });
        });

        // Update the DOM
        let t = router$1.window.document.startViewTransition(() => {
          flushSyncSafe(() => setStateImpl(newState));
        });

        // Clean up after the animation completes
        t.finished.finally(() => {
          flushSyncSafe(() => {
            setRenderDfd(undefined);
            setTransition(undefined);
            setPendingState(undefined);
            setVtContext({
              isTransitioning: false
            });
          });
        });
        flushSyncSafe(() => setTransition(t));
        return;
      }

      // startTransition + startViewTransition
      if (transition) {
        // Interrupting an in-progress transition, cancel and let everything flush
        // out, and then kick off a new transition from the interruption state
        renderDfd && renderDfd.resolve();
        transition.skipTransition();
        setInterruption({
          state: newState,
          currentLocation: viewTransitionOpts.currentLocation,
          nextLocation: viewTransitionOpts.nextLocation
        });
      } else {
        // Completed navigation update with opted-in view transitions, let 'er rip
        setPendingState(newState);
        setVtContext({
          isTransitioning: true,
          flushSync: false,
          currentLocation: viewTransitionOpts.currentLocation,
          nextLocation: viewTransitionOpts.nextLocation
        });
      }
    }, [router$1.window, transition, renderDfd, fetcherData, optInStartTransition]);

    // Need to use a layout effect here so we are subscribed early enough to
    // pick up on any render-driven redirects/navigations (useEffect/<Navigate>)
    React__namespace.useLayoutEffect(() => router$1.subscribe(setState), [router$1, setState]);

    // When we start a view transition, create a Deferred we can use for the
    // eventual "completed" render
    React__namespace.useEffect(() => {
      if (vtContext.isTransitioning && !vtContext.flushSync) {
        setRenderDfd(new Deferred());
      }
    }, [vtContext]);

    // Once the deferred is created, kick off startViewTransition() to update the
    // DOM and then wait on the Deferred to resolve (indicating the DOM update has
    // happened)
    React__namespace.useEffect(() => {
      if (renderDfd && pendingState && router$1.window) {
        let newState = pendingState;
        let renderPromise = renderDfd.promise;
        let transition = router$1.window.document.startViewTransition(async () => {
          optInStartTransition(() => setStateImpl(newState));
          await renderPromise;
        });
        transition.finished.finally(() => {
          setRenderDfd(undefined);
          setTransition(undefined);
          setPendingState(undefined);
          setVtContext({
            isTransitioning: false
          });
        });
        setTransition(transition);
      }
    }, [optInStartTransition, pendingState, renderDfd, router$1.window]);

    // When the new location finally renders and is committed to the DOM, this
    // effect will run to resolve the transition
    React__namespace.useEffect(() => {
      if (renderDfd && pendingState && state.location.key === pendingState.location.key) {
        renderDfd.resolve();
      }
    }, [renderDfd, transition, state.location, pendingState]);

    // If we get interrupted with a new navigation during a transition, we skip
    // the active transition, let it cleanup, then kick it off again here
    React__namespace.useEffect(() => {
      if (!vtContext.isTransitioning && interruption) {
        setPendingState(interruption.state);
        setVtContext({
          isTransitioning: true,
          flushSync: false,
          currentLocation: interruption.currentLocation,
          nextLocation: interruption.nextLocation
        });
        setInterruption(undefined);
      }
    }, [vtContext.isTransitioning, interruption]);
    React__namespace.useEffect(() => {
      router.UNSAFE_warning(fallbackElement == null || !router$1.future.v7_partialHydration, "`<RouterProvider fallbackElement>` is deprecated when using " + "`v7_partialHydration`, use a `HydrateFallback` component instead") ;
      // Only log this once on initial mount
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    let navigator = React__namespace.useMemo(() => {
      return {
        createHref: router$1.createHref,
        encodeLocation: router$1.encodeLocation,
        go: n => router$1.navigate(n),
        push: (to, state, opts) => router$1.navigate(to, {
          state,
          preventScrollReset: opts == null ? void 0 : opts.preventScrollReset
        }),
        replace: (to, state, opts) => router$1.navigate(to, {
          replace: true,
          state,
          preventScrollReset: opts == null ? void 0 : opts.preventScrollReset
        })
      };
    }, [router$1]);
    let basename = router$1.basename || "/";
    let dataRouterContext = React__namespace.useMemo(() => ({
      router: router$1,
      navigator,
      static: false,
      basename
    }), [router$1, navigator, basename]);
    let routerFuture = React__namespace.useMemo(() => ({
      v7_relativeSplatPath: router$1.future.v7_relativeSplatPath
    }), [router$1.future.v7_relativeSplatPath]);
    React__namespace.useEffect(() => reactRouter.UNSAFE_logV6DeprecationWarnings(future, router$1.future), [future, router$1.future]);

    // The fragment and {null} here are important!  We need them to keep React 18's
    // useId happy when we are server-rendering since we may have a <script> here
    // containing the hydrated server-side staticContext (from StaticRouterProvider).
    // useId relies on the component tree structure to generate deterministic id's
    // so we need to ensure it remains the same on the client even though
    // we don't need the <script> tag
    return /*#__PURE__*/React__namespace.createElement(React__namespace.Fragment, null, /*#__PURE__*/React__namespace.createElement(reactRouter.UNSAFE_DataRouterContext.Provider, {
      value: dataRouterContext
    }, /*#__PURE__*/React__namespace.createElement(reactRouter.UNSAFE_DataRouterStateContext.Provider, {
      value: state
    }, /*#__PURE__*/React__namespace.createElement(FetchersContext.Provider, {
      value: fetcherData.current
    }, /*#__PURE__*/React__namespace.createElement(ViewTransitionContext.Provider, {
      value: vtContext
    }, /*#__PURE__*/React__namespace.createElement(reactRouter.Router, {
      basename: basename,
      location: state.location,
      navigationType: state.historyAction,
      navigator: navigator,
      future: routerFuture
    }, state.initialized || router$1.future.v7_partialHydration ? /*#__PURE__*/React__namespace.createElement(MemoizedDataRoutes, {
      routes: router$1.routes,
      future: router$1.future,
      state: state
    }) : fallbackElement))))), null);
  }

  // Memoize to avoid re-renders when updating `ViewTransitionContext`
  const MemoizedDataRoutes = /*#__PURE__*/React__namespace.memo(DataRoutes);
  function DataRoutes(_ref3) {
    let {
      routes,
      future,
      state
    } = _ref3;
    return reactRouter.UNSAFE_useRoutesImpl(routes, undefined, state, future);
  }
  /**
   * A `<Router>` for use in web browsers. Provides the cleanest URLs.
   */
  function BrowserRouter(_ref4) {
    let {
      basename,
      children,
      future,
      window
    } = _ref4;
    let historyRef = React__namespace.useRef();
    if (historyRef.current == null) {
      historyRef.current = router.createBrowserHistory({
        window,
        v5Compat: true
      });
    }
    let history = historyRef.current;
    let [state, setStateImpl] = React__namespace.useState({
      action: history.action,
      location: history.location
    });
    let {
      v7_startTransition
    } = future || {};
    let setState = React__namespace.useCallback(newState => {
      v7_startTransition && startTransitionImpl ? startTransitionImpl(() => setStateImpl(newState)) : setStateImpl(newState);
    }, [setStateImpl, v7_startTransition]);
    React__namespace.useLayoutEffect(() => history.listen(setState), [history, setState]);
    React__namespace.useEffect(() => reactRouter.UNSAFE_logV6DeprecationWarnings(future), [future]);
    return /*#__PURE__*/React__namespace.createElement(reactRouter.Router, {
      basename: basename,
      children: children,
      location: state.location,
      navigationType: state.action,
      navigator: history,
      future: future
    });
  }
  /**
   * A `<Router>` for use in web browsers. Stores the location in the hash
   * portion of the URL so it is not sent to the server.
   */
  function HashRouter(_ref5) {
    let {
      basename,
      children,
      future,
      window
    } = _ref5;
    let historyRef = React__namespace.useRef();
    if (historyRef.current == null) {
      historyRef.current = router.createHashHistory({
        window,
        v5Compat: true
      });
    }
    let history = historyRef.current;
    let [state, setStateImpl] = React__namespace.useState({
      action: history.action,
      location: history.location
    });
    let {
      v7_startTransition
    } = future || {};
    let setState = React__namespace.useCallback(newState => {
      v7_startTransition && startTransitionImpl ? startTransitionImpl(() => setStateImpl(newState)) : setStateImpl(newState);
    }, [setStateImpl, v7_startTransition]);
    React__namespace.useLayoutEffect(() => history.listen(setState), [history, setState]);
    React__namespace.useEffect(() => reactRouter.UNSAFE_logV6DeprecationWarnings(future), [future]);
    return /*#__PURE__*/React__namespace.createElement(reactRouter.Router, {
      basename: basename,
      children: children,
      location: state.location,
      navigationType: state.action,
      navigator: history,
      future: future
    });
  }
  /**
   * A `<Router>` that accepts a pre-instantiated history object. It's important
   * to note that using your own history object is highly discouraged and may add
   * two versions of the history library to your bundles unless you use the same
   * version of the history library that React Router uses internally.
   */
  function HistoryRouter(_ref6) {
    let {
      basename,
      children,
      future,
      history
    } = _ref6;
    let [state, setStateImpl] = React__namespace.useState({
      action: history.action,
      location: history.location
    });
    let {
      v7_startTransition
    } = future || {};
    let setState = React__namespace.useCallback(newState => {
      v7_startTransition && startTransitionImpl ? startTransitionImpl(() => setStateImpl(newState)) : setStateImpl(newState);
    }, [setStateImpl, v7_startTransition]);
    React__namespace.useLayoutEffect(() => history.listen(setState), [history, setState]);
    React__namespace.useEffect(() => reactRouter.UNSAFE_logV6DeprecationWarnings(future), [future]);
    return /*#__PURE__*/React__namespace.createElement(reactRouter.Router, {
      basename: basename,
      children: children,
      location: state.location,
      navigationType: state.action,
      navigator: history,
      future: future
    });
  }
  {
    HistoryRouter.displayName = "unstable_HistoryRouter";
  }
  const isBrowser = typeof window !== "undefined" && typeof window.document !== "undefined" && typeof window.document.createElement !== "undefined";
  const ABSOLUTE_URL_REGEX = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i;

  /**
   * The public API for rendering a history-aware `<a>`.
   */
  const Link = /*#__PURE__*/React__namespace.forwardRef(function LinkWithRef(_ref7, ref) {
    let {
        onClick,
        relative,
        reloadDocument,
        replace,
        state,
        target,
        to,
        preventScrollReset,
        viewTransition
      } = _ref7,
      rest = _objectWithoutPropertiesLoose(_ref7, _excluded);
    let {
      basename
    } = React__namespace.useContext(reactRouter.UNSAFE_NavigationContext);

    // Rendered into <a href> for absolute URLs
    let absoluteHref;
    let isExternal = false;
    if (typeof to === "string" && ABSOLUTE_URL_REGEX.test(to)) {
      // Render the absolute href server- and client-side
      absoluteHref = to;

      // Only check for external origins client-side
      if (isBrowser) {
        try {
          let currentUrl = new URL(window.location.href);
          let targetUrl = to.startsWith("//") ? new URL(currentUrl.protocol + to) : new URL(to);
          let path = router.stripBasename(targetUrl.pathname, basename);
          if (targetUrl.origin === currentUrl.origin && path != null) {
            // Strip the protocol/origin/basename for same-origin absolute URLs
            to = path + targetUrl.search + targetUrl.hash;
          } else {
            isExternal = true;
          }
        } catch (e) {
          // We can't do external URL detection without a valid URL
          router.UNSAFE_warning(false, "<Link to=\"" + to + "\"> contains an invalid URL which will probably break " + "when clicked - please update to a valid URL path.") ;
        }
      }
    }

    // Rendered into <a href> for relative URLs
    let href = reactRouter.useHref(to, {
      relative
    });
    let internalOnClick = useLinkClickHandler(to, {
      replace,
      state,
      target,
      preventScrollReset,
      relative,
      viewTransition
    });
    function handleClick(event) {
      if (onClick) onClick(event);
      if (!event.defaultPrevented) {
        internalOnClick(event);
      }
    }
    return (
      /*#__PURE__*/
      // eslint-disable-next-line jsx-a11y/anchor-has-content
      React__namespace.createElement("a", _extends({}, rest, {
        href: absoluteHref || href,
        onClick: isExternal || reloadDocument ? onClick : handleClick,
        ref: ref,
        target: target
      }))
    );
  });
  {
    Link.displayName = "Link";
  }
  /**
   * A `<Link>` wrapper that knows if it's "active" or not.
   */
  const NavLink = /*#__PURE__*/React__namespace.forwardRef(function NavLinkWithRef(_ref8, ref) {
    let {
        "aria-current": ariaCurrentProp = "page",
        caseSensitive = false,
        className: classNameProp = "",
        end = false,
        style: styleProp,
        to,
        viewTransition,
        children
      } = _ref8,
      rest = _objectWithoutPropertiesLoose(_ref8, _excluded2);
    let path = reactRouter.useResolvedPath(to, {
      relative: rest.relative
    });
    let location = reactRouter.useLocation();
    let routerState = React__namespace.useContext(reactRouter.UNSAFE_DataRouterStateContext);
    let {
      navigator,
      basename
    } = React__namespace.useContext(reactRouter.UNSAFE_NavigationContext);
    let isTransitioning = routerState != null &&
    // Conditional usage is OK here because the usage of a data router is static
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useViewTransitionState(path) && viewTransition === true;
    let toPathname = navigator.encodeLocation ? navigator.encodeLocation(path).pathname : path.pathname;
    let locationPathname = location.pathname;
    let nextLocationPathname = routerState && routerState.navigation && routerState.navigation.location ? routerState.navigation.location.pathname : null;
    if (!caseSensitive) {
      locationPathname = locationPathname.toLowerCase();
      nextLocationPathname = nextLocationPathname ? nextLocationPathname.toLowerCase() : null;
      toPathname = toPathname.toLowerCase();
    }
    if (nextLocationPathname && basename) {
      nextLocationPathname = router.stripBasename(nextLocationPathname, basename) || nextLocationPathname;
    }

    // If the `to` has a trailing slash, look at that exact spot.  Otherwise,
    // we're looking for a slash _after_ what's in `to`.  For example:
    //
    // <NavLink to="/users"> and <NavLink to="/users/">
    // both want to look for a / at index 6 to match URL `/users/matt`
    const endSlashPosition = toPathname !== "/" && toPathname.endsWith("/") ? toPathname.length - 1 : toPathname.length;
    let isActive = locationPathname === toPathname || !end && locationPathname.startsWith(toPathname) && locationPathname.charAt(endSlashPosition) === "/";
    let isPending = nextLocationPathname != null && (nextLocationPathname === toPathname || !end && nextLocationPathname.startsWith(toPathname) && nextLocationPathname.charAt(toPathname.length) === "/");
    let renderProps = {
      isActive,
      isPending,
      isTransitioning
    };
    let ariaCurrent = isActive ? ariaCurrentProp : undefined;
    let className;
    if (typeof classNameProp === "function") {
      className = classNameProp(renderProps);
    } else {
      // If the className prop is not a function, we use a default `active`
      // class for <NavLink />s that are active. In v5 `active` was the default
      // value for `activeClassName`, but we are removing that API and can still
      // use the old default behavior for a cleaner upgrade path and keep the
      // simple styling rules working as they currently do.
      className = [classNameProp, isActive ? "active" : null, isPending ? "pending" : null, isTransitioning ? "transitioning" : null].filter(Boolean).join(" ");
    }
    let style = typeof styleProp === "function" ? styleProp(renderProps) : styleProp;
    return /*#__PURE__*/React__namespace.createElement(Link, _extends({}, rest, {
      "aria-current": ariaCurrent,
      className: className,
      ref: ref,
      style: style,
      to: to,
      viewTransition: viewTransition
    }), typeof children === "function" ? children(renderProps) : children);
  });
  {
    NavLink.displayName = "NavLink";
  }

  /**
   * Form props shared by navigations and fetchers
   */

  /**
   * Form props available to fetchers
   */

  /**
   * Form props available to navigations
   */

  /**
   * A `@remix-run/router`-aware `<form>`. It behaves like a normal form except
   * that the interaction with the server is with `fetch` instead of new document
   * requests, allowing components to add nicer UX to the page as the form is
   * submitted and returns with data.
   */
  const Form = /*#__PURE__*/React__namespace.forwardRef((_ref9, forwardedRef) => {
    let {
        fetcherKey,
        navigate,
        reloadDocument,
        replace,
        state,
        method = defaultMethod,
        action,
        onSubmit,
        relative,
        preventScrollReset,
        viewTransition
      } = _ref9,
      props = _objectWithoutPropertiesLoose(_ref9, _excluded3);
    let submit = useSubmit();
    let formAction = useFormAction(action, {
      relative
    });
    let formMethod = method.toLowerCase() === "get" ? "get" : "post";
    let submitHandler = event => {
      onSubmit && onSubmit(event);
      if (event.defaultPrevented) return;
      event.preventDefault();
      let submitter = event.nativeEvent.submitter;
      let submitMethod = (submitter == null ? void 0 : submitter.getAttribute("formmethod")) || method;
      submit(submitter || event.currentTarget, {
        fetcherKey,
        method: submitMethod,
        navigate,
        replace,
        state,
        relative,
        preventScrollReset,
        viewTransition
      });
    };
    return /*#__PURE__*/React__namespace.createElement("form", _extends({
      ref: forwardedRef,
      method: formMethod,
      action: formAction,
      onSubmit: reloadDocument ? onSubmit : submitHandler
    }, props));
  });
  {
    Form.displayName = "Form";
  }
  /**
   * This component will emulate the browser's scroll restoration on location
   * changes.
   */
  function ScrollRestoration(_ref10) {
    let {
      getKey,
      storageKey
    } = _ref10;
    useScrollRestoration({
      getKey,
      storageKey
    });
    return null;
  }
  {
    ScrollRestoration.displayName = "ScrollRestoration";
  }
  //#endregion

  ////////////////////////////////////////////////////////////////////////////////
  //#region Hooks
  ////////////////////////////////////////////////////////////////////////////////
  var DataRouterHook = /*#__PURE__*/function (DataRouterHook) {
    DataRouterHook["UseScrollRestoration"] = "useScrollRestoration";
    DataRouterHook["UseSubmit"] = "useSubmit";
    DataRouterHook["UseSubmitFetcher"] = "useSubmitFetcher";
    DataRouterHook["UseFetcher"] = "useFetcher";
    DataRouterHook["useViewTransitionState"] = "useViewTransitionState";
    return DataRouterHook;
  }(DataRouterHook || {});
  var DataRouterStateHook = /*#__PURE__*/function (DataRouterStateHook) {
    DataRouterStateHook["UseFetcher"] = "useFetcher";
    DataRouterStateHook["UseFetchers"] = "useFetchers";
    DataRouterStateHook["UseScrollRestoration"] = "useScrollRestoration";
    return DataRouterStateHook;
  }(DataRouterStateHook || {}); // Internal hooks
  function getDataRouterConsoleError(hookName) {
    return hookName + " must be used within a data router.  See https://reactrouter.com/v6/routers/picking-a-router.";
  }
  function useDataRouterContext(hookName) {
    let ctx = React__namespace.useContext(reactRouter.UNSAFE_DataRouterContext);
    !ctx ? router.UNSAFE_invariant(false, getDataRouterConsoleError(hookName))  : void 0;
    return ctx;
  }
  function useDataRouterState(hookName) {
    let state = React__namespace.useContext(reactRouter.UNSAFE_DataRouterStateContext);
    !state ? router.UNSAFE_invariant(false, getDataRouterConsoleError(hookName))  : void 0;
    return state;
  }

  // External hooks

  /**
   * Handles the click behavior for router `<Link>` components. This is useful if
   * you need to create custom `<Link>` components with the same click behavior we
   * use in our exported `<Link>`.
   */
  function useLinkClickHandler(to, _temp) {
    let {
      target,
      replace: replaceProp,
      state,
      preventScrollReset,
      relative,
      viewTransition
    } = _temp === void 0 ? {} : _temp;
    let navigate = reactRouter.useNavigate();
    let location = reactRouter.useLocation();
    let path = reactRouter.useResolvedPath(to, {
      relative
    });
    return React__namespace.useCallback(event => {
      if (shouldProcessLinkClick(event, target)) {
        event.preventDefault();

        // If the URL hasn't changed, a regular <a> will do a replace instead of
        // a push, so do the same here unless the replace prop is explicitly set
        let replace = replaceProp !== undefined ? replaceProp : reactRouter.createPath(location) === reactRouter.createPath(path);
        navigate(to, {
          replace,
          state,
          preventScrollReset,
          relative,
          viewTransition
        });
      }
    }, [location, navigate, path, replaceProp, state, target, to, preventScrollReset, relative, viewTransition]);
  }

  /**
   * A convenient wrapper for reading and writing search parameters via the
   * URLSearchParams interface.
   */
  function useSearchParams(defaultInit) {
    router.UNSAFE_warning(typeof URLSearchParams !== "undefined", "You cannot use the `useSearchParams` hook in a browser that does not " + "support the URLSearchParams API. If you need to support Internet " + "Explorer 11, we recommend you load a polyfill such as " + "https://github.com/ungap/url-search-params.") ;
    let defaultSearchParamsRef = React__namespace.useRef(createSearchParams(defaultInit));
    let hasSetSearchParamsRef = React__namespace.useRef(false);
    let location = reactRouter.useLocation();
    let searchParams = React__namespace.useMemo(() =>
    // Only merge in the defaults if we haven't yet called setSearchParams.
    // Once we call that we want those to take precedence, otherwise you can't
    // remove a param with setSearchParams({}) if it has an initial value
    getSearchParamsForLocation(location.search, hasSetSearchParamsRef.current ? null : defaultSearchParamsRef.current), [location.search]);
    let navigate = reactRouter.useNavigate();
    let setSearchParams = React__namespace.useCallback((nextInit, navigateOptions) => {
      const newSearchParams = createSearchParams(typeof nextInit === "function" ? nextInit(searchParams) : nextInit);
      hasSetSearchParamsRef.current = true;
      navigate("?" + newSearchParams, navigateOptions);
    }, [navigate, searchParams]);
    return [searchParams, setSearchParams];
  }

  /**
   * Submits a HTML `<form>` to the server without reloading the page.
   */

  /**
   * Submits a fetcher `<form>` to the server without reloading the page.
   */

  function validateClientSideSubmission() {
    if (typeof document === "undefined") {
      throw new Error("You are calling submit during the server render. " + "Try calling submit within a `useEffect` or callback instead.");
    }
  }
  let fetcherId = 0;
  let getUniqueFetcherId = () => "__" + String(++fetcherId) + "__";

  /**
   * Returns a function that may be used to programmatically submit a form (or
   * some arbitrary data) to the server.
   */
  function useSubmit() {
    let {
      router
    } = useDataRouterContext(DataRouterHook.UseSubmit);
    let {
      basename
    } = React__namespace.useContext(reactRouter.UNSAFE_NavigationContext);
    let currentRouteId = reactRouter.UNSAFE_useRouteId();
    return React__namespace.useCallback(function (target, options) {
      if (options === void 0) {
        options = {};
      }
      validateClientSideSubmission();
      let {
        action,
        method,
        encType,
        formData,
        body
      } = getFormSubmissionInfo(target, basename);
      if (options.navigate === false) {
        let key = options.fetcherKey || getUniqueFetcherId();
        router.fetch(key, currentRouteId, options.action || action, {
          preventScrollReset: options.preventScrollReset,
          formData,
          body,
          formMethod: options.method || method,
          formEncType: options.encType || encType,
          flushSync: options.flushSync
        });
      } else {
        router.navigate(options.action || action, {
          preventScrollReset: options.preventScrollReset,
          formData,
          body,
          formMethod: options.method || method,
          formEncType: options.encType || encType,
          replace: options.replace,
          state: options.state,
          fromRouteId: currentRouteId,
          flushSync: options.flushSync,
          viewTransition: options.viewTransition
        });
      }
    }, [router, basename, currentRouteId]);
  }

  // v7: Eventually we should deprecate this entirely in favor of using the
  // router method directly?
  function useFormAction(action, _temp2) {
    let {
      relative
    } = _temp2 === void 0 ? {} : _temp2;
    let {
      basename
    } = React__namespace.useContext(reactRouter.UNSAFE_NavigationContext);
    let routeContext = React__namespace.useContext(reactRouter.UNSAFE_RouteContext);
    !routeContext ? router.UNSAFE_invariant(false, "useFormAction must be used inside a RouteContext")  : void 0;
    let [match] = routeContext.matches.slice(-1);
    // Shallow clone path so we can modify it below, otherwise we modify the
    // object referenced by useMemo inside useResolvedPath
    let path = _extends({}, reactRouter.useResolvedPath(action ? action : ".", {
      relative
    }));

    // If no action was specified, browsers will persist current search params
    // when determining the path, so match that behavior
    // https://github.com/remix-run/remix/issues/927
    let location = reactRouter.useLocation();
    if (action == null) {
      // Safe to write to this directly here since if action was undefined, we
      // would have called useResolvedPath(".") which will never include a search
      path.search = location.search;

      // When grabbing search params from the URL, remove any included ?index param
      // since it might not apply to our contextual route.  We add it back based
      // on match.route.index below
      let params = new URLSearchParams(path.search);
      let indexValues = params.getAll("index");
      let hasNakedIndexParam = indexValues.some(v => v === "");
      if (hasNakedIndexParam) {
        params.delete("index");
        indexValues.filter(v => v).forEach(v => params.append("index", v));
        let qs = params.toString();
        path.search = qs ? "?" + qs : "";
      }
    }
    if ((!action || action === ".") && match.route.index) {
      path.search = path.search ? path.search.replace(/^\?/, "?index&") : "?index";
    }

    // If we're operating within a basename, prepend it to the pathname prior
    // to creating the form action.  If this is a root navigation, then just use
    // the raw basename which allows the basename to have full control over the
    // presence of a trailing slash on root actions
    if (basename !== "/") {
      path.pathname = path.pathname === "/" ? basename : router.joinPaths([basename, path.pathname]);
    }
    return reactRouter.createPath(path);
  }
  // TODO: (v7) Change the useFetcher generic default from `any` to `unknown`
  /**
   * Interacts with route loaders and actions without causing a navigation. Great
   * for any interaction that stays on the same page.
   */
  function useFetcher(_temp3) {
    var _route$matches;
    let {
      key
    } = _temp3 === void 0 ? {} : _temp3;
    let {
      router: router$1
    } = useDataRouterContext(DataRouterHook.UseFetcher);
    let state = useDataRouterState(DataRouterStateHook.UseFetcher);
    let fetcherData = React__namespace.useContext(FetchersContext);
    let route = React__namespace.useContext(reactRouter.UNSAFE_RouteContext);
    let routeId = (_route$matches = route.matches[route.matches.length - 1]) == null ? void 0 : _route$matches.route.id;
    !fetcherData ? router.UNSAFE_invariant(false, "useFetcher must be used inside a FetchersContext")  : void 0;
    !route ? router.UNSAFE_invariant(false, "useFetcher must be used inside a RouteContext")  : void 0;
    !(routeId != null) ? router.UNSAFE_invariant(false, "useFetcher can only be used on routes that contain a unique \"id\"")  : void 0;

    // Fetcher key handling
    // OK to call conditionally to feature detect `useId`
    // eslint-disable-next-line react-hooks/rules-of-hooks
    let defaultKey = useIdImpl ? useIdImpl() : "";
    let [fetcherKey, setFetcherKey] = React__namespace.useState(key || defaultKey);
    if (key && key !== fetcherKey) {
      setFetcherKey(key);
    } else if (!fetcherKey) {
      // We will only fall through here when `useId` is not available
      setFetcherKey(getUniqueFetcherId());
    }

    // Registration/cleanup
    React__namespace.useEffect(() => {
      router$1.getFetcher(fetcherKey);
      return () => {
        // Tell the router we've unmounted - if v7_fetcherPersist is enabled this
        // will not delete immediately but instead queue up a delete after the
        // fetcher returns to an `idle` state
        router$1.deleteFetcher(fetcherKey);
      };
    }, [router$1, fetcherKey]);

    // Fetcher additions
    let load = React__namespace.useCallback((href, opts) => {
      !routeId ? router.UNSAFE_invariant(false, "No routeId available for fetcher.load()")  : void 0;
      router$1.fetch(fetcherKey, routeId, href, opts);
    }, [fetcherKey, routeId, router$1]);
    let submitImpl = useSubmit();
    let submit = React__namespace.useCallback((target, opts) => {
      submitImpl(target, _extends({}, opts, {
        navigate: false,
        fetcherKey
      }));
    }, [fetcherKey, submitImpl]);
    let FetcherForm = React__namespace.useMemo(() => {
      let FetcherForm = /*#__PURE__*/React__namespace.forwardRef((props, ref) => {
        return /*#__PURE__*/React__namespace.createElement(Form, _extends({}, props, {
          navigate: false,
          fetcherKey: fetcherKey,
          ref: ref
        }));
      });
      {
        FetcherForm.displayName = "fetcher.Form";
      }
      return FetcherForm;
    }, [fetcherKey]);

    // Exposed FetcherWithComponents
    let fetcher = state.fetchers.get(fetcherKey) || router.IDLE_FETCHER;
    let data = fetcherData.get(fetcherKey);
    let fetcherWithComponents = React__namespace.useMemo(() => _extends({
      Form: FetcherForm,
      submit,
      load
    }, fetcher, {
      data
    }), [FetcherForm, submit, load, fetcher, data]);
    return fetcherWithComponents;
  }

  /**
   * Provides all fetchers currently on the page. Useful for layouts and parent
   * routes that need to provide pending/optimistic UI regarding the fetch.
   */
  function useFetchers() {
    let state = useDataRouterState(DataRouterStateHook.UseFetchers);
    return Array.from(state.fetchers.entries()).map(_ref11 => {
      let [key, fetcher] = _ref11;
      return _extends({}, fetcher, {
        key
      });
    });
  }
  const SCROLL_RESTORATION_STORAGE_KEY = "react-router-scroll-positions";
  let savedScrollPositions = {};

  /**
   * When rendered inside a RouterProvider, will restore scroll positions on navigations
   */
  function useScrollRestoration(_temp4) {
    let {
      getKey,
      storageKey
    } = _temp4 === void 0 ? {} : _temp4;
    let {
      router: router$1
    } = useDataRouterContext(DataRouterHook.UseScrollRestoration);
    let {
      restoreScrollPosition,
      preventScrollReset
    } = useDataRouterState(DataRouterStateHook.UseScrollRestoration);
    let {
      basename
    } = React__namespace.useContext(reactRouter.UNSAFE_NavigationContext);
    let location = reactRouter.useLocation();
    let matches = reactRouter.useMatches();
    let navigation = reactRouter.useNavigation();

    // Trigger manual scroll restoration while we're active
    React__namespace.useEffect(() => {
      window.history.scrollRestoration = "manual";
      return () => {
        window.history.scrollRestoration = "auto";
      };
    }, []);

    // Save positions on pagehide
    usePageHide(React__namespace.useCallback(() => {
      if (navigation.state === "idle") {
        let key = (getKey ? getKey(location, matches) : null) || location.key;
        savedScrollPositions[key] = window.scrollY;
      }
      try {
        sessionStorage.setItem(storageKey || SCROLL_RESTORATION_STORAGE_KEY, JSON.stringify(savedScrollPositions));
      } catch (error) {
        router.UNSAFE_warning(false, "Failed to save scroll positions in sessionStorage, <ScrollRestoration /> will not work properly (" + error + ").") ;
      }
      window.history.scrollRestoration = "auto";
    }, [storageKey, getKey, navigation.state, location, matches]));

    // Read in any saved scroll locations
    if (typeof document !== "undefined") {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      React__namespace.useLayoutEffect(() => {
        try {
          let sessionPositions = sessionStorage.getItem(storageKey || SCROLL_RESTORATION_STORAGE_KEY);
          if (sessionPositions) {
            savedScrollPositions = JSON.parse(sessionPositions);
          }
        } catch (e) {
          // no-op, use default empty object
        }
      }, [storageKey]);

      // Enable scroll restoration in the router
      // eslint-disable-next-line react-hooks/rules-of-hooks
      React__namespace.useLayoutEffect(() => {
        let getKeyWithoutBasename = getKey && basename !== "/" ? (location, matches) => getKey( // Strip the basename to match useLocation()
        _extends({}, location, {
          pathname: router.stripBasename(location.pathname, basename) || location.pathname
        }), matches) : getKey;
        let disableScrollRestoration = router$1 == null ? void 0 : router$1.enableScrollRestoration(savedScrollPositions, () => window.scrollY, getKeyWithoutBasename);
        return () => disableScrollRestoration && disableScrollRestoration();
      }, [router$1, basename, getKey]);

      // Restore scrolling when state.restoreScrollPosition changes
      // eslint-disable-next-line react-hooks/rules-of-hooks
      React__namespace.useLayoutEffect(() => {
        // Explicit false means don't do anything (used for submissions)
        if (restoreScrollPosition === false) {
          return;
        }

        // been here before, scroll to it
        if (typeof restoreScrollPosition === "number") {
          window.scrollTo(0, restoreScrollPosition);
          return;
        }

        // try to scroll to the hash
        if (location.hash) {
          let el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
          if (el) {
            el.scrollIntoView();
            return;
          }
        }

        // Don't reset if this navigation opted out
        if (preventScrollReset === true) {
          return;
        }

        // otherwise go to the top on new locations
        window.scrollTo(0, 0);
      }, [location, restoreScrollPosition, preventScrollReset]);
    }
  }

  /**
   * Setup a callback to be fired on the window's `beforeunload` event. This is
   * useful for saving some data to `window.localStorage` just before the page
   * refreshes.
   *
   * Note: The `callback` argument should be a function created with
   * `React.useCallback()`.
   */
  function useBeforeUnload(callback, options) {
    let {
      capture
    } = options || {};
    React__namespace.useEffect(() => {
      let opts = capture != null ? {
        capture
      } : undefined;
      window.addEventListener("beforeunload", callback, opts);
      return () => {
        window.removeEventListener("beforeunload", callback, opts);
      };
    }, [callback, capture]);
  }

  /**
   * Setup a callback to be fired on the window's `pagehide` event. This is
   * useful for saving some data to `window.localStorage` just before the page
   * refreshes.  This event is better supported than beforeunload across browsers.
   *
   * Note: The `callback` argument should be a function created with
   * `React.useCallback()`.
   */
  function usePageHide(callback, options) {
    let {
      capture
    } = options || {};
    React__namespace.useEffect(() => {
      let opts = capture != null ? {
        capture
      } : undefined;
      window.addEventListener("pagehide", callback, opts);
      return () => {
        window.removeEventListener("pagehide", callback, opts);
      };
    }, [callback, capture]);
  }

  /**
   * Wrapper around useBlocker to show a window.confirm prompt to users instead
   * of building a custom UI with useBlocker.
   *
   * Warning: This has *a lot of rough edges* and behaves very differently (and
   * very incorrectly in some cases) across browsers if user click addition
   * back/forward navigations while the confirm is open.  Use at your own risk.
   */
  function usePrompt(_ref12) {
    let {
      when,
      message
    } = _ref12;
    let blocker = reactRouter.useBlocker(when);
    React__namespace.useEffect(() => {
      if (blocker.state === "blocked") {
        let proceed = window.confirm(message);
        if (proceed) {
          // This timeout is needed to avoid a weird "race" on POP navigations
          // between the `window.history` revert navigation and the result of
          // `window.confirm`
          setTimeout(blocker.proceed, 0);
        } else {
          blocker.reset();
        }
      }
    }, [blocker, message]);
    React__namespace.useEffect(() => {
      if (blocker.state === "blocked" && !when) {
        blocker.reset();
      }
    }, [blocker, when]);
  }

  /**
   * Return a boolean indicating if there is an active view transition to the
   * given href.  You can use this value to render CSS classes or viewTransitionName
   * styles onto your elements
   *
   * @param href The destination href
   * @param [opts.relative] Relative routing type ("route" | "path")
   */
  function useViewTransitionState(to, opts) {
    if (opts === void 0) {
      opts = {};
    }
    let vtContext = React__namespace.useContext(ViewTransitionContext);
    !(vtContext != null) ? router.UNSAFE_invariant(false, "`useViewTransitionState` must be used within `react-router-dom`'s `RouterProvider`.  " + "Did you accidentally import `RouterProvider` from `react-router`?")  : void 0;
    let {
      basename
    } = useDataRouterContext(DataRouterHook.useViewTransitionState);
    let path = reactRouter.useResolvedPath(to, {
      relative: opts.relative
    });
    if (!vtContext.isTransitioning) {
      return false;
    }
    let currentPath = router.stripBasename(vtContext.currentLocation.pathname, basename) || vtContext.currentLocation.pathname;
    let nextPath = router.stripBasename(vtContext.nextLocation.pathname, basename) || vtContext.nextLocation.pathname;

    // Transition is active if we're going to or coming from the indicated
    // destination.  This ensures that other PUSH navigations that reverse
    // an indicated transition apply.  I.e., on the list view you have:
    //
    //   <NavLink to="/details/1" viewTransition>
    //
    // If you click the breadcrumb back to the list view:
    //
    //   <NavLink to="/list" viewTransition>
    //
    // We should apply the transition because it's indicated as active going
    // from /list -> /details/1 and therefore should be active on the reverse
    // (even though this isn't strictly a POP reverse)
    return router.matchPath(path.pathname, nextPath) != null || router.matchPath(path.pathname, currentPath) != null;
  }

  //#endregion

  Object.defineProperty(exports, 'AbortedDeferredError', {
    enumerable: true,
    get: function () { return reactRouter.AbortedDeferredError; }
  });
  Object.defineProperty(exports, 'Await', {
    enumerable: true,
    get: function () { return reactRouter.Await; }
  });
  Object.defineProperty(exports, 'MemoryRouter', {
    enumerable: true,
    get: function () { return reactRouter.MemoryRouter; }
  });
  Object.defineProperty(exports, 'Navigate', {
    enumerable: true,
    get: function () { return reactRouter.Navigate; }
  });
  Object.defineProperty(exports, 'NavigationType', {
    enumerable: true,
    get: function () { return reactRouter.NavigationType; }
  });
  Object.defineProperty(exports, 'Outlet', {
    enumerable: true,
    get: function () { return reactRouter.Outlet; }
  });
  Object.defineProperty(exports, 'Route', {
    enumerable: true,
    get: function () { return reactRouter.Route; }
  });
  Object.defineProperty(exports, 'Router', {
    enumerable: true,
    get: function () { return reactRouter.Router; }
  });
  Object.defineProperty(exports, 'Routes', {
    enumerable: true,
    get: function () { return reactRouter.Routes; }
  });
  Object.defineProperty(exports, 'UNSAFE_DataRouterContext', {
    enumerable: true,
    get: function () { return reactRouter.UNSAFE_DataRouterContext; }
  });
  Object.defineProperty(exports, 'UNSAFE_DataRouterStateContext', {
    enumerable: true,
    get: function () { return reactRouter.UNSAFE_DataRouterStateContext; }
  });
  Object.defineProperty(exports, 'UNSAFE_LocationContext', {
    enumerable: true,
    get: function () { return reactRouter.UNSAFE_LocationContext; }
  });
  Object.defineProperty(exports, 'UNSAFE_NavigationContext', {
    enumerable: true,
    get: function () { return reactRouter.UNSAFE_NavigationContext; }
  });
  Object.defineProperty(exports, 'UNSAFE_RouteContext', {
    enumerable: true,
    get: function () { return reactRouter.UNSAFE_RouteContext; }
  });
  Object.defineProperty(exports, 'UNSAFE_useRouteId', {
    enumerable: true,
    get: function () { return reactRouter.UNSAFE_useRouteId; }
  });
  Object.defineProperty(exports, 'createMemoryRouter', {
    enumerable: true,
    get: function () { return reactRouter.createMemoryRouter; }
  });
  Object.defineProperty(exports, 'createPath', {
    enumerable: true,
    get: function () { return reactRouter.createPath; }
  });
  Object.defineProperty(exports, 'createRoutesFromChildren', {
    enumerable: true,
    get: function () { return reactRouter.createRoutesFromChildren; }
  });
  Object.defineProperty(exports, 'createRoutesFromElements', {
    enumerable: true,
    get: function () { return reactRouter.createRoutesFromElements; }
  });
  Object.defineProperty(exports, 'defer', {
    enumerable: true,
    get: function () { return reactRouter.defer; }
  });
  Object.defineProperty(exports, 'generatePath', {
    enumerable: true,
    get: function () { return reactRouter.generatePath; }
  });
  Object.defineProperty(exports, 'isRouteErrorResponse', {
    enumerable: true,
    get: function () { return reactRouter.isRouteErrorResponse; }
  });
  Object.defineProperty(exports, 'json', {
    enumerable: true,
    get: function () { return reactRouter.json; }
  });
  Object.defineProperty(exports, 'matchPath', {
    enumerable: true,
    get: function () { return reactRouter.matchPath; }
  });
  Object.defineProperty(exports, 'matchRoutes', {
    enumerable: true,
    get: function () { return reactRouter.matchRoutes; }
  });
  Object.defineProperty(exports, 'parsePath', {
    enumerable: true,
    get: function () { return reactRouter.parsePath; }
  });
  Object.defineProperty(exports, 'redirect', {
    enumerable: true,
    get: function () { return reactRouter.redirect; }
  });
  Object.defineProperty(exports, 'redirectDocument', {
    enumerable: true,
    get: function () { return reactRouter.redirectDocument; }
  });
  Object.defineProperty(exports, 'renderMatches', {
    enumerable: true,
    get: function () { return reactRouter.renderMatches; }
  });
  Object.defineProperty(exports, 'replace', {
    enumerable: true,
    get: function () { return reactRouter.replace; }
  });
  Object.defineProperty(exports, 'resolvePath', {
    enumerable: true,
    get: function () { return reactRouter.resolvePath; }
  });
  Object.defineProperty(exports, 'useActionData', {
    enumerable: true,
    get: function () { return reactRouter.useActionData; }
  });
  Object.defineProperty(exports, 'useAsyncError', {
    enumerable: true,
    get: function () { return reactRouter.useAsyncError; }
  });
  Object.defineProperty(exports, 'useAsyncValue', {
    enumerable: true,
    get: function () { return reactRouter.useAsyncValue; }
  });
  Object.defineProperty(exports, 'useBlocker', {
    enumerable: true,
    get: function () { return reactRouter.useBlocker; }
  });
  Object.defineProperty(exports, 'useHref', {
    enumerable: true,
    get: function () { return reactRouter.useHref; }
  });
  Object.defineProperty(exports, 'useInRouterContext', {
    enumerable: true,
    get: function () { return reactRouter.useInRouterContext; }
  });
  Object.defineProperty(exports, 'useLoaderData', {
    enumerable: true,
    get: function () { return reactRouter.useLoaderData; }
  });
  Object.defineProperty(exports, 'useLocation', {
    enumerable: true,
    get: function () { return reactRouter.useLocation; }
  });
  Object.defineProperty(exports, 'useMatch', {
    enumerable: true,
    get: function () { return reactRouter.useMatch; }
  });
  Object.defineProperty(exports, 'useMatches', {
    enumerable: true,
    get: function () { return reactRouter.useMatches; }
  });
  Object.defineProperty(exports, 'useNavigate', {
    enumerable: true,
    get: function () { return reactRouter.useNavigate; }
  });
  Object.defineProperty(exports, 'useNavigation', {
    enumerable: true,
    get: function () { return reactRouter.useNavigation; }
  });
  Object.defineProperty(exports, 'useNavigationType', {
    enumerable: true,
    get: function () { return reactRouter.useNavigationType; }
  });
  Object.defineProperty(exports, 'useOutlet', {
    enumerable: true,
    get: function () { return reactRouter.useOutlet; }
  });
  Object.defineProperty(exports, 'useOutletContext', {
    enumerable: true,
    get: function () { return reactRouter.useOutletContext; }
  });
  Object.defineProperty(exports, 'useParams', {
    enumerable: true,
    get: function () { return reactRouter.useParams; }
  });
  Object.defineProperty(exports, 'useResolvedPath', {
    enumerable: true,
    get: function () { return reactRouter.useResolvedPath; }
  });
  Object.defineProperty(exports, 'useRevalidator', {
    enumerable: true,
    get: function () { return reactRouter.useRevalidator; }
  });
  Object.defineProperty(exports, 'useRouteError', {
    enumerable: true,
    get: function () { return reactRouter.useRouteError; }
  });
  Object.defineProperty(exports, 'useRouteLoaderData', {
    enumerable: true,
    get: function () { return reactRouter.useRouteLoaderData; }
  });
  Object.defineProperty(exports, 'useRoutes', {
    enumerable: true,
    get: function () { return reactRouter.useRoutes; }
  });
  Object.defineProperty(exports, 'UNSAFE_ErrorResponseImpl', {
    enumerable: true,
    get: function () { return router.UNSAFE_ErrorResponseImpl; }
  });
  exports.BrowserRouter = BrowserRouter;
  exports.Form = Form;
  exports.HashRouter = HashRouter;
  exports.Link = Link;
  exports.NavLink = NavLink;
  exports.RouterProvider = RouterProvider;
  exports.ScrollRestoration = ScrollRestoration;
  exports.UNSAFE_FetchersContext = FetchersContext;
  exports.UNSAFE_ViewTransitionContext = ViewTransitionContext;
  exports.UNSAFE_useScrollRestoration = useScrollRestoration;
  exports.createBrowserRouter = createBrowserRouter;
  exports.createHashRouter = createHashRouter;
  exports.createSearchParams = createSearchParams;
  exports.unstable_HistoryRouter = HistoryRouter;
  exports.unstable_usePrompt = usePrompt;
  exports.useBeforeUnload = useBeforeUnload;
  exports.useFetcher = useFetcher;
  exports.useFetchers = useFetchers;
  exports.useFormAction = useFormAction;
  exports.useLinkClickHandler = useLinkClickHandler;
  exports.useSearchParams = useSearchParams;
  exports.useSubmit = useSubmit;
  exports.useViewTransitionState = useViewTransitionState;

  Object.defineProperty(exports, '__esModule', { value: true });

}));
//# sourceMappingURL=react-router-dom.development.js.map
